## Assignment 03

Building on the anomaly-detection pipeline from Assignment 02, this assignment focuses on identifying the relationships between environment features and the navigation task that lead to failures across scenario variations. Your goal is to derive generalizable, human-interpretable rules that explain failures/anamolies across both known and unseen scenarios, backed by the available data, and use these rules to predict outcomes and the expected failure location without inspecting logs.

You will also create your own validation scenario files that cover the full range of geometric variability and can be used to thoroughly validate and refine the derived rules.

Please find the geometric coordinate details of all variations of existing maps at this [link](https://nc.uni-bremen.de/index.php/s/jK2f2ceNWgLRazK).

---

### Task

1. Identify and extract all relevant features from the environment, the robot, and the task. These may include (but are not limited to):
    - Robot features: sensor height, robot footprint
    - Map geometry: walls, door sizes, corridor width
    - Environment variations: obstacle size, shape, and location
    - Sensor-related factors: noise levels
    - Other geometric elements: window height and placement

2. Using the failure cases and anomalies from Assignment 02, identify the relationships between these features that lead to failure. This may involve evaluating geometric constraints, threshold conditions, or combinations of feature relations that consistently appear in failure cases. These relations can be represented using First-Order Logic (FOL), a standard formalism for expressing structured, interpretable rules [1].
You may use any systematic approach to derive these rules, for example (you are free to use any justifiable approach of your choice):
    - Enumerating possible relations (e.g., distances, angles, relative positions) and checking which ones hold true in failure cases
    - Comparing the truth values of relations in success vs. failure scenarios
    - Searching for consistent patterns or minimal sets of relations that leads to failure
    Example: distance(obstacle, wall_id) < X cm AND inbetween(waypoint, obstacle, wall)

3. Demonstrate that these relations generalize across the dataset by reporting:
    - How frequently each relation appears in all scenarios
    - How often it corresponds to failure vs. success

4. Provide your own set of scenario files for validating and further refining your derived rules, and justify how your scenarios cover the full range of environment variability

---

### Deliverables

1. **Document**: (50 Points)
  Submit a single markdown file containing:
    - **Feature List** (5 pts): Concise list of all ientified and/or extracted robot, environment, and task features with short relevance notes
    - **Relations & Root Causes** (15 pts): Human-interpretable relations between multiple features and the task that cause failures or anomalies. Describe the procedure used to derive these rules
    - **Generalization Analysis** (10 pts): Counts of how often each relation appears across scenarios and how often it correctly predicts the outcome
    - **Custom Scenarios** (20 pts): Your own scenario files + short justification of how they cover all environment variability and which rules they validate or help to refine
    - Use the following format of filename format: team_\<number\>_assignment03.md (Example: team_1_assignment03.md)

2. Code + Visualizations (50 Points)
    - Implementation of feature extraction and derivation of rules (20 pts)
    - Analysis of relation occurrences across scenarios (20 pts)
    - Store all generated figures in the `images/` folder within your submission directory. This includes visualisation of results for task 2 and confusion matrix for task 3. Please feel free to include any additional plots that helps to present your results based on your approach (10 pts)

**Note**:  
- Submit all files and folders in the same folder level where *task.md* is located by **17:00 on December 17, 2025**  
- **Presenting your assignment** during the tutorial session scheduled after the deadline is mandatory to receive a grade for the assignment. Otherwise, the submission will not be graded     

---

### Resources
[1] [First order logc](https://en.wikipedia.org/wiki/First-order_logic)