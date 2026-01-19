# Anomaly Detection Pipeline for Robot Navigation

A modular Python package for detecting and predicting anomalies in robot navigation scenarios. This pipeline supports two prediction modes:

1. **Scenario-based prediction**: Predict potential anomalies from scenario description, robot information, and environment configuration (without runtime logs)
2. **Log-based prediction**: Detect and reason about anomalies using actual run logs, CSV files, and scenario configuration

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Pipeline Architecture](#pipeline-architecture)
- [Usage](#usage)
  - [Training](#training)
  - [Scenario-based Prediction](#scenario-based-prediction)
  - [Log-based Prediction](#log-based-prediction)
  - [Visualization](#visualization)
- [Input/Output Formats](#inputoutput-formats)
- [Anomaly Types](#anomaly-types)
- [Features](#features)
- [Project Structure](#project-structure)

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
python3 -c "from anomaly_detection import AnomalyDetectionPipeline; print('Installation successful!')"
```

## Quick Start

```python
from anomaly_detection import AnomalyDetectionPipeline
from pathlib import Path

# Initialize the pipeline
pipeline = AnomalyDetectionPipeline(
    dataset_path=Path('ws25_aia_complete_data'),
    maps_path=Path('maps_details.json'),
    models_path=Path('models')
)

# Train models (first time only)
pipeline.train()

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
```

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ANOMALY DETECTION PIPELINE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Data Loading │───▶│ Preprocessing│───▶│   Metrics    │       │
│  │              │    │              │    │ Calculation  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                                       │                │
│         ▼                                       ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Feature    │◀───│   Anomaly    │◀───│  Rule-based  │       │
│  │  Extraction  │    │  Detection   │    │  Detection   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                                    │
│         ▼                   ▼                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Ensemble   │───▶│  Surrogate   │───▶│  FOL Rules   │       │
│  │   Models     │    │    Trees     │    │  & Explain   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Usage

### Command-Line Interface

The pipeline provides a CLI for all operations:

#### Training

Train the anomaly detection models on the dataset:

```bash
python3 -m anomaly_detection train \
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
python3 -m anomaly_detection predict-scenario \
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
python3 -m anomaly_detection predict-logs \
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

Generate all visualizations:

```bash
python3 -m anomaly_detection visualize \
    --dataset ws25_aia_complete_data \
    --maps maps_details.json \
    --output images
```

### Python API

```python
from anomaly_detection import AnomalyDetectionPipeline
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

# Generate visualizations
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

## Anomaly Types

| Anomaly | Description |
|---------|-------------|
| `goal_failure` | Navigation failed to reach the goal |
| `position_error_spike` | Localization error exceeded threshold |
| `stuck` | Robot was stationary for extended period |
| `high_amcl_uncertainty` | High localization uncertainty from AMCL |
| `high_yaw_error` | Large orientation error |
| `path_inefficiency` | Path was significantly longer than optimal |
| `Isolation Forest` | ML-detected anomalous behavior |

## Features

The pipeline extracts 27 features for anomaly prediction:

### Continuous Features (12)
- `min_wall_distance`: Distance to closest wall
- `min_door_distance`: Distance to closest door
- `door_width`: Width of nearest door
- `corridor_width`: Width of corridor
- `room_area`: Area of current room
- `clearance_ratio`: Wall clearance relative to robot size
- `goal_wall_distance`: Goal distance to wall
- `noise_level`: Laser noise standard deviation
- `min_obstacle_distance`: Distance to closest static obstacle
- `obstacle_clearance_ratio`: Obstacle clearance relative to robot size
- `num_obstacles`: Number of static obstacles
- `total_obstacle_area`: Total area of obstacles

### Boolean Features (15)
- `near_wall`, `at_door`, `door_too_narrow`
- `in_narrow_corridor`, `in_small_room`, `tight_clearance`
- `in_corridor`, `goal_near_wall`, `goal_through_door`
- `waypoint_in_tight_space`, `high_noise`, `min_door_narrow`
- `near_static_obstacle`, `tight_obstacle_clearance`, `has_static_obstacles`

## Project Structure

```
assignment4/
├── anomaly_detection/           # Main package
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

1. **Anomaly Distribution** (`anomaly_distribution.png`): Frequency of each anomaly type by scenario category
2. **Surrogate Trees** (`surrogate_trees.png`): Decision tree visualizations for each anomaly type
3. **Feature Importance** (`surrogate_feature_importance.png`): Heatmap of feature importance by anomaly type
4. **Performance Summary** (`surrogate_tree_performance.png`): Heatmap of precision, recall, F1, and fidelity

Team 02 Assignment 4
