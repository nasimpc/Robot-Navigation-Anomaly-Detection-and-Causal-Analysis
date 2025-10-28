# Team Information

**Team Number**: 2 <br>
**Team Members**:  Marina, Keerthi, Nasim , Shariful, Chandrika <br>
**Project Title**: Analysis Framework for Evaluating Robot Localization and Navigation Performance in Simulation<br>
**Date**: 29 October 2025 <br>

# 1. Protocol for Requirement Elicitation & Follow-up questions 

## Participants

**Primary Stakeholder**: Mr. Samuel Wiest (Researcher and Dataset Owner) <br>
**Student Team Members**: Team 2 – Analysts and Developers  <br>
**Role**: The researcher provides domain knowledge, dataset context, and expected outcomes; the student team is responsible for identifying, defining, and implementing the analysis requirements.

## Question Format and Purpose

Questions are framed to explore organizational, technical, and data-related aspects of the project. Each aims to derive measurable requirements related to the testing framework.

* **Open-ended questions**: for understanding goals and expectations.
* **Closed-ended questions**: for verification and clarification.
* **Scenario-based questions**: for understanding workflow and outcomes.


## Categorization of Questions

### A. Organizational Questions

1. What are the key deliverables or insights expected from our analysis?
2. How will our findings contribute to improving the testing framework?
3. Should we focus on qualitative insights (e.g., anomaly detection) or quantitative results (e.g., performance metrics)?
4. How should visualizations and reports be structured for integration into future studies?

### B. Technical Questions

5. Which metrics best represent localization and navigation performance (e.g., RMSE, completion time, deviation)?
6. How do you define a failed or abnormal run in the dataset?
7. Should the analysis include dynamic visualization of trajectories and obstacles?
8. Are there preferred evaluation benchmarks or reference datasets?

### C. Data-Related Questions

9. What does the transform column represent — is it the robot’s real-time pose (position and orientation)?
10. How is sensor noise, dropout rate, or delay recorded in the logs?
11. Are the PGM and YAML map files used to represent static obstacles or full environment boundaries?
12. Should we correlate transforms, localization accuracy, and obstacle information together?
13. Are timestamps between estimated and ground truth trajectories synchronized or should we align them manually?

## Tools and Methods

**Primary Tools**: Python (Pandas, NumPy, Matplotlib, Seaborn), Jupyter Notebook
**Supporting Tools**: YAML parser, OpenCV, ROS2 bag data utilities
**Version Control**: GitHub for tracking requirements and progress

## Estimated Time and StructureTotal Duration: ~60 minutes

| **Activity**           | **Description**                             | **Duration** |
|-------------------------|---------------------------------------------|--------------|
| Data Familiarization    | Reviewing logs, YAML, and PG files          | 15 min       |
| Interview Session       | Oral discussion with Mr. Wiest              | 15 min       |
| Clarification Round     | Follow-up via email                         | 10 min       |
| Documentation           | Recording and validating insights           | 20 min       |


## Documentation and Verification

* Responses will be documented collaboratively using a shared online document.
* Key insights will be summarized and validated by Mr. Wiest via follow-up communication.
* All final clarifications will be logged with timestamps for traceability.

## Traceability and Validation Plan

* Each requirement will be linked to its corresponding question in a traceability matrix.
* Validation will occur through review and confirmation from Mr. Wiest.
* All updates will be version-controlled and dated for consistency.

## Follow-up Plan for Validation

After the initial elicitation and documentation of requirements, our team will conduct a structured follow-up to validate our interpretations and ensure that the extracted requirements accurately reflect the researcher’s intentions.

### 1. Internal Review Meeting

Team members will review the documented requirements and interpretations from the elicitation session.

Discrepancies, unclear items, or assumptions will be highlighted for clarification.

### 2. Vlidation Session with the Researcher (Samuel Wiest)

A short follow-up discussion (10–15 minutes) will be arranged with the researcher to confirm the accuracy of our understanding.

Each interpreted requirement will be presented in concise statements, and Samuel will be asked to confirm, modify, or elaborate.

Any feedback or corrections will be recorded immediately during the meeting.

### 3. Traceability Matrix Update

A traceability matrix will be maintained to map each validated requirement to its corresponding source question or dataset observation.

This ensures that every requirement can be traced back to a specific justification or user input.

### 4. Version Control and Documentation

The validated document will be saved as a new version (e.g., v2_Validated_Requirements.docx).
Changes and confirmations will be logged in a change-tracking table for auditability.

### 5. Continuous Validation Loop

As new data insights emerge in later assignments, the same validation process will be repeated to refine or expand requirements.

This ensures evolving alignment between analytical findings and project goals.

# 2. Preliminary Requirements (User Story Format)

The standard user story format is "As a [user role], I want to [perform an action] so that [I can achieve a goal/benefit].

##### Evaluate Navigation Accuracy

As a researcher, I want to compare the robot’s estimated path to the ground truth trajectory, so that I can measure how accurately the robot navigates.

##### Detect Abnormal or Failed Runs

As an analyst, I want to detect irregular or failed runs, so that we can identify possible causes of errors or instability.

##### Analyze Obstacle Impact

As a researcher, I want to study how obstacle size and position affect navigation accuracy, so that I can relate physical variations to robot performance.

##### Visualize Robot Trajectories

As a developer, I want to overlay robot paths on environment maps, so that I can visualize navigation and detect obstacle-related deviations.

##### Generate Performance Summaries

As a data analyst, I want to compute key statistics (e.g., deviation, completion time), so that comparisons can be made across multiple runs.

##### Integrate Multiple Data Sources

As a system designer, I want to merge map, transform, and sensor data, so that unified insights can be produced efficiently.

##### Ensure Scalability and Automation

As a developer, I want an automated and reusable data analysis pipeline, so that the same framework can handle larger datasets in the future

# 3. Plan for Gathering and Refining Requirements

1. **Initial Data Exploration**: Examine CSV, YAML, and map files to understand relationships among logs, transforms, and maps.
2. **Stakeholder Discussion**: Conduct an interview with Mr. Wiest to clarify expected analysis goals.
3. **Iterative Refinement**: Convert findings into detailed User Stories and validate through feedback.
4. **Traceability**: Maintain a mapping between questions and requirements for transparency.
5. **Validation**: Reconfirm final interpretations with Mr. Wiest before implementation.


















