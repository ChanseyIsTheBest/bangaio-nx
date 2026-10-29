#!/usr/bin/env python3
"""banjo-nx (2026-10-28, the title update): maps guest addresses of the base executable to the title update's, with
tools/map_functions.py's maps, and rewrites files with them.

An address is
- a function start: the function map's new start;
- inside a function (a hook, a call site, a jump-table case): the containing function's pair, and the instruction
  there found by aligning the two functions' instruction lists (the generator's `// mnemonic operands` comments, one
  a 4-byte instruction): the full text with immediates blanked first, then mnemonics only; the instruction at the
  result must have the same mnemonic ('exact'), or the address is reported ('unsure');
- data (outside the code): the data map.
Every rewrite is listed with its kind and confidence; the unmapped and unsure are reported, never guessed silently.

  python tools/remap_addresses.py --maps <dir> --old-gen <dir> --new-gen <dir> [--test-hooks old.toml new.toml]
         [--rewrite file ...] [--dry-run] [--report out.tsv]
"""
import argparse
import bisect
import difflib
import glob
import json
import os
import re
import sys

FUNC = re.compile(r'^DEFINE_REX_FUNC\(([A-Za-z_][A-Za-z0-9_]*)\) \{$')
TABLE = re.compile(r'\{ 0x([0-9A-Fa-f]{8}), ([A-Za-z_][A-Za-z0-9_]*) \}')
INSN = re.compile(r'^\s*// ([a-z][a-z0-9.+\-]*)(?:\s+(.*))?$')
ADDR = re.compile(r'0x8[0-9a-f]{7}', re.I)
IMM = re.compile(r'(?<![rfv])-?\b(?:0x[0-9a-f]+|\d+)\b', re.I)


class Code:
    """One generated tree's functions: starts, and instruction lists on demand."""

    def __init__(self, gen_dir, sigs):
        self.gen_dir = gen_dir
        self.starts = sorted(int(a, 16) for a in sigs)
        self.sigs = sigs
        self.insns = None
        names = {}
        with open(os.path.join(gen_dir, 'renut_init.cpp'), encoding='utf-8', errors='replace') as f:
            for m in TABLE.finditer(f.read()):
                names[m.group(2)] = m.group(1).upper()
        self.names = names

    def load(self, wanted):
        self.insns = {}
        for path in glob.glob(os.path.join(self.gen_dir, '*.cpp')):
            cur = None
            with open(path, encoding='utf-8', errors='replace') as f:
                for line in f:
                    m = FUNC.match(line)
                    if m:
                        n = m.group(1)
                        a = self.names.get(n) or (n[4:] if n.startswith('sub_') else None)
                        cur = a if a in wanted else None
                        if cur:
                            self.insns[cur] = []
                        continue
                    if cur is None:
                        continue
                    i = INSN.match(line)
                    if i:
                        self.insns[cur].append((i.group(1), i.group(2) or ''))

    def containing(self, addr):
        k = bisect.bisect_right(self.starts, addr) - 1
        return '%08X' % self.starts[k] if k >= 0 else None


def norm(insn):
    mnem, ops = insn
    return mnem + ' ' + IMM.sub('#', ADDR.sub('A', ops))


def align_index(old_list, new_list, k):
    """The new index of old instruction k, and how sure ('exact', 'unsure')."""
    for key in (norm, lambda x: x[0]):
        a, b = [key(x) for x in old_list], [key(x) for x in new_list]
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        for tag, i0, i1, j0, j1 in sm.get_opcodes():
            if i0 <= k < i1 and tag in ('equal', 'replace') and (tag == 'equal' or i1 - i0 == j1 - j0):
                kk = j0 + (k - i0)
                if kk < len(new_list) and new_list[kk][0] == old_list[k][0]:
                    return kk, 'exact' if tag == 'equal' else 'replaced'
    return None, 'unsure'


