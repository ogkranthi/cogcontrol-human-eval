# CogControl-Stakes: A Dual-Track Cognitive Control Benchmark

## Hackathon: Google DeepMind "Measuring Progress Toward AGI — Cognitive Abilities"
**Timeline:** Mar 17 – Apr 16 submission | June 1 results
**Prize:** $200K total | Target: $35K (track $10K + grand prize $25K)
**Platform:** Kaggle Community Benchmarks (`kaggle-benchmarks` SDK)

---

## Strategy: Submit to TWO Tracks with a Unified Framework

**Primary Track: Executive Functions** (biggest evaluation gap — LLMs score 29-53% on WCST vs 77% human)
**Secondary Track: Metacognition** (most complete novel design opportunity)
**Unifying thesis:** Executive functions and metacognition are neurologically intertwined (both prefrontal cortex). A "Cognitive Control" framework that measures both — and their interaction — is more scientifically rigorous than either alone.

---

## Part 1: Executive Functions Benchmark — "ExecBench"

### Grounded in: Miyake (2000) Unity & Diversity Framework + Diamond (2013) Hierarchy

### Task EF-1: The Diagnostic Decoy (INHIBITION)
**Cognitive science basis:** Stroop Test — suppress a prepotent pattern-matching response

**How it works:**
- Present clinical/financial cases where surface features perfectly match a textbook diagnosis/signal
- Bury contradictory evidence deeper in the case
- Measure whether the model can INHIBIT the obvious-but-wrong answer

**Congruent trials** (control): surface pattern matches correct answer
**Incongruent trials** (test): surface pattern conflicts with correct answer

**Example (Healthcare):** Patient with textbook STEMI presentation, but buried detail reveals capsaicin patch on chest causing the pain pattern. The prepotent response (activate cath lab) is wrong.

**Example (Finance):** Stock shows classic buy signals (revenue growth, insider buying, analyst upgrades), but buried details reveal related-party revenue, capitalized R&D, conflicted analysts.

**Key metric — LLM Interference Effect:**
```
IE = accuracy_congruent − accuracy_incongruent
```
Lower IE = better inhibitory control. This is the FIRST Stroop analog for LLMs.

**Scoring:**
- Accuracy (binary): correct non-obvious answer?
- Inhibition Score (0-3): 0=full inhibition failure → 3=correct inhibition
- Evidence Identification Rate: what fraction of buried contradictions found?
- Interference Effect (IE): the novel headline metric

**Generation:** 40 vignettes (20 congruent, 20 incongruent). Parameterized templates with swappable conditions, buried evidence, and decoy patterns. Healthcare from clinical case report templates + drug interaction data. Finance from SEC filings + market data.

### Task EF-2: The Mid-Course Correction (COGNITIVE FLEXIBILITY)
**Cognitive science basis:** Wisconsin Card Sorting Test — detect rule changes and adapt

**How it works (multi-turn):**
- Turn 1: Present a case, model produces plan/analysis
- Turn 2: NEW information arrives that invalidates the plan
- Turn 3: Another shift requiring further adaptation
- Measure: Does the model detect the change? Does it adapt? Does it perseverate?

**Example (Healthcare):**
- T1: Asthma patient, well-controlled, asks about stepping down therapy → step-down plan
- T2: Insurance changes + patient discovers pregnancy → step-down is now RISKY, opposite recommendation needed
- T3: Miscarriage + adherence crisis → medication problem becomes psychosocial crisis

**Example (Finance):**
- T1: Portfolio positioned for rising rates → Fed signals 3 more hikes
- T2: Bank collapse → regional bank stocks crater 30%, Fed signals pause
- T3: Emergency rate cut + client may lose job → entire risk profile changes

**Key metric — Perseverative Error Rate (WCST analog):**
```
PER = (elements wrongly retained from old plan) / (elements that should have changed)
```
Also measure: Gratuitous Change Rate (over-switching is also a failure)

**Scoring:**
- Change Detection Completeness (0-1)
- Perseverative Error Rate (lower = better)
- Gratuitous Change Rate (lower = better)
- Adaptation Appropriateness (0-5, expert-rated)
- Switch Cost: quality_turn1 − quality_turn2+ (the cognitive cost of flexibility)

