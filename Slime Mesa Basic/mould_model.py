from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
import networkx as nx
import random
from slime_agents import SlimeAgent, FoodAgent
from geo_utils import load_stations
import numpy as np
import matplotlib.pyplot as plt
import os

class MouldModel(Model):
    def __init__(
        self, 
        grid_width=200, 
        grid_height=200, 
        decay=0.01, 
        geojson_path="Geojson Stops/rome_rail_subway_stops.geojson", 
        initial_slime=5, 
        start_loc=None,
        diffusion_threshold=3.5,
        diffusion_decay_rate=1.26,
        distance_for_diffusion_threshold=55,
        moving_threshold=1,
        max_ph=5.5,
        max_ph_increase_step=0.2
    ):
        super().__init__()
        self.grid = MultiGrid(grid_width, grid_height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.decay = decay
        self.step_count = 0

        self.diffusion_threshold = diffusion_threshold
        self.diffusion_decay_rate = diffusion_decay_rate
        self.distance_for_diffusion_threshold = distance_for_diffusion_threshold
        self.moving_threshold = moving_threshold
        self.max_ph = max_ph
        self.max_ph_increase_step = max_ph_increase_step

        self.food_graph = nx.Graph()
        self.spread_graph = nx.Graph()  # Graph of reached/connected food nodes by slime
        self.food_positions = {}
        self.reached_food_ids = set()

        # Load station locations with geographic coordinates
        stations = load_stations(geojson_path)
        geo_nodes = np.array(stations['nodes'].tolist())  # Nx2 array of (lon, lat)
        start_loc = (95, 85)  # manual slime start location; (x,y)

        # Normalize geo coordinates to grid coordinates
        min_x, min_y = geo_nodes.min(axis=0)
        max_x, max_y = geo_nodes.max(axis=0)

        def normalize(coord):
            x_norm = int((coord[0] - min_x) / (max_x - min_x) * (grid_width - 1))
            y_norm = int((coord[1] - min_y) / (max_y - min_y) * (grid_height - 1))
            x_norm = max(0, min(grid_width - 1, x_norm))
            y_norm = max(0, min(grid_height - 1, y_norm))
            return (x_norm, y_norm)

        normalized_nodes = [normalize(coord) for coord in geo_nodes]

        # Place food agents on grid and add nodes to food_graph and spread_graph
        for i, pos in enumerate(normalized_nodes):
            food_agent = FoodAgent(self.next_id(), self, pos, food_id=i)
            self.grid.place_agent(food_agent, pos)
            self.schedule.add(food_agent)
            self.food_positions[i] = pos
            self.food_graph.add_node(i)
            self.spread_graph.add_node(i)

        # Fully connect the original food graph (static)
        for i in range(len(normalized_nodes)):
            for j in range(i + 1, len(normalized_nodes)):
                self.food_graph.add_edge(i, j)

        self.current_target = 0

        if start_loc is None:
            cx, cy = grid_width // 2, grid_height // 2
        else:
            cx, cy = start_loc
        for _ in range(initial_slime):
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            pos = (min(max(cx + dx, 0), grid_width - 1), min(max(cy + dy, 0), grid_height - 1))
            slime_agent = SlimeAgent(self.next_id(), self, pos, pheromone=7, is_capital=True)
            self.grid.place_agent(slime_agent, pos)
            self.schedule.add(slime_agent)

    def add_spread_edge(self, node_a, node_b):
        """Add an edge between food nodes in the spread graph if not present."""
        if node_a != node_b and not self.spread_graph.has_edge(node_a, node_b):
            self.spread_graph.add_edge(node_a, node_b)

    def step(self):
        self.schedule.step()
        self.step_count += 1

        # Update spread_graph edges based on slime agents who connected food nodes
        # Find slime agents that just reached a new food node
        for agent in self.schedule.agents:
            if isinstance(agent, SlimeAgent):
                if agent.reached_food_id is not None:
                    # Connect newly reached food with previous reached food
                    last_reached = getattr(agent, 'last_reached_food', None)
                    if last_reached is not None and last_reached != agent.reached_food_id:
                        self.add_spread_edge(last_reached, agent.reached_food_id)
                    # Update last reached food for next iteration
                    agent.last_reached_food = agent.reached_food_id

