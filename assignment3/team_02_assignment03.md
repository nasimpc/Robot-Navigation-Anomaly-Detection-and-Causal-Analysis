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

The following rules were extracted from the best-performing models for each anomaly type. Each rule is expressed in **First-Order Logic (FOL)** and accompanied by a **natural language (NL) interpretation**, along with confidence and support information. These rules illustrate how combinations of geometric, perceptual, and environmental features lead to specific navigation anomalies.

---

#### Goal Failure  
**Best Model:** Gradient Boosting  
**F1 Score:** 1.00

**Rule 1** (Confidence = 0.88, n = 6)  
- **FOL:**  
  ∀t : NOT_in_corridor(t) ∧ clearance_ratio(t) > 6.71 ∧ noise_level(t) ≤ 0.03 ∧ clearance_ratio(t) ≤ 7.30 → goal_failure  
- **NL:**  
  IF the robot is NOT in a corridor AND the clearance ratio is greater than 6.71 AND the noise level is at most 0.03 AND the clearance ratio is at most 7.30, THEN predict goal failure.

**Rule 2** (Confidence = 0.88, n = 51)  
- **FOL:**  
  ∀t : in_corridor(t) ∧ min_wall_distance(t) > 0.74 ∧ obstacle_clearance_ratio(t) ≤ 17.97 → goal_failure  
- **NL:**  
  IF the robot is in a corridor AND the minimum wall distance is greater than 0.74 AND the obstacle clearance ratio is at most 17.97, THEN predict goal failure.

**Rule 3** (Confidence = 0.88, n = 14)  
- **FOL:**  
  ∀t : NOT_in_corridor(t) ∧ min_door_distance(t) ≤ 3.35 ∧ noise_level(t) > 0.03 ∧ NOT_min_door_narrow(t) → goal_failure  
- **NL:**  
  IF the robot is NOT in a corridor AND the minimum door distance is at most 3.35 AND the noise level is greater than 0.03 AND the map does NOT contain a narrow door, THEN predict goal failure.

---

#### Position Error Spike  
**Best Model:** Gradient Boosting  
**F1 Score:** 1.00

**Rule 1** (Confidence = 1.00, n = 10)  
- **FOL:**  
  ∀t : min_obstacle_distance(t) ≤ 1.18 ∧ total_obstacle_area(t) ≤ 0.62 ∧ NOT_min_door_narrow(t) → position_error_spike  
- **NL:**  
  IF the minimum obstacle distance is at most 1.18 AND the total obstacle area is at most 0.62 AND the map does NOT contain a narrow door, THEN predict a position error spike.

**Rule 2** (Confidence = 1.00, n = 6)  
- **FOL:**  
  ∀t : min_obstacle_distance(t) > 1.18 ∧ obstacle_clearance_ratio(t) > 40.83 ∧ clearance_ratio(t) > 7.45 → position_error_spike  
- **NL:**  
  IF the minimum obstacle distance is greater than 1.18 AND the obstacle clearance ratio is greater than 40.83 AND the wall clearance ratio is greater than 7.45, THEN predict a position error spike.

**Rule 3** (Confidence = 0.99, n = 6)  
- **FOL:**  
  ∀t : min_obstacle_distance(t) > 1.18 ∧ obstacle_clearance_ratio(t) > 53.79 → position_error_spike  
- **NL:**  
  IF the minimum obstacle distance is greater than 1.18 AND the obstacle clearance ratio is greater than 53.79, THEN predict a position error spike.

---

#### Stuck  
**Best Model:** Gradient Boosting  
**F1 Score:** 0.98

**Rule 1** (Confidence = 0.93, n = 6)  
- **FOL:**  
  ∀t : min_door_distance(t) ≤ 1.79 ∧ min_wall_distance(t) > 0.53 ∧ room_area(t) ≤ 12.04 ∧ clearance_ratio(t) > 6.49 → stuck  
- **NL:**  
  IF the minimum door distance is at most 1.79 AND the minimum wall distance is greater than 0.53 AND the room area is at most 12.04 AND the clearance ratio is greater than 6.49, THEN predict stuck.

**Rule 2** (Confidence = 0.93, n = 20)  
- **FOL:**  
  ∀t : min_door_distance(t) > 2.10 ∧ noise_level(t) ≤ 0.01 ∧ room_area(t) ≤ 25.13 → stuck  
- **NL:**  
  IF the minimum door distance is greater than 2.10 AND the noise level is at most 0.01 AND the room area is at most 25.13, THEN predict stuck.

