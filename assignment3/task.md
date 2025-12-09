## Assignment 03

Building on the anomaly-detection pipeline from Assignment 02, this assignment focuses on identifying the relationships between environment features and the navigation task that lead to failures across scenario variations. Your goal is to derive generalizable, human-interpretable rules that explain failures/anomalies across both known and unseen scenarios, supported by the available data, and later use these rules to predict outcomes and the expected failure location **without inspecting the logs**.

You will also create your own validation scenario files that cover the full range of geometric variability and can be used to thoroughly validate and refine the derived rules.

Please find the geometric coordinate details of all variations of existing maps at this [link](https://nc.uni-bremen.de/index.php/s/jK2f2ceNWgLRazK).

---

### Task

1. **Identify relevant features, functions, atomic relations, and contexts from scenarios**

    Based on the dataset you have,
    - Identify relevant features from the environment, the robot, and the task. These may include (but are not exhaustive here):
        - Robot features: sensor height, robot footprint
        - Map geometry: walls, door sizes, corridor width
        - Environment variations: obstacle size, shape, and location
        - Sensor-related factors: noise levels
    - Define a set of computable functions *F = {f<sub>1</sub>, f<sub>2</sub>, .., f<sub>n</sub>}*, that can be evaluated per timestamp for the turtlebot or can be constant across the entire scenario   
    Examples: `distance(turtlebot, closest_wall)`, `noise(lidar)`
    - Define a set of atomic relations *R = {r<sub>1</sub>, r<sub>2</sub>, .., r<sub>n</sub>}*, where each atomic relation is a computable predicate that evaluates to a truth value. These relations may include some of your hypothesis for failure. It can be composed of some of the features and the functions defined earlier   
    Examples: `distance(turtlebot, closest_wall) < robot_radius`, `in_between(waypoint, closest_obstacle, closest_wall)`, `noise(lidar) > 0.05`, `door_width(room_id) < robot_width`, `distance(waypoint, closest wall) < robot_radius`
    - Since not all atomic relations are relevant in every situation, identify and define a set of contexts *C*, and list which atomic relations and functions should be evaluated in each context   
    Example: `C = {robot_near_door, robot_near_obstacle, ...}`, where *door_width(room_id) < robot_width* needs to be evaluated only when *robot_near_door* context is active, or when waypoints connect both spaces. Some relations may be relevant across multiple contexts or even all contexts

2. **Create feature vectors for every context at anomalies**

    Evaluate the set of atomic relations and relevant continuous functions every identified anomaly timestamp, for the contexts are active at that anomaly. For each context, create feature vectors that include both the truth values of atomic relations and the corresponding continuous function values. Normalize continuous function values if you consider it necessary


3. **Use multi-dimensional clustering to derive patterns**
    - Apply multi-dimensional clustering methods to determine which atomic relations and boundaries for continuous-function values that consistently satisfy across anomalies within each context
    - Express the identified relations using First-Order Logic (FOL), a standard formalism for structured, interpretable rules [1]  
    - *Example*: A relation that holds at every time step *t* when the robot fails in a context C<sub>k</sub>​ can be represented as:   
    ∀ t ∈ C<sub>k</sub>​, distance(robot, closest_wall) < 0.1m ∧ diameter(turtlebot) < door_width(room_id) ∧ waypoint_across(door_id) ⇒ Anomaly

4. Demonstrate that these relations generalize across the dataset by reporting:
    - How frequently each derived relations appear across all scenarios in relevant contexts?
    - How often each relation corresponds to an anomaly versus a success?
    - How often each relation correctly predicts the outcome (true positives, false positives, etc.)?

5. Provide your own set of scenario files for validating and further refining your derived rules, and justify that these scenarios cover the full range of environment variability (optional for this assignment, but will be part of project deliverable)

---

### Deliverables

1. **Document**: (50 Points)
  Submit a single markdown file containing:
    - **Feature List** (25 pts): Concise list of all identified features, functions, atomic relations, and contexts with mapping to relevant atomic relations and functions with short relevance notes
    - **Relations & Root Causes** (10 pts): Human-interpretable relations between multiple features and the task that cause failures or anomalies. Describe the procedure used to derive these rules
    - **Generalization Analysis** (15 pts): Frequency of how often each relation appears across scenarios in relevant contexts and how often it correctly predicts the outcome
    - **Custom Scenarios** (optional for this assignment, but will be part of project deliverable): Your own scenario files with a short justification of how they cover all environment variability and which rules they validate or help to refine
    - Use the following format of filename format: team_\<number\>_assignment03.md (Example: team_1_assignment03.md)

2. Code + Visualizations (50 Points)
    - Implementation of feature extraction (10 pts)
    - Derivation of rules based on multi-dimensional clustering approach (15 pts)
    - Analysis of relation occurrences across scenarios (15 pts)
    - Store all generated figures in the `images/` folder within your submission directory. This includes visualization of results for clustering task and confusion matrix for generalization demonstration. Please feel free to include any additional plots that helps present your results based on your approach (10 pts)

**Note**:
- Submit all files and folders in the same folder level where *task.md* is located by **17:00 on December 22, 2025**
- **Presenting your assignment** during the tutorial session scheduled after the deadline is mandatory to receive a grade for the assignment. Otherwise, the submission will not be graded

---

### Resources
[1] [First-order logic wikipedia page](https://en.wikipedia.org/wiki/First-order_logic)