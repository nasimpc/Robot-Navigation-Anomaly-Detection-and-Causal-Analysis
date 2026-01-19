"""
Anomaly detection module for the pipeline.
Provides rule-based and ML-based anomaly detection.
"""

from typing import List, Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .data_structures import RunData


class RuleBasedAnomalyDetector:
    """Rule-based anomaly detection using multiple data sources."""
    
    def __init__(self, pos_error_sigma: float = 3.0, consecutive_frames: int = 3):
        """Initialize detector with thresholds.
        
        Args:
            pos_error_sigma: Number of standard deviations for position error anomaly
            consecutive_frames: Number of consecutive frames for spike detection
        """
        self.pos_error_sigma = pos_error_sigma
        self.consecutive_frames = consecutive_frames
        self.global_pos_error_stats = None
    
    def compute_global_stats(self, runs: List[RunData]) -> None:
        """Compute global statistics from all runs.
        
        Args:
            runs: List of RunData instances
        """
        all_errors = []
        for run in runs:
            if run.is_valid and run.time_series_metrics is not None:
                all_errors.extend(run.time_series_metrics['pos_error'].values)
        
        if all_errors:
            self.global_pos_error_stats = {
                'mean': np.mean(all_errors),
                'std': np.std(all_errors)
            }
    
    def detect_goal_failure(self, run: RunData) -> bool:
        """Detect if the run failed to reach goal.
        
        Args:
            run: RunData instance
            
        Returns:
            True if goal failure occurred
        """
        return run.outcome == 'failure'
    
    def detect_position_error_spike(self, run: RunData) -> bool:
        """Detect position error spikes.
        
        Args:
            run: RunData instance
            
        Returns:
            True if position error spike detected
        """
        if not run.is_valid or run.time_series_metrics is None or self.global_pos_error_stats is None:
            return False
        
        threshold = (self.global_pos_error_stats['mean'] + 
                    self.pos_error_sigma * self.global_pos_error_stats['std'])
        errors = run.time_series_metrics['pos_error'].values
        above_threshold = errors > threshold
        
        # Check for consecutive frames above threshold
        for i in range(len(above_threshold) - self.consecutive_frames + 1):
            if all(above_threshold[i:i+self.consecutive_frames]):
                return True
        return False
    
    def detect_stuck(self, run: RunData, velocity_threshold: float = 0.01, 
                     duration_threshold: float = 5.0) -> bool:
        """Detect if robot got stuck.
        
        Args:
            run: RunData instance
            velocity_threshold: Velocity below which robot is considered stuck
            duration_threshold: Minimum duration to be considered stuck (seconds)
            
        Returns:
            True if stuck condition detected
        """
        if not run.is_valid or run.time_series_metrics is None:
            return False
        
        ts = run.time_series_metrics
        stuck_mask = ts['linear_vel'] < velocity_threshold
        
        start = None
        for i, is_stuck in enumerate(stuck_mask):
            if is_stuck and start is None:
                start = ts['timestamp'].iloc[i]
            elif not is_stuck and start is not None:
                duration = ts['timestamp'].iloc[i] - start
                if duration > duration_threshold:
                    return True
                start = None
        
        return False
    
    def detect_high_amcl_uncertainty(self, run: RunData, threshold: float = 0.5) -> bool:
        """Detect high localization uncertainty from AMCL.
        
        Args:
            run: RunData instance
            threshold: Uncertainty threshold
            
        Returns:
            True if high uncertainty detected
        """
        if run.metrics is None:
            return False
        return run.metrics.mean_amcl_uncertainty > threshold
    
    def detect_high_yaw_error(self, run: RunData, threshold: float = 0.5) -> bool:
        """Detect high yaw error.
        
        Args:
            run: RunData instance
            threshold: Yaw error threshold (radians)
            
        Returns:
            True if high yaw error detected
        """
        if run.metrics is None:
            return False
        return run.metrics.mean_yaw_error > threshold
    
    def detect_path_inefficiency(self, run: RunData, threshold: float = 0.6) -> bool:
        """Detect path inefficiency.
        
        Args:
            run: RunData instance
            threshold: Path efficiency threshold
            
        Returns:
            True if path inefficiency detected
        """
        if run.metrics is None:
            return False
        return run.metrics.path_efficiency < threshold
    
    def detect_all(self, run: RunData) -> List[str]:
        """Detect all anomalies for a run.
        
        Args:
            run: RunData instance
            
        Returns:
            List of detected anomaly names
        """
        anomalies = []
        
        if self.detect_goal_failure(run):
            anomalies.append('goal_failure')
        if self.detect_position_error_spike(run):
            anomalies.append('position_error_spike')
        if self.detect_stuck(run):
            anomalies.append('stuck')
        if self.detect_high_amcl_uncertainty(run):
            anomalies.append('high_amcl_uncertainty')
        if self.detect_high_yaw_error(run):
            anomalies.append('high_yaw_error')
        if self.detect_path_inefficiency(run):
            anomalies.append('path_inefficiency')
        
        return anomalies


class MLAnomalyDetector:
    """ML-based anomaly detection using Isolation Forest."""
    
    def __init__(self, contamination: float = 0.1):
        """Initialize detector with contamination rate.
        
        Args:
            contamination: Expected proportion of anomalies
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def extract_features(self, run: RunData) -> Optional[np.ndarray]:
        """Extract features for ML model.
        
        Args:
            run: RunData instance
            
        Returns:
            Feature array or None if extraction fails
        """
        if not run.is_valid or run.metrics is None:
            return None
        
        m = run.metrics
        return np.array([
            m.mean_pos_error,
            m.rmse_pos,
            m.mean_yaw_error,
            m.executed_path_length,
            m.duration,
            m.path_efficiency,
            m.mean_linear_velocity,
            m.trajectory_smoothness,
            m.mean_amcl_uncertainty
        ])
    
    def fit(self, runs: List[RunData]) -> None:
        """Fit the model on run data.
        
        Args:
            runs: List of RunData instances
        """
        features = [self.extract_features(r) for r in runs if r.is_valid and r.metrics is not None]
        features = [f for f in features if f is not None]
        
        if len(features) < 10:
            return
        
        X = np.vstack(features)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
    
    def predict(self, run: RunData) -> bool:
        """Predict if run is anomalous.
        
        Args:
            run: RunData instance
            
        Returns:
            True if anomaly detected
        """
        if not self.is_fitted:
            return False
        
        features = self.extract_features(run)
        if features is None:
            return False
        
        X_scaled = self.scaler.transform(features.reshape(1, -1))
        return self.model.predict(X_scaled)[0] == -1
    
    def predict_score(self, run: RunData) -> float:
        """Get anomaly score for a run.
        
        Args:
            run: RunData instance
            
        Returns:
            Anomaly score (more negative = more anomalous)
        """
        if not self.is_fitted:
            return 0.0
        
        features = self.extract_features(run)
        if features is None:
            return 0.0
        
        X_scaled = self.scaler.transform(features.reshape(1, -1))
        return float(self.model.score_samples(X_scaled)[0])
