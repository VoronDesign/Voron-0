import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf8')
import numpy as np, trimesh, holes, apply
from multiprocessing import Pool

def check(rel):
    m = trimesh.load(apply.ROOT + rel, process=True)
    bodies = m.split(only_watertight=False)
    lines = [f'{rel}: watertight={m.is_watertight} bodies={len(bodies)}']
    for e in apply.SPEC.get(rel, []):
        p = apply.CAT[rel]['pockets'][e[0]]
        prof = holes.profile(m, np.array(p['perp']), np.array(p['axis']), p['h0'] - 1.0, p['h1'] + 1.0)
        lines.append(f'  #{e[0]} {e[1]:9s} {holes.compress(prof)}')
    left = [h for h in holes.find_holes(m, 4.35, 4.8, extra_axes=False) if h['h1'] - h['h0'] >= 2.0]
    lines.append(f'  remaining 4.35-4.8mm pockets: {len(left)}')
    return '\n'.join(lines)

if __name__ == '__main__':
    files = list(apply.SPEC) + ['Multibody_STLs/Cowling/[a]_MiniSB_Cowling_Multibody.STL']
    with Pool(11) as p:
        for r in p.map(check, files):
            print(r)
