import csv
import math
import random
import statistics
import time
from pathlib import Path

from quadtree import Point, build_quadtree

SEED = 2026
SIZES = [100, 250, 500, 1_000, 2_500, 5_000, 10_000, 25_000, 50_000]
REPEATS = 7
QUERY_COUNT = 100
DOMAIN_METERS = 10_000
RADIUS_METERS = 500


def make_points(n, seed=SEED):
    rng = random.Random(seed)
    return [Point(rng.uniform(0, DOMAIN_METERS), rng.uniform(0, DOMAIN_METERS)) for _ in range(n)]


def median_ms(fn, repeats=REPEATS):
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.median(samples)


def run_benchmark(output_dir="graficas"):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED + 1)
    queries = [Point(rng.uniform(0, DOMAIN_METERS), rng.uniform(0, DOMAIN_METERS))
               for _ in range(QUERY_COUNT)]
    rows = []
    for n in SIZES:
        points = make_points(n)
        build_ms = median_ms(lambda: build_quadtree(points))
        tree = build_quadtree(points)
        brute_range_ms = median_ms(lambda: [[point for point in points
                                             if (point.x-query.x)**2+(point.y-query.y)**2 <= RADIUS_METERS**2]
                                            for query in queries])
        tree_range_ms = median_ms(lambda: [tree.range_search(q, RADIUS_METERS) for q in queries])
        brute_nearest_ms = median_ms(lambda: [min(points, key=lambda p:(p.x-q.x)**2+(p.y-q.y)**2)
                                               for q in queries])
        tree_nearest_ms = median_ms(lambda: [tree.nearest(q) for q in queries])
        rows.append({"n": n, "queries": QUERY_COUNT, "repeats": REPEATS,
                     "build_ms": build_ms, "range_brute_ms": brute_range_ms,
                     "range_tree_query_ms": tree_range_ms,
                     "range_tree_total_ms": build_ms + tree_range_ms,
                     "nearest_brute_ms": brute_nearest_ms,
                     "nearest_tree_query_ms": tree_nearest_ms,
                     "nearest_tree_total_ms": build_ms + tree_nearest_ms})
        print(f"n={n:>6}: construcción {build_ms:8.2f} ms | rango (100) lista {brute_range_ms:8.2f}, "
              f"árbol {tree_range_ms:8.2f} ms | nearest lista {brute_nearest_ms:8.2f}, "
              f"árbol {tree_nearest_ms:8.2f} ms")
    with (out / "metricas.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    colors = {"range_brute_ms":"#1f77b4", "range_tree_query_ms":"#e4572e", "range_tree_total_ms":"#2ca02c",
              "nearest_brute_ms":"#1f77b4", "nearest_tree_query_ms":"#e4572e", "nearest_tree_total_ms":"#2ca02c"}
    labels = {"brute_ms":"Fuerza bruta", "tree_query_ms":"Quadtree: consultas", "tree_total_ms":"Quadtree: construir + consultas"}
    width, height = 620, 400
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="{height}" viewBox="0 0 1240 {height}">', '<rect width="100%" height="100%" fill="white"/>']
    for panel, (kind, title) in enumerate([("range", "Búsqueda por radio (100 consultas)"), ("nearest", "Vecino más cercano (100 consultas)")]):
        ox = panel * width
        vals = [r[f"{kind}_{metric}"] for r in rows for metric in ("brute_ms", "tree_query_ms", "tree_total_ms")]
        lo, hi = min(vals), max(vals)
        ylo, yhi = math.log10(max(lo, 1e-5)), math.log10(max(hi, lo*1.01))
        xlo, xhi = math.log10(SIZES[0]), math.log10(SIZES[-1])
        def px(n): return ox + 55 + (math.log10(n)-xlo)/(xhi-xlo) * 510
        def py(v): return 330 - (math.log10(max(v, 1e-5))-ylo)/(yhi-ylo)*270
        parts += [f'<text x="{ox+310}" y="22" text-anchor="middle" font-family="sans-serif" font-size="16">{title}</text>',
                  f'<path d="M {ox+55} 60 V 330 H {ox+575}" fill="none" stroke="#444"/>']
        for tick in range(math.floor(ylo), math.ceil(yhi)+1):
            value = 10**tick
            if ylo <= tick <= yhi:
                yy = py(value)
                parts += [f'<path d="M {ox+55} {yy:.1f} H {ox+575}" stroke="#dce3ea"/>',
                          f'<text x="{ox+49}" y="{yy+4:.1f}" text-anchor="end" font-size="10">{value:g}</text>']
        for metric in ("brute_ms", "tree_query_ms", "tree_total_ms"):
            key = f"{kind}_{metric}"
            coords = " ".join(("M" if i == 0 else "L")+f"{px(r['n']):.1f} {py(r[key]):.1f}" for i,r in enumerate(rows))
            parts.append(f'<path d="{coords}" fill="none" stroke="{colors[key]}" stroke-width="2"/>')
            for r in rows: parts.append(f'<circle cx="{px(r["n"]):.1f}" cy="{py(r[key]):.1f}" r="3" fill="{colors[key]}"/>')
        for j, n in enumerate(SIZES): parts.append(f'<text x="{px(n):.1f}" y="350" text-anchor="middle" font-size="10">{n}</text>')
        parts.append(f'<text x="{ox+310}" y="380" text-anchor="middle" font-family="sans-serif" font-size="12">Número de puntos (eje x logarítmico)</text>')
        parts.append(f'<text x="{ox+12}" y="195" transform="rotate(-90 {ox+12} 195)" text-anchor="middle" font-family="sans-serif" font-size="12">Tiempo (ms, escala logarítmica)</text>')
        for i, metric in enumerate(("brute_ms", "tree_query_ms", "tree_total_ms")):
            y = 45 + i*16
            parts.append(f'<path d="M {ox+80} {y} h 20" stroke="{colors[f"{kind}_{metric}"]}" stroke-width="2"/><text x="{ox+105}" y="{y+4}" font-size="11">{labels[metric]}</text>')
    parts.append('</svg>')
    (out / "comparacion_rendimiento.svg").write_text('\n'.join(parts), encoding='utf-8')
    return rows


if __name__ == "__main__":
    run_benchmark()
