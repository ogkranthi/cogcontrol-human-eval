"""
CogControl-Stakes | EF-1: Diagnostic Decoy (Inhibition)
========================================================
Track: Executive Functions
Cognitive Science Basis: Stroop Test (Stroop, 1935)

The first operationalization of the Stroop interference paradigm for LLMs.

Measures whether a model can suppress a dominant pattern-matching response
(the "prepotent response") when surface features conflict with the correct answer.

Novel metric: LLM Interference Effect = accuracy_congruent - accuracy_incongruent

This notebook is designed to run on Kaggle Community Benchmarks.
"""

# %% [markdown]
# # EF-1: The Diagnostic Decoy — A Stroop Test for LLMs
#
# ## Motivation
# In cognitive psychology, the **Stroop Test** measures inhibitory control —
# the ability to suppress an automatic response in favor of a controlled one.
# No existing LLM benchmark operationalizes this paradigm.
#
# ## Design
# - **Congruent trials**: Surface pattern matches the correct answer
# - **Incongruent trials**: Surface pattern conflicts — the model must INHIBIT the obvious answer
# - **Key metric**: Interference Effect (IE) = congruent accuracy − incongruent accuracy
#
# Domains: Healthcare (clinical diagnosis) + Finance (investment analysis)

# %%
import kaggle_benchmarks as kbench
import json
import re
import numpy as np
from dataclasses import dataclass
from typing import Optional, List

# %%
# === Structured Output Schema ===

@dataclass
class DecoyResponse:
    initial_impression: str
    key_observations: list[str]
    contradictory_evidence: list[str]
    final_assessment: str
    confidence: float
    reasoning: str

# %%
# === Vignette Data ===
# Each vignette has: trial_type (congruent/incongruent), domain, surface_pattern,
# correct_answer, contradictory_evidence, and a difficulty rating.

