"""Geometric core of the Giorgio CAD: Part / Hole data model + CadQuery helpers.

Units: millimetres, kilograms. Frame: robot base frame ("amr" body of the MuJoCo model):
origin on the floor at the centre of the Tracer 2.0, x forward, y left, z up.
All parts are built directly in the base frame at column lift = 0 and shuttle retracted;
moving parts carry a `motion` tag so the validator can sweep them.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cadquery as cq
import numpy as np

# ------------------------------------------------------------------ materials (density kg/m^3)
MATERIALS = {
    "EN AW-6082-T6": dict(rho=2700, Rm=310, Rp02=260, color=(0.78, 0.79, 0.81), kind="alu"),
    "EN AW-5754-H22": dict(rho=2670, Rm=220, Rp02=130, color=(0.80, 0.81, 0.83), kind="alu"),
    "EN AW-6060-T66": dict(rho=2700, Rm=215, Rp02=160, color=(0.78, 0.79, 0.81), kind="alu"),
    "EN AW-6063-T66 (profile)": dict(rho=2700, Rm=245, Rp02=200, color=(0.75, 0.76, 0.78), kind="alu"),
    "S235 / 1.4301": dict(rho=7900, Rm=500, Rp02=210, color=(0.6, 0.6, 0.62), kind="steel"),
    "PA12 (SLS/MJF)": dict(rho=1010, Rm=48, Rp02=40, color=(0.92, 0.92, 0.90), kind="plastic"),
    "PA12-GB (SLS)": dict(rho=1220, Rm=38, Rp02=30, color=(0.92, 0.92, 0.90), kind="plastic"),
    "POM-C": dict(rho=1410, Rm=65, Rp02=60, color=(0.95, 0.95, 0.93), kind="plastic"),
    "PETG translucent": dict(rho=1270, Rm=50, Rp02=45, color=(0.85, 0.9, 0.95), kind="plastic"),
    "TPU 90A / EPDM": dict(rho=1200, Rm=30, Rp02=10, color=(0.08, 0.08, 0.09), kind="plastic"),
    "C26000 brass": dict(rho=8530, Rm=350, Rp02=200, color=(0.85, 0.65, 0.3), kind="cu"),
    "purchased": dict(rho=0, Rm=0, Rp02=0, color=(0.2, 0.2, 0.22), kind="purchased"),
}


@dataclass
class Hole:
    """A hole feature. `p` = point on the axis at the ENTRY face, `axis` = unit vector pointing INTO the part.
    kind: 'clear' (ISO 273 clearance), 'tap' (tapped, d = tap drill), 'insert' (bore for threaded insert),
          'slot' (clearance slot, `slot_len` along `slot_dir`), 'nut' (clearance + captive nut / T-slot nut side),
          'bore' (non-fastener hole, e.g. pin)
    `thread` = 'M5' etc for tap/insert/clear (the bolt it is meant for)."""
    name: str
    p: tuple
    axis: tuple
    d: float
    depth: float
    kind: str
    thread: str = ""
    slot_len: float = 0.0
    slot_dir: tuple = (1, 0, 0)
    cbore: tuple | None = None        # (diameter, depth) counterbore at entry


@dataclass
class Part:
    name: str
    shape: object                     # cq.Shape (Solid/Compound) in base frame, mm
    material: str
    process: str
    category: str = "custom"          # custom | purchased | shell | fastener
    color: tuple | None = None
    explode: tuple = (0, 0, 0)        # explode direction * distance (mm)
    mass_kg: float | None = None      # override (purchased parts: datasheet mass)
    mass_src: str = ""
    holes: dict = field(default_factory=dict)
    motion: str = ""                  # '' | 'lift' | 'shuttle'
    qty: int = 1
    notes: str = ""
    mesh_file: str = ""               # optional real mesh (purchased part STL) for export / clearance
    check_interference: bool = True

    def add_hole(self, h: Hole):
        self.holes[h.name] = h
        return h

    @property
    def rho(self):
        return MATERIALS[self.material]["rho"]

    def volume_cm3(self):
        return self.shape.Volume() / 1000.0

    def mass(self):
        if self.mass_kg is not None:
            return self.mass_kg
        return self.shape.Volume() * 1e-9 * self.rho

    def com(self):
        """centre of mass (mm) of the CAD solid (purchased envelopes: geometric centroid unless overridden)"""
        c = cq.Shape.centerOfMass(self.shape)
        return np.array([c.x, c.y, c.z])


# ------------------------------------------------------------------ shape helpers
def V(*a):
    return cq.Vector(*a)


def box(x0, x1, y0, y1, z0, z1):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, h, p, d=(0, 0, 1)):
    return cq.Solid.makeCylinder(r, h, V(*p), V(*d))


def wp_plate(outline_pts, t, z0, fillet=0.0):
    """extrude a closed polygon (x,y) list from z0 by t"""
    w = cq.Workplane("XY", origin=(0, 0, z0)).polyline(outline_pts).close().extrude(t)
    s = w.val()
    if fillet > 0:
        try:
            s = cq.Workplane().add(s).edges("|Z").fillet(fillet).val()
        except Exception:
            pass
    return s


def rounded_rect(cx, cy, lx, ly, t, z0, r=0.0):
    w = cq.Workplane("XY", origin=(cx, cy, z0)).rect(lx, ly).extrude(t)
    if r > 0:
        w = w.edges("|Z").fillet(r)
    return w.val()


def cut_hole(shape, h: Hole, through_extra=0.5):
    """cut the hole described by h from shape (cylinder or slot, optional counterbore)"""
    p = np.array(h.p, float)
    a = np.array(h.axis, float); a /= np.linalg.norm(a)
    start = p - a * through_extra
    L = h.depth + 2 * through_extra
    if h.kind == "slot" and h.slot_len > 0:
        sd = np.array(h.slot_dir, float); sd /= np.linalg.norm(sd)
        c1 = start - sd * h.slot_len / 2
        tool = cyl(h.d / 2, L, c1, a).fuse(cyl(h.d / 2, L, c1 + sd * h.slot_len, a))
        # rectangle between the two end circles
        n = np.cross(a, sd)
        pts = [c1 + n * h.d / 2, c1 - n * h.d / 2, c1 - n * h.d / 2 + sd * h.slot_len, c1 + n * h.d / 2 + sd * h.slot_len]
        face = cq.Face.makeFromWires(cq.Wire.makePolygon([V(*q) for q in pts], close=True))
        tool = tool.fuse(cq.Solid.extrudeLinear(face, V(*(a * L))))
    else:
        tool = cyl(h.d / 2, L, start, a)
    if h.cbore:
        cd, cdep = h.cbore
        tool = tool.fuse(cyl(cd / 2, cdep + through_extra, start, a))
    return shape.cut(tool)


def transform_shape(shape, R=np.eye(3), t=(0, 0, 0)):
    """apply rigid transform x' = R x + t"""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf
    R = np.asarray(R, float)
    u, _, vt = np.linalg.svd(R)
    R = u @ vt                                  # re-orthonormalise
    tr = gp_Trsf()
    tr.SetValues(R[0, 0], R[0, 1], R[0, 2], float(t[0]), R[1, 0], R[1, 1], R[1, 2], float(t[1]), R[2, 0], R[2, 1], R[2, 2], float(t[2]))
    return cq.Shape.cast(BRepBuilderAPI_Transform(shape.wrapped, tr, True).Shape())


