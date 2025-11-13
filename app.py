# import streamlit as st
# import folium
# from streamlit_folium import folium_static
# import numpy as np
# from router_backend import optimize_route

# # ========================
# # FRONTEND
# # ========================

# def plot_route_map(locations, route):
#     center_lat = np.mean([locations[loc][0] for loc in locations])
#     center_lon = np.mean([locations[loc][1] for loc in locations])
#     m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

#     for idx, stop in enumerate(route):
#         folium.Marker(
#             locations[stop],
#             popup=f"{idx+1}. {stop}",
#             icon=folium.Icon(color="blue" if idx != 0 else "red", icon="info-sign")
#         ).add_to(m)

#     route_coords = [locations[stop] for stop in route]
#     folium.PolyLine(route_coords, weight=5, color="blue", opacity=0.7).add_to(m)
#     return m

# # --------------------
# # Streamlit UI
# # --------------------
# st.title("🗺️ Dynamic Stop Route Optimizer")

# if "stops" not in st.session_state:
#     st.session_state["stops"] = [""]

# # Dynamic stop fields
# for i in range(len(st.session_state.stops)):
#     stop_input = st.text_input(f"Stop {i+1}", value=st.session_state.stops[i])
#     st.session_state.stops[i] = stop_input

# if st.button("Add Another Stop"):
#     st.session_state.stops.append("")

# if st.button("Optimize Route"):
#     result = optimize_route(st.session_state.stops)
#     if "error" in result:
#         st.error(result["error"])
#     else:
#         st.subheader("Optimized Route:")
#         st.write(" → ".join(result["optimized_route"]))
#         st.write(f"Total Travel Time: {result['route_cost']:.1f} minutes")

#         route_map = plot_route_map(result["locations"], result["optimized_route"])
#         folium_static(route_map)
import streamlit as st
import folium
from streamlit_folium import folium_static
import numpy as np
from router_backend import optimize_route

# ========================
# FRONTEND
# ========================

def plot_route_map(locations, route):
    center_lat = np.mean([locations[loc][0] for loc in locations])
    center_lon = np.mean([locations[loc][1] for loc in locations])
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    for idx, stop in enumerate(route):
        folium.Marker(
            locations[stop],
            popup=f"{idx+1}. {stop}",
            icon=folium.Icon(color="blue" if idx != 0 else "red", icon="info-sign")
        ).add_to(m)

    route_coords = [locations[stop] for stop in route]
    folium.PolyLine(route_coords, weight=5, color="blue", opacity=0.7).add_to(m)
    return m

# --------------------
# Streamlit UI
# --------------------
st.set_page_config(layout="wide")
st.title("🗺️ Dynamic Stop Route Optimizer")

if "stops" not in st.session_state:
    st.session_state["stops"] = [""]

# Create two columns: Left for inputs, right for results
col1, col2 = st.columns([1, 2])

with col1:
    st.header("🚏 Enter Stops")
    for i in range(len(st.session_state.stops)):
        stop_input = st.text_input(f"Stop {i+1}", value=st.session_state.stops[i])
        st.session_state.stops[i] = stop_input

    if st.button("➕ Add Another Stop"):
        st.session_state.stops.append("")

    if st.button("📍 Optimize Route"):
        result = optimize_route(st.session_state.stops)
        st.session_state["result"] = result

with col2:
    st.header("🗺️ Optimized Route Map")
    if "result" in st.session_state:
        result = st.session_state["result"]
        if "error" in result:
            st.error(result["error"])
        else:
            st.subheader("Optimized Route:")
            st.write(" → ".join(result["optimized_route"]))
            st.write(f"Total Travel Time: {result['route_cost']:.1f} minutes")

            route_map = plot_route_map(result["locations"], result["optimized_route"])
            folium_static(route_map)
