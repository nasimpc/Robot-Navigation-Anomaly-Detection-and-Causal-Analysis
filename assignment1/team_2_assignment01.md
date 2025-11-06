# Team Information

**Team Number**: 2 <br>
**Team Members**:  Marina, Keerthi, Nasim , Shariful, Chandrika <br>
**Project Title**: *Evaluating Robot Localization and Navigation Performance in Simulation*<br>
**Date**: 5 October 2025 <br>

# 1. Protocol for Requirement Elicitation & Follow-up questions 

  This document outlines our team’s structured approach for understanding and defining requirements related to the testing framework for evaluating robot localization and navigation performance in simulation.  
  Based on the researcher’s initial email, the goal is to identify performance indicators, detect anomalies, and analyze correlations between scenario variations and navigation outcomes.  
The following sections present our protocol for conducting the follow-up discussion, preliminary requirements, and our plan for gathering and refining requirements.

## Participants
| Role | Name / Description |
|------|--------------------|
| **Primary Stakeholder** | Mr. Samuel Wiest (Researcher and Dataset Owner) |
| **Student Team** | Team 2 – Marina, Keerthi, Nasim, Shariful, Chandrika |
| **Responsibilities** | Researcher provides domain knowledge, dataset context, and expected outcomes. The student team identifies, defines, and implements analysis requirements. |

## Question Format and Purpose

Questions are framed to explore **high-level goals** and **specific data needs**.

- **Open-ended questions:** To explore motivations, goals, and expectations.  
- **Closed-ended questions:** To verify assumptions and confirm details.  
- **Scenario-based questions:** To understand decision-making, workflow, and expected outputs.  


## Categorization of Questions

### **B. Technical Questions (Goal: Identify performance metrics and tools)**
1. In case localization and navigation perfomance analysis, Which evaluation metrics do you consider most important?
(For example: total path length, time required to reach the goal, success rate, localization error such as RMSE, number of re-plans, collision count, average cross-track error, cumulative rotation, etc.)
Please mention any metrics you currently use or prioritize.
2. Do you have any preferred tolerance values or limits?
(For instance: acceptable distance-to-goal error in meters, allowable orientation deviation in radians, or maximum collision/contact force thresholds.)
3. How do you define a successful run?
(e.g., reaching the goal within tolerance, no collisions, completion within a time limit, or maintaining stable localization.)
4. To better process TFMesssages, please mention TF tree conventions you use? (Please list the frame names and relationships — for example: map, odom, base_link, camera_link, imu_link, etc.)

### **C. Data-Related Questions (Goal: Clarify data content and structure)**

5. Could you please clarify what the information in the “data” column of the /scenario_status topic represents? For instance, entries such as
bag_record(BEHAVIOUR): RUNNING > SUCCESS or differential_drive_robot.nav_through_poses(BEHAVIOUR): INVALID > RUNNING?
6. We observe that AMCL pose estimates are much sparser than ground-truth poses. Could you confirm the expected publish/logging rates for AMCL versus ground truth and whether any throttling, downsampling, or event-triggered logging explains this discrepancy ?
7. In the Hallways scenarios, All 3 rosbag2-derived CSVs show the robot immobile due to initial spawn collisions or overlap between the robot start pose and static obstacles (scenario.variant). For localization performance analysis, should these runs be excluded as invalid, or retained with a distinct label (e.g., “spawn-collision/immobile”)? 
### **A. Organizational Questions (Goal: Understand expectations and scope)**

8. What is the main research objective or focus you would like students to address in this assignment (e.g., anomaly detection, metric formulation, correlation study, or dashboard development)?
9. How will these contribute to improving the testing framework?
10. Should the team adhere to any specific coding standards or repository structure?
11. Who will serve as the primary contact for data-related questions or clarifications, and what are the preferred communication method ?
12. Are there any reference results or benchmark values that students should use for comparison (e.g., baseline success rate or localization RMSE)?
13. Do you expect students to conduct new simulations with modified parameters, or should they limit their work to analyzing the existing dataset?
14. Should we focus on qualitative insights (e.g., anomaly detection) or quantitative results (e.g., performance metrics)?


## Tools and Methods

| Category | Tools / Methods |
|-----------|----------------|
| **Primary Tools** | Python (Pandas, Matplotlib), Jupyter Notebook |
| **Supporting Tools** | YAML parser, OpenCV, ROS2 bag data utilities |
| **Version Control** | Git (for requirement tracking and progress management) |

## Estimated Time and StructureTotal Duration: ~60 minutes

