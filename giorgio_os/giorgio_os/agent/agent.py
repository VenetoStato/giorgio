"""Natural-language agent: a local rule router ("System 1", < 1 ms, offline) plus an OPTIONAL Claude
planner ("System 2") for free-form requests. The LLM is off by default (``agent.llm_enabled``) and,
when on, it can only return a plan made of registered skills that the mission manager validates.
The agent never talks to drivers or to the safety supervisor.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..config import AgentConfig
from ..mission.manager import SkillCall

log = logging.getLogger("giorgio.agent")


@dataclass
class AgentReply:
    say: str
    plan: list[SkillCall] = field(default_factory=list)
    engine: str = "router"           # router | claude | none
    latency_ms: float = 0.0
    stop: bool = False               # the user asked Giorgio to stop (software stop, NOT safety)


PLACES = {"a": "A", "b": "B", "c": "C", "charger": "C", "dock": "C", "station a": "A", "station b": "B",
          "kitting": "A", "bench a": "A", "bench b": "B", "banco a": "A", "banco b": "B", "ricarica": "C"}


class LocalRouter:
    """Deterministic keyword router, English + Italian. Returns None when unsure."""

    def __init__(self, people: list[str]):
        self.people = people

    def route(self, text: str, status: Callable[[], dict[str, Any]]) -> Optional[AgentReply]:
        t = " " + text.lower().strip() + " "
        who = next((p for p in self.people if p.lower() in t), None)
        if re.search(r"\b(stop|halt|freeze|fermati|ferma|alt)\b", t):
            return AgentReply("Stopping. (Software stop - the safety system is separate.)", stop=True)
        if re.search(r"\b(then|after that|poi|dopo|if|se|when|quando|unless)\b", t):
            return None                                   # compound request -> System 2
        if re.search(r"\b(battery|batteria|status|stato|how are you|come stai)\b", t) and not re.search(r"charge|caric", t):
            s = status()
            b = s.get("battery", {})
            return AgentReply(f"Battery {100 * b.get('soc', 0):.0f}%{' (charging)' if b.get('charging') else ''}, "
                              f"safety zone {s.get('safety', {}).get('zone', '?')}, "
                              f"{'idle' if not s.get('mission', {}).get('current') else 'busy'}.")
        if re.search(r"(coffee|caff|espresso)", t):
            plan = [SkillCall("make_coffee")]
            if who:
                plan.append(SkillCall("hand_over", {"person": who}))
            return AgentReply(f"One espresso coming{' for ' + who if who else ''}!", plan)
        if re.search(r"\b(charge|recharge|ricarica|ricaricati|in carica|go to sleep)\b", t):
            return AgentReply("Going to charge.", [SkillCall("dock_charge")])
        if re.search(r"\b(wave|hello|hi|ciao|saluta)\b", t):
            return AgentReply("Ciao!", [SkillCall("wave")])
        if re.search(r"\b(load|carica)\b.*\b(tray|bottles|flaconi|vassoio)\b|\bload the tray\b", t):
            return AgentReply("Loading the tray at bench A.", [SkillCall("load_tray")])
        if re.search(r"\b(unload|insert|scarica|inserisci)\b", t):
            return AgentReply("Unloading at bench B.", [SkillCall("unload_tray")])
        if re.search(r"\b(pick|grab|prendi)\b", t):
            return AgentReply("Picking a bottle.", [SkillCall("pick", {"what": "bottle"})])
        m = re.search(r"\b(?:go|drive|move|vai|torna)\s+(?:to\s+|a\s+|al\s+|alla\s+|in\s+)?(?:the\s+)?(.+?)\s*$", t.strip())
        if m:
            raw = m.group(1).strip(" .!")
            tgt = PLACES.get(raw) or (who if who else None)
            if tgt is None and raw.upper() in ("A", "B", "C"):
                tgt = raw.upper()
            if tgt:
                return AgentReply(f"On my way to {tgt}.", [SkillCall("navigate", {"target": tgt})])
        return None


SYSTEM_PROMPT = """You are the task planner of GIORGIO, a mobile bimanual service robot (AgileX Tracer 2.0 base,
two Enactic OpenArm 2.0 arms, Orbbec Gemini 336L, SICK safety scanners, capsule coffee machine on its back).
Map the user's request to a short plan using ONLY the skills listed in the JSON schema. If the request is not
feasible with these skills, explain briefly in 'say' and return an empty plan. Never plan anything about safety
settings: safety is handled by certified hardware and is not yours to change. Reply in the user's language."""


