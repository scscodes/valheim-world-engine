"""
Biome Analysis Configuration
=============================

Centralized constants and configuration for all biome analysis notebooks.
This ensures consistency across all analysis tools.

Source: Valheim decompiled code (WorldGenerator.cs) and renderer.js
"""

# ============================================================================
# BIOME DEFINITIONS
# ============================================================================

# Biome enum values (powers of 2, as per Valheim)
BIOME_MAP = {
    1: "Meadows",
    2: "BlackForest",
    4: "Swamp",
    8: "Mountain",
    16: "Plains",
    32: "Ocean",
    64: "Mistlands",
    256: "DeepNorth",
    512: "Ashlands"
}

# Reverse lookup: name -> ID
BIOME_NAME_TO_ID = {v: k for k, v in BIOME_MAP.items()}

# Biome colors (RGB) - matching renderer.js for visual consistency
BIOME_COLORS = {
    1: (121, 179, 85),     # Meadows - Green
    2: (64, 81, 50),       # BlackForest - Dark green
    4: (119, 108, 82),     # Swamp - Brown-gray
    8: (220, 225, 238),    # Mountain - Light gray/white
    16: (193, 181, 122),   # Plains - Tan
    32: (59, 103, 163),    # Ocean - Blue
    64: (78, 93, 107),     # Mistlands - Dark gray
    256: (210, 230, 255),  # DeepNorth - Lavender
    512: (155, 75, 60)     # Ashlands - Red-brown
}

# Biome colors as normalized (0-1) for matplotlib
BIOME_COLORS_NORMALIZED = {
    k: tuple(c/255 for c in v) for k, v in BIOME_COLORS.items()
}

# ============================================================================
# GAME CONSTANTS (from decompiled WorldGenerator.cs)
# ============================================================================

# Height constants
OCEAN_LEVEL_NORMALIZED = 0.05  # baseHeight threshold for ocean (line 773)
MOUNTAIN_HEIGHT_NORMALIZED = 0.4  # baseHeight threshold for mountain (line 785)
HEIGHT_MULTIPLIER = 200.0  # Converts normalized height to meters (line 81)
SEA_LEVEL_METERS = 30.0  # Actual height threshold in meters (renderer.js)

# World dimensions
WORLD_SIZE = 10000.0  # World radius in meters
WORLD_DIAMETER = 20000.0  # Full world size
WATER_EDGE = 10500.0  # Hard boundary where terrain forced underwater

# ============================================================================
# DISTANCE THRESHOLDS (from decompiled code)
# ============================================================================

# Per-biome distance rings (min/max from center)
DISTANCE_THRESHOLDS = {
    # Format: (min_distance, max_distance)
    'meadows': (0, 5000),
    'blackforest': (600, 6000),  # Note: Also has fallback at >5000m
    'swamp': (2000, 6000),
    'plains': (3000, 8000),
    'mistlands': (6000, 10000),
    'deepnorth': (7140, 12000),  # Reverse-engineered actual threshold
    'ashlands': (9626, 12000),   # Reverse-engineered actual threshold
    'ocean': (7900, 12000),      # Approximate outer ocean boundary
}

# Polar biome Y-axis offsets (directional bias)
POLAR_OFFSETS = {
    'deepnorth': 4000.0,   # Positive offset = northern bias
    'ashlands': -4000.0,   # Negative offset = southern bias
}

# ============================================================================
# NOISE THRESHOLDS (from decompiled code)
# ============================================================================

# Perlin noise thresholds for biome determination
NOISE_THRESHOLDS = {
    'swamp': 0.6,          # Line 789 - Most restrictive
    'mistlands': 0.4,      # Line 793 - Standard
    'plains': 0.4,         # Line 797 - Standard
    'blackforest': 0.4,    # Line 801 - Standard
}

# Noise scale (all biomes use same scale)
BIOME_NOISE_SCALE = 0.001

# ============================================================================
# HEIGHT BAND REQUIREMENTS
# ============================================================================

# Some biomes have specific height requirements
HEIGHT_BANDS = {
    'swamp': {
        'min': 0.05,  # Normalized baseHeight
        'max': 0.25,
        'min_meters': 10.0,  # After * 200 multiplier
        'max_meters': 50.0,
    },
    'mountain': {
        'min': 0.4,
        'min_meters': 80.0,
    },
    'ocean': {
        'max': 0.05,
        'max_meters': 10.0,
    }
}

# ============================================================================
# FILTER DEFAULTS (renderer.js current values)
# ============================================================================

FILTER_DEFAULTS = {
    # Sea level detection
    'sea_level': 30.0,           # Height threshold for water (meters)
    'shoreline_depth': -5.0,     # Shallow water gradient start (meters)

    # Mistlands recovery filter
    'outer_ring_min': 6000.0,    # Start of outer ring (meters)
    'outer_ring_max': 10000.0,   # End of outer ring (meters)
    'polar_threshold': 7000.0,   # Latitude cutoff for polar crescents (meters)

    # Edge biome water distinction
    'deep_water_threshold': 20.0,  # SEA_LEVEL - 10 (meters)
}

# ============================================================================
# DISTANCE RING DEFINITIONS (for spatial analysis)
# ============================================================================

# Standard distance rings for analysis
ANALYSIS_RINGS = [
    (0, 2000, "Center (0-2km)"),
    (2000, 4000, "Inner (2-4km)"),
    (4000, 6000, "Mid (4-6km)"),
    (6000, 8000, "Outer (6-8km)"),
    (8000, 10000, "Far (8-10km)"),
    (10000, 12000, "Edge (10-12km)"),
]

# ============================================================================
# VISUALIZATION SETTINGS
# ============================================================================

# Matplotlib defaults for consistent plots
PLOT_DEFAULTS = {
    'figure_size': (12, 8),
    'dpi': 100,
    'font_size': 11,
    'title_size': 14,
    'label_size': 12,
}

# Color scheme for plots
COLOR_SCHEME = {
    'background': '#f5f5f5',
    'grid': '#cccccc',
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_biome_name(biome_id):
    """Get biome name from ID"""
    return BIOME_MAP.get(biome_id, f"Unknown({biome_id})")

def get_biome_color(biome_id, normalized=False):
    """Get biome color (RGB or normalized)"""
    colors = BIOME_COLORS_NORMALIZED if normalized else BIOME_COLORS
    return colors.get(biome_id, (255, 0, 255) if not normalized else (1.0, 0.0, 1.0))

def normalize_height(height_meters):
    """Convert height in meters to normalized baseHeight"""
    return height_meters / HEIGHT_MULTIPLIER

def meters_to_baseheight(height_meters):
    """Alias for normalize_height"""
    return normalize_height(height_meters)

def baseheight_to_meters(baseheight):
    """Convert normalized baseHeight to meters"""
    return baseheight * HEIGHT_MULTIPLIER

# ============================================================================
# VALIDATION
# ============================================================================

# Expected biome IDs (all valid values)
VALID_BIOME_IDS = set(BIOME_MAP.keys())

def validate_biome_id(biome_id):
    """Check if biome ID is valid"""
    return biome_id in VALID_BIOME_IDS

def is_power_of_two(n):
    """Check if number is a power of 2 (valid biome ID)"""
    return n != 0 and (n & (n - 1)) == 0
