
# a_star.py
from queue import PriorityQueue

def a_star_pathfinding(start, goal, obstacles, grid_size=20):
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    cost_so_far = {start: 0}

    while not open_set.empty():
        _, current = open_set.get()

        if current == goal:
            path = []
            while current != start:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            neighbor = (current[0] + dx * grid_size, current[1] + dy * grid_size)
            if neighbor in obstacles:
                continue
            new_cost = cost_so_far[current] + 1
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(goal, neighbor)
                open_set.put((priority, neighbor))
                came_from[neighbor] = current

    return None
