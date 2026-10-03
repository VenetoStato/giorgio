"""Giorgio's skill library.

Primitive skills (navigate, dock_charge, pick, place, sort, wave, say) are written ONLY against the
HAL + services, so they run unchanged on the real robot once the real drivers exist.
Composite skills marked ``requires_choreo`` (load_tray, unload_tray, make_coffee, hand_over) run v5's
proven choreographies in sim; on the real robot they are reported as unavailable until rebuilt
from primitives (see README roadmap).
"""
from __future__ import annotations

from typing import Any, Optional

from ..types import Detection
from .base import SkillContext, SkillError, SkillGen, skill


def _pick_side(ctx: SkillContext, det: Detection, side: Optional[str]) -> str:
    if side in ("right", "left"):
        return side
    _, y = ctx.robot_frame(det.xy)
    return "left" if y > 0 else "right"


def _free_hand(ctx: SkillContext, prefer: str = "right") -> str:
    order = [prefer, "left" if prefer == "right" else "right"]
    for s in order:
        if not ctx.hw.grippers[s].status().holding and not ctx.hw.arms[s].status().busy:
            return s
    raise SkillError("both hands are busy")


# --------------------------------------------------------------------------------------- mobility
@skill("navigate", "Drive to a named place (A, B, C/charger) or a person", {"target": "place or person name"})
def navigate(ctx: SkillContext, target: str = "A") -> SkillGen:
    goal = ctx.hw.world.resolve(target)
    if goal is None:
        raise SkillError(f"I don't know where '{target}' is (known: {', '.join(ctx.hw.world.known_targets())})")
    ctx.event(f"navigating to {target}")
    h = yield from ctx.wait(ctx.hw.base.navigate_to(goal), timeout_s=180, what=f"navigate to {target}")
    return f"at {target} ({h.message})"


@skill("dock_charge", "Go to the charging station, dock and start charging")
def dock_charge(ctx: SkillContext) -> SkillGen:
    if ctx.hw.dock.status().contacts_closed:
        return "already docked and charging"
    ctx.say("Going to the charging station.")
    h = yield from ctx.wait(ctx.hw.dock.dock(), timeout_s=150, what="docking")
    ctx.say("Charging: contacts closed, 48 V.")
    return h.message


# --------------------------------------------------------------------------------------- manipulation
@skill("pick", "Find an object with the Gemini camera and pick it", {"what": "object class (bottle)", "side": "right|left|auto"},
       requires_hands=("parallel",))
def pick(ctx: SkillContext, what: str = "bottle", side: Optional[str] = None, ref: Optional[str] = None) -> SkillGen:
    dets = ctx.hw.perception.detect(what)
    yield
    if ref:
        dets = [d for d in dets if d.ref == ref]
    if not dets:
        raise SkillError(f"no {what} found")
    if side in ("right", "left"):
        mine = [d for d in dets if _pick_side(ctx, d, None) == side] or dets
    else:
        mine = dets
    # outermost first: the forearm then passes over free space (same rule as v5's loader)
    det = max(mine, key=lambda d: abs(ctx.robot_frame(d.xy)[1]))
    s = _pick_side(ctx, det, side)
    if ctx.hw.grippers[s].status().holding:
        raise SkillError(f"{s} hand already holds something")
    traj = ctx.hw.planner.plan_pick(s, det)
    if traj is None:
        raise SkillError("no grasp plan")
    yield from ctx.wait(ctx.hw.arms[s].execute(traj), timeout_s=60, what=f"pick ({s})")
    if not ctx.hw.grippers[s].status().holding:
        raise SkillError(f"grasp failed ({s})")
    ctx.event(f"picked {det.label} with the {s} hand")
    return f"{s}:{det.ref or det.label}"


@skill("place", "Place the held object", {"where": "tray|bench|hole", "side": "right|left|auto", "slot": "tray slot"},
       requires_hands=("parallel",))
def place(ctx: SkillContext, where: str = "tray", side: Optional[str] = None, slot: Optional[int] = None,
          xy: Optional[tuple[float, float]] = None) -> SkillGen:
    sides = [side] if side in ("right", "left") else ["right", "left"]
    s = next((x for x in sides if ctx.hw.grippers[x].status().holding), None)
    if s is None:
        raise SkillError("nothing in hand to place")
    target: dict[str, Any]
    if where == "tray":
        if slot is None:
            free = [d for d in ctx.hw.perception.detect("tray_slot") if d.ref and d.ref.startswith(s)]
            if not free:
                raise SkillError(f"tray full on the {s} side")
            slot = min(int(d.ref.split(":")[1]) for d in free)
        target = {"kind": "tray", "slot": int(slot)}
    elif where == "hole":
        holes = ctx.hw.perception.detect("hole") if xy is None else [Detection("hole", tuple(xy))]
        yield
        holes = [h for h in holes if _pick_side(ctx, h, None) == s] or holes
        if not holes:
            raise SkillError("no free hole found")
        target = {"kind": "hole", "xy": min(holes, key=lambda h: abs(ctx.robot_frame(h.xy)[1])).xy}
    else:
        if xy is None:
            raise SkillError("bench placement needs xy")
        target = {"kind": "bench", "xy": tuple(xy)}
    traj = ctx.hw.planner.plan_place(s, target)
    if traj is None:
        raise SkillError("no place plan")
    yield from ctx.wait(ctx.hw.arms[s].execute(traj), timeout_s=60, what=f"place ({s})")
    if ctx.hw.grippers[s].status().holding:
        raise SkillError("object still in hand after place")
    return f"placed in {where}" + (f" slot {slot}" if where == "tray" else "")


