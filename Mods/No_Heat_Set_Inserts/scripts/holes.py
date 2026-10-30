"""Detect round holes in an STL mesh by slicing along candidate axes.

Returns cylinders: axis direction, 3D centre line start/end, diameter.
"""
import numpy as np
import trimesh
from collections import defaultdict

STEP = 0.2


def candidate_axes(mesh, min_count=12):
    """Axes of cylindrical surfaces: cross product of normals of adjacent,
    slightly-bent faces is parallel to the cylinder axis."""
    axes = [np.eye(3)[i] for i in range(3)]
    adj = mesh.face_adjacency
    ang = mesh.face_adjacency_angles
    sel = (ang > np.radians(3)) & (ang < np.radians(40))
    n = mesh.face_normals
    c = np.cross(n[adj[sel, 0]], n[adj[sel, 1]])
    ln = np.linalg.norm(c, axis=1)
    c = c[ln > 1e-6] / ln[ln > 1e-6, None]
    # canonical sign: first significant component positive
    for v in c:
        k = np.argmax(np.abs(v) > 0.3)
        if v[k] < 0:
            v *= -1
    # cluster by rounding
    buckets = defaultdict(list)
    for v in c:
        buckets[tuple(np.round(v, 1))].append(v)
    for k, vs in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        if len(vs) < min_count:
            break
        m = np.mean(vs, axis=0)
        m /= np.linalg.norm(m)
        if all(abs(np.dot(m, a)) < 0.995 for a in axes):
            axes.append(m)
    return axes


def ring_circle(coords):
    pts = np.asarray(coords)[:-1]
    if len(pts) < 8:
        return None
    ctr = pts.mean(axis=0)
    d = np.linalg.norm(pts - ctr, axis=1)
    r = d.mean()
    if r <= 0 or (d.max() - d.min()) > max(0.06 * r, 0.08):
        return None
    return ctr, r


def hole_loops(path):
    """Closed loops of a planar section that are holes (odd nesting depth)."""
    from shapely.geometry import Polygon, Point
    loops = [np.asarray(d) for d in path.discrete if len(d) >= 4]
    polys = [Polygon(l) for l in loops]
    for i, l in enumerate(loops):
        p = Point(l[0])
        bi = polys[i].bounds
        depth = 0
        for j, q in enumerate(polys):
            if j == i:
                continue
            bq = q.bounds
            if bq[0] <= bi[0] and bq[1] <= bi[1] and bq[2] >= bi[2] and bq[3] >= bi[3] and q.contains(p):
                depth += 1
        if depth % 2 == 1:
            yield l


def find_holes(mesh, dmin=1.5, dmax=7.0, extra_axes=True):
    out = []
    for axis in (candidate_axes(mesh) if extra_axes else list(np.eye(3))):
        proj = mesh.vertices @ axis
        lo, hi = proj.min(), proj.max()
        heights = np.arange(lo + STEP / 2, hi, STEP)
        origin = axis * 0.0
        secs = mesh.section_multiplane(plane_origin=origin, plane_normal=axis, heights=heights)
        recs = []  # (height, cx, cy, r, to3D)
        T = None
        for h, s in zip(heights, secs):
            if s is None:
                continue
            T = s.metadata.get("to_3D", None) if hasattr(s, "metadata") else None
            for coords in hole_loops(s):
                    fit = ring_circle(coords)
                    if fit is None:
                        continue
                    (cx, cy), r = fit
                    if dmin <= 2 * r <= dmax:
                        # map to 3D centre
                        p3 = trimesh.transform_points([[cx, cy, 0.0]], s.metadata["to_3D"])[0]
                        recs.append((h, p3, r))
        # cluster: same axis line (perp distance) and contiguous heights, same radius
        recs.sort(key=lambda t: t[0])
        groups = []
        for h, p, r in recs:
            placed = False
            for g in groups:
                hp, pp, rr = g[-1]
                perp = (p - pp) - np.dot(p - pp, axis) * axis
                if np.linalg.norm(perp) < 0.15 and abs(r - rr) < 0.08 and h - hp <= STEP * 1.5 + 1e-6:
                    g.append((h, p, r))
                    placed = True
                    break
            if not placed:
                groups.append([(h, p, r)])
        for g in groups:
            if len(g) < 3:
                continue
            hs = np.array([t[0] for t in g])
            ps = np.array([t[1] for t in g])
            rs = np.array([t[2] for t in g])
            c = ps.mean(axis=0)
            c = c - np.dot(c, axis) * axis  # perp component of centre line
            out.append(dict(axis=axis, perp=c, h0=hs.min() - STEP / 2, h1=hs.max() + STEP / 2,
                            d=2 * rs.mean()))
    return out


def point_at(hole, h):
    return hole["perp"] + hole["axis"] * h


def profile(mesh, p0, axis, t0, t1, step=0.2):
    """Walk along the line p0+axis*t. At each t, section the mesh with the
    plane normal to the axis. Report 'S' if the line is inside material,
    'O' if in open air (no enclosing loop narrower than 9mm), else the
    equivalent diameter of the smallest void loop enclosing the line."""
    from shapely.geometry import Polygon, Point
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    p0 = np.asarray(p0, float)
    res = []
    for t in np.arange(t0, t1 + 1e-9, step):
        o = p0 + axis * t
        s = mesh.section(plane_origin=o, plane_normal=axis)
        if s is None:
            res.append((t, 'O')); continue
        p2, T = s.to_2D() if hasattr(s, 'to_2D') else s.to_planar()
        pt = trimesh.transform_points([o], np.linalg.inv(T))[0][:2]
        P = Point(pt)
        enc = []
        for d in p2.discrete:
            if len(d) < 4: continue
            pg = Polygon(d)
            if pg.is_valid and pg.contains(P):
                enc.append(pg)
            elif not pg.is_valid and Polygon(d).buffer(0).contains(P):
                enc.append(Polygon(d).buffer(0))
        if len(enc) % 2 == 1:
            res.append((t, 'S')); continue
        if not enc:
            res.append((t, 'O')); continue
        sm = min(enc, key=lambda g: g.area)
        deq = 2 * np.sqrt(sm.area / np.pi)
        b = sm.bounds
        if max(b[2] - b[0], b[3] - b[1]) > 9:
            res.append((t, 'O'))
        else:
            # hexagon detection: ratio of area to circumscribed circle
            res.append((t, round(float(deq), 2)))
    return res


def compress(res):
    out = []
    for t, s in res:
        key = s if isinstance(s, str) else round(s, 1)
        if out and out[-1][2] == key:
            out[-1][1] = t
        else:
            out.append([t, t, key])
    return ' '.join(f'[{a:.1f}..{b:.1f}:{k}]' for a, b, k in out)
