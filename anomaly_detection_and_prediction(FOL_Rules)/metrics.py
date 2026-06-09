"""
Metrics computation module for the anomaly detection and prediction pipeline.
Computes performance metrics including position error, velocity, and AMCL uncertainty.
"""

from typing import Tuple, Optional
import numpy as np
import pandas as pd

from .data_structures import RunData, RunMetrics, AMCLData


class MetricCalculator:
    """Computes performance metrics including AMCL uncertainty."""
    
    @staticmethod
    def compute_position_error(synced: pd.DataFrame) -> np.ndarray:
        """Compute position error between estimated and ground truth.
        
        Args:
            synced: Synchronized pose DataFrame
            
        Returns:
            Array of position errors
        """
        return np.sqrt((synced['est_x'] - synced['gt_x'])**2 + 
                      (synced['est_y'] - synced['gt_y'])**2)
    
    @staticmethod
    def compute_yaw_error(synced: pd.DataFrame) -> np.ndarray:
        """Compute yaw error between estimated and ground truth.
        
        Args:
            synced: Synchronized pose DataFrame
            
        Returns:
            Array of absolute yaw errors
        """
        diff = synced['est_yaw'] - synced['gt_yaw']
        return np.abs(np.arctan2(np.sin(diff), np.cos(diff)))
    
    @staticmethod
    def compute_path_length(x: np.ndarray, y: np.ndarray) -> float:
        """Compute total path length.
        
        Args:
            x: Array of x coordinates
            y: Array of y coordinates
            
        Returns:
            Total path length
        """
        return float(np.sum(np.sqrt(np.diff(x)**2 + np.diff(y)**2)))
    
    @staticmethod
    def compute_velocities(synced: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Compute linear and angular velocities.
        
        Args:
            synced: Synchronized pose DataFrame
            
        Returns:
            Tuple of (linear_velocity, angular_velocity) arrays
        """
        t = synced['timestamp'].values
        dt = np.diff(t)
        dt = np.where(dt == 0, 1e-6, dt)
        
        dx = np.diff(synced['est_x'].values)
        dy = np.diff(synced['est_y'].values)
        dyaw = np.diff(synced['est_yaw'].values)
        dyaw = np.arctan2(np.sin(dyaw), np.cos(dyaw))
        
        linear_vel = np.sqrt(dx**2 + dy**2) / dt
        angular_vel = np.abs(dyaw) / dt
        
        return linear_vel, angular_vel
    
    @staticmethod
    def compute_trajectory_smoothness(angular_vel: np.ndarray, dt: np.ndarray) -> float:
        """Compute trajectory smoothness as mean angular acceleration.
        
        Args:
            angular_vel: Array of angular velocities
            dt: Array of time deltas
            
        Returns:
            Mean absolute angular acceleration
        """
        if len(angular_vel) < 2:
            return 0.0
        
        dt_safe = np.where(dt[:-1] == 0, 1e-6, dt[:-1]) if len(dt) > len(angular_vel)-1 else dt
        angular_acc = np.diff(angular_vel) / dt_safe[:len(angular_vel)-1]
        
        return float(np.mean(np.abs(angular_acc)))
    
    @staticmethod
    def compute_amcl_uncertainty(amcl_data: Optional[AMCLData]) -> float:
        """Compute mean positional uncertainty from AMCL covariance.
        
        Uses sqrt of sum of x,y variances (diagonal elements 0,0 and 1,1).
        This represents the 1-sigma positional uncertainty ellipse size.
        
        Args:
            amcl_data: AMCLData instance with covariance matrices
            
        Returns:
            Mean positional uncertainty
        """
        if amcl_data is None or not amcl_data.covariances:
            return 0.0
        
        uncertainties = []
        for cov in amcl_data.covariances:
            try:
                if cov is None or not isinstance(cov, np.ndarray):
                    continue
                if cov.shape != (6, 6):
                    continue
                
                # Extract x and y variances (diagonal elements)
                var_x = cov[0, 0]
                var_y = cov[1, 1]
                
                # Skip invalid values
                if not (np.isfinite(var_x) and np.isfinite(var_y)):
                    continue
                if var_x < 0 or var_y < 0:
                    continue
                
                # Positional uncertainty: sqrt of sum of variances
                pos_uncertainty = np.sqrt(var_x + var_y)
                
                # Sanity check: uncertainty should be reasonable (<100m)
                if pos_uncertainty < 100.0:
                    uncertainties.append(pos_uncertainty)
            except Exception:
                continue
        
        if not uncertainties:
            return 0.0
        
        return float(np.mean(uncertainties))
    
    def compute_time_series(self, synced: pd.DataFrame) -> pd.DataFrame:
        """Compute time series of error and velocity metrics.
        
        Args:
            synced: Synchronized pose DataFrame
            
        Returns:
            DataFrame with time series metrics
        """
        pos_error = self.compute_position_error(synced)
        yaw_error = self.compute_yaw_error(synced)
        linear_vel, angular_vel = self.compute_velocities(synced)
        
        ts = pd.DataFrame({
            'timestamp': synced['timestamp'].values,
            'pos_error': pos_error,
            'yaw_error': yaw_error
        })
        
        # Pad velocities to match length
        ts['linear_vel'] = np.concatenate([[linear_vel[0]], linear_vel])
        ts['angular_vel'] = np.concatenate([[angular_vel[0]], angular_vel])
        
        return ts
    
    def compute_metrics(self, run: RunData) -> RunData:
        """Compute all metrics for a run.
        
        Args:
            run: RunData instance with synced_data
            
        Returns:
            RunData instance with computed metrics
        """
        if not run.is_valid or run.synced_data is None:
            return run
        
        synced = run.synced_data
        
        # Compute individual metrics
        pos_error = self.compute_position_error(synced)
        yaw_error = self.compute_yaw_error(synced)
        linear_vel, angular_vel = self.compute_velocities(synced)
        
        executed_path = self.compute_path_length(synced['est_x'].values, synced['est_y'].values)
        gt_path = self.compute_path_length(synced['gt_x'].values, synced['gt_y'].values)
        
        dt = np.diff(synced['timestamp'].values)
        mean_amcl = self.compute_amcl_uncertainty(run.amcl_data)
        
        run.metrics = RunMetrics(
            mean_pos_error=float(np.mean(pos_error)),
            rmse_pos=float(np.sqrt(np.mean(pos_error**2))),
            mean_yaw_error=float(np.mean(yaw_error)),
            executed_path_length=executed_path,
            path_efficiency=gt_path / executed_path if executed_path > 0 else 0,
            mean_linear_velocity=float(np.mean(linear_vel)),
            mean_angular_velocity=float(np.mean(angular_vel)),
            trajectory_smoothness=self.compute_trajectory_smoothness(angular_vel, dt),
            duration=float(synced['timestamp'].iloc[-1] - synced['timestamp'].iloc[0]),
            mean_amcl_uncertainty=mean_amcl
        )
        
        run.time_series_metrics = self.compute_time_series(synced)
        
        return run
