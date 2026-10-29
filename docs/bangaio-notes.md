# Bangai-O HD: Missile Fury port: notes

This file records the port: what each step found, with its evidence. The project is a copy of banjo-nx's tree at its
HEAD `be8476a3` (2026-10-28: the renderer state its docs describe), taken as the base as the user asked. The app-side
split of banjo-nx's N&B-only sources (`app/CMakeLists.txt` `BANGAIO_NB_SOURCES`, `src/bangaio_dropped_cvars.cpp`) and
the analysis tools marked "nights-nx" come from the NiGHTS port (`D:\nights\nights-nx`), which started from the same
banjo-nx state an hour earlier. Comments that say "banjo-nx", "nights-nx", "peggle2-nx", "bejeweled3-nx" or
"zumasrevenge-nx" record findings from those ports.

Credits: reNut's renderer (masterspike52; reuse in the user's ports permitted), sa2-nx (input, CPU rounds),
NetherSX2_nx (four-core layout, MIT), battd_nx (the GPU arena), bejeweled3-nx and the zuma ports (the hot-function
method, the Direct3D-layout tools), nights-nx (the hook pairing tools). GPL-3.0 where the sources are. Game data is never
committed or distributed.

## The game (2026-10-29)

- The user's file is `D:\bango\Bangai O HD Missile Fury.rar`: one package, `Bangai O HD Missile Fury/58410AF2/000D0000/
  A571FFD0...`, an XBLA game (content type `0x000D0000`), title **58410AF2**, a read-only LIVE STFS volume, no title
  update or DLC. `tools/stfs_extract.py` read its 65,997 blocks: 868 entries, 255.6 MiB, into `D:\bango\game` (outside
  the repository). The build reads it from `app/assets` (git-ignored; `default.xex` copied there).
- **`default.xex`** (`tools/xex_info.py`): original PE name `Bangai-O.exe`, base `0x82000000`, entry `0x82163960`,
  image size `0x590000`. Imports `xam.xex` (176) and `xboxkrnl.exe` (354), 2.0.20209. Static libraries: XDK
  **2.0.20209** (XAPILIB, D3D9 / XGRAPHC 20209.3, D3DX9, XAUDIO2, XAPOBA, XACT3, X3DAUD, VCOMP, XINP2, XONLINE, XNET,
  XUIRNDR, XUIRUN, QNETXA2, XRNSS, XRNMS, XCAM, XMEDIA2, XHV2, XPARTY, XMCORE, XAUD), MSVC 16.0.10224. The nearest XDKs
  already ported: Bejeweled 3's 20764, then Zuma's Revenge's 20871.
- **Sections** (PE header of the loaded image, `out/renut_image.bin`): `.rdata 82000400-820AE46C`, `.pdata
  820AE600-820BE1C0`, `.text 820C0000-82491544` (3.8 MB of code), `.embsec_ 82491600-82496138`, `.data
  824A0000-82547258`, `.XBMOVIE`, `.idata 82550000`, `.XBLD`, `.reloc`.
- **Data** (`media/`): `back_bg`, `bg`, `font`, `hit`, `icon`, `light`, `map`, `model`, `obj`, `replay`, `shader`,
  `sound`; the achievement icons, `ArcadeInfo.xml`, `icon64.png`.

## Code generation (2026-10-29)

`tools/codegen.ps1` (nights-nx's; `rexglue codegen renut_manifest.toml`, image dumped to `out/renut_image.bin`) with
banjo-nx's built generator (`sdk/out/win-amd64/rexglue.exe` of 10-20; the codegen sources last changed 10-19) runs in
19 s and writes 141 files (68 MB) into `app/generated`. The build then uses the generator it builds from `sdk/`.

- **First run**: no "target not in any function", no unresolved branch.
- **setjmp / longjmp** by shape, as in zumasrevenge-nx and nights-nx: setjmp `0x82425E30` (a hook word at `0x82547248`
  tried first, `bnectr`, then `mflr`, `mfcr`, `stfd f14,0(r3)` at `0x82425E4C`: the only one in the image), longjmp
  `0x824258F0` (`mr r6,r4`, the check of +312, `mr r7,r3`, `lfd f14,0(r7)` at `0x8242592C`: the only one).
  `app/config/renut_funcs.toml`.
- **Pointer sweep** (`tools/pointer_fixpoint.py`, `REXGLUE` = banjo-nx's generator): pass 1, 5,722 gaps, 54 candidates,
  39 accepted (11 no code, 2 SEH scope labels, 1 tail branch into a body, 1 fragment); fixpoint in pass 2.
- **Jump tables** (`tools/switch_check.py --code 820C0000:82491544`): 121 tables in the binary (79 absolute, 22 byte,
  20 half), 121 `switch` statements generated (the checker does not read the `ctx.rN.u32` spelling, as nights-nx
  found, so its bound checks report nothing).
  - **`sub_822A89A0`'s byte table has no bound in the code** (`lwz r11,272(r3); addi r11,r11,-1`, table 0x82074B70):
    the generator read 40 entries, past the 16 that target this function into the next table's bytes, whose targets
    run into `sub_822A8AF0`'s body; the first build failed on undeclared labels (`loc_822A8EC0` .. `loc_822A90B8`).
    The 16 real entries are given in `app/config/renut_switch_tables.toml` (entry 4 is the tail call to `0x822A8AF0`).
- **Register locals** (zumasrevenge-nx's / nights-nx's audited set: CR / CTR / XER / reservation and the
  non-volatiles as locals, `skip_msr`, the float-mode diet; `non_argument_as_local` and `elide_lr_stores` left out until
  they have Bangai-O's audit). `tools/read_before_write.py app/generated` reported 18:
  - v64-v72 read and never written by XDK library code: v69 / v72 by `sub_823AEDD0`, `sub_823AF408`, `sub_823DA3B0`,
    `sub_82462B20`, `sub_82462EC8`, `sub_82463188`, `sub_824633F0`; v64 / v65 by `sub_824644F8`:
    `non_volatile_as_local_keep = ["v64-v72"]`, Zuma's Revenge's and NiGHTS's range.
  - harmless, as banjo-nx and nights-nx classified the same shapes: `xor r30,r30,r30` (`sub_82164810`,
    `sub_82164BA0`); setjmp's callers' `env.rN = rN` copies (`sub_82189F28`, `sub_8218AC98`, `sub_8219F1F0`) and
    setjmp itself; `subfe` of one register (`sub_821F2E20`); software-pipelined vector loops in functions that save
    their own registers (`sub_823B08C8`, `sub_823B1268`); `sub_822A89A0`'s reads were on the bogus table entries.
- banjo-nx's per-function lists were N&B's and are empty here until Bangai-O has its own census or profile (taken from
  nights-nx's emptied copies): `app/indirect_promotions.txt`, `app/config/{hot_edges,hot_functions,locals_optout,
  switch_goto}.txt`, `app/config/{lr_write_same_choice,r1_local_choice}.json`, `app/src/cpu/hot/{localized,
  localized_bulk,hand}.txt`.
- **N&B hooks in the app** (scratchpad `sub_collisions.py`: `sub_X` names the app's sources hook that are Bangai-O
  function starts): 9, all in Renut's Direct3D layer (remapped below), `townsfolk.cpp` / `frontend_debug_menu.cpp`
  (N&B-only sources, not built) and `guest/widescreen.cpp` (N&B's widescreen hooks, see below). None in the sources
  the first build compiles.

## Renut's Direct3D hooks at Bangai-O's addresses (2026-10-29)

Three ports already moved banjo-nx's hooks to their XDKs, each with notes naming the N&B function: bejeweled3-nx
(20764), zumasrevenge-nx (20871) and peggle2-nx (21256, `out/renut_port/hook_map.json` with evidence for all 361).
`tools/d3d_propagate.py` (nights-nx's `d3d_propagate_p2.py` with the reference's and the target's state tables as
arguments) pairs each reference's functions with Bangai-O's: unique shapes (opcode / register tokens, no immediates),
the two state tables, then the aligned `bl` call sites to a fixpoint.

- **State tables** (`{getter, setter, default}` rows, stride 12), found by Bejeweled 3's default column word for word:
  render states `0x824A3460` (101 rows), sampler states `0x824A3920` (20 rows). Zuma's Revenge's and N&B's default
  columns find the same two.
- **Pairs**: Bejeweled 3 2,550 (1,695 unique shapes, 640 calls, 224 table cells), Zuma's Revenge 2,536, Peggle 2 1,979,
  N&B directly 1,380.
- `tools/renut_hook_map_bangaio.py` combines the routes (N&B -> reference by its notes or hook map, reference ->
  Bangai-O by the pairs) into `out/renut_map/nb_to_bangaio_final.json`: of 371 N&B addresses the renderer names (361
  hooks and 10 other references), **325 placed, 309 of them by two or more routes that agree**; the one conflict
  (Resolve: Peggle 2's route gives the wrapper peggle2-nx hooked) resolved for Bejeweled 3's / Zuma's Revenge's answer.
- **By hand** (`MANUAL` in the tool, each with its evidence): Resolve `82174198`, VertexBuffer_Unlock `82168898`,
  EndIndexedVertices `82171290` (each the only function with the reference's tokens), SetRenderTarget_Thunk `8216D9C0`
  and Get2DSurfaceDesc_Thunk `82167C98` (two-instruction thunks, 104 of that shape: the one that branches to the
  paired target), GetSurfaceLevel `82167CA0` (the direct route had paired GetCubeMapSurface with it too; its frame and
  helper call are GetSurfaceLevel's: face 0 in r4).
- **Not linked by Bangai-O** (no route finds them, no function of their shape): SetVertexShaderConstantB / I,
  SetPixelShaderConstantB / I, ConstantBuffer_Unlock, CreateIndexBuffer, IndexBuffer_Lock, Acquire / Release
  ThreadOwnership (their device-word patterns are nowhere in the code), InsertCallback, GetDisplayMode, the tiling
  and command-buffer functions, the tessellated draw, GetCubeMapSurface, Present, IsFusion.

## Renut's Direct3D layer at Bangai-O's addresses (2026-10-29)

Applied in this order (each tool is idempotent): `tools/renut_hook_remap_bangaio.py` (324 hook lines at Bangai-O's
addresses with a `// N&B sub_X` note, 37 under `#if 0`), `tools/renut_device_offsets.py` on
`out/renut_port/device_offset_sites.json` (written by `tools/renut_device_offsets_bangaio.py`: 144 sites rewritten),
`tools/bangaio_renut_port.py` (25 hand edits).

**The device layout** (`tools/d3d_device_layout.py`: over the same-shape pairs of the two Direct3D libraries, every
D-form displacement that differs; 282 pairs with N&B, 603 with Peggle 2, 541 with Bejeweled 3). XDK 20209's device is
neither N&B's nor Peggle 2's:

