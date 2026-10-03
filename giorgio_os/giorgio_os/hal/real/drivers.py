"""Real-robot driver STUBS.

Every class documents the exact SDK / ROS 2 interface it will wrap. None of them talks to hardware
yet: methods raise :class:`NotImplementedError` with a pointer to the bring-up step in the README
roadmap. Construction is side-effect free, so the full stack (runtime, API, UI) can be started with
``--backend real`` on a laptop to check wiring/config without hardware.

ROS 2 is accessed through ``rclpy`` from a single executor thread owned by
:class:`RosBridge`; drivers only touch cached messages and action clients, so the giorgio_os
control loop never blocks on DDS.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

from ...types import (ActionHandle, ArmStatus, BaseStatus, BatteryStatus, CoffeeStatus, DockStatus, GripperStatus,
                      Pose2D, RelayStatus, ScanFrame)
from ..interfaces import (ArmDriver, BaseDriver, BatteryDriver, CameraDriver, CoffeeModuleDriver, DockDriver, FaceDriver,
                          GripperDriver, SafetyRelayDriver, SafetyScannerDriver, Trajectory)


class NotBroughtUp(NotImplementedError):
    pass


class RosBridge:
    """Owns rclpy init, one node ('giorgio_os') and a MultiThreadedExecutor spinning in a thread.

    TODO(bring-up step 1): ``rclpy.init(domain_id=cfg.real['ros_domain_id'])``; create node; start executor thread.
    """

    def __init__(self, cfg: dict[str, Any]):
        self.cfg = cfg
        self.node = None            # rclpy.node.Node once started

    def start(self) -> None:
        raise NotBroughtUp("RosBridge.start: rclpy not wired yet (README roadmap, step 1)")


class _Real:
    backend = "real"
    SDK = ""

    def __init__(self, name: str, cfg: dict[str, Any], ros: RosBridge):
        self.name, self.cfg, self.ros = name, cfg, ros

    def _todo(self, what: str):
        raise NotBroughtUp(f"{type(self).__name__}.{what}: not implemented - will use {self.SDK}")

    def healthy(self) -> bool:
        return False

    def info(self) -> dict[str, Any]:
        return {"name": self.name, "backend": "real", "healthy": False, "sdk": self.SDK, "cfg": self.cfg}


class TracerBase(_Real, BaseDriver):
    """AgileX Tracer 2.0 over CAN 2.0B @500 kbit/s (``can0``, SocketCAN on the Orin MTTCAN controller).

    SDK: ``agilexrobotics/ugv_sdk`` (C++, Apache-2.0) via ``agilexrobotics/tracer_ros2`` node.
    Topics: sub ``/odom`` (nav_msgs/Odometry), ``/tracer_status`` (tracer_msgs/TracerStatus);
            pub ``/cmd_vel`` (geometry_msgs/Twist) - only through the ``twist_mux`` + speed-scale filter node.
    Navigation: Nav2 action ``/navigate_to_pose`` (nav2_msgs/action/NavigateToPose).
    Speed scale: Nav2 ``/speed_limit`` (nav2_msgs/SpeedLimit, percentage=True) AND a cmd_vel scaling filter,
    so the scale also applies to teleop / docking controllers.
    """

    SDK = "ugv_sdk + tracer_ros2 (CAN0 500k), Nav2 NavigateToPose, /speed_limit"

    def status(self) -> BaseStatus:
        self._todo("status")

    def navigate_to(self, goal: Pose2D) -> ActionHandle:
        self._todo("navigate_to")

    def stop(self) -> None:
        self._todo("stop")

    def set_speed_scale(self, k: float) -> None:
        self._todo("set_speed_scale")


class NavDock(_Real, DockDriver):
    """Nav2 docking server: ``opennav_docking`` (Apache-2.0; humble branch / part of Nav2 from Jazzy).

    Actions: ``/dock_robot`` (opennav_docking_msgs/action/DockRobot, dock_id from YAML database),
             ``/undock_robot``. Dock pose detection: laser-profile ICP on the station plate or AprilTag on the
    Gemini; charge confirmation from the BMS current sign + contact voltage (ADC on the coffee/face MCU).
    """

    SDK = "opennav_docking DockRobot/UndockRobot + BMS charge current"

    def dock(self, dock_id: str = "home") -> ActionHandle:
        self._todo("dock")

    def undock(self) -> ActionHandle:
        self._todo("undock")

    def status(self) -> DockStatus:
        self._todo("status")


class OpenArm(_Real, ArmDriver):
    """Enactic OpenArm 2.0, 7x Damiao DM-J motors per arm on CAN-FD (1 Mbit/s nominal / 5 Mbit/s data).

    SDK: ``enactic/openarm_can`` (C++/Python, Apache-2.0, SocketCAN) under ``enactic/openarm_ros2``
    (ros2_control hardware interface). Controllers: ``/{side}_joint_trajectory_controller/follow_joint_trajectory``
    (control_msgs/action/FollowJointTrajectory); state ``/joint_states``.
    Speed scale: ``scaled_joint_trajectory_controller`` speed-scaling interface (or trajectory time re-scaling here).
    Stop: ``stop()`` = hold position via controller (SS2-like); power cut is done by the PNOZ, not by us.
    One CAN-FD interface per arm (can1 / can2) - see FEASIBILITY.md for adapter choice.
    """

    SDK = "openarm_can + openarm_ros2 (ros2_control), FollowJointTrajectory, CAN-FD"

    def __init__(self, name: str, cfg: dict[str, Any], ros: RosBridge, side: str):
        super().__init__(name, cfg, ros)
        self.side = side

    def status(self) -> ArmStatus:
        self._todo("status")

    def execute(self, traj: Trajectory) -> ActionHandle:
        self._todo("execute")

    def stop(self) -> None:
        self._todo("stop")

    def set_speed_scale(self, k: float) -> None:
        self._todo("set_speed_scale")


class OpenArmGripper(_Real, GripperDriver):
    """OpenArm parallel gripper (8th Damiao motor on the arm's CAN-FD bus).

    ROS 2: ``/{side}_gripper_controller/gripper_cmd`` (control_msgs/action/GripperCommand) from openarm_ros2.
    """

    SDK = "openarm_ros2 GripperCommand"
    kind = "parallel"

    def __init__(self, name: str, cfg: dict[str, Any], ros: RosBridge, side: str):
        super().__init__(name, cfg, ros)
        self.side = side

    def status(self) -> GripperStatus:
        self._todo("status")

    def command(self, opening: float, effort: float = 0.5) -> ActionHandle:
        self._todo("command")


class OrcaHand(OpenArmGripper):
    """ORCA Hand v2 - ``orcahand/orca_core`` (Python, MIT) over USB (Dynamixel/Feetech bus). No ROS 2 package:
    we wrap orca_core in a small ros2_control-free node publishing ``/{side}_hand/joint_states`` and accepting a
    synergy command. Grasping requires a learned policy (see ~/giorgio_sim/rl_mani)."""

    SDK = "orca_core (Python, MIT) over USB serial"
    kind = "orca"


class AmazingHand(OpenArmGripper):
    """Pollen Robotics AmazingHand - Python/Rust examples (Apache-2.0), 8x Feetech SCS0009 servos over a
    serial bus adapter. Wrapped like OrcaHand."""

    SDK = "AmazingHand python (Feetech SCS serial bus)"
    kind = "amazing"


class NanoScan3(_Real, SafetyScannerDriver):
    """SICK nanoScan3 (Pro I/O recommended) - ``SICKAG/sick_safetyscanners2`` (C++, Apache-2.0), UDP data output.

    Topics: ``/scan_front`` | ``/scan_rear`` (sensor_msgs/LaserScan), ``.../raw_data`` (sick_safetyscanners2_interfaces/RawMicroScanData)
    with ``general_system_state`` + ``intrusion_data`` -> protective / warning flags.
    Field cases: switched by the PNOZ/static control inputs or, on Pro I/O, by speed (encoder inputs);
    ``set_field_case`` only *requests* a case through a non-safe output - the scanner remains the authority.
    Field sets are designed and signed in SICK Safety Designer (Windows), not in this code.
    """

    SDK = "sick_safetyscanners2 (UDP), Safety Designer for field sets"

    def read(self) -> ScanFrame:
        self._todo("read")

    def set_field_case(self, case: str) -> None:
        self._todo("set_field_case")


class PnozRelay(_Real, SafetyRelayDriver):
    """Pilz PNOZmulti 2 (PNOZ m B0/B1). No SDK: program written in PNOZmulti Configurator (Windows, licence).

    Read-back options (both read-only):
      1. semiconductor outputs -> opto-isolated -> Jetson 40-pin GPIO, read with ``python3-libgpiod`` (cfg.relay.inputs);
      2. Modbus/TCP from a PNOZ m ES ETH module or the B1 base unit (``pymodbus``), virtual outputs mapped to registers.
    """

    SDK = "libgpiod (opto-isolated PNOZ semiconductor outputs) / Modbus TCP via PNOZ m ES ETH"

    def status(self) -> RelayStatus:
        self._todo("status")


class OrbbecCamera(_Real, CameraDriver):
    """Orbbec Gemini 336L - ``orbbec/OrbbecSDK_ROS2`` (v2 branch, Apache-2.0 wrapper over OrbbecSDK v2).

    Topics: ``/camera/gemini/color/image_raw``, ``/camera/gemini/depth/image_raw``, ``.../depth/points``,
    ``.../color/camera_info``. Jetson: USB 3 + ``orbbec_camera`` launch ``gemini_330_series.launch.py``.
    """

    SDK = "OrbbecSDK_ROS2 (gemini_330_series.launch.py)"

    def frame(self, width: int = 640, height: int = 400) -> Optional[np.ndarray]:
        self._todo("frame")


class UvcCamera(_Real, CameraDriver):
    """Any UVC camera (wrist cameras, fisheye 360 replacement) - ``ros-<distro>-usb-cam`` or ``v4l2_camera``
    publishing ``/<name>/image_raw``; or OpenCV ``cv2.VideoCapture(device, cv2.CAP_V4L2)`` directly."""

    SDK = "v4l2_camera / usb_cam (UVC)"

    def frame(self, width: int = 640, height: int = 400) -> Optional[np.ndarray]:
        self._todo("frame")


class CanBms(_Real, BatteryDriver):
    """48 V LiFePO4 pack, BMS with documented CAN protocol (e.g. REC-BMS Victron-compatible frames 0x351/0x355/0x356,
    or Orion BMS 2 custom CAN). Read with ``python-can`` on SocketCAN ``can3`` and decode; publish ``/battery_state``
    (sensor_msgs/BatteryState) for Nav2 / opennav_docking."""

    SDK = "python-can (SocketCAN) + Victron/Pylontech CAN frame decoding"

    def status(self) -> BatteryStatus:
        self._todo("status")


class Hub75Face(_Real, FaceDriver):
    """32x16 HUB75 RGB matrix driven by an ESP32-S3 (``ESP32-HUB75-MatrixPanel-DMA``, MIT).
    Host protocol: newline-delimited JSON over USB CDC (``pyserial``):
    ``{"expr":"happy","gaze":[x,y],"rgb":[r,g,b]}`` - the MCU owns animation (blink) at 60 fps."""

    SDK = "pyserial -> ESP32-S3 HUB75 firmware"

    def set_expression(self, expression: str, hold_s: float = 0.0) -> None:
        self._todo("set_expression")

    def state(self) -> dict[str, Any]:
        return {"expression": "unknown", "gaze": [0, 0], "blink": 0, "color": [80, 80, 80]}


class CoffeeMcu(_Real, CoffeeModuleDriver):
    """RP2040/ESP32 running micro-ROS (``micro_ros_agent serial``): actuator driver for the 150 mm shuttle
    (limit switches), opto-isolated relay across the machine's brew button, NTC/flow sensing.
    ROS 2: actions ``/coffee/shuttle`` and ``/coffee/brew``; topic ``/coffee/status``.
    The 230 V side stays inside the commercial machine; the MCU only closes a dry contact."""

    SDK = "micro-ROS on RP2040/ESP32 (serial transport)"

    def status(self) -> CoffeeStatus:
        self._todo("status")

    def shuttle(self, position: str) -> ActionHandle:
        self._todo("shuttle")

    def brew(self) -> ActionHandle:
        self._todo("brew")
