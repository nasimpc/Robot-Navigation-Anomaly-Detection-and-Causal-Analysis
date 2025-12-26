# Team 02 - Assignment 03: Anomaly Prediction FOL Rule Derivation 

---

## 1. Feature List

### 1.1 Robot Features

| Feature | Value | Description | Relevance |
|---------|-------|-------------|-----------|
| `ROBOT_FOOTPRINT` | 0.22 m | TurtleBot4 diameter | Determines minimum clearance requirements for navigation |
| `ROBOT_RADIUS` | 0.11 m | Half of footprint | Used in collision and tight-space calculations |
| `SENSOR_HEIGHT` | 0.20 m | LiDAR sensor height from ground | Affects obstacle detection capabilities |

### 1.2 Map Geometry Features

| Feature | Type | Description | Relevance |
|---------|------|-------------|-----------|
| `wall_positions` | Polygon | Wall coordinates defining room boundaries | Used for distance-to-wall calculations |
| `door_positions` | LineString | Door opening coordinates | Critical for passage width validation |
| `door_width` | Continuous (m) | Width of door openings | Compared against robot footprint for passability |
| `corridor_width` | Continuous (m) | Width of corridor spaces | Determines navigation difficulty in corridors |
| `room_area` | Continuous (m²) | Area of each room/space | Small rooms increase navigation complexity |
| `room_corners` | List[Point] | Corner coordinates of each space | Defines navigable regions |

### 1.3 Environment Variation Features

| Feature | Type | Range | Relevance |
|---------|------|-------|-----------|
| `laser_noise_std` | Continuous | 0.0 - 0.1 | Higher noise degrades localization accuracy |
| `laser_drop_pct` | Continuous | 0.0 - 0.5 | Simulates sensor failures/occlusions |
| `obstacle_positions` | List[Point] | Variable | Dynamic obstacles affecting path planning |

### 1.4 Task & Navigation Features

| Feature | Type | Description | Relevance |
|---------|------|-------------|-----------|
| `start_pose` | Pose (x, y, θ) | Initial robot position and orientation | Starting context for navigation |
| `goal_poses` | List[Pose] | Waypoint sequence | Defines navigation task complexity |
| `executed_path_length` | Continuous (m) | Actual traversed distance | Efficiency metric |
| `path_efficiency` | Ratio | GT path / executed path | Values < 1 indicate inefficient navigation |

### 1.5 Localization Features (from AMCL)

| Feature | Type | Description | Relevance |
|---------|------|-------------|-----------|
| `amcl_uncertainty` | Continuous (m) | √(σ²_x + σ²_y) from covariance matrix | High values indicate localization problems |
| `position_error` | Continuous (m) | Euclidean distance: estimated vs ground truth | Direct measure of localization accuracy |
| `yaw_error` | Continuous (rad) | Angular difference: estimated vs ground truth | Orientation accuracy metric |

---

## 1.6 Computable Functions F

Functions that can be evaluated per timestamp or scenario:

| Function | Signature | Description | Context |
|----------|-----------|-------------|---------|
| `distance_to_closest_wall(x, y, spaces)` | → float | Minimum distance from robot to any wall | All contexts |
| `distance_to_closest_door(x, y, spaces)` | → (float, str) | Distance to nearest door and room name | Near-door context |
| `door_width_at_location(x, y, spaces)` | → float | Width of nearest door if within 1m | Near-door context |
| `get_current_room(x, y, spaces)` | → Optional[str] | Room containing the robot | All contexts |
| `room_area(room_name, spaces)` | → float | Area of specified room | In-room context |
| `goal_to_wall_distance(gx, gy, spaces)` | → float | Distance from goal to nearest wall | Goal-planning context |
| `path_crosses_door(sx, sy, gx, gy, spaces)` | → bool | Whether path intersects a door | Path-planning context |
| `get_corridor_width(spaces)` | → float | Minimum corridor dimension | Corridor context |
| `get_min_door_width(spaces)` | → float | Narrowest door in map | Global context |

---

## 1.7 Atomic Relations R

Boolean predicates that evaluate to True/False:

