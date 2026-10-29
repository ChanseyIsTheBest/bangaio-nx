#!/usr/bin/env python3
"""bangaio-nx (2026-10-29): where each of Renut's Direct3D hooks (banjo-nx's copy: N&B's addresses, XDK 2.0.7645)
lives in Bangai-O HD (XDK 2.0.20209), by three routes through ports that already moved them:

  BJ3  bejeweled3-nx's gpu tree (XDK 2.0.20764, the nearest): its hook lines carry `// N&B sub_X` notes; Bejeweled 3
       -> Bangai-O by tools/d3d_propagate.py (out/renut_map/bj3_to_bangaio.json: unique shapes, the state tables,
       call sites);
  ZR   zumasrevenge-nx's gpu tree (2.0.20871), the same way (out/renut_map/zr_to_bangaio.json);
  P2   peggle2-nx's out/renut_port/hook_map.json (N&B -> Peggle 2, 2.0.21256, with evidence) and
       out/renut_map/p2_to_bangaio.json.

A hook is placed when the routes that answer agree; a disagreement is listed and left out. Lines under `#if 0` in a
reference tree (hooks it does not link, written at another game's addresses) are not read.

  python -I tools/renut_hook_map_bangaio.py
Writes out/renut_map/nb_to_bangaio_final.json ({nb: {target, why, name}}) and prints the coverage.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPU = os.path.join(ROOT, 'app', 'src', 'renut_engine', 'gpu')
MAP = os.path.join(ROOT, 'out', 'renut_map')
HOOK = re.compile(r'BANJO_RENUT_HOOK(?:_RAW)?(?:_SHARED)?\(\s*sub_([0-9A-Fa-f]{8})\s*(?:,\s*([A-Za-z0-9_<>:]+))?')
NOTE = re.compile(r'//\s*N&B sub_([0-9A-Fa-f]{8})')
SUB = re.compile(r'(?<![0-9A-Za-z_])(?:__imp__|renut_native_)?sub_([0-9A-Fa-f]{8})\b')


# Placed by hand (2026-10-29), each with its evidence (tools/d3d_shape_find.py against Bejeweled 3's image; the
# scratch thunk search follows a thunk's branch through bj3_to_bangaio.json):
MANUAL = {
    # Bejeweled 3 and Zuma's Revenge agree (BJ3 82301020's tokens equal one Bangai-O function, 9 callers); Peggle 2's
    # route gives the wrapper peggle2-nx hooked instead (its notes: "Resolve hooked on its wrapper").
    '8222D6C8': ('82174198', 'D3DDevice_Resolve', 'BJ3 sub_82301020 / ZR sub_82327948 agree; exact shape, 9 callers'),
    '82654ED0': ('82168898', 'D3DVertexBuffer_Unlock', 'BJ3 sub_822F91F8: the only function with its tokens, 11 callers'),
    '826561F8': ('82171290', 'D3DDevice_EndIndexedVertices', 'BJ3 sub_82309B18: the only function with its tokens'),
    '8264D8C8': ('8216D9C0', 'D3DDevice_SetRenderTarget_Thunk',
                 'BJ3 sub_822F3BF8 = b 822F3590 (SetRenderTarget, paired 8216D398); the only Bangai-O b 8216D398 thunk'),
    '82655CC8': ('82167C98', 'D3D_Get2DSurfaceDesc_Thunk',
                 'BJ3 sub_82302948 = b 82301C80 (paired 82166E20); the only Bangai-O b 82166E20 thunk'),
    # The direct route paired both N&B functions with 82167CA0 by call alignment. 82167CA0 has GetSurfaceLevel's
    # frame and call: the same nine stack out-pointers, then the level-description helper (82167020) with r4 = 0
    # (face 0) and r5 = the level, then a 48-byte allocation; N&B's GetCubeMapSurface passes the face in r4. So
    # 82167CA0 is GetSurfaceLevel, and Bangai-O does not link GetCubeMapSurface (no function of its shape >= 0.7).
    '82208928': ('82167CA0', 'D3DTexture_GetSurfaceLevel',
                 'frame and helper call equal to N&B 82208928 (face 0 in r4, the level in r5)'),
    '82655CD0': (None, 'D3DCubeTexture_GetCubeMapSurface', 'not linked (no shape match; 82167CA0 is GetSurfaceLevel)'),
}


def walk(root):
    for d, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(('.cpp', '.h')):
                yield os.path.join(d, f)


def lines_outside_if0(path):
    depth0 = None
    depth = 0
    for line in open(path, encoding='utf-8', errors='replace'):
        s = line.strip()
        if s.startswith('#if'):
            depth += 1
            if depth0 is None and re.match(r'#if\s+0\b', s):
                depth0 = depth
        elif s.startswith('#endif'):
            if depth0 == depth:
                depth0 = None
            depth -= 1
        elif s.startswith('#else') and depth0 == depth:
            depth0 = None
        if depth0 is None:
            yield line


def notes_map(tree):
    """N&B address -> the reference's address, from hook lines (and other references) with a `// N&B sub_X` note."""
    out = {}
    for p in walk(os.path.join(tree, 'app', 'src', 'renut_engine', 'gpu')):
        for line in lines_outside_if0(p):
            n = NOTE.search(line)
            if not n:
                continue
            code = line[:n.start()]
            m = HOOK.search(code) or SUB.search(code)
            if m:
                out.setdefault(n.group(1).upper(), m.group(1).upper())
    return out


