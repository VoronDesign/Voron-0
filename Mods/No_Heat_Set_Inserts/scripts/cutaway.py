"""Before/after cutaways of the three conversion types for the docs."""
import sys, os, numpy as np, trimesh, matplotlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, load_original
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# title, STL (original read from git), point on pocket axis, axis, normal of the axial cut, z of the cross cut
CASES = [
    ('Drive frame lower - captive nut on the floor\n(M3x35 bearing axle enters from above)',
     'A_Drive_Frame_Lower_x1.stl', (111.73, 193.66, 3.0), (0, 0, 1), (1, 0, 0), 4.0),
    ('XY joint lower - nut recessed at the mouth\n(bolt head below, bearing-stack shim sits on the nut)',
     'XY_Joint_Left_Lower_x1.stl', (206.9, 203.24, 20.0), (0, 0, 1), (1, 0, 0), 21.6),
    ('Thumb nut - nut pocket on the underside',
     '[a]_Thumb_Nut_x3.stl', (158.07, 79.83, 2.0), (0, 0, 1), (1, 0, 0), 1.2),
    ('Cowling - filled pocket with 2.8mm self-tapping pilot',
     'Toolheads/Mini_Stealthburner/[a]_MiniSB_Cowling_x1.STL', (82.9, 76.8, 55.0), (0, 0, 1), (1, 0, 0), 55.0),
]
W = 7.0


def draw(ax, rel, origin, normal, up, title, original=False):
    m = load_original(rel) if original else trimesh.load(ROOT + rel, process=True)
    s = m.section(plane_origin=origin, plane_normal=normal)
    o = np.asarray(origin, float)
    up = np.asarray(up, float)
    right = np.cross(up, normal)
    for ent in s.entities:
        pts = s.vertices[ent.points] - o
        x, y = pts @ right, pts @ up
        ax.plot(x, y, 'k-', lw=1)
    # shade solid by even-odd fill of the closed loops
    p2, T = s.to_2D() if hasattr(s, 'to_2D') else s.to_planar()
    for d in p2.discrete:
        pts3 = trimesh.transform_points(np.column_stack([d, np.zeros(len(d))]), T) - o
        ax.fill(pts3 @ right, pts3 @ up, color='#4c78a8', alpha=0.35, lw=0)
    ax.set_xlim(-W, W); ax.set_ylim(-W, W); ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=8)


fig, axs = plt.subplots(len(CASES), 3, figsize=(9, 3.2 * len(CASES)))
for r, (title, rel, p, axis, nrm, zc) in enumerate(CASES):
    draw(axs[r, 0], rel, p, nrm, axis, 'original (heat-set insert)', original=True)
    draw(axs[r, 1], rel, p, nrm, axis, 'converted - axial section')
    draw(axs[r, 2], rel, (p[0], p[1], zc), axis, np.cross(axis, nrm) * -1, 'converted - cross section')
    axs[r, 0].set_ylabel(title, fontsize=8, rotation=0, ha='right', va='center', labelpad=10)
plt.tight_layout()
plt.savefig(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cutaways.png'), dpi=110)
