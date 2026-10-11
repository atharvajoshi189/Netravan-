"""
Official GIS Boundary Coordinates, Camera Trap Grid Stations, and Surrounding Villages
for Pench Tiger Reserve (Madhya Pradesh & Maharashtra border).
"""

# 1. Pench Tiger Reserve Core Zone Boundary Polygon (approx 411 sq km core)
PENCH_CORE_BOUNDARY = [
    (21.6500, 79.2200),
    (21.6700, 79.2050),
    (21.7200, 79.2150),
    (21.7600, 79.2500),
    (21.7850, 79.3000),
    (21.7700, 79.3450),
    (21.7300, 79.3300),
    (21.6900, 79.3100),
    (21.6600, 79.2800),
    (21.6500, 79.2200)
]

# 2. Pench Tiger Reserve Buffer Zone Boundary Polygon (outer monitoring envelope)
PENCH_BUFFER_BOUNDARY = [
    (21.6100, 79.1800),
    (21.6600, 79.1600),
    (21.7400, 79.1800),
    (21.8200, 79.2200),
    (21.8700, 79.3100),
    (21.8600, 79.4300),
    (21.7800, 79.4500),
    (21.6800, 79.3900),
    (21.6200, 79.3500),
    (21.6100, 79.1800)
]

# 3. Surrounding Human-Wildlife Conflict Vulnerable Villages
PENCH_VILLAGES = [
    {
        "village_id": "VIL_01",
        "name": "Turia Village",
        "lat": 21.6750,
        "lon": 79.2450,
        "zone": "village_fringe",
        "risk_level": "HIGH",
        "description": "Border village near Turia Gate; high cattle grazing and tiger movement."
    },
    {
        "village_id": "VIL_02",
        "name": "Khawasa Village",
        "lat": 21.7950,
        "lon": 79.3750,
        "zone": "village_fringe",
        "risk_level": "HIGH",
        "description": "Highway-adjacent market village on NH-44 corridor; high sub-adult dispersal."
    },
    {
        "village_id": "VIL_03",
        "name": "Awarghani Village",
        "lat": 21.6680,
        "lon": 79.2620,
        "zone": "village_fringe",
        "risk_level": "MEDIUM",
        "description": "Agricultural buffer village frequently visited by resident tigress Collarwali/Patdev."
    },
    {
        "village_id": "VIL_04",
        "name": "Kohka Village",
        "lat": 21.6900,
        "lon": 79.2300,
        "zone": "village_fringe",
        "risk_level": "MEDIUM",
        "description": "Western buffer village near waterbody fringes."
    },
    {
        "village_id": "VIL_05",
        "name": "Karmajhiri Village",
        "lat": 21.7480,
        "lon": 79.2750,
        "zone": "village_fringe",
        "risk_level": "MEDIUM",
        "description": "Central entry gate settlement adjacent to core forest."
    },
    {
        "village_id": "VIL_06",
        "name": "Rukhad Village",
        "lat": 21.8550,
        "lon": 79.4450,
        "zone": "village_fringe",
        "risk_level": "CRITICAL",
        "description": "Northern corridor connecting Pench to Kanha; dispersing male tiger corridor."
    },
    {
        "village_id": "VIL_07",
        "name": "Dhawalpur Village",
        "lat": 21.7900,
        "lon": 79.4100,
        "zone": "village_fringe",
        "risk_level": "HIGH",
        "description": "Eastern buffer settlement prone to livestock depredation."
    },
    {
        "village_id": "VIL_08",
        "name": "Jamtara Village",
        "lat": 21.7650,
        "lon": 79.3300,
        "zone": "village_fringe",
        "risk_level": "MEDIUM",
        "description": "Northern buffer zone near Chhindwara border."
    }
]