def pairs(name):
    path = os.path.join(MAP, name)
    if not os.path.isfile(path):
        return {}
    return {k.upper(): v['nights'].upper() for k, v in json.load(open(path)).items()}


def main():
    hooks = {}
    for p in walk(GPU):
        for line in open(p, encoding='utf-8', errors='replace'):
            m = HOOK.search(line)
            if m:
                name = line.split('//')[1].strip() if '//' in line else (m.group(2) or '')
                hooks.setdefault(m.group(1).upper(), (name, os.path.relpath(p, GPU)))
    routes = {
        'Bejeweled 3': (notes_map('D:/peggle 2/bejeweled3-nx'), pairs('bj3_to_bangaio.json')),
        "Zuma's Revenge": (notes_map('D:/peggle 2/zumasrevenge-nx'), pairs('zr_to_bangaio.json')),
    }
    hm = json.load(open('D:/peggle 2/peggle2-nx/out/renut_port/hook_map.json'))
    p2 = {e['banjo_addr'][4:].upper(): (e['peggle_addr'] or '')[4:].upper() or None for e in hm}
    p2_absent = {e['banjo_addr'][4:].upper() for e in hm if e['confidence'] == 'absent'}
    routes['Peggle 2'] = ({k: v for k, v in p2.items() if v}, pairs('p2_to_bangaio.json'))
    # N&B -> Bangai-O directly (tools/d3d_propagate.py with banjo-nx's image as the reference): an older XDK, so
    # fewer pairs, but every one is a unique shape, a state-table row or an aligned call.
    direct = pairs('nb_to_bangaio.json')
    routes['N&B direct'] = ({k: k for k in direct}, direct)
    # Every other N&B address the renderer's code names (the originals its hooks call, thunks, helpers).
    for p in walk(GPU):
        for line in open(p, encoding='utf-8', errors='replace'):
            code = line.split('//')[0]
            if HOOK.search(code) or '#define' in code:
                continue
            for m in SUB.finditer(code):
                hooks.setdefault(m.group(1).upper(), ('(reference)', os.path.relpath(p, GPU)))
    final, conflicts, unplaced = {}, [], []
    for nb, (name, f) in sorted(hooks.items()):
        answers = {}
        for rname, (to_ref, ref_to_bo) in routes.items():
            ref = to_ref.get(nb)
            if ref and ref in ref_to_bo:
                answers[rname] = (ref, ref_to_bo[ref])
        targets = {bo for _, bo in answers.values()}
        if nb in MANUAL:
            bo, mname, why = MANUAL[nb]
            final[nb] = {'target': bo, 'why': 'by hand: ' + why, 'name': name or mname}
        elif len(targets) == 1:
            bo = targets.pop()
            why = '; '.join(f'via {r} sub_{ref}' for r, (ref, _) in answers.items())
            final[nb] = {'target': bo, 'why': why, 'name': name}
        elif len(targets) > 1:
            conflicts.append((nb, name, answers))
        else:
            known = [r for r, (to_ref, _) in routes.items() if nb in to_ref and r != 'N&B direct']
            unplaced.append((nb, name, f, known, nb in p2_absent))
            # Not linked by Bangai-O as far as every route can tell: the remap puts such a hook under #if 0.
            final[nb] = {'target': None, 'name': name,
                         'why': 'not found in Bangai-O by any route (' + (', '.join(known) or 'no reference port links it')
                                + (' / absent in Peggle 2' if nb in p2_absent else '') + ')'}
    os.makedirs(MAP, exist_ok=True)
    json.dump(final, open(os.path.join(MAP, 'nb_to_bangaio_final.json'), 'w'), indent=1)
    agree3 = sum(1 for v in final.values() if v['why'].count('via') >= 2)
    placed = sum(1 for v in final.values() if v['target'])
    print(f'addresses {len(hooks)}: placed {placed} ({agree3} by two or more routes), conflicts {len(conflicts)}, '
          f'unplaced {len(unplaced)}')
    for nb, name, ans in conflicts:
        print('  CONFLICT', nb, name, {r: f'{a}->{b}' for r, (a, b) in ans.items()})
    for nb, name, f, known, absent in unplaced:
        print(f'  unplaced {nb} {name} ({f}); reference addresses known in {known or "none"}'
              f'{"; absent in Peggle 2" if absent else ""}')


if __name__ == '__main__':
    main()
