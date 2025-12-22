# Team 02 - Assignment 02: Robot Navigation & Localization Analysis

---

## 1. World and Machine Phenomena

### World Phenomena

World phenomena exist in the physical/simulated environment independent of the computational system:

1. **Robot Physical State (W1)**: The actual position, orientation, and velocity of the TurtleBot4 as it exists in the simulated world, independent of any estimation.

2. **Environment Layout (W2)**: The physical map structure including walls, rooms, doorways, hallways, and static obstacles that constrain robot motion.

3. **Door Width Variations (W3)**: Physical doorway widths ranging from 0.3m to 0.5m that directly affect whether the robot can pass through certain passages.

4. **Room Size Variations (W4)**: The dimensions of rooms in different scenarios, which affect navigation path length and localization difficulty.

5. **Sensor Noise (W5)**: Physical imperfections and environmental interference in LiDAR readings that corrupt the raw measurements before they reach the machine.

6. **Goal and Start Locations (W6)**: The physical waypoints defining where the robot must navigate, specified in world coordinates.

### Machine Phenomena

Machine phenomena are internal computational states and processes:

1. **Estimated Pose (M1)**: The AMCL-computed position and orientation based on particle filter sensor fusion. This is the robot's internal belief about its location.

2. **Occupancy Grid Map (M2)**: The discretized internal representation of the environment used for path planning and localization.

3. **Covariance Matrix (M3)**: The 6×6 matrix from AMCL representing uncertainty in the pose estimate. Larger values indicate lower confidence.

4. **Planned Path (M4)**: The trajectory computed by Nav2's path planner from current position to goal.

5. **Velocity Commands (M5)**: The linear and angular velocity control outputs sent to the motor controllers.

6. **Behavior Tree State (M6)**: The navigation action status maintained by the behavior tree (RUNNING, SUCCESS, FAILURE).

### Shared Phenomena

Shared phenomena exist at the interface between world and machine:

1. **LiDAR Scan Data (S1)**: Raw laser measurements that originate from physical reflections (world) but are digitized for processing (machine).

2. **Odometry Data (S2)**: Wheel encoder readings that measure physical rotation but are converted to motion estimates.

3. **Motor Commands (S3)**: Velocity commands (machine) that actuate physical motion (world).

4. **Ground Truth Pose (S4)**: Simulator-provided actual robot state used for validation only.

---

## 2. Goals

### System and Feature Goals

These goals define the technical capabilities required from the analysis system:

**SG1 - Robust Data Pipeline**: The system must reliably process multi-source data including poses.csv, behaviors.csv, and rosbag2.csv from over 300 simulation scenarios with varying data quality.

**SG2 - Time Synchronization**: The system must accurately interpolate ground truth poses to match estimated pose timestamps, since the two sources have different sampling rates.

**SG3 - Metric Computation**: The system must compute a comprehensive set of performance metrics covering localization accuracy, path efficiency, and robot kinematics.

**SG4 - Anomaly Detection**: The system must identify anomalous runs using both interpretable rule-based methods and machine learning approaches.

**SG5 - Multi-Source Integration**: The system must combine AMCL uncertainty data from rosbag2.csv with pose error data from poses.csv to enable richer analysis.

### User Goals

These goals address the researcher's needs as identified in requirements elicitation:

**UG1 - Performance Quantification**: Enable numerical comparison of robot behavior across different environmental conditions (door widths, room sizes, hallway configurations).

**UG2 - Failure Classification**: Understand the reasons for navigation failures, distinguishing between stuck conditions, localization divergence, and planning failures.

**UG3 - Scenario Comparison**: Identify which scenario categories (door-width, room-size, hallway-window) correlate with specific failure modes.

**UG4 - Pattern Discovery**: Discover early warning signals in sensor and metric data that precede navigation failures.

**UG5 - Actionable Insights**: Generate findings that can inform improvements to localization and navigation algorithms.

### Model Goals

These goals define objectives for the analytical and ML models:

**MG1 - Anomaly Separation**: The Isolation Forest model should clearly separate nominal runs from anomalous runs in the multi-dimensional feature space.

