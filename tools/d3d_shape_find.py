#!/usr/bin/env python3
"""bangaio-nx (2026-10-29): finds a reference game's function in Bangai-O by its shape, for the hooks the call-site
propagation (tools/d3d_propagate.py) left unpaired: small functions (thunks, getters) have no unique-shape seed and
few calls. The shape is tools/d3d_propagate.py's token (opcodes and registers, no immediates or displacements).

For each `name=REFADDR` it prints every Bangai-O function with the same tokens (exact), or the best few by
difflib ratio, with their callers' counts (a `bl` to it anywhere in the code).

  python -I tools/d3d_shape_find.py --ref-image <img> --ref-gen <generated dir> NAME=ADDR [NAME=ADDR ...]
"""
import argparse
import difflib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from d3d_propagate import Img, starts_of, TGT_CODE, ROOT  # noqa: E402


def callers(img, target):
    n = 0
    for s in img.starts:
        for _, t in img.calls(s):
            if t == target:
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref-image', required=True)
    ap.add_argument('--ref-gen', required=True)
    ap.add_argument('items', nargs='+')
    a = ap.parse_args()
    P = Img(a.ref_image, starts_of(a.ref_gen), 0x82000000, 0x83000000)
    N = Img(os.path.join(ROOT, 'out', 'renut_image.bin'), starts_of(os.path.join(ROOT, 'app', 'generated')),
            TGT_CODE[0], TGT_CODE[1])
    for item in a.items:
        name, addr = item.split('=')
        r = int(addr, 16)
        if r not in P.f:
            print(f'{name} {r:08X}: not a function start in the reference')
            continue
        pt = P.f[r][1]
        exact = [s for s, (w, t) in N.f.items() if t == pt]
        if exact:
            print(f'{name} ref {r:08X} ({len(pt)} insns, {callers(P, r)} ref callers): exact {len(exact)}: ' +
                  ', '.join(f'{s:08X}({callers(N, s)} callers)' for s in exact[:8]))
            continue
        best = []
        for s, (w, t) in N.f.items():
            if abs(len(t) - len(pt)) > max(4, len(pt) // 3):
                continue
            q = difflib.SequenceMatcher(None, pt, t, autojunk=False).ratio()
            if q >= 0.7:
                best.append((q, s))
        best.sort(reverse=True)
        print(f'{name} ref {r:08X} ({len(pt)} insns, {callers(P, r)} ref callers): best ' +
              ', '.join(f'{s:08X} {q:.2f} ({callers(N, s)} callers)' for q, s in best[:5]))


if __name__ == '__main__':
    main()
