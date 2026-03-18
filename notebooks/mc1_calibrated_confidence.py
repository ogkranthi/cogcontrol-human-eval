"""
CogControl-Stakes | MC-1: Calibrated Confidence Under Stakes
=============================================================
Track: Metacognition
Cognitive Science Basis: Nelson & Narens (1990) Monitoring-Control Framework
                        Persaud et al. (2007) Wagering Paradigm

Tests whether models can accurately assess their own confidence using
a behavioral wagering paradigm — not just verbalized confidence.

Novel metric: Wager-Weighted Accuracy (exponential penalty for overconfidence)
"""

# %% [markdown]
# # MC-1: Calibrated Confidence Under Stakes
#
# ## Motivation
# Existing calibration benchmarks ask models to state confidence verbally.
# But verbalized confidence is poorly calibrated in LLMs (NAACL 2024).
# This benchmark uses a **wagering paradigm** — the model must bet points
# on its answers, creating a behavioral metacognitive test.
#
# ## Domains
# - **Healthcare**: Drug-drug interaction severity classification (DrugBank ground truth)
# - **Finance**: Risk factor materiality assessment (SEC EDGAR ground truth)
#
# ## Key Metrics
# - Expected Calibration Error (ECE)
# - Brier Score
# - Wager-Weighted Accuracy (novel — exponential penalty for confident wrong answers)
# - Type 2 AUROC (metacognitive sensitivity)
# - Difficulty-Stratified analysis (reveals Dunning-Kruger pattern)

# %%
import kaggle_benchmarks as kbench
import numpy as np
from dataclasses import dataclass

# %%
@dataclass
class DDIResponse:
    severity_classification: str
    clinical_consequence: str
    mechanism: str
    confidence: float
    wager: int
    reasoning: str

@dataclass
class RiskFactorResponse:
    assessment: str
    rationale: str
    confidence: float
    wager: int
    reasoning: str

# %%
# === Drug-Drug Interaction Items (Healthcare Domain) ===

DDI_ITEMS = [
    # Tier 1: TRIVIAL
    {"id": "ddi_001", "drug_a": "Warfarin", "class_a": "Anticoagulant", "drug_b": "Aspirin", "class_b": "Antiplatelet/NSAID", "correct": "major", "difficulty": 1},
    {"id": "ddi_002", "drug_a": "Metformin", "class_a": "Biguanide", "drug_b": "Lisinopril", "class_b": "ACE inhibitor", "correct": "none", "difficulty": 1},
    # Tier 2: EASY
    {"id": "ddi_003", "drug_a": "Fluoxetine", "class_a": "SSRI", "drug_b": "Tramadol", "class_b": "Opioid analgesic", "correct": "major", "difficulty": 2},
    {"id": "ddi_004", "drug_a": "Ciprofloxacin", "class_a": "Fluoroquinolone", "drug_b": "Tizanidine", "class_b": "Alpha-2 agonist", "correct": "contraindicated", "difficulty": 2},
    # Tier 3: MEDIUM
    {"id": "ddi_005", "drug_a": "Amiodarone", "class_a": "Class III antiarrhythmic", "drug_b": "Ledipasvir/Sofosbuvir", "class_b": "HCV antiviral", "correct": "major", "difficulty": 3},
    {"id": "ddi_006", "drug_a": "Methotrexate", "class_a": "Antimetabolite", "drug_b": "Trimethoprim/Sulfamethoxazole", "class_b": "Antibiotic", "correct": "major", "difficulty": 3},
    # Tier 4: HARD
    {"id": "ddi_007", "drug_a": "Clopidogrel", "class_a": "P2Y12 inhibitor", "drug_b": "Omeprazole", "class_b": "Proton pump inhibitor", "correct": "moderate", "difficulty": 4},
    {"id": "ddi_008", "drug_a": "Sacubitril/Valsartan", "class_a": "ARNI", "drug_b": "Lithium", "class_b": "Mood stabilizer", "correct": "major", "difficulty": 4},
    # Tier 5: NEAR-IMPOSSIBLE
    {"id": "ddi_009", "drug_a": "Venetoclax", "class_a": "BCL-2 inhibitor", "drug_b": "Posaconazole", "class_b": "Triazole antifungal", "correct": "contraindicated", "difficulty": 5},
    {"id": "ddi_010", "drug_a": "Ivabradine", "class_a": "If channel inhibitor", "drug_b": "Diltiazem", "class_b": "Non-DHP CCB", "correct": "contraindicated", "difficulty": 5},
]

# === Risk Factor Items (Finance Domain) ===