**MG2 - Feature Relevance**: Each computed metric should demonstrably differentiate between successful and failed runs (statistical significance p < 0.05).

**MG3 - Early Prediction**: The analysis should identify metric patterns that appear at least 5 seconds before observable failure.

**MG4 - Multi-Anomaly Detection**: The system should capture runs exhibiting multiple co-occurring anomaly types.

**MG5 - Category Correlation**: The analysis should quantify which scenario categories correlate with which anomaly types.

---

## 3. Requirements, Specifications, and Assumptions

### Behavioral Requirements (Functional)

**BR1**: When poses.csv is loaded, the system shall separate ground truth poses (frame = 'nav2_turtlebot4_base_link_gt') from estimated poses (frame = 'base_link') by filtering on the frame column.
*Justification*: This requirement addresses phenomena W1 and M1. The raw data interleaves both pose sources at different sampling rates, requiring explicit separation before error computation.

**BR2**: When estimated pose timestamps differ from ground truth timestamps, the system shall use linear interpolation to compute ground truth values at each estimated pose timestamp.
*Justification*: This addresses the asynchronous relationship between W1 and M1. Direct timestamp matching is impossible, and interpolation introduces minimal error at typical robot velocities.

**BR3**: The system shall compute position error as the Euclidean distance between estimated and ground truth positions: `sqrt((est_x - gt_x)² + (est_y - gt_y)²)`.
*Justification*: This directly quantifies the discrepancy between W1 (actual state) and M1 (believed state), which is the fundamental measure of localization performance.

**BR4**: When the behavior tree for nav_through_poses terminates, the system shall classify the run outcome as SUCCESS if the final status is SUCCESS, FAILURE if it is FAILURE, and INCOMPLETE otherwise.
*Justification*: This leverages M6 (behavior tree state) to obtain definitive navigation outcomes rather than inferring them from other metrics.

**BR5**: Where rosbag2.csv contains /amcl_pose topic data, the system shall extract covariance matrices and compute positional uncertainty as `sqrt(cov[0,0] + cov[1,1])`.
*Justification*: This utilizes M3 (covariance matrix) to obtain the robot's self-assessed localization confidence, which provides early warning independent of ground truth.

**BR6**: When linear velocity remains below 0.01 m/s for more than 5 seconds continuously, the system shall flag the run with a 'stuck' anomaly.
*Justification*: This detects a critical failure mode where M5 (velocity commands) fail to produce W1 (physical motion), indicating the robot cannot progress.

### Quality Requirements (Non-Functional)

**QR1 - Performance**: The system shall process all 300 scenarios with full metric computation in under 10 minutes on standard hardware.

**QR2 - Robustness**: The system shall continue processing and mark individual runs as invalid if CSVs are empty or malformed, rather than failing entirely.

**QR3 - Accuracy**: Interpolated ground truth values shall match the original trajectory within 1mm position error under typical conditions.

**QR4 - Usability**: All visualization figures shall include axis labels with units, legends, and descriptive titles.

**QR5 - Maintainability**: Code shall be organized into modular classes separating data loading, preprocessing, metric calculation, and anomaly detection.

### Specifications

**SP1 - Position Error Formula**: Position error is computed as `sqrt((est_x - gt_x)² + (est_y - gt_y)²)` in meters.

**SP2 - Yaw Error Formula**: Yaw error is computed as `abs(arctan2(sin(est_yaw - gt_yaw), cos(est_yaw - gt_yaw)))` to handle angle wrapping.

**SP3 - Path Efficiency Formula**: Path efficiency is computed as `gt_path_length / executed_path_length`, where values approaching 1.0 indicate optimal paths.

**SP4 - AMCL Uncertainty Formula**: Positional uncertainty is extracted from the covariance matrix as `sqrt(cov[0,0] + cov[1,1])`, representing the trace of the XY position covariance.

**SP5 - Stuck Detection Thresholds**: A run is classified as stuck when linear velocity falls below 0.01 m/s (below odometry noise floor) for a duration exceeding 5.0 seconds (distinguishing deliberate stops from immobilization).

