#!/usr/bin/env python3
"""bangaio-nx: the picture-changing options as separate tomls for the user to decide on. Each is the shipped renut.toml
plus the keys its header names (inserted before the first [section], if any), so a log compares directly with the
shipped one. Nothing here is on in the shipped renut.toml (pixel-identical by default).

  python tools/make_bangaio_configs.py [--base dist/switch/bangaio-nx/renut.toml] [--out dist/switch/configs]
"""
import argparse
import os
import re

CONFIGS = {
    'bangaio_smaa.toml': (
        "SMAA 1x on the 3D image before the HUD (banjo-nx's banjo_renut_smaa): smoother edges, a changed picture.",
        {'banjo_renut_smaa': 'true'}),
    'bangaio_docked_1080.toml': (
        "Docked: the game drawn at 1080 lines and shown at 1080 (banjo-nx's render / display heights): sharper on a\n"
        "1080p TV, more GPU work; handheld unchanged (720).",
        {'banjo_renut_render_height_docked': '1080', 'banjo_renut_display_height_docked': '1080'}),
    'bangaio_handheld_540.toml': (
        "Handheld: the 3D image drawn at 540 lines and scaled to the screen's 720 (the HUD stays at 720): less GPU work,\n"
        "a softer picture. For a console run where the GPU is the limit.",
        {'banjo_renut_render_height_handheld': '540'}),
    'bangaio_dynamic_resolution.toml': (
        "Dynamic resolution (banjo-nx's banjo_renut_dynamic_resolution: steps by the GPU's time against its budget,\n"
        "720 at the top end): the picture changes only when the GPU is late.",
        {'banjo_renut_dynamic_resolution': 'true'}),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='dist/switch/bangaio-nx/renut.toml')
    ap.add_argument('--out', default='dist/switch/configs')
    a = ap.parse_args()
    base = open(a.base, encoding='utf-8').read()
    os.makedirs(a.out, exist_ok=True)
    for name, (what, keys) in CONFIGS.items():
        text = base
        for k, v in keys.items():
            line = f'{k} = {v}'
            pat = re.compile(r'^%s\s*=.*$' % re.escape(k), re.M)
            if pat.search(text):
                text = pat.sub(line, text)
            else:
                m = re.search(r'^\[', text, re.M)
                text = text[:m.start()] + line + '\n' + text[m.start():] if m else text.rstrip('\n') + '\n' + line + '\n'
        head = '# ' + what.replace('\n', '\n# ') + '\n# Changes from renut.toml: ' + ', '.join(keys) + \
               '. NOT pixel-identical: the user decides.\n\n'
        open(os.path.join(a.out, name), 'w', encoding='utf-8', newline='\n').write(head + text)
        print('wrote', os.path.join(a.out, name))


if __name__ == '__main__':
    main()
