// Giorgio operator console - plain JS, no build step.
"use strict";
const $ = (id) => document.getElementById(id);
const api = async (path, opts = {}) => {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  const body = r.headers.get("content-type")?.includes("json") ? await r.json() : null;
  if (!r.ok) throw new Error(body?.detail || r.statusText);
  return body;
};
const post = (path, data) => api(path, { method: "POST", body: JSON.stringify(data || {}) });
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let S = null;            // latest status
let cam = new URLSearchParams(location.search).get("cam") || "chase";
let lastChatLen = -1;

// ------------------------------------------------------------------ curated commands
const COMMANDS = [
  { label: "Make coffee", hint: "for Marco", needs: ["make_coffee", "hand_over"], chat: "make a coffee for Marco" },
  { label: "Load tray", hint: "bench A, both arms", needs: ["load_tray"], task: { skill: "load_tray" } },
  { label: "Unload at B", hint: "insert bottles", needs: ["unload_tray"], task: { skill: "unload_tray" } },
  { label: "Pick bottle", hint: "Gemini + right arm", needs: ["pick"], task: { skill: "pick", args: { what: "bottle", side: "right" } } },
  { label: "Place in tray", hint: "held object", needs: ["place"], task: { skill: "place", args: { where: "tray" } } },
  { label: "Go to A", hint: "kitting bench", needs: ["navigate"], task: { skill: "navigate", args: { target: "A" } } },
  { label: "Go to B", hint: "insertion bench", needs: ["navigate"], task: { skill: "navigate", args: { target: "B" } } },
  { label: "Dock & charge", hint: "station C", needs: ["dock_charge"], task: { skill: "dock_charge" } },
  { label: "Wave", hint: "say ciao", needs: ["wave"], task: { skill: "wave" } },
  { label: "Sort", hint: "bottles -> tray", needs: ["sort"], task: { skill: "sort" } },
];

function buildCommands() {
  const box = $("cmds");
  box.innerHTML = "";
  const avail = new Map((S?.skills || []).map((s) => [s.name, s]));
  for (const c of COMMANDS) {
    const b = document.createElement("button");
    const missing = c.needs.map((n) => avail.get(n)).find((s) => !s || !s.available);
    b.innerHTML = `${esc(c.label)}<small>${esc(missing ? (missing.why || "unavailable") : c.hint)}</small>`;
    b.disabled = !!missing;
    b.title = missing ? missing.why : c.hint;
    b.onclick = async () => {
      try {
        if (c.chat) await sendChat(c.chat);
        else await post("/api/tasks", c.task);
      } catch (e) { toast(e.message); }
    };
    box.appendChild(b);
  }
}

// ------------------------------------------------------------------ camera
function buildTabs() {
  const tabs = $("camTabs");
  tabs.innerHTML = "";
  const names = [...(S?.cameras || []), "gemini_overlay"];
  const label = { chase: "chase", top: "map", gemini: "gemini", gemini_overlay: "vision", wrist_right: "wrist R", wrist_left: "wrist L", pano: "360" };
  for (const n of names) {
    const b = document.createElement("button");
    b.textContent = label[n] || n;
    b.className = n === cam ? "on" : "";
    b.onclick = () => { cam = n; $("cam").hidden = true; $("nosig").hidden = false; buildTabs(); };
    tabs.appendChild(b);
  }
}
let camBusy = false;
function pollCam() {
  if (camBusy) return;
  camBusy = true;
  const img = new Image();
  img.onload = () => { $("cam").src = img.src; $("cam").hidden = false; $("nosig").hidden = true; camBusy = false; };
  img.onerror = () => { camBusy = false; };   // 204 = no frame yet: keep the last one
  img.src = `/api/camera/${cam}.jpg?t=${Date.now()}`;
}

