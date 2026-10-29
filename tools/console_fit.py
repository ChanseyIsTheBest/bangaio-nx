"""Frame time against draws a frame per version (windows with >= 1,500 draws a frame): a least-squares line, and the
frame time / fps it gives at matched loads. Also the render thread and GPU time per frame at those loads."""
import re, sys

line_re = re.compile(r'\[renut\] ([0-9.]+) s: (\d+) game frames \(([0-9.]+) fps\), render thread busy ([0-9.]+) ms a frame '
                     r'\((\d+) frames\), GPU ([0-9.]+) ms a frame')
snap_re = re.compile(r'device snapshots \(banjo_renut_snapshot_deltas\): (\d+) draws')

def windows(path):
    rows, cur = [], None
    for raw in open(path, errors='replace'):
        m = line_re.search(raw)
        if m:
            cur = dict(fps=float(m.group(3)), frames=int(m.group(2)), r=float(m.group(4)), g=float(m.group(6)), d=0)
            rows.append(cur)
            continue
        m = snap_re.search(raw)
        if m and cur is not None and not cur['d']:
            cur['d'] = int(m.group(1))
    return [r for r in rows if r['frames'] and r['d'] / r['frames'] >= 1500]

def fit(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    return my - b * mx, b

loads = [2500, 3500, 4500]
print('%-4s %3s  %-28s %-28s %-28s' % ('', 'n', *('at %d draws: fps / render / GPU' % l for l in loads)))
for name, path in zip(sys.argv[1::2], sys.argv[2::2]):
    w = windows(path)
    if len(w) < 2:
        print(name, 'too few windows'); continue
    xs = [r['d'] / r['frames'] for r in w]
    a, b = fit(xs, [1000.0 / r['fps'] for r in w])
    ra, rb = fit(xs, [r['r'] for r in w])
    ga, gb = fit(xs, [r['g'] for r in w])
    cells = []
    for l in loads:
        ft = a + b * l
        cells.append('%5.1f fps / %4.1f / %4.1f ms' % (1000.0 / ft, ra + rb * l, ga + gb * l))
    print('%-4s %3d  %s   (range %d-%d draws)' % (name, len(w), '  '.join(cells), min(xs), max(xs)))