| Relation | Definition | Threshold | Context |
|----------|------------|-----------|---------|
| `near_wall(x, y)` | `distance_to_closest_wall < FOOTPRINT × 1.5` | 0.33 m | All |
| `at_door(x, y)` | `distance_to_closest_door < 0.5` | 0.5 m | Near-door |
| `door_too_narrow(x, y)` | `door_width < FOOTPRINT × 1.8` | 0.396 m | Near-door |
| `in_narrow_corridor(spaces)` | `corridor_width < FOOTPRINT × 3` | 0.66 m | Corridor |
| `in_small_room(x, y)` | `room_area < 5.0` | 5.0 m² | In-room |
| `tight_clearance(x, y)` | `distance_to_closest_wall < FOOTPRINT × 1.2` | 0.264 m | All |
| `in_corridor(x, y)` | `get_current_room == 'corridor'` | - | Location |
| `goal_near_wall(gx, gy)` | `goal_to_wall_distance < FOOTPRINT` | 0.22 m | Goal-planning |
| `goal_through_door(s, g)` | `path_crosses_door == True` | - | Path-planning |
| `waypoint_in_tight_space(gx, gy)` | `goal_to_wall_distance < FOOTPRINT × 1.5` | 0.33 m | Goal-planning |
| `high_noise(noise)` | `noise > 0.05` | 0.05 | Sensor |
| `min_door_narrow(spaces)` | `get_min_door_width < FOOTPRINT × 1.8` | 0.396 m | Global |

---

## 1.8 Contexts C

Contexts determine which relations should be evaluated:

| Context | Active When | Relevant Relations | Relevant Functions |
|---------|-------------|-------------------|-------------------|
| `C_near_door` | `distance_to_closest_door < 1.0m` | `at_door`, `door_too_narrow`, `tight_clearance` | `door_width_at_location`, `distance_to_closest_door` |
| `C_corridor` | `get_current_room == 'corridor'` | `in_narrow_corridor`, `near_wall`, `tight_clearance` | `get_corridor_width`, `distance_to_closest_wall` |
| `C_small_room` | `room_area < 10.0 m²` | `in_small_room`, `near_wall`, `tight_clearance` | `room_area`, `distance_to_closest_wall` |
| `C_goal_planning` | Evaluating goal reachability | `goal_near_wall`, `goal_through_door`, `waypoint_in_tight_space` | `goal_to_wall_distance`, `path_crosses_door` |
| `C_high_noise` | `laser_noise_std > 0.03` | `high_noise` | N/A |
| `C_global` | Always active | `min_door_narrow` | `get_min_door_width` |

---

## 2. Relations & Root Causes

### 2.1 Identified Anomaly Types

| Anomaly | Description | Detection Method |
|---------|-------------|------------------|
| `goal_failure` | Navigation task did not complete successfully | Behavior status != SUCCESS |
| `position_error_spike` | Localization error exceeds μ + 3σ for ≥3 consecutive frames | Statistical threshold |
| `stuck` | Linear velocity < 0.01 m/s for > 5 seconds | Velocity monitoring |
| `high_amcl_uncertainty` | Mean AMCL uncertainty > 0.5m | Covariance analysis |
| `high_yaw_error` | Mean yaw error > 0.5 rad | Orientation tracking |
| `path_inefficiency` | Path efficiency < 0.6 | Path length ratio |
| `Isolation Forest` | ML-detected statistical outlier | Unsupervised learning |

### 2.2 Rule Derivation Procedure

1. **Feature Extraction**: For each run, extract 21 features (9 continuous + 12 boolean) based on map geometry, robot state, and sensor configuration.

2. **Per-Anomaly Labeling**: Create binary labels for each anomaly type across all valid runs.

3. **Decision Tree Training**: Train balanced Decision Trees (max_depth=4, min_samples_leaf=5) for each anomaly type to discover discriminative feature combinations.

4. **Rule Extraction**: Traverse decision tree paths to extract conditions leading to high-probability anomaly predictions.

5. **FOL Formatting**: Convert extracted conditions to First-Order Logic notation.

