from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import numpy as np
from itertools import combinations
import math
import time

app = FastAPI()

# Allow requests from your frontend (Expo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to your frontend URL later
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# ORS CONFIG
# ------------------------
ORS_API_KEY = "5b3ce3597851110001cf6248c6ef8a7c027f4e2a8bda7338ceea67aa"

# ------------------------
# Request Model
# ------------------------
class RouteRequest(BaseModel):
    stops: list[str]

# ------------------------
# Helper Functions
# ------------------------

def geocode_place(place_name):
    """Convert place name to (lat, lon) using ORS."""
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
        coords = features[0]["geometry"]["coordinates"]  # lon, lat
        label = features[0]["properties"]["label"]
        return (coords[1], coords[0]), label
    except:
        return None


def get_travel_time_minutes(coord_a, coord_b):
    """Get real driving time between two coordinates using ORS Directions API."""
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {"coordinates": [[coord_a[1], coord_a[0]], [coord_b[1], coord_b[0]]], "instructions": False}
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        segs = data.get("features", [{}])[0].get("properties", {}).get("segments", [])
        if segs and "duration" in segs[0]:
            return segs[0]["duration"] / 60.0  # seconds → minutes
    except:
        pass
    # fallback if API fails
    return haversine_fallback_minutes(coord_a, coord_b)


def haversine_fallback_minutes(coord1, coord2, avg_speed_kmph=60.0):
    """Estimate driving time from straight-line distance if ORS fails."""
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    R = 6371
    distance = R * c
    return (distance / avg_speed_kmph) * 60.0


def build_graph(locations):
    """Create weighted graph (minutes between all nodes)."""
    nodes = list(locations.keys())
    G = {}
    for n1, n2 in combinations(nodes, 2):
        time_min = get_travel_time_minutes(locations[n1], locations[n2])
        G.setdefault(n1, {})[n2] = time_min
        G.setdefault(n2, {})[n1] = time_min
        time.sleep(0.1)  # prevent rate-limit
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
    return sum(graph[route[i]][route[i+1]] for i in range(len(route)-1))


def two_opt(route, graph):
    best = route
    improved = True
    while improved:
        improved = False
        for i in range(1, len(route)-2):
            for j in range(i+1, len(route)):
                if j - i == 1:
                    continue
                new_route = best[:]
                new_route[i:j] = best[j-1:i-1:-1]
                if route_cost(new_route, graph) < route_cost(best, graph):
                    best = new_route
                    improved = True
        route = best
    return best

# ------------------------
# API ENDPOINTS
# ------------------------

@app.post("/optimize_route")
def optimize_route(req: RouteRequest):
    stops = req.stops
    if not stops:
        return {"error": "No stops provided"}

    # 1️⃣ Geocode all stops
    locations = {}
    labels = {}
    for stop in stops:
        if stop.strip():
            geo = geocode_place(stop)
            if geo:
                coord, label = geo
                locations[label] = coord
                labels[stop] = label
            else:
                return {"error": f"Could not geocode stop: {stop}"}

    if len(locations) < 2:
        return {"error": "Please add at least two valid stops."}

    # 2️⃣ Build travel-time graph
    graph = build_graph(locations)

    # 3️⃣ Optimize route
    start = list(locations.keys())[0]
    nn_route = nearest_neighbour(graph, start)
    optimized_route = two_opt(nn_route, graph)
    total_time = route_cost(optimized_route, graph)

    return {
        "optimized_route": optimized_route,
        "coordinates": [locations[r] for r in optimized_route],
        "route_cost": round(total_time, 2)  # in minutes
    }


@app.get("/")
def home():
    return {"message": "Backend is running!"}
