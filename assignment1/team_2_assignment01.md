# Team Information

**Team Number**: 2 <br>
**Team Members**:  Marina, Keerthi, Nasim , Shariful, Chandrika <br>
**Project Title**: *Analysis Framework for Evaluating Robot Localization and Navigation Performance in Simulation*<br>
**Date**: 29 October 2025 <br>

# 1. Protocol for Requirement Elicitation & Follow-up questions 

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

### **A. Organizational Questions (Goal: Understand expectations and scope)**

1. What are the key deliverables or insights expected from our analysis?
2. How will our findings contribute to improving the testing framework?
3. Should we focus on qualitative insights (e.g., anomaly detection) or quantitative results (e.g., performance metrics)?
4. How should visualizations and reports be structured for integration into future studies?

### **B. Technical Questions (Goal: Identify performance metrics and tools)**

5. Which metrics best represent localization and navigation performance (e.g., RMSE, completion time, deviation)?
6. How do you define a failed or abnormal run in the dataset?
7. Should the analysis include dynamic visualization of trajectories and obstacles?
8. Are there preferred evaluation benchmarks or reference datasets?

### **C. Data-Related Questions (Goal: Clarify data content and structure)**

9. What does the transform column represent — is it the robot’s real-time pose (position and orientation)?
10. How is sensor noise, dropout rate, or delay recorded in the logs?
11. Are the PGM and YAML map files used to represent static obstacles or full environment boundaries?
12. Should we correlate transforms, localization accuracy, and obstacle information together?

## Tools and Methods

| Category | Tools / Methods |
|-----------|----------------|
| **Primary Tools** | Python (Pandas, NumPy, Matplotlib, Seaborn), Jupyter Notebook |
| **Supporting Tools** | YAML parser, OpenCV, ROS2 bag data utilities |
| **Version Control** | GitHub (for requirement tracking and progress management) |

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
Based on the follow-up questions and stakeholder discussions, the following **preliminary requirements** have been identified.  
These are expressed in **User Story format**, which clearly defines the user role, action, and purpose behind each requirement.

The standard user story structure is:  
**"As a [user role], I want to [perform an action] so that [I can achieve a goal or benefit]."**

| **ID** | **Heading** | **User Story** |
|--------|--------------|----------------|
| R1 | Evaluate Navigation Accuracy | As a researcher, I want to compare the robot’s estimated path to the ground truth trajectory, so that I can measure navigation accuracy. |
| R2 | Detect Abnormal or Failed Runs | As an analyst, I want to detect irregular or failed runs, so that I can identify possible causes of errors or instability. |
| R3 | Analyze Obstacle Impact | As a researcher, I want to study how obstacle size and position affect navigation accuracy, so that I can relate physical variations to robot performance. |
| R4 | Visualize Robot Trajectories | As a developer, I want to overlay robot paths on environment maps, so that I can visualize navigation and detect obstacle-related deviations. |
| R5 | Generate Performance Summaries | As a data analyst, I want to compute key statistics such as deviation and completion time, so that comparisons can be made across multiple runs. |
| R6 | Integrate Multiple Data Sources | As a system designer, I want to merge map, transform, and sensor data, so that unified insights can be produced efficiently. |
| R7 | Ensure Scalability and Automation | As a developer, I want an automated and reusable data analysis pipeline, so that the same framework can handle larger datasets in the future. |


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

















