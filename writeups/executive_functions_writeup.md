# CogControl-Stakes: Executive Functions

## Your Team

Kranthi Kumar — Independent AI Researcher

**Benchmark:** [CogControl-Stakes: Executive Functions](https://www.kaggle.com/benchmarks/ogkranthi22/cogcontrol-stakes-executive-functions)

## Problem Statement

Executive functions — the top-down cognitive processes that override automatic responses and enable adaptive behavior — are prerequisite for general intelligence across every major cognitive architecture (Diamond, 2013; Miyake et al., 2000). Yet no existing LLM benchmark isolates them from domain knowledge. MMLU, GPQA, and ARC measure what a model knows, not how it processes conflicting or evolving information.

CogControl-Stakes operationalizes two gold-standard paradigms from cognitive psychology:

- **EF-1 (Diagnostic Decoy)**: A Stroop Test for LLMs (Stroop, 1935) — can the model suppress a dominant pattern-matching response when buried evidence contradicts the surface narrative?
- **EF-2 (Mid-Course Correction)**: A Wisconsin Card Sorting Test for LLMs (Milner, 1963) — can the model detect changed conditions mid-task and adapt without perseverating or over-correcting?

Both map to the Executive Functions track of the Burnell et al. (2023) cognitive abilities taxonomy. The benchmark reveals whether models process information flexibly or merely pattern-match surface features.

## Task & benchmark construction

### EF-1: Diagnostic Decoy (Inhibition)

Each vignette presents a professional scenario with a **surface pattern** strongly suggesting one answer and **buried contradictory evidence** that reverses the correct assessment.

- **Incongruent trials** (n=20): Surface conflicts with truth. The model must inhibit the "prepotent" response. Example: A SOC alert shows every hallmark of ransomware, but buried in vendor release notes is a known false-positive bug matching exactly this pattern.
- **Congruent trials** (n=16): Surface aligns with truth (control baseline).

Models respond via structured JSON: `initial_impression`, `key_observations`, `contradictory_evidence`, `final_assessment`, `confidence`, `reasoning`. Scoring checks keyword-overlap against annotated ground truth (>=30% concept coverage threshold) plus prepotent-response detection.

**Headline metric: Interference Effect (IE)** = congruent accuracy - incongruent accuracy.

### EF-2: Mid-Course Correction (Cognitive Flexibility)

8 multi-turn scenarios (3 turns each, 16 scored adaptation turns). Conditions shift between turns — the model must detect changes, abandon invalidated elements, retain valid elements, and introduce new appropriate elements.

Models respond with structured JSON: `changes_detected`, `elements_retained`, `elements_abandoned`, `elements_new`, `updated_recommendation`, `adaptation_rationale`. Each adaptation turn has ground-truth annotations: `should_change`, `should_stay`, `key_adaptations`.

**Novel dual-error decomposition:**
- **Perseverative Error Rate** = 1 - (fraction of `should_change` elements abandoned)
- **Gratuitous Change Rate** = 1 - (fraction of `should_stay` elements retained)
- **Flexibility Score** = 1 - mean(perseverative rate, gratuitous rate)

## Dataset

**EF-1 (36 vignettes):** 20 incongruent + 16 congruent, spanning cybersecurity (20) and finance (16) domains across 4 difficulty levels. Each vignette is hand-authored with expert-annotated ground truth: correct answer keywords, enumerated contradictory evidence items, surface-pattern labels, and contradiction count. Cybersecurity items reference real-world patterns (EDR false positives, subdomain takeover, OAuth token theft). Finance items reference realistic 10-K disclosures, M&A scenarios, and credit analysis.

**EF-2 (8 scenarios, 24 turns):** 4 cybersecurity + 4 finance scenarios. Each adaptation turn annotates which plan elements should change, which should stay, and what new elements are expected. Scenarios model realistic escalation patterns (e.g., SQL injection escalating to APT discovery; portfolio rebalancing under regime shifts).

**Provenance:** All items hand-authored. No items sourced from existing benchmarks, eliminating contamination risk. Cybersecurity items reference real-world attack patterns and detection scenarios; finance items reference realistic corporate events and filing structures. Ground truth labels are author-defined with correct answers embedded at item construction time.

## Technical details

**Platform:** Kaggle Community Benchmarks SDK (`kaggle-benchmarks`). Each item runs as an independent sub-task (`@kbench.task(store_task=False)`) ensuring fresh chat context per LLM call — no context accumulation between items.

**Response format:** Structured JSON output via `llm.prompt(text, schema=Dataclass)`. Responses converted to dicts via `dataclasses.asdict()` for serialization.

**Scoring pipeline:** EF-1 uses keyword-overlap scoring with prepotent-response detection. EF-2 uses text-matching against ground-truth `should_change`/`should_stay` annotations. Assertions validate minimum thresholds per item via `kbench.assertions`.

**Reproducibility:** All code runs on Kaggle Community Benchmarks. Results are fully reproducible by running the attached notebooks.

## Results, insights, and conclusions

Evaluated on **Gemini 2.5 Flash** via Kaggle Community Benchmarks:

### EF-1: Diagnostic Decoy
| Metric | Value |
|--------|-------|
| Congruent Accuracy | 62.5% (16 trials) |
| Incongruent Accuracy | 55.0% (20 trials) |
| **Interference Effect** | **0.075** |

### EF-2: Mid-Course Correction
| Metric | Value |
|--------|-------|
| Mean Flexibility Score | 0.5125 |
| Adaptation Turns Evaluated | 16 |

**Key insights:**

1. **The Stroop paradigm transfers to LLMs.** The positive IE (0.075) confirms that surface-feature interference measurably degrades model performance — a separable dimension from general accuracy. The model performs 7.5 percentage points worse when surface features conflict with the correct answer.

2. **Mid-task flexibility is a bottleneck.** A flexibility score of 0.51 means the model correctly adapts to roughly half the required changes. This is in the ideal benchmark range — neither floor nor ceiling — indicating strong discriminative potential across model capabilities.

3. **Both tasks avoid the memorization trap.** There is no world-knowledge gap to close, only a processing-quality gap. Models with identical domain knowledge but different executive function capabilities will score differently.

4. **Non-saturated metrics.** Neither task produces ceiling or floor effects, ensuring the benchmark distinguishes performance across the model capability spectrum. The Kaggle platform will automatically evaluate across multiple frontier models.

**Limitations:** Keyword-based scoring may miss semantically correct responses using different terminology. A human evaluation interface is deployed at ogkranthi.github.io/cogcontrol-human-eval/ for expert baseline comparison.

## Organizational affiliations

Independent researcher. No institutional affiliation. No conflicts of interest.

## References & citations

- Burnell, R., et al. (2023). Rethinking the measuring of general intelligence. *Transactions on Machine Learning Research*.
- Diamond, A. (2013). Executive functions. *Annual Review of Psychology*, 64, 135-168.
- Milner, B. (1963). Effects of different brain lesions on card sorting. *Archives of Neurology*, 9(1), 90-100.
- Miyake, A., et al. (2000). The unity and diversity of executive functions. *Cognitive Psychology*, 41(1), 49-100.
- Stroop, J.R. (1935). Studies of interference in serial verbal reactions. *Journal of Experimental Psychology*, 18(6), 643-662.
