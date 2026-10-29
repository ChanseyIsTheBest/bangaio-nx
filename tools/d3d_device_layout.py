#!/usr/bin/env python3
"""bangaio-nx (2026-10-29): Bangai-O's Direct3D device layout (XDK 2.0.20209) against a reference's, measured as
zumasrevenge-nx measured Zuma's Revenge's against Bejeweled 3's: over the paired functions of the two Direct3D
libraries (out/renut_map/<ref>_to_bangaio.json) whose instruction counts are equal and whose tokens align one to one,
every D-form load / store whose displacement differs gives a (reference, Bangai-O) offset pair. Offsets are reported
per reference value with how many accesses agree, then folded into ranges of one delta.

  python -I tools/d3d_device_layout.py --ref-image <img> --ref-gen <dir> --pairs bj3_to_bangaio.json
         --ref-range 822F0000:82312000 [--min 0x2000]
"""
import argparse
import os
import struct
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from d3d_propagate import Img, starts_of, TGT_CODE, ROOT  # noqa: E402
import json  # noqa: E402

DFORM = {32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 14}
DS = {58, 62}


def disp(w):
    op = w >> 26
    if op in DFORM:
        d = w & 0xFFFF
        return d - 0x10000 if d & 0x8000 else d
    if op in DS:
        d = w & 0xFFFC
        return d - 0x10000 if d & 0x8000 else d
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref-image', required=True)
    ap.add_argument('--ref-gen', required=True)
    ap.add_argument('--pairs', required=True)
    ap.add_argument('--ref-range', required=True)
    ap.add_argument('--min', default='0x2A00')
    ap.add_argument('--max', default='0x6000')
    # --dump: out/renut_map/<name> gets {reference offset: Bangai-O offset} for every offset whose accesses all agree
    # and whose delta is under 1024 (larger ones pair stack or other structures' fields by chance).
    ap.add_argument('--dump', default='')
    a = ap.parse_args()
    lo, hi = (int(x, 16) for x in a.ref_range.split(':'))
    dmin, dmax = int(a.min, 16), int(a.max, 16)
    P = Img(a.ref_image, starts_of(a.ref_gen), 0x82000000, 0x83000000)
    N = Img(os.path.join(ROOT, 'out', 'renut_image.bin'), starts_of(os.path.join(ROOT, 'app', 'generated')),
            TGT_CODE[0], TGT_CODE[1])
    pairs = {int(k, 16): int(v['nights'], 16) for k, v in json.load(open(os.path.join(ROOT, 'out', 'renut_map', a.pairs))).items()}
    obs = defaultdict(Counter)
    used = 0
    for p, n in pairs.items():
        if not (lo <= p < hi) or p not in P.f or n not in N.f:
            continue
        pw, pt = P.f[p]
        nw, nt = N.f[n]
        if len(pw) != len(nw) or pt != nt:
            continue
        used += 1
        for x, y in zip(pw, nw):
            dx, dy = disp(x), disp(y)
            if dx is None or dy is None or x >> 26 == 14:
                continue
            if dmin <= dx <= dmax:
                obs[dx][dy] += 1
    print(f'{used} same-shape function pairs in the reference range')
    rows = []
    for dx in sorted(obs):
        dy, c = obs[dx].most_common(1)[0]
        tot = sum(obs[dx].values())
        rows.append((dx, dy, c, tot))
    # fold into delta runs
    runs = []
    for dx, dy, c, tot in rows:
        d = dy - dx
        if runs and runs[-1][2] == d:
            runs[-1][1] = dx
            runs[-1][3] += 1
            runs[-1][4] += c
        else:
            runs.append([dx, dx, d, 1, c])
    for r0, r1, d, n, c in runs:
        print(f'  ref {r0:6d}-{r1:6d} ({r0:#06x}-{r1:#06x}): delta {d:+5d}  ({n} offsets, {c} accesses)')
    if a.dump:
        good = {}
        for dx, dy, c, tot in rows:
            plausible = {y: k for y, k in obs[dx].items() if abs(y - dx) < 1024}
            if len(plausible) == 1:
                y, k = next(iter(plausible.items()))
                good[dx] = (y, k)
        json.dump({str(k): {'bo': v[0], 'n': v[1]} for k, v in sorted(good.items())},
                  open(os.path.join(ROOT, 'out', 'renut_map', a.dump), 'w'), indent=0)
    bad = [(dx, dict(obs[dx])) for dx, dy, c, tot in rows if c != tot]
    if bad:
        print('offsets with more than one answer:')
        for dx, o in bad[:40]:
            print('   ', dx, o)


if __name__ == '__main__':
    main()
