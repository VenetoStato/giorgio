# giorgio_os - architecture

One Python package runs Giorgio in two places:

* **sim**: against the existing MuJoCo simulation (`../giorgio_v5.py`), headless or with the web console;
* **real**: on the Jetson AGX Orin with ROS 2 (Humble now, Jazzy later), through drivers that wrap the vendor SDKs.

Everything above the HAL is the same code in both cases.

```
                         ┌──────────────────────────────────────────────────────────────┐
  Operator (browser) ───▶│  Operator console   ui/static (plain JS)  ◀─ FastAPI api/app  │
                         └───────────────┬──────────────────────────────────────────────┘
                                         │ commands are queued into the control thread
                                         ▼  (sim_server.SimServer)
 ┌───────────────────────────────────────────────────────────────────────────────────────┐
 │ GiorgioRuntime (runtime.py) - single control thread, 50 Hz, fixed order per tick:      │
 │                                                                                       │
 │  ① SafetySupervisor ──── reads scanners + PNOZ status ──▶ set_speed_scale(arms, base)  │
 │      (safety/)            deterministic, NO AI inputs, fail-safe on stale data         │
 │  ② software-stop latch ─▶ cancels tasks                                                │
 │  ③ EnergyManager ──────▶ queues dock_charge / aborts on critical SoC (energy/)         │
 │  ④ TaskManager ────────▶ ticks one Skill generator (mission/, skills/)                 │
 │  ⑤ hw.advance(dt) ─────▶ sim: physics step · real: no-op                               │
 │                                                                                       │
 │  GiorgioAgent (agent/) ─▶ LocalRouter (regex, EN/IT) → plan of SkillCalls               │
 │                           optional ClaudePlanner (OFF by default) → same SkillCalls     │
 │                           plans are validated by TaskManager like any operator task      │
 └───────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │ only through HAL interfaces (hal/interfaces.py)
 ┌───────────────────────────────────────▼───────────────────────────────────────────────┐
 │ HAL: one driver per device + services                                                  │
 │  BaseDriver  DockDriver  ArmDriver×2  GripperDriver×2  SafetyScannerDriver×2            │
 │  SafetyRelayDriver  CameraDriver×n  BatteryDriver  FaceDriver  CoffeeModuleDriver       │
 │  services: MotionPlanner · Perception · WorldModel · Choreographies (sim only for now)  │
 ├───────────────────────────────────────────┬──────────────────────────────────────────┤
 │ hal/sim  (implemented)                     │ hal/real  (stubs, name the exact SDK)     │
 │  SimEngine: exec giorgio_v5.py up to its   │  TracerBase   ugv_sdk/tracer_ros2, Nav2    │
 │  main loop, own control step, renderers    │  OpenArm      openarm_can/openarm_ros2     │
 │  drivers → v5 globals (arms, BAT, FIELDS)  │  NanoScan3    sick_safetyscanners2         │
 │  planner → v5 Arm.pick/place/jmove/clash   │  PnozRelay    GPIO opto / Modbus TCP       │
 │  perception → v5 Vision (Gemini RGB-D)     │  OrbbecCamera OrbbecSDK_ROS2               │
 │  choreo → v5 Skill (coffee, hand-over,     │  CanBms       python-can + Victron frames  │
 │           tray load/unload, docking)       │  NavDock      opennav_docking              │
 │                                            │  Hub75Face    ESP32-S3 over USB serial     │
 │                                            │  CoffeeMcu    micro-ROS RP2040/ESP32        │
 │                                            │  MoveItPlanner pymoveit2 / MoveGroup       │
 └───────────────────────────────────────────┴──────────────────────────────────────────┘

 Safety-rated layer (outside software, PL d):  nanoScan3 OSSDs ─▶ PNOZmulti 2 ─▶ Tracer drive enable,
                                                E-stop ─────────┘                 arm-bus DC contactors
```

## Layers

### HAL (`giorgio_os/hal`)
`interfaces.py` defines one abstract driver per device and four services. Rules:

* long operations return an `ActionHandle` (ROS 2 action semantics: pending → running → succeeded/failed/canceled);
* `set_speed_scale()` is called **only** by the safety supervisor;
* the safety relay and scanners are read-only, except selecting the scanner's monitoring case (as on the real device);
* drivers have no mission logic.

**sim backend** (`hal/sim`). `giorgio_v5.py` is a script with argparse, global state and a main loop, so it cannot be imported. `SimEngine` executes its source up to the `# ---- uscite` marker in a private namespace (the same technique as `giorgio_sort.py`), then:

* replaces `control_step` with its own `_physics_step` (same order of operations; the speed scaling comes from our supervisor; base and arm scaling are separate);
* replaces `log`, `ag_say` (forwarded to the event log, translated to English) and `system2` (no `claude` CLI calls from the sim);
* hosts one "base action" at a time (navigation, docking or a v5 choreography) and watchers that complete `ActionHandle`s.

Physics, scene, IK, the clash-aware planner, people, vision, the energy model and docking control are v5's, unchanged.

**real backend** (`hal/real`). Constructible without hardware; each method raises `NotBroughtUp` with the SDK it will use. ROS 2 access goes through one `RosBridge` (single node + executor thread).

### Safety supervisor (`safety/supervisor.py`)
Non-safety-rated software layer *on top of* the hardware safety chain. Inputs: the scanners' own field flags (the nanoScan3 evaluates its fields internally), relay status and data age. Output: arm and base speed scales.

| Condition | Arms | Base |
|---|---|---|
| clear field | 100% | 100% |
| warning field interrupted | 30% | 30% |
| protective field / E-stop / relay reset pending / stale or missing data | 0 (0.3 s ramp) | 0 |
| software STOP (operator console) | 0 until RESET | 0 |

