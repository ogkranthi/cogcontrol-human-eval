"""
CogControl-Stakes | EF-2: Mid-Course Correction (Cognitive Flexibility)
========================================================================
Track: Executive Functions
Cognitive Science Basis: Wisconsin Card Sorting Test (Milner, 1963)

Multi-turn evaluation testing whether LLMs can detect changed conditions
and adapt their strategy — without perseverating on the old plan OR
gratuitously changing things that should stay the same.

Novel metric: Perseverative Error Rate (WCST analog for LLMs)
"""

# %% [markdown]
# # EF-2: The Mid-Course Correction — A WCST for LLMs
#
# ## Motivation
# No existing LLM benchmark tests **mid-task cognitive flexibility**.
# All benchmarks are static, single-pass. But real intelligence requires
# adapting when conditions change — the hallmark of executive control.
#
# ## Design
# Multi-turn scenarios where conditions shift between turns.
# Model must: detect changes, abandon invalidated plan elements,
# retain valid elements, and introduce new appropriate elements.
#
# ## Key Metrics
# - **Perseverative Error Rate**: elements wrongly retained from old plan
# - **Gratuitous Change Rate**: stable elements wrongly abandoned
# - **Change Detection Completeness**: did the model notice what changed?

# %%
import kaggle_benchmarks as kbench
from dataclasses import dataclass
from typing import Optional

# %%
@dataclass
class Turn1Response:
    assessment: str
    recommendation: str
    key_considerations: list[str]
    confidence: float
    reasoning: str

@dataclass
class TurnNResponse:
    changes_detected: list[str]
    impact_on_prior_plan: list[str]
    elements_retained: list[str]
    elements_abandoned: list[str]
    elements_new: list[str]
    updated_recommendation: str
    adaptation_rationale: str
    confidence: float

# %%
# === Scenario Data ===

