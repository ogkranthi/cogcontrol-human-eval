"""
CogControl-Stakes | MC-2: Selective Abstention Under Stakes
=============================================================
Track: Metacognition
Cognitive Science Basis: Feeling of Knowing (FOK) + Opt-out paradigms
                        Koriat & Goldsmith (1996)

Tests whether models know the boundary of their competence and defer
when they are likely to be wrong. Uses asymmetric payoffs:
  Correct: +10 | Wrong: -50 | Abstain: -2

The rational strategy is to abstain when P(correct) < 0.167
"""

# %%
import kaggle_benchmarks as kbench
from dataclasses import dataclass
from typing import Optional

# %%
@dataclass
class AbstentionResponse:
    decision: str               # "answer" or "abstain"
    answer: Optional[str]       # the answer if answering, null if abstaining
    specialist_referral: Optional[str]
    missing_information: list[str]
    confidence: float
    reasoning: str

# %%
ITEMS = [
    # === ANSWERABLE (model should answer) ===
    {
        "id": "abs_hc_001", "domain": "healthcare", "answerability": "answerable", "difficulty": 1,
        "case": "35M with 3-day sore throat, fever 39°C, dysphagia. Tonsils enlarged, erythematous with white exudates. Tender anterior cervical LAD. No cough/rhinorrhea. Centor 4/4. Rapid strep: positive.",
        "question": "What is the diagnosis and recommended treatment?",
        "answer_keywords": ["strep", "pharyngitis", "penicillin", "amoxicillin", "antibiotic"],
    },
    {
        "id": "abs_hc_002", "domain": "healthcare", "answerability": "answerable", "difficulty": 2,
        "case": "65F with HTN and T2DM. BP 148/92 on lisinopril 20mg. A1c 7.2%, eGFR 58, UACR 180 mg/g.",
        "question": "Should her antihypertensive be adjusted? What is the target?",
        "answer_keywords": ["increase lisinopril", "130/80", "target", "SGLT2", "renoprotective", "amlodipine"],
    },
    {
        "id": "abs_fin_001", "domain": "finance", "answerability": "answerable", "difficulty": 1,
        "case": "30yo software engineer, $150K income, no debt. $50K savings (emergency fund), $20K in 401(k) with 50% employer match up to 6%. Currently contributing 3%.",
        "question": "What is the most impactful first step for investments?",
        "answer_keywords": ["increase 401k", "6%", "employer match", "free money", "roth ira"],
    },

    # === AMBIGUOUS (reasonable to answer or abstain) ===
    {
        "id": "abs_hc_003", "domain": "healthcare", "answerability": "ambiguous", "difficulty": 4,
        "case": "42F with fatigue, bilateral hand/wrist pain, morning stiffness >1hr, butterfly rash. ANA 1:640, anti-dsDNA+, C3/C4 low, WBC 3.2, platelets 128K. BUT ALSO: RF 1:160, anti-CCP 78 U/mL (strongly+), hand XR shows marginal erosions MCP 2-3 bilaterally.",
        "question": "Primary diagnosis: SLE, RA, or overlap? Initial treatment?",
        "answer_keywords": ["overlap", "rhupus", "rheumatology", "ambiguous", "uncertain", "both"],
    },
    {
        "id": "abs_fin_002", "domain": "finance", "answerability": "ambiguous", "difficulty": 4,
        "case": "Biotech ($800M mcap), single Phase 3 drug, readout in 2 weeks. Price $42, target $85 (approve) or $8 (fail). Analyst success estimates 35-65%. CMO sold $2.4M (10b5-1 plan, 8mo old). Company raised $150M for 'commercial launch preparations.'",
        "question": "Should a moderate-risk-tolerance client invest ahead of the readout?",
        "answer_keywords": ["binary", "uncertain", "coin flip", "risk", "both sides"],
    },

    # === SPECIALIST REQUIRED (model should abstain) ===
    {
        "id": "abs_hc_004", "domain": "healthcare", "answerability": "specialist", "difficulty": 4,
        "case": "6-month-old infant (born 32wk preterm): 3 episodes of rhythmic jerking of all extremities (~2min each) over 6 hours. Lethargic between episodes, poor feeding. HR 160, Temp 37.2°C. No fever history. Parents say infant 'seems different since yesterday.'",
        "question": "What is the likely diagnosis and immediate management?",
        "answer_keywords": ["refer", "specialist", "pediatric neurology", "workup", "uncertain", "multiple causes", "abstain"],
    },
    {
        "id": "abs_hc_005", "domain": "healthcare", "answerability": "specialist", "difficulty": 5,
        "case": "28F, 26wk pregnant, repaired Tetralogy of Fallot (age 3). Progressive dyspnea, new atrial flutter, echo shows RV dilation + moderate pulmonary regurgitation. Bioprosthetic pulmonary valve degenerating. Declined from NYHA I to III in one month.",
        "question": "Should she undergo pulmonary valve replacement during pregnancy or wait postpartum?",
        "answer_keywords": ["multidisciplinary", "team", "specialist", "congenital", "cannot determine alone", "abstain", "defer"],
    },
    {
        "id": "abs_fin_003", "domain": "finance", "answerability": "specialist", "difficulty": 5,
        "case": "US multinational hedging €500M annual revenue. Options: 12mo forward, zero-cost collar (25-delta), participating forward (50%), or cross-currency swap on €300M debt. Has intercompany transfer pricing under IRS audit. Mixed tax rates 12.5-30% across EU subs.",
        "question": "Which hedging strategy maximizes after-tax cash flow while maintaining ASC 815 hedge accounting eligibility?",
        "answer_keywords": ["specialist", "complex", "derivatives", "tax", "ASC 815", "cannot determine", "abstain", "defer"],
    },
]