// ------------------------------------------------------------------ LED face (32x16)
const FW = 32, FH = 16;
function drawFace(f) {
  const c = $("face"), g = c.getContext("2d");
  const px = c.width / FW;
  const col = f?.color ? `rgb(${f.color.join(",")})` : "#6fc3ff";
  const on = new Set();
  const set = (x, y) => { if (x >= 0 && x < FW && y >= 0 && y < FH) on.add(x + "," + y); };
  const rect = (x, y, w, h) => { for (let i = 0; i < w; i++) for (let j = 0; j < h; j++) set(x + i, y + j); };
  const e = f?.expression || "neutral";
  const gx = Math.round((f?.gaze?.[0] || 0) * 2), gy = -Math.round((f?.gaze?.[1] || 0) * 1.5);
  const blink = (f?.blink || 0) > 0.5;
  const eyes = [[7, 3], [21, 3]];
  for (const [ex0, ey0] of eyes) {
    const ex = ex0 + gx, ey = ey0 + gy;
    if (e === "stop") { for (let k = 0; k < 5; k++) { set(ex + k, ey + k); set(ex + 4 - k, ey + k); } }
    else if (e === "happy" || e === "wave") { set(ex, ey + 3); set(ex + 1, ey + 2); set(ex + 2, ey + 1); set(ex + 3, ey + 2); set(ex + 4, ey + 3); }
    else if (e === "love") { rect(ex, ey + 1, 2, 2); rect(ex + 3, ey + 1, 2, 2); rect(ex, ey + 2, 5, 1); rect(ex + 1, ey + 3, 3, 1); set(ex + 2, ey + 4); }
    else if (e === "charging" || blink) { rect(ex, ey + 3, 5, 1); }
    else if (e === "attentive") { rect(ex, ey, 5, 5); }
    else if (e === "thinking") { rect(ex + 1, ey, 3, 3); }
    else { rect(ex + 1, ey, 3, 5); rect(ex, ey + 1, 5, 3); }
  }
  // the moustache (Giorgio's trademark): up when happy, down when stopped
  const mood = e === "stop" ? -1 : (e === "happy" || e === "love" || e === "coffee" || e === "wave") ? 1 : 0;
  const my = 11;
  for (let i = 0; i < 6; i++) { set(15 - i, my + (i > 3 ? -mood : 0)); set(16 + i, my + (i > 3 ? -mood : 0)); }
  rect(12, my + 1, 8, 1);
  set(9, my - mood * 2); set(22, my - mood * 2);
  if (e === "thinking") { set(26, 2); set(28, 1); set(30, 0); }
  if (e === "coffee") { rect(26, 12, 4, 3); set(30, 13); set(27, 10); set(28, 9); }
  if (e === "charging") { set(28, 0); set(27, 1); set(28, 1); set(29, 1); set(28, 2); }
  g.fillStyle = "#040505"; g.fillRect(0, 0, c.width, c.height);
  for (let y = 0; y < FH; y++) for (let x = 0; x < FW; x++) {
    const lit = on.has(x + "," + y);
    g.fillStyle = lit ? col : "#101315";
    g.beginPath(); g.arc(x * px + px / 2, y * px + px / 2, px * (lit ? 0.42 : 0.3), 0, 2 * Math.PI); g.fill();
  }
  $("faceExpr").textContent = e;
}

// ------------------------------------------------------------------ radar (robot frame, x forward = up)
function drawRadar(s) {
  const c = $("radar"), g = c.getContext("2d"), W = c.width, H = c.height;
  const sc = W / 7.4, cx = W / 2, cy = H / 2;
  const P = (x, y) => [cx - y * sc, cy - x * sc];
  g.fillStyle = "#050606"; g.fillRect(0, 0, W, H);
  g.strokeStyle = "#15191c"; g.lineWidth = 1;
  for (let r = 1; r <= 3; r++) { g.beginPath(); g.arc(cx, cy, r * sc, 0, 2 * Math.PI); g.stroke(); }
  g.beginPath(); g.moveTo(cx, 0); g.lineTo(cx, H); g.moveTo(0, cy); g.lineTo(W, cy); g.stroke();
  const sf = s.safety, zone = sf.zone;
  const ring = (r, color, hot) => { g.setLineDash(hot ? [] : [4, 4]); g.strokeStyle = color; g.lineWidth = hot ? 2 : 1.2;
    g.beginPath(); g.arc(cx, cy, r * sc, 0, 2 * Math.PI); g.stroke(); g.setLineDash([]); };
  ring(sf.warning_r, zone === "WARNING" || zone === "PROTECTIVE" ? "#ffb547" : "#5a4a1e", zone === "WARNING");
  ring(sf.protective_r, zone === "PROTECTIVE" ? "#ff4b3e" : "#5a2320", zone === "PROTECTIVE");
  for (const [x, y] of sf.scan || []) {
    const d = Math.hypot(x, y);
    g.fillStyle = d < sf.protective_r ? "#ff4b3e" : d < sf.warning_r ? "#ffb547" : "#7d858c";
    const [u, v] = P(x, y); g.fillRect(u - 1, v - 1, 2, 2);
  }
  if (s.sim?.people) {   // ground-truth people (sim only)
    const b = s.base, c0 = Math.cos(b.theta), s0 = Math.sin(b.theta);
    for (const [wx, wy] of s.sim.people) {
      const dx = wx - b.x, dy = wy - b.y, x = c0 * dx + s0 * dy, y = -s0 * dx + c0 * dy;
      const [u, v] = P(x, y);
      if (u < 0 || v < 0 || u > W || v > H) continue;
      g.strokeStyle = "#6fc3ff"; g.strokeRect(u - 4, v - 4, 8, 8);
    }
  }
  // footprint 0.70 x 0.61
  const [x0, y0] = P(0.35, 0.305);
  g.strokeStyle = "#e8ebe6"; g.lineWidth = 1.5; g.strokeRect(x0, y0, 0.61 * sc, 0.70 * sc);
  g.fillStyle = "#c9f26b"; g.beginPath(); const [tx, ty] = P(0.42, 0); g.moveTo(tx, ty - 3); g.lineTo(tx - 5, ty + 5); g.lineTo(tx + 5, ty + 5); g.fill();
  g.fillStyle = "#4b5258"; g.font = "10px ui-monospace, monospace"; g.fillText("1 m", cx + sc + 3, cy - 3);
}