# 4. Comprehensive Camera Trap Grid Stations (Core, Buffer, and Village Fringe)
PENCH_CAMERA_STATIONS = [
    # Turia Core Range (Collarwali / Patdev resident territory)
    {"station_id": "PTR_STN_01", "grid_id": "GRID_A1", "range": "Turia", "zone": "core", "lat": 21.6845, "lon": 79.2561, "elevation_m": 410.0, "camera_model": "Cuddeback_X6"},
    {"station_id": "PTR_STN_02", "grid_id": "GRID_A2", "range": "Turia", "zone": "core", "lat": 21.6950, "lon": 79.2780, "elevation_m": 425.0, "camera_model": "Cuddeback_X6"},
    {"station_id": "PTR_STN_03", "grid_id": "GRID_A3", "range": "Turia", "zone": "core", "lat": 21.7120, "lon": 79.2610, "elevation_m": 395.0, "camera_model": "Reconyx_HyperFire"},
    
    # Karmajhiri Core Range (Bajirao / Karmajhiri resident territory)
    {"station_id": "PTR_STN_04", "grid_id": "GRID_B1", "range": "Karmajhiri", "zone": "core", "lat": 21.7340, "lon": 79.2890, "elevation_m": 405.0, "camera_model": "Reconyx_HyperFire"},
    {"station_id": "PTR_STN_05", "grid_id": "GRID_B2", "range": "Karmajhiri", "zone": "core", "lat": 21.7450, "lon": 79.3080, "elevation_m": 415.0, "camera_model": "Cuddeback_X6"},
    {"station_id": "PTR_STN_06", "grid_id": "GRID_B3", "range": "Karmajhiri", "zone": "core", "lat": 21.7280, "lon": 79.3250, "elevation_m": 420.0, "camera_model": "Cuddeback_X6"},
    
    # Jamtara / Chhindwara Core Range (L-Mark T-74 territory)
    {"station_id": "PTR_STN_07", "grid_id": "GRID_C1", "range": "Jamtara", "zone": "core", "lat": 21.7550, "lon": 79.3150, "elevation_m": 435.0, "camera_model": "Reconyx_HyperFire"},
    {"station_id": "PTR_STN_08", "grid_id": "GRID_C2", "range": "Jamtara", "zone": "core", "lat": 21.7680, "lon": 79.3280, "elevation_m": 440.0, "camera_model": "Reconyx_HyperFire"},
    {"station_id": "PTR_STN_09", "grid_id": "GRID_C3", "range": "Jamtara", "zone": "core", "lat": 21.7500, "lon": 79.3400, "elevation_m": 430.0, "camera_model": "Cuddeback_X6"},

    # Khawasa / Gumtara Buffer Range (Swastik territory & sub-adult dispersal)
    {"station_id": "PTR_STN_10", "grid_id": "GRID_D1", "range": "Khawasa", "zone": "buffer", "lat": 21.7820, "lon": 79.3650, "elevation_m": 450.0, "camera_model": "Browning_StrikeForce"},
    {"station_id": "PTR_STN_11", "grid_id": "GRID_D2", "range": "Khawasa", "zone": "buffer", "lat": 21.7750, "lon": 79.3800, "elevation_m": 455.0, "camera_model": "Browning_StrikeForce"},
    {"station_id": "PTR_STN_12", "grid_id": "GRID_D3", "range": "Gumtara", "zone": "buffer", "lat": 21.7600, "lon": 79.3600, "elevation_m": 445.0, "camera_model": "Browning_StrikeForce"},

    # Village Fringe Border Stations (High Alert Human-Wildlife Interface)
    {"station_id": "PTR_STN_13", "grid_id": "GRID_E1", "range": "Turia_Fringe", "zone": "village_fringe", "lat": 21.6780, "lon": 79.2480, "elevation_m": 412.0, "camera_model": "Browning_StrikeForce"},
    {"station_id": "PTR_STN_14", "grid_id": "GRID_E2", "range": "Awarghani_Fringe", "zone": "village_fringe", "lat": 21.6710, "lon": 79.2590, "elevation_m": 418.0, "camera_model": "Browning_StrikeForce"},
    {"station_id": "PTR_STN_15", "grid_id": "GRID_E3", "range": "Khawasa_Fringe", "zone": "village_fringe", "lat": 21.7910, "lon": 79.3710, "elevation_m": 452.0, "camera_model": "Browning_StrikeForce"},
    {"station_id": "PTR_STN_16", "grid_id": "GRID_E4", "range": "Dhawalpur_Fringe", "zone": "village_fringe", "lat": 21.7880, "lon": 79.4050, "elevation_m": 458.0, "camera_model": "Browning_StrikeForce"},
    {"station_id": "PTR_STN_17", "grid_id": "GRID_E5", "range": "Rukhad_Corridor", "zone": "village_fringe", "lat": 21.8480, "lon": 79.4380, "elevation_m": 470.0, "camera_model": "Browning_StrikeForce"},
    {"station_id": "PTR_STN_18", "grid_id": "GRID_E6", "range": "Kohka_Fringe", "zone": "village_fringe", "lat": 21.6920, "lon": 79.2340, "elevation_m": 402.0, "camera_model": "Browning_StrikeForce"},
]