@skill("sort", "Sort detected objects into destinations by class", {"rules": "label->tray|hole"}, requires_hands=("parallel",))
def sort(ctx: SkillContext, rules: Optional[dict[str, str]] = None, max_items: int = 4) -> SkillGen:
    rules = rules or {"bottle": "tray"}
    done = 0
    for label, dest in rules.items():
        while done < max_items:
            dets = ctx.hw.perception.detect(label)
            yield
            if not dets:
                break
            ref = (yield from pick(ctx, what=label))
            yield from place(ctx, where=dest, side=ref.split(":")[0])
            done += 1
    return f"sorted {done} objects"


@skill("load_tray", "At bench A: find the bottles and load them on the onboard tray (both arms)",
       requires_modules=("tray",), requires_hands=("parallel",), requires_choreo=True)
def load_tray(ctx: SkillContext) -> SkillGen:
    if ctx.hw.base.status().pose.dist(ctx.hw.world.resolve("A")) > 0.15:
        yield from navigate(ctx, "A")
    h = yield from ctx.wait(ctx.hw.choreo.run("load_tray"), timeout_s=240, what="load tray")
    return h.message


@skill("unload_tray", "At bench B: find free holes and insert the bottles on board",
       requires_modules=("tray",), requires_hands=("parallel",), requires_choreo=True)
def unload_tray(ctx: SkillContext) -> SkillGen:
    if ctx.hw.base.status().pose.dist(ctx.hw.world.resolve("B")) > 0.15:
        yield from navigate(ctx, "B")
    h = yield from ctx.wait(ctx.hw.choreo.run("unload_tray"), timeout_s=240, what="unload tray")
    return h.message


@skill("make_coffee", "Brew an espresso with the backpack capsule machine; ends with the cup in the right hand",
       requires_modules=("coffee",), requires_hands=("parallel",), requires_choreo=True)
def make_coffee(ctx: SkillContext) -> SkillGen:
    if ctx.hw.coffee is not None and not ctx.hw.coffee.status().ready:
        raise SkillError("coffee module busy")
    h = yield from ctx.wait(ctx.hw.choreo.run("make_coffee"), timeout_s=180, what="make coffee")
    return h.message


@skill("hand_over", "Bring the held cup to a person and hand it over", {"person": "name"},
       requires_modules=("coffee",), requires_hands=("parallel",), requires_choreo=True)
def hand_over(ctx: SkillContext, person: str = "Marco") -> SkillGen:
    if ctx.hw.world.resolve(person) is None:
        raise SkillError(f"I don't know {person}")
    if not ctx.hw.grippers["right"].status().holding:
        raise SkillError("no cup in hand - make a coffee first")
    h = yield from ctx.wait(ctx.hw.choreo.run("hand_over", person=person), timeout_s=180, what="hand over")
    return h.message


# --------------------------------------------------------------------------------------- social
@skill("wave", "Wave hello with a free arm", {"side": "right|left|auto"})
def wave(ctx: SkillContext, side: Optional[str] = None) -> SkillGen:
    s = side if side in ("right", "left") else _free_hand(ctx, "left")
    sg = 1 if s == "left" else -1
    ctx.hw.face.set_expression("happy", hold_s=4.0)
    ctx.say("Ciao!")
    plan = ctx.hw.planner
    up = plan.plan_to_point(s, (0.22, sg * 0.36, 1.30))
    yield from ctx.wait(ctx.hw.arms[s].execute(up), timeout_s=30, what="wave (raise)")
    for k in range(4):
        dy = 0.07 if k % 2 == 0 else -0.07
        t = plan.plan_to_point(s, (0.22, sg * 0.36 + dy, 1.32), duration_s=0.45)
        yield from ctx.wait(ctx.hw.arms[s].execute(t), timeout_s=10, what="wave")
    yield from ctx.wait(ctx.hw.arms[s].execute(plan.plan_home(s)), timeout_s=30, what="wave (home)")
    return f"waved with the {s} arm"


@skill("say", "Say a short sentence (face + speaker)", {"text": "sentence"})
def say(ctx: SkillContext, text: str = "Ciao!") -> SkillGen:
    ctx.say(text)
    yield from ctx.sleep(1.5)
    return "said"
