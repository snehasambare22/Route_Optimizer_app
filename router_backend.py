from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import numpy as np
from itertools import combinations

app = FastAPI()

# Allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ORS API key
ORS_API_KEY = "5b3ce3597851110001cf6248c6ef8a7c027f4e2a8bda7338ceea67aa"

# Request model
class RouteRequest(BaseModel):
    stops: list[str]

# ------------------------
# Helper functions
# ------------------------

def geocode_place(place_name):
    url = "https://api.openrouteservice.org/geocode/autocomplete"
    params = {
        "api_key": ORS_API_KEY,
        "text": place_name,
        "boundary.country": "IND",
        "size": 1
    }
    try:
        resp = requests.get(url, params=params, timeout=5).json()
        features = resp.get("features", [])
        if not features:
            return None
        coords = features[0]["geometry"]["coordinates"]
        label = features[0]["properties"]["label"]
        return (coords[1], coords[0]), label  # lat, lon
    except:
        return None

def haversine(coord1, coord2):
    lat1, lon1 = np.radians(coord1)
    lat2, lon2 = np.radians(coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2*np.arcsin(np.sqrt(a))
    R = 6371  # km
    return R * c

def build_graph(locations):
    nodes = list(locations.keys())
    G = {}
    for n1, n2 in combinations(nodes, 2):
        distance = haversine(locations[n1], locations[n2])
        travel_time = distance * np.random.uniform(2, 4)  # simulate traffic
        G.setdefault(n1, {})[n2] = travel_time
        G.setdefault(n2, {})[n1] = travel_time
    return G

def nearest_neighbour(graph, start):
    route = [start]
    nodes = list(graph.keys())
    nodes.remove(start)
    while nodes:
        last = route[-1]
        next_node = min(nodes, key=lambda x: graph[last][x])
        route.append(next_node)
        nodes.remove(next_node)
    return route

def route_cost(route, graph):
    cost = 0
    for i in range(len(route)-1):
        cost += graph[route[i]][route[i+1]]
    return cost

def two_opt(route, graph):
    best = route
    improved = True
    while improved:
        improved = False
        for i in range(1, len(route)-2):
            for j in range(i+1, len(route)):
                if j-i == 1: continue
                new_route = best[:]
                new_route[i:j] = best[j-1:i-1:-1]
                if route_cost(new_route, graph) < route_cost(best, graph):
                    best = new_route
                    improved = True
        route = best
    return best

# ------------------------
# API Endpoints
# ------------------------

@app.post("/optimize_route")
def optimize_route(req: RouteRequest):
    stops = req.stops
    if not stops:
        return {"error": "No stops provided"}

    locations = {}
    labels = {}
    for stop in stops:
        if stop.strip():
            geocode = geocode_place(stop)
            if geocode:
                coord, label = geocode
                locations[label] = coord
                labels[stop] = label
            else:
                return {"error": f"Could not geocode stop: {stop}"}

    if len(locations) < 2:
        return {"error": "Please add at least two valid stops."}

    graph = build_graph(locations)
    start = list(locations.keys())[0]
    nn_route = nearest_neighbour(graph, start)
    optimized_route = two_opt(nn_route, graph)
    cost = route_cost(optimized_route, graph)

    return {
        "locations": locations,
        "optimized_route": optimized_route,
        "route_cost": round(cost, 2)
    }

@app.get("/")
def home():
    return {"message": "Backend is running"}