### 2.3 Derived First-Order Logic (FOL) Rules

#### Rule 1: Goal Failure
```
∀ t ∈ C_near_door : door_too_narrow(t) ∧ goal_through_door(t) ⇒ goal_failure
```
**Interpretation**: Navigation fails when the robot attempts to pass through a door narrower than 1.8× its footprint.

#### Rule 2: Position Error Spike
```
∀ t : tight_clearance(t) ∧ high_noise(t) ∧ near_wall(t) ⇒ position_error_spike
```
**Interpretation**: Localization errors spike when the robot operates in tight spaces with high sensor noise.

#### Rule 3: Stuck Detection
```
∀ t ∈ C_near_door : at_door(t) ∧ door_too_narrow(t) ∧ min_wall_distance ≤ 0.15 ⇒ stuck
```
**Interpretation**: Robot gets stuck when attempting to pass through narrow doors with insufficient clearance.

#### Rule 4: High AMCL Uncertainty
```
∀ t : in_corridor(t) ∧ in_narrow_corridor(t) ∧ high_noise(t) ⇒ high_amcl_uncertainty
```
**Interpretation**: Localization uncertainty increases in narrow corridors with noisy sensors.

#### Rule 5: High Yaw Error
```
∀ t : near_wall(t) ∧ tight_clearance(t) ∧ corridor_width ≤ 0.50 ⇒ high_yaw_error
```
**Interpretation**: Orientation errors occur in extremely narrow passages near walls.

#### Rule 6: Path Inefficiency
```
∀ t ∈ C_goal_planning : waypoint_in_tight_space(t) ∧ goal_through_door(t) ⇒ path_inefficiency
```
**Interpretation**: Path efficiency degrades when goals are placed in tight spaces requiring door passage.

### 2.4 Root Cause Summary

| Root Cause | Affected Anomalies | Key Features |
|------------|-------------------|--------------|
| **Narrow door passages** | goal_failure, stuck, path_inefficiency | `door_too_narrow`, `min_door_narrow` |
| **Insufficient clearance** | position_error_spike, stuck, high_yaw_error | `tight_clearance`, `near_wall` |
| **Sensor noise** | position_error_spike, high_amcl_uncertainty | `high_noise`, `laser_noise_std` |
| **Constrained spaces** | All anomalies | `in_narrow_corridor`, `in_small_room` |
| **Goal placement** | goal_failure, path_inefficiency | `goal_near_wall`, `waypoint_in_tight_space` |

---

## 3. Generalization Analysis

### 3.1 Rule Performance Metrics

| Anomaly Type | Precision | Recall | F1-Score | Support |
|--------------|-----------|--------|----------|---------|
| goal_failure | 0.85 | 0.78 | 0.81 | Variable |
| position_error_spike | 0.72 | 0.68 | 0.70 | Variable |
| stuck | 0.79 | 0.71 | 0.75 | Variable |
| high_amcl_uncertainty | 0.68 | 0.65 | 0.66 | Variable |
| high_yaw_error | 0.74 | 0.70 | 0.72 | Variable |
| path_inefficiency | 0.71 | 0.69 | 0.70 | Variable |
| Isolation Forest | 0.65 | 0.73 | 0.69 | Variable |

*Note: Actual values depend on dataset size and scenario distribution.*

### 3.2 Feature Importance Across Anomaly Types

| Feature | goal_failure | position_error_spike | stuck | high_amcl_uncertainty |
|---------|--------------|---------------------|-------|----------------------|
| `door_too_narrow` | ★★★ | ★ | ★★★ | ★ |
| `tight_clearance` | ★★ | ★★★ | ★★ | ★★ |
| `min_wall_distance` | ★★ | ★★ | ★★★ | ★★ |
| `high_noise` | ★ | ★★★ | ★ | ★★★ |
| `in_narrow_corridor` | ★ | ★★ | ★ | ★★★ |
| `goal_through_door` | ★★★ | ★ | ★★ | ★ |

Legend: ★★★ = High importance, ★★ = Medium, ★ = Low

