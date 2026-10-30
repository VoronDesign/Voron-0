"""Apply the no-insert conversions to the repo STLs, in place.

Modes per pocket (indices refer to catalog.json):
  pilot      fill the pocket, drill a 2.8mm M3 self-tapping pilot
  nut_floor  hex nut pocket over the full pocket depth; nut seats on the
             existing floor (screw enters through the floor clearance hole)
  nut_mouth  hex recess of nut depth, measured from the part face at the
             mouth, rest of the pocket filled with a 3.4mm clearance bore; the
             nut seats on the filled material and ends flush with the face
             (screw enters through the floor; used where the floor is thin or
             the mouth face carries a bearing-stack shim)
mouth: 'lo' or 'hi' - which end of the pocket (along catalog axis) is open.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import trimesh
import manifold3d as mf
import modify as M

from common import ROOT, load_original
CAT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'catalog.json')))
NUT_T = 2.4          # recess depth: a DIN 934 M3 nut (2.4mm) ends flush with the face
CLEAR_D = 3.4

TS = 'Toolheads/Mini_Stealthburner/'
HS = 'Toolheads/Hotend_Mounts/Standard/'
HF = 'Toolheads/Hotend_Mounts/Fan_Saver/'
SPEC = {
    # flats towards the outer wall (X), vertices towards the neighbouring pocket
    'A_Drive_Frame_Lower_x1.stl': [(0, 'nut_floor', 'lo', (0, 1, 0)), (1, 'pilot', 'lo'), (2, 'nut_floor', 'lo', (0, 1, 0))],
    'B_Drive_Frame_Lower_x1.stl': [(0, 'nut_floor', 'lo', (0, 1, 0)), (1, 'pilot', 'lo'), (2, 'nut_floor', 'lo', (0, 1, 0))],
    'A_Drive_Frame_Upper_x1.stl': [(0, 'pilot', 'lo')],
    'B_Drive_Frame_Upper_x1.stl': [(0, 'pilot', 'lo')],
    'Electronics/Fan_Mount_Bottom_x1.stl': [(i, 'pilot', 'lo') for i in range(4)],
    'Rear_Bed_Mount_Right_x1.stl': [(0, 'pilot', 'lo'), (1, 'pilot', 'lo')],
    'Skirts/Foot_Front_Left_x1.STL': [(0, 'pilot', 'lo')],
    'Skirts/Foot_Front_Right_x1.STL': [(0, 'pilot', 'lo')],
    'Skirts/Foot_Rear_Left_Inlet_x1.STL': [(0, 'pilot', 'hi'), (1, 'pilot', 'lo')],
    'Skirts/Foot_Rear_Right_FRS_x1.STL': [(0, 'pilot', 'lo'), (1, 'pilot', 'hi')],
    'Skirts/Foot_Rear_Right_Plain.STL': [(0, 'pilot', 'lo'), (1, 'pilot', 'hi')],
    'Toolheads/Bowden/MiniSB_Bowden_ECAS04.STL': [(0, 'pilot', 'hi')],
    'Toolheads/Bowden/MiniSB_Bowden_M10.STL': [(0, 'pilot', 'hi')],
    'Toolheads/Bowden/MiniSB_Bowden_M6.STL': [(0, 'pilot', 'hi')],
    # Bambu/MicroSwiss pockets are back-entry, but a 5.7AF hex does not fit:
    # Bambu pockets are 6.85mm apart and 3.35mm from the top face, MicroSwiss
    # pockets sit in a 3.4mm radius boss. The pilot also works with the screw
    # arriving through the floor clearance hole.
    HF + '[a]_FS_Hotend_Mount_Bambu_X1C.stl': [(0, 'pilot', 'lo'), (1, 'pilot', 'lo')],
    HS + '[a]_Hotend_Mount_Bambu_X1C.stl': [(0, 'pilot', 'lo'), (1, 'pilot', 'lo')],
    HS + '[a]_Hotend_Mount_MicroSwiss_All_Metal.stl': [(0, 'pilot', 'lo'), (1, 'pilot', 'lo')],
    TS + 'Strain_Relief_Spacer_x2.stl': [(0, 'pilot', 'lo'), (1, 'pilot', 'hi')],
    TS + '[a]_MiniSB_Cowling_x1.STL': [(i, 'pilot', 'hi') for i in range(3)],
    TS + '[a]_MiniSB_MidBody_x1.STL': [(0, 'pilot', 'lo'), (1, 'pilot', 'lo'), (3, 'pilot', 'hi'), (4, 'pilot', 'hi')],
    TS + '[a]_Shuttle_x1.stl': [(0, 'pilot', 'lo')],
    'XY_Joint_Left_Lower_x1.stl': [(2, 'nut_mouth', 'hi'), (3, 'nut_mouth', 'hi')],
    'XY_Joint_Right_Lower_x1.stl': [(2, 'nut_mouth', 'hi'), (3, 'nut_mouth', 'hi')],
    'X_Carriage_x1.stl': [(0, 'pilot', 'lo'), (1, 'pilot', 'lo'), (2, 'pilot', 'hi'), (3, 'pilot', 'hi')],
    '[a]_Thumb_Nut_x3.stl': [(0, 'nut_mouth', 'lo')],
}


def tools_for(p, mode, mouth_end, hex_ref=None, face_t=None):
    """Return (add, sub, wall_envelope) manifolds for one pocket.
    face_t: axial position of the part face at the mouth (nut_mouth only)."""
    ax = np.array(p['axis'])
    h0, h1, d = p['h0'], p['h1'], p['d']
    perp = np.array(p['perp'])
    if mouth_end == 'lo':
        mouth, floor, out = perp + ax * h0, perp + ax * h1, -ax
    else:
        mouth, floor, out = perp + ax * h1, perp + ax * h0, ax
    L = h1 - h0
    fill = M.prism(floor - 0.05 * out, out, L + 0.05, d + 0.15)
    if mode == 'pilot':
        sub = M.prism(floor - 0.3 * out, out, L + 0.3 + 1.5, M.PILOT_D, circumscribed=True)
        return fill, sub, None
    if mode == 'nut_floor':
        sub = M.prism(floor, out, L + 1.0, M.HEX_AF, sides=6, hex_ref=hex_ref)
        env = M.prism(floor, out, L, M.HEX_AF + 1.6, sides=6, hex_ref=hex_ref)
        return None, sub, env
    if mode == 'nut_mouth':
        hex_start = perp + ax * face_t - out * NUT_T
        sub = (M.prism(hex_start, out, NUT_T + 1.0, M.HEX_AF, sides=6, hex_ref=hex_ref)
               + M.prism(floor - 0.3 * out, out, L + 0.3 + 1.0, CLEAR_D, circumscribed=True))
        env = M.prism(hex_start, out, NUT_T, M.HEX_AF + 1.6, sides=6, hex_ref=hex_ref)
        return fill, sub, env
    raise ValueError(mode)


def load_bodies(rel):
    m = load_original(rel)
    bodies = [b for b in m.split(only_watertight=False) if len(b.faces) > 4]
    return m, bodies


def mouth_face(m, p, mouth_end):
    """Axial position of the part face around the pocket mouth: the straight
    bore (h0..h1) ends at the start of the entry chamfer, the face is the
    outermost vertex ring of that chamfer."""
    ax = np.array(p['axis'])
    rel = m.vertices - np.array(p['perp'])
    t = rel @ ax
    radial = np.linalg.norm(rel - np.outer(t, ax), axis=1)
    near = radial < p['d'] / 2 + 1.2
    if mouth_end == 'hi':
        sel = near & (t >= p['h1'] - 0.3) & (t <= p['h1'] + 1.5)
        return t[sel].max()
    sel = near & (t <= p['h0'] + 0.3) & (t >= p['h0'] - 1.5)
    return t[sel].min()


def process(rel):
    m, bodies = load_bodies(rel)
    pockets = CAT[rel]['pockets']
    tools = []
    for e in SPEC[rel]:
        i, mode, end = e[:3]
        hex_ref = e[3] if len(e) > 3 else None
        face_t = mouth_face(m, pockets[i], end) if mode == 'nut_mouth' else None
        tools.append((i, mode, end) + tools_for(pockets[i], mode, end, hex_ref, face_t))
    report = []
    out_meshes = []
    shells = {}
    for e in SPEC[rel]:
        i = e[0]
        p = pockets[i]
        ax = np.array(p['axis']); base = np.array(p['perp']) + ax * p['h0']
        L = p['h1'] - p['h0']
        shells[i] = M.prism(base, ax, L, p['d'] + 2.0) - M.prism(base - ax, ax, L + 2, p['d'])
    for b in bodies:
        try:
            man = M.to_manifold(b)
        except RuntimeError:
            man = None
        if man is None:
            # open accent shells of multibody files: leave untouched
            report.append(f'  !! body with {len(b.faces)} faces is not manifold - left unchanged')
            out_meshes.append(b)
            continue
        v0 = man.volume()
        touched = False
        for i, mode, end, add, sub, env in tools:
            # apply only to the body whose material surrounds this pocket
            if (man ^ shells[i]).volume() < 0.3 * shells[i].volume():
                continue
            if env is not None:
                vf = M.void_fraction(man, env)
                report.append(f'  pocket {i} {mode}: envelope void {vf:.3f}')
            if add is not None:
                man = man + add
            man = man - sub
            touched = True
            report.append(f'  pocket {i} -> {mode} (mouth {end})')
        if touched:
            report.append(f'  body volume {v0:.1f} -> {man.volume():.1f} mm3, genus {man.genus()}')
            out_meshes.append(M.to_trimesh(man))
        else:
            out_meshes.append(b)
    res = trimesh.util.concatenate(out_meshes)
    return res, report


if __name__ == '__main__':
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    for rel in SPEC:
        if only and rel not in only:
            continue
        res, report = process(rel)
        print(rel)
        print('\n'.join(report))
        if '--dry' not in sys.argv:
            res.export(ROOT + rel)
