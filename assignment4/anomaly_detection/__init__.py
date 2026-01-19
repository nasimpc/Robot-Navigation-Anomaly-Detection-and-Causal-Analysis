"""
Anomaly Detection Pipeline for Robot Navigation

A modular Python package for detecting and predicting anomalies in robot navigation scenarios.
Supports two modes:
- Scenario-based prediction: Predict potential anomalies from scenario description
- Log-based prediction: Detect anomalies from actual run logs

"""

__version__ = "1.0.0"
__author__ = "Team 02"

from .config import (
    DATASET_PATH,
    IMAGES_PATH,
    MODELS_PATH,
    ROBOT_FOOTPRINT,
    ROBOT_RADIUS,
    SENSOR_HEIGHT,
    ANOM_LABELS,
)

from .data_structures import (
    StaticObject,
    ScenarioConfig,
    AMCLData,
    RunMetrics,
    RunData,
)

from .data_loading import DatasetLoader
from .preprocessing import DataPreprocessor
from .metrics import MetricCalculator
from .anomaly_detection import RuleBasedAnomalyDetector, MLAnomalyDetector
from .feature_engineering import MapGeometry, ComputableFunctions, AtomicRelations, FeatureExtractor
from .models import EnsembleAnomalyPredictor, SurrogateTreeExtractor
from .pipeline import AnomalyDetectionPipeline

__all__ = [
    # Version info
    "__version__",
    "__author__",
    # Config
    "DATASET_PATH",
    "IMAGES_PATH",
    "MODELS_PATH",
    "ROBOT_FOOTPRINT",
    "ROBOT_RADIUS",
    "SENSOR_HEIGHT",
    "ANOM_LABELS",
    # Data structures
    "StaticObject",
    "ScenarioConfig",
    "AMCLData",
    "RunMetrics",
    "RunData",
    # Core classes
    "DatasetLoader",
    "DataPreprocessor",
    "MetricCalculator",
    "RuleBasedAnomalyDetector",
    "MLAnomalyDetector",
    "MapGeometry",
    "ComputableFunctions",
    "AtomicRelations",
    "FeatureExtractor",
    "EnsembleAnomalyPredictor",
    "SurrogateTreeExtractor",
    "AnomalyDetectionPipeline",
]
