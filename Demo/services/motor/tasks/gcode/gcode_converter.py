from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

from gcodeparser import GcodeLine, GcodeParser

from services.motor.tasks.gcode.gcode_command import EGcodeCommand

Point = Tuple[float, float, float]  # (x, y, z)

# ----------------- Math helpers -----------------
def _norm_angle(a: float) -> float:
    two = 2.0 * math.pi
    a = a % two
    return a if a >= 0.0 else a + two

def _sweep_angle(theta_start: float, theta_end: float, cw: bool) -> float:
    """Signed sweep: CW negative, CCW positive; full circle if same angle."""
    ts = _norm_angle(theta_start)
    te = _norm_angle(theta_end)
    if cw:
        return -((_norm_angle(ts - te)) or (2.0 * math.pi))
    else:
        return (_norm_angle(te - ts)) or (2.0 * math.pi)

def _segments_for_tol(radius: float, sweep: float, chord_tol: float) -> int:
    r = abs(radius)
    if r < 1e-12 or abs(sweep) < 1e-12:
        return 1
    # Sagitta s = r(1 - cos(Δ/2)) <= chord_tol → Δ = 2*acos(1 - s/r)
    c = max(-1.0, min(1.0, 1.0 - (chord_tol / max(r, 1e-12))))
    delta = 2.0 * math.acos(c)
    return max(1, min(10000, int(math.ceil(abs(sweep) / max(delta, 1e-6)))))

def arc_xy_waypoints_from_ij(
    start: Point,
    end_abs: Point,
    i: float, j: float,
    clockwise: bool,             # True=G02, False=G03
    ij_is_incremental: bool = True,
    chord_tol: float = 0.02
) -> List[Point]:
    """
    Produce absolute waypoints along an XY arc from start to end (end included).
    Z is linearly interpolated to end_abs.z to support helical arcs.
    """
    x0, y0, z0 = start
    xe, ye, ze = end_abs

    if ij_is_incremental:
        cx, cy = x0 + i, y0 + j
    else:
        cx, cy = i, j

    rs = math.hypot(x0 - cx, y0 - cy)
    re = math.hypot(xe - cx, ye - cy)

    # if abs(rs - re) > 1e-3:  # tune tolerance to your units
    #     raise ValueError(f"Arc radii mismatch: start {rs:.4f} vs end {re:.4f}")
    # r = rs  # or (rs + re)/2.0 if you *really* want to tolerate tiny mismatch
    r  = 0.5 * (rs + re)  # tolerate tiny mismatch

    ths = math.atan2(y0 - cy, x0 - cx)
    the = math.atan2(ye - cy, xe - cx)
    sweep = _sweep_angle(ths, the, clockwise)

    n = _segments_for_tol(r, sweep, chord_tol)
    dth = sweep / n

    points: List[Point] = []
    for k in range(1, n):
        th = ths + dth * k
        xk = cx + r * math.cos(th)
        yk = cy + r * math.sin(th)
        zk = z0 + (ze - z0) * (k / n)
        points.append((xk, yk, zk))

    points.append(end_abs)  # exact end
    return points

# ----------------- Modal / position helpers -----------------
@dataclass
class ModalState:
    absolute_pos_mode: bool = True   # True => G90 (absolute), False => G91 (relative)
    ij_incremental: bool = True      # True => G91.1 (I/J offsets), False => G90.1 (absolute centers)

def _apply_move_update(current: Point, line: GcodeLine, modal: ModalState) -> Point:
    """
    Update current machine position based on a generic linear (G0/G1) move line.
    Only X/Y/Z are considered for position tracking.
    """
    x, y, z = current
    px = line.params.get('X')
    py = line.params.get('Y')
    pz = line.params.get('Z')

    if modal.absolute_pos_mode:
        if px is not None: x = px
        if py is not None: y = py
        if pz is not None: z = pz
    else:
        if px is not None: x += px
        if py is not None: y += py
        if pz is not None: z += pz
    return (x, y, z)

def _target_from_params(current: Point, params: Dict[str, float], modal: ModalState) -> Point:
    """
    Compute the intended absolute target (X,Y,Z) for a motion command,
    respecting modal absolute/relative (G90/G91) for endpoints.
    """
    x, y, z = current
    dx = params.get('X')
    dy = params.get('Y')
    dz = params.get('Z')

    if modal.absolute_pos_mode:
        tx = x if dx is None else dx
        ty = y if dy is None else dy
        tz = z if dz is None else dz
    else:
        tx = x + (dx or 0.0)
        ty = y + (dy or 0.0)
        tz = z + (dz or 0.0)
    return (tx, ty, tz)

