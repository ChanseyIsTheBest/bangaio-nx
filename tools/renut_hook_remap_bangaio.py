#!/usr/bin/env python3
"""bangaio-nx (2026-10-29, nights-nx's renut_hook_remap_nights.py with Bangai-O's map): Renut's renderer hooks
(banjo-nx's copy: N&B's addresses, XDK 2.0.7645) at Bangai-O HD's (XDK 2.0.20209), from
out/renut_map/nb_to_bangaio_final.json (tools/renut_hook_map_bangaio.py: the Bejeweled 3, Zuma's Revenge, Peggle 2
and direct routes, and its hand list).

In app/src/renut_engine/gpu:
  - each hook macro BANJO_RENUT_HOOK[_RAW][_SHARED](sub_<N&B>, ...) gets Bangai-O's address and a `// N&B sub_X`
    note; the _SHARED forms become plain ones, except the addresses the port's own code also hooks (NIGHTS_HOOKED:
    the Swap of src/bangaio_frame_hooks.cpp), whose Renut side becomes renut_native_sub_X;
  - a hook whose function Bangai-O does not link goes under `#if 0` (RAW hooks with their body);
  - every other `sub_<N&B>` / `__imp__sub_<N&B>` / `renut_native_sub_<N&B>` whose address is in the map is rewritten;
    the rest are listed for the port to fix by hand.
Idempotent: a line with a `// N&B sub_X` note is rewritten from that note.

  python -I tools/renut_hook_remap_bangaio.py [--check]
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPU = os.path.join(ROOT, 'app', 'src', 'renut_engine', 'gpu')
HOOK = re.compile(r'BANJO_RENUT_HOOK(_RAW)?(_SHARED)?\(\s*sub_([0-9A-Fa-f]{8})')
# bangaio-nx: Bangai-O's own hooks at Direct3D addresses (src/bangaio_frame_hooks.cpp): Renut's side becomes renut_native_sub_X there.
NIGHTS_HOOKED = {'8216F7C8', '8216FE50'}  # D3DDevice_Swap, D3DDevice_Present (Bangai-O presents through it)
REF = re.compile(r'(?<![0-9A-Za-z_])((?:__imp__|renut_native_)?sub_)([0-9A-Fa-f]{8})\b')


def load_map():
    """N&B address -> (NiGHTS address or None, name, evidence), from out/renut_map/nb_to_bangaio_final.json: Peggle 2's
    tree (its hooks' `// N&B sub_X` notes, hand fixes included) then Zuma's Revenge's for what Peggle 2 does not link,
    each through tools/d3d_propagate_p2.py's pairing; N&B's unique shapes for ten lock / desc functions."""
    out = {}
    for k, v in json.load(open(os.path.join(ROOT, 'out', 'renut_map', 'nb_to_bangaio_final.json'))).items():
        out[k.upper()] = ((v['target'] or '').upper() or None, v['name'], v['why'])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    mapping = load_map()
    # Every other N&B address the map knows (the hooks' callees of the original, thunks).
    done = absent = 0
    shared = set()
    left = {}
    report = []
    for d, _, fs in os.walk(GPU):
        for f in fs:
            if not f.endswith(('.cpp', '.h')) or f in ('banjo_shared_hooks.h',):
                continue
            path = os.path.join(d, f)
            text = open(path, encoding='utf-8', newline='').read()
            nl = '\r\n' if '\r\n' in text else '\n'
            lines = text.split(nl)
            out, i, changed = [], 0, False
            while i < len(lines):
                line = lines[i]
                m = HOOK.search(line)
                if m and not line.lstrip().startswith('//') and '#define' not in line:
                    raw, banjo = bool(m.group(1)), m.group(3).upper()
                    note = re.search(r'// N&B sub_([0-9A-F]{8})', line)
                    if note:
                        banjo = note.group(1)
                    if banjo not in mapping:
                        left.setdefault(banjo, []).append(f)
                        out.append(line)
                        i += 1
                        continue
                    nights, name, why = mapping[banjo]
                    if not nights and out and out[-1].startswith('#if 0  // bangaio-nx'):
                        out.append(line)  # already left out by an earlier run
                        i += 1
                        continue
                    if not nights:
                        block = [line]
                        if raw and '{' in line:
                            depth = line.count('{') - line.count('}')
                            while depth > 0 and i + 1 < len(lines):
                                i += 1
                                block.append(lines[i])
                                depth += lines[i].count('{') - lines[i].count('}')
                        out.append(f'#if 0  // bangaio-nx: N&B sub_{banjo} ({name}): {why}')
                        out.extend(block)
                        out.append('#endif')
                        report.append(f'left out: sub_{banjo} {name} ({f}): {why}')
                        absent += 1
                        changed = True
                        i += 1
                        continue
                    form = 'BANJO_RENUT_HOOK' + ('_RAW' if raw else '') + ('_SHARED' if nights in NIGHTS_HOOKED else '')
                    if nights in NIGHTS_HOOKED:
                        shared.add(nights)
                    new = HOOK.sub(lambda _: f'{form}(sub_{nights}', line, count=1)
                    if not note:
                        new += f'  // N&B sub_{banjo}'
                    if new != line:
                        changed = True
                        done += 1
                    out.append(new)
                    i += 1
                    continue
                # Other references: rewrite those the map knows (outside comments that carry the N&B note).
                def sub(mm):
                    addr = mm.group(2).upper()
                    if addr in mapping and mapping[addr][0]:
                        return mm.group(1) + mapping[addr][0]
                    return mm.group(0)
                if '// N&B sub_' not in line and REF.search(line):
                    code, sep, comment = line.partition('//')
                    new = REF.sub(sub, code) + sep + comment
                    for mm in REF.finditer(new.partition('//')[0]):
                        addr = mm.group(2).upper()
                        if addr not in {v[0] for v in mapping.values() if v[0]}:
                            left.setdefault(addr, []).append(f)
                    if new != line:
                        changed = True
                    line = new
                out.append(line)
                i += 1
            if changed and not a.check:
                open(path, 'w', encoding='utf-8', newline='').write(nl.join(out))
    hdr = os.path.join(GPU, 'banjo_shared_hooks.h')
    if not a.check:
        body = ["// bangaio-nx (tools/renut_hook_remap_bangaio.py): the addresses both Renut's renderer and the port's own code hook",
                "// (src/bangaio_frame_hooks.cpp); the port's hook calls renut_native_sub_X when Renut's renderer is chosen.",
                '#pragma once', '', '#include <cstdint>', '', '#include <rex/ppc.h>', '']
        body += [f'extern "C" void renut_native_sub_{x}(PPCContext& ctx, uint8_t* base);' for x in sorted(shared | NIGHTS_HOOKED)]
        open(hdr, 'w', encoding='utf-8', newline='\n').write('\n'.join(body) + '\n')
    print(f'renut_hook_remap_bangaio: {done} hooks at Bangai-O addresses, {absent} left out')
    for r in report:
        print('  ' + r)
    print('N&B addresses still in code (fix by hand):')
    for k, v in sorted(left.items()):
        print(f'  sub_{k}: {sorted(set(v))}')


if __name__ == '__main__':
    sys.exit(main())
