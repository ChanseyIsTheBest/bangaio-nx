#!/usr/bin/env python3
"""bangaio-nx (2026-10-29): Renut's Direct3D device offsets (banjo-nx's code: N&B's values, XDK 2.0.7645) at
Bangai-O HD's (XDK 2.0.20209).

Bangai-O's device is neither N&B's nor Peggle 2's: the public part (0 .. 0x2AC0) is the same, MaxAnisotropy / ZFilter
are private byte arrays as in N&B (Bejeweled 3's +0x2A70 is Bangai-O's 12100), and the private part sits about +176
bytes above N&B's (+212..+220 past 0x3500). So each site is resolved from three measurements of the paired Direct3D
functions (tools/d3d_device_layout.py --dump; out/renut_map/obs_*.json: every offset whose same-shape accesses all
agree):

  NB   N&B -> Bangai-O directly (the site's N&B value);
  P2   Peggle 2 -> Bangai-O (the site's Peggle 2 value from peggle2-nx's out/renut_port/device_offset_sites.json);
  BJ3  Bejeweled 3 -> Bangai-O (Peggle 2's value moved to Bejeweled 3's layout: -24 from 11584, -16 from 13600).

A site takes the value the observations agree on. One with no observation takes the delta of its N&B neighbours when
the nearest observed offsets below and above it (within 64 bytes) have the same delta; anything else is listed for a
hand decision (`--report`). Writes out/renut_map/device_sites_bangaio.json: [{site, code, name, nb, bo, how}].

  python -I tools/renut_device_offsets_bangaio.py [--report]
"""
import argparse
import bisect
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'out', 'renut_map')
SITES = 'D:/peggle 2/peggle2-nx/out/renut_port/device_offset_sites.json'


def load(name):
    return {int(k): v['bo'] for k, v in json.load(open(os.path.join(MAP, name))).items()}


def p2_to_bj3(p):
    if p >= 13600:
        return p - 16
    if p >= 11584:
        return p - 24
    return p


def neighbour_delta(obs, v, reach=64):
    keys = sorted(obs)
    i = bisect.bisect_left(keys, v)
    lo = keys[i - 1] if i > 0 else None
    hi = keys[i] if i < len(keys) else None
    if lo is None or hi is None or v - lo > reach or hi - v > reach:
        return None
    dl, dh = obs[lo] - lo, obs[hi] - hi
    return dl if dl == dh else None


def resolve(nb, p2, onb, op2, obj3):
    answers = {}
    if nb is not None and nb in onb:
        answers['NB'] = onb[nb]
    if p2 is not None and p2 in op2:
        answers['P2'] = op2[p2]
    if p2 is not None and p2_to_bj3(p2) in obj3:
        answers['BJ3'] = obj3[p2_to_bj3(p2)]
    vals = set(answers.values())
    if len(vals) == 1:
        return vals.pop(), 'observed ' + '/'.join(answers)
    if len(vals) > 1:
        return None, 'CONFLICT ' + ', '.join(f'{k}={v}' for k, v in answers.items())
    if nb is not None and nb < 0x2AC0:
        return nb, 'public part (unchanged in every measurement)'
    d = neighbour_delta(onb, nb) if nb is not None else None
    if d is not None:
        return nb + d, f'NB neighbours' + f' {d:+d}'
    if p2 is not None:
        d = neighbour_delta(op2, p2)
        if d is not None:
            return p2 + d, f'P2 neighbours {d:+d}'
    # Array bases and fields reached only through an index: the run they sit in, when the nearest observations on
    # both sides (any distance up to 512 bytes) share one delta in BOTH measurements and the two agree.
    dn = neighbour_delta(onb, nb, 512) if nb is not None else None
    dp = neighbour_delta(op2, p2, 512) if p2 is not None else None
    if dn is not None and dp is not None and nb + dn == p2 + dp:
        return nb + dn, f'run NB {dn:+d} = P2 {dp:+d}'
    if dn is not None and p2 is None:
        return nb + dn, f'run NB {dn:+d} (no Peggle 2 value)'
    return None, f'UNRESOLVED (run NB {dn}, P2 {dp})'


