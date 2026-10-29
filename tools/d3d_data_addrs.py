#!/usr/bin/env python3
"""bangaio-nx (2026-10-29, from nights-nx's out/renut_map/data_addrs.py): the guest data addresses Renut's Direct3D
layer reads, at Bangai-O's, from Bejeweled 3's (bejeweled3-nx / zumasrevenge-nx notes: "Guest data"):

  constant blocks   found by content (the reference's bytes, word for word);
  variables         by the instruction that builds them: every `lis` + D-form use in Bejeweled 3's Direct3D range
                    that makes the address, read at the same offset of the paired Bangai-O function
                    (out/renut_map/bj3_to_bangaio.json).

  python -I tools/d3d_data_addrs.py
"""
import bisect
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from d3d_propagate import starts_of, ROOT  # noqa: E402

B = 0x82000000
REF = 'D:/peggle 2/bejeweled3-nx'
P = open(os.path.join(REF, 'out', 'default_image.bin'), 'rb').read()
N = open(os.path.join(ROOT, 'out', 'renut_image.bin'), 'rb').read()
pst = starts_of(os.path.join(REF, 'app', 'generated', 'default'))
p2n = {int(k, 16): int(v['nights'], 16) for k, v in
       json.load(open(os.path.join(ROOT, 'out', 'renut_map', 'bj3_to_bangaio.json'))).items()}


def find_all(img, pat):
    out, i = [], img.find(pat)
    while i != -1:
        if i % 4 == 0:
            out.append(B + i)
        i = img.find(pat, i + 1)
    return out


def refs(img, target, lo, hi):
    hits = []
    for off in range(lo - B, hi - B, 4):
        w = struct.unpack_from('>I', img, off)[0]
        if w >> 26 == 15 and ((w >> 16) & 31) == 0:  # lis rD, hi
            rd, hi16 = (w >> 21) & 31, w & 0xFFFF
            for k in range(1, 16):
                w2 = struct.unpack_from('>I', img, off + 4 * k)[0]
                op = w2 >> 26
                if op in (14, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 48, 50, 52, 54, 58, 62) and \
                        ((w2 >> 16) & 31) == rd:
                    lo16 = w2 & (0xFFFC if op in (58, 62) else 0xFFFF)
                    lo16 -= 0x10000 if lo16 & 0x8000 else 0
                    if ((hi16 << 16) + lo16) & 0xFFFFFFFF == target:
                        hits.append((B + off, B + off + 4 * k))
                    break
    return hits


def by_instruction(name, a, lo=0x822E0000, hi=0x82320000):
    res = {}
    for lis, use in refs(P, a, lo, hi):
        f = pst[bisect.bisect_right(pst, lis) - 1]
        if f not in p2n:
            continue
        nf = p2n[f]
        w = struct.unpack_from('>I', N, nf + (lis - f) - B)[0]
        w2 = struct.unpack_from('>I', N, nf + (use - f) - B)[0]
        if w >> 26 == 15 and w2 >> 26 == struct.unpack_from('>I', P, use - B)[0] >> 26:
            op = w2 >> 26
            lo16 = w2 & (0xFFFC if op in (58, 62) else 0xFFFF)
            lo16 -= 0x10000 if lo16 & 0x8000 else 0
            v = (((w & 0xFFFF) << 16) + lo16) & 0xFFFFFFFF
            res.setdefault(v, []).append(f'{f:08X}->{nf:08X}')
    print(f'{name:24s} BJ3 {a:08X} -> ' + (', '.join(f'{v:08X} ({len(s)} uses: {s[0]})' for v, s in res.items()) or 'none'))


print('-- constant blocks')
for name, a, n in [('kFormatTable', 0x82001620, 128), ('kDeviceCapsVa', 0x82001830, 304), ('kFullViewport', 0x82001284, 24)]:
    print(f'{name:24s} BJ3 {a:08X} -> {[hex(x) for x in find_all(N, P[a - B:a - B + n])][:5]}')
print('kGlobalQwordVa (20209)', [hex(x) for x in find_all(N, struct.pack('>I', 0x00020000))
                                 if struct.unpack_from('>I', N, x - B + 4)[0] >> 16 == 20209][:8])
print('-- variables by the instruction that builds them')
for name, a in [('state table (render)', 0x82AD01E8), ('state table (sampler)', 0x82AD06A8),
                ('kFormatTable', 0x82001620), ('kDeviceCapsVa', 0x82001830), ('kFullViewport', 0x82001284),
                ('kGlobalQwordVa', 0x82AD07A0), ('kVdGlobalDeviceImportSlot', 0x82000618),
                ('kHiZOwnerVa', 0x82B113E0), ('kSkipExportNanVertex', 0x82B103B0), ('kSkipExport512Pixels', 0x82B103B4),
                ('kGameNoLargePagesVa', 0x82B10380)]:
    by_instruction(name, a)
