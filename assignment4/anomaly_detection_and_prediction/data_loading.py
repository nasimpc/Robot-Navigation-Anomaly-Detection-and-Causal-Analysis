"""
Data loading module for the anomaly detection and prediction pipeline.
Handles loading and parsing of all dataset files.
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Optional
import yaml
import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from .data_structures import StaticObject, ScenarioConfig, AMCLData, RunData
from .config import CATEGORY_PATTERNS


class DatasetLoader:
    """Handles loading and parsing of all dataset files including rosbag2.csv."""
    
    def __init__(self, dataset_path: Path):
        """Initialize the loader with dataset path.
        
        Args:
            dataset_path: Path to the dataset directory
        """
        self.dataset_path = Path(dataset_path)
    
    def get_scenario_category(self, scenario_name: str) -> str:
        """Determine scenario category from name.
        
        Args:
            scenario_name: Name of the scenario
            
        Returns:
            Category string ('door-width', 'room-size', etc.) or 'other'
        """
        for cat, pattern in CATEGORY_PATTERNS.items():
            if re.search(pattern, scenario_name, re.IGNORECASE):
                return cat
        return 'other'
    
    def parse_static_objects(self, static_objs_data: List[Dict]) -> List[StaticObject]:
        """Parse static objects from scenario config.
        
        Args:
            static_objs_data: List of static object dictionaries from config
            
        Returns:
            List of StaticObject instances
        """
        objects = []
        if not static_objs_data:
            return objects
            
        for obj in static_objs_data:
            try:
                spawn_pose = obj.get('spawn_pose', {})
                pos = spawn_pose.get('position', {})
                ori = spawn_pose.get('orientation', {})
                
                # Parse xacro_arguments (e.g., 'width:=0.5, length:=0.5, height:=1.0')
                xacro = obj.get('xacro_arguments', '')
                dims = {'width': 0.5, 'length': 0.5, 'height': 1.0}
                if xacro:
                    for part in xacro.split(','):
                        if ':=' in part:
                            k, v = part.strip().split(':=')
                            dims[k.strip()] = float(v.strip())
                            
                objects.append(StaticObject(
                    entity_name=obj.get('entity_name', 'unknown'),
                    position=(float(pos.get('x', 0)), float(pos.get('y', 0)), float(pos.get('z', 0))),
                    orientation_yaw=float(ori.get('yaw', 0)),
                    dimensions=(dims['width'], dims['length'], dims['height'])
                ))
            except Exception:
                continue
                
        return objects
    
    def parse_scenario_config(self, config_path: Path) -> Optional[ScenarioConfig]:
        """Parse scenario configuration file.
        
        Args:
            config_path: Path to scenario.config file
            
        Returns:
            ScenarioConfig instance or None if parsing fails
        """
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            ts = data.get('test_scenario', {})
            static_objs = self.parse_static_objects(ts.get('static_objects', []))
            
            return ScenarioConfig(
                goal_poses=ts.get('goal_poses', []),
                start_pose=ts.get('start_pose', {}),
                laser_noise_std=float(ts.get('laserscan_gaussian_noise_std_deviation', 0.02)),
                laser_drop_pct=float(ts.get('laserscan_random_drop_percentage', 0.0)),
                map_file=ts.get('map_file', ''),
                static_objects=static_objs
            )
        except Exception:
            return None
    
    def parse_amcl_data(self, rosbag_df: pd.DataFrame) -> Optional[AMCLData]:
        """Extract AMCL pose data with uncertainty from rosbag2.csv.
        
        Args:
            rosbag_df: DataFrame from rosbag2.csv
            
        Returns:
            AMCLData instance or None if parsing fails
        """
        if rosbag_df is None or rosbag_df.empty:
            return None
            
        amcl_rows = rosbag_df[rosbag_df['topic'] == '/amcl_pose']
        if amcl_rows.empty:
            return None
            
        try:
            timestamps = (amcl_rows['timestamp'].values / 1e9).astype(float)
            positions = np.column_stack([
                amcl_rows['pose.pose.position.x'].values,
                amcl_rows['pose.pose.position.y'].values,
                amcl_rows['pose.pose.position.z'].fillna(0).values
            ])
            orientations = np.column_stack([
                amcl_rows['pose.pose.orientation.w'].values,
                amcl_rows['pose.pose.orientation.x'].values,
                amcl_rows['pose.pose.orientation.y'].values,
                amcl_rows['pose.pose.orientation.z'].values
            ])
            
            # Parse covariance matrices with improved handling
            covariances = []
            for cov_val in amcl_rows['pose.covariance'].values:
                try:
                    if cov_val is None or (isinstance(cov_val, float) and np.isnan(cov_val)):
                        covariances.append(np.eye(6) * 0.01)
                        continue
                    
                    if isinstance(cov_val, str):
                        # Clean string and parse
                        cov_str = cov_val.replace('\n', ' ').replace('[', '').replace(']', '')
                        cov_arr = np.fromstring(cov_str, sep=' ')
                        if len(cov_arr) != 36:
                            # Try comma separation
                            cov_arr = np.fromstring(cov_str, sep=',')
                        if len(cov_arr) != 36:
                            # Try ast.literal_eval as fallback
                            cov_arr = np.array(ast.literal_eval(cov_val.replace('\n', ' ')))
                    elif isinstance(cov_val, (list, np.ndarray)):
                        cov_arr = np.array(cov_val).flatten()
                    else:
                        covariances.append(np.eye(6) * 0.01)
                        continue
                    
                    if len(cov_arr) == 36:
                        cov_matrix = cov_arr.reshape(6, 6)
                        # Validate: covariance diagonal should be non-negative
                        if np.all(np.diag(cov_matrix) >= 0):
                            covariances.append(cov_matrix)
                        else:
                            covariances.append(np.eye(6) * 0.01)
                    else:
                        covariances.append(np.eye(6) * 0.01)
                except Exception:
                    covariances.append(np.eye(6) * 0.01)
            
            return AMCLData(
                timestamps=timestamps, 
                positions=positions,
                orientations=orientations, 
                covariances=covariances
            )
        except Exception:
            return None
    
    def get_run_outcome(self, behaviors_df: pd.DataFrame) -> str:
        """Determine run outcome from behaviors data.
        
        Args:
            behaviors_df: DataFrame from behaviors.csv
            
        Returns:
            Outcome string ('success', 'failure', 'incomplete', 'no_data', 'no_navigation')
        """
        if behaviors_df is None or behaviors_df.empty:
            return 'no_data'
            
        nav = behaviors_df[behaviors_df['behavior_name'].str.contains('nav_through_poses', na=False)]
        if nav.empty:
            return 'no_navigation'
            
        last_status = nav.iloc[-1]['status_name']
        if last_status == 'SUCCESS':
            return 'success'
        elif last_status == 'FAILURE':
            return 'failure'
        else:
            return 'incomplete'
    
    def load_run(self, run_path: Path, scenario_name: str, run_id: int) -> RunData:
        """Load a single run's data.
        
        Args:
            run_path: Path to the run directory
            scenario_name: Name of the scenario
            run_id: Run identifier
            
        Returns:
            RunData instance with loaded data
        """
        run = RunData(
            scenario_name=scenario_name,
            run_id=run_id,
            run_path=run_path,
            scenario_category=self.get_scenario_category(scenario_name)
        )
        
        # Load poses.csv
        poses_path = run_path / 'poses.csv'
        if poses_path.exists():
            try:
                run.poses_df = pd.read_csv(poses_path)
                if run.poses_df.empty:
                    run.is_valid = False
                    run.error_msg = 'Empty poses.csv'
            except Exception as e:
                run.is_valid = False
                run.error_msg = f'Poses error: {e}'
        else:
            run.is_valid = False
            run.error_msg = 'Missing poses.csv'
        
        # Load behaviors.csv
        behaviors_path = run_path / 'behaviors.csv'
        if behaviors_path.exists():
            try:
                run.behaviors_df = pd.read_csv(behaviors_path)
            except Exception:
                pass
        
        # Load rosbag2.csv
        rosbag_path = run_path / 'rosbag2.csv'
        if rosbag_path.exists():
            try:
                run.rosbag_df = pd.read_csv(rosbag_path, low_memory=False)
                run.amcl_data = self.parse_amcl_data(run.rosbag_df)
            except Exception:
                pass
        
        # Load config
        config_path = run_path / 'scenario.config'
        if config_path.exists():
            run.config = self.parse_scenario_config(config_path)
        
        run.outcome = self.get_run_outcome(run.behaviors_df)
        return run
    
    def load_all_runs(self, max_scenarios: int = None, show_progress: bool = True) -> List[RunData]:
        """Load all runs from the dataset.
        
        Args:
            max_scenarios: Maximum number of scenarios to load (None for all)
            show_progress: Whether to show progress bar
            
        Returns:
            List of RunData instances
        """
        runs = []
        scenario_dirs = sorted([d for d in self.dataset_path.iterdir() if d.is_dir()])
        
        if max_scenarios:
            scenario_dirs = scenario_dirs[:max_scenarios]
        
        iterator = tqdm(scenario_dirs, desc='Loading scenarios') if show_progress else scenario_dirs
        
        for scenario_dir in iterator:
            scenario_name = scenario_dir.name
            run_dirs = sorted([d for d in scenario_dir.iterdir() if d.is_dir() and d.name.isdigit()])
            
            for run_dir in run_dirs:
                run = self.load_run(run_dir, scenario_name, int(run_dir.name))
                runs.append(run)
        
        return runs
    
    def load_scenario_only(self, scenario_config_path: Path) -> Optional[ScenarioConfig]:
        """Load only scenario configuration (for scenario-based prediction).
        
        Args:
            scenario_config_path: Path to scenario.config file
            
        Returns:
            ScenarioConfig instance or None
        """
        return self.parse_scenario_config(scenario_config_path)