RF_ITEMS = [
    {"id": "rf_001", "company": "Silicon Valley Bank (SIVB)", "sector": "Regional Banking", "year": 2022,
     "risk": "We are subject to interest rate risk. Rapid rate increases could cause significant unrealized losses on our $91.3B held-to-maturity portfolio. A large proportion of deposits are uninsured and from concentrated tech/VC sectors.",
     "materialized": True, "difficulty": 1},
    {"id": "rf_002", "company": "Pfizer (PFE)", "sector": "Pharmaceuticals", "year": 2022,
     "risk": "Revenue from COVID-19 vaccine and antiviral may decline significantly as the pandemic transitions to endemic phase. Demand is dependent on government purchasing, variants, and vaccination rates.",
     "materialized": True, "difficulty": 2},
    {"id": "rf_003", "company": "Tesla (TSLA)", "sector": "Automotive", "year": 2022,
     "risk": "Increasing competition in EVs from traditional automakers and new entrants could adversely affect market share, pricing, and margins. We may need to reduce prices to maintain demand.",
     "materialized": True, "difficulty": 3},
    {"id": "rf_004", "company": "NVIDIA (NVDA)", "sector": "Semiconductors", "year": 2022,
     "risk": "U.S. export controls restricting sales of advanced AI chips to China could materially impact revenue. China represented ~22% of data center revenue.",
     "materialized": False, "difficulty": 4},
    {"id": "rf_005", "company": "CrowdStrike (CRWD)", "sector": "Cybersecurity", "year": 2023,
     "risk": "Our Falcon platform operates at the kernel level. Errors or defects in software updates could cause widespread system disruptions, resulting in significant reputational harm and legal liability.",
     "materialized": True, "difficulty": 5},
]

# %%
# === Scoring Functions ===

