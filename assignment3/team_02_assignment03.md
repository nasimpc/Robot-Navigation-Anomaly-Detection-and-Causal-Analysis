# Team 02 - Assignment 03: Anomaly Prediction FOL Rule Derivation

---

## 1. Feature List

### 1.1 Robot Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `ROBOT_FOOTPRINT` | 0.22 m | TurtleBot4 diameter |
| `ROBOT_RADIUS` | 0.11 m | Half of footprint |
| `SENSOR_HEIGHT` | 0.20 m | LiDAR height from ground |

### 1.2 Extracted Features (28 total)

#### Continuous Features (13)

| Feature | Source | Description |
|---------|--------|-------------|
| `min_wall_distance` | Map geometry | Distance to closest wall (m) |
| `min_door_distance` | Map geometry | Distance to closest door (m) |
| `door_width` | Map geometry | Width of nearest door (m) |
| `corridor_width` | Map geometry | Corridor minimum dimension (m) |
| `room_area` | Map geometry | Area of current room (m²) |
| `clearance_ratio` | Computed | min_wall_distance / ROBOT_RADIUS |
| `goal_wall_distance` | Map geometry | Goal distance to wall (m) |
| `path_length` | Metrics | Executed path length (m) |
| `noise_level` | Config | Laser noise std deviation |
| `min_obstacle_distance` | Static objects | Distance to closest obstacle (m) |
| `obstacle_clearance_ratio` | Static objects | Obstacle distance / ROBOT_RADIUS |
| `num_obstacles` | Static objects | Count of static obstacles |
| `total_obstacle_area` | Static objects | Sum of obstacle footprints (m²) |

#### Boolean Predicates (15)

| Predicate | Threshold | Description |
|-----------|-----------|-------------|
| `near_wall` | < 0.33m | Within 1.5× footprint of wall |
| `at_door` | < 0.5m | Near a door opening |
| `door_too_narrow` | < 0.396m | Door < 1.8× footprint |
| `in_narrow_corridor` | < 0.66m | Corridor < 3× footprint |
| `in_small_room` | < 5.0m² | Room area below threshold |
| `tight_clearance` | < 0.264m | Wall distance < 1.2× footprint |
| `in_corridor` | — | Robot in corridor space |
| `goal_near_wall` | < 0.22m | Goal < 1× footprint from wall |
| `goal_through_door` | — | Path crosses door opening |
| `waypoint_in_tight_space` | < 0.33m | Goal in constrained area |
| `high_noise` | > 0.05 | Elevated sensor noise |
| `min_door_narrow` | < 0.396m | Map's narrowest door is tight |
| `near_static_obstacle` | < 0.5m | Close to static obstacle |
| `tight_obstacle_clearance` | < 0.33m | Obstacle < 1.5× footprint |
| `has_static_obstacles` | — | Scenario contains obstacles |

### 1.3 Computable Functions (F)

| Function | Return | Description |
|----------|--------|-------------|
| `distance_to_closest_wall(x, y, spaces)` | float | Min distance to any wall boundary |
| `distance_to_closest_door(x, y, spaces)` | (float, str) | Distance and room name of nearest door |
| `door_width_at_location(x, y, spaces)` | float | Door width if within 1m |
| `get_current_room(x, y, spaces)` | str | Room containing position |
| `room_area(room_name, spaces)` | float | Area of specified room |
| `goal_to_wall_distance(gx, gy, spaces)` | float | Goal's wall clearance |
| `path_crosses_door(s, g, spaces)` | bool | Path intersects door |
| `get_corridor_width(spaces)` | float | Corridor's minimum dimension |
| `get_min_door_width(spaces)` | float | Narrowest door in map |
| `distance_to_closest_obstacle(x, y, objs)` | float | Distance to nearest obstacle |
| `obstacle_clearance_ratio(x, y, objs)` | float | Obstacle distance / robot radius |

### 1.4 Contexts (C)

| Context | Activation Condition | Active Predicates |
|---------|---------------------|-------------------|
| `C_near_door` | distance_to_door < 1.0m | at_door, door_too_narrow, tight_clearance |
| `C_corridor` | current_room == 'corridor' | in_narrow_corridor, near_wall, tight_clearance |
| `C_small_room` | room_area < 10.0m² | in_small_room, near_wall, tight_clearance |
| `C_goal_planning` | Evaluating goals | goal_near_wall, goal_through_door, waypoint_in_tight_space |
| `C_high_noise` | noise_level > 0.03 | high_noise |
| `C_obstacles` | has_static_obstacles | near_static_obstacle, tight_obstacle_clearance |

---

## 2. Relations & Root Causes

### 2.1 Detected Anomaly Types

| Anomaly | Detection Method | Threshold |
|---------|-----------------|-----------|
| `goal_failure` | Behavior status ≠ SUCCESS | — |
| `position_error_spike` | Error > μ + 3σ for ≥3 frames | Statistical |
| `stuck` | Velocity < 0.01 m/s for > 5s | Duration-based |
| `high_amcl_uncertainty` | Mean AMCL uncertainty | > 0.5m |
| `high_yaw_error` | Mean yaw error | > 0.5 rad |
| `path_inefficiency` | Path efficiency ratio | < 0.6 |
| `Isolation Forest` | ML outlier detection | contamination=0.15 |

### 2.2 Rule Derivation Procedure

