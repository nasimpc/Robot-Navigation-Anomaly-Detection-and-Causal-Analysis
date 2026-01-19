"""
Data structures for the anomaly detection pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
import pandas as pd


@dataclass
class StaticObject:
    """Static obstacle in the environment."""
    entity_name: str
    position: Tuple[float, float, float]  # x, y, z
    orientation_yaw: float
    dimensions: Tuple[float, float, float]  # width, length, height


@dataclass
class ScenarioConfig:
    """Scenario configuration parameters."""
    goal_poses: List[Dict]
    start_pose: Dict
    laser_noise_std: float
    laser_drop_pct: float
    map_file: str
    static_objects: List['StaticObject'] = field(default_factory=list)


@dataclass
class AMCLData:
    """AMCL localization data from rosbag2.csv."""
    timestamps: np.ndarray  # seconds
    positions: np.ndarray   # (N, 3) x, y, z
    orientations: np.ndarray  # (N, 4) w, x, y, z quaternion
    covariances: List[np.ndarray]  # List of 6x6 covariance matrices


@dataclass
class RunMetrics:
    """Computed metrics for a single run."""
    mean_pos_error: float = 0.0
    rmse_pos: float = 0.0
    mean_yaw_error: float = 0.0
    executed_path_length: float = 0.0
    path_efficiency: float = 0.0
    mean_linear_velocity: float = 0.0
    mean_angular_velocity: float = 0.0
    trajectory_smoothness: float = 0.0
    duration: float = 0.0
    mean_amcl_uncertainty: float = 0.0


@dataclass
class RunData:
    """Complete data for a single simulation run."""
    scenario_name: str
    run_id: int
    run_path: Path
    scenario_category: str = ''
    outcome: str = 'unknown'
    poses_df: Optional[pd.DataFrame] = None
    behaviors_df: Optional[pd.DataFrame] = None
    rosbag_df: Optional[pd.DataFrame] = None  # rosbag2.csv data
    amcl_data: Optional[AMCLData] = None  # Parsed AMCL data
    config: Optional[ScenarioConfig] = None
    synced_data: Optional[pd.DataFrame] = None
    metrics: Optional[RunMetrics] = None
    anomalies: List[str] = field(default_factory=list)
    time_series_metrics: Optional[pd.DataFrame] = None
    is_valid: bool = True
    error_msg: str = ''


@dataclass
class PredictionResult:
    """Result of anomaly prediction."""
    scenario_name: str
    run_id: Optional[int] = None
    mode: str = 'scenario'  # 'scenario' or 'log'
    predicted_anomalies: List[str] = field(default_factory=list)
    anomaly_probabilities: Dict[str, float] = field(default_factory=dict)
    explanations: Dict[str, str] = field(default_factory=dict)
    fol_rules: Dict[str, str] = field(default_factory=dict)
    metrics: Optional[RunMetrics] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'scenario_name': self.scenario_name,
            'run_id': self.run_id,
            'mode': self.mode,
            'predicted_anomalies': self.predicted_anomalies,
            'anomaly_probabilities': self.anomaly_probabilities,
            'explanations': self.explanations,
            'fol_rules': self.fol_rules,
            'metrics': {
                'mean_pos_error': self.metrics.mean_pos_error,
                'rmse_pos': self.metrics.rmse_pos,
                'mean_yaw_error': self.metrics.mean_yaw_error,
                'path_efficiency': self.metrics.path_efficiency,
                'duration': self.metrics.duration,
                'mean_amcl_uncertainty': self.metrics.mean_amcl_uncertainty,
            } if self.metrics else None,
            'confidence': self.confidence
        }