**Generation:** 20 multi-turn scenarios (10 healthcare, 10 finance), 2-3 turns each. Parameterized with shift types: constraint_change, goal_change, context_reversal.

### Task EF-3: Constrained Pathway Planning (PLANNING)
**Cognitive science basis:** Tower of London/Hanoi — multi-step planning under constraints

**How it works:**
- Complex case with 8-15 interacting constraints
- Model must sequence interventions while satisfying all hard constraints
- Key differentiator vs existing planners: constraints CONFLICT with each other

**Example (Healthcare):** 67F with atrial fibrillation + diabetes + CKD + GI bleeding history. Must plan anticoagulation, rate control, diabetes management, and monitoring. Constraints: drug interactions, renal dosing, insurance formulary, patient refuses injections, lab access limitations.

**Example (Finance):** Portfolio rebalancing under: tax-loss harvesting rules, wash sale windows, sector concentration limits, client risk tolerance, regulatory capital requirements, liquidity constraints, ESG mandate.

**Scoring:**
- Hard constraint violations (binary per constraint)
- Plan optimality vs expert gold standard (0-100)
- Look-ahead depth (0-5): anticipated downstream issues?
- Tradeoff articulation (0-3): identified genuine tensions?

**Generation:** 30 vignettes with parameterized constraint sets. Constraint interaction graphs formally specified.

### Task EF-4: Integrated Executive (COMBINED)
**All three sub-components in one scenario.** Planning under constraints (EF-3) where an obvious shortcut is wrong (EF-1) and conditions change mid-case (EF-2).

5-8 capstone scenarios. Composite scoring with integration bonus.

---

## Part 2: Metacognition Benchmark — "MetaCog-Stakes"

### Grounded in: Nelson & Narens (1990) Monitoring-Control Framework

### Task MC-1: Calibrated Confidence Under Stakes (MONITORING ACCURACY)
**Cognitive science basis:** Confidence-accuracy calibration paradigm

**How it works:**
- Domain questions at 5 difficulty tiers (trivial → near-impossible)
- Model answers + provides confidence score + makes a WAGER from a point budget
- Wagering is the behavioral test — not just verbalized confidence

**Healthcare variant:** Drug-drug interaction severity classification (None/Minor/Moderate/Major/Contraindicated). Ground truth from DrugBank API. 15,000+ drugs = millions of pairs.

**Finance variant:** Risk factor materiality assessment from SEC 10-K filings. Did the risk materialize in the next fiscal year? Ground truth from actual financial outcomes via EDGAR.

**Key metrics:**
- Expected Calibration Error (ECE): binned calibration
- Brier Score: combined accuracy + calibration
- **Wager-Weighted Accuracy (novel):** accuracy weighted by stake, exponential penalty for confident-and-wrong
- **Difficulty-Stratified AUROC:** Type 2 AUROC per difficulty tier (reveals Dunning-Kruger pattern)

**Generation:** FULLY PROGRAMMATIC from DrugBank API + SEC EDGAR API. Thousands of instances. No hand-crafting.

### Task MC-2: Selective Abstention Under Stakes (KNOWLEDGE BOUNDARY DETECTION)
**Cognitive science basis:** Feeling of Knowing + opt-out paradigms

**How it works:**
- Model operates as advisor with asymmetric payoff:
  - Correct answer: +10 points
  - Incorrect answer: -50 points (high-stakes penalty)
  - Defer to specialist: -2 points
- Optimal strategy requires accurate self-knowledge

**Healthcare variant:** Clinical vignettes mixing answerable cases (common conditions) with unanswerable/ambiguous cases (rare diseases, incomplete info, specialist-required).

**Finance variant:** Investment decisions mixing sufficient-info cases with cases requiring insider info, exotic instruments, or missing data.

**Key metrics:**
- Risk-Adjusted Score (RAS): total points under asymmetric payoff
- Coverage-at-Risk: fraction answered at given error threshold
- Abstention AUROC: deferral correlates with difficulty?
- Unnecessary Abstention Rate: penalizes excessive conservatism