# Decided by hand (2026-10-29), N&B value -> (Bangai-O value, evidence). Bangai-O's instructions are read in its own
# functions (tools/ppc_dis.py) where both measurements were silent.
HAND = {
    # Direct3D_CreateDevice's allocation: see tools/bangaio_renut_port.py (the `li r3` of Bangai-O's create).
    # The fence / critical-section / gamma words past 0x3A00: N&B +212 = Peggle 2 -192 (the runs of both measurements
    # around them: N&B 14824-14832 +212, Peggle 2 13600-14196 / 15220-15340 -192).
    14940: (15152, 'N&B +212 = Peggle 2 15344 - 192'),
    14944: (15156, 'N&B +212 = Peggle 2 15348 - 192'),
    14972: (15184, 'N&B +212 = Peggle 2 15376 - 192'),
    15004: (15216, 'N&B +212 = Peggle 2 15408 - 192'),
    13724: (13936, 'N&B +212 = Peggle 2 14128 - 192 (13600-14196 run)'),
    13608: (13820, 'N&B +212 = Peggle 2 14012 - 192'),
    13640: (13852, 'N&B +212 = Peggle 2 14044 - 192'),
    # The title-device words set to -1: N&B +220 = Peggle 2 23792 - 192 (21940-24448 run; N&B 23980 +220).
    23380: (23600, 'N&B +220 = Peggle 2 23792 - 192'),
    # Tile rects: N&B +176 = Peggle 2 13128 - 200 (13024-13124 and 13368-13560 runs).
    12752: (12928, 'N&B +176 = Peggle 2 13128 - 200'),
    # InitializeHardwareDevice's cleared word: Bangai-O's sub_82177AF0 (paired with Bejeweled 3's sub_82311390) does
    # `li r11,0; stw r11,16928(r31)` (N&B +216).
    16712: (16928, "Bangai-O sub_82177AF0 `stw r11,16928(r31)`"),
    # The tiling and command-buffer words (13112-13220): the functions that write them (Begin / EndTiling, the command
    # buffers) are not linked by Bangai-O, so the words stay 0 there; N&B's +176 run (11848-13184) holds up to 13184.
    13112: (13288, 'N&B +176 run (tiling word; its writers are not linked)'),
    13188: (13364, 'N&B +176 (tiling word; its writers are not linked)'),
    13200: (13376, 'N&B +176 (tiling word; its writers are not linked)'),
    13216: (13392, 'N&B +176 (tiling word; its writers are not linked)'),
    13220: (13396, 'N&B +176 (tiling word; its writers are not linked)'),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()
    onb, op2, obj3 = load('obs_nb.json'), load('obs_p2.json'), load('obs_bj3.json')
    out = []
    for s in json.load(open(SITES)):
        nb, p2 = s.get('banjo'), s.get('peggle')
        if not isinstance(nb, int):
            out.append({**s, 'bo': None, 'how': 'not a single value: by hand'})
            continue
        bo, how = resolve(nb, p2 if isinstance(p2, int) else None, onb, op2, obj3)
        if bo is None and nb in HAND:
            bo, how = HAND[nb][0], 'by hand: ' + HAND[nb][1]
        out.append({'site': s['site'], 'code': s.get('code'), 'name': s.get('name'), 'kind': s.get('kind'),
                    'nb': nb, 'p2': p2, 'bo': bo, 'how': how})
    json.dump(out, open(os.path.join(MAP, 'device_sites_bangaio.json'), 'w'), indent=1)
    # The same list in peggle2-nx's site format, the Bangai-O value in the 'peggle' column, for
    # tools/renut_device_offsets.py (SITES = this file): each site's line is found by its code and its N&B literal
    # replaced.
    sites = []
    for o, s in zip(out, json.load(open(SITES))):
        if o.get('bo') is None:
            continue
        sites.append({**s, 'peggle': o['bo'], 'changed': o['bo'] != s.get('banjo'),
                      'evidence': o['how']})
    os.makedirs(os.path.join(ROOT, 'out', 'renut_port'), exist_ok=True)
    json.dump(sites, open(os.path.join(ROOT, 'out', 'renut_port', 'device_offset_sites.json'), 'w'), indent=1)
    kinds = {}
    for o in out:
        k = o['how'].split(' ')[0]
        kinds[k] = kinds.get(k, 0) + 1
    print(len(out), 'sites:', kinds)
    if a.report:
        for o in out:
            if o['bo'] is None or not o['how'].startswith(('observed', 'public')):
                print(f"  {o['site']:34s} {str(o.get('name')):38s} nb={o.get('nb')} p2={o.get('p2')} -> {o['bo']}  "
                      f"[{o['how']}]")


if __name__ == '__main__':
    main()
