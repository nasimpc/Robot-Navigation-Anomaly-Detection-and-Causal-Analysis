# Team 02 - Assignment 03: Anomaly Prediction FOL Rule Derivation

---

## 1. Feature List


This section summarizes all identified **features, functions, atomic relations (predicates), and contexts** used for anomaly prediction. For each element, we provide a concise description and its relevance to navigation failures.

### 1.1 Robot Constants

| Constant | Value | Description | Relevance |
|--------|-------|-------------|-----------|
| ROBOT_FOOTPRINT | 0.22 m | TurtleBot4 diameter | Defines minimum traversable openings and clearance constraints |
| ROBOT_RADIUS | 0.11 m | Half of footprint | Used to normalize distances into clearance ratios |
| SENSOR_HEIGHT | 0.20 m | LiDAR height from ground | Assumption for wall/obstacle interaction |

### 1.2 Extracted Features (28 total)

#### Continuous Features (13)

| Feature | Source | Description | Relevance |
|-------|--------|-------------|-----------|
| min_wall_distance | Map geometry | Distance to closest wall (m) | Low values increase collision risk and localization error |
| min_door_distance | Map geometry | Distance to closest door (m) | Indicates interaction with narrow transitions |
| door_width | Map geometry | Width of nearest door (m) | Determines feasibility of passing through doors |
| corridor_width | Map geometry | Corridor minimum dimension (m) | Narrow corridors degrade navigation and yaw stability |
| room_area | Map geometry | Area of current room (m²) | Small rooms amplify wall proximity effects |
| clearance_ratio | Computed | min_wall_distance / ROBOT_RADIUS | Normalized measure of navigational safety margin |
| goal_wall_distance | Map geometry | Goal distance to wall (m) | Goals near walls increase failure probability |
| path_length | Metrics | Executed path length (m) | Long paths indicate replanning or inefficiency |
| noise_level | Config | Laser noise standard deviation | High noise degrades AMCL and pose estimation |
| min_obstacle_distance | Static objects | Distance to closest obstacle (m) | Indicates risk of obstacle-induced failure |
| obstacle_clearance_ratio | Static objects | Obstacle distance / ROBOT_RADIUS | Normalized obstacle proximity |
| num_obstacles | Static objects | Count of static obstacles | Measures environmental clutter |
| total_obstacle_area | Static objects | Sum of obstacle footprints (m²) | Approximates obstacle density |


#### Boolean Predicates (15)

| Predicate | Threshold | Description | Relevance |
|---------|----------|-------------|-----------|
| near_wall | < 0.33 m | Within 1.5× footprint of wall | Strongly linked to localization and yaw errors |
| at_door | < 0.5 m | Near a door opening | Door transitions are common failure points |
| door_too_narrow | < 0.396 m | Door < 1.8× footprint | Geometrically infeasible passage |
| in_narrow_corridor | < 0.66 m | Corridor < 3× footprint | Limits maneuverability and sensor coverage |
| in_small_room | < 5.0 m² | Room area below threshold | High wall interaction density |
| tight_clearance | < 0.264 m | Wall distance < 1.2× footprint | High collision and localization risk |
| in_corridor | — | Robot in corridor space | Corridor dynamics differ from rooms |
| goal_near_wall | < 0.22 m | Goal < 1× footprint from wall | Risky goal placement |
| goal_through_door | — | Path crosses door opening | Planning through constrained transition |
| waypoint_in_tight_space | < 0.33 m | Goal in constrained area | Indicates poor intermediate planning |
| high_noise | > 0.05 | Elevated sensor noise | Degrades pose estimation |
| min_door_narrow | < 0.396 m | Map’s narrowest door is tight | Global map feasibility constraint |
| near_static_obstacle | < 0.5 m | Close to static obstacle | Local blockage risk |
| tight_obstacle_clearance | < 0.33 m | Obstacle < 1.5× footprint | High likelihood of getting stuck |
| has_static_obstacles | — | Scenario contains obstacles | Enables obstacle-related rules |


### 1.3 Computable Functions (F)