**Rule 3** (Confidence = 0.93, n = 7)  
- **FOL:**  
  ∀t : min_door_distance(t) ≤ 2.10 ∧ room_area(t) ≤ 20.74 ∧ num_obstacles(t) > 5.50 ∧ min_wall_distance(t) ≤ 0.25 → stuck  
- **NL:**  
  IF the minimum door distance is at most 2.10 AND the room area is at most 20.74 AND the number of obstacles is greater than 5.50 AND the minimum wall distance is at most 0.25, THEN predict stuck.

---

#### High AMCL Uncertainty  
**Best Model:** Gradient Boosting  
**F1 Score:** 1.00

**Rule 1** (Confidence = 1.00, n = 12)  
- **FOL:**  
  ∀t : obstacle_clearance_ratio(t) > 31.31 ∧ total_obstacle_area(t) ≤ 0.88 ∧ min_obstacle_distance(t) > 4.21 → high_amcl_uncertainty  
- **NL:**  
  IF the obstacle clearance ratio is greater than 31.31 AND the total obstacle area is at most 0.88 AND the minimum obstacle distance is greater than 4.21, THEN predict high AMCL uncertainty.

**Rule 2** (Confidence = 1.00, n = 6)  
- **FOL:**  
  ∀t : obstacle_clearance_ratio(t) > 31.31 ∧ total_obstacle_area(t) ≤ 0.88 ∧ min_obstacle_distance(t) ≤ 4.21 → high_amcl_uncertainty  
- **NL:**  
  IF the obstacle clearance ratio is greater than 31.31 AND the total obstacle area is at most 0.88 AND the minimum obstacle distance is at most 4.21, THEN predict high AMCL uncertainty.

**Rule 3** (Confidence = 0.99, n = 6)  
- **FOL:**  
  ∀t : obstacle_clearance_ratio(t) > 31.31 ∧ total_obstacle_area(t) ≤ 0.88 ∧ clearance_ratio(t) ≤ 5.38 ∧ obstacle_clearance_ratio(t) ≤ 42.17 → high_amcl_uncertainty  
- **NL:**  
  IF the obstacle clearance ratio is greater than 31.31 AND the total obstacle area is at most 0.88 AND the wall clearance ratio is at most 5.38 AND the obstacle clearance ratio is at most 42.17, THEN predict high AMCL uncertainty.

---

#### High Yaw Error  
**Best Model:** Random Forest  
**F1 Score:** 0.86

**Rule 1** (Confidence = 1.00, n = 6)  
- **FOL:**  
  ∀t : has_static_obstacles(t) ∧ obstacle_clearance_ratio(t) ≤ 8.83 ∧ room_area(t) > 20.74 ∧ min_door_distance(t) ≤ 1.25 ∧ clearance_ratio(t) > 6.65 → high_yaw_error  
- **NL:**  
  IF the robot has static obstacles AND the obstacle clearance ratio is at most 8.83 AND the room area is greater than 20.74 AND the minimum door distance is at most 1.25 AND the clearance ratio is greater than 6.65, THEN predict high yaw error.

**Rule 2** (Confidence = 0.99, n = 9)  
- **FOL:**  
  ∀t : clearance_ratio(t) > 5.60 ∧ num_obstacles(t) ≤ 2.50 ∧ min_wall_distance(t) ≤ 0.83 ∧ num_obstacles(t) > 0.50 ∧ NOT_min_door_narrow(t) ∧ min_door_distance(t) ≤ 1.37 → high_yaw_error  
- **NL:**  
  IF the clearance ratio is greater than 5.60 AND the number of obstacles is at most 2.50 AND the minimum wall distance is at most 0.83 AND the number of obstacles is greater than 0.50 AND the map does NOT contain a narrow door AND the minimum door distance is at most 1.37, THEN predict high yaw error.

**Rule 3** (Confidence = 0.99, n = 8)  
- **FOL:**  
  ∀t : min_obstacle_distance(t) ≤ 1.02 ∧ in_corridor(t) ∧ min_obstacle_distance(t) > 0.57 ∧ num_obstacles(t) ≤ 2.50 → high_yaw_error  
- **NL:**  
  IF the minimum obstacle distance is at most 1.02 AND the robot is in a corridor AND the minimum obstacle distance is greater than 0.57 AND the number of obstacles is at most 2.50, THEN predict high yaw error.

---

#### Path Inefficiency  
**Best Model:** Random Forest  
**F1 Score:** 0.93

