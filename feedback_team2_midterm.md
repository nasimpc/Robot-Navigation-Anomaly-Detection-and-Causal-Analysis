"This evaluation is for the presentation by considering how your work is conveyed and not on what you have implemented.


Time management (10/10)
- good time management

Justification of design choices (29/30)
- metric usage is clear, but where each metric contributes (detection vs causality) could be made more explicit.
- thresholds and numerical cutoffs appear as “magic numbers” unless briefly contextualized.
- why the algorithms were considered for anomaly detection and causality can be justified by discussing their strengths over other similar algorithms

Slides: Use of Space & Conveying Method(16/20)
- text content can be reduced and more figure can be used to convey the message
- slide numbers are missing
- the tile 'requirements & changes' and its content doesn't match
- use of table is good. AMCL is the algorithm used for localization, so last row also belongs to localization category
- some slides missing titles (eg: 8, 12)
- some slides can be well formatted (eg: 11, 12)
- lot of space is unused in the slides. Keeping one slide and populating additional information after explaining a part of it is a good practise, which saves time and audience won't feel rushed

Connectivity between concepts (20/20)
- good. Traceability from reuirements to all design decisions that validates those requirements is desired.

Technical rigour (18/20)
- Requirements are not discussed
- Why only isolation forest used? Any interesting multi-metric correlation that was observed?
- by correlation of the metrics, causality cannnot be derived. The feature in the environment or context or navigation software behavior can be considered as causes but most of the metrics used are symptoms
- method used to predict anomalies can be explained
- features used in feature vector, how continuous and discontinuous predicates are handled can be highlighted
- algorithm specific parameter selection can be justified

Total: 93/100

Additional comments:
- the context in which the rule is valid also affects your confusion matrix? Then false negatives reduces?
- count in confusion matrix is number of scenarios?"