| Function | Return | Description | Used to Derive |
|--------|--------|-------------|---------------|
| distance_to_closest_wall(x,y,spaces) | float | Min distance to any wall boundary | near_wall, tight_clearance |
| distance_to_closest_door(x,y,spaces) | (float, str) | Distance and room name of nearest door | at_door |
| door_width_at_location(x,y,spaces) | float | Door width if within 1 m | door_too_narrow |
| get_current_room(x,y,spaces) | str | Room containing position | in_corridor, in_small_room |
| room_area(room,spaces) | float | Area of specified room | in_small_room |
| goal_to_wall_distance(gx,gy,spaces) | float | Goal’s wall clearance | goal_near_wall |
| path_crosses_door(s,g,spaces) | bool | Path intersects door | goal_through_door |
| get_corridor_width(spaces) | float | Corridor’s minimum dimension | in_narrow_corridor |
| get_min_door_width(spaces) | float | Narrowest door in map | min_door_narrow |
| distance_to_closest_obstacle(x,y,objs) | float | Distance to nearest obstacle | near_static_obstacle |
| obstacle_clearance_ratio(x,y,objs) | float | Obstacle distance / robot radius | tight_obstacle_clearance |


### 1.4 Contexts (C)


Contexts activate **subsets of predicates** depending on spatial or operational conditions.

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

The following rules were extracted from the best-performing models for each anomaly type. Each rule is expressed in **First-Order Logic (FOL)** and accompanied by a **natural language (NL) interpretation**. These rules illustrate how combinations of geometric, perceptual, and environmental features lead to specific navigation anomalies.

---

#### goal_failure

**Rule 1**
- **FOL:** `∀t : in_corridor(t) ∧ min_wall_distance(t) > 0.737 ∧ obstacle_clearance_ratio(t) <= 17.970 ⇒ goal_failure`
- **NL:** IF robot is in corridor AND min wall distance > 0.737 AND obstacle clearance ratio ≤ 17.970 THEN goal_failure

**Rule 2**
- **FOL:** `∀t : ¬in_corridor(t) ∧ min_door_distance(t) <= 3.350 ∧ noise_level(t) > 0.030 ∧ ¬min_door_narrow(t) ⇒ goal_failure`
- **NL:** IF robot is NOT in corridor AND min door distance ≤ 3.350 AND noise level > 0.030 AND robot is NOT min door narrow THEN goal_failure

**Rule 3**
- **FOL:** `∀t : in_corridor(t) ∧ min_wall_distance(t) > 0.737 ∧ obstacle_clearance_ratio(t) > 17.970 ∧ min_obstacle_distance(t) > 2.142 ⇒ goal_failure`
- **NL:** IF robot is in corridor AND min wall distance > 0.737 AND obstacle clearance ratio > 17.970 AND min obstacle distance > 2.142 THEN goal_failure

#### position_error_spike

**Rule 1**
- **FOL:** `∀t : has_static_obstacles(t) ∧ total_obstacle_area(t) <= 0.875 ∧ room_area(t) > 12.127 ∧ goal_wall_distance(t) > 0.245 ⇒ position_error_spike`
- **NL:** IF robot is has static obstacles AND total obstacle area ≤ 0.875 AND room area > 12.127 AND goal wall distance > 0.245 THEN position_error_spike

#### stuck

**Rule 1**
- **FOL:** `∀t : min_door_distance(t) > 1.792 ∧ noise_level(t) <= 0.015 ∧ min_door_distance(t) > 2.104 ∧ room_area(t) <= 25.130 ⇒ stuck`
- **NL:** IF min door distance > 1.792 AND noise level ≤ 0.015 AND min door distance > 2.104 AND room area ≤ 25.130 THEN stuck

**Rule 2**
- **FOL:** `∀t : min_door_distance(t) > 1.792 ∧ noise_level(t) <= 0.015 ∧ min_door_distance(t) > 2.104 ∧ room_area(t) > 25.130 ⇒ stuck`
- **NL:** IF min door distance > 1.792 AND noise level ≤ 0.015 AND min door distance > 2.104 AND room area > 25.130 THEN stuck

**Rule 3**
- **FOL:** `∀t : min_door_distance(t) <= 1.792 ∧ min_door_distance(t) > 1.320 ∧ clearance_ratio(t) <= 3.645 ∧ goal_wall_distance(t) > 0.835 ⇒ stuck`
- **NL:** IF min door distance ≤ 1.792 AND min door distance > 1.320 AND clearance ratio ≤ 3.645 AND goal wall distance > 0.835 THEN stuck

#### high_amcl_uncertainty

**Rule 1**
- **FOL:** `∀t : obstacle_clearance_ratio(t) > 31.314 ∧ total_obstacle_area(t) <= 0.875 ∧ door_width(t) > 0.935 ⇒ high_amcl_uncertainty`
- **NL:** IF obstacle clearance ratio > 31.314 AND total obstacle area ≤ 0.875 AND door width > 0.935 THEN high_amcl_uncertainty

