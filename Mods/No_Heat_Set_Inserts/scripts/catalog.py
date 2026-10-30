"""Catalog round pockets of M3 heat-set insert size (4.2-5.3mm) in every
upstream STL. Writes catalog.json, which apply.py indexes into. Not every
entry is an insert (PTFE bores, M2/M2.5 counterbores also match); apply.py
lists the ones that are."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import holes
from common import load_original, original_stls
from multiprocessing import Pool

DMIN, DMAX = 4.2, 5.3


def _line_dist(pt, h):
    q = pt - h['perp']
    return np.linalg.norm(q - np.dot(q, h['axis']) * h['axis'])


def principal_dedupe(found):
    """Keep axis-aligned pockets; keep an oblique one only if no kept pocket
    already passes through its middle (oblique slices of a straight hole
    or of chamfer cones produce near-duplicates)."""
    keep = [h for h in found if max(abs(h['axis'])) > 0.999]
    extra = sorted((h for h in found if max(abs(h['axis'])) <= 0.999),
                   key=lambda h: -(h['h1'] - h['h0']))
    for h in extra:
        mid = holes.point_at(h, (h['h0'] + h['h1']) / 2)
        if all(_line_dist(mid, k) > 1.5 for k in keep):
            keep.append(h)
    return keep


def analyse(rel):
    try:
        return rel, _analyse(rel)
    except Exception as e:
        return rel, dict(error=repr(e), pockets=[])


def _analyse(rel):
    m = load_original(rel)
    found = [h for h in holes.find_holes(m, 1.5, 7.0)]
    pockets = [h for h in found if DMIN <= h['d'] <= DMAX]
    pockets = principal_dedupe(pockets)
    out = []
    for h in pockets:
        ax = h['axis']
        prof = holes.profile(m, h['perp'], ax, h['h0'] - 3, h['h1'] + 3)
        out.append(dict(axis=ax.round(4).tolist(), perp=h['perp'].round(3).tolist(),
                        h0=round(h['h0'], 2), h1=round(h['h1'], 2), d=round(h['d'], 3),
                        profile=holes.compress(prof)))
    return dict(watertight=bool(m.is_watertight), bounds=m.bounds.round(2).tolist(), pockets=out)


if __name__ == '__main__':
    files = sorted(original_stls())
    with Pool() as p:
        res = dict(p.map(analyse, files, chunksize=1))
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'catalog.json'), 'w'), indent=1)
    for k, v in res.items():
        if v['pockets']:
            print(k, len(v['pockets']))