| N&B offsets | Bangai-O | Evidence |
|---|---|---|
| 0 .. 0x2ABF (public) | the same | 39 offsets / 171 accesses (N&B), 76 / 312 (Peggle 2: also unchanged) |
| 0x2A80 .. 0x2B4F (fences, flags, predication args, GPR allocation) | the same | Peggle 2 -> Bangai-O -128 (19 offsets, 152 accesses) = Peggle 2's +128 undone |
| 0x2E2C (vertex declaration) | +172 (0x2ED8) | all three |
| 0x2E48 .. 0x3384 (private render state, MaxAnisotropy / ZFilter (private, as N&B's), the snapshot tail: index buffer, targets, streams, texture words, scissor, shaders, predication) | +176 | N&B 28 + 25 offsets; Peggle 2 -200 (60 + 80 accesses) |
| 0x3500 .. 0x3A9C (present interval, ring and fence words, critical sections, gamma ramp) | +212 | N&B 0x351C, 0x39E8-0x39F0; Peggle 2 -192 (77 + 68 accesses) |
| 0x4158 .. 0x54AC | +216 | N&B 2 offsets; Peggle 2 -192 |
| 0x5DAC (behaviour flags 2) | +220 | all three |
| device size 0x5E00 | 0x5F00 | Direct3D_CreateDevice sub_8216A1E8 `li r3,24320; li r4,128` |

291 sites of peggle2-nx's list (N&B and Peggle 2 values): 222 observed (the measurements that answer agree), 23 in the
public part, 22 from the delta of the observed neighbours in both measurements, 20 decided by hand
(`HAND` in the tool, each with its evidence), 4 by the bangaio_renut_port edits (the device size and the -1 words
`{21776, 21780, 15148}`: InitializeHardwareDevice sub_82177BF8 `stw r11,21776` / `21780`). Two more N&B literals
found by scanning the lines no tool changed: `kStateTagChunks`' private render state (N&B 0x2E00-0x2EFF -> 0x2EAC +
0x104) and a census hash's tail.

The renderer's field classes (`render/draw.h` FieldOfOffset) at XDK 20209: Misc below 0x2A80, Unread to 0x2EAC
(N&B 0x2E00 + 172, the smaller of the two shifts around it), Decl 0x2ED8, Private to 0x2FB0, then N&B's classes + 176
(index 0x3144, targets 0x3148, streams 0x315C, texture words 0x31B0, scissor 0x3234, shaders 0x3244, predication
0x3254); the delta chain's private unread words 10880-11903 (a multiple of 64 inside the unread range).

**Guest data** (`tools/d3d_data_addrs.py`: by content and by the instruction of the paired Bejeweled 3 function; the
two agree for every one):

| What | Bangai-O | N&B | Evidence |
|---|---|---|---|
| state tables | `0x824A3460` / `0x824A3920` | `0x82E506F0` / `0x82E50BD0` | Bejeweled 3's default columns word for word; D3D_InitializeApiState sub_82177488 |
| format table | `0x82038F90` | `0x820052F8` | 128 bytes equal; 9 aligned uses |
| caps | `0x8203AC28` | `0x82183B00` | 304 bytes equal; GetDeviceCaps sub_821787C0 |
| full viewport | `0x82039140` | `0x820018DC` | 24 bytes equal; SetSurfaceInfo sub_8216D308 |
| build qword | `0x824A3A68` | `0x82F39B38` | `0x000200004EF1xxxx` (0x4EF1 = 20209); sub_82177B88 |
| `VdGlobalDevice` slot | `0x82000618` | `0x820007FC` | 16 aligned uses (as Bejeweled 3) |
| HiZ owner | `0x8250C1A4` | `0x82FA36C8` | 3 uses |
| export switches (NaN vertex / 512 px) | `0x8250C1B4` / `0x8250C1B8` | `0x82FAD204` / `0x82FAD208` | DoBeginExportNanVertex sub_821688A8, DoEndExport512Pixels sub_82168A00 |
| no-large-pages flag | `0x8250C18C` | `0x82F39E34` | XPhysicalAlloc sub_82161D10 |
| GetCurrentThreadId | `sub_8243A860` (named `rex_GetCurrentThreadId`) | | `lwz r11,256(r13); lwz r3,332(r11); blr` |
| XMemFree (D3D's) | `sub_82165530` | `sub_822399D8` | the direct route's call alignment |
| D3DDevice_Swap | `sub_8216F7C8` | `sub_82287590` | Bejeweled 3 / Zuma's Revenge routes; the frame hook (`src/bangaio_frame_hooks.cpp`, presentation interval +13808) |

**XDK behaviour**, each read in Bangai-O's own code:
- SetTexture(NULL) clears the fetch constant's type bits (sub_82168268 at 0x82168370: `lwzx; rlwinm r10,r10,0,0,29;
  stwx`), as Bejeweled 3's / Peggle 2's: their fix is ported.
- BeginExport keeps N&B's rule (sub_82168D88 tests the "done" word +13716 before DoBeginExportNanVertex): banjo-nx's code
  stands, unlike Bejeweled 3 / Peggle 2.
- InitializeHardwareDevice's cleared word exists (sub_82177AF0 `stw r11,16928(r31)`, N&B +16712): kept, moved.
- InitializeHardwareDevice allocates the 32-byte hardware block at +10900 itself (`li r3,32; bl XMemAlloc; stw
  r3,10900(r31)`, and the 96-byte completed-fence block at +10896), as Bejeweled 3 does at +11028; N&B's
  SetRingBufferParameters made both. The interrupt, fence and present paths read +10900, so the native device gets
  bejeweled3-nx's block (after the fence word), at N&B's offset.

**N&B game hooks in Renut's tree**: `guest/widescreen.cpp`, `guest/photo_capture.cpp` (N&B's widescreen pools and photo
mode) are under `#if 0` (their functions are not Bangai-O's; `sub_823ED828` is a Bangai-O function start, so leaving
the hook would have replaced an unrelated function). `render/graphics_options.h` names N&B functions only in comments.

## SDK fixes from the Peggle 2 session's ports (2026-10-29)

The Peggle 2 session sent its list of SDK fixes for XBLA games (Zuma's Revenge 1.0.1's `sdk/src`, console-tested).
Taken where Bangai-O can meet them and banjo-nx's SDK lacks them:

- whole files, the change only adding to banjo-nx's: `core/filesystem_posix.cpp` (on Horizon every read and write in
  1 MB pieces through a host buffer: guest memory is refused as an IPC buffer, and one 22.9 MB read froze Peggle's
  console; Bangai-O's sound files are 74 MB), `kernel/xam/apps/xgi_app.cpp` (XUserReadStats fails and zeroes the
  results header: no leaderboards without Xbox Live), `kernel/xam/xam_user.cpp` (the stats enumerators fail; guest
  sign-in for a second controller), `core/memory_switch.cpp` + `guest_memory_switch.{cpp,h}` (a decommitted range
  reads as zeros when committed again), `kernel/xboxkrnl/xboxkrnl_usbcam.cpp` (Xbox Live Vision "not connected");
- by hand: `system/xthread.cpp` XHostThread::Execute initialises the host FPSCR policy (an audio callback on a host
  thread trapped on an inexact vcfsx in Zuma), `ui/rex_app.cpp` resets the runtime before the window (a std::terminate
  log at every console exit);
- not taken: zumasrevenge-nx's `runtime.cpp` / `rex_app.cpp` whole (they carry its asset-pack device, which banjo-nx's
  SDK has not, and lack banjo-nx's four-core start-up); its offline sockets (`xsocket.cpp`, `xam_net.cpp`): banjo-nx's
  `guest_network = false` already makes socket() fail with WSAENETDOWN, as with the cable unplugged.

The XBLA licence: the SDK's `license_mask` is 0 (the trial) by default; the runs and the shipped tomls set 1.

## Four-core mode's forwarder (2026-10-29)

**Decision**: Bangai-O's forwarder program id is `0x05BA6A1000001000` (`tools/forwarder/bangaio_forwarder.json`,
banjo-nx's NetherSX2_nx-derived NPDM with that id; `bangaio_main.npdm` built with devkitPro's npdmtool; the SDK's
`banjo_forwarder_program_id` default). A forwarder made with another id needs that id in `renut.toml`.

## First boots on the PC (2026-10-29)

**banjo-nx's tree did not build Renut for the PC** (its 10-27/28 rounds were built for the Switch only; nights-nx found
the same three): the shared-constant helpers (`SameBytes`, `SetShared`, `g_draw_sc`, `PersistentSharedVerifyOn`)
inside `render/draw.cpp`'s deko3d-only block (moved out; the pushed-uniform half and its report counters stay
deko3d-only), the scale tables' setter lambda in `surfaces.cpp` outside its `#if`, two `RepeatCensusReport`s in one
namespace (the recording one is `RecordingRepeatCensusReport`), a local named `far` (a Windows macro) in
`command_buffers.cpp`; and `me_pc_stubs.cpp` (the Switch profiler's counters as no-ops) had gone with the N&B sources.
The device layout's own asserts: 40 compared delta chunks (N&B 39), a 24-byte last snapshot chunk (N&B 40:
`TakeLastChunk`'s NEON loads rewritten for 16 + 8 bytes).

- **The PC build always opened banjo-nx's path wizard** and waited for a click (the first boots stopped right after the
  GPU's set-up, 0.3 s of CPU in 15 s). A game folder that holds `default.xex` (`game_root` beside the exe, or
  `--game_data_root`) now skips it (`renut_app.h` OnFinalizePaths), keeping the run's own user data folder.
- **Runs**: `tools/bangaio_pc_run.ps1` (muted, minimised, `--license_mask=1` for the full game, `--headless=true` so a
  message box takes its focused button, as nights-nx found for the save-data prompt), log from the exe's `logs/`
  (with `--log_file` the GPU plugin's logger reopened the same file and the app's lines were lost).
- `renut2` (Renut on D3D12, RTX 3060): the device is created (type 1), the render thread starts, the XAudio render
  driver registers (callback `0x821D7AC0`), the light and font files load; then **"Call to invalid or unregistered
  function at guest address 0x8224D630"**: a 20-instruction leaf whose address is built at `0x8224D7EC` and passed at
  run time (the pointer sweep had rejected it as a fragment because it reads r5, an argument register). Declared.
