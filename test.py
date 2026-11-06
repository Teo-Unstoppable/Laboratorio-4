import math
import random
import unittest
from pathlib import Path

from quadtree import Point, QuadTree, Rectangle, build_quadtree


SEED = 2026
_rng = random.Random(SEED)
DATA = [Point(_rng.uniform(0, 10_000), _rng.uniform(0, 10_000)) for _ in range(10_000)]


class QuadTreeTests(unittest.TestCase):
    def setUp(self):
        self.points = [Point(0, 0), Point(3, 4), Point(5, 0), Point(-2, 0), Point(0, 0), Point(100, 100)]
        self.tree = QuadTree(Rectangle(-10, -10, 120, 120), capacity=1)
        for point in self.points:
            self.assertTrue(self.tree.insert(point))

    def test_radius_includes_boundary_and_duplicates(self):
        self.assertCountEqual(
            self.tree.range_search(Point(0, 0), 5),
            [Point(0, 0), Point(3, 4), Point(5, 0), Point(-2, 0), Point(0, 0)],
        )

    def test_nearest_and_k_nearest_match_brute_force(self):
        query = Point(2.1, 3.7)
        expected = sorted(
            self.points,
            key=lambda point: (math.dist((point.x, point.y), (query.x, query.y)), point.x, point.y),
        )
        self.assertEqual(self.tree.k_nearest(query, 4), expected[:4])
        self.assertEqual(self.tree.nearest(query), expected[0])

    def test_rectangle_query_and_outside_insert(self):
        self.assertFalse(self.tree.insert(Point(500, 500)))
        self.assertCountEqual(
            self.tree.query(Rectangle(-1, -1, 7, 6)),
            [Point(0, 0), Point(3, 4), Point(5, 0), Point(0, 0)],
        )

    def test_edge_cases(self):
        self.assertEqual(self.tree.k_nearest(Point(0, 0), 0), [])
        self.assertEqual(len(self.tree.k_nearest(Point(0, 0), 20)), len(self.points))
        with self.assertRaises(ValueError):
            self.tree.k_nearest(Point(0, 0), -1)
        with self.assertRaises(ValueError):
            self.tree.range_search(Point(0, 0), -1)
        with self.assertRaises(ValueError):
            build_quadtree([])

    def test_coincident_points_and_depth_limit(self):
        points = [Point(2, 2) for _ in range(20)]
        tree = build_quadtree(points, capacity=1, max_depth=4)
        self.assertEqual(tree.range_search(Point(2, 2), 0), points)
        self.assertEqual(tree.k_nearest(Point(2, 2), 7), points[:7])

    def test_random_queries_match_brute_force(self):
        rng = random.Random(SEED + 1)
        tree = build_quadtree(DATA)
        for _ in range(30):
            query = Point(rng.uniform(0, 10_000), rng.uniform(0, 10_000))
            radius = rng.uniform(50, 1000)
            expected = [point for point in DATA if math.dist((point.x, point.y), (query.x, query.y)) <= radius]
            self.assertCountEqual(tree.range_search(query, radius), expected)
            expected_k = sorted(
                DATA,
                key=lambda point: (math.dist((point.x, point.y), (query.x, query.y)), point.x, point.y),
            )[:7]
            self.assertEqual(tree.k_nearest(query, 7), expected_k)


def create_visualizations(output_dir="graficas"):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    tree = build_quadtree(DATA)
    query, radius = Point(5000, 5000), 500
    neighbors = tree.range_search(query, radius)

    def svg(name, title, location, selected, radius_value=None):
        size, pad = 800, 45

        def xy(point):
            return pad + point.x / 10_000 * (size - 2 * pad), size - pad - point.y / 10_000 * (size - 2 * pad)

        qx, qy = xy(location)
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
            '<rect width="100%" height="100%" fill="white"/>',
            f'<text x="400" y="25" text-anchor="middle" font-family="sans-serif" font-size="18">{title}</text>',
            f'<rect x="{pad}" y="{pad}" width="{size - 2 * pad}" height="{size - 2 * pad}" fill="none" stroke="#777"/>',
        ]
        parts.extend(
            f'<circle cx="{xy(point)[0]:.2f}" cy="{xy(point)[1]:.2f}" r="2" fill="#b8c2cc"/>'
            for point in DATA
        )
        if radius_value is not None:
            circle_radius = radius_value / 10_000 * (size - 2 * pad)
            parts.append(
                f'<circle cx="{qx:.2f}" cy="{qy:.2f}" r="{circle_radius:.2f}" fill="none" stroke="#1f77b4" stroke-width="2"/>'
            )
        for index, point in enumerate(selected, 1):
            px, py = xy(point)
            parts.append(
                f'<line x1="{qx:.2f}" y1="{qy:.2f}" x2="{px:.2f}" y2="{py:.2f}" stroke="#e4572e" opacity=".6"/>'
            )
            parts.append(
                f'<circle cx="{px:.2f}" cy="{py:.2f}" r="5" fill="#e4572e"/><text x="{px + 6:.2f}" y="{py - 5:.2f}" font-size="11">{index}</text>'
            )
        parts.extend(
            [
                f'<path d="M {qx:.2f} {qy - 9:.2f} L {qx + 3:.2f} {qy - 3:.2f} L {qx + 10:.2f} {qy - 3:.2f} L {qx + 4:.2f} {qy + 1:.2f} L {qx + 6:.2f} {qy + 8:.2f} L {qx:.2f} {qy + 4:.2f} L {qx - 6:.2f} {qy + 8:.2f} L {qx - 4:.2f} {qy + 1:.2f} L {qx - 10:.2f} {qy - 3:.2f} L {qx - 3:.2f} {qy - 3:.2f} Z" fill="#222"/>',
                '<text x="400" y="790" text-anchor="middle" font-family="sans-serif">Este (m)</text>',
                '<text x="15" y="400" transform="rotate(-90 15 400)" text-anchor="middle" font-family="sans-serif">Norte (m)</text>',
                "</svg>",
            ]
        )
        (output / name).write_text("\n".join(parts), encoding="utf-8")

    svg("busqueda_radio.svg", "Búsqueda por radio de 500 m — 10.000 puntos", query, neighbors, radius)
    nearest_query = Point(5200, 4800)
    svg("vecinos_cercanos.svg", "Cinco puntos de entrega más cercanos", nearest_query, tree.k_nearest(nearest_query, 5))
    return output


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__)))
    if result.wasSuccessful():
        create_visualizations()
    raise SystemExit(not result.wasSuccessful())
