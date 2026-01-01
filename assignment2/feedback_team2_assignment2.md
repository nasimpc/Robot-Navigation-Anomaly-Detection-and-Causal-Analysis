## Feedback

### Document (70 Points)
1. A list of world and machine phenomena. A list of goals (system and feature goals, user goals, and model goals), requirements (behavioral and quality requirements), specifications, and assumptions categorized appropriately (atleast 5 each) ( 20/20)
    - 

2. A list of performance metrics with rationale in the scope of the project, along with the formula used for their calculation. Reason over your approach for data preprocessing ( 20/20)
    - All metrics are well defined and their relevance is well explained
    - Data-preprocessing is very well executed and justified
    

3. Justification for your approach to anomaly detection and explanation over their behavior. Reasoning over identification of single or multiple combination of sensor and/or metric data in identifying anomalies, and the identification of relationships between metrics and anomalies for their early prediction. Ensure it is suitably formatted for presenting during the tutorial session ( 30/30)
    - Rule-based anomaly detection is well covered
    - ML-based anomaly detection explanation is clear. It is unclear if you could detect anomaly at a particular instace of time or is it only possible to label a run as anomalous. If not, how do you justify your approach orhow do you plan to detect a time stamp at which an anomaly is observed?
    - Have you categorised anomalies detected via Isolation Forest?
    - Relaiton between metrics and anomalies and their early prediction is very well justified. The meaning of "early_smoothness" is not clear
    - The correlation matrix is well summarised. Could you also infer when isolation 
    - All fields used in analysis_summary.csv looks good

### Code and Visualizations  (30 Points)
1. Code modularity, reusability, and readability, implementation of anomaly-detection pipeline  ( /20)


3. Relevance and clarity of visualizations with appropriate labels, headers, units, and legends ( 10/10)
    - All plots are very well represented
    - Some observations from feature importance for early anomaly prediction are interesting, especially most of negative coefficients

Score: /100