"""
Configuration constants and settings for the anomaly detection pipeline.
"""

from pathlib import Path
import matplotlib.pyplot as plt

# ============================================================================
# Path Configuration
# ============================================================================

DATASET_PATH = Path('ws25_aia_complete_data')
IMAGES_PATH = Path('images')
MODELS_PATH = Path('models')

# ============================================================================
# Robot Constants (TurtleBot4)
# ============================================================================

ROBOT_FOOTPRINT = 0.22  # TurtleBot4 diameter in meters
ROBOT_RADIUS = ROBOT_FOOTPRINT / 2
SENSOR_HEIGHT = 0.20  # LiDAR sensor height from ground (20cm)

# ============================================================================
# Anomaly Labels
# ============================================================================

ANOM_LABELS = [
    'goal_failure',
    'position_error_spike',
    'stuck',
    'high_amcl_uncertainty',
    'high_yaw_error',
    'path_inefficiency',
    'Isolation Forest'
]

# ============================================================================
# Matplotlib Styling
# ============================================================================

def configure_matplotlib():
    """Configure matplotlib with consistent styling for visualizations."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 11
    
    # White background for all plots (important for dark mode compatibility)
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'savefig.facecolor': 'white',
        'savefig.edgecolor': 'white',
        'savefig.transparent': False,
        'axes.edgecolor': 'black',
        'axes.labelcolor': 'black',
        'xtick.color': 'black',
        'ytick.color': 'black',
        'text.color': 'black',
        'grid.color': '#d0d0d0',
        'axes.spines.top': True,
        'axes.spines.right': True,
        'axes.spines.left': True,
        'axes.spines.bottom': True,
    })

# Common kwargs for savefig to ensure white background
SAVEFIG_KW = dict(facecolor='white', edgecolor='white', transparent=False)

# ============================================================================
# Feature Configuration
# ============================================================================

FEATURE_NAMES = [
    # Map-based features (8 continuous)
    'min_wall_distance', 'min_door_distance', 'door_width', 'corridor_width',
    'room_area', 'clearance_ratio', 'goal_wall_distance', 'noise_level',
    # Boolean predicates (12)
    'near_wall', 'at_door', 'door_too_narrow', 'in_narrow_corridor', 'in_small_room',
    'tight_clearance', 'in_corridor', 'goal_near_wall', 'goal_through_door',
    'waypoint_in_tight_space', 'high_noise', 'min_door_narrow',
    # Obstacle-derived features (4 continuous + 3 boolean)
    'min_obstacle_distance', 'obstacle_clearance_ratio', 'num_obstacles', 'total_obstacle_area',
    'near_static_obstacle', 'tight_obstacle_clearance', 'has_static_obstacles'
]

BOOL_FEATURES = {
    'near_wall', 'at_door', 'door_too_narrow', 'in_narrow_corridor', 'in_small_room',
    'tight_clearance', 'in_corridor', 'goal_near_wall', 'goal_through_door',
    'waypoint_in_tight_space', 'high_noise', 'min_door_narrow',
    'near_static_obstacle', 'tight_obstacle_clearance', 'has_static_obstacles'
}

# Static features available BEFORE runtime (for scenario-based prediction)
# These can be computed from scenario.config and maps_details.json only
STATIC_FEATURE_NAMES = [
    # Map-based continuous features (8)
    'min_wall_distance', 'min_door_distance', 'door_width', 'corridor_width',
    'room_area', 'clearance_ratio', 'goal_wall_distance', 'noise_level',
    # Obstacle-derived continuous features (4)
    'min_obstacle_distance', 'obstacle_clearance_ratio', 'num_obstacles', 'total_obstacle_area',
    # Boolean predicates (15)
    'near_wall', 'at_door', 'door_too_narrow', 'in_narrow_corridor', 'in_small_room',
    'tight_clearance', 'in_corridor', 'goal_near_wall', 'goal_through_door',
    'waypoint_in_tight_space', 'high_noise', 'min_door_narrow',
    'near_static_obstacle', 'tight_obstacle_clearance', 'has_static_obstacles'
]

# All features including runtime metrics (for log-based prediction)
# LOG_FEATURE_NAMES = FEATURE_NAMES (same as default, kept for clarity)

# ============================================================================
# Scenario Category Patterns
# ============================================================================

CATEGORY_PATTERNS = {
    'door-width': r'door-width|door-size',
    'room-size': r'room-size',
    'hallway-window': r'hallway-window',
    'everything-failure': r'everything-failure',
    'floorplan-failure': r'floorplan-failure'
}