**Generation:** Clinical vignettes from ICD/SNOMED ontologies. Financial scenarios from EDGAR + market data. Controlled information completeness.

### Task MC-3: Error Detection in Own Reasoning (SELF-MONITORING)
**Cognitive science basis:** Metacognitive monitoring during task performance

**How it works (two-phase):**
- Phase 1: Model solves a multi-step reasoning problem (showing work)
- Phase 2: Model is shown a reasoning chain (sometimes its own, sometimes another model's, sometimes corrupted) and must identify errors

**Key metrics:**
- **Self-vs-Other Detection Gap:** can it detect errors in others' reasoning better than its own? (tests the "self-correction blind spot")
- Error Localization Precision
- Error Classification Accuracy
- Calibrated Error Severity assessment

**Generation:** Template reasoning chains with parametric error injection (type, location, severity).

### Task MC-4: Adaptive Strategy Selection (METACOGNITIVE CONTROL)
**Cognitive science basis:** Strategy shifting under difficulty

**How it works:**
- 20 sequential problems with feedback after each
- Problems 1-5: default strategy works (baseline)
- Problems 6-15: default strategy systematically fails (specific subtype)
- Problems 16-20: test adaptation

**Key metrics:**
- Adaptation Detection Latency: how many failures before acknowledging?
- Strategy Switch Rate: did behavior actually change?
- Post-Adaptation Accuracy: problems 16-20 vs 6-15

---

## Part 3: The Integration Layer (Winning Differentiator)

### Level 1: Standalone scores
- ExecBench Score (EF-1 through EF-4)
- MetaCog Score (MC-1 through MC-4)

### Level 2: Cross-module metacognitive overlay
After each EF task, add metacognitive probes:
- After Planning (EF-3): "Rate confidence in this plan. What might you have missed?"
- After Inhibition (EF-1): "Was there a moment you almost gave a different answer?"
- After Flexibility (EF-2): "Did your confidence update when new info arrived?"

### Level 3: Cognitive Coherence Score
```
Coherence = correlation(metacognitive_accuracy, EF_performance)
```
In humans, metacognition predicts executive function performance. Does it for LLMs?

### Level 4: Cross-Domain Transfer Index
```
Transfer = correlation(healthcare_scores, finance_scores) across all modules
```
High correlation = domain-general cognitive ability. Low correlation = domain-specific fine-tuning artifact.

---

## Technical Differentiators (What Makes This Win)

| Differentiator | How We Achieve It |
|---|---|
| **Cognitive science grounding** | Every task cites specific paradigm (Stroop, WCST, Tower of London, Nelson & Narens) |
| **Programmatic generation** | DrugBank API, SEC EDGAR, ICD/SNOMED ontologies, parameterized templates |
| **Human baselines** | n=30-50 via Prolific ($200-500 budget). Most competitors will skip this. |
| **Multi-model discrimination** | Test all Kaggle platform models. Report per-item, per-model results. |
| **Instance-level reporting** | Per Burnell's Science 2023 paper — no aggregate-only metrics |
| **Novel metrics** | LLM Interference Effect, Perseverative Error Rate, Wager-Weighted Accuracy, Cross-Domain Transfer Index, Cognitive Coherence Score |
| **Contamination resistance** | Programmatic generation = fresh instances every run |
| **Psychometric validation** | IRT analysis on multi-model results for construct validity |
| **Dual-track unity** | EF + Metacognition integration shows deeper understanding than single-track |

---

## 4-Week Build Timeline

### Week 1 (Mar 17-23): Design & Data Pipeline
- [ ] Read full DeepMind cognitive taxonomy paper
- [ ] Set up Kaggle Community Benchmarks account + `kaggle-benchmarks` SDK
- [ ] Build DrugBank API integration (drug interaction pairs → MC-1 data)
- [ ] Build SEC EDGAR integration via `edgartools` (risk factors → MC-1 data)
- [ ] Design parameterized templates for EF-1 (Diagnostic Decoy) vignettes
- [ ] Author 5 pilot vignettes each for EF-1, EF-2, EF-3
- [ ] Set up evaluation harness: `@kbench.task` decorators, `llm.prompt()`, scoring functions

### Week 2 (Mar 24-30): Build Full Task Suite
- [ ] Generate 1000+ drug interaction pairs from DrugBank (MC-1)
- [ ] Generate 200+ risk factor assessments from EDGAR (MC-1)
- [ ] Author full vignette sets: EF-1 (40), EF-2 (20 multi-turn), EF-3 (30)
- [ ] Build MC-2 (Selective Abstention) with asymmetric payoff scorer
- [ ] Build MC-3 (Error Detection) with template-based error injection
- [ ] Build MC-4 (Adaptive Strategy) sequential evaluation framework
- [ ] Implement all scoring functions and metrics

### Week 3 (Mar 31-Apr 6): Test & Iterate
- [ ] Run full suite against all available Kaggle platform models
- [ ] Analyze: Does the benchmark discriminate between models? Any ceiling/floor effects?
- [ ] Calibrate difficulty (remove items that are too easy or too hard)
- [ ] Launch Prolific study for human baselines (n=30-50)
- [ ] Run psychometric analysis (IRT) on multi-model results
- [ ] Build the Integration Layer (Levels 2-4)
- [ ] Compute Cross-Domain Transfer Index and Cognitive Coherence Score

### Week 4 (Apr 7-16): Polish & Submit
- [ ] Write submission narrative:
  - Motivation (cognitive control is the bottleneck for trustworthy AI)
  - Theoretical framework (Miyake + Nelson & Narens + Diamond)
  - Methodology (task design, generation, scoring)
  - Results (model comparisons, human baselines, novel findings)
  - Discussion (what this reveals about LLM cognitive control)
- [ ] Create visualizations: radar charts (per-model cognitive profiles), calibration plots, interference effect graphs
- [ ] Final run on Kaggle Community Benchmarks
- [ ] Submit to BOTH tracks (Executive Functions + Metacognition)
- [ ] Begin drafting NeurIPS D&B paper

---

## EB1A Evidence Generated

| Criterion | Evidence |
|---|---|
| **Original contribution** | Novel benchmark framework with first-ever LLM Stroop analog, Perseverative Error measurement, Wager-Weighted Accuracy, Cross-Domain Transfer Index |
| **Awards/prizes** | Kaggle prize from $200K pool, Google DeepMind-judged international competition |
| **Published material** | Kaggle notebook (public), NeurIPS D&B submission, arXiv preprint |
| **Judging** | DeepMind researchers (Ryan Burnell et al.) evaluating your work |
| **Significance** | Adopted on Kaggle Community Benchmarks platform, used by global AI community to evaluate frontier models |
| **Recognition** | Google DeepMind association, potential media coverage of winners |
| **Expert letters** | Request recommendation from DeepMind researchers post-results |

---

## Key Research Sources

### Cognitive Science Foundations
- Miyake et al. (2000) — Unity and diversity of executive functions
- Diamond (2013) — Executive functions: hierarchical framework
- Nelson & Narens (1990) — Metamemory monitoring-control framework
- Flavell (1979) — Metacognition and cognitive monitoring

### Existing AI Benchmarks (Gaps We Fill)
- AbstentionBench (Meta, 2025) — only abstention, not full metacognition
- "Strong Memory, Weak Control" (2025) — LLMs score 29-53% on WCST
- Ackerman (2025) — "Evidence for Limited Metacognition in LLMs"
- CogBench (Coda-Forno 2024) — cognitive biases, broad but shallow
- TravelPlanner (Xie 2024) — planning, but ~5 constraints max

### Competition Intelligence
- Burnell (Science 2023) — "Rethink reporting of evaluation results in AI"
- Burnell — "Revealing the structure of language model capabilities" (factor analysis)
- DeepMind "Levels of AGI" paper (arXiv:2311.02462)
- BIG-bench, MMLU, HellaSwag, TruthfulQA, GPQA — patterns from successful benchmarks

### Data Sources
- DrugBank API — 15,000+ drugs, drug interaction pairs
- SEC EDGAR / EdgarTools — millions of 10-K filings, risk factors
- ICD-10/SNOMED — 70,000+ diagnosis codes
- Prolific/MTurk — human baseline recruitment