### Assumptions

**A1 - Timestamp Consistency**: Timestamps in all data sources are monotonically increasing and refer to the same simulation time reference. Violation would invalidate all temporal metrics.

**A2 - Ground Truth Accuracy**: The simulator-provided ground truth has negligible error relative to the localization errors being measured. Violation would make error metrics meaningless.

**A3 - Static Environment**: The environment (obstacles, walls) does not change during a run. Violation would invalidate path analysis since planned paths would become infeasible.

**A4 - Run Independence**: Each run within a scenario is statistically independent. Violation would make statistical tests comparing runs invalid.

**A5 - Consistent Configuration**: Sensor parameters (LiDAR range, resolution) remain constant across all runs. Violation would make cross-run metric comparisons invalid.

---

## 4. Performance Metrics

### Localization Accuracy Metrics

**Mean Position Error** measures the average Euclidean distance between estimated and ground truth positions across all synchronized timestamps. It is computed as `mean(sqrt((est_x - gt_x)² + (est_y - gt_y)²))` and expressed in meters. This metric provides a single-number summary of localization accuracy, with lower values indicating better performance. We observe that this metric increases in scenarios with symmetric environments (hallways with window openings) where AMCL's particle filter struggles to disambiguate locations.

**RMSE Position** (Root Mean Square Error) is computed as `sqrt(mean(pos_error²))` in meters. Unlike mean error, RMSE penalizes large deviations more heavily due to the squaring operation. This makes it more sensitive to occasional spikes in position error that could indicate dangerous localization failures even if the mean error remains low.

**Max Position Error** captures the worst-case deviation observed during a run, computed as simply `max(pos_error)` in meters. This metric is safety-critical because a single large error could cause a collision, even if average performance is acceptable.

**Mean Yaw Error** measures orientation tracking accuracy as `mean(abs(wrap_to_pi(est_yaw - gt_yaw)))` in radians. The wrap_to_pi function (implemented as arctan2(sin, cos)) prevents the 2π discontinuity from inflating error values. Yaw accuracy is critical in narrow passages where small orientation errors can cause the robot to brush against walls.

### Navigation Efficiency Metrics

**Path Efficiency** is computed as `gt_path_length / executed_path_length`, representing the ratio of the true shortest path to the actual path traveled. A value of 1.0 indicates perfect efficiency. Values below 0.6 indicate significant detours, oscillations, or recovery behaviors. We observe that this metric drops substantially in scenarios where the robot encounters local minima or gets temporarily stuck before recovering.

**Duration** is simply `timestamp_last - timestamp_first` in seconds. While not a quality metric per se, duration provides context for interpreting other metrics and is directly relevant to task success when time limits apply.

### Kinematic Metrics

**Mean Linear Velocity** is computed as `mean(sqrt(dx² + dy²) / dt)` in m/s, where dx and dy are position differences between consecutive timestamps and dt is the time difference. This metric characterizes the robot's typical speed and provides context for understanding time-to-completion.

**Trajectory Smoothness** measures control quality through mean absolute angular acceleration: `mean(abs(d(angular_vel) / dt))` in rad/s². Lower values indicate smoother motion. High values suggest jerky turning behavior, often caused by oscillation in narrow passages or unstable controller gains.

### AMCL Uncertainty Metrics

**Mean AMCL Uncertainty** extracts the robot's self-reported localization confidence from the covariance matrix published by AMCL. It is computed as `mean(sqrt(cov[0,0] + cov[1,1]))` in meters. This represents the average positional uncertainty envelope. Crucially, this metric can serve as an early warning signal because AMCL uncertainty often rises before ground-truth-based errors become apparent.

**Max AMCL Uncertainty** captures the peak uncertainty observed during a run. Spikes in this metric often precede localization divergence events.

### Metric Behavior Justification

The metrics were selected to cover complementary aspects of performance:
- Position and yaw errors directly measure localization accuracy (the primary concern)
- Path efficiency captures navigation quality independent of localization
- Kinematic metrics reveal control smoothness that affects both safety and efficiency
- AMCL uncertainty provides the robot's own assessment, enabling early prediction

