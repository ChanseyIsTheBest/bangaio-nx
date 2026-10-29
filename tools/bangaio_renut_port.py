#!/usr/bin/env python3
"""bangaio-nx (2026-10-29, from nights-nx's nights_renut_port.py): the hand edits that move banjo-nx's Renut renderer
to Bangai-O HD (XDK 2.0.20209), after tools/renut_hook_remap_bangaio.py (hooks) and tools/renut_device_offsets.py
(the device-offset sites, out/renut_port/device_offset_sites.json from tools/renut_device_offsets_bangaio.py).
docs/bangaio-notes.md, "Renut's Direct3D layer at Bangai-O's addresses", has the evidence.

  1. guest data addresses (N&B -> Bangai-O), each found by content and by the instruction of the paired Bejeweled 3
     function (tools/d3d_data_addrs.py);
  2. sites the site list cannot express (an array of offsets, the device size);
  3. raw N&B device offsets in banjo-nx's code written after peggle2-nx's site list (2026-10-19), as nights-nx listed
     them, at Bangai-O's layout.
Each edit is an exact (old, new) text pair; a pair whose new text is already there is skipped (idempotent), one whose
old text is missing is reported.

  python -I tools/bangaio_renut_port.py [--check]
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPU = os.path.join(ROOT, 'app', 'src', 'renut_engine', 'gpu')

EDITS = [
    # 1. Guest data addresses.
    ('d3d/d3d_native_state.cpp', 'kRenderStateTable = 0x82E506F0;',
     'kRenderStateTable = 0x824A3460;  // bangaio-nx: N&B 0x82E506F0 (D3D_InitializeApiState sub_82177488)'),
    ('d3d/d3d_native_state.cpp', 'kSamplerStateTable = 0x82E50BD0;',
     'kSamplerStateTable = 0x824A3920;  // bangaio-nx: N&B 0x82E50BD0'),
    ('d3d/d3d_native_state.cpp', 'kFormatTable = 0x820052F8;',
     'kFormatTable = 0x82038F90;  // bangaio-nx: N&B 0x820052F8 (128 bytes identical; 9 aligned uses)'),
    ('d3d/d3d_native_state.cpp', 'kSkipExportNanVertex = 0x82FAD204;',
     'kSkipExportNanVertex = 0x8250C1B4;  // bangaio-nx: N&B 0x82FAD204 (DoBeginExportNanVertex sub_821688A8)'),
    ('d3d/d3d_native_state.cpp', 'kSkipExport512Pixels = 0x82FAD208;',
     'kSkipExport512Pixels = 0x8250C1B8;  // bangaio-nx: N&B 0x82FAD208 (DoEndExport512Pixels sub_82168A00)'),
    ('d3d/hooks/device.cpp', 'kDeviceCapsVa = 0x82183B00;',
     'kDeviceCapsVa = 0x8203AC28;  // bangaio-nx: N&B 0x82183B00 (304 bytes identical; GetDeviceCaps sub_821787C0)'),
    ('d3d/hooks/device.cpp', 'kGlobalQwordVa = 0x82F39B38;',
     'kGlobalQwordVa = 0x824A3A68;  // bangaio-nx: N&B 0x82F39B38 (the build qword, 0x4EF1 = 20209; sub_82177B88)'),
    ('d3d/hooks/device.cpp', 'kVdGlobalDeviceImportSlot = 0x820007FC;',
     'kVdGlobalDeviceImportSlot = 0x82000618;  // bangaio-nx: N&B 0x820007FC (16 aligned uses, as Bejeweled 3)'),
    ('d3d/hooks/draw.cpp', 'kFullViewport = 0x820018DC;',
     'kFullViewport = 0x82039140;  // bangaio-nx: N&B 0x820018DC (24 bytes identical; SetSurfaceInfo sub_8216D308)'),
    ('d3d/hooks/resource.cpp', 'kFormatTable = 0x820052F8;',
     'kFormatTable = 0x82038F90;  // bangaio-nx: N&B 0x820052F8'),
    ('d3d/hooks/resource.cpp', 'kGameNoLargePagesVa = 0x82F39E34;',
     'kGameNoLargePagesVa = 0x8250C18C;  // bangaio-nx: N&B 0x82F39E34 (XPhysicalAlloc sub_82161D10)'),
    ('d3d/hooks/resource.cpp', 'kHiZOwnerVa = 0x82FA36C8;',
     'kHiZOwnerVa = 0x8250C1A4;  // bangaio-nx: N&B 0x82FA36C8 (3 aligned uses)'),
    # 2. Sites the list does not express.
    ('d3d/d3d.h', 'constexpr u32 kDeviceAllocSize = 0x5E00;',
     'constexpr u32 kDeviceAllocSize = 0x5F00;  // bangaio-nx: Direct3D_CreateDevice sub_8216A1E8 `li r3,24320; li r4,128` (N&B 0x5E00)'),
    ('d3d/hooks/device.cpp', 'constexpr u32 kDeviceOffsetsMinusOne[] = {21560, 21564, 14936};',
     'constexpr u32 kDeviceOffsetsMinusOne[] = {21776, 21780, 15148};  // bangaio-nx: N&B {21560, 21564, 14936} '
     '(InitializeHardwareDevice sub_82177BF8 `stw r11,21776` / `21780`; 14936 +212, Peggle 2 15340 - 192)'),
    # 2b. XDK-behaviour differences, each checked in Bangai-O's own code (bejeweled3-nx's / peggle2-nx's fixes where
    # 20209 behaves as 20764 / 21256; banjo-nx's N&B behaviour kept where it behaves as 7645):
    #   - SetTexture(NULL) clears the fetch constant's type bits: Bangai-O's SetTexture sub_82168268 (paired with
    #     Bejeweled 3's sub_82302BC8, unique shape) does `lwzx r10,r11,r31; rlwinm r10,r10,0,0,29; stwx` at 0x82168370.
    ('d3d/d3d_native_state.cpp', '''    device.SetW(Fetch(sampler, 4), dword4);
    device.Dirty(kPendingFetch, FetchBit(sampler));
  }
  device.SetW(off::Textures + sampler * 4, texture);''', '''    device.SetW(Fetch(sampler, 4), dword4);
    device.Dirty(kPendingFetch, FetchBit(sampler));
  } else {
    // bangaio-nx: Bangai-O's SetTexture (sub_82168268, XDK 20209) clears a NULL texture's fetch constant type bits
    // (`lwzx; rlwinm r10,r10,0,0,29; stwx` at 0x82168370), as Bejeweled 3's and Peggle 2's do; N&B's does not.
    device.SetW(Fetch(sampler, 0), device.W(Fetch(sampler, 0)) & ~3u);
  }
  device.SetW(off::Textures + sampler * 4, texture);'''),
    #   - BeginExport keeps N&B's rule (the NaN vertex only for flags 0xA or when the "done" word is 0): Bangai-O's
    #     sub_82168D88 tests [+13716] at 0x82168E34 before calling DoBeginExportNanVertex; banjo-nx's code stands.
    #   - The +16712 clear stands (Bangai-O's sub_82177AF0 `stw r11,16928(r31)`): the site list moves it.
    #   - The 32-byte hardware block: Bangai-O's InitializeHardwareDevice (sub_82177BF8) allocates it itself
    #     (`li r3,32; bl XMemAlloc; stw r3,10900(r31)`, and a 96-byte block for +10896, the completed-fence word's), as
    #     Bejeweled 3's does at +11028 (its notes); N&B's SetRingBufferParameters made both. The interrupt, fence and
    #     present paths read +10900 (sub_8216F020, sub_8216F140, sub_8216F398, sub_82174DB0, sub_82175E38), so the
    #     native device gets one, after the fence word, as bejeweled3-nx's does.
    ('d3d/hooks/device.cpp', '''constexpr u32 kDeviceOffsetFenceCompletion = 10896;
''', '''constexpr u32 kDeviceOffsetFenceCompletion = 10896;
// bangaio-nx: Bangai-O's InitializeHardwareDevice (sub_82177BF8, XDK 20209) gives the device a 32-byte block at +10900
// (`li r3,32; bl XMemAlloc; stw r3,10900(r31)`), which its interrupt, fence and present paths read (sub_8216F020,
// sub_8216F140, sub_8216F398, sub_82174DB0, sub_82175E38); bejeweled3-nx's +11028 at N&B's offset.
constexpr u32 kDeviceOffsetHardwareBlock = 10900;
'''),
    ('d3d/hooks/device.cpp', '''  constexpr u32 kFenceOffset = d3d::kDeviceAllocSize + ((kSideBufferSize + 0x7F) & ~0x7Fu);
  constexpr u32 kBlockSize = kFenceOffset + 0x80;''', '''  constexpr u32 kFenceOffset = d3d::kDeviceAllocSize + ((kSideBufferSize + 0x7F) & ~0x7Fu);
  // bangaio-nx (bejeweled3-nx's form): the 32-byte hardware block (kDeviceOffsetHardwareBlock) follows the fence word.
  constexpr u32 kHardwareBlockOffset = kFenceOffset + 0x80;
  constexpr u32 kBlockSize = kHardwareBlockOffset + 0x80;'''),
    ('d3d/hooks/device.cpp', '''  WriteU32(bytes, kDeviceOffsetFenceCompletion, fence_va);
''', '''  WriteU32(bytes, kDeviceOffsetFenceCompletion, fence_va);
  WriteU32(bytes, kDeviceOffsetHardwareBlock, block_va ? device_va + kHardwareBlockOffset : 0);  // bangaio-nx
'''),
    # 3. Raw N&B offsets in banjo-nx's newer code (nights-nx's list), at Bangai-O's layout. The private words no draw
    # reads: N&B 10880-11775; Bangai-O keeps N&B's offsets below 0x2AC0 and is N&B + 172 at the declaration
    # (0x2E2C -> 0x2ED8), so their end is taken at N&B's + 172 (the smaller of the shifts measured around it), a
    # multiple of 64 from 10112 as the delta units need: 11776 + 128 = 11904 keeps the range inside both.
    ('backend/queued.cpp', 'constexpr u32 kDeltaPrivateUnreadBegin = 10880, kDeltaPrivateUnreadEnd = 11776;',
     'constexpr u32 kDeltaPrivateUnreadBegin = 10880, kDeltaPrivateUnreadEnd = 11904;  // bangaio-nx: XDK 20209 (N&B 10880-11775; the declaration +172)'),
    ('d3d/hooks/device.cpp', 'Video::NoteGameGamma(device + 0x3A9C);',
     'Video::NoteGameGamma(device + 0x3B70);  // bangaio-nx: N&B 0x3A9C (+212, Peggle 2 0x3C30 - 192)'),
    ('d3d/d3d_native.h', 't.chunks[n] |= TouchBits(d3d::kDeviceOffsetStreamSources, 0x3100 - d3d::kDeviceOffsetStreamSources);',
     't.chunks[n] |= TouchBits(d3d::kDeviceOffsetStreamSources, d3d::kDeviceOffsetTextures - d3d::kDeviceOffsetStreamSources);  // bangaio-nx (nights-nx): was N&B 0x3100'),
    ('render/draw.cpp', 'static_assert(kCensusTailBegin < 10880 && 11776 < d3d::kDeviceSnapshotSize);',
     'static_assert(kCensusTailBegin < 10880 && 11904 < d3d::kDeviceSnapshotSize);  // bangaio-nx: XDK 20209 (N&B 10880, 11776)'),
    # Found by a scan of the lines no tool changed for literals in N&B's moved range (0x2E00-0x5E00):
    ('d3d/d3d_native.h', 'constexpr uint64_t kStateTagChunks = TouchBits(0x2780, 0x300) | TouchBits(0x2E00, 0x100);',
     'constexpr uint64_t kStateTagChunks = TouchBits(0x2780, 0x300) | TouchBits(0x2EAC, 0x104);  // bangaio-nx: the private render state at XDK 20209 (N&B 0x2E00-0x2EFF)'),
    ('render/draw.cpp', 'state = XXH3_64bits_withSeed(device_state + 11776, d3d::kDeviceSnapshotSize - 11776, state);',
     'state = XXH3_64bits_withSeed(device_state + 11904, d3d::kDeviceSnapshotSize - 11904, state);  // bangaio-nx: N&B 11776'),
    # (device.cpp's BeginCommandBuffer clears N&B's 0x34D0-0x34E4: Bangai-O does not link the command buffers, so its
    # hook is under #if 0 and that code never runs; left as it is.)
    ('render/draw.h', '''  if (at < 0x2A80)
    return kFieldMisc;
  if (at < 0x2E00)
    return kFieldUnread;
  if (at >= 0x2E2C && at < 0x2E30)
    return kFieldDecl;
  if (at < 0x2F00)
    return kFieldPrivate;
  if (at < 0x3094)
    return kFieldTail;
  if (at < 0x3098)
    return kFieldIndex;
  if (at < 0x30AC)
    return kFieldTargets;
  if (at < 0x3100)
    return kFieldStreams;
  if (at < 0x3168)
    return kFieldTexWords;
  if (at < 0x3184)
    return kFieldTail;
  if (at < 0x3194)
    return kFieldScissor;
  if (at < 0x319C)
    return kFieldShaders;
  if (at < 0x31A4)
    return kFieldTail;
  return kFieldPredication;''', '''  // bangaio-nx: XDK 20209's layout (tools/renut_device_offsets_bangaio.py): N&B's below 0x2AC0, the declaration at
  // +0x2ED8 (N&B +0x2E2C, +172), the private render state from N&B's +0x2E00 + 172 to N&B's +0x2F00 + 176 (MaxAnisotropy
  // and ZFilter are private here as in N&B: +0x2F44 / +0x2F92), and the snapshot's tail (index buffer ... predication)
  // N&B's + 176 (+0x3144 ... +0x3254).
  if (at < 0x2A80)
    return kFieldMisc;
  if (at < 0x2EAC)
    return kFieldUnread;
  if (at >= 0x2ED8 && at < 0x2EDC)
    return kFieldDecl;
  if (at < 0x2FB0)
    return kFieldPrivate;
  if (at < 0x3144)
    return kFieldTail;
  if (at < 0x3148)
    return kFieldIndex;
  if (at < 0x315C)
    return kFieldTargets;
  if (at < 0x31B0)
    return kFieldStreams;
  if (at < 0x3218)
    return kFieldTexWords;
  if (at < 0x3234)
    return kFieldTail;
  if (at < 0x3244)
    return kFieldScissor;
  if (at < 0x324C)
    return kFieldShaders;
  if (at < 0x3254)
    return kFieldTail;
  return kFieldPredication;'''),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    done = skipped = 0
    missing = []
    for rel, old, new in EDITS:
        path = os.path.join(GPU, rel)
        text = open(path, encoding='utf-8', newline='').read()
        crlf = '\r\n' in text
        o, n = (old.replace('\n', '\r\n'), new.replace('\n', '\r\n')) if crlf else (old, new)
        if n in text:
            skipped += 1
            continue
        if o not in text:
            missing.append((rel, old.splitlines()[0]))
            continue
        text = text.replace(o, n, 1)
        done += 1
        if not a.check:
            open(path, 'w', encoding='utf-8', newline='').write(text)
    print(f'bangaio_renut_port: {done} applied, {skipped} already there, {len(missing)} missing')
    for rel, first in missing:
        print(f'  MISSING {rel}: {first}')
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