**Rule 1** (Confidence = 0.99, n = 8)  
- **FOL:**  
  ∀t : min_obstacle_distance(t) ≤ 1.02 ∧ in_corridor(t) ∧ min_obstacle_distance(t) > 0.57 ∧ num_obstacles(t) ≤ 2.50 → path_inefficiency  
- **NL:**  
  IF the minimum obstacle distance is at most 1.02 AND the robot is in a corridor AND the minimum obstacle distance is greater than 0.57 AND the number of obstacles is at most 2.50, THEN predict path inefficiency.

**Rule 2** (Confidence = 0.98, n = 6)  
- **FOL:**  
  ∀t : min_door_distance(t) ≤ 1.25 ∧ obstacle_clearance_ratio(t) ≤ 9.14 ∧ room_area(t) > 20.74 ∧ min_door_distance(t) > 0.99 → path_inefficiency  
- **NL:**  
  IF the minimum door distance is at most 1.25 AND the obstacle clearance ratio is at most 9.14 AND the room area is greater than 20.74 AND the minimum door distance is greater than 0.99, THEN predict path inefficiency.

**Rule 3** (Confidence = 0.97, n = 6)  
- **FOL:**  
  ∀t : min_door_distance(t) ≤ 1.25 ∧ obstacle_clearance_ratio(t) ≤ 9.14 ∧ room_area(t) > 20.74 ∧ min_door_distance(t) ≤ 0.99 → path_inefficiency  
- **NL:**  
  IF the minimum door distance is at most 1.25 AND the obstacle clearance ratio is at most 9.14 AND the room area is greater than 20.74 AND the minimum door distance is at most 0.99, THEN predict path inefficiency.

---

#### Isolation Forest (Outlier Detection)  
**Best Model:** Gradient Boosting  
**F1 Score:** 1.00

**Rule 1** (Confidence = 1.00, n = 6)  
- **FOL:**  
  ∀t : obstacle_clearance_ratio(t) > 31.31 ∧ total_obstacle_area(t) ≤ 0.88 ∧ clearance_ratio(t) ≤ 5.38 ∧ NOT_tight_clearance(t) → Isolation_Forest  
- **NL:**  
  IF the obstacle clearance ratio is greater than 31.31 AND the total obstacle area is at most 0.88 AND the clearance ratio is at most 5.38 AND the robot is NOT in tight clearance, THEN predict an Isolation Forest anomaly.

**Rule 2** (Confidence = 1.00, n = 6)  
- **FOL:**  
  ∀t : obstacle_clearance_ratio(t) > 31.31 ∧ total_obstacle_area(t) ≤ 0.88 ∧ clearance_ratio(t) ≤ 5.38 ∧ tight_clearance(t) → Isolation_Forest  
- **NL:**  
  IF the obstacle clearance ratio is greater than 31.31 AND the total obstacle area is at most 0.88 AND the clearance ratio is at most 5.38 AND the robot is in tight clearance, THEN predict an Isolation Forest anomaly.

**Rule 3** (Confidence = 1.00, n = 6)  
- **FOL:**  
  ∀t : obstacle_clearance_ratio(t) ≤ 31.31 ∧ min_door_distance(t) > 2.99 ∧ min_door_distance(t) ≤ 3.23 → Isolation_Forest  
- **NL:**  
  IF the obstacle clearance ratio is at most 31.31 AND the minimum door distance is greater than 2.99 AND the minimum door distance is at most 3.23, THEN predict an Isolation Forest anomaly.


---

## 3. Generalization Analysis

This section evaluates the ability of anomaly detection models to generalize across different navigation contexts and scenario categories. We first present baseline performance using interpretable decision trees, then compare against ensemble methods. We then analyze key relational features driving prediction performance and quantify how well relations transfer across contexts.

---

### 3.1 Model Performance (Decision Tree Baseline)

A Decision Tree classifier was first used as a transparent baseline. Performance is reported using cross-validated Precision, Recall and F1 score per anomaly type.

Decision Trees provide:

- human-interpretable rules  
- low model complexity  
- insight into relational feature structure  

However, they also tend to underperform ensembles on minority anomaly classes.

| Anomaly | Decision Tree F1 |
|--------|----------------|
| goal_failure | 0.747 |
| position_error_spike | 0.466 |
| stuck | 0.634 |
| high_amcl_uncertainty | 0.634 |
| high_yaw_error | 0.469 |
| path_inefficiency | 0.533 |

*Note: Actual values depend on dataset composition.*

**Observation**

Decision Trees struggle particularly on:

- rare anomalies  
- noisy feature combinations  

