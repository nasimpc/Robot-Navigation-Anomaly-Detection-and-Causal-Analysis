# Team 02 - Final Project: Anomaly Detection and Causal Analysis Pipeline for Robot Navigation

This document presents a comprehensive end-to-end pipeline for anomaly detection and causal analysis in autonomous robot navigation. The pipeline integrates data processing, metric computation, anomaly detection, machine learning-based anomaly prediction, and First-Order Logic (FOL) rule derivation to provide interpretable insights into navigation Anomalies including failures. 

---

## Table of Contents

1. [Traceability of Requirements](#1-traceability-of-requirements)
2. [Data Understanding and Summarization](#2-data-understanding-and-summarization)
3. [Feature Identification and Extraction](#3-feature-identification-and-extraction)
4. [Metric Definition and Justification](#4-metric-definition-and-justification)
5. [Anomaly Detection Approach and Validation](#5-anomaly-detection-approach-and-validation)
6. [Causal Analysis and Root-Cause Identification](#6-causal-analysis-and-root-cause-identification)
7. [Discussion: Generalization, Challenges, and Insights](#7-discussion-generalization-challenges-and-insights)

---

## 1. Traceability of Requirements


| ID | Requirement | Design Decision | Implementation | Justification |
|----|-------------|-----------------|----------------|---------------|
| R1 | Quatify localization and navigation perfomance (selection of metrics) | Defined 8 perfomance metrics | `MetricCalculator` | Metrics capture accuracy, efficiency, and belief distinctively to cover different failure modes |
| R2 | Based on metrics, single source anomaly ditection (algorithms for anomalies)|  Defined 8 single rule based anomaly detectors | `RuleBasedAnomalyDetector` | Explains specific physical violations (e.g., collisions, stops) based on domain thresholds |
| R3 | Based on metrics, multiple source anomaly ditection (algorithms for anomalies)| Defined a isolation forest anomaly detector that detect anomalies based on all 8 metrics| `MLAnomalyDetector` | Captures non-linear relationships and subtle deviations missed by single-metric rules |
| R4 | Extract interpretable FOL rules (causal reasoning) | Ensemble model training->Surrogate tree distillation->FOL rule extraction| `EnsembleAnomalyPredictor`,`SurrogateTreeExtractor` | Combines high predictive accuracy of ensemble models with the interpretability of logic rules |


---

## 2. Data Understanding and Summarization

### 2.1 Dataset Overview

The dataset `ws25_aia_complete_data` contains simulation runs of a TurtleBot4 robot navigating through various indoor environments.

| Property | Value |
|----------|-------|
| **Total Scenarios** | 100 directories |
| **Runs per Scenario** | 3 (labeled 0, 1, 2) |
| **Total Runs** | ~300 navigation experiments |
| **Environment Types** | door-width, door-size, room-size, hallway-window |
| **Robot Platform** | TurtleBot4 (0.22m diameter) |

### 2.2 File Formats and Contents

Each run directory contains the following files:

| File | Format | Content | Size Range |
|------|--------|---------|------------|
| **poses.csv** | CSV | Robot pose trajectories (ground truth + estimated) | ~500KB |
| **behaviors.csv** | CSV | Navigation behavior tree execution logs | ~200KB |
| **rosbag2.csv** | CSV | ROS2 bag data including AMCL localization | ~2-3MB |
| **scenario.config** | YAML | Scenario configuration (goals, start pose, sensor params) | ~500B |
| **run.yaml** | YAML | Run metadata (IDs, timestamps) | ~150B |
| **logs/** | Directory | ROS2 node logs (system.log, component logs) | ~200KB-1MB |
| **capture.webm** | WebM | Video recording of simulation | ~1.5MB |

### 2.3 Sensor Logs Structure

#### 2.3.1 poses.csv Schema
```
frame, timestamp, position.x, position.y, position.z, 
orientation.roll, orientation.pitch, orientation.yaw
```
- **Frames**: `nav2_turtlebot4_base_link_gt` (ground truth), `base_link` (estimated)
- **Sampling Rate**: ~30-50 Hz

#### 2.3.2 behaviors.csv Schema
```
timestamp, behavior_name, status_name, ...
```
- **Key Behaviors**: `nav_through_poses` (main navigation task)
- **Status Values**: `SUCCESS`, `FAILURE`, `RUNNING`

#### 2.3.3 rosbag2.csv Key Topics
```
timestamp, topic, message_type, pose.pose.position.x/y, 
pose.pose.orientation.w/x/y/z, pose.covariance
```
- **AMCL Topic**: `/amcl_pose` - Provides localization uncertainty via 6x6 covariance matrix
- **TF Topic**: `/tf` - Transform tree data

### 2.4 Scenario Configuration Structure

```yaml
test_scenario:
  goal_poses:              # List of target waypoints
    - position: {x, y}
      orientation: {yaw}
  start_pose:              # Initial robot position
    position: {x, y}
    orientation: {yaw}
  laserscan_gaussian_noise_std_deviation: 0.02-0.1  # Sensor noise level
  laserscan_random_drop_percentage: 0.0-0.2         # Sensor dropout rate
  map_file: path/to/map.yaml                        # Environment map
  static_objects: [...]                              # Optional obstacles
```

### 2.5 Scenario Category Distribution

| Category | Scenario Count | Total Runs | Description |
|----------|----------------|------------|-------------|
| door-width | 5 | 15 | Narrow door passages (0.3-0.47m) |
| door-size | 35 | 105 | Standard door width (0.5m) |
| hallway-window | 40 | 120 | Hallway with window features |
| room-size | 20 | 60 | Small room constraints (<50m²) |

### 2.6 Statistical Overview

Based on analysis of the complete dataset (300 runs):

#### 2.6.2 Key Metrics by Environment

| Scenario Type | Total Runs | Successes | Success Rate | Anomaly Rate |
|---------------|------------|-----------|--------------|--------------|
| **door-width** | 15 | 0 | 0% | 100% |
| **door-size** | 105 | 41 | 39% | 61% |
| **hallway-window** | 120 | 65 | 54% | 46% |
| **room-size** | 60 | 35 | 58% | 42% |
| **Global** | **300** | **141** | **47%** | **53%** |

#### 2.6.3 Performance Aggregates

| Statistic | Value | Notes |
|-----------|-------|-------|
| **Mean Duration** | ~175 seconds | Derived from 50Hz sampling |
| **Valid Runs** | 300 (100%) | All CSV logs valid (>1.5KB) |
| **Position Error** | 0.05-0.15m (Successes) | Diverges significantly in anomalies |
| **Path Efficiency** | 0.7-0.95 | For successful navigations |

---

## 3. Feature Identification and Extraction

### 3.1 Feature Categories

The pipeline extracts **27 features** organized into three categories aligned with environment–task–robot relations:

Below are the features we have selected for our causal analysis for anomaly prediction (we did not used feature for anomaly detection):

#### 3.1.1 Continuous Features (12)

| Feature | Source | Description | Unit | Justification (Relevance to causua analysis) |
|---------|--------|-------------|------|---------------------|
| `min_wall_distance` | Map geometry | Distance to nearest wall | meters | Low values correlate with collision/stuck anomalies due to limited maneuvering space |
| `min_door_distance` | Map geometry | Distance to nearest door | meters | Proximity to doors indicates navigation bottleneck zones where failures cluster |
| `door_width` | Map geometry | Width of nearest door | meters | Narrow doors (< 1.8× robot footprint) causally linked to passage failures |
| `corridor_width` | Map geometry | Width of corridor | meters | Narrow corridors restrict recovery maneuvers, causing stuck states |
| `room_area` | Map geometry | Area of current room | m² | Small rooms limit trajectory options, increasing goal failure probability |
| `clearance_ratio` | Computed | Wall distance / robot radius | ratio | Dimensionless safety margin; values <1.5 strongly predict collisions |
| `goal_wall_distance` | Map geometry | Goal proximity to walls | meters | Goals near walls are harder to reach precisely, causing position errors |
| `noise_level` | Config | Laser noise std deviation | - | Higher noise degrades AMCL localization, directly causing uncertainty anomalies |
| `min_obstacle_distance` | Config | Distance to closest static obstacle | meters | Close obstacles require precise navigation; failures correlate with <0.5m |
| `obstacle_clearance_ratio` | Computed | Obstacle distance / robot radius | ratio | Low ratios indicate tight obstacle clearance, predicting path inefficiency |
| `num_obstacles` | Config | Count of static obstacles | count | More obstacles increase planning complexity and anomaly likelihood |
| `total_obstacle_area` | Config | Sum of obstacle footprints | m² | Large total area reduces navigable space, correlating with stuck/failure |

#### 3.1.2 Boolean Predicates (15)

| Predicate | Condition | Justification (Relevance to causua analysis) |
|-----------|-----------|---------------------|
| `near_wall` | wall_dist < 1.5 × footprint | Direct spatial precondition for collision-type anomalies |
| `at_door` | door_dist < 0.5m | Doorway traversal is a known failure mode in Nav2; causal bottleneck |
| `door_too_narrow` | door_width < 1.8 × footprint | Physical constraint makes passage geometrically infeasible |
| `in_narrow_corridor` | corridor_width < 3 × footprint | Limits rotational recovery, causally linked to stuck states |
| `in_small_room` | room_area < 5.0 m² | Constrained turning radius prevents goal alignment |
| `tight_clearance` | wall_dist < 1.2 × footprint | Imminent collision zone; strong causal predictor |
| `in_corridor` | Current space is corridor | Corridors have restricted escape paths; context for stuck/failure |
| `goal_near_wall` | goal_wall_dist < footprint | Goal unreachable if robot cannot approach due to collision avoidance |
| `goal_through_door` | Path crosses door | Multi-step task complexity increases failure probability |
| `waypoint_in_tight_space` | Goal in confined area | Combines spatial constraints; composite causal factor |
| `high_noise` | noise > 0.05 | Sensor degradation directly causes localization uncertainty |
| `min_door_narrow` | Narrowest door < 1.8 × footprint | Map-level traversability constraint; global failure predictor |
| `near_static_obstacle` | obstacle_dist < 0.5m | Close obstacles require reactive avoidance, increasing failure risk |
| `tight_obstacle_clearance` | obstacle_dist < 1.5 × footprint | Marginal clearance predicts path inefficiency and collisions |
| `has_static_obstacles` | obstacles present | Presence of obstacles increases scenario complexity overall |

### 3.2 Feature Extraction Pipeline

```
ScenarioConfig + MapGeometry + CSVs
            ↓
    FeatureExtractor.extract_features(run)
            ↓
    27-dimensional feature vector
            ↓
    Feature Matrix X (n_runs × 27)
```

---

## 4. Perfomance Metric Definition and Justification

We used metrics solely for the detection of anomalies and not for prediction.

#### Localization accuracy (position)
1. **mean_pos_error** *(meters, m)*  
   - **Definition:** Average Euclidean distance between estimated and ground-truth positions.  
   - **Computed as:** mean of `sqrt((est_x-gt_x)^2 + (est_y-gt_y)^2)` over all synced timestamps.  
   - **Interpretation:** Lower is better.
   - **Anomaly Detection Justification:** Used to detect `position_error_spike`. When error exceeds μ + 3σ for ≥3 consecutive frames, it indicates localization failure—the robot has "lost" its position estimate.

2. **rmse_pos** *(m)*  
   - **Definition:** Root mean square of position error (penalizes large errors more than mean).  
   - **Computed as:** `sqrt(mean(pos_error^2))`.  
   - **Interpretation:** Lower is better; sensitive to spikes.
   - **Anomaly Detection Justification:** Used as a feature in Isolation Forest ML detector. High RMSE indicates persistent localization degradation.

#### Localization accuracy (orientation)
3. **mean_yaw_error** *(radians, rad)*  
   - **Definition:** Average absolute yaw difference between estimate and ground truth.  
   - **Computed as:** mean of `abs(wrap_to_pi(est_yaw - gt_yaw))`.  
   - **Interpretation:** Lower is better.
   - **Anomaly Detection Justification:** Used to detect `high_yaw_error` (threshold: >0.5 rad ≈ 29°). High yaw error indicates orientation drift due to sensor issues.

#### Path geometry & efficiency

4. **path_efficiency** *(unitless ratio)*  
   - **Definition:** How direct the executed motion is relative to ground truth.  
   - **Computed as:** `gt_path / executed_path` (0 if executed length is 0).  
   - **Interpretation:** Closer to 1 is better; low values suggest detours.
   - **Anomaly Detection Justification:** Used to detect `path_inefficiency` (threshold: <0.6). Efficiency below 60% indicates significant detours or suboptimal planning.

#### Kinematics & smoothness
5. **mean_linear_velocity** *(m/s)*  
   - **Definition:** Mean translational speed derived from estimated motion.  
   - **Computed as:** mean of `sqrt(dx^2+dy^2)/dt`.  
   - **Interpretation:** Context for speed-vs-accuracy tradeoffs.
   - **Anomaly Detection Justification:** Used to detect `stuck` anomaly. Velocity <0.01 m/s for >5 seconds indicates the robot is physically immobile.

6. **trajectory_smoothness** *(rad/s²)*  
   - **Definition:** Average absolute angular acceleration magnitude.  
   - **Computed as:** mean of `abs(diff(angular_vel)/dt)` (with safe handling for zero dt).  
   - **Interpretation:** Lower is smoother; higher implies oscillation/jerky turning.
   - **Anomaly Detection Justification:** Used as feature in Isolation Forest. High values indicate erratic rotational behavior from recovery maneuvers.

7. **duration** *(seconds, s)*  
   - **Definition:** Total time span of the synced segment.  
   - **Computed as:** `timestamp_last - timestamp_first`.
   - **Anomaly Detection Justification:** Combined with behavior outcome to detect `goal_failure`. Extended duration with FAILURE status indicates navigation timeout.

#### AMCL uncertainty 
8. **mean_amcl_uncertainty** *(meters-equivalent, m)*  
   - **Definition:** Average positional uncertainty proxy from AMCL covariance.  
   - **Computed as:** for each covariance `cov`, use `sqrt(cov[0,0] + cov[1,1])`, then take the mean.  
   - **Interpretation:** Higher values indicate less confident localization.
   - **Anomaly Detection Justification:** Used to detect `high_amcl_uncertainty` (threshold: >0.5m). This **novel metric** captures the robot's self-reported localization confidence and provides early warning of potential failures.

---

## 5. Anomaly Detection Approach and Validation


### 1. Rule-based anomalies — `RuleBasedAnomalyDetector`

1. **goal_failure**  
   - **Triggered when:** behavior outcome indicates navigation ended in failure (`outcome == 'failure'`).  
   - **Justification:** Separates explicit task failure from degraded-but-successful runs.

2. **no_initiation**  
   - **Triggered when:** no behavior data or no navigation behavior present (`outcome in {'no_data','no_navigation'}`).  
   - **Justification:** Captures missing logs / navigation never started.

3. **position_error_spike**  
   - **Triggered when:** position error exceeds a global threshold for *K* consecutive frames.  
   - **Threshold:** `global_mean + pos_error_sigma * global_std` computed across all valid runs’ `pos_error`.  
   - **Consecutive requirement:** `consecutive_frames` (default 3).  
   - **Justification:** Detects sustained localization divergence, not single-point noise.

4. **stuck**  
   - **Triggered when:** `linear_vel < velocity_threshold` continuously for longer than `duration_threshold`.  
   - **Defaults:** `velocity_threshold=0.01 m/s`, `duration_threshold=5.0 s`.  
   - **Justification:** Detects immobilization / inability to progress.

5. **high_amcl_uncertainty**  
   - **Triggered when:** `mean_amcl_uncertainty > threshold`.  
   - **Default:** `threshold=0.5` (using the notebook’s uncertainty proxy).  
   - **Justification:** Flags runs where AMCL reports persistently poor confidence.

6. **high_yaw_error**  
   - **Triggered when:** `mean_yaw_error > 0.5 rad`.  
   - **Justification:** Detects runs with poor orientation tracking.

7. **path_inefficiency**  
   - **Triggered when:** `path_efficiency < 0.6`.  
   - **Justification:** Flags excessive detours or "wandering" behavior.

8. **oscillation**  
   - **Triggered when:** `trajectory_smoothness > 2.0`.  
   - **Justification:** Detects jerky motion or control instability.


### 2. Isolation Forest — `MLAnomalyDetector` (ML Based Anomaly)

9. **Isolation Forest**  
   - **Triggered when:** Isolation Forest predicts the run as an outlier (`-1`) in standardized feature space.  
   - **Features used (exact list, in order):**  
     1) mean_pos_error  
     2) rmse_pos  
     4) mean_yaw_error  
     5) duration  
     6) path_efficiency  
     7) mean_linear_velocity  
     8) trajectory_smoothness  
     9) mean_amcl_uncertainty  

   - **Note:** Model is only fitted if enough valid runs exist (guarded in code).  
   - **Justification:** Captures multi-metric abnormal patterns that rules may miss.

### 3. Validation Methodology

To validate the robustness of our anomaly detection system, we employed a two-tier evaluation strategy:

1.  **Rule-Based Validation:**
    *   **Method:** Manual inspection of 50 sampled runs (25 success, 25 failure) to verify that rules triggered correctly against ground truth observations (video replay).
    *   **Metric:** False Positive Rate (FPR) and False Negative Rate (FNR) for each rule type.
    *   **Result:** Rules achieved high precision for `goal_failure` and `stuck` (F1 > 0.9), but `position_error_spike` required tuning of the `sigma` threshold to 3.0 to minimize false alarms on noisy-but-safe runs.

2.  **ML-Based Validation:**
    *   **Method:** 5-Fold Cross-Validation on the `IsolationForest` model.
    *   **Procedure:** The dataset was split into 5 stratified folds. For each fold, the model was trained on 80% of data (unsupervised) and evaluated on the remaining 20% against the composite ground truth (union of all rule-based labels).
    *   **Performance:** achieved an average **Precision of 0.82** and **Recall of 0.76**, confirming that the ML detector effectively correlates with known physical anomalies while capturing additional subtle failure modes.

## 6. Causal Analysis and Root-Cause Identification

### 6.1 Causal Framework

Our approach uses **environment–task–robot relations** to identify anomaly causes:

```
Environment Features          Task Features           Robot Features
├─ door_width                ├─ goal_poses           ├─ footprint
├─ corridor_width            ├─ path_length          ├─ sensor_noise
├─ room_area                 ├─ door_crossings       └─ AMCL precision
└─ obstacle_layout           └─ waypoint_count
         ↘                         ↓                       ↙
                    ┌───────────────────────────┐
                    │   Causal Feature Space    │
                    │   (27 features)           │
                    └─────────────┬─────────────┘
                                  ↓
                    ┌───────────────────────────┐
                    │   Surrogate Tree          │
                    │   (distilled rules)       │
                    └─────────────┬─────────────┘
                                  ↓
                    ┌───────────────────────────┐
                    │   FOL Causal Rules        │
                    └───────────────────────────┘
```

### 6.2 Surrogate Tree Approach

#### 6.2.1 Methodology
1. **Train Ensemble**: Use Random Forest/Gradient Boosting for high accuracy
2. **Distill to Surrogate**: Train interpretable decision tree on ensemble predictions
3. **Extract Rules**: Convert tree paths to FOL expressions

#### 6.2.2 Justification
- **Fidelity**: Surrogate tree mimics ensemble decisions (>90% agreement)
- **Interpretability**: Simple decision rules are human-readable
- **Causal Validity**: Rules correspond to physical/geometric constraints

### 6.3 FOL Rule Representation

#### 6.3.1 Formal Syntax

```
∀t : condition₁(t) ∧ condition₂(t) ∧ ... ⇒ Anomaly(t)
```

Where conditions are:
- Boolean predicates: `near_wall(t)`, `door_too_narrow(t)`
- Threshold conditions: `door_width(t) ≤ 0.396`


### 6.4 Causal Assumptions 

| Assumption | Justification |
|------------|---------------|
| Features precede anomalies | Features from scenario config, anomalies from execution |
| Environment causes failures | Door widths, corridors physically constrain navigation |
| Selected Features are sufficient | 27 features capture relevant causal factors |

### 6.5 Methodology to Validate Causal Explanations

We validate causal explanations at two levels: **(i)** whether the surrogate tree faithfully approximates the high-performing ensemble (model-level explanation fidelity), and **(ii)** whether the extracted FOL rules are accurate and applicable across scenarios (rule-level explanation quality).

1. **Protocol (teacher–student distillation)**
   - **Teacher model:** best-performing ensemble predictor per anomaly type (Random Forest / Gradient Boosting / Decision Tree).
   - **Student/explainer:** depth-limited surrogate decision tree trained to mimic the teacher predictions.
   - **Rule extraction:** each positive leaf-to-root path is converted to a FOL rule; rule quality is evaluated using confusion counts on the dataset.

2. **Fidelity to the ensemble**
   - **Metric:** agreement between teacher and surrogate predictions.
   - **Computation:** `fidelity = Accuracy(y_teacher, y_surrogate)` (higher is better).
   - **Purpose:** ensures the explanations represent the *same decision logic* as the accurate model.

3. **Rule coverage and correctness**
   - For each extracted rule, we compute:
     - **Coverage:** fraction of runs satisfying the rule conditions: `coverage = n_matches / N`.
     - **Precision:** `TP / (TP + FP)` computed over runs matching the rule.
     - **Recall:** `TP / (TP + FN)` with FN counted as positives not covered by the rule.
   - **Mean Rule Coverage** is computed across the top-ranked rules (sorted by confidence/support) to quantify how much of the anomaly set is explained by a compact rule set.

4. **Cross-scenario applicability (generalization)**
   - **Method:** evaluate rule triggers across different scenario directories to reduce overfitting to a single map instance.
   - **Computation:** for each rule, count distinct scenarios where it matches at least one run and report
     `scenario_frequency = (#scenarios_hit / #total_scenarios)`.
   - **Interpretation:** high scenario frequency indicates the rule captures a general geometric/sensor cause rather than a scenario-specific artifact.

5. **Sanity checks**
   - We additionally verify that the dominant rule antecedents correspond to physically meaningful constraints (e.g., door width vs footprint, clearance ratios, high noise) and are consistent with observed failure modes in the runs.
---

## 7. Discussion: Generalization, Challenges, and Insights

### 7.1 Generalization and Scalability

#### 7.1.1 Generalization to Different Robots

| Adaptation | Required Changes | Difficulty |
|------------|------------------|------------|
| Different footprint | Update `ROBOT_FOOTPRINT` constant | Low |
| Different sensors | Adjust noise thresholds, add sensor-specific metrics | Medium |
| Different kinematics | Modify smoothness/velocity thresholds | Medium |
| Aerial robots | Add altitude features, 3D geometry | High |

**Key Design for Generalization:**
- Parameters (footprint, thresholds) are configurable
- Features are robot-agnostic (relative clearances, not absolute)
- FOL rules are derived from Applaying ML models on avilable data based on 27 input features.

#### 7.1.2 Generalization to Different Environments

| Environment Type | Required Data Variations |
|------------------|-------------------------|
| Outdoor navigation | Map geometry without walls, GPS-based localization |
| Multi-floor buildings | Elevator features, floor transitions |
| Dynamic obstacles | Real-time obstacle tracking, prediction features |
| Unstructured environments | Terrain features, traversability metrics |

#### 7.1.3 Required Data Variations for Generalization

To support generalization, the dataset should include:

1. **Diverse Robot Platforms**: Different sizes (0.1m - 1.0m footprint)
2. **Environment Variety**: Indoor, outdoor, structured, unstructured
3. **Sensor Modalities**: LiDAR, cameras, IMU, GPS
4. **Failure Modes**: Representative samples of each anomaly type
5. **Scale**: Minimum 300 scenarios for robust model training. The more scenarios and runs better quality FOL causual rules.

### 7.2 Challenges Encountered

| Challenge | Description | Solution |
|-----------|-------------|----------|
|**Small dataset** |Data set only contain 100 scenarios, and 4 evironment|larger and more divese dataset|
| **Class Imbalance** | Some anomalies are rare (<5% of runs) | Stratified sampling, class weights |
| **Feature Engineering** | Selecting relevant features | Domain expertise + feature importance |
| **Threshold Selection** | Determining optimal thresholds for rule-based detection | Statistical analysis (3σ), cross-validation |
| **Surrogate Fidelity** | Balancing interpretability vs accuracy | Depth-limited trees, fidelity monitoring |



### 7.3 Unique Insights

#### 7.3.1 Methodological and Technical Insights (Important)

1. **Better quality rules with just scenario information**: In case of many anomalies it showed better predictive power and generalization (F1 score and other metrices) when just used scenario description, robot information, and environment JSON file for deriving FOL rules instead of also including more informative logs, CSV files.
2. **Surrogate Distillation**: Ensemble models achieve higher accuracy, but surrogate trees provide 90%+ fidelity with full interpretability. Surrogate trees where enven simpler than simple decision trees yet showed better results (F1, confusion metrics)

#### 7.3.2 Domain  and Navigaion Insights

1. “Geometry dominates” (eg: obstacle clearance ratios, door distance/door width, wall distances) most failures.
2. Corridors are a high-risk context for goal failure (log-based).
3. Narrow/near-door situations are a recurring hazard zone across multiple failure modes.
4. Be cautious with “perfect” confidence and perfomance (F1) on tiny supports

---

*Team 02 Assignment 04*
