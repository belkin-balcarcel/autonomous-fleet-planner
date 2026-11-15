import heapq
import math
from typing import List, Tuple, Set, Optional

GridPoint = Tuple[int, int]


def heuristic(a: GridPoint, b: GridPoint) -> float:
    """Euclidean distance heuristic between two grid coordinates."""
    return math.hypot(b[0] - a[0], b[1] - a[1])


def astar_route(
    start: GridPoint,
    goal: GridPoint,
    no_fly_zones: Set[GridPoint],
    grid_size: int = 20
) -> Optional[List[GridPoint]]:
    """
    Computes the shortest collision-free path on a 2D airspace grid using A*.
    Uses a min-heap priority queue and 8-directional movement.
    """
    if start in no_fly_zones or goal in no_fly_zones:
        return None

    # Min-heap storing tuples of (f_score, g_score, current_node)
    open_heap: List[Tuple[float, float, GridPoint]] = []
    heapq.heappush(open_heap, (heuristic(start, goal), 0.0, start))

    came_from: dict[GridPoint, GridPoint] = {}
    g_score: dict[GridPoint, float] = {start: 0.0}
    closed_set: Set[GridPoint] = set()

    # 8-directional flight movement (cardinal + diagonal)
    directions = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)
    ]

    while open_heap:
        _, current_g, current = heapq.heappop(open_heap)

        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        if current in closed_set:
            continue
        closed_set.add(current)

        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)

            # Enforce airspace boundaries and restricted no-fly zones
            if not (0 <= neighbor[0] < grid_size and 0 <= neighbor[1] < grid_size):
                continue
            if neighbor in no_fly_zones or neighbor in closed_set:
                continue

            step_cost = math.hypot(dx, dy)
            tentative_g = current_g + step_cost

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f_score, tentative_g, neighbor))

    return None


if __name__ == "__main__":
    # Quick test: route from (0, 0) to (6, 6) around a restricted wall at x=3
    obstacles = {(3, 1), (3, 2), (3, 3), (3, 4), (3, 5)}
    route = astar_route((0, 0), (6, 6), obstacles, grid_size=10)
    print("Optimal collision-free waypoints:", route)
