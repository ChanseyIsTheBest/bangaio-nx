#!/bin/bash
# bangaio-nx (from nights-nx's / banjo-nx's emu_run.sh): one Ryujinx run of the SD card's NRO in this port's own data
# folder (D:\New folder\ryu-data\bangaio), with a toml made from a base toml plus extra keys; captures and the log are
# moved to out/emu/<name>. Only this run's process is stopped, by its PID (never Ryujinx by name: other ports run
# theirs). Starts only when no Ryujinx runs at all and the free commit memory is 13 GB or more (another port's emulator
# can run the host out of memory).
#
#   tools/emu_run.sh <name> <seconds> [key = value ...]      NRO=<path> copies that NRO in first; BASE=<toml>
set -u
NAME=$1; SECS=$2; shift 2
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/out/emu/$NAME"
DATA_W='D:\New folder\ryu-data\bangaio'
SD="/d/New folder/ryu-data/bangaio/sdcard/switch/bangaio-nx"
BASE=${BASE:-$ROOT/dist/emu_base.toml}
mkdir -p "$OUT" "$SD"
if [ -n "${NRO:-}" ]; then
  cp "$NRO" "$SD/bangaio-nx.nro" && md5sum "$SD/bangaio-nx.nro" | cut -c1-12
fi
# No Ryujinx of any port running, and free commit memory (GB).
# (2026-10-29: every 10 s for up to 60 minutes; other ports' runs take the emulator within seconds of it being free.)
for i in $(seq 1 360); do
  R=$(powershell.exe -NoProfile -Command "@(Get-Process Ryujinx -ErrorAction SilentlyContinue).Count" | tr -d '\r')
  F=$(powershell.exe -NoProfile -Command "\$o=Get-CimInstance Win32_OperatingSystem; [int](\$o.FreeVirtualMemory/1MB)" | tr -d '\r')
  [ "$R" -eq 0 ] && [ "$F" -ge "${COMMIT_GB:-13}" ] && break
  [ $((i % 6)) -eq 1 ] && echo "Ryujinx processes ${R}, free commit ${F} GB: waiting"; sleep 10
done
if [ "$R" -ne 0 ] || [ "$F" -lt "${COMMIT_GB:-13}" ]; then echo "emu run $NAME: not started (Ryujinx ${R}, ${F} GB)"; exit 2; fi
echo "free commit ${F} GB"
python - "$BASE" "$SD/renut.toml" "$@" <<'EOF'
import re, sys
text = open(sys.argv[1], encoding='utf-8').read()
for kv in sys.argv[3:]:
    k, _, v = kv.partition('=')
    k, v = k.strip(), v.strip()
    pat = re.compile(r'^%s\s*=.*$' % re.escape(k), re.M)
    line = '%s = %s' % (k, v)
    if pat.search(text):
        text = pat.sub(line, text)
    else:
        m = re.search(r'^\[', text, re.M)
        text = text[:m.start()] + line + '\n' + text[m.start():] if m else text.rstrip('\n') + '\n' + line + '\n'
open(sys.argv[2], 'w', encoding='utf-8', newline='\n').write(text)
EOF
rm -f "$SD"/capturas/captura_*.png 2>/dev/null
powershell.exe -NoProfile -Command "\$env:DOTNET_ROOT = 'D:\New folder\dotnet10'; \$env:RYUJINX_HOMEBREW_SHADER_CACHE_ID = '05BA6A1000001000'; \$nro = '$DATA_W\sdcard\switch\bangaio-nx\bangaio-nx.nro'; \$p = Start-Process -FilePath 'D:\New folder\Ryubing-src\ryubing\build\Ryujinx.exe' -ArgumentList @('-r', '\"$DATA_W\"', ('\"' + \$nro + '\"')) -WindowStyle Minimized -PassThru -RedirectStandardError '$(cygpath -w "$OUT")\stderr.txt' -RedirectStandardOutput '$(cygpath -w "$OUT")\stdout.txt'; 'pid ' + \$p.Id; try { Wait-Process -Id \$p.Id -Timeout $SECS -ErrorAction Stop; 'exited by itself' } catch { }; Stop-Process -Id \$p.Id -Force -ErrorAction SilentlyContinue; Start-Sleep 2"
for f in "$SD"/capturas/captura_*.png; do [ -f "$f" ] && mv "$f" "$OUT/"; done
L=$(ls -t "$SD/logs" 2>/dev/null | head -1)
[ -n "$L" ] && cp -r "$SD/logs/$L" "$OUT/" 2>/dev/null
cp "$SD/rex_profile.log" "$OUT/" 2>/dev/null; cp "/d/New folder/ryu-data/bangaio/sdcard/switch/rex_profile.log" "$OUT/" 2>/dev/null
echo "emu run $NAME: $(ls "$OUT" | grep -c png) captures, log ${L:-none}"
