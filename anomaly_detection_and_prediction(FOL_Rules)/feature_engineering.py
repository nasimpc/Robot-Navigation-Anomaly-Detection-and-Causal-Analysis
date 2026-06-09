"""
Feature engineering module for the anomaly detection and prediction pipeline.
Provides map geometry parsing, computable functions, atomic relations, and feature extraction.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
from shapely.geometry import Point, Polygon, LineString

from .data_structures import RunData, StaticObject
from .config import ROBOT_FOOTPRINT, ROBOT_RADIUS, FEATURE_NAMES


class MapGeometry:
    """Loads and provides geometric queries for map features."""
    
    def __init__(self, maps_details_path: Path):
        """Initialize with path to maps_details.json.
        
        Args:
            maps_details_path: Path to the maps details JSON file
        """
        with open(maps_details_path, 'r') as f:
            self.data = json.load(f)
        self.maps = {}
        self._parse_maps()
    
    def _parse_maps(self) -> None:
        """Parse all maps from the JSON data."""
        for map_info in self.data['maps']:
            map_name = map_info['map']
            spaces = {}
            
            for space in map_info['spaces']:
                space_name = space['space_name']
                corners = space['corners']
                door = space.get('door', [])
                
                polygon = Polygon(corners) if len(corners) >= 3 else None
                door_line = LineString(door) if len(door) == 2 else None
                door_width = door_line.length if door_line else 0.0
                
                spaces[space_name] = {
                    'polygon': polygon,
                    'corners': corners,
                    'door_line': door_line,
                    'door_width': door_width,
                    'door_center': door_line.centroid if door_line else None
                }
            
            self.maps[map_name] = spaces
    
    def get_map_for_scenario(self, scenario_name: str) -> Optional[dict]:
        """Get map spaces for a scenario.
        
        Args:
            scenario_name: Name of the scenario
            
        Returns:
            Dictionary of space info or None
        """
        scenario_lower = scenario_name.lower()
        
        mapping = {
            '0.3 door': '0-3-door', '0.33 door': '0-33-door', '0.36 door': '0-36-door',
            '0.44 door': '0-44-door', '0.47 door': '0-47-door', 'door_size_0.5': 'door-size-0-5',
            'hallway_window': 'hallway-window', 'room_size_less_50': 'room-size-less-50'
        }
        
        for map_name, spaces in self.maps.items():
            for key, pattern in mapping.items():
                if key in map_name.lower() and pattern in scenario_lower:
                    return spaces
        
        return list(self.maps.values())[0] if self.maps else None
    
    def get_corridor_width(self, spaces: dict) -> float:
        """Get corridor width from spaces.
        
        Args:
            spaces: Dictionary of space info
            
        Returns:
            Corridor width in meters
        """
        if 'corridor' in spaces and spaces['corridor']['polygon']:
            bounds = spaces['corridor']['polygon'].bounds
            return min(bounds[2] - bounds[0], bounds[3] - bounds[1])
        return 1.67
    
    def get_min_door_width(self, spaces: dict) -> float:
        """Get minimum door width from spaces.
        
        Args:
            spaces: Dictionary of space info
            
        Returns:
            Minimum door width in meters
        """
        widths = [s['door_width'] for s in spaces.values() if s['door_width'] > 0]
        return min(widths) if widths else 1.0


class ComputableFunctions:
    """Computable functions F - distances, areas, clearances."""
    
    def __init__(self, map_geometry: MapGeometry):
        """Initialize with MapGeometry instance.
        
        Args:
            map_geometry: MapGeometry instance for geometric queries
        """
        self.map_geometry = map_geometry
    
    def distance_to_closest_wall(self, x: float, y: float, spaces: dict) -> float:
        """Compute distance to closest wall.
        
        Args:
            x, y: Position coordinates
            spaces: Dictionary of space info
            
        Returns:
            Distance to closest wall in meters
        """
        point = Point(x, y)
        min_dist = float('inf')
        
        for space_info in spaces.values():
            if space_info['polygon']:
                min_dist = min(min_dist, point.distance(space_info['polygon'].exterior))
        
        return min_dist if min_dist != float('inf') else 0.5
    
    def distance_to_closest_door(self, x: float, y: float, spaces: dict) -> Tuple[float, Optional[str]]:
        """Compute distance to closest door.
        
        Args:
            x, y: Position coordinates
            spaces: Dictionary of space info
            
        Returns:
            Tuple of (distance, room_name) or (10.0, None) if no door found
        """
        point = Point(x, y)
        min_dist = float('inf')
        closest_room = None
        
        for space_name, space_info in spaces.items():
            if space_info['door_center']:
                dist = point.distance(space_info['door_center'])
                if dist < min_dist:
                    min_dist = dist
                    closest_room = space_name
        
        return (min_dist if min_dist != float('inf') else 10.0, closest_room)
    
    def door_width_at_location(self, x: float, y: float, spaces: dict) -> float:
        """Get door width at a location.
        
        Args:
            x, y: Position coordinates
            spaces: Dictionary of space info
            
        Returns:
            Door width if near a door, else 1.0
        """
        dist, room = self.distance_to_closest_door(x, y, spaces)
        return spaces[room]['door_width'] if room and dist < 1.0 else 1.0
    
    def get_current_room(self, x: float, y: float, spaces: dict) -> Optional[str]:
        """Get the room containing a position.
        
        Args:
            x, y: Position coordinates
            spaces: Dictionary of space info
            
        Returns:
            Room name or None
        """
        point = Point(x, y)
        for space_name, space_info in spaces.items():
            if space_info['polygon'] and space_info['polygon'].contains(point):
                return space_name
        return None
    
    def room_area(self, room_name: str, spaces: dict) -> float:
        """Get area of a room.
        
        Args:
            room_name: Name of the room
            spaces: Dictionary of space info
            
        Returns:
            Room area in square meters
        """
        if room_name and room_name in spaces and spaces[room_name]['polygon']:
            return spaces[room_name]['polygon'].area
        return 20.0
    
    def goal_to_wall_distance(self, gx: float, gy: float, spaces: dict) -> float:
        """Compute distance from goal to closest wall.
        
        Args:
            gx, gy: Goal coordinates
            spaces: Dictionary of space info
            
        Returns:
            Distance to closest wall
        """
        return self.distance_to_closest_wall(gx, gy, spaces)
    
    def path_crosses_door(self, sx: float, sy: float, gx: float, gy: float, spaces: dict) -> bool:
        """Check if path from start to goal crosses a door.
        
        Args:
            sx, sy: Start coordinates
            gx, gy: Goal coordinates
            spaces: Dictionary of space info
            
        Returns:
            True if path crosses a door
        """
        path = LineString([(sx, sy), (gx, gy)])
        return any(s['door_line'] and path.intersects(s['door_line']) for s in spaces.values())
    
    # Static Object (Obstacle) Functions
    
    def distance_to_closest_obstacle(self, x: float, y: float, 
                                      static_objects: List[StaticObject]) -> float:
        """Compute distance to closest static obstacle center.
        
        Args:
            x, y: Position coordinates
            static_objects: List of StaticObject instances
            
        Returns:
            Distance to closest obstacle or infinity if none
        """
        if not static_objects:
            return float('inf')
        return min(np.sqrt((x - obj.position[0])**2 + (y - obj.position[1])**2) 
                   for obj in static_objects)
    
    def obstacle_clearance_ratio(self, x: float, y: float, 
                                  static_objects: List[StaticObject]) -> float:
        """Compute ratio of distance to closest obstacle vs robot radius.
        
        Args:
            x, y: Position coordinates
            static_objects: List of StaticObject instances
            
        Returns:
            Clearance ratio (higher is better)
        """
        dist = self.distance_to_closest_obstacle(x, y, static_objects)
        return dist / ROBOT_RADIUS if dist != float('inf') else 10.0
    
    def path_passes_near_obstacle(self, trajectory_x: np.ndarray, trajectory_y: np.ndarray,
                                   static_objects: List[StaticObject], 
                                   threshold: float = 0.5) -> bool:
        """Check if trajectory passes within threshold of any obstacle.
        
        Args:
            trajectory_x, trajectory_y: Arrays of trajectory coordinates
            static_objects: List of StaticObject instances
            threshold: Distance threshold in meters
            
        Returns:
            True if trajectory passes near an obstacle
        """
        if not static_objects:
            return False
        for x, y in zip(trajectory_x, trajectory_y):
            if self.distance_to_closest_obstacle(x, y, static_objects) < threshold:
                return True
        return False


class AtomicRelations:
    """Boolean predicates R based on causal features."""
    
    def __init__(self, functions: ComputableFunctions, footprint: float = ROBOT_FOOTPRINT):
        """Initialize with ComputableFunctions.
        
        Args:
            functions: ComputableFunctions instance
            footprint: Robot footprint diameter
        """
        self.F = functions
        self.footprint = footprint
    
    def near_wall(self, x: float, y: float, spaces: dict) -> bool:
        """True if near a wall."""
        return self.F.distance_to_closest_wall(x, y, spaces) < self.footprint * 1.5
    
    def at_door(self, x: float, y: float, spaces: dict) -> bool:
        """True if at a door."""
        return self.F.distance_to_closest_door(x, y, spaces)[0] < 0.5
    
    def door_too_narrow(self, x: float, y: float, spaces: dict) -> bool:
        """True if nearby door is too narrow."""
        return self.F.door_width_at_location(x, y, spaces) < self.footprint * 1.8
    
    def in_narrow_corridor(self, spaces: dict) -> bool:
        """True if in a narrow corridor."""
        return self.F.map_geometry.get_corridor_width(spaces) < self.footprint * 3
    
    def in_small_room(self, x: float, y: float, spaces: dict) -> bool:
        """True if in a small room."""
        room = self.F.get_current_room(x, y, spaces)
        return self.F.room_area(room, spaces) < 5.0 if room else False
    
    def tight_clearance(self, x: float, y: float, spaces: dict) -> bool:
        """True if clearance to wall is tight."""
        return self.F.distance_to_closest_wall(x, y, spaces) < self.footprint * 1.2
    
    def in_corridor(self, x: float, y: float, spaces: dict) -> bool:
        """True if position is in corridor."""
        return self.F.get_current_room(x, y, spaces) == 'corridor'
    
    def goal_near_wall(self, gx: float, gy: float, spaces: dict) -> bool:
        """True if goal is near a wall."""
        return self.F.goal_to_wall_distance(gx, gy, spaces) < self.footprint
    
    def goal_through_door(self, sx: float, sy: float, gx: float, gy: float, spaces: dict) -> bool:
        """True if path to goal crosses a door."""
        return self.F.path_crosses_door(sx, sy, gx, gy, spaces)
    
    def waypoint_in_tight_space(self, gx: float, gy: float, spaces: dict) -> bool:
        """True if goal/waypoint is in tight space."""
        return self.F.distance_to_closest_wall(gx, gy, spaces) < self.footprint * 1.5
    
    def high_noise(self, noise: float) -> bool:
        """True if laser noise is high."""
        return noise > 0.05
    
    def min_door_narrow(self, spaces: dict) -> bool:
        """True if minimum door width is narrow."""
        return self.F.map_geometry.get_min_door_width(spaces) < self.footprint * 1.8
    
    # Static Object (Obstacle) Predicates
    
    def near_static_obstacle(self, x: float, y: float, 
                              static_objects: List[StaticObject], threshold: float = 0.5) -> bool:
        """True if position is near a static obstacle."""
        return self.F.distance_to_closest_obstacle(x, y, static_objects) < threshold
    
    def tight_obstacle_clearance(self, x: float, y: float, static_objects: List[StaticObject]) -> bool:
        """True if clearance to obstacle is less than 1.5x robot footprint."""
        dist = self.F.distance_to_closest_obstacle(x, y, static_objects)
        return dist < self.footprint * 1.5 if dist != float('inf') else False
    
    def has_static_obstacles(self, static_objects: List[StaticObject]) -> bool:
        """True if scenario has any static obstacles."""
        return len(static_objects) > 0


class FeatureExtractor:
    """Extract feature vectors for anomaly rule derivation."""
    
    FEATURE_NAMES = FEATURE_NAMES
    
    def __init__(self, map_geometry: MapGeometry, relations: AtomicRelations, 
                 functions: ComputableFunctions):
        """Initialize with geometry and relation classes.
        
        Args:
            map_geometry: MapGeometry instance
            relations: AtomicRelations instance
            functions: ComputableFunctions instance
        """
        self.map_geometry = map_geometry
        self.R = relations
        self.F = functions
    
    def extract_features(self, run: RunData) -> Optional[np.ndarray]:
        """Extract feature vector for a run.
        
        Args:
            run: RunData instance
            
        Returns:
            Feature array or None if extraction fails
        """
        if not run.is_valid or run.synced_data is None or run.config is None:
            return None
        
        spaces = self.map_geometry.get_map_for_scenario(run.scenario_name)
        if not spaces:
            return None
        
        synced = run.synced_data
        config = run.config
        
        # Mean trajectory position
        mean_x = synced['gt_x'].mean()
        mean_y = synced['gt_y'].mean()
        
        # Goal and start positions
        goals = config.goal_poses
        goal_x = goals[-1].get('position', {}).get('x', 0) if goals else mean_x
        goal_y = goals[-1].get('position', {}).get('y', 0) if goals else mean_y
        start_x = config.start_pose.get('position', {}).get('x', 0)
        start_y = config.start_pose.get('position', {}).get('y', 0)
        noise = config.laser_noise_std
        
        # Get static objects from config
        static_objects = config.static_objects if hasattr(config, 'static_objects') else []
        
        # Map-based features
        min_wall = self.F.distance_to_closest_wall(mean_x, mean_y, spaces)
        min_door, _ = self.F.distance_to_closest_door(mean_x, mean_y, spaces)
        door_w = self.F.door_width_at_location(mean_x, mean_y, spaces)
        corr_w = self.map_geometry.get_corridor_width(spaces)
        room = self.F.get_current_room(mean_x, mean_y, spaces)
        room_a = self.F.room_area(room, spaces) if room else 20.0
        clearance = min_wall / ROBOT_RADIUS if ROBOT_RADIUS > 0 else 10.0
        goal_wall = self.F.goal_to_wall_distance(goal_x, goal_y, spaces)
        
        # Obstacle-derived continuous features
        min_obs_dist = self.F.distance_to_closest_obstacle(mean_x, mean_y, static_objects)
        min_obs_dist = min_obs_dist if min_obs_dist != float('inf') else 10.0
        obs_clearance = self.F.obstacle_clearance_ratio(mean_x, mean_y, static_objects)
        num_obstacles = len(static_objects)
        total_obs_area = sum(o.dimensions[0] * o.dimensions[1] for o in static_objects) if static_objects else 0.0
        
        return np.array([
            # 8 continuous features
            min_wall, min_door, door_w, corr_w, room_a, clearance, goal_wall, noise,
            # 12 boolean predicates
            int(self.R.near_wall(mean_x, mean_y, spaces)),
            int(self.R.at_door(mean_x, mean_y, spaces)),
            int(self.R.door_too_narrow(mean_x, mean_y, spaces)),
            int(self.R.in_narrow_corridor(spaces)),
            int(self.R.in_small_room(mean_x, mean_y, spaces)),
            int(self.R.tight_clearance(mean_x, mean_y, spaces)),
            int(self.R.in_corridor(mean_x, mean_y, spaces)),
            int(self.R.goal_near_wall(goal_x, goal_y, spaces)),
            int(self.R.goal_through_door(start_x, start_y, goal_x, goal_y, spaces)),
            int(self.R.waypoint_in_tight_space(goal_x, goal_y, spaces)),
            int(self.R.high_noise(noise)),
            int(self.R.min_door_narrow(spaces)),
            # 4 obstacle continuous + 3 obstacle boolean features
            min_obs_dist, obs_clearance, num_obstacles, total_obs_area,
            int(self.R.near_static_obstacle(mean_x, mean_y, static_objects)),
            int(self.R.tight_obstacle_clearance(mean_x, mean_y, static_objects)),
            int(self.R.has_static_obstacles(static_objects))
        ])
    
    def extract_scenario_features(self, config: 'ScenarioConfig', scenario_name: str) -> Optional[np.ndarray]:
        """Extract features from scenario configuration only (for scenario-based prediction).
        
        Args:
            config: ScenarioConfig instance
            scenario_name: Name of the scenario
            
        Returns:
            Feature array or None
        """
        spaces = self.map_geometry.get_map_for_scenario(scenario_name)
        if not spaces:
            return None
        
        # Use start and goal positions for features
        goals = config.goal_poses
        goal_x = goals[-1].get('position', {}).get('x', 0) if goals else 0
        goal_y = goals[-1].get('position', {}).get('y', 0) if goals else 0
        start_x = config.start_pose.get('position', {}).get('x', 0)
        start_y = config.start_pose.get('position', {}).get('y', 0)
        
        # Use midpoint as "mean position"
        mean_x = (start_x + goal_x) / 2
        mean_y = (start_y + goal_y) / 2
        noise = config.laser_noise_std
        static_objects = config.static_objects if hasattr(config, 'static_objects') else []
        
        # Map-based features
        min_wall = self.F.distance_to_closest_wall(mean_x, mean_y, spaces)
        min_door, _ = self.F.distance_to_closest_door(mean_x, mean_y, spaces)
        door_w = self.F.door_width_at_location(mean_x, mean_y, spaces)
        corr_w = self.map_geometry.get_corridor_width(spaces)
        room = self.F.get_current_room(mean_x, mean_y, spaces)
        room_a = self.F.room_area(room, spaces) if room else 20.0
        clearance = min_wall / ROBOT_RADIUS if ROBOT_RADIUS > 0 else 10.0
        goal_wall = self.F.goal_to_wall_distance(goal_x, goal_y, spaces)
        
        # Obstacle-derived features
        min_obs_dist = self.F.distance_to_closest_obstacle(mean_x, mean_y, static_objects)
        min_obs_dist = min_obs_dist if min_obs_dist != float('inf') else 10.0
        obs_clearance = self.F.obstacle_clearance_ratio(mean_x, mean_y, static_objects)
        num_obstacles = len(static_objects)
        total_obs_area = sum(o.dimensions[0] * o.dimensions[1] for o in static_objects) if static_objects else 0.0
        
        return np.array([
            min_wall, min_door, door_w, corr_w, room_a, clearance, goal_wall, noise,
            int(self.R.near_wall(mean_x, mean_y, spaces)),
            int(self.R.at_door(mean_x, mean_y, spaces)),
            int(self.R.door_too_narrow(mean_x, mean_y, spaces)),
            int(self.R.in_narrow_corridor(spaces)),
            int(self.R.in_small_room(mean_x, mean_y, spaces)),
            int(self.R.tight_clearance(mean_x, mean_y, spaces)),
            int(self.R.in_corridor(mean_x, mean_y, spaces)),
            int(self.R.goal_near_wall(goal_x, goal_y, spaces)),
            int(self.R.goal_through_door(start_x, start_y, goal_x, goal_y, spaces)),
            int(self.R.waypoint_in_tight_space(goal_x, goal_y, spaces)),
            int(self.R.high_noise(noise)),
            int(self.R.min_door_narrow(spaces)),
            min_obs_dist, obs_clearance, num_obstacles, total_obs_area,
            int(self.R.near_static_obstacle(mean_x, mean_y, static_objects)),
            int(self.R.tight_obstacle_clearance(mean_x, mean_y, static_objects)),
            int(self.R.has_static_obstacles(static_objects))
        ])