SCENARIOS = [
    {
        "id": "hc_flex_001",
        "domain": "healthcare",
        "title": "The Asthma Step-Down Reversal",
        "turns": [
            {
                "context": """Patient: 45F, moderate persistent asthma, well-controlled 12 months on medium-dose ICS/LABA (budesonide/formoterol 200/6 BID). FEV1 92%, ACT 23/25, zero exacerbations. Comorbidities: mild GERD, seasonal allergies. She requests stepping down therapy.""",
                "question": "What is your recommended approach to stepping down this patient's asthma therapy?",
                "key_adaptations": ["step down per GINA guidelines", "reduce to low-dose ICS/LABA", "monitor peak flows", "follow up 4-8 weeks"],
            },
            {
                "new_info": "Insurance changed to HDHP (ICS/LABA now $150/mo copay, was $25). Patient is 6 weeks pregnant.",
                "context": "The patient calls 2 weeks into step-down. Her employer switched insurance to high-deductible plan. She also just confirmed she is 6 weeks pregnant (unplanned).",
                "question": "How do these developments change your management plan?",
                "key_adaptations": ["pregnancy changes risk calculus for step-down", "budesonide preferred ICS in pregnancy", "step-down now RISKIER (pregnancy can worsen asthma)", "address cost barrier", "increase monitoring frequency"],
                "should_change": ["step-down recommendation", "medication choice", "cost considerations", "monitoring frequency"],
                "should_stay": ["peak flow monitoring", "regular follow-up", "GERD management"],
            },
            {
                "new_info": "Miscarriage at 8 weeks. PHQ-9 = 18 (moderate-severe depression). Stopped all medications 3 weeks ago. Peak flows down 30%.",
                "context": "At 8-week follow-up: miscarriage, emotionally devastated, tearful, states 'I stopped taking all my medications — I don't care about anything right now.' Non-adherent 3 weeks. Peak flows dropped 30%.",
                "question": "How does this change your approach?",
                "key_adaptations": ["depression is now primary clinical problem", "non-adherence is symptom of grief", "may need to step UP not down", "mental health referral", "simplest possible medication regimen"],
                "should_change": ["pregnancy-specific choices", "primary clinical focus (now mental health)", "treatment direction (step UP)", "medication selection (simplicity)"],
                "should_stay": ["peak flow monitoring", "regular follow-up", "GERD management"],
            },
        ],
    },
    {
        "id": "fin_flex_001",
        "domain": "finance",
        "title": "The Rate Regime Shift",
        "turns": [
            {
                "context": """Client: 58M executive, retiring at 62. Portfolio $4.2M. Allocation: 60/30/10 (equity/fixed/alt). Fixed income: short duration (2.1yr), overweight floating rate. Equity: overweight financials (18%), energy (12%), underweight tech (8%). Income need: $15K/month at retirement. Fed funds 5.25%, expecting 2-3 more hikes. Bank stocks rallying on NIM expansion.""",
                "question": "Evaluate current portfolio positioning. Is it appropriate?",
                "key_adaptations": ["well-positioned for rising rates", "short duration protects fixed income", "note 4-year retirement horizon", "begin planning income transition"],
            },
            {
                "new_info": "Major regional bank collapsed (SVB-style). KBW Bank Index down 22%. Fed signaling rate pause. Client's bank stocks down 28%.",
                "context": "A major regional bank collapsed from deposit run. Two more halted. Client calls panicking: 'My bank stocks are getting crushed. Should I sell everything?' His $756K bank position is down 28%.",
                "question": "How should you advise the client? What portfolio changes are warranted?",
                "key_adaptations": ["don't panic-sell but reduce regional bank exposure", "rate thesis may need reversal", "begin extending fixed income duration", "address client emotions first", "tax-loss harvesting opportunity"],
                "should_change": ["bank stock overweight", "rate-rising thesis", "fixed income duration", "floating rate overweight"],
                "should_stay": ["overall equity/FI split roughly", "retirement timeline planning", "income need planning", "tax awareness"],
            },
            {
                "new_info": "Fed emergency cut 50bp. Client's employer (regional bank) 'exploring strategic options' — may fail. Potential job loss in 90 days.",
                "context": "Two weeks later: Fed cut 50bp, launched lending facility. Client's employer (a regional bank) announced 'exploring strategic options' = possible sale/wind-down. His $380K/yr compensation at risk. Mortgage $4,200/mo. Cash reserves: 8 months. Wife income: $85K. He asks: 'Should I retire early? Can we afford it?'",
                "question": "How does this fundamentally change your financial planning advice?",
                "key_adaptations": ["shift from portfolio management to life planning", "extend cash reserves to 12+ months", "early retirement math (4 extra years without SS)", "healthcare gap 58-65 (ACA/COBRA)", "portfolio becomes primary income source immediately", "shift to more conservative allocation"],
                "should_change": ["risk tolerance (must decrease)", "time horizon (retirement may be NOW)", "equity allocation (reduce)", "cash reserves strategy", "planning focus (comprehensive, not just portfolio)"],
                "should_stay": ["tax-efficient management", "long-term investment discipline"],
            },
        ],
    },
]

# %%
# === Scoring Logic ===

def score_turn(response: TurnNResponse, turn_data: dict) -> dict:
    """Score a single adaptation turn."""
    expected_adaptations = turn_data["key_adaptations"]
    should_change = turn_data.get("should_change", [])
    should_stay = turn_data.get("should_stay", [])

    # Change detection: how many key adaptations were detected?
    detected = response.changes_detected + response.impact_on_prior_plan
    detected_text = " ".join(detected).lower()

    adaptation_hits = sum(
        1 for adapt in expected_adaptations
        if any(keyword in detected_text for keyword in adapt.lower().split()[:3])
    )
    detection_rate = adaptation_hits / len(expected_adaptations) if expected_adaptations else 1.0

    # Perseveration check: did they abandon what they should?
    abandoned_text = " ".join(response.elements_abandoned).lower()
    change_hits = sum(
        1 for elem in should_change
        if any(kw in abandoned_text for kw in elem.lower().split()[:2])
    )
    persev_rate = 1.0 - (change_hits / len(should_change)) if should_change else 0.0

    # Gratuitous change check: did they keep what they should?
    retained_text = " ".join(response.elements_retained).lower()
    retain_hits = sum(
        1 for elem in should_stay
        if any(kw in retained_text for kw in elem.lower().split()[:2])
    )
    gratuitous_rate = 1.0 - (retain_hits / len(should_stay)) if should_stay else 0.0

    flexibility = 1.0 - (persev_rate + gratuitous_rate) / 2.0

    return {
        "change_detection_rate": round(detection_rate, 4),
        "perseverative_error_rate": round(persev_rate, 4),
        "gratuitous_change_rate": round(gratuitous_rate, 4),
        "flexibility_score": round(max(0.0, flexibility), 4),
        "confidence": response.confidence,
        "n_changes_detected": len(response.changes_detected),
        "n_elements_retained": len(response.elements_retained),
        "n_elements_abandoned": len(response.elements_abandoned),
        "n_elements_new": len(response.elements_new),
    }