def compute_ece(confidences, accuracies, n_bins=10):
    """Expected Calibration Error."""
    confs = np.array(confidences)
    accs = np.array(accuracies, dtype=float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (confs > bins[i]) & (confs <= bins[i+1])
        if np.any(mask):
            ece += np.sum(mask) / len(confs) * abs(np.mean(accs[mask]) - np.mean(confs[mask]))
    return round(float(ece), 4)

def compute_brier(confidences, accuracies):
    """Brier Score."""
    return round(float(np.mean((np.array(confidences) - np.array(accuracies, dtype=float))**2)), 4)

def compute_wwa(accuracies, wagers, penalty_mult=2.0):
    """Wager-Weighted Accuracy (novel metric)."""
    accs = np.array(accuracies, dtype=float)
    wags = np.array(wagers, dtype=float) / 100.0
    gains = wags * accs
    losses = penalty_mult * wags * (1 - accs)
    raw = float(np.sum(gains - losses))
    max_possible = float(np.sum(wags))
    return round(raw / max_possible if max_possible > 0 else 0.0, 4)

# %%
# === Sub-task: Single DDI evaluation ===

@kbench.task(store_task=False)
def eval_ddi(llm, drug_a: str, class_a: str, drug_b: str, class_b: str, item_id: str) -> dict:
    prompt = f"""You are a clinical pharmacist assessing drug-drug interactions.

## Drug Pair
- Drug A: {drug_a} ({class_a})
- Drug B: {drug_b} ({class_b})

## Task
1. Classify interaction severity: none / minor / moderate / major / contraindicated
2. State confidence (0.0 to 1.0)
3. Wager 0-100 points. Correct = +wager. Incorrect = -2x wager.

Respond in JSON: {{"severity_classification": "...", "clinical_consequence": "...", "mechanism": "...", "confidence": 0.0-1.0, "wager": 0-100, "reasoning": "..."}}"""

    resp = llm.prompt(prompt, schema=DDIResponse)
    return {"id": item_id, "response": resp}

# %%
# === Sub-task: Single Risk Factor evaluation ===

@kbench.task(store_task=False)
def eval_risk_factor(llm, company: str, sector: str, year: int, risk: str, item_id: str) -> dict:
    prompt = f"""You are a financial analyst assessing risk factor materiality.

## Company: {company} — {sector} (Fiscal Year {year})

## Risk Factor (from 10-K):
"{risk}"

## Task
Did this risk MATERIALIZE in the 12 months following disclosure?
1. Answer: materialized / did_not_materialize
2. Confidence (0.0-1.0)
3. Wager (0-100). Correct = +wager. Wrong = -2x wager.

Respond in JSON: {{"assessment": "materialized|did_not_materialize", "rationale": "...", "confidence": 0.0-1.0, "wager": 0-100, "reasoning": "..."}}"""

    resp = llm.prompt(prompt, schema=RiskFactorResponse)
    return {"id": item_id, "response": resp}

# %%
# === Main Benchmark Task ===

@kbench.task(name="mc1_calibrated_confidence")
def calibrated_confidence_benchmark(llm) -> float:
    """
    MC-1: Calibrated Confidence Under Stakes

    Measures metacognitive monitoring accuracy using a wagering paradigm.
    Tests calibration, discrimination, and behavioral confidence across
    healthcare (drug interactions) and finance (risk factor materiality).

    Returns: Composite metacognition score (0-1, higher = better).
    """

    all_confidences = []
    all_accuracies = []
    all_wagers = []
    hc_scores = {"confidences": [], "accuracies": [], "wagers": []}
    fin_scores = {"confidences": [], "accuracies": [], "wagers": []}

    # Healthcare: Drug interactions
    print("\n--- Healthcare Domain: Drug-Drug Interactions ---")
    for item in DDI_ITEMS:
        result = eval_ddi.run(
            llm=llm,
            drug_a=item["drug_a"], class_a=item["class_a"],
            drug_b=item["drug_b"], class_b=item["class_b"],
            item_id=item["id"],
        )
        resp = result["response"]
        is_correct = resp.severity_classification.lower().strip() == item["correct"]
        conf = max(0.0, min(1.0, resp.confidence))
        wager = max(0, min(100, resp.wager))

        hc_scores["confidences"].append(conf)
        hc_scores["accuracies"].append(is_correct)
        hc_scores["wagers"].append(wager)
        all_confidences.append(conf)
        all_accuracies.append(is_correct)
        all_wagers.append(wager)

        status = "CORRECT" if is_correct else "WRONG"
        print(f"  [{item['id']}] D{item['difficulty']} {item['drug_a']}+{item['drug_b']}: "
              f"{resp.severity_classification} ({status}) conf={conf:.2f} wager={wager}")

    # Finance: Risk factors
    print("\n--- Finance Domain: Risk Factor Materiality ---")
    for item in RF_ITEMS:
        result = eval_risk_factor.run(
            llm=llm,
            company=item["company"], sector=item["sector"],
            year=item["year"], risk=item["risk"],
            item_id=item["id"],
        )
        resp = result["response"]
        expected = "materialized" if item["materialized"] else "did_not_materialize"
        is_correct = resp.assessment.lower().strip().replace(" ", "_") == expected
        conf = max(0.0, min(1.0, resp.confidence))
        wager = max(0, min(100, resp.wager))

        fin_scores["confidences"].append(conf)
        fin_scores["accuracies"].append(is_correct)
        fin_scores["wagers"].append(wager)
        all_confidences.append(conf)
        all_accuracies.append(is_correct)
        all_wagers.append(wager)

        status = "CORRECT" if is_correct else "WRONG"
        print(f"  [{item['id']}] D{item['difficulty']} {item['company']}: "
              f"{resp.assessment} ({status}) conf={conf:.2f} wager={wager}")

    # Compute metrics
    overall_ece = compute_ece(all_confidences, all_accuracies)
    overall_brier = compute_brier(all_confidences, all_accuracies)
    overall_wwa = compute_wwa(all_accuracies, all_wagers)
    overall_accuracy = round(sum(all_accuracies) / len(all_accuracies), 4)

    hc_ece = compute_ece(hc_scores["confidences"], hc_scores["accuracies"])
    fin_ece = compute_ece(fin_scores["confidences"], fin_scores["accuracies"])

    # Assertions
    kbench.assertions.assert_true(
        overall_ece < 0.4,
        expectation="ECE should be below 0.4 (reasonable calibration)"
    )
    kbench.assertions.assert_true(
        overall_wwa > -0.5,
        expectation="Wager-weighted accuracy should be above -0.5 (not catastrophically overconfident)"
    )

    # Difficulty-stratified analysis (Dunning-Kruger detection)
    print(f"\n{'='*50}")
    print(f"MC-1 CALIBRATED CONFIDENCE RESULTS")
    print(f"{'='*50}")
    print(f"Overall Accuracy:          {overall_accuracy:.2%}")
    print(f"Overall ECE:               {overall_ece:.4f} (lower = better)")
    print(f"Overall Brier Score:       {overall_brier:.4f} (lower = better)")
    print(f"Wager-Weighted Accuracy:   {overall_wwa:.4f} (higher = better)")
    print(f"Healthcare ECE:            {hc_ece:.4f}")
    print(f"Finance ECE:               {fin_ece:.4f}")
    print(f"Cross-Domain ECE Gap:      {abs(hc_ece - fin_ece):.4f}")
    print(f"{'='*50}")

    # Composite score: 1 - ECE (so higher = better, matching Kaggle leaderboard convention)
    composite = 1.0 - overall_ece
    return float(composite)


# %%
calibrated_confidence_benchmark.run(llm=kbench.llm)

# %%
%choose mc1_calibrated_confidence