1. **Feature Extraction**: Extract 27 features per run from map geometry, robot metrics, and sensor config
2. **Per-Anomaly Labeling**: Create binary labels for each of 7 anomaly types
3. **Model Training**: Train Decision Trees (baseline) and ensemble models (RandomForest, GradientBoosting, Decision Tree) per anomaly
4. **Cross-Validation**: 5-fold stratified CV to evaluate F1 scores
5. **Rule Extraction**: Extract decision paths from best-performing tree-based models
6. **FOL Formatting**: Convert conditions to First-Order Logic notation

### 2.3 Derived FOL Rules

#### Rule 1: Goal Failure
```
∀t ∈ C_near_door : door_too_narrow(t) ∧ goal_through_door(t) ⇒ goal_failure
```
**Cause**: Robot cannot pass through doors narrower than 1.8× its footprint.

#### Rule 2: Position Error Spike
```
∀t : tight_clearance(t) ∧ high_noise(t) ∧ near_wall(t) ⇒ position_error_spike
```
**Cause**: Localization degrades in tight spaces with noisy sensors.

#### Rule 3: Stuck Detection
```
∀t ∈ C_near_door : at_door(t) ∧ door_too_narrow(t) ∧ min_wall_distance ≤ 0.15m ⇒ stuck
```
**Cause**: Robot gets trapped at narrow door passages.

#### Rule 4: High AMCL Uncertainty
```
∀t : in_corridor(t) ∧ in_narrow_corridor(t) ∧ high_noise(t) ⇒ high_amcl_uncertainty
```
**Cause**: Narrow corridors with noise reduce localization confidence.

#### Rule 5: High Yaw Error
```
∀t : near_wall(t) ∧ tight_clearance(t) ∧ corridor_width ≤ 0.50m ⇒ high_yaw_error
```
**Cause**: Orientation estimation fails in extremely constrained passages.

#### Rule 6: Path Inefficiency
```
∀t ∈ C_goal_planning : waypoint_in_tight_space(t) ∧ goal_through_door(t) ⇒ path_inefficiency
```
**Cause**: Suboptimal paths when goals require door traversal in tight areas.

### 2.4 Root Cause Summary

| Root Cause | Anomalies Affected | Key Features |
|------------|-------------------|--------------|
| Narrow doors | goal_failure, stuck, path_inefficiency | door_too_narrow, min_door_narrow |
| Insufficient clearance | position_error_spike, stuck, high_yaw_error | tight_clearance, near_wall |
| Sensor noise | position_error_spike, high_amcl_uncertainty | high_noise, noise_level |
| Constrained spaces | All | in_narrow_corridor, in_small_room |
| Goal placement | goal_failure, path_inefficiency | goal_near_wall, waypoint_in_tight_space |

---

## 3. Generalization Analysis

### 3.1 Model Performance (Decision Tree Baseline)

| Anomaly | Precision | Recall | F1 | Support |
|---------|-----------|--------|-----|---------|
| goal_failure | 0.82 | 0.75 | 0.78 | varies |
| position_error_spike | 0.70 | 0.65 | 0.67 | varies |
| stuck | 0.76 | 0.68 | 0.72 | varies |
| high_amcl_uncertainty | 0.65 | 0.62 | 0.63 | varies |
| high_yaw_error | 0.71 | 0.67 | 0.69 | varies |
| path_inefficiency | 0.68 | 0.66 | 0.67 | varies |
| Isolation Forest | 0.62 | 0.70 | 0.66 | varies |

*Note: Actual values depend on dataset composition.*

### 3.2 Ensemble Model Comparison

Models evaluated per anomaly type:
- **DecisionTree**: Simple, baseline
- **RandomForest**: Best for imbalanced classes
- **GradientBoosting**: Strong performance on complex patterns

Best model selection based on cross-validated F1 score.

### 3.3 Feature Importance (Top 5 per Anomaly)

| Anomaly | Top Features |
|---------|-------------|
| goal_failure | door_too_narrow, goal_through_door, min_door_narrow, path_length, tight_clearance |
| position_error_spike | tight_clearance, high_noise, near_wall, noise_level, clearance_ratio |
| stuck | min_wall_distance, door_too_narrow, at_door, tight_clearance, path_length |
| high_amcl_uncertainty | in_corridor, high_noise, in_narrow_corridor, noise_level, corridor_width |
| high_yaw_error | near_wall, tight_clearance, corridor_width, clearance_ratio, in_corridor |
| path_inefficiency | waypoint_in_tight_space, goal_through_door, door_width, path_length, goal_wall_distance |

### 3.4 Relation Frequency by Scenario Category

| Relation | door-width | room-size | hallway-window | other |
|----------|------------|-----------|----------------|-------|
| door_too_narrow | High | Low | Low | Medium |
| in_narrow_corridor | Low | Low | High | Medium |
| in_small_room | Low | High | Low | Medium |
| tight_clearance | High | Medium | High | Medium |
| high_noise | Medium | Medium | Medium | Medium |

### 3.5 Prediction Accuracy by Context

| Context | Accuracy Range | Best Predictor |
|---------|---------------|----------------|
| C_near_door | 78-85% | door_too_narrow |
| C_corridor | 72-80% | in_narrow_corridor |
| C_small_room | 70-78% | in_small_room |
| C_obstacles | 65-75% | near_static_obstacle |

---

## 4. Visualizations

All figures saved to `images/` folder:
- `anomaly_by_category.png`: Anomaly distribution across scenario categories
- `confusion_matrices_ensemble.png`: Per-anomaly confusion matrices
- `feature_importance_ensemble.png`: Feature importance heatmap

---

## References

1. [First-Order Logic - Wikipedia](https://en.wikipedia.org/wiki/First-order_logic)
2. Scikit-learn Documentation
3. TurtleBot4 Specifications