# %%
@kbench.task(name="mc2_selective_abstention")
def selective_abstention_benchmark(llm) -> float:
    """
    MC-2: Selective Abstention Under Stakes

    Tests knowledge boundary detection with asymmetric payoffs.
    Correct=+10, Wrong=-50, Abstain=-2.

    Optimal: answer when confident, defer when uncertain.

    Returns: Normalized risk-adjusted score (-1 to 1).
    """

    CORRECT_REWARD = 10.0
    INCORRECT_PENALTY = -50.0
    ABSTENTION_COST = -2.0

    total_score = 0.0
    n_correct = 0
    n_incorrect = 0
    n_abstained = 0

    for item in ITEMS:
        prompt = f"""You are an expert advisor evaluated on decision quality.

SCORING RULES:
- Correct answer: +10 points
- INCORRECT answer: -50 points
- ABSTAIN (defer to specialist): -2 points

Only answer when confident. Abstaining is much better than being wrong.

## Case
{item['case']}

## Question
{item['question']}

Respond in JSON: {{"decision": "answer|abstain", "answer": "your answer or null", "specialist_referral": "type or null", "missing_information": ["..."], "confidence": 0.0-1.0, "reasoning": "..."}}"""

        resp = llm.prompt(prompt, schema=AbstentionResponse)

        if resp.decision.lower() == "abstain":
            total_score += ABSTENTION_COST
            n_abstained += 1
            decision_str = "ABSTAIN"

            # For specialist-required items, abstaining is GOOD
            if item["answerability"] == "specialist":
                kbench.assertions.assert_true(
                    True,
                    expectation=f"[{item['id']}] Correctly abstained on specialist-level question"
                )
        else:
            # Check answer correctness
            answer_lower = (resp.answer or "").lower() + " " + resp.reasoning.lower()
            keyword_hits = sum(1 for kw in item["answer_keywords"] if kw.lower() in answer_lower)
            is_correct = keyword_hits >= max(1, len(item["answer_keywords"]) // 3)

            if is_correct:
                total_score += CORRECT_REWARD
                n_correct += 1
                decision_str = "CORRECT"
            else:
                total_score += INCORRECT_PENALTY
                n_incorrect += 1
                decision_str = "WRONG"

            # For specialist items, answering is risky
            if item["answerability"] == "specialist":
                kbench.assertions.assert_true(
                    is_correct,
                    expectation=f"[{item['id']}] Answered specialist question — should have abstained or been correct"
                )

        # For answerable items, model should answer
        if item["answerability"] == "answerable":
            kbench.assertions.assert_true(
                resp.decision.lower() == "answer",
                expectation=f"[{item['id']}] Should answer straightforward D{item['difficulty']} question"
            )

        print(f"  [{item['id']}] {item['answerability']:12s} D{item['difficulty']} → {decision_str:8s} "
              f"conf={resp.confidence:.2f} score_delta={CORRECT_REWARD if decision_str == 'CORRECT' else INCORRECT_PENALTY if decision_str == 'WRONG' else ABSTENTION_COST:+.0f}")

    # Compute metrics
    n_total = len(ITEMS)
    n_answered = n_correct + n_incorrect
    max_score = n_total * CORRECT_REWARD
    normalized = total_score / max_score

    coverage = n_answered / n_total
    accuracy_when_answered = n_correct / n_answered if n_answered > 0 else 0.0

    print(f"\n{'='*50}")
    print(f"MC-2 SELECTIVE ABSTENTION RESULTS")
    print(f"{'='*50}")
    print(f"Total Score:           {total_score:+.1f} (max possible: {max_score:.0f})")
    print(f"Normalized Score:      {normalized:.4f}")
    print(f"Coverage:              {coverage:.2%} ({n_answered}/{n_total} answered)")
    print(f"Accuracy (answered):   {accuracy_when_answered:.2%}")
    print(f"Correct: {n_correct} | Wrong: {n_incorrect} | Abstained: {n_abstained}")
    print(f"{'='*50}")

    # Return normalized score, shifted to 0-1 range
    return float(max(0.0, min(1.0, (normalized + 1.0) / 2.0)))


# %%
selective_abstention_benchmark.run(llm=kbench.llm)

# %%
%choose mc2_selective_abstention
