"""Rebuild the multibody cowling from the converted single-body cowling.

The original multibody file is the cowling with a 0.4mm first-layer Voron
logo (three convex slashes) split into separate bodies, exported as open
shells. Rebuild it as two closed bodies: cowling minus logo, and logo.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh, manifold3d as mf
from scipy.spatial import ConvexHull
import modify as M

from common import ROOT, load_original
MULTI = ROOT + 'Multibody_STLs/Cowling/[a]_MiniSB_Cowling_Multibody.STL'
GAP = 0.01
SINGLE = ROOT + 'Toolheads/Mini_Stealthburner/[a]_MiniSB_Cowling_x1.STL'


def logo_solid(multi, cow):
    """Closed solid filling the debossed logo of the single-body cowling.
    Footprint = union of the accent bodies' downward faces on the bed plane."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    parts = multi.split(only_watertight=False)
    main = max(parts, key=lambda p: len(p.faces))
    acc = trimesh.util.concatenate([p for p in parts if p is not main])
    z0 = multi.bounds[0, 2]
    sel = (abs(acc.triangles_center[:, 2] - z0) < 0.01) & (acc.face_normals[:, 2] < -0.9)
    foot = unary_union([Polygon(t[:, :2]) for t in acc.triangles[sel]]).buffer(0.01).buffer(-0.01)
    area = foot.area
    # 10um clearance to the cowling so the two bodies stay disjoint in the STL
    foot = foot.buffer(-GAP)
    polys = list(getattr(foot, 'geoms', [foot]))
    cs = mf.CrossSection([np.asarray(p.exterior.coords)[:-1].tolist() for p in polys]
                         + [np.asarray(r.coords)[:-1].tolist() for p in polys for r in p.interiors],
                         mf.FillRule.EvenOdd)
    z1 = acc.vertices[acc.vertices[:, 2] < z0 + 2, 2].max()
    slab = mf.Manifold.extrude(cs, z1 - z0 + 0.3).translate([0, 0, z0])
    return slab - cow.translate([0, 0, -GAP]), area, (z0, z1)


if __name__ == '__main__':
    multi = load_original('Multibody_STLs/Cowling/[a]_MiniSB_Cowling_Multibody.STL')
    single = trimesh.load(SINGLE, process=True)
    body = max(single.split(only_watertight=False), key=lambda p: len(p.faces))
    main = M.to_manifold(body)
    logo, area, (z0, z1) = logo_solid(multi, main)
    # keep only the logo pieces in the recess, not air outside the part
    logo = mf.Manifold.batch_boolean([c for c in logo.decompose() if c.volume() > 1.0], mf.OpType.Add)
    print(f'logo footprint {area:.1f} mm2, z {z0:.2f}..{z1:.2f}, fill vol {logo.volume():.2f}, '
          f'avg depth {logo.volume() / area:.2f} mm, main vol {main.volume():.1f}')
    res = trimesh.util.concatenate([M.to_trimesh(main), M.to_trimesh(logo)])
    if '--dry' not in sys.argv:
        res.export(MULTI)
    else:
        res.export('multi_test.stl')
