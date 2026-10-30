"""Shared paths and access to the unmodified upstream STLs."""
import io
import os
import subprocess

import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
ROOT = os.path.join(REPO, 'STLs').replace(os.sep, '/') + '/'
BASE = 'Voron0.2r1'   # unmodified upstream branch the conversion starts from


def load_original(rel):
    """Read an upstream STL (path relative to STLs/) from git, so the
    conversion always starts from the original part and can be re-run."""
    data = subprocess.run(['git', '-C', REPO, 'show', f'{BASE}:STLs/{rel}'],
                          capture_output=True, check=True).stdout
    return trimesh.load(io.BytesIO(data), file_type='stl', process=True)


def original_stls():
    out = subprocess.run(['git', '-C', REPO, 'ls-tree', '-r', '--name-only', BASE, 'STLs'],
                         capture_output=True, check=True, text=True).stdout.split('\n')
    return [p[len('STLs/'):] for p in out if p.lower().endswith('.stl')]
