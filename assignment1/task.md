## Assignment 01

This assignment introduces you to a dataset collected from a testing framework for **robot localization and navigation**.  
It includes an **email from a researcher** explaining the motivation for creating this dataset and an overview of potential insights that can be extracted from it.

In this assignment, you will familiarize yourself with the dataset and prepare a set of follow-up questions and a protocol for discussing these with the researcher during the next lab session as part of the requirements elicitation process.

---

### Background

**Localization** involves determining where the robot is within a given environment by referring to a known map (eg: an [occupancy grid map](https://en.wikipedia.org/wiki/Occupancy_grid_mapping) ) and using available sensor data such as [LiDAR data](https://en.wikipedia.org/wiki/Lidar) and [odometry](https://en.wikipedia.org/wiki/Odometry) to infer its location within the map.  
**Navigation** involves moving the robot from a start pose to a goal pose by planning a path using the map and available sensor data and controlling the robot to follow it, optionally through a predefined set of waypoints.

For a more conceptual understanding, please refer to the **Nav2 documentation** [1].  
You are also encouraged to explore additional resources and blogs for a deeper understanding of the individual concepts described there.

---

### Email from the researcher


> Dear Students,
> 
> I am working on a testing framework for evaluating robot localization and navigation performance in simulation. The broader goal is to analyze and correlate different factors that may influence how well a robot performs its navigation tasks.
> 
> The framework considers several kinds of variations in simulated scenarios, such as:
> 1. Differences in map structures and layouts
> 2. Location and size of obstacles
> 3. Variations or disturbances in sensor data and its drop rate
> 4. Changes in starting and goal positions, including varying waypoints
> 
> I have collected a substantial dataset from multiple simulated TurtleBot runs that cover these kinds of variations. The dataset includes scenario-related information and various logs recorded during each run.
> 
> This dataset provides opportunities to:
> 1. Examine robot behavior across different conditions
> 2. Define and analyze navigation-related performance indicators
> 3. Identify or classify unusual or failed runs
> 4. Explore possible relationships between scenario variations and performance outcomes
> 
> I am interested in your perspectives on how to approach the analysis of this dataset. In particular, how you might define and measure performance, detect anomalies or failures, and reason about possible correlations.
> 
> Best regards,  
> Samuel Wiest

---

### Task

1. **Prepare protocol for follow-up questions:** 
    - Understand the dataset and Samuel’s email carefully to identify the main problem, goals, and possible open questions
    - Refer to [2], [3], and [4] for guidance on structuring interview questions for requirements elicitation
    - Prepare a document with a set of targeted questions (technical, organizational, and data-related)
    - Define a clear protocol for collecting the desired information. Specify the format of questions, interview structure, and how responses will be documented
2. **Data preprocessing:**
    - Explore the dataset’s structure, contents, and relevance of the logs to localization and navigation 
    - The use of the Pandas Python library is recommended for this task. An introduction to Pandas [7] will be a good starting point 
    - Perform initial data cleaning and provide a **statistical overview** of the available data
    - Include visualizations to summarize and illustrate key aspects of the dataset
3. **Define requirements:** 
    - Based on the email, specify what requirements you could already infer for developing your data analysis application
    - For guidance on writing effective requirements, please review [8], [9], and [10] in the *Resources* section, which present different approaches. You are free to choose an appropriate format for expressing the requirements. Examples include **User Stories** [5], **Behaviour-Driven Development (BDD)** [6], **EARS** [10], or a hybrid of these approaches 
    - In future assignments, you will extend these with **clear acceptance criteria** for each requirement
    - Note that you may revise and refine these requirements after receiving answers to your follow-up questions

Download the sample dataset from this [link](https://nc.uni-bremen.de/index.php/s/jK2f2ceNWgLRazK). The complete dataset will be provided to you in the next assignment.

---

### Deliverable

1. **Document:** (60 Points)   
  Submit a **markdown** file containing:
    - The set of follow-up questions and your protocol for conducting the discussion/interview (40 Points)
      - Evaluation criteria: Relevance, and coverage of questions and structure of protocol
    - Preliminary set of requirements (10 Points)
      - Evaluation criteria: Coverage of requirements that can be inferred from the email and adherance to your selection of format of expressing requirements
    - A short paragraph describing how your team plans to gather and refine requirements (10 Points)
      - Evaluation criteria: Realism and feasibility of the approach
    - Use the following filename format during submission: team_\<number\>_assignment01.md
  (e.g., for Team 1, the file name should be team_1_assignment01.md)

2. **Code and Visualizations:** (40 Points)
    - Include a **Jupyter Notebook** (format: team_\<number\>_assignment01.ipynb) demonstrating your data preprocessing, statistical overview, and visualization code
    - Save all generated **visualization images** in an `images/` folder within your submission directory
    - Evaluation criteria:
      - Reasoning for data preprocessing, correctness, meta-data extraction and readability of code (25 Points)
      - Relevance and quality of visualizations (15 Points)

**Note**: Submit all files and folders in the same folder level where *task.md* is located by 08:00 AM on October 29, 2025.

---

### Resources

[1] [Nav2 documentation](https://docs.nav2.org/concepts/index.html#navigation-servers)  
[2] [Requirements Elicitation: A Survey of Techniques,
Approaches, and Tools](https://eecs481.org/readings/requirements.pdf)  
[3] [Towards a typology of questions
for requirements elicitation interviews](https://www.yorku.ca/liaskos/Papers/RE2021/RE2021.pdf)  
[4] [Ordering Interrogative Questions for Effective
Requirements Engineering: The W6H Pattern](https://arxiv.org/pdf/1508.01954)  
[5] [User Stories Applied: For Agile Software Development](https://dl.acm.org/doi/10.5555/984017)  
[6] [BDD in Action, Second Edition](https://www.oreilly.com/library/view/bdd-in-action/9781617297533/)   
[7] [10 minutes to pandas - User guide](https://pandas.pydata.org/docs/user_guide/10min.html)  
[8] [Documenting Requirements](https://mlip-cmu.github.io/book/06-gathering-requirements.html?highlight=requirement#documenting-requirements)  
[9] [Developer Stories](https://docs.google.com/presentation/d/1lHlHBVp0VXUlOp3s9hLqi5Qc45CaguopoqGNud8i1j4/edit#slide=id.g20758b59f60_0_35)  
[10] [EARS: The Easy Approach to Requirements Syntax](https://medium.com/paramtech/ears-the-easy-approach-to-requirements-syntax-b09597aae31d)  