def rotz(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def roty(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rotx(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


# ------------------------------------------------------------------ superellipsoid shells (same law as shells.py)
def _sp(x, p):
    return np.sign(x) * np.abs(x) ** p


def superellipse_pts(a, b, e2, n=64):
    v = np.linspace(-np.pi, np.pi, n, endpoint=False)
    return np.stack([a * _sp(np.cos(v), e2), b * _sp(np.sin(v), e2)], 1)


def superellipsoid_solid(a, b, c, e1, e2, center=(0, 0, 0), taper=None, nsec=22, npts=56, umax_deg=86.0):
    """B-rep approximation of shells.py superellipsoid: loft of superellipse sections (closed splines)
    from u=-umax to +umax, closed by planar caps. taper(t), t=z/c in [-1,1] scales x,y like shells.py."""
    us = np.radians(np.linspace(-umax_deg, umax_deg, nsec))
    wires = []
    for u in us:
        k = _sp(math.cos(u), e1)
        z = c * _sp(math.sin(u), e1)
        s = taper(z / c) if taper else 1.0
        P = superellipse_pts(a * k * s, b * k * s, e2, npts)
        pts = [V(px + center[0], py + center[1], z + center[2]) for px, py in P]
        e = cq.Edge.makeSpline(pts + [pts[0]], periodic=False)
        wires.append(cq.Wire.assembleEdges([e]))
    solid = cq.Solid.makeLoft(wires, True)
    return solid


def superellipsoid_mesh_pts(a, b, c, e1, e2, center=(0, 0, 0), taper=None, nu=48, nv=96):
    """same vertex law as shells.py (for checks against the sim meshes)"""
    u = np.linspace(-np.pi / 2, np.pi / 2, nu)
    v = np.linspace(-np.pi, np.pi, nv, endpoint=False)
    U, Vv = np.meshgrid(u, v, indexing="ij")
    x = a * _sp(np.cos(U), e1) * _sp(np.cos(Vv), e2)
    y = b * _sp(np.cos(U), e1) * _sp(np.sin(Vv), e2)
    z = c * _sp(np.sin(U), e1)
    if taper is not None:
        s = taper(z / c)
        x, y = x * s, y * s
    return np.stack([x + center[0], y + center[1], z + center[2]], -1).reshape(-1, 3)


def hollow(outer, inner):
    return outer.cut(inner)


def shape_to_trimesh(shape, tol=0.4, ang=0.3):
    import trimesh
    vs, fs = shape.tessellate(tol, ang)
    V_ = np.array([[v.x, v.y, v.z] for v in vs])
    F_ = np.array(fs, dtype=np.int64)
    return trimesh.Trimesh(V_, F_, process=True)


def bbox_of(shape):
    bb = shape.BoundingBox()
    return np.array([[bb.xmin, bb.ymin, bb.zmin], [bb.xmax, bb.ymax, bb.zmax]])
