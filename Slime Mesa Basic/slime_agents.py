from mesa import Agent
import math
from collections import deque
import networkx as nx

def get_neighbours(idx):
    x, y = idx
    return [(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]

def step_direction(index: int, idx: tuple):
    directions = {
        0: (0, 0),
        1: (-1, -1), 2: (1, -1), 3: (-1, 1), 4: (1, 1),
        5: (-1, 0), 6: (1, 0), 7: (0, -1), 8: (0, 1)
    }
    dx, dy = directions.get(index, (0, 0))
    return idx[0] + dx, idx[1] + dy

class FoodAgent(Agent):
    def __init__(self, unique_id, model, pos, food_id):
        super().__init__(unique_id, model)
        self.pos = pos
        self.food_id = food_id

    def step(self):
        pass

class SlimeAgent(Agent):
    def __init__(self, unique_id, model, pos, pheromone=7, is_capital=False):
        super().__init__(unique_id, model)
        self.pos = pos
        self.pheromone = pheromone
        self.max_ph = 4
        self.direction = None
        self.is_capital = is_capital
        self.reached_food_id = None
        self.food_path = []
        self.step_food = None
        self.curr_target = None
        self.last_reached_food = None  

    def find_nearest_food(self, food_ids):
        return min(((i, math.dist(self.pos, self.model.food_positions[i])) for i in food_ids), key=lambda x: x[1], default=(None, float('inf')))

    def set_reached_food_path(self):
        target = self.model.current_target
        self.curr_target = target
        reached_ids = self.model.reached_food_ids

        if not reached_ids:
            self.food_path = [target]
        else:
            nearest, _ = self.find_nearest_food(reached_ids)
            if nearest is not None:
                try:
                    path = nx.shortest_path(self.model.food_graph, nearest, target)
                except:
                    path = [nearest, target]
                self.food_path = path
            else:
                self.food_path = [target]

        if self.food_path:
            step_id = self.food_path.pop(0)
            self.step_food = (step_id, self.model.food_positions[step_id])

    def reset_step_food(self):
        if self.reached_food_id == self.curr_target == self.model.current_target:
            return
        if self.step_food is None or not self.food_path:
            self.set_reached_food_path()
        else:
            step_pos = self.model.food_positions[self.step_food[0]]
            if math.dist(step_pos, self.pos) < 3 and self.food_path:
                step_id = self.food_path.pop(0)
                self.step_food = (step_id, self.model.food_positions[step_id])

    def sensory(self):
        if self.step_food is None:
            self.reset_step_food()
        food_pos = self.step_food[1]
        dx = food_pos[0] - self.pos[0]
        dy = food_pos[1] - self.pos[1]
        self.direction = {
            (-1, -1): 1, (1, -1): 2, (-1, 1): 3, (1, 1): 4,
            (-1, 0): 5, (1, 0): 6, (0, -1): 7, (0, 1): 8
        }.get((int(math.copysign(1, dx)) if dx else 0, int(math.copysign(1, dy)) if dy else 0), 0)

    def check_boundary(self, pos):
        x, y = pos
        return 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height

    def diffusion(self):
        lattice = self.model.grid
        decay = self.model.decay

        new_idx = step_direction(self.direction, self.pos)
        neighbours = get_neighbours(self.pos)

        if new_idx in neighbours:
            neighbours.remove(new_idx)
        neighbours = deque(neighbours)
        neighbours.appendleft(new_idx)

        diffusion_threshold = self.model.diffusion_threshold
        diffusion_decay_rate = self.model.diffusion_decay_rate
        distance_threshold = self.model.distance_for_diffusion_threshold
        moving_threshold = self.model.moving_threshold
        max_ph = self.model.max_ph
        max_ph_increase_step = self.model.max_ph_increase_step

        for neigh in neighbours:
            if not self.check_boundary(neigh):
                continue
            cellmates = lattice.get_cell_list_contents([neigh])
            if len(cellmates) == 0:
                if neigh == new_idx and self.pheromone > moving_threshold:
                    new_slime = SlimeAgent(self.model.next_id(), self.model, neigh, pheromone=self.pheromone, is_capital=self.is_capital)
                    self.model.grid.place_agent(new_slime, neigh)
                    self.model.schedule.add(new_slime)
                    self.pheromone *= (1 - diffusion_decay_rate * decay)
                    self.is_capital = False
                    break

                if self.pheromone > diffusion_threshold and \
                   self.find_nearest_food(self.model.reached_food_ids)[1] < distance_threshold:
                    new_slime = SlimeAgent(self.model.next_id(), self.model, neigh, pheromone=self.pheromone / diffusion_decay_rate)
                    self.model.grid.place_agent(new_slime, neigh)
                    self.model.schedule.add(new_slime)
                    self.pheromone *= (1 - (2 * diffusion_decay_rate * decay))
                    break

            else:
                cell = cellmates[0]
                if isinstance(cell, SlimeAgent):
                    if neigh == new_idx and self.pheromone > moving_threshold:
                        new_ph = cell.pheromone + self.pheromone / diffusion_decay_rate
                        cell.pheromone = min(new_ph, cell.max_ph)
                        self.pheromone /= diffusion_decay_rate
                    if cell.pheromone > self.pheromone and self.max_ph < max_ph:
                        self.max_ph += max_ph_increase_step
                        self.pheromone += (cell.pheromone / 10)
                elif isinstance(cell, FoodAgent):
                    # When slime reaches food, update reached food info
                    if self.reached_food_id != cell.food_id:
                        self.last_reached_food = self.reached_food_id  # store old reached food
                        self.reached_food_id = cell.food_id
                        if cell.food_id not in self.model.reached_food_ids:
                            self.model.reached_food_ids.add(cell.food_id)
                    self.pheromone = 7
                    self.max_ph = 7

    def step(self):
        self.sensory()
        self.diffusion()
