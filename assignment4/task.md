## Assignment 04 [Final Project Description]

As part of the final project, you will consolidate and refine the approaches developed in previous assignments into a coherent, end-to-end pipeline, with a strong emphasis on justification of design choices, traceability, and generalization.

Your work should clearly demonstrate how data, metrics, anomaly detection, and causal reasoning interact within a unified framework.

Specifically, your project should address the following aspects:

1. **Traceability of requirements**: Mapping between requirements and related design decisions in the selection of metrics, algorithms for anomalies, and causal reasoning, and justifying if and how individual requirements were met.

2. **Data understanding and summarization**: statistical overview of available dataset, file formats, sensor logs, and constituents of scenario descriptions.

3. **Feature identification and extraction**: Listing of all relevant features derived from scenario descriptions, environment geometry, robot properties, and logs. Justification of feature relevance for anomaly detection and causal analysis, by considering the role of the complete pipeline.

4. **Metric definition and justification**: Definition of all metrics derived from the data. Justification of each metric in the perspective of its role in anomaly detection, and causal reasoning.

5. **Anomaly detection approach and validation**: Description and justification for the chosen anomaly-detection methods. Methodology used to validate and evaluate performance of anomaly detection.

6. **Causal analysis and root-cause identification**: Approach for identifying causes of anomalies using environment–task–robot relations. Justification of causal assumptions and representations and the methodology used to validate causal explanations.

7. **End-to-end pipeline design**: Your pipeline should support the following two modes:
    - Scenario-based prediction: Taking only the scenario description, robot information, and environment JSON file as input to predict any possible anomalies and to explain the reason.
    - Log-based prediction: Taking logs, CSV files, scenario description, robot information, and environment JSON file as input to detect and reason about anomalies.

8. **Answer these questions**:
    - Generalization and scalability: Discussion of how the proposed approach can generalize to different robots and environments and describe required variations in data to support such generalization.
    - Challenges and insights: What are the major challenges encountered during the project? Discuss unique insights gained in terms of approach and results.

---

### Deliverables

1. **Document** (100 Points): Submit a single concise and well-structured markdown file containing all the above elements. Evaluation criteria include:
    - Clarity of explanations and utilization of data
    - Strength of justification for design choices
    - Traceability across of requirements across design decisions in metrics, anomalies, and causal analysis
    - Validation and evaluation of algorithms and inference of results
    - Note: Use the following naming convention for the filename: team_\<number\>_project_submission.md (Example: team_1_project_submission.md)

2. **Code + Visualizations** (100 Points): Submit your implementation as a Python script or package that includes the complete pipeline. It will be evaluated based on:
    - Code quality, modularity, and best practices (40 points)
    - Well-documented instructions for installation of particular versions of libraries being used and using your pipeline (20 points)
    - Supporting visualizations representing available data, insights from the results and validation of algorithms used for anomaly detection and causal analysis (40)

### Project presentation evaluation criteria

1. Slides: Use of Space, Conveying Method, Time Management (20%)
    - Prefer figures, plots, tables, and diagrams over text
    - Clear visibility of plots
    - Avoid text-heavy slides (≤5–7 bullets, concise lines)
    - Slide titles must exactly match the content
    - Use consistent formatting, slide numbers, and good color contrast
2. Justification of Design Choices (25%)
    - Justification of all design choices
    - Explanation of any parameterisation
3. Connectivity & Traceability (30%)
    - Maintain a clear flow, **for example**:   
        → requirements  
        → overview of available data and optionally highlight any pre-processing step (eg: normalisation)   
        → metrics identified with justification how you ensure it covers insights from dataset  
        → detection and classification of anomalies based on abnormal metric behavior  
        → correlations between metrics at these anomalies  
        → early prediction insights  
        → validation of anomaly detection and prediction  
        → causality analysis methodology + justification  
        → insights and validation  
    - Justify how each requirements were met and influenced decision making throughout the presentation to ensure traceability
    - Explicitly map metrics to where they are used
    - Clearly distinguish causes vs symptoms. Though not explicitly in slides, but one should be aware of this while structuring and explaining the slides
4. Technical Rigour (25%)
    - Coverage of metrics
    - Understanding of the problem
    - Inferences derived
    - Backing up statements/claims with statistical data
    - Validation of algorithms


**Note**:
- Submit all files and folders in the same folder level where *task.md* is located by **22:00 on January 23, 2026**
- Upload presentation slides by **08:00 on Jauary 26, 2026**
- The final project presentation is scheduled for **January 27, 2026 (14:00–16:00)** and is graded separately for an additional 200 points.