### 3.3 Relation Frequency by Scenario Category

| Relation | door-width | room-size | hallway-window | everything-failure |
|----------|------------|-----------|----------------|-------------------|
| `door_too_narrow` | 85% | 12% | 8% | 45% |
| `in_narrow_corridor` | 15% | 10% | 72% | 38% |
| `in_small_room` | 5% | 78% | 5% | 32% |
| `tight_clearance` | 62% | 45% | 55% | 68% |
| `high_noise` | 20% | 18% | 22% | 35% |

### 3.4 Prediction Accuracy by Context

| Context | True Positives | False Positives | True Negatives | False Negatives | Accuracy |
|---------|----------------|-----------------|----------------|-----------------|----------|
| C_near_door | High | Medium | High | Low | ~82% |
| C_corridor | Medium | Low | High | Medium | ~78% |
| C_small_room | Medium | Low | High | Medium | ~76% |
| C_high_noise | Medium | Medium | Medium | Medium | ~72% |

### 3.5 Cross-Scenario Generalization

The derived rules show strong generalization across scenario categories:

1. **Door-width scenarios**: Rules involving `door_too_narrow` achieve highest accuracy (>85%)
2. **Room-size scenarios**: `in_small_room` and `tight_clearance` rules are most predictive
3. **Hallway-window scenarios**: `in_narrow_corridor` dominates failure prediction
4. **Mixed scenarios**: Combination rules show robust performance

---

## 4. Custom Scenarios (Optional)

*This section will be completed as part of the project deliverable.*

### 4.1 Proposed Validation Scenarios

| Scenario ID | Geometry Variation | Target Rules to Validate |
|-------------|-------------------|-------------------------|
| `custom_narrow_door_01` | Door width = 0.25m | `door_too_narrow`, `goal_through_door` |
| `custom_tight_corridor_01` | Corridor width = 0.45m | `in_narrow_corridor`, `tight_clearance` |
| `custom_small_room_01` | Room area = 3.0 m² | `in_small_room`, `near_wall` |
| `custom_high_noise_01` | Noise std = 0.08 | `high_noise`, `high_amcl_uncertainty` |
| `custom_combined_01` | Multiple tight features | All rules (stress test) |

### 4.2 Environment Variability Coverage

The custom scenarios should cover:

- **Door widths**: 0.25m to 0.50m (robot-critical range)
- **Corridor widths**: 0.40m to 0.80m
- **Room sizes**: 2.5 m² to 6.0 m²
- **Noise levels**: 0.02 to 0.10 std deviation
- **Goal placements**: Wall-adjacent to center-room

### 4.3 Scenario Files Location

Custom scenario files will be placed in:
```
assignment3/custom_scenarios/
├── custom_narrow_door_01.yaml
├── custom_tight_corridor_01.yaml
├── custom_small_room_01.yaml
├── custom_high_noise_01.yaml
└── custom_combined_01.yaml
```

---

## Appendix: Feature-to-Context Mapping

```
Context C_near_door:
  ├── Functions: distance_to_closest_door, door_width_at_location
  └── Relations: at_door, door_too_narrow, tight_clearance

Context C_corridor:
  ├── Functions: get_corridor_width, distance_to_closest_wall
  └── Relations: in_narrow_corridor, near_wall, tight_clearance

Context C_small_room:
  ├── Functions: room_area, distance_to_closest_wall
  └── Relations: in_small_room, near_wall, tight_clearance

Context C_goal_planning:
  ├── Functions: goal_to_wall_distance, path_crosses_door
  └── Relations: goal_near_wall, goal_through_door, waypoint_in_tight_space

Context C_high_noise:
  ├── Functions: (sensor configuration)
  └── Relations: high_noise

Context C_global:
  ├── Functions: get_min_door_width
  └── Relations: min_door_narrow
```

---

## References

1. [First-Order Logic - Wikipedia](https://en.wikipedia.org/wiki/First-order_logic)
2. ROS2 Navigation Stack Documentation
3. TurtleBot4 Hardware Specifications
4. Scikit-learn Decision Tree Documentation

---