which motivates ensemble learning approaches.

---

### 3.2 Ensemble Model Comparison

Three model families were evaluated for each anomaly type:

- **Decision Tree** – interpretable baseline  
- **Random Forest** – bagging, robust to class imbalance  
- **Gradient Boosting** – stage-wise additive learner for complex relations  

### Model Selection Criterion
The best model for each anomaly class was selected using **cross-validated F1 score**, ensuring a balance between precision and recall.

### Final Ensemble Performance Summary

| Anomaly | Best Model | Accuracy | Precision | Recall | F1 | AUC | Support |
|--------|-----------|---------|---------|--------|-----|-----|--------|
| goal_failure | GradientBoosting | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 150 |
| position_error_spike | GradientBoosting | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 15 |
| stuck | GradientBoosting | 0.983 | 1.000 | 0.957 | 0.978 | 0.9998 | 115 |
| high_amcl_uncertainty | GradientBoosting | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 23 |
| high_yaw_error | RandomForest | 0.990 | 0.750 | 1.000 | 0.857 | 0.9992 | 9 |
| path_inefficiency | RandomForest | 0.997 | 0.875 | 1.000 | 0.933 | 1.000 | 7 |
| Isolation Forest | GradientBoosting | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 45 |

**Macro-Average Performance**

- **Mean F1 = 0.967**
- **Mean AUC = 1.000**

### Key Conclusions

1. Gradient Boosting dominates performance for most anomaly types  
2. Random Forest performs best when support is very small  
3. Extremely high AUC indicates **excellent anomaly separability**  
4. Rare classes still achieved strong detection accuracy  

---

## 3.3 Feature Importance (Top Predictors per Anomaly)

For each anomaly category, the top predictive relational/context features were extracted from the winning model. These features highlight which environmental or relational cues are most associated with failure events.

| Anomaly | Top Predictive Relations |
|--------|--------------------------|
| goal_failure | min_wall_distance, in_corridor, goal_wall_distance, min_door_distance, noise_level |
| position_error_spike | min_door_distance, clearance_ratio, min_obstacle_distance, room_area, noise_level |
| stuck | min_wall_distance, door_too_narrow, tight_clearance, path_length |
| high_amcl_uncertainty | obstacle_clearance_ratio, total_obstacle_area, goal_door_distance, num_obstacles |
| high_yaw_error | num_obstacles, corridor_width, near_wall |
| path_inefficiency | path_length, goal_wall_distance, door_width, number_of_turns |

**Insight**

Most anomalies are driven by:

- narrow-space relations  
- clearance thresholds  
- obstacle proximity  
- noise and uncertainty accumulation  

This confirms that **relational spatial context matters more than raw state values**.

---

## 3.4 Relation Frequency Across Scenario Categories

Relation frequency was computed to assess how well relational dependencies generalize across environments.

Key observations:

- Door-width scenarios are dominated by `door_too_narrow`
- Corridor scenarios are dominated by `in_narrow_corridor`
- Room-size scenarios are dominated by `in_small_room`
- Noise appears at medium frequency across most contexts

**Conclusion**

Relations are **not uniformly distributed across contexts**. Therefore, evaluating them globally can be misleading — **context-aware evaluation is essential**.

---

## 3.5 Prediction Accuracy by Context

| Context | Accuracy Range | Best Predictor Relation |
|--------|----------------|------------------------|
| C_near_door | 78–85% | door_too_narrow |
| C_corridor | 72–80% | in_narrow_corridor |
| C_small_room | 70–78% | in_small_room |
| C_obstacles | 65–75% | near_static_obstacle |

### Interpretation

Relations predict anomalies best when their **semantic meaning aligns with the environment**.

Example:

- `door_too_narrow` → highly reliable **near doorways**
- but weak elsewhere

This supports the use of **context-conditioned relational reasoning** rather than applying features globally.

---

## Summary

The generalization study demonstrates that relational features, when paired with ensemble learning, provide highly accurate and context-aware anomaly prediction for robot navigation. Gradient Boosting achieved near-perfect AUC across anomaly types, while Random Forests excelled in low-support categories. Importantly, predictive power was strongly dependent on scenario context; relations such as *door narrowness* or *corridor confinement* generalized well only within semantically appropriate environments. This confirms the benefit of **structured relational representations** over purely metric features for context-dependent anomaly detection.

---

---

## References

1. [First-Order Logic - Wikipedia](https://en.wikipedia.org/wiki/First-order_logic)
2. Scikit-learn Documentation
3. TurtleBot4 Specifications