// ------------------------------------------------------------------ render status
function fmtT(t) { const m = Math.floor(t / 60), s = (t % 60).toFixed(1).padStart(4, "0"); return `T+${m}:${s}`; }

function render(s) {
  S = s;
  if (s.booting) { $("modeText").textContent = "BOOTING"; return; }
  const ban = $("banner");
  if (s.error) { ban.hidden = false; ban.textContent = s.error; } else ban.hidden = true;
  if (!s.safety) return;
  const zone = s.safety.zone;
  const m = $("mode");
  m.className = "mode " + (s.mode === "software stop" || zone === "PROTECTIVE" ? "m-stop" : zone === "WARNING" ? "m-warn" : "");
  $("modeText").textContent = s.mode;
  $("clock").textContent = fmtT(s.t);
  $("backend").textContent = s.backend.toUpperCase();
  $("backend").className = "badge " + (s.backend === "real" ? "real" : "");

  // power
  const b = s.battery, pct = Math.round(b.soc * 100);
  $("batPct").textContent = pct;
  $("batFill").style.width = pct + "%";
  $("batFill").style.background = b.soc < 0.15 ? "var(--red)" : b.soc < 0.3 ? "var(--amber)" : "var(--accent)";
  $("batV").textContent = `${b.voltage.toFixed(1)} V  ${b.current.toFixed(1)} A`;
  $("batW").textContent = `${Math.round(b.power)} W`;
  $("batState").textContent = b.charging ? "CHARGING" : "DISCHARGING";
  $("batAut").textContent = `${b.autonomy_h} h`;
  $("dock").textContent = s.dock.contacts_closed ? "CONTACTS CLOSED" : s.dock.docked ? "DOCKED" : "UNDOCKED";

  // safety
  const sf = s.safety;
  $("zone").textContent = zone === "PROTECTIVE" ? "STOP" : zone === "WARNING" ? "SLOW 30%" : "CLEAR";
  $("zone").className = "zone " + zone;
  $("zoneReason").textContent = sf.reason === "clear" ? `arms ${Math.round(sf.arm_scale * 100)}%  base ${Math.round(sf.base_scale * 100)}%`
    : `${sf.reason}`;
  $("fieldCase").textContent = `case: ${sf.field_case}`;
  const rl = sf.relay;
  $("relay").innerHTML = [["E-STOP CHAIN", rl.estop_ok], ["OSSD", rl.scanners_ok], ["DRIVES", rl.drives_enabled], ["ARM POWER", rl.arm_power],
    ["RESET", !rl.reset_required]].map(([n, ok]) => `<span class="chip ${ok ? "ok" : "bad"}">${n}</span>`).join("");
  $("safetyFoot").textContent = `ISO 13855 S = ${sf.iso13855_s_m} m · stops ${sf.stops} · slow-downs ${sf.slowdowns}`;
  drawRadar(s);
  drawFace(s.face);
  $("say").textContent = s.say || "";
  const cz = $("camZone"); cz.className = "cam-zone " + zone;
  cz.textContent = zone === "PROTECTIVE" ? "STOP - PERSON IN PROTECTIVE FIELD" : zone === "WARNING" ? "SLOW - PERSON NEARBY" : "";
  if (s.mode === "software stop") { cz.className = "cam-zone PROTECTIVE"; cz.textContent = "SOFTWARE STOP"; }

  // HUD
  const cur = s.mission.current;
  $("hud").textContent = [`POS  ${s.base.x.toFixed(2)} ${s.base.y.toFixed(2)}  ${(s.base.theta * 57.3).toFixed(0)}°`,
    `V    ${s.base.v.toFixed(2)} m/s  x${s.base.speed_scale.toFixed(2)}`,
    `ARMS x${sf.arm_scale.toFixed(2)}`,
    `TASK ${cur ? cur.skill || cur.title : "-"}`].join("\n");
  $("camInfo").textContent = s.sim ? `on board ${s.sim.onboard} · inserted ${s.sim.inserted}` : "";

  // mission
  $("mState").textContent = s.mission.state;
  if (cur) {
    $("current").innerHTML = `<div class="title">${esc(cur.title)}</div>
      <div class="meta">#${cur.id} · ${esc(cur.source)} · ${esc(cur.skill || "")} · ${cur.skill_elapsed ?? 0}s</div>
      <ol class="steps">${cur.steps.map((st, i) => `<li class="${i < cur.step ? "done" : i === cur.step ? "now" : ""}">${esc(st)}</li>`).join("")}</ol>`;
  } else {
    $("current").innerHTML = `<div class="empty">${s.mode === "software stop" ? "Stopped. Press RESET when the area is clear." : "Nothing to do. Giorgio is enjoying the moment."}</div>`;
  }
  $("qCount").textContent = s.mission.queue.length;
  $("queue").innerHTML = s.mission.queue.map((t) => `<li><span class="id">#${t.id}</span>${esc(t.title)}<span class="src">${esc(t.source)}</span>
      <button class="x" title="cancel" data-cancel="${t.id}">&times;</button></li>`).join("") || `<li class="empty" style="border:0;padding:0">Queue empty</li>`;
  $("history").innerHTML = s.mission.history.map((t) => `<li class="${t.status}"><div><span class="id">#${t.id}</span> ${esc(t.title)}
      <span class="msg">${esc(t.message)}</span></div><span class="st" style="margin-left:auto">${t.status}</span></li>`).join("");

  // chat
  if (s.chat.length !== lastChatLen) {
    lastChatLen = s.chat.length;
    $("chat").innerHTML = s.chat.map((c) => c.who === "user" ? `<li class="user">${esc(c.text)}</li>`
      : `<li class="giorgio">${esc(c.text)}<span class="meta">${esc(c.engine)}${c.latency_ms ? " · " + c.latency_ms + " ms" : ""}${c.plan?.length ? " · " + esc(c.plan.join(" → ")) : ""}</span></li>`).join("");
    $("chat").scrollTop = 1e9;
  }
  $("llm").textContent = s.llm_enabled ? "router + claude" : "local router";

  // log
  const ev = s.events.slice().reverse();
  $("evCount").textContent = ev.length;
  $("log").innerHTML = ev.map((e) => `<li><span class="t">${e.t.toFixed(1)}</span><span class="k k-${e.kind}">${esc(e.kind)}</span><span>${esc(e.text)}</span></li>`).join("");

  $("simCard").style.display = s.backend === "sim" ? "" : "none";
}

