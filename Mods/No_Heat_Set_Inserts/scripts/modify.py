"""Mesh operations that replace heat-set insert pockets.

nut_trap(): turn the round pocket into a hexagonal M3 nut pocket of the same
            depth; the nut bears on the pocket floor (screw enters from floor side).
pilot():    fill the pocket and drill a self-tapping pilot hole for an M3 screw
            entering from the mouth.
"""
import numpy as np
import trimesh
import manifold3d as mf

HEX_AF = 5.7        # M3 nut is 5.5 AF; +0.2 printed clearance
PILOT_D = 2.8       # M3 thread-forming pilot in ABS/ASA
SEGMENTS = 48


def to_manifold(m):
    mesh = mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                   tri_verts=np.asarray(m.faces, np.uint32))
    out = mf.Manifold(mesh)
    if out.status() != mf.Error.NoError:
        raise RuntimeError(f'not manifold: {out.status()}')
    return out


def to_trimesh(man):
    """Manifold output can contain zero-length edges (coincident but distinct
    vertices); STL cannot represent those, so collapse them before export."""
    import io
    mm = man.to_mesh()
    n_bodies = len(man.decompose())
    for digits in (5, 4, 6, 3):
        t = trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=False)
        t.merge_vertices(digits_vertex=digits)
        t.update_faces(t.nondegenerate_faces(height=1e-7))
        t.remove_unreferenced_vertices()
        buf = io.BytesIO()
        t.export(buf, file_type='stl')
        buf.seek(0)
        back = trimesh.load(buf, file_type='stl')
        if back.is_watertight and len(back.split(only_watertight=False)) == n_bodies:
            return t
    raise RuntimeError('mesh does not survive an STL round trip')


def _frame(axis, hex_ref=None):
    """Rotation taking +Z to axis. For horizontal axes the hex is turned so a
    vertex points up (+Z) - a self-supporting 60 deg roof when printed."""
    z = np.asarray(axis, float) / np.linalg.norm(axis)
    if hex_ref is not None:
        x = np.asarray(hex_ref, float)
        x = x - np.dot(x, z) * z
    elif abs(z[2]) > 0.9:
        x = np.array([1.0, 0, 0])
    else:
        up = np.array([0, 0, 1.0])
        x = up - np.dot(up, z) * z     # x lies in the print-vertical direction
    x = x / np.linalg.norm(x)
    y = np.cross(z, x)
    R = np.eye(4)
    R[:3, :3] = np.column_stack([x, y, z])
    return R


def prism(p_start, axis, length, d, sides=SEGMENTS, circumscribed=False, hex_ref=None):
    """Prism/cylinder starting at p_start, extending `length` along axis.
    For sides=6, `d` is the across-flats size and one vertex is on local +X."""
    if sides == 6:
        r = d / 2 / np.cos(np.pi / 6)
    else:
        r = d / 2 / np.cos(np.pi / sides) if circumscribed else d / 2
    c = mf.Manifold.cylinder(length, r, r, sides)
    R = _frame(axis, hex_ref)
    R[:3, 3] = p_start
    return c.transform(R[:3, :])


def nut_trap(man, mouth, floor, axis_out, hex_ref=None, extra_out=1.0):
    """mouth/floor: 3D points on the pocket axis; axis_out points out of the mouth."""
    L = np.linalg.norm(np.asarray(mouth) - floor)
    tool = prism(np.asarray(floor), axis_out, L + extra_out, HEX_AF, sides=6, hex_ref=hex_ref)
    return man - tool, tool


def pilot(man, mouth, floor, axis_out, pocket_d, extra_out=1.5):
    L = np.linalg.norm(np.asarray(mouth) - floor)
    fill = prism(np.asarray(floor) - 0.05 * np.asarray(axis_out), axis_out, L + 0.05, pocket_d + 0.15)
    drill = prism(np.asarray(floor), axis_out, L + extra_out, PILOT_D, circumscribed=True)
    return (man + fill) - drill, fill


def void_fraction(man, tool):
    """Fraction of a tool envelope that is already empty in the part."""
    inter = (man ^ tool).volume()
    return 1.0 - inter / tool.volume()
