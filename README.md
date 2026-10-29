<div align=center>

<img src="tools/switch/icon/bangaio_icon.jpg" alt="Bangai-O HD: Missile Fury" width="25%">

</div>
<h1 align=center>Bangai-O HD: Missile Fury — Nintendo Switch port</h1>

A native Nintendo Switch port of the Xbox 360 (Xbox Live Arcade) version of **Bangai-O HD: Missile Fury** (title
`58410AF2`).

It is not an emulator. The PowerPC code of the game's `default.xex` is statically recompiled to C++ with
[ReXGlue](https://github.com/rexglue/rexglue-sdk) and compiled for the Switch, and the game is drawn by Renut's
Direct3D-level renderer ([reNut](https://github.com/masterspike52/reNut) by masterspike52, as banjo-nx carries it)
directly on the Switch's own graphics API, deko3d.

> [!NOTE]
> You need your own copy of the game: its Xbox Live Arcade package from an Xbox 360
> (`Content/0000000000000000/58410AF2/000D0000/`). The game has no title update. No game files and no shaders made
> from them are in this repository or its releases.

## How to install

Use the **[bangaio-nx installer](https://chanseyisthebest.github.io/bangaio-nx-installer/)**
([its source](https://github.com/ChanseyIsTheBest/bangaio-nx-installer)): a web page that takes your package (or the
folder you extracted it to), makes the game's shaders for the Switch from it in your browser (nothing is uploaded)
and gives you a zip to extract to the root of your SD card. Start `switch/bangaio-nx/bangaio-nx.nro` from the
Homebrew Menu with a title takeover (hold R while starting a game).

## Settings

`switch/bangaio-nx/renut.toml` holds only the player's options:

| Setting | Default | |
|---|---|---|
| `docked_resolution` | `900` | docked: `900` = drawn at 1600x900 and shown at 1920x1080 (the HUD and text drawn at 1080); `1080` = everything at 1920x1080 (more GPU work). Handheld is always 1280x720 |
| `smaa` | `true` | SMAA edge smoothing on the playfield (the HUD and text stay as they are) |
| `language` | `"english"` | `"english"`, `"japanese"` or `"french"` |

Everything else is built into the NRO. Any other setting written in `renut.toml` overrides the built-in one. Logging
is off; only `logs/rex/rex_stderr.log` (about 1.5 KB, rewritten at each start) is kept, for crash reports.

## Building

The Switch build cross-compiles with devkitA64 (`tools/build_switch.bat`, PGO + LTO for the release); the PC build
(`tools/build_pc.bat`) uses reNut's renderer on Vulkan. Both need the code generated from your own `default.xex`
(ReXGlue's codegen with `app/config/`, `tools/codegen.ps1`), which is not in this repository. The release NRO is a
distribution build: its shader table is empty (`tools/renut_switch_shader_cache.py --only` on an empty folder, no GLSL
package), and it reads the shaders the installer makes. Notes: `docs/`.

## Credits

- [ReXGlue](https://github.com/rexglue/rexglue-sdk) (the recompiler and runtime) and its Discord.
- reNut's renderer by masterspike52 (its author permits its reuse in these ports), SolarCookies (mid-asm hooks, the
  reNut launcher), ValcomDrifty, OlieGamerTV.
- banjo-nx (this port's base), nights-nx (the hook pairing tools, the installer), sa2-nx (input, CPU work),
  peggle2-nx, bejeweled3-nx and the Zuma ports (frame pacing, the hot-function method, the Direct3D tools).
- battd_nx (the GPU arena).
- SMAA by Jorge Jimenez et al. (MIT).

GPL-3.0 where the sources are (LICENSE). Bangai-O HD: Missile Fury is (c) Treasure Co., Ltd.; this project is not
affiliated with Treasure.