**Rule 2**
- **FOL:** `∀t : obstacle_clearance_ratio(t) > 31.314 ∧ total_obstacle_area(t) <= 0.875 ∧ door_width(t) <= 0.935 ⇒ high_amcl_uncertainty`
- **NL:** IF obstacle clearance ratio > 31.314 AND total obstacle area ≤ 0.875 AND door width ≤ 0.935 THEN high_amcl_uncertainty

**Rule 3**
- **FOL:** `∀t : obstacle_clearance_ratio(t) <= 31.314 ∧ clearance_ratio(t) > 5.874 ∧ total_obstacle_area(t) <= 0.625 ∧ min_obstacle_distance(t) <= 0.802 ⇒ high_amcl_uncertainty`
- **NL:** IF obstacle clearance ratio ≤ 31.314 AND clearance ratio > 5.874 AND total obstacle area ≤ 0.625 AND min obstacle distance ≤ 0.802 THEN high_amcl_uncertainty

#### high_yaw_error

**Rule 1**
- **FOL:** `∀t : obstacle_clearance_ratio(t) <= 8.833 ∧ num_obstacles(t) <= 2.500 ∧ room_area(t) > 21.562 ⇒ high_yaw_error`
- **NL:** IF obstacle clearance ratio ≤ 8.833 AND num obstacles ≤ 2.500 AND room area > 21.562 THEN high_yaw_error

**Rule 2**
- **FOL:** `∀t : obstacle_clearance_ratio(t) <= 8.833 ∧ num_obstacles(t) <= 2.500 ∧ room_area(t) <= 21.562 ⇒ high_yaw_error`
- **NL:** IF obstacle clearance ratio ≤ 8.833 AND num obstacles ≤ 2.500 AND room area ≤ 21.562 THEN high_yaw_error

**Rule 3**
- **FOL:** `∀t : obstacle_clearance_ratio(t) > 8.833 ∧ goal_wall_distance(t) > 1.760 ⇒ high_yaw_error`
- **NL:** IF obstacle clearance ratio > 8.833 AND goal wall distance > 1.760 THEN high_yaw_error

#### path_inefficiency

**Rule 1**
- **FOL:** `∀t : obstacle_clearance_ratio(t) <= 8.833 ∧ clearance_ratio(t) > 6.812 ∧ min_door_distance(t) <= 1.349 ⇒ path_inefficiency`
- **NL:** IF obstacle clearance ratio ≤ 8.833 AND clearance ratio > 6.812 AND min door distance ≤ 1.349 THEN path_inefficiency

#### Isolation Forest

**Rule 1**
- **FOL:** `∀t : obstacle_clearance_ratio(t) > 31.314 ∧ total_obstacle_area(t) <= 0.875 ∧ door_width(t) > 0.935 ⇒ Isolation Forest`
- **NL:** IF obstacle clearance ratio > 31.314 AND total obstacle area ≤ 0.875 AND door width > 0.935 THEN Isolation Forest

**Rule 2**
- **FOL:** `∀t : obstacle_clearance_ratio(t) > 31.314 ∧ total_obstacle_area(t) <= 0.875 ∧ door_width(t) <= 0.935 ⇒ Isolation Forest`
- **NL:** IF obstacle clearance ratio > 31.314 AND total obstacle area ≤ 0.875 AND door width ≤ 0.935 THEN Isolation Forest

**Rule 3**
- **FOL:** `∀t : obstacle_clearance_ratio(t) <= 31.314 ∧ noise_level(t) <= 0.005 ∧ total_obstacle_area(t) <= 0.625 ∧ ¬goal_near_wall(t) ⇒ Isolation Forest`
- **NL:** IF obstacle clearance ratio ≤ 31.314 AND noise level ≤ 0.005 AND total obstacle area ≤ 0.625 AND robot is NOT goal near wall THEN Isolation Forest

---

## 3. Generalization Analysis

### 3.1 Metric Definitions

| Metric | Definition | Interpretation |
|--------|------------|----------------|
| **Fidelity** | Accuracy of surrogate tree vs. ensemble model | How well the interpretable rules mimic the complex model |
| **F1 Score** | Harmonic mean of Precision and Recall | Overall classification performance against ground truth |
| **Cov (Coverage)** | % of total samples matching the rule condition | How general or specific the rule is |
| **Prec (Precision)** | TP / (TP + FP) for the rule | Probability that the anomaly exists given the rule triggers |
| **Rec (Recall)** | TP / (TP + FN) for the rule | Percentage of actual anomalies captured by this rule |
| **n** | Number of samples matching the rule | Statistical support for the rule |
| **Scenarios** | Count of unique scenarios where rule triggers | Indicates if rule is scenario-specific or general |
| **Confusion** | TP, FP, FN, TN counts | Raw breakdown of prediction outcomes |