| **Activity** | **Description** | **Estimated Duration** |
|--------------|-----------------|-------------------------|
| **Data Familiarization** | Review and understand dataset contents (CSV logs, YAML, and map files) to identify relevant parameters for localization and navigation. | 1.5 days |
| **Question Preparation** | Formulate and refine follow-up questions categorized under organizational, technical, and data-related aspects. | 0.5 day |
| **Interview Session** | Conduct a short virtual meeting with Mr. Wiest to clarify goals, expectations, and dataset details. | 15 minutes |
| **Clarification and Feedback Round** | Exchange follow-up emails or messages to resolve pending questions after the interview. | 0.5 day |
| **Documentation and Analysis** | Compile insights, summarize responses, and prepare preliminary requirements collaboratively as a team. | 2 days |
| **Validation and Review** | Conduct internal review and finalize the validated requirement document for submission. | 1 day |

**Total Duration:** ~6 days (distributed across the week)

## Documentation and Verification

* Responses will be documented collaboratively using a shared online document.
* Key insights will be summarized and validated by Mr. Wiest via follow-up communication.
* All final clarifications will be logged with timestamps for traceability.

## Traceability and Validation Plan

1. Each requirement will be linked to its **source question** in a traceability matrix.  
2. Validation will occur through review and confirmation from the stakeholder.  
3. Updates will be version-controlled, dated, and logged for consistency.  

## Follow-up Plan for Validation

After the initial elicitation and documentation of requirements, our team will conduct a structured follow-up to validate our interpretations and ensure that the extracted requirements accurately reflect the researcher’s intentions.

#### **1. Internal Review Meeting**
- Team members review documented requirements for clarity and correctness.  
- Any assumptions or unclear items are flagged for clarification.

#### **2. Validation Session with the Researcher**
- Conduct a short (10–15 min) discussion with Mr. Wiest to confirm interpretations.  
- Present each requirement concisely for direct confirmation or correction.

#### **3. Traceability Matrix Update**
- Maintain a mapping between validated requirements and their source questions or dataset observations.

#### **4. Version Control and Documentation**
- Save the validated requirements as a new version (e.g., `v2_Validated_Requirements.md`).  
- Maintain a **change log table** summarizing updates and reviewer confirmations.

#### **5. Continuous Validation Loop**
- Repeat the same process for later datasets or updated analysis tasks.  
- Ensures evolving alignment between data findings and research goals.  

# 2. Preliminary Requirements (User Story Format)
Based on the email, the following **preliminary requirements** have been identified and expressed in **User Story format**.

<!-- The standard user story structure is:  
**"As a [user role], I want to [perform an action] so that [I can achieve a goal or benefit]."** -->

| **ID** | **Heading** | **User Story** |
|--------|--------------|----------------|
| R1 | Data Cleaning & Overview| As a data analyst, I want to clean and preprocess the robot rosbag2 dataset so that I can obtain a consistent and accurate basis for further analysis.
| R2 | Behavioral Analysis Across cenarios| As a robotics researcher, I want to compare robot behavior across different scenarios (circle, hallways, large room, rooms) and multiple runs so that I can identify how environment and layout affect performance.
| R3 | Sensor Variation Impact | As a system analyst, I want to study how sensor disturbances and data drop rates influence localization and navigation accuracy.
| R4 | Analyze Obstacle Impact | As a researcher, I want to study how obstacle size and position affect navigation & localization accuracy. |
| R5 | Failure Detection | As an experiment evaluator, I want to identify and classify unusual or failed runs so that I can isolate performance outliers and sources of error.
| R6 | Scenario–Performance Correlation | As a data scientist, I want to correlate scenario variations (e.g., map layout, obstacle placement, start/goal positions) with performance metrics (e.g., time-to-goal, success rate, localization error) so that I can derive meaningful insights about robot localization & navigation efficiency.
| R7 | Visualization | As a data explorer, I want to create visualizations (plots and graphs) that summarize key factors so that I can visually interpret trends and anomalies in robot localization and navigation.
| R8 | Statistical Summary | As a researcher, I want to generate a statistical overview (e.g., means, variances, missing values) so that I can understand the overall characteristics of the data.


# 3. Plan for Gathering and Refining Requirements

### **Step 1 – Initial Data Exploration**
- Examine the dataset (CSV, YAML, and PGM files) to understand relationships among transforms, logs, and maps.  
- Identify missing or redundant values, and prepare for data cleaning.  

### **Step 2 – Stakeholder Discussion**
- Conduct a structured interview with Mr. Wiest to clarify analysis objectives and expected visualizations.  
- Record all responses in a shared document for consistency.  

### **Step 3 – Iterative Refinement**
- Convert insights into **User Stories** and refine based on continuous stakeholder feedback.  
- Maintain change-tracking to record evolution of requirements.  

### **Step 4 – Traceability and Validation**
- Develop a simple **traceability matrix** mapping questions ↔ requirements ↔ code implementation.  

### **Step 5 – Continuous Review**
- Review and refine requirements **after each dataset phase or analysis milestone** (e.g., after Run 1–3).  
- Revalidate updated stories with Mr. Wiest for approval.





















