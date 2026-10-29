Bangai-O HD: Missile Fury for the Nintendo Switch - bangaio-nx 1.0.0 by ChanseyIsTheBest
=========================================================================================

A native Switch port of the Xbox 360 game (XBLA), recompiled with ReXGlue and drawn with reNut's renderer on deko3d.
It holds no game data: you need your own copy of the game, extracted from its Xbox 360 package.

Setting up
----------
1. Copy sd/switch/bangaio-nx/ to sdmc:/switch/bangaio-nx/ on your SD card.
2. Put your extracted game in sdmc:/switch/bangaio-nx/game_root/ (the package's contents: default.xex, media/,
   ArcadeInfo.xml ...).
3. Launch bangaio-nx from the homebrew menu.

Settings (sdmc:/switch/bangaio-nx/renut.toml)
---------------------------------------------
  docked_resolution = 900       900: drawn at 1600x900 and shown at 1920x1080 (the HUD and text at 1080).
                                1080: everything at 1920x1080 (sharper, more GPU work). Handheld is always 1280x720.
  smaa = true                   SMAA anti-aliasing of the playfield (the HUD and text are not touched). false = off.
  language = "english"          "english", "japanese" or "french".

The game keeps its progress in sdmc:/switch/bangaio-nx/renut/58410AF2/profile/.

Credits
-------
- ReXGlue SDK (the rexglue team) and its Discord.
- reNut's renderer (masterspike52), SolarCookies (mid-asm hooks, the reNut launcher), ValcomDrifty, OlieGamerTV.
- banjo-nx (the base of this port), sa2-nx (input, CPU work), nights-nx, peggle2-nx, bejeweled3-nx and the Zuma
  ports (frame pacing, the hot-function method, the Direct3D tools).
- battd_nx (the GPU arena).
- SMAA by Jorge Jimenez et al. (MIT).
- Bangai-O HD: Missile Fury is (c) Treasure Co., Ltd. This port contains none of the game's data.
