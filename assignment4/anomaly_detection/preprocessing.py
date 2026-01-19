"""
Data preprocessing module for the anomaly detection pipeline.
Handles data synchronization and preprocessing of robot navigation data.
"""

from typing import Optional
import numpy as np
import pandas as pd
from scipy import interpolate

from .data_structures import RunData


class DataPreprocessor:
    """Handles data synchronization and preprocessing."""
    
    @staticmethod
    def normalize_yaw(yaw: np.ndarray) -> np.ndarray:
        """Normalize yaw angle to [-pi, pi] range.
        
        Args:
            yaw: Array of yaw angles
            
        Returns:
            Normalized yaw angles
        """
        return np.arctan2(np.sin(yaw), np.cos(yaw))
    
    @staticmethod
    def quaternion_to_yaw(w: float, x: float, y: float, z: float) -> float:
        """Convert quaternion to yaw angle.
        
        Args:
            w, x, y, z: Quaternion components
            
        Returns:
            Yaw angle in radians
        """
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        return np.arctan2(siny_cosp, cosy_cosp)
    
    @staticmethod
    def sync_poses(poses_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Synchronize ground truth and estimated poses.
        
        Args:
            poses_df: DataFrame with pose data containing ground truth and estimated frames
            
        Returns:
            DataFrame with synchronized data or None if sync fails
        """
        if poses_df is None or poses_df.empty:
            return None
        
        # Separate ground truth and estimated poses
        gt_df = poses_df[poses_df['frame'] == 'nav2_turtlebot4_base_link_gt'].copy()
        est_df = poses_df[poses_df['frame'] == 'base_link'].copy()
        
        if gt_df.empty or est_df.empty:
            return None
        
        # Sort and deduplicate
        gt_df = gt_df.sort_values('timestamp').drop_duplicates('timestamp')
        est_df = est_df.sort_values('timestamp').drop_duplicates('timestamp')
        
        est_times = est_df['timestamp'].values
        gt_times = gt_df['timestamp'].values
        
        if len(gt_times) < 2:
            return None
        
        # Filter to overlapping time range
        valid_mask = (est_times >= gt_times.min()) & (est_times <= gt_times.max())
        est_df = est_df[valid_mask]
        
        if len(est_df) < 2:
            return None
        
        # Create synchronized dataframe
        synced = est_df.copy()
        synced = synced.rename(columns={
            'position.x': 'est_x',
            'position.y': 'est_y',
            'orientation.yaw': 'est_yaw'
        })
        
        # Interpolate ground truth to estimated timestamps
        for col, new_col in [('position.x', 'gt_x'), ('position.y', 'gt_y'), ('orientation.yaw', 'gt_yaw')]:
            f = interpolate.interp1d(gt_times, gt_df[col].values, kind='linear', fill_value='extrapolate')
            synced[new_col] = f(synced['timestamp'].values)
        
        # Normalize yaw angles
        synced['gt_yaw'] = DataPreprocessor.normalize_yaw(synced['gt_yaw'].values)
        synced['est_yaw'] = DataPreprocessor.normalize_yaw(synced['est_yaw'].values)
        
        # Select only needed columns
        synced = synced[['timestamp', 'est_x', 'est_y', 'est_yaw', 'gt_x', 'gt_y', 'gt_yaw']]
        
        return synced.reset_index(drop=True)
    
    @staticmethod
    def filter_stationary(synced_df: pd.DataFrame, velocity_threshold: float = 0.01) -> pd.DataFrame:
        """Filter out stationary periods at start and end of trajectory.
        
        Args:
            synced_df: Synchronized pose DataFrame
            velocity_threshold: Minimum velocity to consider as moving (m/s)
            
        Returns:
            Filtered DataFrame with stationary periods removed
        """
        if synced_df is None or len(synced_df) < 3:
            return synced_df
        
        # Calculate velocity
        dx = np.diff(synced_df['est_x'].values)
        dy = np.diff(synced_df['est_y'].values)
        dt = np.diff(synced_df['timestamp'].values)
        dt = np.where(dt == 0, 1e-6, dt)
        
        velocity = np.sqrt(dx**2 + dy**2) / dt
        velocity = np.concatenate([[velocity[0]], velocity])
        
        # Find moving region
        moving_mask = velocity > velocity_threshold
        first_moving = np.argmax(moving_mask)
        last_moving = len(moving_mask) - np.argmax(moving_mask[::-1]) - 1
        
        return synced_df.iloc[first_moving:last_moving+1].reset_index(drop=True)
    
    def preprocess(self, run: RunData, filter_stationary: bool = True) -> RunData:
        """Full preprocessing pipeline for a run.
        
        Args:
            run: RunData instance to preprocess
            filter_stationary: Whether to filter out stationary periods
            
        Returns:
            Preprocessed RunData instance
        """
        if not run.is_valid:
            return run
        
        # Synchronize poses
        synced = self.sync_poses(run.poses_df)
        
        if synced is None or len(synced) < 10:
            run.is_valid = False
            run.error_msg = 'Sync failed'
            return run
        
        # Filter stationary periods
        if filter_stationary:
            synced = self.filter_stationary(synced)
        
        if synced is None or len(synced) < 5:
            run.is_valid = False
            run.error_msg = 'Too few points after filtering'
            return run
        
        run.synced_data = synced
        return run
