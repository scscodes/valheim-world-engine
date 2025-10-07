BIOME_COLORS = {
	"Meadows": "#4CAF50",
	"BlackForest": "#1B5E20",
	"Swamp": "#5D4037",
	"Mountain": "#E0E0E0",
	"Plains": "#FDD835",
	"Mistlands": "#9E9E9E",
	"Ashlands": "#D32F2F",
	"DeepNorth": "#1E88E5",
	"Ocean": "#0277BD",
}

SHORELINE_CONFIG = {
	"detection_method": "heightmap_biome_intersection",
	"water_level": {"value": 30.0, "source": "Game constants", "tested": []},
	"shoreline_depth_threshold": {"value": -5.0, "source": "TBD validation", "tested": [-3.0, -5.0, -8.0]},
	"pattern_type": "diagonal_stripes",
	"pattern_angle": 45,
	"pattern_spacing": {"value": 4, "source": "TBD tests", "tested": [3, 4, 6]},
	"pattern_width": {"value": 2, "source": "TBD tests", "tested": [1, 2, 3]},
	"ocean_color": "#0277BD",
	"blend_ratio": {"value": 0.5, "source": "TBD tests", "tested": [0.4, 0.5, 0.6]},
}

NEIGHBORHOOD = "8-connected"
RENDER_RESOLUTION_PX = 2048
WORLD_SIZE_METERS = 21000
METERS_PER_PIXEL = WORLD_SIZE_METERS / RENDER_RESOLUTION_PX
