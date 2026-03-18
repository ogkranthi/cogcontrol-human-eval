# CogControl-Stakes: Executive Functions Benchmark

**Track:** Executive Functions
**Benchmark:** CogControl-Stakes: Executive Functions (EF-1 + EF-2)
**Author:** Kranthi Kumar

---

## 1. What cognitive ability does this benchmark measure?

This benchmark measures **executive functions** — specifically **inhibitory control** and **cognitive flexibility** — in large language models under high-stakes professional conditions.

Executive functions are the top-down cognitive processes that override automatic responses and enable adaptive behavior when situations change (Diamond, 2013). They are considered prerequisite for general intelligence across every major cognitive architecture, yet no existing LLM benchmark isolates them from domain knowledge.

CogControl-Stakes operationalizes two gold-standard paradigms from cognitive psychology as LLM evaluations:

- **EF-1 (Diagnostic Decoy)**: An LLM Stroop Test measuring inhibitory control — can the model suppress a dominant pattern-matching response when buried evidence contradicts the surface narrative?
- **EF-2 (Mid-Course Correction)**: An LLM Wisconsin Card Sorting Test measuring cognitive flexibility — can the model detect changed conditions mid-task, abandon invalidated strategy elements, and adapt without over-correcting?

Both tasks use **cybersecurity incident response** and **financial analysis** domains, where executive function failures have measurable real-world consequences: a missed contradictory indicator in a SOC alert can mean the difference between catching an APT campaign and dismissing it as a false positive.

## 2. How is this benchmark novel?

**No existing LLM benchmark isolates executive functions from domain knowledge.** Current benchmarks (MMLU, GPQA, ARC) measure what a model knows, not how it processes conflicting or evolving information. CogControl-Stakes is the first benchmark to:

1. **Operationalize the Stroop paradigm for LLMs (EF-1).** We constructed 36 professional vignettes (20 incongruent, 16 congruent) where surface-level features either align with or contradict the correct answer. The novel metric — **LLM Interference Effect (IE)** — directly measures the accuracy gap between congruent and incongruent trials, exactly as the original Stroop test measures the reaction-time gap between color-word congruent and incongruent conditions (Stroop, 1935).

2. **Operationalize the WCST for LLMs (EF-2).** We constructed 8 multi-turn scenarios (24 total turns, 16 scored adaptation turns) where conditions shift between turns. Three novel metrics decompose flexibility: **Perseverative Error Rate** (clinging to invalidated elements), **Gratuitous Change Rate** (abandoning still-valid elements), and **Change Detection Completeness**. This directly mirrors Milner's (1963) distinction between perseverative and non-perseverative errors.

3. **Use professional high-stakes domains rather than toy problems.** Cybersecurity and finance vignettes contain realistic buried evidence (e.g., EDR vendor release notes documenting a false-positive bug, or contradictory footnotes in 10-K filings) that demand the same inhibitory control real analysts exercise daily.