# ----------------- Arc → segments (RELATIVE G0/G1 only) -----------------
def g_segments_for_arc_rel(
    line: GcodeLine,
    start_abs: Point,
    modal: ModalState,
    *,
    chord_tol: float = 0.02,
    use_g1: bool = False,
    feed_for_g1: Optional[float] = None
) -> List[GcodeLine]:
    """
    Convert a G02/G03 line (I/J arcs in the XY plane) into
    a list of RELATIVE G0/G1 segments (no G90 emitted).
    - start_abs: absolute start position before this line
    - modal.absolute_pos_mode is respected for the line's X/Y/Z endpoint
    - modal.ij_incremental controls I/J semantics (G91.1 vs G90.1)
    - use_g1: True -> emit G1; False -> emit G0
    - feed_for_g1: optional F to set on the FIRST G1 segment
    """
    if not (line.command and line.command[0] == 'G' and line.command[1] in (2, 3)):
        raise ValueError("g_segments_for_arc_rel expects a G02/G03 line")

    clockwise = (line.command[1] == 2)
    params = line.params

    # Compute absolute end point for this arc (respect G90/G91 for end)
    end_abs = _target_from_params(start_abs, params, modal)

    # I/J (and optional Z helical)
    i = params.get('I', 0.0)
    j = params.get('J', 0.0)
    # If Z present, do helical
    ze_present = 'Z' in params

    # Build absolute waypoints, then convert to RELATIVE deltas
    waypoints_abs = arc_xy_waypoints_from_ij(
        start=start_abs,
        end_abs=end_abs,
        i=i, j=j,
        clockwise=clockwise,
        ij_is_incremental=modal.ij_incremental,
        chord_tol=chord_tol
    )

    out: List[GcodeLine] = []
    cx, cy, cz = start_abs
    code = ('G', 1) if use_g1 else ('G', 0)

    for idx, (px, py, pz) in enumerate(waypoints_abs):
        dx, dy, dz = px - cx, py - cy, pz - cz
        # Build minimal params (omit axes with ~0 delta to keep tidy)
        lp: Dict[str, float] = {}
        if abs(dx) > 1e-12: lp['X'] = dx
        if abs(dy) > 1e-12: lp['Y'] = dy
        if ze_present and abs(dz) > 1e-12: lp['Z'] = dz

        # If all deltas are ~0, skip
        if not lp:
            cx, cy, cz = px, py, pz
            continue

        if use_g1 and feed_for_g1 is not None and idx == 0:
            lp['F'] = feed_for_g1

        out.append(GcodeLine(command=code, params=lp, comment="arc-seg"))
        cx, cy, cz = px, py, pz

    return out

# ----------------- Top-level transformer -----------------
def transform_arcs_to_segments(
    lines: List[GcodeLine],
    *,
    start_pos: Point = (0.0, 0.0, 0.0),
    ij_incremental: bool = False,     # True => G91.1
    chord_tol: float = 0.002,
    emit_g1: bool = False,
    feed_for_g1: Optional[float] = None
) -> List[GcodeLine]:
    """
    Walk a parsed program (list of GcodeLine), replacing each G02/G03
    with RELATIVE G0/G1 segments. Output list contains only original lines
    (except arcs) + inserted G0/G1 segments. No G90/G91 is emitted.

    NOTE:
    - We respect incoming G90/G91 for *interpreting* endpoints of moves, but
      the produced arc segments themselves are always relative.
    - We update position on G0/G1/G2/G3 that carry X/Y/Z.
    - Other codes are passed through untouched.
    """
    modal = ModalState(absolute_pos_mode=True, ij_incremental=ij_incremental)
    cur = start_pos
    out: List[GcodeLine] = []

    for line in lines:
        cmd = line.command

        # Track modal G90/G91 if present (some parsers emit them as GcodeLine with no XYZ)
        if cmd and cmd[0] == 'G' and cmd[1] in (90, 91):
            modal.absolute_pos_mode = (cmd[1] == 90)
            out.append(line)  # pass through the modal line unchanged
            continue

        if cmd and cmd[0] == 'G' and cmd[1] in (2, 3):
            # Replace arc with segments
            segs = g_segments_for_arc_rel(
                line=line,
                start_abs=cur,
                modal=modal,
                chord_tol=chord_tol,
                use_g1=emit_g1,
                feed_for_g1=feed_for_g1
            )
            out.extend(segs)
            # Update current absolute position to arc end
            cur = _target_from_params(cur, line.params, modal)
            continue

        # Pass-through non-arc lines
        out.append(line)

        # Update current position on linear moves (G0/G1) that carry X/Y/Z
        if cmd and cmd[0] == 'G' and cmd[1] in (0, 1):
            cur = _apply_move_update(cur, line, modal)

    return out

def parse_gcode_cmd(gcode_cmd: str) -> list[GcodeLine]:
    original_lines = GcodeParser(gcode_cmd).lines
    result: list[GcodeLine] = []

    for line in original_lines:
        match line.command_str:
            case EGcodeCommand.G0 | EGcodeCommand.G1:
                result.append(line)
            case EGcodeCommand.G2:
                converted = transform_arcs_to_segments([line])
                result.extend(converted)
            case _:
                print("Not implemented: ", line)
    return result