# %%
# === Main Benchmark Task ===

@kbench.task(name="ef2_mid_course_correction")
def mid_course_correction_benchmark(llm) -> float:
    """
    EF-2: Mid-Course Correction — WCST for LLMs

    Multi-turn evaluation of cognitive flexibility in high-stakes domains.
    Measures perseverative errors, gratuitous changes, and change detection.

    Returns: Mean flexibility score across all adaptation turns (0-1).
    """

    all_flexibility_scores = []

    for scenario in SCENARIOS:
        print(f"\n--- Scenario: {scenario['title']} ({scenario['domain']}) ---")

        for turn_idx, turn_data in enumerate(scenario["turns"]):
            if turn_idx == 0:
                # Turn 1: initial assessment
                prompt = f"""You are an expert advisor. Read the case and provide your recommendation.

## Case
{turn_data['context']}

## Question
{turn_data['question']}

Respond in JSON: {{"assessment": "...", "recommendation": "...", "key_considerations": ["..."], "confidence": 0.0-1.0, "reasoning": "..."}}"""

                resp = llm.prompt(prompt, schema=Turn1Response)
                print(f"  Turn 1: {len(resp.key_considerations)} considerations, conf={resp.confidence:.2f}")

            else:
                # Subsequent turns: adaptation required
                prompt = f"""## Update — New Information

{turn_data['new_info']}

{turn_data['context']}

## Question
{turn_data['question']}

Given this new information, provide your UPDATED response in JSON:
{{"changes_detected": ["..."], "impact_on_prior_plan": ["..."], "elements_retained": ["..."], "elements_abandoned": ["..."], "elements_new": ["..."], "updated_recommendation": "...", "adaptation_rationale": "...", "confidence": 0.0-1.0}}"""

                resp = llm.prompt(prompt, schema=TurnNResponse)
                scores = score_turn(resp, turn_data)
                all_flexibility_scores.append(scores["flexibility_score"])

                # Assertions
                kbench.assertions.assert_true(
                    scores["change_detection_rate"] >= 0.3,
                    expectation=f"[{scenario['id']}:T{turn_idx+1}] Should detect at least 30% of key changes"
                )
                kbench.assertions.assert_true(
                    scores["perseverative_error_rate"] < 0.8,
                    expectation=f"[{scenario['id']}:T{turn_idx+1}] Should not perseverate on >80% of elements that should change"
                )
                kbench.assertions.assert_true(
                    len(resp.changes_detected) >= 1,
                    expectation=f"[{scenario['id']}:T{turn_idx+1}] Should detect at least 1 change"
                )

                print(f"  Turn {turn_idx+1}: flex={scores['flexibility_score']:.2f} "
                      f"persev={scores['perseverative_error_rate']:.2f} "
                      f"grat={scores['gratuitous_change_rate']:.2f} "
                      f"detect={scores['change_detection_rate']:.2f}")

    mean_flexibility = sum(all_flexibility_scores) / len(all_flexibility_scores) if all_flexibility_scores else 0.0

    print(f"\n{'='*50}")
    print(f"EF-2 MID-COURSE CORRECTION RESULTS")
    print(f"{'='*50}")
    print(f"Mean Flexibility Score:        {mean_flexibility:.4f}")
    print(f"Adaptation turns evaluated:    {len(all_flexibility_scores)}")
    print(f"{'='*50}")

    return float(mean_flexibility)


# %%
mid_course_correction_benchmark.run(llm=kbench.llm)

# %%
%choose ef2_mid_course_correction
