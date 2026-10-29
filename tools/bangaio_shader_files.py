#!/usr/bin/env python3
"""bangaio-nx (2026-10-29): Bangai-O's shader files (media/shader/*.xvu, *.xpu: 11 whole containers, header +
virtual + physical part, e.g. tex_ps.xpu 0x154 + 0xA0 = 500 bytes) as run dumps for tools/renut_shader_dump.py:
<out>/{vs,ps}_<xxh3_64 of the container>.bin, the name Renut's renderer looks a shader up by (the low bit of the
magic 0x102A11xx: 1 = vertex shader).

  python tools/bangaio_shader_files.py <game>/media/shader out/bangaio_shader_files
  python tools/renut_shader_dump.py --image out/renut_image.bin --dumps out/bangaio_shader_files --out out/renut_shader_dump
"""
import os
import struct
import sys

import xxhash


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    n = 0
    for name in sorted(os.listdir(src)):
        data = open(os.path.join(src, name), 'rb').read()
        if len(data) < 0x24 or data[:3] != b'\x10\x2a\x11':
            print(f'  skipped {name}: not a shader container')
            continue
        virt, phys = struct.unpack_from('>II', data, 4)
        if virt + phys != len(data):
            print(f'  {name}: header says {virt + phys} bytes, the file has {len(data)}; the header\'s size is used')
            data = data[:virt + phys]
        kind = 'vs' if data[3] & 1 else 'ps'
        dst = f'{kind}_{xxhash.xxh3_64_hexdigest(data)}.bin'
        open(os.path.join(out, dst), 'wb').write(data)
        print(f'  {name} -> {dst}')
        n += 1
    print(f'bangaio_shader_files: {n} containers')


if __name__ == '__main__':
    main()