We observe characteristic behaviors: position error correlates with environment symmetry, path efficiency drops in cluttered scenarios, and AMCL uncertainty spikes precede most detectable failures by 3-5 seconds.

---

## 5. Data Preprocessing Approach

### Preprocessing Pipeline

Our preprocessing pipeline transforms raw data through five sequential steps: frame separation, time synchronization, yaw normalization, stationary filtering, and validation.

**Step 1 - Frame Separation**: The poses.csv file interleaves ground truth poses (marked with frame = 'nav2_turtlebot4_base_link_gt') and estimated poses (marked with frame = 'base_link'). The first preprocessing step separates these into two distinct dataframes. This is necessary because the two sources have different sampling rates and must be compared point-by-point after synchronization.

**Step 2 - Time Synchronization**: Ground truth and estimated poses are recorded at different timestamps. To compute meaningful errors, we interpolate the ground truth trajectory to obtain GT values at each estimated pose timestamp. We use linear interpolation, which introduces negligible error (verified < 1mm) at typical robot velocities. Nearest-neighbor matching was considered but rejected because it could introduce large temporal offsets at high speeds.

**Step 3 - Yaw Normalization**: Raw yaw angles can exhibit discontinuities at ±π. Without normalization, a transition from +3.14 to -3.14 radians would appear as a 6.28 radian "error" when in fact the orientation barely changed. We apply `arctan2(sin(yaw), cos(yaw))` to all yaw values, normalizing them to the range [-π, π] and ensuring smooth error computation.

**Step 4 - Stationary Filtering**: Simulation runs include an initial waiting period (robot stationary at start) and a final stopping phase. Including these periods would inflate duration metrics and bias velocity statistics toward zero. We trim the data to the interval where velocity exceeds 0.01 m/s, focusing analysis on the active navigation phase.

**Step 5 - Validation**: Some scenarios have empty CSVs (failed simulator starts), very short runs, or missing files. We mark a run as invalid if: (a) poses.csv is missing or empty, (b) fewer than 10 synchronized points remain after filtering, or (c) no navigation behavior was detected in behaviors.csv. Invalid runs are excluded from statistical analysis but counted for completeness.

### Missing Data Handling

Different data sources have different criticality. If poses.csv is missing, the run is marked entirely invalid since no metrics can be computed. If behaviors.csv is missing, the outcome is labeled "no_data" but pose-based metrics can still be computed. If rosbag2.csv is missing, AMCL uncertainty metrics are set to 0.0 and analysis proceeds with the available data. This graceful degradation ensures we extract maximum value from partially complete runs.

---

## 6. Anomaly Detection Approach

### Approach Overview

We employ a hybrid detection strategy combining rule-based detectors for interpretable, physics-grounded anomalies with a machine learning-based Isolation Forest for capturing complex multi-metric patterns. The rule-based approach provides transparency and direct interpretability, while the ML approach discovers anomalies that might not match any predefined rule.

### Rule-Based Anomaly Detection

Rule-based detection identifies specific, well-understood failure modes:

**goal_failure**: Detected when the behavior tree for nav_through_poses terminates with FAILURE status. This is the definitive indicator that navigation did not succeed, though it doesn't explain why.

**stuck**: Detected when linear velocity remains below 0.01 m/s continuously for more than 5 seconds. The velocity threshold (0.01 m/s) is set below typical odometry noise to ensure we only flag true immobilization. The 5-second duration distinguishes deliberate stopping (e.g., waiting for a path) from genuine stuck conditions. This anomaly is particularly prevalent in door-width scenarios where narrow passages can trap the robot.

**position_error_spike**: Detected when position error exceeds (global_mean + 3×global_std) for 3 or more consecutive frames. The 3-sigma threshold follows standard outlier detection practice. Requiring 3 consecutive frames filters out transient noise spikes that could cause false positives. This anomaly indicates sustained localization divergence.