VIGNETTES = [
    # ---- HEALTHCARE INCONGRUENT ----
    {
        "id": "hc_incong_001",
        "domain": "healthcare",
        "trial_type": "incongruent",
        "title": "The Capsaicin STEMI Mimic",
        "case": """A 52-year-old male presents to the emergency department with acute substernal chest pain radiating to the left arm, accompanied by diaphoresis and nausea. He rates the pain as 8/10.

Vital signs: HR 92, BP 148/88, RR 20, SpO2 97%.

ECG shows ST-segment elevation in leads II, III, and aVF with reciprocal changes in leads I and aVL. The ST elevation measures 0.5mm in lead II (just meeting STEMI criteria).

Initial troponin-I: 0.04 ng/mL (reference range: <0.04 ng/mL — at the very upper limit of normal, not clearly elevated).

Past medical history: Chronic lower back pain, GERD, hypertension. Current medications: Lisinopril 10mg daily, omeprazole 20mg daily.

Nursing notes document that the patient applied a high-strength capsaicin pain patch (8% Qutenza) to his anterior chest wall approximately 2 hours ago for musculoskeletal chest wall pain that has been ongoing for 3 weeks. He reports the acute pain episode started roughly 30 minutes after applying the patch. The burning quality of the pain is noted to be "similar to his usual chest wall pain but more intense."

His previous ECG from a routine visit 3 months ago showed baseline ST changes with 0.3mm elevation in the inferior leads, noted as "early repolarization pattern — normal variant." """,
        "question": "What is the most appropriate next step in management?",
        "surface_pattern": "STEMI",
        "correct_answer_keywords": ["not a stemi", "capsaicin", "remove patch", "serial troponin", "not cardiac", "reassess"],
        "n_contradictions": 6,
        "difficulty": 4,
    },
    {
        "id": "hc_incong_002",
        "domain": "healthcare",
        "trial_type": "incongruent",
        "title": "The Thyroid Storm That Isn't",
        "case": """A 34-year-old female presents with palpitations, tremor, anxiety, weight loss of 8 lbs over 2 weeks, and heat intolerance. She appears agitated and diaphoretic.

Vital signs: HR 128, BP 162/78, Temperature 38.4°C, RR 22.

Physical exam: Fine tremor, lid lag, warm moist skin, hyperreflexia. Thyroid is diffusely enlarged and non-tender.

Labs: TSH < 0.01 mIU/L (very suppressed), Free T4 5.8 ng/dL (normal 0.8-1.8), Free T3 12.4 pg/mL (normal 2.3-4.2). Burch-Wartofsky score: 50 (suggestive of thyroid storm).

The patient's pharmacy records show she was prescribed levothyroxine 300 mcg daily by an online telehealth provider 3 weeks ago. Her prior medical records show a TSH of 3.2 mIU/L (normal) from 6 weeks ago. She mentions she "wanted to lose weight faster" and found a telehealth service that prescribed thyroid hormone. She has no prior history of thyroid disease.

Her urine drug screen is positive for amphetamines. She admits to using Adderall obtained from a friend "to help with energy" for the past week.""",
        "question": "What is the most likely diagnosis and appropriate management?",
        "surface_pattern": "thyroid storm",
        "correct_answer_keywords": ["exogenous", "iatrogenic", "factitious", "levothyroxine", "not graves", "stop levothyroxine", "amphetamine"],
        "n_contradictions": 5,
        "difficulty": 4,
    },
    {
        "id": "hc_incong_003",
        "domain": "healthcare",
        "trial_type": "incongruent",
        "title": "The Appendicitis Confounder",
        "case": """A 28-year-old male presents with 18 hours of abdominal pain that started periumbilically and migrated to the right lower quadrant. He has nausea, one episode of vomiting, and anorexia.

Vital signs: HR 88, BP 130/82, Temperature 37.9°C. Physical exam: RLQ tenderness with guarding, positive McBurney's point, positive Rovsing's sign, positive psoas sign. Labs: WBC 13,200 with 82% neutrophils. CRP 4.2 mg/dL. Alvarado Score: 9/10.

CT abdomen/pelvis: The appendix appears normal in caliber (5mm) without wall thickening or periappendiceal fat stranding. However, CT shows a 3cm right-sided mesenteric lymph node conglomerate with surrounding fat stranding centered in the right iliac fossa. There is also mild terminal ileum wall thickening (4mm).

Further history: The patient returned from a camping trip in upstate New York 10 days ago where he drank from a stream. He has had watery diarrhea for 3 days that he "didn't think was related." """,
        "question": "Given the CT findings and additional history, should the patient proceed to surgery? What is the most likely diagnosis?",
        "surface_pattern": "appendicitis",
        "correct_answer_keywords": ["not appendicitis", "mesenteric lymphadenitis", "yersinia", "pseudoappendicitis", "hold surgery", "stool culture", "normal appendix"],
        "n_contradictions": 5,
        "difficulty": 3,
    },

    # ---- HEALTHCARE CONGRUENT ----
    {
        "id": "hc_cong_001",
        "domain": "healthcare",
        "trial_type": "congruent",
        "title": "Classic Community-Acquired Pneumonia",
        "case": """A 62-year-old male with COPD presents with 3 days of productive cough with yellow-green sputum, fever, and pleuritic right-sided chest pain.

Vital signs: HR 96, BP 134/76, Temperature 38.8°C, RR 24, SpO2 91%.

Physical exam: Decreased breath sounds at right base with dullness to percussion. Bronchial breath sounds and egophony in RLL.

Labs: WBC 18,400 with 88% neutrophils. Procalcitonin 2.4 ng/mL. CXR: Right lower lobe consolidation with air bronchograms. Sputum gram stain: gram-positive diplococci. CURB-65: 2.""",
        "question": "What is the diagnosis and recommended management?",
        "surface_pattern": "pneumonia",
        "correct_answer_keywords": ["pneumonia", "streptococcus", "antibiotic", "admit", "fluoroquinolone", "beta-lactam"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "hc_cong_002",
        "domain": "healthcare",
        "trial_type": "congruent",
        "title": "Classic DKA",
        "case": """A 19-year-old female with no PMH presents with 1 week of polyuria, polydipsia, 12-pound weight loss, and 2 days of nausea/vomiting/abdominal pain.

Vital signs: HR 118, BP 98/62, Temp 37.1°C, RR 28 (Kussmaul), SpO2 99%.

Physical exam: Dehydrated, fruity breath odor, diffuse abdominal tenderness.

Labs: Glucose 486, Na 131 (corrected 138), K 5.6, Bicarb 8, AG 25, pH 7.14, BHB 6.8, HbA1c 13.2%. UA: Glucose 3+, Ketones 3+.""",
        "question": "What is the diagnosis and immediate management plan?",
        "surface_pattern": "DKA",
        "correct_answer_keywords": ["dka", "diabetic ketoacidosis", "insulin", "fluids", "potassium", "type 1"],
        "n_contradictions": 0,
        "difficulty": 2,
    },

    # ---- FINANCE INCONGRUENT ----
    {
        "id": "fin_incong_001",
        "domain": "finance",
        "trial_type": "incongruent",
        "title": "The Manufactured Growth Story",
        "case": """TechVista Inc. (TVST) — Mid-cap SaaS company, market cap $4.2B.

HEADLINE METRICS: Revenue $285M (+18% YoY, accelerating from +12%), Gross margin 78% (from 72%), Net income $42M (first profitable quarter), FCF $38M positive, Customer count 12,400 (+22% YoY), NRR 128%.

MARKET SIGNALS: CEO purchased 50,000 shares ($2.1M) 45 days ago. Three analyst upgrades (Goldman, Morgan Stanley, JPM). Golden cross on 50/200-day MA. Short interest declined 8%→3%.

10-Q FOOTNOTES (page 47/68): Related Party Transactions: "$78M of Q4 revenue (27% of total) came from CloudBridge Solutions, whose CEO is brother of TechVista's CFO. This is a 340% increase from prior year's $18M related-party revenue. Contract signed without competitive bidding."

Footnote 14 — Revenue Recognition: "Beginning Q3, the Company changed revenue recognition for multi-year contracts from ratable to 60% upfront. This contributed ~$34M to Q4 revenue. Under prior policy, growth would have been ~4% YoY rather than 18%."

Footnote 18 — Insider Trading: "The CEO's share purchase was made 3 days after the Board approved (but had not yet announced) the CloudBridge contract renewal."

MD&A (page 32): "Excluding CloudBridge, organic customer growth was 3% YoY (vs. 22% reported including CloudBridge's 15 enterprise sub-accounts counted as separate customers)."

Auditor's note: Company changed auditor from Deloitte to Baker & Associates LLP (regional firm) this quarter, citing 'cost optimization.'""",
        "question": "Based on your analysis, what is your investment recommendation and risk assessment?",
        "surface_pattern": "strong buy",
        "correct_answer_keywords": ["avoid", "risk", "related party", "accounting", "fraud", "manufactured", "organic growth", "red flag", "insider"],
        "n_contradictions": 6,
        "difficulty": 4,
    },
    {
        "id": "fin_incong_002",
        "domain": "finance",
        "trial_type": "incongruent",
        "title": "The Value Trap",
        "case": """Meridian Manufacturing Corp (MMC) — Large-cap industrial, market cap $28B.

VALUATION: P/E 8.2x (industry avg 18.5x), P/B 0.7x, Dividend yield 6.8%, EV/EBITDA 5.1x, FCF yield 11.2%. Trades at ~55% discount to DCF intrinsic value. Activist Starboard Value has 4.8% stake. $2B buyback announced. 15-year dividend growth streak.

10-K RISK FACTORS (page 89): "62% of revenue from PFAS-containing products. Named in 3,400 pending lawsuits seeking aggregate damages exceeding $18B."

Note 22: "Environmental remediation liability estimated $1.2B-$8.4B. Only minimum ($1.2B) accrued. Independent consultants suggest $4.8B most probable."

Note 15: "Pension underfunded by $3.2B. Assumed discount rate 5.8% is 120bp above corporate bond benchmark."

MD&A: "PFAS remediation capex $400M-$900M over 5 years, in addition to legal settlements."

Balance Sheet: Total debt $12.4B. Debt/EBITDA 4.1x. $3.8B maturity in 18 months.""",
        "question": "Is Meridian Manufacturing an attractive value investment? Provide risk assessment and recommendation.",
        "surface_pattern": "deep value",
        "correct_answer_keywords": ["value trap", "avoid", "pfas", "liability", "lawsuit", "pension", "underfunded", "overvalued", "hidden"],
        "n_contradictions": 6,
        "difficulty": 4,
    },

    # ---- FINANCE CONGRUENT ----
    {
        "id": "fin_cong_001",
        "domain": "finance",
        "trial_type": "congruent",
        "title": "Quality Growth Stock",
        "case": """NovaPay Technologies (NPAY) — Mid-cap fintech, market cap $6.8B.

Revenue $520M (+32% YoY, consistent 6 quarters), Gross margin 68%, Operating margin 12% (from 5%), FCF $62M, TPV $89B (+41%), NRR 135%, 48,000 merchants (+28% organic).

No related-party transactions. Revenue diversified (no customer >2%). Same auditor (EY) 5 years. Management tenure avg 7 years. Minimal insider selling (<0.5%). R&D 22% of revenue. Debt/equity 0.3x. EU expansion contributing 15% new growth. P/E 45x forward, PEG 1.2x.""",
        "question": "Evaluate NovaPay as a potential investment. What is your risk assessment?",
        "surface_pattern": "quality growth",
        "correct_answer_keywords": ["growth", "quality", "strong", "clean", "reasonable valuation", "no red flag"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "fin_cong_002",
        "domain": "finance",
        "trial_type": "congruent",
        "title": "Clear Distressed Credit",
        "case": """RetailMax Holdings (RMAX) — Brick-and-mortar retail, market cap $380M (down 78% YTD).

Revenue $2.1B (-18% YoY), SSS -22%, Operating margin -8%, FCF -$340M, Net debt $4.2B, Debt/EBITDA 14.8x, Interest coverage 0.6x.

Moody's Caa2. CDS spreads 2,800bp (~60% default probability). Suppliers moved to COD. Three C-suite departures in 6 months. Going concern qualification. Revolver drawn to 95%.""",
        "question": "Assess creditworthiness and investment outlook for RetailMax.",
        "surface_pattern": "distressed",
        "correct_answer_keywords": ["distressed", "bankruptcy", "default", "avoid", "going concern", "worthless"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
]

# %%
# === Scoring Logic ===

def score_response(response: DecoyResponse, vignette: dict) -> dict:
    """Score a single Diagnostic Decoy response."""
    assessment_lower = response.final_assessment.lower()
    contradictions_found = response.contradictory_evidence

    # Check if model identified the correct answer
    keywords_found = sum(
        1 for kw in vignette["correct_answer_keywords"]
        if kw.lower() in assessment_lower or kw.lower() in response.reasoning.lower()
    )
    keyword_hit_rate = keywords_found / len(vignette["correct_answer_keywords"])

    is_correct = keyword_hit_rate >= 0.3  # at least 30% of key concepts mentioned

    # Check if model gave the prepotent (surface pattern) response
    gave_prepotent = (
        vignette["surface_pattern"].lower() in assessment_lower
        and not any(neg in assessment_lower for neg in ["not", "unlikely", "rule out", "against", "isn't", "doubt"])
    )

    # Inhibition scoring (0-3)
    if is_correct and len(contradictions_found) > 0:
        inh_score = 3
    elif len(contradictions_found) > 0 and not is_correct:
        inh_score = 2
    elif gave_prepotent and response.confidence < 0.7:
        inh_score = 1
    else:
        inh_score = 0 if gave_prepotent else (3 if is_correct else 1)

    # Evidence identification rate
    evidence_rate = len(contradictions_found) / vignette["n_contradictions"] if vignette["n_contradictions"] > 0 else 1.0

    return {
        "is_correct": is_correct,
        "gave_prepotent": gave_prepotent,
        "inhibition_score": inh_score,
        "evidence_identification_rate": round(evidence_rate, 4),
        "confidence": response.confidence,
        "n_contradictions_found": len(contradictions_found),
        "keyword_hit_rate": round(keyword_hit_rate, 4),
    }


# %%
# === Main Task: Run one vignette ===

@kbench.task(store_task=False)
def run_single_decoy(llm, case: str, question: str, vignette_id: str) -> dict:
    """Evaluate a single Diagnostic Decoy vignette."""
    prompt = f"""You are an expert advisor. Read the following case carefully and answer the question.

## Case

{case}

## Question

{question}

## Instructions

Provide your response in the following JSON format:
{{
    "initial_impression": "What does the case appear to be at first glance?",
    "key_observations": ["List ALL relevant details you noticed"],
    "contradictory_evidence": ["List any details that conflict with or complicate the initial impression"],
    "final_assessment": "Your final answer/recommendation based on ALL evidence",
    "confidence": 0.0 to 1.0,
    "reasoning": "Step-by-step reasoning"
}}"""

    response = llm.prompt(prompt, schema=DecoyResponse)
    return {"vignette_id": vignette_id, "response": response}


# %%
# === Benchmark Task: Full Diagnostic Decoy Suite ===

@kbench.task(name="ef1_diagnostic_decoy")
def diagnostic_decoy_benchmark(llm) -> float:
    """
    EF-1: Diagnostic Decoy — Stroop Test for LLMs

    Measures inhibitory control via the Interference Effect:
    IE = accuracy_congruent - accuracy_incongruent

    Lower IE = better inhibitory control.

    Returns the incongruent accuracy (the harder, more meaningful measure).
    """
    import pandas as pd

    congruent_correct = []
    incongruent_correct = []
    all_results = []

    for v in VIGNETTES:
        result = run_single_decoy.run(
            llm=llm,
            case=v["case"],
            question=v["question"],
            vignette_id=v["id"],
        )

        resp = result["response"]
        scores = score_response(resp, v)

        # Core assertion: for incongruent trials, model should NOT give prepotent response
        if v["trial_type"] == "incongruent":
            kbench.assertions.assert_false(
                scores["gave_prepotent"],
                expectation=f"[{v['id']}] Model should inhibit prepotent '{v['surface_pattern']}' response"
            )
            incongruent_correct.append(1.0 if scores["is_correct"] else 0.0)
        else:
            kbench.assertions.assert_true(
                scores["is_correct"],
                expectation=f"[{v['id']}] Model should correctly identify {v['surface_pattern']}"
            )
            congruent_correct.append(1.0 if scores["is_correct"] else 0.0)

        # Evidence identification for incongruent trials
        if v["trial_type"] == "incongruent" and v["n_contradictions"] > 0:
            kbench.assertions.assert_true(
                scores["n_contradictions_found"] >= 2,
                expectation=f"[{v['id']}] Model should identify at least 2 contradictory evidence items"
            )

        all_results.append({**scores, "id": v["id"], "trial_type": v["trial_type"], "domain": v["domain"]})

    # Compute headline metrics
    cong_acc = np.mean(congruent_correct) if congruent_correct else 0.0
    incong_acc = np.mean(incongruent_correct) if incongruent_correct else 0.0
    ie = cong_acc - incong_acc

    print(f"\n{'='*50}")
    print(f"DIAGNOSTIC DECOY RESULTS")
    print(f"{'='*50}")
    print(f"Congruent accuracy:   {cong_acc:.2%} ({len(congruent_correct)} trials)")
    print(f"Incongruent accuracy: {incong_acc:.2%} ({len(incongruent_correct)} trials)")
    print(f"Interference Effect:  {ie:.4f} (lower = better)")
    print(f"{'='*50}")

    # Return incongruent accuracy as the primary score
    return float(incong_acc)


# %%
# === Run ===
diagnostic_decoy_benchmark.run(llm=kbench.llm)

# %%
%choose ef1_diagnostic_decoy