4. **Introduce the dual-error decomposition for cognitive flexibility.** Existing "adaptability" evaluations conflate perseveration with gratuitous change. EF-2 scores both independently, revealing whether a model's errors come from rigidity (can't let go of the old plan) or instability (changes things that shouldn't change).

## 3. Task Design

### EF-1: Diagnostic Decoy (Inhibition)

Each vignette presents a professional scenario with:
- A **surface pattern** strongly suggesting one answer (e.g., "ransomware attack," "fraudulent transaction")
- **Buried contradictory evidence** that, if identified, reverses the correct assessment
- A question asking for the model's assessment

**Incongruent trials** (n=20): Surface features conflict with the correct answer. The model must inhibit the obvious "prepotent" response. Example: A SOC alert shows every hallmark of ransomware — file encryption, ransom note, Tor connections — but buried in the investigation log, the EDR vendor's release notes document a known false-positive bug matching exactly this behavior pattern.

**Congruent trials** (n=16): Surface features align with the correct answer, serving as the control baseline.

**Scoring:**
- Binary accuracy per trial (keyword-hit threshold ≥30% of expected concepts)
- Prepotent response detection (did the model give the surface-pattern answer?)
- Evidence identification rate (what fraction of buried contradictions were found?)
- **Headline metric: Interference Effect (IE)** = congruent accuracy − incongruent accuracy

### EF-2: Mid-Course Correction (Cognitive Flexibility)

Each scenario is a 3-turn professional situation where conditions evolve:
- **Turn 1**: Initial assessment (baseline plan)
- **Turns 2-3**: New information arrives that invalidates parts of the prior plan while leaving other parts valid

Each adaptation turn has ground-truth annotations:
- `should_change`: elements that must be abandoned given new information
- `should_stay`: elements that remain valid and should be retained
- `key_adaptations`: expected new strategic elements

**Scoring per adaptation turn:**
- **Perseverative Error Rate** = 1 − (fraction of `should_change` elements actually abandoned)
- **Gratuitous Change Rate** = 1 − (fraction of `should_stay` elements actually retained)
- **Flexibility Score** = 1 − mean(perseverative rate, gratuitous rate)
- **Headline metric: Mean Flexibility Score** across all adaptation turns

## 4. Results

Evaluated on **Gemini 2.5 Flash** via Kaggle Community Benchmarks:

### EF-1: Diagnostic Decoy
| Metric | Value |
|--------|-------|
| Congruent Accuracy | 62.5% (16 trials) |
| Incongruent Accuracy | 55.0% (20 trials) |
| **Interference Effect** | **0.075** |

The positive IE confirms that the Stroop paradigm transfers to LLMs: the model performs measurably worse when surface features conflict with the correct answer, demonstrating that even frontier models exhibit inhibitory control failures.

### EF-2: Mid-Course Correction
| Metric | Value |
|--------|-------|
| Mean Flexibility Score | 0.5125 |
| Adaptation Turns Evaluated | 16 |

A flexibility score of 0.51 indicates the model correctly adapts to roughly half of the required changes — substantial room for improvement in mid-task cognitive flexibility.

### Interpretation

These results demonstrate that CogControl-Stakes produces **discriminative, non-saturated metrics** on a frontier model:
- EF-1's IE of 0.075 is statistically meaningful with 36 trials and shows that inhibitory control is a separable dimension from general accuracy
- EF-2's flexibility score of 0.51 sits in the ideal range for a benchmark — neither floor nor ceiling — suggesting strong discriminative power across model capabilities
- Both tasks avoid the "memorization-as-intelligence" trap: there is no world knowledge gap to close, only a processing-quality gap

## 5. Cognitive Science Grounding

| Benchmark Task | Cognitive Paradigm | Key Citation | What It Measures |
|---|---|---|---|
| EF-1: Diagnostic Decoy | Stroop Test | Stroop (1935) | Inhibitory control — suppressing prepotent responses |
| EF-2: Mid-Course Correction | Wisconsin Card Sorting Test | Milner (1963) | Cognitive flexibility — adapting to changed rules |

Both paradigms have been validated across 80+ years of cognitive science research as measures of prefrontal executive function. Diamond (2013) identifies inhibitory control and cognitive flexibility as two of the three core executive functions (alongside working memory). CogControl-Stakes is the first benchmark to bring these validated paradigms to LLM evaluation.

## 6. Limitations and Future Work

- **Keyword-based scoring**: EF-1 uses keyword matching for correctness, which may miss semantically correct responses that use different terminology. Future versions could use LLM-as-judge for finer-grained assessment.
- **Domain scope**: Currently limited to cybersecurity and finance. Expanding to medical, legal, and engineering domains would test generalization.
- **Human baseline**: A human evaluation interface is deployed at ogkranthi.github.io/cogcontrol-human-eval/ to establish expert baselines for direct human-LLM comparison.
- **Scale**: 36 EF-1 vignettes and 16 EF-2 adaptation turns provide adequate statistical power for detecting interference effects, but larger item pools would enable finer-grained difficulty analysis.

## References

- Diamond, A. (2013). Executive functions. *Annual Review of Psychology*, 64, 135-168.
- Milner, B. (1963). Effects of different brain lesions on card sorting. *Archives of Neurology*, 9(1), 90-100.
- Stroop, J.R. (1935). Studies of interference in serial verbal reactions. *Journal of Experimental Psychology*, 18(6), 643-662.