class ClaudePlanner:
    """Optional System 2 using the Anthropic Python SDK (``pip install anthropic``) and structured output."""

    def __init__(self, cfg: AgentConfig, skills: dict[str, str]):
        self.cfg, self.skills = cfg, skills
        self._client = None

    @property
    def available(self) -> bool:
        if not self.cfg.llm_enabled:
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def schema(self) -> dict[str, Any]:
        return {"type": "object", "additionalProperties": False, "required": ["say", "plan"], "properties": {
            "say": {"type": "string"},
            "plan": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["skill", "target"],
                                                "properties": {"skill": {"type": "string", "enum": sorted(self.skills)},
                                                               "target": {"type": "string"}}}}}}

    def plan(self, text: str, scene: dict[str, Any]) -> AgentReply:
        import anthropic
        if self._client is None:
            self._client = anthropic.Anthropic(timeout=self.cfg.llm_timeout_s)
        t0 = time.perf_counter()
        skills_doc = "\n".join(f"- {k}: {v}" for k, v in sorted(self.skills.items()))
        resp = self._client.messages.create(
            model=self.cfg.llm_model, max_tokens=2000,
            system=SYSTEM_PROMPT + "\nSkills (use 'target' for the place/person argument, empty string otherwise):\n" + skills_doc,
            output_config={"effort": self.cfg.llm_effort, "format": {"type": "json_schema", "schema": self.schema()}},
            messages=[{"role": "user", "content": f"Scene: {json.dumps(scene)}\nRequest: {text}"}],
        )
        if resp.stop_reason == "refusal":
            return AgentReply("I can't help with that one.", engine="claude")
        txt = next((b.text for b in resp.content if b.type == "text"), "{}")
        data = json.loads(txt)
        arg_name = {"navigate": "target", "hand_over": "person", "say": "text"}
        plan = []
        for p in data.get("plan", []):
            args = {arg_name[p["skill"]]: p["target"]} if p["skill"] in arg_name and p.get("target") else {}
            plan.append(SkillCall(p["skill"], args))
        return AgentReply(data.get("say", ""), plan, "claude", 1000 * (time.perf_counter() - t0))


class GiorgioAgent:
    def __init__(self, cfg: AgentConfig, people: list[str], skills: dict[str, str]):
        self.cfg = cfg
        self.router = LocalRouter(people)
        self.llm = ClaudePlanner(cfg, skills)
        self.chat: list[dict[str, Any]] = []

    def handle(self, text: str, status: Callable[[], dict[str, Any]]) -> AgentReply:
        t0 = time.perf_counter()
        reply = self.router.route(text, status)
        if reply is not None:
            reply.latency_ms = 1000 * (time.perf_counter() - t0)
        elif self.llm.available and os.environ.get("GIORGIO_OFFLINE") != "1":
            try:
                reply = self.llm.plan(text, status())
            except Exception as e:     # network down, no key, ... -> degrade gracefully
                log.warning("Claude planner failed: %s", e)
                reply = AgentReply(f"My planner is offline ({type(e).__name__}). Try a simple command.", engine="none")
        else:
            reply = AgentReply("I didn't get that. Try: 'make a coffee for Marco', 'go to B', 'load the tray', "
                               "'charge', 'wave'. (The Claude planner is off in this configuration.)", engine="none")
        self.chat = (self.chat + [{"who": "user", "text": text},
                                  {"who": "giorgio", "text": reply.say, "engine": reply.engine,
                                   "latency_ms": round(reply.latency_ms, 2), "plan": [c.label() for c in reply.plan]}])[-40:]
        return reply