class Mapper:
    def __init__(self, maps, old_gen, new_gen):
        self.fmap = json.load(open(os.path.join(maps, 'func_map.json')))
        self.dmap = json.load(open(os.path.join(maps, 'data_map.json')))
        self.old = Code(old_gen, json.load(open(os.path.join(maps, 'base_sigs.json'))))
        self.new = Code(new_gen, json.load(open(os.path.join(maps, 'tu_sigs.json'))))
        self.lo, self.hi = self.old.starts[0], self.old.starts[-1] + 0x40000

    def prepare(self, addrs):
        need_old, need_new = set(), set()
        for a in addrs:
            if '%08X' % a in self.fmap or not (self.lo <= a < self.hi):
                continue
            f = self.old.containing(a)
            if f in self.fmap:
                need_old.add(f)
                need_new.add(self.fmap[f][0])
        self.old.load(need_old)
        self.new.load(need_new)

    def map(self, a):
        """(new address or None, kind, note)."""
        key = '%08X' % a
        if key in self.fmap:
            nf, st = self.fmap[key][0], self.fmap[key][1]
            return int(nf, 16), 'start', st
        if not (self.lo <= a < self.hi):
            if key in self.dmap:
                y, votes, rivals = self.dmap[key]
                return int(y, 16), 'data', '%d votes%s' % (votes, ', %d rival' % rivals if rivals else '')
            return None, 'data', 'unmapped'
        f = self.old.containing(a)
        if f not in self.fmap:
            return None, 'inside', 'function %s unmapped' % f
        nf, st = self.fmap[f][0], self.fmap[f][1]
        k = (a - int(f, 16)) // 4
        ol, nl = self.old.insns.get(f), self.new.insns.get(nf)
        if ol is None or nl is None or k >= len(ol):
            return None, 'inside', 'no instructions for %s' % f
        if st == 'same':
            return int(nf, 16) + (a - int(f, 16)), 'inside', 'same function'
        kk, how = align_index(ol, nl, k)
        if kk is None:
            return None, 'inside', 'unsure in %s (%s)' % (f, st)
        return int(nf, 16) + kk * 4, 'inside', '%s in %s (%s): %s' % (how, f, st, norm(ol[k]))


TOKEN = re.compile(r'(?<![0-9A-Za-z_])(sub_|0x|rex_\w*?_|)(8[2-9A-Fa-f][0-9A-Fa-f]{6})(?![0-9A-Za-z])')


def hooks(path):
    out = {}
    for blk in re.split(r'\n(?=\[\[)', open(path, encoding='utf-8').read()):
        a = re.search(r'address\s*=\s*(0x[0-9A-Fa-f]+)', blk)
        n = re.search(r'name\s*=\s*"([^"]+)"', blk)
        if a and n:
            out[n.group(1)] = int(a.group(1), 16)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--maps', required=True)
    ap.add_argument('--old-gen', required=True)
    ap.add_argument('--new-gen', required=True)
    ap.add_argument('--test-hooks', nargs=2)
    ap.add_argument('--rewrite', nargs='*', default=[])
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--report')
    a = ap.parse_args()
    m = Mapper(a.maps, a.old_gen, a.new_gen)
    if a.test_hooks:
        o, u = hooks(a.test_hooks[0]), hooks(a.test_hooks[1])
        m.prepare(list(o.values()))
        ok = 0
        for n, addr in o.items():
            if n not in u:
                continue
            got, kind, note = m.map(addr)
            good = got == u[n]
            ok += good
            print('%-34s %08X -> %s  upstream %08X  %s  %s' % (n, addr, '%08X' % got if got else 'NONE', u[n],
                                                                'OK' if good else 'MISS', note))
        print('ok %d of %d' % (ok, sum(1 for n in o if n in u)))
        return
    texts = {}
    addrs = set()
    for p in a.rewrite:
        t = open(p, encoding='utf-8', errors='replace').read()
        texts[p] = t
        for mm in TOKEN.finditer(t):
            addrs.add(int(mm.group(2), 16))
    m.prepare(addrs)
    table = {x: m.map(x) for x in addrs}
    rows = []
    for p, t in texts.items():
        def sub(mm):
            x = int(mm.group(2), 16)
            got, kind, note = table[x]
            if got is None:
                return mm.group(0)
            s = mm.group(2)
            new = ('%08X' % got) if s.isupper() or s.isdigit() else ('%08x' % got)
            return mm.group(1) + new
        out = TOKEN.sub(sub, t)
        for mm in TOKEN.finditer(t):
            x = int(mm.group(2), 16)
            got, kind, note = table[x]
            rows.append((p, '%08X' % x, '%08X' % got if got else '-', kind, note))
        if not a.dry_run and out != t:
            with open(p, 'w', encoding='utf-8', newline='') as f:
                f.write(out)
    unm = sum(1 for v in table.values() if v[0] is None)
    print('%d addresses: %d mapped, %d not' % (len(table), len(table) - unm, unm))
    if a.report:
        with open(a.report, 'w', encoding='utf-8') as f:
            for r in rows:
                f.write('\t'.join(r) + '\n')


if __name__ == '__main__':
    main()