### 3.2 Detailed Rule Generalization Analysis

#### goal_failure (Fidelity=0.84, F1=0.82)

| Rule | Cov | Prec | Rec | n | Scenarios | Confusion |
|------|-----|------|-----|---|-----------|-----------|
| Rule 1 | 17.0% | 1.00 | 0.34 | 51 | 20 (20.0%) | TP=51, FP=0, FN=99, TN=150 |
| Rule 2 | 4.7% | 1.00 | 0.09 | 14 | 5 (5.0%) | TP=14, FP=0, FN=136, TN=150 |
| Rule 3 | 3.3% | 1.00 | 0.07 | 10 | 4 (4.0%) | TP=10, FP=0, FN=140, TN=150 |

#### position_error_spike (Fidelity=0.86, F1=0.41)

| Rule | Cov | Prec | Rec | n | Scenarios | Confusion |
|------|-----|------|-----|---|-----------|-----------|
| Rule 1 | 19.3% | 0.26 | 1.00 | 58 | 20 (20.0%) | TP=15, FP=43, FN=0, TN=242 |

#### stuck (Fidelity=0.64, F1=0.65)

| Rule | Cov | Prec | Rec | n | Scenarios | Confusion |
|------|-----|------|-----|---|-----------|-----------|
| Rule 1 | 6.7% | 1.00 | 0.17 | 20 | 9 (9.0%) | TP=20, FP=0, FN=95, TN=185 |
| Rule 2 | 3.0% | 0.78 | 0.06 | 9 | 3 (3.0%) | TP=7, FP=2, FN=108, TN=183 |
| Rule 3 | 2.0% | 0.67 | 0.03 | 6 | 4 (4.0%) | TP=4, FP=2, FN=111, TN=183 |

#### high_amcl_uncertainty (Fidelity=0.97, F1=0.83)

| Rule | Cov | Prec | Rec | n | Scenarios | Confusion |
|------|-----|------|-----|---|-----------|-----------|
| Rule 1 | 4.0% | 1.00 | 0.52 | 12 | 4 (4.0%) | TP=12, FP=0, FN=11, TN=277 |
| Rule 2 | 2.0% | 0.83 | 0.22 | 6 | 3 (3.0%) | TP=5, FP=1, FN=18, TN=276 |
| Rule 3 | 2.3% | 0.43 | 0.13 | 7 | 4 (4.0%) | TP=3, FP=4, FN=20, TN=273 |

#### high_yaw_error (Fidelity=0.96, F1=0.55)

| Rule | Cov | Prec | Rec | n | Scenarios | Confusion |
|------|-----|------|-----|---|-----------|-----------|
| Rule 1 | 2.7% | 0.62 | 0.56 | 8 | 3 (3.0%) | TP=5, FP=3, FN=4, TN=288 |
| Rule 2 | 2.0% | 0.50 | 0.33 | 6 | 2 (2.0%) | TP=3, FP=3, FN=6, TN=288 |
| Rule 3 | 3.3% | 0.10 | 0.11 | 10 | 4 (4.0%) | TP=1, FP=9, FN=8, TN=282 |

#### path_inefficiency (Fidelity=0.99, F1=0.82)

| Rule | Cov | Prec | Rec | n | Scenarios | Confusion |
|------|-----|------|-----|---|-----------|-----------|
| Rule 1 | 3.3% | 0.70 | 1.00 | 10 | 6 (6.0%) | TP=7, FP=3, FN=0, TN=290 |

#### Isolation Forest (Fidelity=0.85, F1=0.66)

| Rule | Cov | Prec | Rec | n | Scenarios | Confusion |
|------|-----|------|-----|---|-----------|-----------|
| Rule 1 | 4.0% | 1.00 | 0.27 | 12 | 4 (4.0%) | TP=12, FP=0, FN=33, TN=255 |
| Rule 2 | 2.0% | 0.83 | 0.11 | 6 | 3 (3.0%) | TP=5, FP=1, FN=40, TN=254 |
| Rule 3 | 17.7% | 0.43 | 0.51 | 53 | 18 (18.0%) | TP=23, FP=30, FN=22, TN=225 |

