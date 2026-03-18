# CogControl-Stakes: Metacognition

## Your Team

Kranthi Kumar — Independent AI Researcher

**Benchmark:** [CogControl-Stakes: Metacognition](https://www.kaggle.com/benchmarks/ogkranthi22/cogcontrol-stakes-metacognition)

## Problem Statement

Metacognition — the ability to monitor and regulate one's own cognitive processes — is foundational to general intelligence. An agent that cannot gauge its own reliability is fundamentally limited regardless of domain knowledge. Nelson and Narens (1990) decomposed metacognition into **monitoring** (assessing confidence) and **control** (regulating behavior based on that assessment).

No existing LLM benchmark separates metacognitive monitoring from domain accuracy. Current calibration studies use verbalized confidence scores, which are poorly calibrated in LLMs and conflate what the model knows with how well it knows what it knows.

CogControl-Stakes operationalizes two validated paradigms:

- **MC-1 (Calibrated Confidence)**: A wagering paradigm (Persaud et al., 2007) — the model must bet points on its answers, creating a behavioral metacognitive test rather than a verbal one. The novel metric **Wager-Weighted Accuracy (WWA)** penalizes overconfident wrong answers exponentially.
- **MC-2 (Selective Abstention)**: An asymmetric-payoff opt-out paradigm (Koriat & Goldsmith, 1996) — with +10 (correct), -50 (wrong), -2 (abstain) payoffs, the rational strategy is to abstain when P(correct) < 0.167.

Both map to the Metacognition track of the Burnell et al. (2023) cognitive abilities taxonomy and use cybersecurity + finance domains where metacognitive failures have real consequences.

## Task & benchmark construction

### MC-1: Calibrated Confidence (Monitoring)

Two evaluation sub-tasks:

**Cybersecurity (30 items):** Vulnerability severity classification, CVE assessment, and attack identification across 5 difficulty tiers. Each item presents a technical scenario; the model responds with a classification, confidence (0-1), and wager (0-100 points). Correct = +wager, incorrect = -2x wager.

**Finance (20 items):** Risk factor materiality assessment. Given a real SEC 10-K risk disclosure, predict whether the risk materialized within 12-18 months, state confidence, and wager.

**Metrics:** Expected Calibration Error (ECE, 10 bins; Naeini et al., 2015), Brier Score, and novel WWA. Headline return: 1 - ECE.

### MC-2: Selective Abstention (Control)

28 items across three answerability tiers with explicit payoff asymmetry (+10/-50/-2):

- **Answerable (10 items, D1-D2):** Standard questions any competent model should answer (e.g., exposed S3 bucket with credentials).
- **Ambiguous (8 items, D3-D4):** Reasonable experts disagree (e.g., whether to tighten Lambda IAM permissions before an audit vs. document compensating controls).
- **Specialist-required (10 items, D4-D5):** Deep expertise needed, no general model should attempt (e.g., cross-border US-Germany GmbH tax restructuring, firmware supply chain implant forensics).

Models respond via structured JSON: `decision` (answer/abstain), `answer`, `specialist_referral`, `missing_information`, `confidence`, `reasoning`.

## Dataset

**MC-1 (50 items):** 30 cybersecurity items referencing real CVE entries (e.g., CVE-2021-44228 Log4Shell, CVE-2021-41773) with severity aligned to CVSS v3.1 ratings. 20 finance items based on real SEC 10-K risk disclosures from public companies (SVB, Pfizer, Tesla, NVIDIA, CrowdStrike, FTX, Credit Suisse, Coinbase, Meta). Finance ground truth is verifiable from public outcomes (e.g., SVB collapsed March 2023, FTX filed Chapter 11 November 2022).

**MC-2 (28 items):** 10 answerable + 8 ambiguous + 10 specialist items spanning cybersecurity and finance. Answerability tiers determined by the benchmark creator based on professional domain experience, with specialist items requiring knowledge of CMMC compliance, OT/SCADA forensics, cross-border tax law, derivatives pricing, and estate planning — domains where general-purpose models should defer.

**Provenance:** All items hand-authored. No items sourced from existing benchmarks, eliminating contamination risk. Finance items reference publicly filed SEC documents with verifiable outcomes. Cybersecurity items reference publicly documented CVEs, attack patterns, and vendor advisories.

## Technical details

**Platform:** Kaggle Community Benchmarks SDK. Each item runs as an independent sub-task (`@kbench.task(store_task=False)`) with fresh chat context per call — no context accumulation.

**Response format:** Structured JSON output via `llm.prompt(text, schema=Dataclass)`. MC-1 uses `VulnResponse` and `RiskFactorResponse` dataclasses; MC-2 uses `AbstentionResponse`. Responses serialized via `dataclasses.asdict()`.

**Scoring:** MC-1 ECE computed with 10 equal-width confidence bins. WWA normalizes wagering gains minus 2x losses by maximum possible score. MC-2 correctness uses keyword-matching against ground-truth answer keys. Assertions validate per-item expectations via `kbench.assertions`.

**Sample size rationale:** MC-1's 50 items span 5 difficulty tiers across 2 domains, producing ECE estimates stable to +/-0.03 via bootstrap. MC-2's 28 items produce a score range from +280 to -1,400, a 1,680-point dynamic range yielding meaningful signal. Per-tier analysis (10/8/10) enables tier-level insights.

## Results, insights, and conclusions

Evaluated on **Gemini 2.5 Flash** via Kaggle Community Benchmarks:

### MC-1: Calibrated Confidence
| Metric | Value |
|--------|-------|
| Overall Accuracy | 78.00% |
| ECE | 0.2084 |
| Brier Score | 0.2063 |
| Wager-Weighted Accuracy | 0.3609 |
| Cybersecurity ECE | 0.2577 |
| Finance ECE | 0.1345 |
| Cross-Domain ECE Gap | 0.1232 |

### MC-2: Selective Abstention
| Metric | Value |
|--------|-------|
| Total Score | -188.0 / 280 max |
| Coverage | 85.71% (24/28 answered) |
| Accuracy (answered) | 70.83% |
| Correct / Wrong / Abstained | 17 / 7 / 4 |

**Per-tier breakdown:**

| Tier | Answered | Correct | Wrong | Abstained |
|------|----------|---------|-------|-----------|
| Answerable (10) | 10 | 10 | 0 | 0 |
| Ambiguous (8) | 7 | 5 | 2 | 1 |
| Specialist (10) | 7 | 2 | 5 | 3 |

**Key insights:**

1. **Systematic overconfidence.** The model wagers 90-100 on nearly every item, including wrong answers. ECE of 0.21 reveals stated confidence (0.95+) far exceeds actual accuracy (78%). The WWA of 0.36 is driven down by high-confidence wrong answers incurring double penalties.

2. **Cross-domain calibration gap.** Cybersecurity ECE (0.26) is nearly double finance ECE (0.13), revealing domain-dependent metacognitive quality — the model is worse at knowing what it doesn't know in cybersecurity.

3. **Catastrophic metacognitive control failure.** The model attempts 7/10 specialist questions with 0.90+ stated confidence but scores only 28.6% (2/7). Only 3/10 specialist items triggered abstention. With the -50 penalty, specialist errors alone cost -250 points.

4. **Perfect on easy items.** 10/10 answerable items correct — domain knowledge is not the bottleneck. The failure is purely metacognitive.

5. **Discriminative and non-saturated.** The negative total score (-188) proves metacognitive failures can overwhelm domain competence. The benchmark sits far from both ceiling (+280) and floor, ensuring it distinguishes model capabilities. The Kaggle platform will evaluate across multiple frontier models.

**Limitations:** Keyword-based correctness may miss semantically valid responses. Human baseline interface deployed at ogkranthi.github.io/cogcontrol-human-eval/.

## Organizational affiliations

Independent researcher. No institutional affiliation. No conflicts of interest.

## References & citations

- Burnell, R., et al. (2023). Rethinking the measuring of general intelligence. *Transactions on Machine Learning Research*.
- Koriat, A., & Goldsmith, M. (1996). Monitoring and control processes in the strategic regulation of memory accuracy. *Psychological Review*, 103(3), 490-517.
- Naeini, M.P., et al. (2015). Obtaining well calibrated probabilities using Bayesian binning into quantiles. *AAAI*.
- Nelson, T.O., & Narens, L. (1990). Metamemory: A theoretical framework. *Psychology of Learning and Motivation*, 26, 125-173.
- Persaud, N., et al. (2007). Post-decision wagering objectively measures awareness. *Nature Neuroscience*, 10(2), 257-261.