// ------------------------------------------------------------------ actions
function toast(msg) { const b = $("banner"); b.hidden = false; b.textContent = msg; setTimeout(() => { if (!S?.error) b.hidden = true; }, 4000); }
async function sendChat(text) { await post("/api/chat", { text }); lastChatLen = -1; }

$("chatForm").onsubmit = async (e) => {
  e.preventDefault();
  const t = $("chatText").value.trim(); if (!t) return;
  $("chatText").value = "";
  try { await sendChat(t); } catch (err) { toast(err.message); }
};
$("stop").onclick = () => post("/api/estop").catch((e) => toast(e.message));
$("reset").onclick = async () => { try { const r = await post("/api/reset"); if (!r.ok) toast(r.reason); } catch (e) { toast(e.message); } };
$("queue").onclick = (e) => { const id = e.target?.dataset?.cancel; if (id) api(`/api/tasks/${id}`, { method: "DELETE" }).catch((er) => toast(er.message)); };
document.querySelectorAll("[data-sim]").forEach((b) => b.onclick = async () => {
  const k = b.dataset.sim;
  try {
    if (k === "person") await post("/api/sim/person");
    if (k === "bat25") await post("/api/sim/battery", { soc: 0.25 });
    if (k === "bat90") await post("/api/sim/battery", { soc: 0.9 });
    if (k === "hwon") await post("/api/sim/hw_estop", { pressed: true });
    if (k === "hwoff") await post("/api/sim/hw_estop", { pressed: false });
  } catch (e) { toast(e.message); }
});
$("config").onchange = async (e) => {
  const name = e.target.value;
  $("modeText").textContent = "RECONFIGURING";
  try { await post("/api/config", { name }); skillsKey = ""; } catch (err) { toast(err.message); }
};

async function loadConfigs() {
  const c = await api("/api/configs");
  $("config").innerHTML = c.configs.map((x) => `<option value="${x.name}" ${x.name === c.current ? "selected" : ""} title="${esc(x.description)}">${esc(x.title)}</option>`).join("");
}

let skillsKey = "";
async function poll() {
  try {
    const s = await api("/api/status");
    render(s);
    const key = JSON.stringify([s.config?.name, (s.skills || []).map((x) => x.available), s.cameras]);
    if (key !== skillsKey) { skillsKey = key; buildCommands(); buildTabs(); loadConfigs(); }
  } catch (e) { $("modeText").textContent = "LINK LOST"; $("mode").className = "mode m-stop"; }
}
setInterval(poll, 250);
setInterval(pollCam, 140);
poll();