Speed drops immediately and only goes back up after `clear_hold_s` (1 s) of clear data. The supervisor starts in stop. Field sizes follow ISO 13855: S = 1600 mm/s × 0.37 s + 1128 mm = 1.72 m (stationary case). Skills and the agent get no reference to the supervisor.

### Skills (`skills/`)
Skills are Python generators: `run(ctx, **args)` yields once per tick while waiting on device actions and returns a result string. `SkillError` fails the skill; cancelling closes the generator and cancels every action it started. Each `SkillSpec` declares what it needs: config modules (`coffee`, `tray`), end-effector type (`parallel`) or a choreography. The UI and the task manager use that to grey out or refuse skills.

| Skill | Built on | Sim | Real |
|---|---|---|---|
| navigate | BaseDriver.navigate_to + WorldModel | ✅ v5 A* + pure pursuit | stub → Nav2 |
| dock_charge | DockDriver.dock | ✅ v5 closed-loop docking, contacts | stub → opennav_docking |
| pick / place | Perception + MotionPlanner + ArmDriver | ✅ v5 vision + IK/clash planner | stub → MoveIt 2 |
| sort | pick + place in a loop | ✅ (no dedicated test) | follows pick/place |
| wave, say | MotionPlanner, FaceDriver | ✅ | follows planner/face |
| load_tray / unload_tray / make_coffee / hand_over | Choreographies | ✅ v5 routines unchanged | ❌ unavailable until rebuilt from primitives |

### Mission manager (`mission/manager.py`)
A task is a sequence of skill calls with a priority and a source (operator, `agent:router`, `agent:claude`, `energy`). One task runs at a time; the queue is priority-ordered. Energy guards can insert `dock_charge` before a hungry skill ("charge first, then coffee"). The software stop cancels the running task and keeps the queue until RESET. It is a deliberately small state machine (IDLE / RUNNING / STOPPED). A task is already a Sequence node, so moving to py_trees or BehaviorTree.CPP later is mechanical.

### Energy manager (`energy/manager.py`)
SoC < 30% and idle → queue `dock_charge` (priority 10). SoC < 15% → abort the current task, emergency charge (priority 100). Coffee (1.3 kW heater) below 20% and not docked → charge first. Thresholds are in the YAML.

### Agent (`agent/agent.py`)
* **LocalRouter**: regex rules in English and Italian, under 1 ms, offline. Compound or conditional requests ("then", "if", "poi", "se") go to the planner.
* **ClaudePlanner**: optional (`agent.llm_enabled: true`, `pip install anthropic`, an API key). It uses structured output constrained to the enum of available skills. Its plan goes through the same validation as an operator task and it never sees drivers or safety. With the LLM off, unknown requests get a help message.

### Config (`configs/*.yaml`)
`barista`, `logistics`, `dexterous`, `lowcost`. Each lists the fitted modules, offered skills, named locations, safety/energy parameters, the sim options and the real-robot wiring (CAN interfaces, IPs, topics, serial ports).

### Operator console (`api/`, `ui/static/`)
FastAPI serves a single static page (plain JS, no build step). It polls `/api/status` at 4 Hz and fetches camera JPEGs at about 7 Hz. Rendering happens in the control thread (EGL context), only for cameras a client asked for in the last 3 s. Endpoints:

| Method | Path | |
|---|---|---|
| GET | `/api/health`, `/api/status`, `/api/configs`, `/api/skills`, `/api/tasks` | read |
| POST | `/api/tasks` `{skill, args}` · DELETE `/api/tasks/{id}` | queue / cancel |
| POST | `/api/chat` `{text}` | agent |
| POST | `/api/estop` · `/api/reset` | software stop (**not safety-rated**) |
| POST | `/api/config` `{name}` | rebuild the robot with another configuration |
| GET | `/api/camera/{name}.jpg` | chase, top, gemini, gemini_overlay, wrist_right, wrist_left, pano |
| POST | `/api/sim/person`, `/api/sim/battery`, `/api/sim/hw_estop` | sim-only test inputs |

### Threading
One control thread owns the runtime (and, in sim, the MuJoCo EGL context). HTTP handlers read a snapshot published at 10 Hz, or submit callables through a queue; the control thread runs them between ticks. On the real robot the ROS 2 executor lives in `RosBridge`'s thread, and drivers only touch cached messages and action clients, so a tick never blocks on DDS.

## Mapping to ROS 2 on the robot (target)

```
giorgio_os (this package, one node "giorgio_os")
 ├─ /cmd_vel via twist_mux + speed filter   ◀ TracerBase        tracer_ros2 (CAN0 500k)
 ├─ NavigateToPose, /speed_limit            ◀ TracerBase        nav2 (map, AMCL/SLAM on scanner data)
 ├─ DockRobot / UndockRobot                 ◀ NavDock           opennav_docking (+ BMS current)
 ├─ FollowJointTrajectory ×2, GripperCommand◀ OpenArm/Gripper   openarm_ros2 + ros2_control (CAN-FD ×2)
 ├─ MoveGroup / compute_cartesian_path      ◀ MoveItPlanner     openarm_bimanual_moveit_config
 ├─ /scan_front /scan_rear + raw_data       ◀ NanoScan3         sick_safetyscanners2 (UDP)
 ├─ /camera/gemini/*                        ◀ OrbbecCamera      OrbbecSDK_ROS2
 ├─ /battery_state                          ◀ CanBms            small python-can node (CAN3)
 ├─ /coffee/{shuttle,brew,status}           ◀ CoffeeMcu         micro-ROS agent (serial)
 └─ GPIO / Modbus TCP                       ◀ PnozRelay         libgpiod / pymodbus
```
