from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization import Slider
from mould_model import MouldModel

def agent_portrayal(agent):
    if agent is None:
        return

    portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 1, "h": 1}

    if agent.__class__.__name__ == "FoodAgent":
        portrayal["Color"] = "green"
        portrayal["Layer"] = 1
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8
    elif agent.__class__.__name__ == "SlimeAgent":
        pheromone = agent.pheromone
        alpha = min(1, max(0.2, pheromone / 7))
        portrayal["Color"] = f"rgba(255,165,0, {alpha})" 
        portrayal["Layer"] = 0
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8
    return portrayal

grid = CanvasGrid(agent_portrayal, 200, 200, 1000, 1000)

server = ModularServer(
    MouldModel,
    [grid],
    "Slime Mould Simulation",
    {
        "initial_slime": Slider("Initial Slime Agents", 10, 1, 50, 1),
        "decay": Slider("Decay Rate", 0.2, 0.01, 1.0, 0.01),
        "geojson_path": "Geojson Stops/rome_rail_subway_stops.geojson",
        "diffusion_threshold": Slider("Diffusion Threshold", 3.5, 0.1, 10.0, 0.1),
        "diffusion_decay_rate": Slider("Diffusion Decay Rate", 1.26, 0.1, 5.0, 0.05),
        "distance_for_diffusion_threshold": Slider("Distance for Diffusion Threshold", 55, 1, 100, 1),
        "moving_threshold": Slider("Moving Threshold", 1, 0.1, 10.0, 0.1),
        "max_ph": Slider("Max PH", 5.5, 1.0, 10.0, 0.1),
        "max_ph_increase_step": Slider("Max PH Increase Step", 0.2, 0.01, 1.0, 0.01),
    }
)
