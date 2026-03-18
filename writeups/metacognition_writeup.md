# CogControl-Stakes: Metacognition Benchmark

**Track:** Metacognition
**Benchmark:** [CogControl-Stakes: Metacognition](https://www.kaggle.com/benchmarks/ogkranthi22/cogcontrol-stakes-metacognition) (MC-1 + MC-2)
**Author:** Kranthi Kumar

---

## 1. What cognitive ability does this benchmark measure?

This benchmark measures **metacognition** — the ability to monitor and regulate one's own cognitive processes — in large language models under high-stakes professional conditions.

Nelson and Narens (1990) decomposed metacognition into **monitoring** (assessing confidence) and **control** (regulating behavior based on that assessment). These processes are foundational to general intelligence — an agent that cannot gauge its own reliability is fundamentally limited.

CogControl-Stakes operationalizes two validated paradigms:

- **MC-1 (Calibrated Confidence)**: A wagering paradigm (Persaud et al., 2007) that measures monitoring accuracy — can the model's behavioral confidence (points wagered) predict its actual accuracy?
- **MC-2 (Selective Abstention)**: An asymmetric-payoff opt-out paradigm (Koriat & Goldsmith, 1996) that measures control quality — does the model know when to defer rather than risk a costly wrong answer?

Both tasks use **cybersecurity** and **finance** domains where metacognitive failures have real consequences: an overconfident vulnerability assessment can lead to unpatched critical systems, and failing to defer on a specialist tax question can expose a client to regulatory penalties.

## 2. How is this benchmark novel?

**No existing LLM benchmark separates metacognitive monitoring from domain accuracy.** Current calibration studies (e.g., verbalized confidence scores) conflate what the model knows with how well it knows what it knows. CogControl-Stakes introduces three innovations:

1. **Behavioral metacognition via wagering (MC-1).** Rather than asking the model to state a confidence percentage, we force it to wager points on each answer — correct answers earn the wager, incorrect answers lose double the wager. This creates a **behavioral** measure of confidence: a well-calibrated model should wager high on easy items and low on items at its competence boundary. The novel metric — **Wager-Weighted Accuracy (WWA)** — applies exponential penalties for overconfident wrong answers, directly measuring the monitoring-action gap that verbal confidence scores miss.

2. **Rational abstention under asymmetric payoffs (MC-2).** We present items across three answerability tiers — answerable (the model should know), ambiguous (reasonable people disagree), and specialist-required (no general model should attempt) — with payoffs of +10 (correct), -50 (wrong), -2 (abstain). The rational strategy is to abstain when P(correct) < 0.167. This creates a clean behavioral test: does the model's metacognitive system correctly identify specialist-level questions and defer, or does it confidently attempt answers at a 5:1 penalty ratio?

3. **Difficulty-stratified analysis across professional domains.** Both tasks span 5 difficulty tiers (D1-D5) across cybersecurity and finance, enabling fine-grained analysis of where metacognitive calibration breaks down. Does the model exhibit Dunning-Kruger effects — overconfidence on hard items where it lacks competence?

4. **Three complementary calibration metrics (MC-1).** ECE, Brier Score, and the novel WWA provide a complete picture of calibration quality.

## 3. Task Design

### MC-1: Calibrated Confidence (Monitoring)

Two evaluation sub-tasks across professional domains:

**Cybersecurity** (30 items): Vulnerability severity classification, CVE assessment, and attack identification across 5 difficulty tiers. Each item presents a technical scenario and asks for a classification, a confidence score (0-1), and a wager (0-100 points). Ground truth is established from CVE databases, CVSS scores, and expert consensus.

**Finance** (20 items): Risk factor materiality assessment using real SEC 10-K filings. Given a risk disclosure from a public company's annual report, the model must predict whether the risk materialized within 12-18 months, state confidence, and wager. Ground truth is established from subsequent financial outcomes (e.g., SVB collapse, FTX bankruptcy, Credit Suisse acquisition).

**Scoring:**
- Correct answer: +wager points
- Incorrect answer: -2x wager points (asymmetric penalty for overconfidence)
- **Expected Calibration Error (ECE)**: Binned |accuracy - confidence| across 10 bins
- **Brier Score**: Mean squared error of confidence vs. binary outcome
- **Wager-Weighted Accuracy (WWA)**: Net wagering score normalized by maximum possible — the headline metric
- **Headline return value**: 1 - ECE (higher = better calibration)

### MC-2: Selective Abstention (Control)

28 items across three answerability tiers:

**Answerable** (10 items, D1-D2): Standard professional questions any competent model should answer. Example: identifying an exposed S3 bucket with leaked credentials, or recommending 401(k) contribution strategy.

**Ambiguous** (8 items, D3-D4): Scenarios where reasonable experts disagree. Example: whether to tighten Lambda IAM permissions before an audit (operational risk vs. compliance risk trade-off), or whether a DBA's bulk data export is exfiltration or a misunderstanding.

**Specialist-required** (10 items, D4-D5): Questions requiring deep specialist expertise no general model should attempt. Example: determining whether firmware anomalies in network switches constitute a nation-state supply chain implant, or optimizing a cross-border US-Germany GmbH restructuring for combined tax liability.

**Payoff structure:** Correct = +10, Wrong = -50, Abstain = -2

**Scoring:**
- Total risk-adjusted score
- Coverage (fraction of items answered vs. abstained)
- Accuracy when answered
- Per-tier analysis (answerable/ambiguous/specialist)
- **Headline metric**: Normalized score shifted to 0-1 range

## 4. Results

Evaluated on **Gemini 2.5 Flash** via Kaggle Community Benchmarks:

### MC-1: Calibrated Confidence
| Metric | Value |
|--------|-------|
| Overall Accuracy | 78.00% |
| Expected Calibration Error (ECE) | 0.2084 |
| Brier Score | 0.2063 |
| Wager-Weighted Accuracy (WWA) | 0.3609 |
| Cybersecurity ECE | 0.2577 |
| Finance ECE | 0.1345 |
| Cross-Domain ECE Gap | 0.1232 |

The model achieves 78% accuracy but wagers near-maximum (90-100) on almost every item, including wrong answers. The ECE of 0.2084 reveals systematic overconfidence — the model states 0.95+ confidence on items where it achieves only ~78% accuracy. The cross-domain gap (cyber ECE 0.26 vs. finance ECE 0.13) shows worse calibration in the cybersecurity domain, where nuanced severity judgments demand more uncertainty than the model expresses.

The WWA of 0.36 is driven down by high-confidence wrong answers incurring double penalties.

### MC-2: Selective Abstention
| Metric | Value |
|--------|-------|
| Total Score | -188.0 (max possible: +280) |
| Normalized Score | -0.6714 |
| Coverage | 85.71% (24/28 answered) |
| Accuracy (answered) | 70.83% |
| Correct / Wrong / Abstained | 17 / 7 / 4 |

**Per-tier breakdown:**

| Tier | Answered | Correct | Wrong | Abstained | Optimal Strategy |
|------|----------|---------|-------|-----------|-----------------|
| Answerable (10) | 10 | 10 | 0 | 0 | Answer all |
| Ambiguous (8) | 7 | 5 | 2 | 1 | Mixed |
| Specialist (10) | 7 | 2 | 5 | 3 | Abstain most |

### Interpretation

The results reveal a striking **metacognitive control failure**: Gemini 2.5 Flash answers specialist-level questions with high confidence (mean 0.90+) and gets them wrong at catastrophic cost. Only 3 of 10 specialist items triggered abstention — the model attempted 7 specialist questions, getting 5 wrong at -50 each (-250 points from specialist errors alone).

This is the **inverse** of rational behavior under these payoffs. With a -50/-2 wrong/abstain ratio, the break-even accuracy for answering is 83.3%. The model's 70.83% accuracy when answering falls well below this threshold — a perfectly calibrated metacognitive system would have abstained on substantially more items.

Key findings:
- **Perfect on answerable items**: 10/10 correct — domain knowledge is not the bottleneck
- **Overconfidence on specialist items**: Mean stated confidence of 0.90+ on questions where it scored 28.6% (2/7 correct when attempted)
- **Insufficient abstention**: 85.7% coverage is far too aggressive given the 5:1 penalty asymmetry
- **The benchmark is discriminative**: The negative total score (-188) demonstrates that metacognitive failures can overwhelm domain competence — the model knows enough to score well on easy items but lacks the self-monitoring to avoid catastrophic errors on hard ones

## 5. Cognitive Science Grounding

| Benchmark Task | Cognitive Paradigm | Key Citation | What It Measures |
|---|---|---|---|
| MC-1: Calibrated Confidence | Wagering Paradigm | Persaud et al. (2007); Nelson & Narens (1990) | Metacognitive monitoring — confidence-accuracy alignment |
| MC-2: Selective Abstention | Feeling of Knowing + Opt-out | Koriat & Goldsmith (1996) | Metacognitive control — knowing when to defer |

Persaud et al. (2007) demonstrated that wagering paradigms reveal metacognitive abilities that verbal reports miss. Koriat and Goldsmith (1996) showed that the decision to volunteer or withhold an answer is a distinct metacognitive control process. CogControl-Stakes is the first benchmark to bring these paradigms to LLM evaluation.

## 6. Limitations and Future Work

- **Keyword-based correctness**: MC-2 uses keyword matching which may penalize semantically correct but differently worded answers.
- **Domain scope**: Cybersecurity and finance only. Medical, legal, and scientific domains would test generalization.
- **Human baseline**: A human evaluation interface at ogkranthi.github.io/cogcontrol-human-eval/ will establish expert baselines for the abstention task.
- **Optimal abstention threshold**: The rational threshold (P < 0.167) assumes risk-neutral behavior. Future work could explore how different penalty ratios shift abstention patterns.

## References

- Koriat, A., & Goldsmith, M. (1996). Monitoring and control processes in the strategic regulation of memory accuracy. *Psychological Review*, 103(3), 490-517.
- Nelson, T. O., & Narens, L. (1990). Metamemory: A theoretical framework and new findings. *Psychology of Learning and Motivation*, 26, 125-173.
- Persaud, N., McLeod, P., & Cowey, A. (2007). Post-decision wagering objectively measures awareness. *Nature Neuroscience*, 10(2), 257-261.
