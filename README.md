# Anomaly Detection Pipeline for Robot Navigation

A modular Python package for detecting and predicting anomalies in robot navigation scenarios. This pipeline supports two prediction modes:

1. **Scenario-based prediction**: Predict potential anomalies from scenario description, robot information, and environment configuration (without runtime logs)
2. **Log-based prediction**: Detect and reason about anomalies using actual run logs, CSV files, and scenario configuration

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
# Clone or navigate to the project directory
cd assignment4

# Install required packages
pip install -r requirements.txt
```

### Verify Installation

```bash
python3 -c "from anomaly_detection_and_prediction import AnomalyDetectionPipeline; print('Installation successful!')"
```


## Command-Line Interface

The pipeline provides a CLI for all operations:

#### Training

Train the anomaly detection models on the dataset:

```bash
python3 -m anomaly_detection_and_prediction train \
    --dataset ws25_aia_complete_data \
    --maps maps_details.json \
    --models models
```

Options:
- `--dataset`: Path to dataset directory (default: `ws25_aia_complete_data`)
- `--maps`: Path to maps_details.json (default: `maps_details.json`)
- `--models`: Directory to save trained models (default: `models`)
- `--max-scenarios`: Limit number of scenarios for faster training
- `--quiet`: Suppress progress output

#### Scenario-based Prediction

Predict potential anomalies from scenario description only:

```bash
python3 -m anomaly_detection_and_prediction predict-scenario \
    --scenario ws25_aia_complete_data/small-dataset-maps-0-3-door-width-1f1-1/0/scenario.config \
    --env maps_details.json \
```

Options:
- `--scenario`: Path to scenario.config file (required)
- `--env`: Path to maps_details.json (default: `maps_details.json`)
- `--models`: Directory containing trained models (default: `models`)
- `--output`: Output JSON file for predictions (optional, prints to console if not specified)

#### Log-based Prediction

Detect anomalies from actual run logs:

```bash
python3 -m anomaly_detection_and_prediction predict-logs \
    --run ws25_aia_complete_data/small-dataset-maps-0-3-door-width-1f1-1/0 \
    --env maps_details.json 
```

Options:
- `--run`: Path to run directory containing poses.csv, behaviors.csv, rosbag2.csv (required)
- `--scenario`: Path to scenario.config (optional, looks in run directory)
- `--env`: Path to maps_details.json (default: `maps_details.json`)
- `--models`: Directory containing trained models (default: `models`)
- `--output`: Output JSON file for predictions (optional)

#### Visualization
visualizations representing available data (anomaly by category and runs per category) is generated when running the command for training. For generating all other visualizations:

```bash
python3 -m anomaly_detection_and_prediction visualize \
    --dataset ws25_aia_complete_data \
    --maps maps_details.json \
    --output images
```

## Python API

```python
from anomaly_detection_and_prediction import AnomalyDetectionPipeline
from pathlib import Path

# Initialize pipeline
pipeline = AnomalyDetectionPipeline(
    dataset_path=Path('ws25_aia_complete_data'),
    maps_path=Path('maps_details.json'),
    models_path=Path('models'),
    images_path=Path('images')
)

# Train models
results = pipeline.train(max_scenarios=50, verbose=True)
print(f"Trained models: {results['models_trained']}")

# Scenario-based prediction
result = pipeline.predict_scenario(
    scenario_config_path=Path('ws25_aia_complete_data/small-dataset-maps-0-3-door-width-1f1-1/0/scenario.config')
)
print(f"Predicted anomalies: {result.predicted_anomalies}")

# Log-based prediction
result = pipeline.predict_logs(
    run_path=Path('ws25_aia_complete_data/small-dataset-maps-0-3-door-width-1f1-1/0')
)
print(f"Detected anomalies: {result.predicted_anomalies}")

# Generate visualizations (all visualizations except visualizations representing avilable data)
pipeline.generate_visualizations()

```

## Input/Output Formats

### Input Files

#### scenario.config (YAML)
```yaml
test_scenario:
  goal_poses:
    - position: {x: 2.0, y: 3.0, z: 0.0}
      orientation: {yaw: 0.0}
  start_pose:
    position: {x: 0.0, y: 0.0, z: 0.0}
    orientation: {yaw: 0.0}
  laserscan_gaussian_noise_std_deviation: 0.02
  laserscan_random_drop_percentage: 0.0
  map_file: map.yaml
  static_objects: []
```

#### maps_details.json
Environment geometry with room polygons and door locations.

#### Run Directory Structure
```
run_directory/
├── poses.csv          # Robot pose data (timestamp, position, orientation)
├── behaviors.csv      # Navigation behavior status
├── rosbag2.csv        # ROS bag data with AMCL poses
└── scenario.config    # Scenario configuration
```

### Output Format

Prediction results are returned as JSON:

```json
{
  "scenario_name": "small-dataset-maps-0-3-door-width-1f1-1",
  "run_id": 0,
  "mode": "log",
  "predicted_anomalies": ["goal_failure"],
  "anomaly_probabilities": {
    "goal_failure": 0.85,
    "position_error_spike": 0.23,
    "stuck": 0.12
  },
  "explanations": {
    "goal_failure": "IF door width ≤ 0.396 AND robot is door too narrow THEN goal_failure"
  },
  "fol_rules": {
    "goal_failure": "∀t : door_width(t) ≤ 0.396 ∧ door_too_narrow(t) ⇒ goal_failure"
  },
  "metrics": {
    "mean_pos_error": 0.0234,
    "rmse_pos": 0.0312,
    "path_efficiency": 0.89,
    "duration": 45.2
  },
  "confidence": 0.85
}
```

## Project Structure

```
assignment4/
├── anomaly_detection_and_prediction/           # Main package
│   ├── __init__.py             # Package exports
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Configuration constants
│   ├── data_structures.py      # Data classes
│   ├── data_loading.py         # Dataset loading
│   ├── preprocessing.py        # Data preprocessing
│   ├── metrics.py              # Metric computation
│   ├── anomaly_detection.py    # Rule-based and ML detectors
│   ├── feature_engineering.py  # Feature extraction
│   ├── models.py               # Ensemble and surrogate models
│   ├── visualization.py        # Plotting functions
│   └── pipeline.py             # Main pipeline orchestration
├── ws25_aia_complete_data/     # Dataset directory
├── maps_details.json           # Environment geometry
├── models/                     # Trained model artifacts
├── images/                     # Generated visualizations
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Visualizations

The pipeline generates the following visualizations:

1. **Anomaly Distribution (Generated during Training)** (`anomaly_by_category.png`): Frequency of each anomaly type grouped by scenario category.
2. **Dataset Overview (Generated during Training)** (`runs_per_category.png`): Distribution of total runs across different scenario categories.
3. **Surrogate Trees (Generated via Visualize Command)** (`surrogate_trees.png`): Visualized decision trees explaining the logic for each anomaly type. Two visualizations, one for cenario-based prediction and one for log-based prediction.
4. **Feature Importance (Generated via Visualize Command)** (`surrogate_feature_importance.png`): Heatmap identifying which metrics are most predictive for specific anomalies.Two visualizations, one for cenario-based prediction and one for log-based prediction.
5. **Performance Summary (Generated via Visualize Command)** (`surrogate_tree_performance.png`): Heatmap showing Precision, Recall, F1-score, and Model Fidelity.Two visualizations, one for cenario-based prediction and one for log-based prediction.

---

Team 02 Assignment 4