- **Bangai-O asks for the automatic front buffer** ("InitializePresentationParameters: an automatic front buffer is not
  supported"), as Bejeweled 3 and Peggle 1 do: Bangai-O's InitializePresentationParameters (sub_821776F0) `lwz
  r11,60(r31)` then CreateTexture sub_82167EE8(w, h, 1, 1, 0, format, 0, 3) and `stw r3,15040(r29)` (N&B +14828 + 212,
  where the layout put it). bejeweled3-nx's creation and its `native::CreateTexture` are ported; banjo-nx's Present
  already resolves the back buffer into the front buffer when there is one.

## The first Switch NRO in Ryujinx (2026-10-29)

- **Shaders** (`tools/bangaio_switch_shaders.ps1`: the PC build's XenosRecomp with the deko3d SPIR-V dump and the
  early-alpha HLSL, then banjo-nx's `deko3d_shaders.py`, `deko3d_glsl_opt.py --check`, `deko3d_shader_package.py`,
  `renut_switch_shader_cache.py`): all 95 compile with uam (76 vertex, median 32 KB, the largest 207 KB; 19 pixel, median
  1 KB); the GLSL package is 533 KB, the Switch shader cache table 19 KB + 543 KB of SPIR-V.
- **Build** (`tools/switch_build_bg.bat`, devkitA64, deko3d only: `REXGLUE_SWITCH_NVK` OFF, no LTO, no PGO): from scratch
  in about 25 minutes; `renut.nro` 30.7 MB.
- `emu1` (Ryujinx, 150 s; data folder `ryu-data\bangaio`, the SD's `switch\bangaio-nx\game_root` a junction to
  `D:\bango\game`): the Treasure logo, the loading screen, the title, Single Player's stage select (Stage 1, the player
  settings), Dr. Ban's briefing. **60.0 fps** throughout (deko3d presents on the display's refresh), render thread
  1.7-1.9 ms a frame, 16 draws a frame in the menus.
- `emu2` (240 s, START, A presses, the sticks wandering from 60 s): Stage 1 played to a GAME OVER. The heaviest moment,
  the game-over explosion with hundreds of missiles: about 1,130 draws a frame, the render thread 27-30 ms a frame,
  26-28 fps (in the emulator, whose timing is not the console's). 59.4 % of the draws on the fast path; the rest leave
  it for their call kind (the immediate-vertex draws: DrawVerticesUP / BeginVertices, Bangai-O's sprites).
- The verify keys (fast draw, tags, chain reuse, whole buffers, store cards, persistent shared, push constants, texture
  queries): 0 differences, but for `banjo_renut_fast_draw_verify: the kept or cached pipeline differs from the one made`,
  3 times a run: the same key with another pipeline object (the provisional pipeline of an asynchronous variant
  compile against the finished one), not a different state.

## Renderer census (porting-guide-renderer.md section 2, 2026-10-29)

| Question | Bangai-O | How |
|---|---|---|
| Where draws come from | 100 % immediate (no recorded command buffers) | `draw sources:` line: 947,938 immediate, 0 replayed |
| Draws a frame | 16 (menus) to ~1,130 (a heavy stage moment) | the 10 s report |
| How state is set | the game's inline Direct3D header code and D3D's setters; `m_Pending` dirty masks as N&B's (MSB-first groups) | the inline callers of SetVertexShaderConstantF (`li r7,3; rldicr r7,r7,59,4` for registers 13-16) |
| Shadow passes | none to speak of: 100-300 depth-only draws per 10 s at 650 fps (under one a frame) | `draw kinds:` line |
| Memexport | none seen | no memexport lines |
| Threads (emulator) | render thread 84.5 % of core 1; main thread 30 %; Audio Worker 10 %; eight game worker threads 1-6 % each | `rex_profile.log` |

So the record-time items (setter marks, record-time objects, the replay stream: banjo-nx's 4.1-4.6g) do not apply:
they work on recorded command buffers. What Bangai-O's draws use is the immediate path: device captures (deltas or
whole copies), the chain's reuse, and the fast path for whole-snapshot draws (A/B 62).

**Snapshot deltas: fixed and on from v3** (section "The stale c24-c27 found" below). Until then:
`banjo_renut_snapshot_deltas_verify` found 1,302,663 of 1,317,470 draws
rebuilt with a stale vertex constant (c24, +2304: 0x3F.. against the device's 0x44..), and with deltas on the menu's sky
panels drew rotated over grey and the attract demo's playfield was missing. With whole copies the attract demo, the
menus and gameplay draw correctly. The vertex constants a delta carries are the groups `m_Pending[0]` marks; checked
so far: the game's setter calls build their masks as N&B's do, Renut consumes the masks only at draws, XDK 20209's own
SetVertexShader clears the marks of the shader's literal groups (Renut's native SetVertexShader does not), and the
pending-state flush `sub_82172DE8` that zeroes `m_Pending[0]` is only reached through the hooked Resolve. The unmarked
writer of c24 is still to find (an instrumented build: log the groups that changed without a mark, with the guest
thread's last D3D call). Cost of the whole copies: 12.9 KB a draw on the game thread (360 MB/s at the heavy moment).

## Hot functions (2026-10-29, from the emulator; the console decides)

The method is zumasrevenge-nx's docs/optimising-functions.md and hand-natives.md, with banjo-nx's tools.

- **Profile** (Ryujinx `prof1`: 240 s, the title, Stage 1 played to its game over, the shipped toml with
  `switch_profile_stacks`; map and ELF `out/nx_elf/bangaio_dev2.*`): of 14,022 busy samples the render thread has
  52.8 %, the UI / present thread 30.8 %, the game's main thread 14.9 %, everything else under 1 %. In the main thread
  the generated game code is 16.6 % (the rest is Renut's Direct3D layer and locks; about half its samples land in the
  emulator's own code). The hottest game functions: `sub_8222B808` (97 samples: a spin wait, `ctr` polls of a flag
  with `mr r31,r31` and a Sleep(0), the main thread waiting for its workers), `sub_820C6840` (a lock wrapper),
  `sub_820E2450` (a list walk with virtual calls), `sub_820D1BD8`, `sub_820C5620` and `sub_820C4100` (inline vertex
  constant writers: they mark `m_Pending[0]` and store c15 / c16), `sub_822D97A0` (an empty function called through a
  pointer).
- **Hand-written natives** (5; `app/src/cpu/hot/hand.txt`, `banjo_hand_natives.h`): the C runtime's memcpy
  (`0x824228D0`), memset (`0x82422830`) and memmove (`0x82424250`), found by `tools/crt_signatures.py` (sa2-nx's
  signatures, each a unique match), and Direct3D's vertex / pixel float-constant writers `sub_8216E370` /
  `sub_8216E448` (every constant upload: the game's inline headers call them). memcpy and memset are banjo-nx's natives
  as they are; memmove follows the original exactly (`cmpw` is signed: equal ranges return at once with no store,
  dst < src is memcpy's tail call, so memcpy's native; the backward copy is declined); the constant writers are
  banjo-nx's `constants::Upload` without its r31 stack slot (XDK 20209's writers are frameless). Why not the profile's
  own top five: they are a spin wait, an empty callback and writers of three floats, where a rewrite removes nothing
  measurable; the five above are the work every frame does through the C runtime and Direct3D.
- **Localized copies**: every game function sampled in the two emulator profiles (`tools/switch_hot_bulk.py --min-samples
  1` over `prof1` and `emu2`): 63 in `localized_bulk.txt` (tiny leaves, a raw atomic and the natives' own left out),
  plus the five natives' functions in `localized.txt`; `tools/localize_native.py --list --bulk`: 5 + 63 copies in 12
  shards (write-backs limited, small callees inlined, direct dispatch as banjo-nx's).
- **Compare mode** (`banjo_cpu_verify = true`): PC `cpuverify3` 476,202 calls compared, emulator `cpuverify2` 175,039
  (the emulator runs at 13 fps in this mode): **0 differences**. The game's main thread is not the frame's limit (the
  render thread is: 1.8 ms a frame in the menus, 28 ms at a 1,130-draw moment in the emulator), so these are measured
  on the console by the next profile, not here.

## PGO + LTO (2026-10-29, docs/pgo-lto.md)

- **Instrumented build** (`app/out/switch-pgo-gen`, `-DBANJO_PGO=generate`, LTO off): from scratch in 13 minutes (the
  SDK's objects were already built by the development folder), NRO 38.8 MB.
- **Profile session** (Ryujinx `pgo1`, 380 s, `renut_play.toml` as the base with the log on, every profiler off): the
  logo, the title, Single Player, Stage 1 and several rounds of play (the sticks wandering from 60 s, A every 15 s:
  each game over retries), 24-60 fps in the emulator. One stream, `sdmc:/switch/bangaio-nx/pgo/banjo_pgo_1.stream`
  (1.4 MB).
- **Merge** (`tools/pgo_merge.py`): 145 `.gcda` files in `pgo/` (not in git), largest arc count 612,603,725.
- **Optimised build** (`app/out/switch-pgo-use`, `-DBANJO_PGO=use -DBANJO_SWITCH_LTO=ON`): started 03:03, done 03:19,
  NRO 33.7 MB (v1; its ELF and map in `out/nx_elf/bangaio_v1.*`), built from commit `3d83dd73`.

v2 (the corrected post-codegen passes and the point-sprite fast path):
- v1's profile set aside (`pgo_v1/`, and the SD card's `pgo/` renamed `pgo_v1/`), never merged with v2's: the code
  changed, so the old counters would not match it.
- **Instrumented build** 05:53-06:00 (incremental, 6 jobs).
- **Profile session** (Ryujinx `pgo2`, 380 s, as `pgo1`): from a fresh save (renamed aside before `v2ab69`), so it
  played Stage 1's game overs and went on to other maps: 34 ten-second lines, most of them busy play at 700-1,700
  draws a frame (pgo1's had mostly menus). One stream, 1.6 MB.
- **Merge**: 145 `.gcda` files in a new `pgo/`, largest arc count 1,255,215,260 (pgo1: 612,603,725).
- **Optimised build** with `--clean-first` (every object reads the new profile): started 06:16.

## Post-codegen tools with N&B's constants (found 2026-10-29 with the NiGHTS session)

Four of banjo-nx's post-codegen passes carried N&B values that no build error reveals:
- `tools/inline_memcalls.py` defaults to N&B's memcpy / memset (`82BB4510` / `82BB4A40`) and `post_codegen.py` passed
  none: in v1 nothing was inlined. Now `--memcpy 824228D0 --memset 82422830`.
- `tools/leaf_dead_stores.py`: `ENTRY_POINT` was N&B's `0x82718798`; Bangai-O's is `0x82163960`.
- `tools/r1_preserve.py` and `tools/lr_preserve.py` imported from `D:/Banjo kazooie port/banjo-nx/tools` (so banjo-nx's
  leaf_dead_stores, with its entry point) and listed N&B's no-return functions. Now this tree's tools, and Bangai-O's
  longjmp `0x824258F0` (nothing in Bangai-O builds 0xE06D7363: no C++ throw). None of N&B's listed addresses is a
  Bangai-O function start, so v1 was not miscompiled by them (the PC's r1 mirror check: 0 differences over 383 million
  calls; the LR pass had proven 0 write-backs): v1 only missed those optimisations. v2 is built with all four.
- A fifth, harmless: `tools/limiter_lazy_log10.py` rewrites N&B's XAudio limiter copy (`n_82B0D0C0.h`), which does
  not exist here; it prints "missing: nothing done".

v2's codegen (04:05, 8.7 min): inline_memcalls 260 of 783 memcpy and 147 of 671 memset calls inline (constant sizes
1-64 bytes); leaf_dead_stores 2,457 dead leaf write-backs in 285 functions; r1_preserve 10,899 of 11,749 functions
preserve r1 (with indirect calls assumed; 4,722 strict). PC check (`out/pc_runs/v2cpuverify`, 150 s, compare mode,
title -> Stage 1 at a busy moment): r1 mirror 0 differences over 101 million calls, generated-code self-checks
0 differences (34.9 million folded constant loads), flush-mode flow 0 of 122.6 million, the 5 hand natives and the
63 bulk copies 0 differences (27.3 million calls compared); the captures show the title and Stage 1 as before.

## Point sprites pushed and on the fast path (v2, `banjo_renut_point_fast_draw`, A/B 69)

Bangai-O's missiles and particles are point lists: 41 % of the draws at a heavy moment, and every one went the full
way with ring-uploaded constants (`FastDrawLocked` returned `kFastCall` for `kPointList`; the full path did not push
for `point_sprite_gs` draws). banjo-nx excluded them because point_sprite_gs's Vulkan shader reads SharedConstants
through the address in its push constants. On deko3d it does not: its `BANJO_DEKO3D` branch reads `[[vk::binding(0, 7)]]`,
which tools/deko3d_glsl.py maps to UBO binding 2 like every game shader's set 7 (the compiled header says
`banjo-dk ubo=0x4`), and plume binds a pipeline's UBOs for each stage that reads them (`bindGraphicsBuffers` walks
vertex, geometry and fragment; `setPipeline` marks them dirty). So the pushed shared buffer at binding 2 reaches the
geometry shader already. The pipeline side was there too (MakeKey sets `point_sprite` from the primitive; pipeline.cpp
attaches the geometry shader; the fast path keys its pipelines with the primitive in `misc` and pushes the point
sprites' push block by `kp_hot.point_sprite`).

The change (draw.cpp): the full path pushes for point draws as well; FastDrawLocked takes point lists, setting
`sc.point_state` from the tessellator packet as DrawStateLocked does (one helper, `PointStateOf`, for both) and
leaving `g_draw_sc_track.point` set for the next draw to clear. Off (or in A/B 69's off half) everything is as before.
On the PC nothing changes (the fast path and pushed constants are deko3d's), so it is checked in the emulator with
`banjo_renut_fast_draw_verify` and the 15 s captures against v1's. A/B 59 (a ring-uploaded point draw leaving the fast
path a state) does nothing while 69 is on, so `renut_ab.toml` lists 69 in its place.

## The stale c24-c27 found: BeginShaderConstantF4 (v3, 2026-10-29)

Found on the PC (no emulator needed) with two diagnostics, kept for the next port:
- The delta verify's warning now lists every stale constant group, not the first byte (`backend/queued.cpp`,
  `DeviceForDraw`): over a whole run only vertex groups 5-7 (c20-c31) were ever stale, mostly group 6 (c24-c27), never
  a pixel group or another device line.
- A PC-only check in the hand-written constant writers (`banjo::hand::ConstantMaskNote`, `cpu/banjo_hot_guest.cpp`):
  no call of `sub_8216E370` / `sub_8216E448` has a dirty mask short of the registers it writes, and in the intervals
  where group 6 changed they had not written it. A ring of the last Renut hooks each thread ran
  (`BANJO_RENUT_NOTE_HOOK`, `banjo_renut_select.h`, PC only) showed SetStreamSource, BeginRingBig, DrawVertices around
  every such change.
- BeginRingBig's callers: `sub_8216E258` is XDK 20209's BeginShaderConstantF4. It reserves a SET_CONSTANT packet
  in the ring, returns two pointers (the device's copy of `c[first]` and the packet's data) for the caller to write the
  values into both, and clears those groups' dirty bits (`ldx` / `andc` / `stdx` on `m_Pending[r4 != 0]`): the packet
  sends them. Renut rewinds the ring without reading it and reads the device's copy, so a whole copy is right and a
  delta, carrying only marked groups, is stale. N&B's Direct3D (XDK 7645) has no such path, so banjo-nx never met it.

The fix: Renut hooks `sub_8216E258` (`d3d/hooks/state.cpp`, raw): the original runs, then the groups it handed out are
marked dirty instead (the caller fills them before its next draw, whose capture takes them). It was one of the 63 bulk
localized copies; it leaves that list (62 now). PC verify (`out/pc_runs/delta5`, `v3verify`): 0 differing draws of
478,864 / 479,845; a draw keeps 244 bytes on average instead of the 12,888-byte whole copy (1.1 chunks and 2.0
constant groups a delta); the attract demo draws right. `banjo_renut_snapshot_deltas` is on by default again (as in
banjo-nx), which removes the game thread's 12.9 KB copy a draw. The same hook also makes
`banjo_renut_snapshot_deltas_constants` (the uploads comparing only the groups a delta says changed) exact for these
groups.

## Emulator runs are only comparable from the same save (2026-10-29)

Bangai-O keeps its progress in the title's profile settings: `sdcard/switch/bangaio-nx/renut/58410AF2/profile/User/`
(three 1,000-byte files) in the port's Ryujinx data folder. The scripted runs' game overs accumulate there; after three
on Stage 1 Dr. Ban moves the player to another map ("You got 3 Game Overs, so I'm letting you move on"), so the same
input script led later runs (`v2prof1`) into Fury Mode's briefing instead of v1's Stage 1 game over (`prof1`). For
measurements the folder is renamed aside before a run (`58410AF2_saved_0527`: the state after `v2prof1`), so each
starts from no save; renamed, never deleted. Verify keys also distort timing in proportion to the fast draws
(`banjo_renut_fast_draw_verify` re-derives each fast draw): v1's heavy scene cost 11.9 us of render thread a draw
without them (`prof1`) and 24.7 with them (`emu2`); speed is compared only between runs without verify keys.

## Status at the deadline (2026-10-29, written 08:10)

The user (08:07): the computer is overloaded, so the emulator's frame rates are not to be taken seriously. Every
emulator speed figure in these notes is therefore only a hint; the emulator runs prove exactness (verify keys,
captures) and nothing else. The last comparison runs (`v3prof`, an unfinished `v2prof`) are not used for any
decision; v3 is the build for the console, and no further build cycle was started to keep the machine's load down.

Packages (`out/package_20261029_<v>`: NRO, the three settings files, the picture-changing configs, the four-core
NPDM, ELF + map, a `git archive` of the commit, README-test.txt; no game data):

| | commit | what | checked |
|---|---|---|---|
| v1 | `3d83dd73` | PGO + LTO, the first profile, deltas off | its dev build in the emulator and PC compare mode; the PGO+LTO NRO itself not run |
| v2 | `bf80f83c` | + Bangai-O's post-codegen constants, point sprites pushed and on the fast path, profile 2 | PC compare mode; emulator `v2verify2`, `v2final` (PGO+LTO): every verify key 0 |
| v3 | `008d3efd` | + snapshot deltas fixed and on (BeginShaderConstantF4 hook), profile 3 | PC delta verify 0 of 479,845; emulator `v3verify`, `v3final` (PGO+LTO): every verify key 0, heavy scene drawn right |
| v4 | `deb9824b` (code `59c2669f`) | + the missile storm fixes (small captures, second-sighting stream cache, quad index buffer; A/B 70-72), profile 4 | PC delta verify 0 of ~4.4 M; emulator `v4verify`, `v4final` (PGO+LTO): every verify key 0 (delta verify 0 of 3,281,706), the game-over storm drawn right. NRO sha256 `608D2ABD3C05A715...` |
| **v5** | `c0af5035` (code `0e3fe40f`) | + NEON delta masks (A/B 73), the stream cache's short idle, 84 console-hot copies (146), `kernel_critsec_spin = 64`, profile 5 | PC compare mode 146 copies / 61 M calls 0 differences, delta verify 0 of 3.4 M; emulator `v5final` (PGO+LTO): delta verify 0 of 4,206,683, hot copies 0, the storm drawn right. NRO sha256 `F1DE4C1E2EAD0A59...` |

What the user decides: the picture-changing configs (`configs/`: SMAA, docked 1080, handheld 540, dynamic
resolution); the forwarder program id (`05BA6A1000001000`, or their own with `banjo_forwarder_program_id`); the console
A/B list's results (`renut_ab.toml`, targets 3 5 7 8 20 31 62 67 69, control 1) and v2 against v3 for the deltas.

## The first console run (v3, 2026-10-29 10:15-10:36, handheld)

The user's logs: `D:\bango\logs\renut_001.log`, `logs\rex\rex_profile.log` (stacks sampled); read with the v3 package's
map (`tools/switch_hot_functions.py`, and a stack-symbolising script). Handheld, stock clocks (CPU 1020, GPU 460.8,
memory 1600 MHz), **three cores** (hbmenu: mask 0x7, the four-core forwarder not used).

- 60 fps in menus and in normal and heavy play: up to ~1,300 draws a frame at 60 fps, with the render thread at 5-8.6 ms
  a frame and the GPU at 6-8.5 ms.
- **The drop** (10:26:05-10:26:45, a missile storm): 22-25 fps for 30 s, 33 and 45 fps while it cleared. At ~4,240
  draws a frame:
  - Render thread busy 30-36 ms a frame; GPU 20-23 ms a frame; game thread 83 % CPU. All three are over 16.7 ms, so
    removing only one of them would not hold 60.
  - GPU per frame: 14.4 ms on 1,880 draws to the 640x360 colour+depth target (~7.6 us a draw), 7.1 ms on 2,358 draws at
    1280x720.
  - Geometry: 92 % of the draws from range copies; the reasons were "kind" (901k of 990k) and "stream written lately"
    (344k).
  - Stream cache: **193,150 entries** at 10:26:24, only 5 MB; at 60 fps it was 4k-74k.
- Render thread, self time in the drop:
  - `AdvanceStreamCacheFrameLocked` 22 % (3 % of all threads in a busy 60 fps window), with `_free_r`/`rmutexLock`
    under it. Its `std::erase_if` walks the whole `unordered_map` (every 60 frames, idle time 3600 frames or the
    memory policy's 20 s), and `DropReplacedRanges` walks it every 16 frames.
  - `FastDrawLocked` 14 %, `WholeGeometryTry` 6 %, `BindStreams` 5 %, `ConvertVertices` 5 %, `PushFloatConstants` 4.6 %,
    the `QueueCapture` lambda 4.6 %, `FlushVertexFillsLocked` 4 %.
- Game thread in the drop:
  - `CaptureDelta` 15 % self.
  - `_malloc_r` 9 %. Every `operator new` on the game thread comes from `CaptureDelta` (via `sub_82171D88`, the draw path,
    `<- sub_820D4D88`). In the busy 60 fps window, malloc is not in the game thread's top list: the per-draw allocations
    appear when the render thread falls behind.
  - mutexLock/Unlock 4 %, `RtlEnterCriticalSection` 2.5 %.
  - The guest's own hot functions are about 1-4 % each.
- Not a cause: the hot copies, the bulk copies and the delta verify show 0 differences; uam compiles were 11 blocking
  waits at boot only.

The banjo-nx session's advice (11:0x; it read the logs and code and changed nothing). Points 1 and 3 were checked here in
the code; none of it is built. In its order:
1. **Capture pool** (`queued.cpp`): `CapturePool::kMaxFree = 2048` ("more than a frame's draws in flight", banjo's
   ~2,000 draws a frame) is below the storm's ~4,250. The render thread gives back ~4.2k captures and deletes all but
   2,048. The game thread then makes ~2.2k again with `new DrawCapture()`, and each one's `state.resize(kDeltaMaxBytes)`
   zero-fills 12.9 KB. That is ~28 MB of memset a frame, plus mallocs and frees on two threads behind newlib's one
   malloc lock. The fix, exact:
   - (a) a larger kMaxFree (8192);
   - (b) the delta written into one 12.9 KB scratch buffer under `g_delta.mutex`, then `state.assign(scratch, to)`.
     Deltas average 221-251 bytes and a pooled vector keeps its capacity.
2. **Second-sighting filter on the stream cache**: banjo's console peak was 3,892 streams (96 % whole buffers). Here,
   sprites drawn from moving offsets of a dynamic buffer make a new key nearly every draw, never seen again. Each such
   key costs:
   - a node malloc;
   - a hash in `FlushVertexFillsLocked`;
   - visits from both walks;
   - a free.

   The fix: a small direct-mapped filter of key hashes in front of `g_stream_memo.Get(..., create=true)`. A first
   sighting takes the upload path that a fresh entry takes today (`fill.cacheable = false`). This is exact: a copy is
   only made after `kStableFlushes` proven hashes anyway. An age FIFO for the idle pass comes after it, if still needed.
3. **Split the "kind" reason** (901k): it lumps together tessellation, up-vertices, triangle fans, **quad lists** and
   skin_once. If the missiles are quad lists (0 Begin*Vertices draws in the storm), each draw is refused a whole buffer
   and has its indices rebuilt (`PrepareGeometry` and `ExpandIndices`). The exact option: one static a,b,c / a,c,d
   index buffer drawn with base vertex = start vertex, the same split as `ExpandIndices`.
4. **GPU**: not barriers, which the `deko3d:` line counts since boot. The storm frames add ~27 fragment and 11 full
   barriers. The 640x360 pass costs 7.6 us a draw against 3.0 at 1280x720 at a quarter of the pixels, so it is fill and
   blend (overdraw of glow and explosion sprites). The next step is one run with `banjo_renut_diag_gpu_shaders`, then,
   for the dominant shader:
   - the target's host format (a 64-bit float target blends at half rate);
   - early Z and zcull;
   - its size after uam.
5. Four cores (the forwarder): the game thread and the render thread are both busy, and three cores give everything
   else one core.

## v4: the missile storm fixes (2026-10-29, the user asked for banjo-nx's 1-3)

All three are exact by construction, and each has a key and an in-run A/B target (on by default):
- **`banjo_renut_small_captures` (A/B 70, `queued.cpp`)**:
  - `CaptureDelta` writes a delta into the chain's own scratch (`DeltaChain::scratch`, the same lines every draw), then
    `state.assign`s it into the capture at its size. A pooled vector keeps its capacity, so there is no allocation
    after warm-up and no 12.9 KB zero-fill.
  - The pool keeps up to 8,192 captures or 32 MB. Whole copies (rebases, clears, resolves) keep 12.9 KB each, so the
    byte cap holds them to about the old 2,048. The held bytes are kept in a vector beside `free_`, so a batch Take
    reads no capture under the lock.
  - Captures the pool does not keep are deleted after its lock is let go.
- **`banjo_renut_stream_second_sighting` (A/B 71, `draw.cpp`, `RangeEntry`)**:
  - `BindStreams` looks a range up with `create=false`. A miss checks `RangeSightings`, a direct-mapped table of 16,384
    32-bit tags (64 KB); only a range seen before gets an entry (`EntryMemo::Make`).
  - A first sighting converts into the upload ring with `fill.cacheable = false`, as a fresh entry's draw did: a copy is
    only made after `kStableFlushes` proven flushes either way.
- **`banjo_renut_quad_indices` (A/B 72, `draw.cpp`, `QuadIndexBuffer`)**:
  - `CountKindWhy` splits the "kind" reason in the 10 s line. The PC gameplay run showed **quad lists**: 788,069 in one
    10 s window, 0 immediate-vertex draws. These are Bangai-O's sprites and missiles, all non-indexed.
  - A non-indexed quad list of 4-65,535 vertices draws from one 16-bit index buffer in the copy pool, made once
    (0,1,2,0,2,3, 4,5,6,4,6,7, ...). Those are the values `ExpandIndices` made, rebased by 0 and 16-bit as
    `PrepareGeometry` wrote them.
  - Every quad draw binds the whole buffer through one view, so `SetIndexBuffer` (buffer, size, format) keeps a single
    binding.
- **ARM audit of the new code**:
  - `SmallCapturesOn()` (a guard and the A/B word) is read once per batch, not per capture under the pool's lock.
  - The quad buffer's state is at namespace scope: no guard read at every quad draw.
  - The sighting check is one multiply, shift, load and compare.
  - The pool vectors are reserved at start, so no push under the lock reallocates.
- **PC (`out/pc_runs/v4pc1`, `v4pc2`, 150 s gameplay)**:
  - The delta verify found 0 differing draws in ~4.4 M draws.
  - Every quad list was drawn with the shared buffer: 352,151 in the busiest 10 s.
  - Ranges drawn without an entry: 355,001 in one 10 s window.
  - The captures at 90 s show the missiles, glows and explosions as v3's.

## The second console run (v4, 2026-10-29 12:04-12:06, handheld, three cores again)

The user's logs are in `D:\bango\newlogs\logs`. The storm ran 12:05:05-12:05:45. Normal play held 58-60 fps, as in v3.
Draws a frame are from the device-snapshots line (every queued draw).

| load | v3 | v4 |
|---|---|---|
| ~2,330 draws a frame | 32.8 fps, render 25.1 ms, GPU 14.4 ms | 36.6 fps, render 17.4 ms, GPU 16.8 ms |
| ~3,800 draws a frame (windows of 3,000 or more) | 24.4 fps, render 32.0 ms, GPU 21.7 ms | 28.8 fps, render 23.2 ms, GPU 20.7 ms |
| ~4,300 draws a frame (the heaviest window) | 25.2 fps, render 30.7 ms, GPU 22.6 ms | 25.3 fps, render 27.7 ms, GPU 24.5 ms |
| all windows of 2,000 or more | 26.5 fps (3,379 draws a frame) | 33.9 fps (3,035 draws a frame) |

- **Render thread per draw**, over the storm windows: 8.84 to 6.23 us (-30 %). GPU per draw 5.75 to 5.90 us (the same:
  the fixes are CPU work).
- **The game thread is now the limiter**: 82-89 % CPU, 17-25 % of its samples waiting (v3: 74-83 % and 24-31 %). The
  render thread went down to 61-70 % CPU, 32-45 % waiting (v3: 75-78 %, 26-36 %). At the heaviest window (39.5 ms a
  frame) the game thread is ~34 ms busy a frame, the render thread 27.7 ms and the GPU 24.5 ms.
- **Game thread**: `CaptureDelta` 18.3 % of it (self), about 6 ms a frame at the peak. `_malloc_r` is gone from its list
  (v3: 9.3 %); overall malloc 1.0 %, free 1.3 % (v3: 4.1 %, 2.0 %). The rest is the game's own code.
- **Render thread**:
  - `FastDrawLocked` 15.6 %.
  - `AdvanceStreamCacheFrameLocked` **12.9 %** (v3: 22.2 %).
  - `WholeGeometryTry` 8.1 %, `ConvertVertices` 8.0 %, the `QueueCapture` lambda 6.5 %, `RangeEntry` 4.5 %.
- **The stream cache still reached 108,892 entries** (v3: 193,150), with 500-870 first sightings skipped a frame.
  Likely cause: the sprites are drawn twice a frame, in the 1280x720 pass and the 640x360 glow pass (2,358 and 1,880
  draws a frame in v3's storm), so a range's second sighting comes in the same frame. Making the entry only at a
  sighting in a later frame would keep these out, and is still exact.
- All quad lists were drawn with the shared index buffer: 1,700-2,400 a frame in the storm.

The heaviest moment is now bound by the game thread. At 30 fps or more, the GPU (24.5 ms, 13.7 ms of it in the
640x360 pass) and the game thread are the walls. Next steps:
1. `CaptureDelta`'s chunk compare (~1.8 us a draw on the game thread).
2. The later-frame sighting rule.
3. Four cores (the forwarder: CPU total 230 % of the three cores' 300 % in the storm).
4. The GPU shader split (`banjo_renut_diag_gpu_shaders`).

## v5: the game thread and the stream cache (2026-10-29, the user asked for the next fixes)

All exact. From the v4 console profile:
- **`CaptureDelta`** (18.3 % of the game thread in the storm): 65 % of its samples were the per-chunk check, a `umaxv`,
  an `fmov` to a register and a branch for each of 40 chunks (1.1 differ a draw).
  - `banjo_renut_delta_masks` (A/B 73): the compared chunks as runs (`DeltaRuns`: the narrow list is 12, 12 and 15 whole
    chunks plus the 24-byte last one). One `Lines64DifferMask` a run (one NEON reduction per four chunks, no branch per
    chunk), then only the set bits, in order.
  - `Lines64DifferMask`'s 1-3 leftover lines are the last four again, not a reduction each (the pushed shared constants'
    compare in `draw.cpp` gets it too).
  - The short chunk is compared inline, not with `memcmp`; a whole chunk is copied with constant-size copies.
  - The chain's switches (`banjo_renut_snapshot_deltas_narrow` / `_verify`, `neon_compare`, `capture_batches`,
    `small_captures`, `delta_masks`) are latched in `Latched` (plain loads) instead of function statics. Each static's
    guard was an `ldar` every draw.
  - The next pooled capture is prefetched for writing (`prfm pstl1keep`, three lines). Its first line was a miss each
    draw: the render thread on another core wrote it last.
- **Stream cache** (`banjo_renut_stream_second_sighting`, A/B 71, extended). The v4 storm still kept 108,892 entries, and
  `AdvanceStreamCacheFrameLocked`'s samples were the replaced-range walk every 16 frames (40 % on one pointer chase, plus
  its binary search) and the idle walk. Bangai-O's sprite ranges move or are rewritten in place; nearly none is cached.
  - The entry is made at a sighting in a later frame than the first. It did not shrink the PC run's map: the ranges are
    not two passes of one frame.
  - An entry with no copy whose bytes were new at 3 kicks in a row is dropped at the frame's start
    (`ForgetChangingRanges`: only its memo slot forgotten), and its range marked as changing in the sightings table.
  - **An entry with no copy unused for 120 frames goes at the idle pass** (it holds only its stable count), not after
    20 s. This is the one that counts: the PC run's map peaked at 8,820 entries (v4: 30,517; v5 before this rule:
    41,884).
  - The sightings table is 32,768 slots (128 KB), 16-bit tag and 15-bit frame.
- **84 more machine-optimised copies** (`localized_bulk.txt`, 148 listed, 146 made). `tools/switch_hot_bulk.py --min-samples 8`
  over the two console runs (v3 and v4, with their packages' ELFs): 40.8 % of the game thread's storm samples were in
  generated code. The hottest are `sub_820C7338` (3.3 %), `sub_821DB438`, `sub_820C4720`, `sub_82160840`, the
  `sub_820C4888` / `sub_820C4988` pair, `sub_82117C68`, `sub_820E4B08`, `sub_8210F1E0` (the critical-section user)...
  Codegen rerun (`tools/codegen.ps1 -PostPasses`, 5 min).
- **`kernel_critsec_spin = 64`** in the shipped settings (SDK default 0). The storm made 2,000-3,700 contended guest
  critical-section waits a second, each straight to the full host waiter: object lookup, condition variable, a
  context switch each way. `sub_8210F1E0`'s `pthread_mutex_lock` was 6 % of the game thread. masseffect-nx lists this
  key as open (Y8).
- **Looked at, not done**:
  - **The audio thread's reverb**: `XThread5A7DFE80` (10-19 % of a core) spends 56 % in `sub_821E6470`. That is XAudio2's
    reverb, 1,000 instructions of delay-line DSP. Its samples are spread flat: byte-swapped loads, store-card marks,
    stack reloads.
    - banjo-nx's `banjo_reverb_native.cpp` is N&B's older XAudio reverb (`stereo_room_t::process`: an 18,000-byte frame,
      r3-r6), not this one (a 560-byte frame, r3-r7 and f1); no other port has XAudio2's.
    - The game thread's spin-wait `sub_8222B808` waits for the game's worker threads, not the audio thread, so a native
      would only free ~10 % of a core. The user chose to skip it.
  - **Batching the render queue's pushes** (the per-draw `g_mutex`): it would change how items from different threads
    interleave, which the delta chain relies on.
  - **Banjo's shader optimisations are all in already**: the GLSL passes on all 95 shaders, the uam flags, per-pipeline
    specialisation, zcull. The console's DKSH cache file is written by the first run (the second run: 39 variants
    read, 0 compiled).

## The third console run (v5, 2026-10-29 15:18-15:19, handheld, three cores)

The user's logs are in the v5 package's `sd/switch/bangaio-nx/logs`. The memory was raised at the start and set back
to 1600 MHz before the title (the storm reports show CPU 1020, GPU 460.8, memory 1600). The storm ran
15:18:47-15:19:17 and was lighter than v4's: the heaviest window had 3,580 draws a frame (v4 4,371).
- **At matched load**:
  - 2,000-3,000 draws a frame: v3 32.8, v4 37.3, v5 **40.8 fps**.
  - 3,000 or more: v3 24.4, v4 28.8, v5 **31.2 fps**.
  - All storm windows: v3 26.5, v4 33.9, v5 **37.6 fps**.
  - Render thread per draw: 8.84 / 6.23 / 6.53 us. GPU per draw: 5.75 / 5.90 / 5.74 us.
- **Game thread** (93.7-96.7 % CPU in the two heaviest reports, 14-17 % waiting: the limit):
  - `CaptureDelta` 15.8 % (v4 18.3 %). Its samples are now the `ld1` loads of the device and shadow lines (40
    chunks, 80 lines a draw, out of L1 after the game's own work between draws), not the per-chunk reduction.
  - The new copies `sub_820C7338` 4.8 % and `sub_821189F8` 4.4 %; mutex lock/unlock 5.7 %.
- **Render thread**: `FastDrawLocked` 17.9 %, `AdvanceStreamCacheFrameLocked` 12.0 % (v4 12.9 %), `WholeGeometryTry` 7.0 %.
- **The stream cache reached 131,408 entries**, worse than v4. In the console storm the copy-less entries are used
  again within 120 frames: they are not idle, and their bytes are not new at 3 kicks in a row. Likely cause: the
  game's sprite buffer is a ring whose offsets come round every few seconds. Dropped: 4-8k per 10 s; first
  sightings without an entry: 75-225k per 10 s. The PC run (8,820 entries) did not show this.
- **Critical-section host waits**: 2,448-2,925 a second, about 70 a frame at 36-39 fps, as v4. `kernel_critsec_spin =
  64` made no measurable difference (if the run's renut.toml had it: the log does not show the setting).

## v6: the stream cache's age queue (2026-10-29; a test build without PGO / LTO, the user's choice)

The user asked for PGO + LTO only in the final build, to make each round quicker. Comparing v6 with v5 must allow for
v5's PGO + LTO.
- **`AgeRanges`** (`banjo_renut_stream_second_sighting`, A/B 71). `RangeEntry` queues each entry it makes, with its
  frame; each frame the entries made 8 frames ago or more are looked at once, oldest first, with no walk:
  - with a copy (or whole): the idle pass's;
  - still counting stable kicks and drawn within 8 frames: queued again;
  - otherwise erased, its memo slot forgotten and its range marked as changing.

  The work is proportional to the entries made, not the map's size. PC `v6pc1`: the map peaked at 5,581 entries
  (v5 8,820, v4 30,517).
- **`banjo_renut_delta_prefetch`** (A/B 74): at `QueueDraw`'s start, the 40 compared device lines and their 40 shadow
  lines are prefetched (`prfm`, a hint), before `FlushDeferredVertices`, `RunReadyCallbacks`, the chain lock and the
  pool. Their misses then overlap instead of stalling the compare a group at a time (v5 `CaptureDelta`'s samples were
  those `ld1`s).
- **The render queue's `Push`** calls `Start()` (a `std::call_once`, so a `pthread_once` call) only until a relaxed flag
  says it has run. `QueueDraw` reads `DeltasOn()` once (its static's guard was three `ldar`s a draw).
- **PC `v6pc1`** (compare mode + delta verify): 0 of 3,423,697 draws differ; 146 of 146 copies, 62 M calls, 0
  differences; the r1 mirror and self-checks 0.

## The fourth console run (v6, 2026-10-29 15:40-15:42, handheld, stock clocks, three cores)

The user's logs are in `out/package_20261029_v6/logs`: `renut_002.log` is v6's run; `renut_001.log` is v5's run,
carried over on the SD.
- **Storm (windows of 2,000+ draws)**: 32.8 fps (v5 37.6, v4 33.9, v3 26.5).
  - 3,000+ draws: 29.4 fps (v5 31.2).
  - 2,000-3,000: 36.1 fps (v5 40.8).
  - Render thread per draw 8.18 us (v5 6.53, v4 6.23). GPU per draw 5.83 us (v5 5.74).

  v6 is a build without PGO / LTO (the user's choice for test rounds), and the render thread (Renut's C++) loses most
  from that.
- **The render thread co-limits again** (77-103 % CPU, 19-30 % waiting), with the game thread (84-100 %).
- **The stream cache: 87,918-103,752 entries** (v5 131,408), while `AgeRanges` and the drop rules dropped only 9-17k
  per 10 s.
  - The rest are **whole-buffer entries**: `WholeStreamCopy` makes an entry (`Get(.., true)`, `whole = true`) for
    every whole-buffer key it tries, including the 190-380k misses per 10 s ("stream written lately").
  - Every v5 / v6 rule skipped whole entries (the last pointers, mesh objects and geometry answers hold them), so they
    stayed 20 s.
  - The PC (not deko3d) never takes the whole path: hence 5,581 there.
  - `DropReplacedRanges` (now its own function, without LTO) walks them every 16 frames: 8.5 % of the render thread.
- **Game thread**: `CaptureDelta` 14.8 % (v5 15.8 %), but `PrefetchDeltaLines` costs 2.1 % itself: no net gain. Off by
  default from v7.

## The game thread by function (v5 and v6 console storms)

Over both storms (`tools/switch_hot_bulk.py`, 2,922 samples): 48.3 % in machine-optimised copies of game functions,
33.5 % host code (Renut, the runtime), 14.1 % plain generated game code, 4.2 % hooked functions. Inclusive (v5's
stacks):

| Part | Share | What |
|---|---|---|
| Draw submission | ~21 % | guest `sub_82171D88` (Direct3D's draw) and Renut's hook: `CaptureDelta` ~14 %, the render queue's push ~4.7 %, its lock |
| Waiting for the render thread at Swap | ~8 % | `D3DDevice_Swap_hook` (condition wait), `PaceRenutSwap` |
| Critical-section contention | ~8 % | `sub_8210F1E0` -> the game's heap: `sub_82160840` (allocate) / `sub_82161138` (free) hold a critical section the worker threads take too; the host waiter (`pthread_mutex_lock`, condition variable) |
| Game logic | ~60 % | spread: `sub_820C7338` 3.7 % (the frame loop: calls Swap), `sub_821189F8` 2.8 %, `sub_820C5030` / `sub_820C5168` 2.2 / 1.8 % (the game's inline `SetVertexShaderConstantF` / pixel twin: `BeginShaderConstantF4` then a VMX copy), `sub_8210EAB0` 2.2 % (sprite submission: float math, then draws), `sub_8210A400` 1.9 %, `sub_82117C68` 1.8 %, `sub_82160840` 1.5 % (heap allocate), `sub_8222B808` 1.5 % (a spin wait on the workers), `sub_820E2450` / `sub_820E24E8` / `sub_820E4450` (object-list walks with virtual calls), ... each 0.5-1.5 % below |

The hot leaf functions (hand-native candidates: no calls) are cold in the console profiles (the hottest, `sub_8222B350`,
uses atomics; the rest 1-8 samples over three runs). So the 15 hand optimisations of v7 are of the hottest functions
on the game and render threads, mostly Renut's and the runtime's, and the game's spread of code gets machine copies.

## v7: whole-buffer entries, 15 hand optimisations, 85 more copies (2026-10-29; test build, no PGO / LTO)

The user asked for 15 hand optimisations of functions and 85 machine optimisations, to test on the console less often.
- **Hand optimisations** (all exact):
  1. `WholeStreamCopy` -> `WholeEntry`: a whole buffer's entry only at a later-frame sighting (A/B 71).
  2. The idle pass (`AdvanceStreamCacheFrameLocked`): a whole entry with no copy 60 frames after it was made goes (one
     `ClearWholeLast` a pass).
  3. `DropReplacedRanges`: entries with no copy are passed over before the spans' binary search.
  4. `DropReplacedRanges`: every 64 frames (16).
  5. `ExpandLoop`: six common swizzles (xy01, yx01, xyz1, yxwz, zyxw, x001) with compile-time picks. The stack round
     trip a vertex was 70 % of `ExpandElement<2>`, 4 % of the render thread.
  6-12. 53 per-draw cvar statics of `draw.cpp` latched in `Latched` (plain loads, no `ldar` guard a read), in:
     6. `DrawStateLocked` (13);
     7. `BindingWords` (3, per texture);
     8. `BindStreams` / `BindWholeStreams`;
     9. `WholeGeometryTry`;
     10. `FastDrawLocked`;
     11. `BindTargets`;
     12. the feature checks (`ChainReuseOn`, `KickReuseOn`, `SecondSightingOn`, `PointFast*On`, `QuadIndicesOn`,
         `FetchCacheOn`, `MeshObjectsOn`, `GeometryObjectsOn`, `HostPacketsOn`, `ResourceObjectsOn`, ...).
     (`tools`: a one-off script; the fields are `sw_*`.)
  13. `RtlEnterCriticalSection_raw` / `RtlTryEnterCriticalSection_raw` (SDK): their settings in a plain global, no
      static guard.
  14. `QueueDraw`: `banjo_renut_delta_prefetch` off by default (it cost 2.1 % for ~1 % less `CaptureDelta`).
  15. `CountPushedConstants` / `CountDrawSource`: inline (no call into the tuning file three or four times a draw).
- **85 more machine-optimised copies**: `localized_bulk.txt` 233 listed, 231 made. The hottest generated functions of
  the three console runs not listed yet (16 down to 2 samples).
- **`kernel_critsec_spin = 0`** again: the v6 profile had a third of `RtlEnterCriticalSection`'s samples on the spin's
  `yield`, and the waits per frame were unchanged.
- **PC `v7cpuverify`**: compare mode 230 of 231 copies reached, 63 M calls, 0 differences; delta verify 0 of 2,987,883;
  self-checks, r1 mirror and flush-mode flow 0. (The whole-buffer path is deko3d's only: the emulator's
  `banjo_renut_whole_buffers_verify` checks it.)

## The fifth console run (v7, 2026-10-29 16:27-16:28, handheld, stock clocks, three cores)

The user's logs are in the v7 package's `sd/switch/bangaio-nx/logs`: one 75 s run, a storm from 16:28:09.
- **Storm (windows of 2,000+ draws)**: 33.7 fps at 3,070 draws a frame (v6 32.8 at 2,996; v5 PGO+LTO 37.6 at 2,821).
  - 3,000+: 30.1 fps at 3,575 (v6 29.4, v5 31.2).
  - 2,000-3,000: 39.1 fps (v6 36.1, v5 40.8).
  - Render thread per draw 7.06 us (v6 8.18: -14 %, both without PGO / LTO; v5 with them 6.53). GPU per draw 5.78 us.
- **The stream cache: 4,130-6,102 entries** (v6 87,918-103,752). Per 10 s: 144-211k whole-buffer first sightings
  without an entry, 9-11k copy-less whole entries dropped, 74-122k draws still from whole-buffer copies.
  `DropReplacedRanges` and `AdvanceStreamCacheFrameLocked` are no longer in the render thread's list (v6 8.5 % + 1.4 %).
- **Render thread** (75-78 % CPU, 22-33 % waiting):
  - `FastDrawLocked` 19.9 %, `PushFloatConstants` 7.3 %, `BindStreams` 7.0 %, the `QueueCapture` lambda 6.8 %,
    `WholeGeometryTry` 4.9 %, `mutexUnlock` 3.3 %, `ConvertVertices` 3.2 %.
  - `ExpandLoop<2>` 2.9 % (v6's `ExpandElement<2>` 4.1 %).
- **Game thread, the limit** (87-90 % CPU, 12-19 % waiting): `CaptureDelta` 15.0 %; the rest the game's own copies,
  `sub_820C7338` 4.7 %, `sub_821189F8` 4.1 %, then 1.4-2.3 % each.

## The game thread by function, and how each is optimised (v7 console storm)

v7's storm, 1,182 game-thread samples (no LTO, so Renut's functions are not merged into each other).
- **By kind**: machine-optimised copies 55.4 %, host code 31.3 % (Renut, the runtime, the C library), Renut-hooked
  functions 7.5 %, plain generated game code 5.8 %.
- **By call tree** (stack samples):
  - drawing (`sub_82171D88` -> `QueueDraw`) 20 %;
  - the sprite submitters above it, `sub_8210EAB0` 10.3 %, `sub_820D4D88` 8.2 %, `sub_820D37C0` 2.9 %;
  - the heap lock: `sub_8210F1E0` 7.8 %, of it `pthread_mutex_lock` 7.5 % and kernel waits 3.9 %;
  - waiting on the workers (`sub_8222CF78`) 4.5 %;
  - the render queue push 2.3 %.

Self time; status: **hand** = written or rewritten by hand, **machine** = a localized copy (`localized_bulk.txt`),
**hooked** = Renut's code replaces the Direct3D function, **not yet** = plain generated code or untouched library code.

| % | Function | What | Status |
|---|---|---|---|
| 15.0 | `CaptureDelta` | the draw's device delta (40-chunk compare, copy) | hand (v4 small captures, v5 NEON masks, v7 latched switches) |
| 4.7 | `sub_820C7338` | the frame loop (57 calls, Swap) | machine |
| 4.1 | `sub_821189F8` | object update dispatch (19 calls, 5 virtual) | machine |
| 2.3 | `sub_820D5568` | float math with 8 calls (object / sprite setup) | machine |
| 2.0 | `sub_820E4450` | object-list walk, virtual calls | machine |
| 2.0 | `sub_820C5030` | the game's inline SetVertexShaderConstantF (BeginShaderConstantF4 + VMX copy) | machine |
| 2.0 | `memcpy` (C library) | big copies of the natives and the capture | not yet (library) |
| 1.9 | `mutexLock` (libnx) | the render queue's and the chain's lock, per draw | not yet (library) |
| 1.9 | `sub_82109FF8` | flag / state checks, 23 calls | machine |
| 1.8 | `sub_8210EAB0` | sprite submission (float math, then draws) | machine |
| 1.8 | `sub_82117C68` | float math, 8 calls | machine |
| 1.8 | `sub_820C5168` | the pixel-shader twin of `sub_820C5030` | machine |
| 1.7 | `sub_8210A400` | four loops, 4 calls | machine |
| 1.4 | `sub_82109218` | float math, 6 calls | machine |
| 1.3 | `mutexUnlock` (libnx) | as `mutexLock` | not yet (library) |
| 1.3 | `QueueDraw` | the draw's queueing | hand (v6, v7) |
| 1.3 | `sub_820E4B08` | flag checks, 5 calls | machine |
| 1.2 | `sub_820D57F8` | a 6-instruction getter (called very often) | machine |
| 1.2 | `sub_82160840` | the game's heap allocate (critical section, NtAllocateVirtualMemory) | machine |
| 1.1 | `sub_820C4800`, `sub_82107C00`, `sub_820E2450`, `sub_820D4D88` | a loop over a list; a 6-call helper; a list walk; sprite vertex writes (16-bit stores) | machine |
| 1.1 | `native::SetStreamSource` | Renut's Direct3D setter | hand (Renut / banjo-nx) |
| 1.0 | `RtlEnterCriticalSection_raw` | guest critical sections | hand (sa2-nx's PCR owner; v7 latched config) |
| 0.9 | `sub_820E24E8`, `sub_820C4720`, `sub_820D37C0` | a list walk; a 6-call helper (the workers too); sprite vertex writes | machine |
| 0.9 | `render_thread::Push` | the render queue | hand (v6: no pthread_once) |
| 0.9 | `sub_8216E258` | Direct3D BeginShaderConstantF4 | hooked (Renut marks the constants, v3) |
| 0.9 | `sub_8222B808` | spin wait on the workers | machine |
| 0.8 | `_malloc_r` (newlib) | host allocations | not yet (library) |
| 0.7 | `native::SetTexture` | Renut's Direct3D setter | hand (Renut / banjo-nx) |
| 0.7 | `sub_82171D88` | Direct3D DrawVertices | hooked (Renut: QueueDraw) |
| 0.5 | `sub_82176468`, `sub_8216C9C0` | Direct3D BeginRingBig, SetStreamSource | hooked |
| 5.8 total | `sub_82108ED0` 0.3, `sub_82101C08` 0.25, `sub_8222B350` 0.2 (atomics: cannot be copied), ... | the rest of the generated code, each under 0.4 % | not yet |

## v8: 10 game-thread hand optimisations, everything sampled machine-optimised (2026-10-29; test build)

The user asked for 10 more hand optimisations, game thread only, and the rest machine-optimised. The game's hot
functions all call others (the hand-native framework covers leaves, and the hot leaves are cold), so the 10 are the
host functions on the game thread's draw and hook paths:
1. `CaptureDelta`: the delta copied into the capture with inline 16-byte moves, and the capture's size only grows (the
   `assign` was a `memmove` call a draw, and a resize for a capture last used by a shorter delta).
2. `QueueDraw`: the three "anything pending" checks inline, relaxed (`g_pending_count`, `g_deferred_count`,
   `g_waiting`, moved out of their anonymous namespaces); `FlushDeferredVertices` / `RunReadyCallbacks` only when one may
   be pending.
3. The draw hooks: `IsRecordingCommandBuffer` inline (the device's command buffer word).
4. `QueueDraw`: `DeltasOn()` latched (`Latched::snapshot_deltas`).
5. The render queue: a draw is queued as `fn(arg)` (`QueuePrefetchedFn`, `RunCapture`), not a `std::function` (made,
   moved and destroyed with a manager call at every draw).
6. `FlushRecordedVertices`: its nothing-pending test inline in `command_buffers.h`; every Direct3D hook calls it first.
7. `FlushDeferredVertices`: the same, in `queued.h`.
8. The chain lock (`g_delta.mutex`, taken at every draw): libnx's `Mutex` directly on the Switch (`ChainMutex`), not
   `std::mutex` through `pthread_mutex_lock` and newlib's lock layer.
9. `InputSystem::GetState`: the device list reused per thread (no allocation at every controller read).
10. `InputSystem::SetState` (and the two other device-list readers): the same.

Looked at and left: a raw `RtlLeaveCriticalSection` (the export thunk is inlined and writes no register for a void
function: nothing to gain), the enter path's spin-count read (the lock's own cache line), `SetStreamSource` /
`SetTexture` (their cost is the game's resource objects' lines) and `Active()` (already inlined).
- **Machine**: `localized_bulk.txt` has every generated function with a sample in the four console runs (v4-v7, all
  threads): 538 listed, 536 made (codegen 8 min, the PC build 22 min).
- **PC `v8cpuverify`**: compare mode 528 of 536 copies reached, 28.7 M calls, 0 differences (the run is slower in compare
  mode with this many copies: it reached a Fury attack); delta verify 0 of 1,015,711; self-checks, r1 mirror and
  flush-mode flow 0.

## The sixth console run (v8, 2026-10-29 17:43-17:47, handheld, stock clocks, three cores)

The user's logs are in `out/package_20261029_v7/sd/switch/bangaio-nx/newlogs`: `renut_002.log` is v8's run (536
copies); `renut_001.log` is v7's, carried over. The heaviest storm yet: up to 5,563 draws a frame (19.6 fps, frame
51 ms, render thread 38.8 ms, GPU 29.5 ms).
- **Band averages mislead here** (v8's 3,000+ windows averaged 3,912 draws, v7's 3,575). A least-squares line of frame
  time against draws a frame per version (windows of 1,500+ draws, `tools/console_fit.py`):

| | 2,500 draws | 3,500 draws | 4,500 draws |
|---|---|---|---|
| v3 | 30.6 fps | 25.8 | 22.4 |
| v4 | 38.2 | 30.5 | 25.4 |
| v5 (PGO+LTO) | 39.4 | 32.7 | 27.9 |
| v6 | 36.8 | 29.3 | 24.3 |
| v7 | 39.1 | 30.4 | 24.9 |
| v8 | 38.4 | 29.4 | 23.8 |

  v8 is v7 within ~3 % (slightly under). The render thread and the GPU per frame are the same at matched loads.
- **Game thread**: copies 55.9 %, host 31.5 %, hooked 9.4 %, generated 3.2 % (v7: 55.4 / 31.3 / 7.5 / 5.8).
  - `CaptureDelta` 15.2 % (v7 15.0 %); mutex lock + unlock 2.8 % (v7 3.1 %); `QueueDraw` 1.0 % (v7 1.3 %).
  - The game thread is still 85-90 % CPU in the storm.

  v8's hand optimisations each took a few tenths of a percent, inside the noise, and the 305 extra copies moved
  generated code into copies and hooks without changing the work. What is left on the game thread is the game's own
  code (spread, ~1-4 % a function) and `CaptureDelta`'s 80 cache lines a draw.
- **At the heaviest moments the GPU is a wall too**: 27-30 ms a frame at 4,700-5,600 draws, so the CPU alone cannot
  hold 30 fps there.

## 1.0.0: the release settings (2026-10-29, the user's list)

The user: PGO + LTO, logging off, handheld 720p and docked 900p by default with docked 1080p as an option, a language
option, banjo-nx's SMAA on by default with an option to turn it off, version 1.0.0, author ChanseyIsTheBest, their logo
as the icon (centred, black above and below). Then: the toml holds only the options they named, as the only ones a
player cares about.

- **The toml** (`dist/switch/bangaio-nx/renut.toml`): `docked_resolution` (900 or 1080), `smaa` (true / false),
  `language` ("english", "japanese", "french"). `src/bangaio_settings.cpp` hands each one the toml sets to its key in
  `OnPreSetup`, after the toml is loaded (`banjo_renut_render_height_docked`, `banjo_renut_smaa`, `user_language`), so
  those keys keep working on their own. Every other setting the old toml carried is now the build's default:
  `banjo_renderer = "renut"`, `renut_gpu_backend = "deko3d"` (Switch), `license_mask = 1`, `headless` (Switch),
  `banjo_show_fps` and `banjo_stall_watch_seconds` off, `log_level = "off"` (Switch). With the level off `rex_app.cpp`
  makes no log file at all (an empty one appeared at every start). The old toml is `renut_log.toml` (log and profiler
  on, for console test runs; not packaged), and `renut_play.toml` / `renut_ab.toml` stay in `dist/` as before.
- **Language**: the game reads XConfig's user language (`ExGetXConfigSetting(3, 9)` in `sub_8215E218`, the SDK's
  `user_language`), and its 19 callers test the result for 2 (Japanese) and 4 (French) only; anything else is English.
  PC `lang_fr` / `smaa1`: the French title, HUD and prompts ("APPUYEZ SUR LA TOUCHE A", "JOUEUR 1", "QUITTER"); PC
  `lang_ja`: the title asks for A instead of START. The PC's scripted pad never reached the menus (`input_script` does
  not act on the PC build: the composite runs show the attract demo, not play), so the Japanese menus are checked in
  the emulator.
- **SMAA and the internal resolution need the frame's final composite** (`banjo_renut_smaa_after_ps`: SMAA runs right
  after it, and docked 900 lines are scaled to the 1080 display there, with the HUD drawn over at 1080). N&B's
  shader is not in Bangai-O, so before 1.0.0 the configs' SMAA never ran and a docked height under the display's drew
  the whole frame at the display's resolution. PC draw log `composite2` (two frames of the attract demo): the 640x360
  glow pass (draws 0-579), then at 1280x720 a full-screen additive draw (vs B39ECA48, **ps E3876A9EE8EE968A**, blend
  ONE+ONE) at draw ~580 (the background), the map and sprites, the **same draw again at ~1290** (the 640x360 glow
  added over the playfield), then only the HUD's sprites (186). `banjo_renut_composite_skip = 1` passes over the
  frame's first: `FinalCompositeLocked` in `render/draw.cpp` counts the shader's draws per frame
  (`TextureFrameLocked`). PC `smaa1`: SMAA on every gameplay frame (560-597 a 10 s line) and none in the menus (one
  such draw a frame there: drawn whole at the display's resolution, as banjo-nx's menus); its picture is the playfield
  with the glows and the enemy banners and none of the HUD; 13-14k pixels changed, the optimised passes 0 different
  from SMAA itself.
- **Icon**: the user's `bango.png` (1174x409, transparent) scaled to 256x89 and centred on black,
  `tools/switch/icon/bangaio_icon.jpg`. NRO: version 1.0.0, author ChanseyIsTheBest.
- **Package** (`tools/bangaio_package.ps1`): the NRO, `renut.toml`, the four-core NPDM, `README.txt` (setting up, the
  settings, the credits), the ELF and map, the source archive; no configs or test tomls.
- **Logging off, all of it** (the release default `log_level = "off"` on the Switch): no game log (`rex_app.cpp`), no
  `rex_profile.log` and no L+R+ZL GPU A/B lap (`switch_perf.cpp`: both need the log on; the A/B lap skipped parts of
  the drawing for 80 s, and L+R+ZL can happen in play), no `deko3d.log` (`banjo_renut_deko3d.cpp`). The overlay's FPS
  and resolution feed stays. `rex_stderr.log` stays on purpose: the crash net (stderr of Mesa, plume and
  `rex::FatalError`, rewritten at each boot, ~1.5 KB of startup lines); `rex_crash.log` only on a crash. Every
  setting the old toml carried is the build's default, checked key by key against `renut_log.toml` and
  `renut_play.toml`.
- **PGO 6** (the 1.0.0 code): v5's profile set aside (`pgo_v5/`); session `pgo6` (380 s with `renut_play.toml`,
  play with game overs and retries), merge 146 files (largest arc count 2,076,601,115); clean PGO-use + LTO build
  (0 coverage mismatches), NRO 37.7 MB. `banjo_renut_deko3d.cpp` changed after the profile with its line count kept,
  so only `InstallShaderCache` (once at startup) loses its profile; `switch_perf.cpp` is not instrumented.
- **Emulator checks of the final NRO**: `v100final` (handheld, every verify key): delta verify 0 different in every
  line (up to 337,899 draws a line), pushed constants 0 wrong, store cards 0 changed, native copies 498 of 536
  reached with 0 differences, fast draws 99.9 %, SMAA on gameplay frames (up to 426 a 10 s line); only slow file
  reads as warnings. `v100docked_ja` (the shipped toml with `language = "japanese"`, the profile's `docked_mode`
  true for the run and restored byte for byte after): "Render resolution 1600x900", SMAA textures 1600x900, the
  composite scaled up for the HUD on every gameplay frame (565-586 a line), captures 1920x1080 with the HUD sharp;
  the main menu's help line and buttons in Japanese (the menu items are the game's own English logos).
  `v100release` (exactly the shipped toml, captures only): no game log, no `rex_profile.log`; it found `deko3d.log`,
  fixed after. `v100release2` (the rebuilt NRO, the shipped toml): the SD got only the save, `rex_stderr.log` and the
  run script's NRO and toml copies; play as usual.
- **The 1.0.0 package**: `out/package_1.0.0` (commit `4282679a`, NRO 35.9 MB, sha256 `B024188248B42DFD...`; the ELF
  and map also in `out/nx_elf/bangaio_1.0.0.*`).

## The web installer and the distribution NRO (2026-10-30, the user's request: "like nights into dreams")

The 1.0.0 package's NRO embeds the game's shaders (the GLSL package and the SPIR-V table made from the game's files),
so it is for the user's own use. What is published is nights-nx's arrangement: a **distribution NRO** that carries
none of them, and a **web installer** (`D:\bango\bangaio-nx-installer`, from `D:\nights\nights-nx-installer`) that
makes them in the player's browser from their own copy.

- **Distribution NRO** (`out/dist_1.0.0/bangaio-nx.nro`, sha256 `4D7D4452...`, 36.6 MB; ELF and map beside it):
  `tools/renut_switch_shader_cache.py --pc app/out/pc-nx --only <empty folder> --out-dir app/out/renut_switch_dist`
  (0 of 95 shaders, no SPIR-V), and `app/out/switch-pgo-use` configured with `BANJO_RENUT_SHADER_CACHE_CPP` at that
  table and `BANJO_DEKO3D_GLSL_CPP` at a file that does not exist (no embedded package; the symbols are weak). An
  incremental PGO-use + LTO build (4 min: the table, the two SDK files that include the configure-time build stamp,
  the link), the 1.0.0 code otherwise. The folder was configured back to `app/out/renut_switch/` after. No `BDKG`
  package and no zstd frame in the NRO (the 1.0.0 NRO: one package, 86 frames). It logs "this NRO has no GLSL
  package" once (`Open()`, the embedded package; an error line only with the log on) and then reads the installed one.
- **The installer's changes to nights-nx-installer**: `lib/bangaio_dump.js` (the image's containers by
  `find_shader_headers`, plus `media/shader/*.xvu` / `*.xpu`); one package (title `58410AF2`, content type
  `000D0000`, no title update) or the extracted folder; the zip's extra files from the manifest with paths from the
  SD card's root: `switch/bangaio-nx/renut.toml` (the three settings: the NRO does not write one at its first start,
  as nights-nx's does), `pipeline_list.bin` (the emulator SD's, 132 pipelines), the four-core NPDM in
  `atmosphere/contents/05BA6A1000001000/exefs/`; the page in the logo's colours, the icons from the user's logo.
- **Variants** (`release/variants.txt`): `tools/deko3d_variant_cache.py --list <SD pipeline_list.bin> --runtime-log`
  (the three logs that compiled at run time: the console's first and the emulator's `emu1` / `emu2`) `--generic
  --export-variants`: 137 variants, every key checked; the run-time logs added none the list did not have. The same
  run wrote the native reference cache `out/deko3d_shaders/deko3d_shaders_installer.bin`.
- **Node test** (`test/full_node.mjs D:/bango/game D:/bango/bangaio-nx out/installer_test`, 31 s): 95 containers (84
  in the image, 11 in `media/shader`), 95 of the native dump's 95 byte for byte; the shader table's numbers the same
  for all 95; GLSL 31 of 95 the native text, the other 64 the native text under a consistent one-to-one renaming of
  DXC's `_N` temporaries and nothing else (the web DXC is v2025.1); **all 137 variants compile to the native DKSH bytes**
  (each variant's web and native GLSL compiled and compared), so the console runs the same shader code as 1.0.0.
  `test/stfs_node.mjs`: the package read in place gives 855 of 855 files the same as `tools/stfs_extract.py`'s.
- **Browser test** (built-in browser, `serve.py --test-files`; `test/browser.html` rewritten for the worker's input):
  the package (`?mode=package`, 53 s) and the extracted folder (`?mode=folder`): 95 shaders, 137 variants, "identical
  to the release's reference build"; a 315 MB zip with 861 entries; the NRO, renut.toml, pipeline list, NPDM and the
  two shader files at the manifest's SHA-256; 855 game files with their CRC-32. The page itself: the package detected
  ("Bangai-O HD: Missile Fury"), a non-package refused, the download service worker registered.
- **Emulator `installer1`** (the distribution NRO with exactly the installer's two shader files and the release's
  pipeline list, `emu_base.toml`, 200 s; `COMMIT_GB=11`, no other Ryujinx running): "installed GLSL package: 95
  shaders", "Shader table: 95 shaders from the installed package", "DKSH cache: 137 variants", **uam 0 compiles** all
  run (the cache file unchanged after); delta verify 0 of 273,853, pushed constants 0, store cards 0, native copies
  0 differences, fast draws 99.9 %, SMAA 60 frames a line; play to a stage. The SD's shader cache and the 1.0.0 NRO
  were put back after.

## GitHub (2026-10-30, the user's request; public, as the NiGHTS repos, the user's choice)

- **https://github.com/ChanseyIsTheBest/bangaio-nx**: one commit (`da4a2991`, "bangaio-nx 1.0.0"), made as nights-nx's
  was: this repository's tree at `fa9c4838` / the icon-path fix, without `app/src/renut_engine/fixes/mullhwucrash.cpp`
  (reNut's recompiled N&B code, not built here) and `app/icon/app.aps` (banjo-nx's icon in a resource cache), no
  history. Made from this repository's own objects (`git read-tree` into a separate index, `git write-tree`, `git
  commit-tree` with no parent), so every file is the committed bytes (an exported copy re-added had changed the CRLF
  files). Local branch `github` and remote `github` (`git push github github:main`); later public changes go on
  `github` as commits of their own. 23,275 files, no `.nro` / `.bin` / `.xex`.
- **Release v1.0.0**: the distribution NRO (`out/dist_1.0.0/bangaio-nx.nro`, sha256 `4d7d4452...`, GitHub's digest
  the same), notes pointing at the installer.
- **https://github.com/ChanseyIsTheBest/bangaio-nx-installer** (`main`, GitHub Pages from `/`):
  **https://chanseyisthebest.github.io/bangaio-nx-installer/**. On the live page the NRO and the zip's three extra
  files fetch at the manifest's SHA-256, `shader_common.h` and `variants.txt` are the tested bytes (`.gitattributes`:
  `release/** -text`), the WebAssembly is served as `application/wasm`, and the download service worker registers.

## The four-core mode removed (2026-10-30, the user's request: "the game doesn't need it")

banjo-nx's port of NetherSX2_nx's four-core mode (2026-10-27) is out of the game and the installer; 1.0.0 republished.
- **SDK**: `threading_switch.cpp` keeps the thread registry, pins and priorities; gone are the cvars
  `banjo_system_core`, `banjo_system_core_xma`, `banjo_system_core_mixer_priority`, `banjo_system_core_test` and
  `banjo_forwarder_program_id`, the system-core state and API (`RexSwitchInitSystemCore`, `RexSwitchSystemCore`,
  `...Mode`, `RexSwitchAppCoreMask`, `RexSwitchProcessCoreMask`, `RexSwitchMoveCurrentThreadToSystemCore`,
  `RexSwitchSystemCoreXma`, `...MixerPriority`, `...Describe`, the core-idle samples), the NPDM writer
  (`RexSwitchEnsureForwarderNpdm`, `forwarder_npdm.inc`) and `__wrap_svcSetThreadCoreMask` (and its `--wrap` in
  `sdk/cmake/rexglue_switch.cmake`). `RexSwitchUnpinCurrentThread` takes the process's three cores
  (`InfoType_CoreMask & 0x7`). The callers: `rex_app.cpp` and `windowed_app_main_switch.cpp` (init, NPDM, the log
  line), `switch_perf.cpp` (the system core's idle line), `xthread.cpp` (Audio Worker / XMA Decoder moves),
  `switch_audio_system.cpp` (the output thread's move and idle samples). With the usual three cores none of this ran,
  so the game's behaviour is the same; launched by a forwarder granting four cores, the game no longer uses core 3.
- **App**: `banjo_renut_tuning.cpp` (`banjo_system_core_compiles` / `_uam`: the compiles stay on
  `banjo_background_compile_core`; the render thread's system-core log line), `me_platform_compat.h`'s stubs,
  `banjo_xaudio_native.cpp`'s two mixer-thread hooks (N&B's, not built here).
- **Files**: `tools/forwarder/` and `bangaio_forwarder.json` deleted; the test tomls, `dist/README*.txt`, `README.md`
  and `tools/bangaio_package.ps1` without the NPDM; NetherSX2_nx's credit dropped (none of its code is left). Only
  comments about other ports' past measurements ("four-core, 30 s halves") still say the word.
- **NRO**: the distribution build again (incremental PGO-use + LTO, 17 steps; the changed SDK files keep only the
  profile of the functions before their first edit), `out/dist_1.0.0/bangaio-nx.nro`, sha256 `3bf298ef...`, 36.6 MB,
  no `05BA6A1000001000` or four-core key in it. `app/out/switch-pgo-use` configured back to `app/out/renut_switch/`
  after (its objects are the four-core-free sources now; the next normal build relinks).
- **Installer**: the NPDM out of `release/`, the manifest, `tools/make_release.py`, the page and README; the zip is
  `switch/bangaio-nx/` only (860 entries). Browser test (package): identical to the reference, every file at the
  manifest's SHA-256.
- **Emulator `installer2`** (the new NRO, the installer's two shader files, `emu_base.toml`, 200 s): the installed
  package and the 137-variant cache read, uam 0 compiles all run, delta verify 0 of 317,573, pushed constants 0,
  store cards 0, native copies 0 differences, SMAA up to 108 frames a line, a missile storm on screen.
- `out/package_1.0.0` (the personal package with the embedded shaders) is the earlier build and still has the mode.

## Next steps (2026-10-29)

1. **Point sprites on the console** (above): A/B 69 where missiles fly. Not done in this port: the push block that
   the fast path pushes for point-sprite pipelines (`kp_hot.point_sprite`, 24 bytes of zeros) is read by nothing on
   deko3d (the geometry shader reads binding 2 only); dropping it there is a few command words a point draw.
2. **The snapshot deltas on the console**: done in v3 (above); `banjo_renut_snapshot_deltas` can only be set at start
   (no in-run A/B), so its console measure is v2 against v3 (same profile route, the 10 s lines' game thread and
   render thread at the same busy moment), or v3 with the key set false in renut.toml.
3. **XAudio2's mixer thread on core 3** (four-core mode): banjo-nx's hooks are on N&B's XAudio (1.x) CEngine entry
   points, which XDK 20209's XAudio2 does not have; the SDK still moves the Audio Worker and XMA Decoder by name. Find
   XAudio2's processing thread entry (its guest CreateThread) and move it as banjo-nx does.
4. **The register options left off**: `non_argument_as_local` and `elide_lr_stores` (banjo-nx measured -10 % on its main
   thread) after Bangai-O's audit (`tools/non_argument_audit.py`, the ctx.lr readers).
5. A console profile of a busy stage: the hot functions and the A/B list are the emulator's until then.
