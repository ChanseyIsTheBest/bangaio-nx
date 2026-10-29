bangaio-nx - Bangai-O HD: Missile Fury on the Switch (ReXGlue, Renut's renderer on deko3d)
=====================================================================================

What this package is
--------------------
A test build for your own console. It holds no game data: copy YOUR extracted game beside the NRO.

v8 (this package) against v7: also a TEST build without PGO or LTO, for the game thread (your fifth run's limit).
10 hand optimisations of the game thread's draw and hook paths (the state capture's copy, the per-draw pending checks
and recording check inline, draws queued without a std::function, the draw lock straight to libnx's mutex, the hooks'
first checks inline, no allocation at each controller read) and every game function your four console runs sampled is
now machine-optimised (536). Same picture: the copies' compare, the delta verify and the emulator's verify keys found
0 differences.
v7 against v6: also a TEST build without PGO or LTO. Your fourth run showed the vertex cache's 100,000
entries were whole-buffer entries (every whole-buffer try made one, and nothing dropped them): now one is made only
when its buffer comes round again and dropped a second later if it never got a copy. Also 15 hand optimisations of the
hottest functions (the six common vertex swizzles in registers, 53 per-draw switches read without a guard, the
critical section's settings, the replaced-range walk, ...), 85 more of the game's functions machine-optimised (231 in
all), the state prefetch off (no gain on your console) and the critical-section spin off again (it only spun). Same
picture: the copies' compare, the delta verify and the emulator's whole-buffer verify found 0 differences.
v6 against v5: a TEST build, without PGO or LTO (those come back for the final build), so compare it
with v5 knowing that v5's PGO+LTO alone is worth a few percent. Your third run showed the vertex-range cache growing to
131,408 entries in the storm (the game reuses its sprite buffer's places within seconds): every such entry is now
looked at 8 frames after it was made and dropped unless it is becoming a copy (PC: 5,581 entries at most). A queued
draw prefetches the device lines the game thread's state compare reads (those loads were its cost in your profile),
and the render queue no longer calls pthread_once at every draw. Same picture: the delta verify, the copies' compare
and the emulator's verify keys found 0 differences. New A/B target 74.
v5 against v4: your second console run showed the game thread limiting the storm. v5 finds a draw's
changed Direct3D state with NEON masks (that compare was 18 % of the game thread), keeps the vertex-range cache at about
8,000 entries instead of ~100,000 (its walks were 13 % of the render thread), runs 84 more of the game's hottest functions
from your two storm profiles as machine-optimised copies (146 in all), and lets a contended critical section spin
briefly before a full kernel wait (kernel_critsec_spin = 64, in renut.toml). Same picture: the delta verify, the hot
copies' compare and the emulator's verify keys found 0 differences. New A/B target 73.
v4 against v3: the fixes for your first console run's missile storm (22-25 fps at ~4,250 draws a
frame, handheld). The game thread no longer makes and frees ~2,200 device captures a frame (deltas copied at their size,
a pool of up to 8,192), the render thread no longer keeps ~190,000 single-use vertex-range cache entries (an entry is
made the second time a range is drawn), and Bangai-O's sprites (quad lists) are drawn with one index buffer made once
instead of indices made at every draw. Same picture: the delta verify found 0 differing draws, every key 0 in the
emulator. In-run A/B targets 70, 71, 72 (renut_ab.toml) measure each one where missiles fly.
v3 against v1: the post-codegen passes now use Bangai-O's own addresses (memcpy / memset inlined at 407 call sites,
2,457 dead register write-backs dropped, the no-return list), Bangai-O's point sprites take the pushed constants and
the fast draw path, the snapshot deltas work (below), and a new PGO profile from more gameplay.
The game keeps its progress in its profile settings: sdmc:/switch/bangaio-nx/renut/58410AF2/profile/.

  sd/switch/bangaio-nx/bangaio-nx.nro        the game (built from the commit in source/)
  sd/switch/bangaio-nx/renut.toml            shipped settings: log + console profiler ON (logs/ beside the NRO)
  sd/switch/bangaio-nx/renut_play.toml       the same with every diagnostic off: copy over renut.toml to just play
  sd/switch/bangaio-nx/renut_ab.toml         in-run A/B measurement (30 s halves, control target 1)
  sd/switch/bangaio-nx/configs/*.toml        options that CHANGE THE PICTURE (your decision; not on by default)
  elf/                                       the NRO's ELF and link map (send them back with a console profile)
  source/                                    a source snapshot of the build (no game data)

Setting up
----------
1. Copy sd/switch/bangaio-nx/ to sdmc:/switch/bangaio-nx/.
2. Put your extracted game in sdmc:/switch/bangaio-nx/game_root/ (the STFS package's contents: default.xex,
   media/, ArcadeInfo.xml ... exactly as stfs_extract.py writes them).

What to test (in this order)
----------------------------
1. Boot: Treasure logo, loading screen, title ("PRESS START BUTTON"). The save prompt is answered by itself
   (headless = true takes the focused button: create the save data).
2. Menus: Single Player -> Stage 1 -> Dr. Ban's briefing (A = next) -> gameplay. Menu panels and the sky should look
   as on the 360 (the menu is a 3D fly-through of sky panels).
3. Gameplay at stock clocks, handheld then docked: the frame rate in the log's 10 s lines
   ("[renut] 10.0 s: N game frames (X fps), render thread busy Y ms a frame, GPU Z ms a frame").
   The emulator held 60 fps in menus and normal play; the heaviest moment (a game over with hundreds of missiles,
   ~1,130 draws a frame) ran 26-28 fps there with the render thread at ~28 ms a frame. The console's number is the
   one that counts: please play a busy stage (lots of missiles / a Fury attack) and send the logs.
4. Audio (music, effects), the pause menu, quitting to the home menu (the process should close cleanly).
5. Second controller (guest sign-in for 2P if the game offers it).

Sending back a console profile
------------------------------
With renut.toml as shipped, sdmc:/switch/bangaio-nx/logs/ holds the game log (renut_*.log) and logs/rex/rex_profile.log
(every 10 s: each thread's CPU and sampled stacks). Send both with the ELF/map of this package: the hot functions
and the render thread's lines are read from them.

The A/B run
-----------
Copy renut_ab.toml over renut.toml, stand at one static spot (a stage, paused or idle) at stock clocks, 10+
minutes. Each target in turn is switched off for 30 s and on for 30 s; the log's
"[renut A/B]" lines give both halves. Target 1 does nothing on the Switch: it is the control (its difference is the
noise). Targets: 3 shared-constants dedupe, 5 capture pool, 7 bool specialisation, 8 blend skip, 20 chain reuse,
31 texture refill skip, 62 whole-snapshot draws on the fast path, 67 repeated clears not sent, 69 point-sprite draws
pushed and on the fast path (new in this port: measure it where missiles fly, not on a still screen).
New in v4, also only where missiles fly (a Fury attack, a busy stage): 70 small captures in a larger pool, 71 stream
cache entries made at a range's second sighting (v5: and dropped when unused or rewritten), 72 quad lists drawn with
one index buffer. New in v5: 73 the game thread's NEON delta masks. New in v6: 74 the delta lines' prefetch.

GPU time in the storm (for the next step): the storm's GPU time was ~22 ms a frame, 14 ms of it in the 640x360 pass
(blended glow and explosion sprites). One run with banjo_renut_diag_gpu_shaders = true added to renut.toml splits that
time by pixel shader; send its log with a storm in it.

Picture-changing options (configs/, your decision)
-------------------------------------------------
bangaio_smaa.toml               SMAA 1x on the 3D image
bangaio_docked_1080.toml        docked rendering at 1080 lines (sharper, more GPU)
bangaio_handheld_540.toml       handheld 3D at 540 lines scaled to 720 (less GPU, softer)
bangaio_dynamic_resolution.toml dynamic resolution by the GPU's time
Each is renut.toml plus the keys its first lines name.

Known
-----
- banjo_renut_snapshot_deltas is ON again from v3: v1 and v2 copied the whole Direct3D device (12.9 KB) at every
  draw because Bangai-O's XDK writes some vertex constants through BeginShaderConstantF4, which clears their dirty
  marks; Renut now hooks it and marks them (verified: 0 differing draws). A draw now keeps about 250 bytes.
- Bangai-O's missiles are point sprites. From v2 they take the pushed constants and the fast draw path
  (banjo_renut_point_fast_draw, A/B 69); the heaviest scenes were render-thread bound before it.
