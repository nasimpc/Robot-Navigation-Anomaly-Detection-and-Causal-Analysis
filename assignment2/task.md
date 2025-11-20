## Assignment 02

This assignment builds on the work completed in Assignment 01, where you explored the dataset and developed a protocol for interacting with the researcher. In this phase, you will translate the outcomes of that discussion into a structured set of goals, requirements, specifications, and assumptions, and create a plan for evaluating them.

On the implementation side, the task involves systematic data preprocessing, defining quantitative metrics for evaluating robot navigation and localization performance, and conducting anomaly detection and prediction.

Through this process, you will transform unstructured logs into interpretable metrics, detect anomalies and identify patterns to predict anomalies. This establishes the foundation for subsequent causal reasoning and predictive modeling based on variations in the scenarios.

You have used a sample dataset for the first assignment. Please download the complete dataset from this [link](https://nc.uni-bremen.de/index.php/s/jK2f2ceNWgLRazK).

---

### Task

1. Write a concise set of **Goals** which are abstracted into *System and Feature Goals, User Goals, and Model Goals* [1]

2. Using insights from the discussion with researcher, 
    - Identify the **world and machine phenomena** in this causality analysis problem and write a *traceable* set of **behavioral and quality (functional and non-functional) requirements, specifications, and relevant assumptions** (at least five for each), justifying their classification based on the identified world and machine phenomena [2,3]. Please refer to the references in the first assignment to select a particular format for writing requirements    
    - Include a short explanation of each requirement and a traceability note linking it to the interview or protocol question for your future reference in the **appendix** (not graded)   

3. **Define performance metrics**
    - Based on the available dataset and knowledge of variations in the dataset, **determine metrics** for quatifying performance of localization and navigation
    - **Justify your choice of metrics** and explain their behavior with probable reasons for their characteristics 

4. **Data cleaning and anomaly detection**
    - Extend your previous data preprocessing implementation to handle missing, irrelevant, or noisy data
    - Make use of the defined metrics and available data to detect and label the anomalies, which include failure to reach goal or any unexpected and non-ideal behavior
    - Based on the metrics and available data, determine whether single source or combination of them could lead to identifying each anomaly and reason about it. One could use learning based (eg: clustering) or rule-based approach for this and correlate to anomalies
    - Identify patterns in the sensor data and your metrics that could 'robustly' predict the identified anomalies

---

### Deliverables

1. **Document**: (70 Points)  
  Submit a single markdown file containing:
    - A list of world and machine phenomena. A list of goals (system and feature goals, user goals, and model goals), requirements (behavioral and quality requirements), specifications, and assumptions categorized appropriately (atleast 5 each) (20 Points)
      - Evaluation criteria: Coverage, correct classification, and clarity of statements
    - A list of performance metrics with rationale in the scope of the project, along with the formula used for their calculation. Reason over your approach for data preprocessing (20 Points)
      - Evaluation criteria: Relevance, measurability, and completeness of metrics. Clarity in reasoning for data preprocessing
    - Justification for your approach to anomaly detection and explanation over their behavior. Reasoning over identification of single or multiple combination of sensor and/or metric data in identifying anomalies, and the identification of relationships between metrics and anomalies for their early prediction. Ensure it is suitably formatted for presenting during the tutorial session (30 Points)
      - Evaluation criteria: Clarity of explanation and soundness of reasoning
  
    - Use the following format of filename format: team_\<number\>_assignment02.md (Example: team_1_assignment02.md)

2. **Code and visualizations**: (30 Points)  
    - Include a Jupyter Notebook (team_\<number\>_assignment02.ipynb) demonstrating:
      - Data preprocessing steps
      - Computation of defined metrics
      - Implementation of anomaly-detection pipeline
      - Visualizations illustrating anomalies, relation between multiple (if exists) metrics and the anomaly, evidence for early prediction of anomaly based on sensor and/or metric data and their correlation
    - Store all generated figures in the `images/` folder within your submission directory.
    - Evaluation criteria:
      - Code modularity, reusability, and readability (20 Points)
      - Relevance and clarity of visualizations with appropriate labels, headers, units, and legends (10 Points)

**Note**:  
- Submit all files and folders in the same folder level where *task.md* is located by **17:00 on November 19, 2025**  
- **Presenting your assignment** during the tutorial session scheduled after the deadline is mandatory to receive a grade for the assignment. Otherwise, the submission will not be graded     

---


### Resources
[1] [Machine Learning in Production: From Models to Products, Chapter 05](https://mlip-cmu.github.io/book/05-setting-and-measuring-goals.html)  
[2] [Machine Learning in Production: From Models to Products, Chapter 06](https://mlip-cmu.github.io/book/06-gathering-requirements.html)  
[3] [Jackson, Michael. "The world and the machine." Proceedings of the 17th ICSE. 1995.](https://dl.acm.org/doi/pdf/10.1145/225014.225041)