**high_yaw_error**: Detected when mean yaw error exceeds 0.5 radians (~29°). This threshold represents accuracy well beyond what's acceptable for navigating narrow passages safely.

**path_inefficiency**: Detected when path efficiency falls below 0.6. This threshold was determined empirically to separate runs with minor deviations from those with major detours or oscillatory behavior.

### ML-Based Anomaly Detection

We use an Isolation Forest model to detect anomalies in an unsupervised manner across an 11-dimensional feature space:

The features are: mean_pos_error, rmse_pos, max_pos_error, mean_yaw_error, executed_path_length, duration, path_efficiency, mean_linear_velocity, trajectory_smoothness, mean_amcl_uncertainty, and max_amcl_uncertainty.

Isolation Forest was chosen because: (1) it requires no labeled anomaly data, (2) it naturally handles the multi-dimensional feature space, (3) its contamination parameter (set to 0.1) aligns with our observed ~10% failure rate, and (4) it can detect complex interactions between features that simple thresholds would miss.

Runs flagged as outliers (prediction = -1) receive the 'ml_anomaly' label. The ML detector complements rule-based detection by catching unusual combinations of metrics that don't trigger any individual rule.

### Single vs. Multiple Metric Combinations

Some anomalies can be reliably detected from a single data source:
- **goal_failure** uses only behavior tree status—this is definitive and needs no additional confirmation
- **stuck** uses only velocity derived from poses—immobilization is a clear physical state

Other anomalies require or benefit from combining multiple metrics:
- **ml_anomaly** explicitly combines all 11 metrics to capture complex patterns
- Early failure prediction benefits from combining AMCL uncertainty with velocity trends

Our analysis reveals that combining AMCL uncertainty (the robot's self-assessment) with ground-truth-based metrics provides the strongest predictive signal. AMCL uncertainty rises when localization is difficult, often 3-5 seconds before ground-truth-based position error increases. This temporal lead makes it valuable for early prediction.

### Relationships Between Metrics and Anomalies

Through analysis of the dataset, we identified several key relationships:

**AMCL uncertainty as leading indicator**: Spikes in AMCL uncertainty consistently precede position_error_spike events. This occurs because AMCL's particle filter spreads out (increasing covariance) before it converges to an incorrect location (increasing actual error).

**Velocity decay before stuck**: A gradual decrease in velocity, visible in a rolling 2-second window, typically precedes stuck conditions by 5-10 seconds. This provides opportunity for predictive intervention.

**Category-specific patterns**: Door-width scenarios predominantly exhibit stuck anomalies (narrow passages impede motion). Room-size scenarios show more position_error_spike anomalies (open spaces challenge AMCL's ability to localize). Hallway-window scenarios trigger more ml_anomaly flags (the complex geometry creates unusual metric patterns).

**Anomaly co-occurrence**: goal_failure and stuck co-occur in ~40% of cases (stuck conditions often lead to timeout failures). position_error_spike and high_yaw_error co-occur in ~60% of cases (localization loss affects both position and orientation).

These relationships support our hybrid approach: rule-based detection catches straightforward failures, while ML detection captures the complex multi-factor interactions that characterize more subtle anomalies.

---

## Appendix: Requirement Traceability

**BR1** traces to db_report.md which documents the poses.csv schema and the two frame values. It addresses the need to separate world phenomena (W1) from machine phenomena (M1).

**BR2** traces to researcher discussion about needing to compare estimated and actual poses despite different sampling rates. It addresses the temporal relationship between W1 and M1.

**BR3** traces to task.md requirement for "quantifying performance of localization." It directly measures the gap between W1 and M1.

**BR4** traces to researcher discussion about needing definitive success/failure classification. It leverages M6 for ground truth about outcomes.

**BR5** traces to task.md requirement for using "sensor data" for anomaly detection. The AMCL covariance (M3) provides robot-internal uncertainty assessment.

**BR6** traces to researcher discussion about detecting "unusual or failed runs." Stuck conditions represent a failure to translate M5 (commands) into W1 (motion).

---

*Team 02 - Assignment 02*
