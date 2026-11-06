from __future__ import annotations

import heapq
import itertools
import math
from typing import Iterable, Sequence


class Point:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("Las coordenadas deben ser números finitos")
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))


class Rectangle:
    __slots__ = ("x", "y", "width", "height")

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        if not all(math.isfinite(v) for v in (self.x, self.y, self.width, self.height)):
            raise ValueError("Los límites del rectángulo deben ser finitos")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("El ancho y el alto deben ser positivos")

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def contains(self, point: Point | Sequence[float]) -> bool:
        point = as_point(point)
        return self.x <= point.x < self.right and self.y <= point.y < self.bottom

    def intersects(self, other: Rectangle) -> bool:
        return not (
            other.x >= self.right
            or other.right <= self.x
            or other.y >= self.bottom
            or other.bottom <= self.y
        )


def as_point(value: Point | Sequence[float]) -> Point:
    if isinstance(value, Point):
        return value
    if len(value) != 2:
        raise ValueError("Cada punto debe tener exactamente dos coordenadas")
    return Point(value[0], value[1])


class QuadTree:
    def __init__(
        self,
        boundary: Rectangle,
        capacity: int = 4,
        max_depth: int = 32,
        _depth: int = 0,
    ) -> None:
        if not isinstance(boundary, Rectangle):
            raise TypeError("boundary debe ser un Rectangle")
        if capacity < 1 or max_depth < 1:
            raise ValueError("capacity y max_depth deben ser positivos")
        self.boundary = boundary
        self.capacity = capacity
        self.max_depth = max_depth
        self._depth = _depth
        self.points: list[Point] = []
        self.divided = False
        self.northwest: QuadTree | None = None
        self.northeast: QuadTree | None = None
        self.southwest: QuadTree | None = None
        self.southeast: QuadTree | None = None
        self.size = 0

    def subdivide(self) -> None:
        if self.divided:
            return
        x, y = self.boundary.x, self.boundary.y
        w, h = self.boundary.width / 2, self.boundary.height / 2
        if w == 0 or h == 0:
            return
        next_depth = self._depth + 1
        args = (self.capacity, self.max_depth, next_depth)
        self.northwest = QuadTree(Rectangle(x, y, w, h), *args)
        self.northeast = QuadTree(Rectangle(x + w, y, w, h), *args)
        self.southwest = QuadTree(Rectangle(x, y + h, w, h), *args)
        self.southeast = QuadTree(Rectangle(x + w, y + h, w, h), *args)
        self.divided = True

    def insert(self, point: Point | Sequence[float]) -> bool:
        point = as_point(point)
        if not self.boundary.contains(point):
            return False
        if not self.divided and (
            len(self.points) < self.capacity
            or self._depth >= self.max_depth
            or self.boundary.width / 2 == 0
            or self.boundary.height / 2 == 0
        ):
            self.points.append(point)
            self.size += 1
            return True
        if not self.divided:
            self.subdivide()
        if not self.divided:
            self.points.append(point)
            self.size += 1
            return True
        for child in self._children():
            if child.insert(point):
                self.size += 1
                return True
        self.points.append(point)
        self.size += 1
        return True

    def query(self, range_rect: Rectangle, found: list[Point] | None = None) -> list[Point]:
        if not isinstance(range_rect, Rectangle):
            raise TypeError("range_rect debe ser un Rectangle")
        if found is None:
            found = []
        if not self.boundary.intersects(range_rect):
            return found
        found.extend(point for point in self.points if range_rect.contains(point))
        if self.divided:
            for child in self._children():
                child.query(range_rect, found)
        return found

    def range_search(self, center: Point | Sequence[float], radius: float) -> list[Point]:
        center = as_point(center)
        radius = float(radius)
        if not math.isfinite(radius) or radius < 0:
            raise ValueError("El radio debe ser finito y no negativo")
        min_x, min_y = center.x - radius, center.y - radius
        max_x = math.nextafter(center.x + radius, math.inf)
        max_y = math.nextafter(center.y + radius, math.inf)
        width, height = max_x - min_x, max_y - min_y
        while min_x + width < max_x:
            width = math.nextafter(width, math.inf)
        while min_y + height < max_y:
            height = math.nextafter(height, math.inf)
        candidates = self.query(Rectangle(min_x, min_y, width, height))
        radius_squared = radius * radius
        return [
            point
            for point in candidates
            if (point.x - center.x) ** 2 + (point.y - center.y) ** 2 <= radius_squared
        ]

    def k_nearest(self, location: Point | Sequence[float], k: int = 1) -> list[Point]:
        location = as_point(location)
        if k < 0:
            raise ValueError("k debe ser no negativo")
        if k == 0 or self.size == 0:
            return []
        serial = itertools.count()
        nodes: list[tuple[float, int, QuadTree]] = [
            (_rectangle_distance_squared(self.boundary, location), next(serial), self)
        ]
        best: list[tuple[float, float, float, int, Point]] = []
        while nodes:
            lower_bound, _, node = heapq.heappop(nodes)
            if len(best) == k and lower_bound > -best[0][0]:
                break
            for point in node.points:
                distance_squared = (point.x - location.x) ** 2 + (point.y - location.y) ** 2
                candidate = (-distance_squared, -point.x, -point.y, next(serial), point)
                if len(best) < k:
                    heapq.heappush(best, candidate)
                elif candidate[:3] > best[0][:3]:
                    heapq.heapreplace(best, candidate)
            if node.divided:
                for child in node._children():
                    child_bound = _rectangle_distance_squared(child.boundary, location)
                    if len(best) < k or child_bound <= -best[0][0]:
                        heapq.heappush(nodes, (child_bound, next(serial), child))
        return [item[4] for item in sorted(best, key=lambda item: (-item[0], -item[1], -item[2]))]

    def nearest(self, location: Point | Sequence[float]) -> Point:
        if self.size == 0:
            raise ValueError("No hay puntos en el árbol")
        return self.k_nearest(location, 1)[0]

    def _children(self) -> tuple[QuadTree, QuadTree, QuadTree, QuadTree]:
        if not self.divided:
            return ()
        return self.northwest, self.northeast, self.southwest, self.southeast


def build_quadtree(
    points: Iterable[Point | Sequence[float]], capacity: int = 4, max_depth: int = 32
) -> QuadTree:
    data = [as_point(point) for point in points]
    if not data:
        raise ValueError("Se requiere al menos un punto para calcular los límites")
    min_x = min(point.x for point in data)
    min_y = min(point.y for point in data)
    max_x = max(point.x for point in data)
    max_y = max(point.y for point in data)
    span = max(max_x - min_x, max_y - min_y, 1.0)
    padding = max(span * 1e-9, 1e-9)
    boundary = Rectangle(
        min_x - padding,
        min_y - padding,
        max_x - min_x + 2 * padding,
        max_y - min_y + 2 * padding,
    )
    tree = QuadTree(boundary, capacity=capacity, max_depth=max_depth)
    for point in data:
        if not tree.insert(point):
            raise RuntimeError("No se pudo insertar un punto dentro de los límites calculados")
    return tree


def _rectangle_distance_squared(rectangle: Rectangle, point: Point) -> float:
    dx = max(rectangle.x - point.x, 0.0, point.x - rectangle.right)
    dy = max(rectangle.y - point.y, 0.0, point.y - rectangle.bottom)
    return dx * dx + dy * dy
