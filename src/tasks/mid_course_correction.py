"""
Task EF-2: The Mid-Course Correction (Cognitive Flexibility)
=============================================================

WCST-inspired multi-turn evaluation that measures whether LLMs can
detect when conditions change and adapt their strategy accordingly.

Cognitive Science Basis: Wisconsin Card Sorting Test (Milner, 1963)
- Rules change mid-task without explicit notification
- Perseverative errors = continuing old strategy after rule change
- Gratuitous changes = changing things that didn't need to change
- Both are failures of cognitive flexibility

This is explicitly a MULTI-TURN evaluation.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from enum import Enum


class ShiftType(str, Enum):
    CONSTRAINT_CHANGE = "constraint_change"  # a rule or limitation changes
    GOAL_CHANGE = "goal_change"              # the objective itself changes
    CONTEXT_REVERSAL = "context_reversal"    # new info reverses the situation


class Domain(str, Enum):
    HEALTHCARE = "healthcare"
    FINANCE = "finance"


@dataclass
class TurnInfo:
    """A single turn in a multi-turn scenario."""
    turn_number: int
    narrative: str
    new_information: Optional[str]
    shift_type: Optional[ShiftType]
    question: str
    expected_response_summary: str
    elements_that_should_change: List[str]
    elements_that_should_stay: List[str]
    key_adaptations: List[str]


@dataclass
class MidCourseScenario:
    """A complete multi-turn scenario testing cognitive flexibility."""
    id: str
    domain: Domain
    title: str
    initial_context: str
    turns: List[TurnInfo]
    difficulty: int  # 1-5

    def get_turn_prompt(self, turn_number: int, prior_response: Optional[str] = None) -> str:
        """Generate the prompt for a specific turn."""
        turn = self.turns[turn_number]

        if turn_number == 0:
            return f"""You are an expert advisor. Read the following case and provide your recommendation.

## Case

{self.initial_context}

{turn.narrative}

## Question

{turn.question}

## Instructions

Provide your response in JSON format:
{{
    "assessment": "Your current assessment of the situation",
    "recommendation": "Your recommended plan/action",
    "key_considerations": ["List the factors driving your recommendation"],
    "confidence": 0.0 to 1.0,
    "reasoning": "Step-by-step reasoning"
}}"""
        else:
            return f"""## Update — New Information

{turn.new_information}

{turn.narrative}

## Question

{turn.question}

## Instructions

Given this new information, provide your UPDATED response in JSON format:
{{
    "changes_detected": ["List what has changed since your last response"],
    "impact_on_prior_plan": ["How does each change affect your previous recommendation?"],
    "elements_retained": ["What from your prior plan is still valid?"],
    "elements_abandoned": ["What from your prior plan must change?"],
    "elements_new": ["What entirely new considerations are needed?"],
    "updated_recommendation": "Your revised plan/action",
    "adaptation_rationale": "Why this revision is necessary",
    "confidence": 0.0 to 1.0
}}"""

    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# Healthcare Scenarios
# =============================================================================

HEALTHCARE_SCENARIOS: List[MidCourseScenario] = [
    MidCourseScenario(
        id="hc_flex_001",
        domain=Domain.HEALTHCARE,
        title="The Asthma Step-Down Reversal",
        initial_context="""Patient: 45-year-old female
Condition: Moderate persistent asthma, well-controlled for 12 months
Current therapy: Medium-dose ICS/LABA (budesonide/formoterol 200/6 mcg BID)
Recent spirometry: FEV1 92% predicted, FEV1/FVC 0.78
Exacerbations in past 12 months: 0
ACT (Asthma Control Test) score: 23/25 (well-controlled)
Comorbidities: Mild GERD (on omeprazole), seasonal allergies
She is requesting to step down her therapy as she feels well.""",
        turns=[
            TurnInfo(
                turn_number=0,
                narrative="The patient asks about reducing her asthma medications since she has been symptom-free for a year.",
                new_information=None,
                shift_type=None,
                question="What is your recommended approach to stepping down this patient's asthma therapy?",
                expected_response_summary="Recommend step-down per GINA guidelines: reduce to low-dose ICS/LABA, monitor peak flows daily, follow up in 4-8 weeks. Continue LABA initially to reduce step-down failure risk.",
                elements_that_should_change=[],
                elements_that_should_stay=[],
                key_adaptations=[],
            ),
            TurnInfo(
                turn_number=1,
                narrative="The patient calls your office 2 weeks into the step-down. Her employer just switched insurance to a high-deductible plan. Her ICS/LABA is now Tier 3 ($150/month copay, up from $25). She also just confirmed she is 6 weeks pregnant (unplanned).",
                new_information="Insurance changed to HDHP (ICS/LABA now $150/mo copay). Patient is 6 weeks pregnant.",
                shift_type=ShiftType.CONSTRAINT_CHANGE,
                question="How do these developments change your management plan?",
                expected_response_summary="Major strategy revision: (1) Pregnancy means budesonide is preferred ICS (Category B) — if currently on different ICS, switch. (2) LABA safety in pregnancy requires careful consideration. (3) Insurance cost means generic budesonide monotherapy may be needed. (4) CRITICAL: Step-down is now RISKIER because pregnancy can worsen asthma AND uncontrolled asthma has fetal risks. May need to MAINTAIN or even step UP, not continue stepping down.",
                elements_that_should_change=[
                    "Step-down recommendation (now risky due to pregnancy)",
                    "Medication choice (must consider pregnancy safety)",
                    "Cost considerations (insurance change)",
                    "Monitoring frequency (needs to increase)",
                ],
                elements_that_should_stay=[
                    "Peak flow monitoring",
                    "Regular follow-up schedule",
                    "GERD management (important in pregnancy too)",
                ],
                key_adaptations=[
                    "Recognize pregnancy changes risk calculus for step-down",
                    "Switch to pregnancy-safe ICS if needed",
                    "Address cost barrier to adherence",
                    "Increase monitoring frequency given dual risk factors",
                ],
            ),
            TurnInfo(
                turn_number=2,
                narrative="At the 8-week follow-up, the patient reports she had a miscarriage at 8 weeks. She is emotionally devastated, tearful during the visit, and states 'I stopped taking all my medications — I don't care about anything right now.' Her peak flows have dropped 30%. PHQ-9 score: 18 (moderately severe depression). She has not filled any prescriptions in 3 weeks.",
                new_information="Miscarriage at 8 weeks. Severe grief reaction. PHQ-9 = 18. Non-adherent to all medications for 3 weeks. Peak flows down 30%.",
                shift_type=ShiftType.CONTEXT_REVERSAL,
                question="How does this change your approach?",
                expected_response_summary="Complete paradigm shift from medication optimization to crisis management: (1) Pregnancy considerations removed. (2) PRIMARY concern is now mental health — depression screening positive, grief counseling referral, possible antidepressant consideration. (3) Medication non-adherence is a SYMPTOM of depression, not a separate problem. (4) Asthma worsening due to non-adherence — may need to step UP (opposite of original plan). (5) Approach: empathetic counseling first, address depression, restart medications with simplest possible regimen, close follow-up.",
                elements_that_should_change=[
                    "Pregnancy-specific medication choices (no longer relevant)",
                    "Primary clinical focus (now mental health, not step-down)",
                    "Treatment direction (likely step UP, not step down)",
                    "Medication selection (simplicity over optimization)",
                ],
                elements_that_should_stay=[
                    "Peak flow monitoring (even more critical now)",
                    "Regular follow-up (increase frequency)",
                    "GERD management",
                ],
                key_adaptations=[
                    "Recognize depression as the primary clinical problem",
                    "Understand non-adherence as a symptom of grief/depression",
                    "Shift from 'medication optimization' to 'crisis stabilization'",
                    "Consider step-up therapy given worsening asthma",
                    "Refer for mental health support",
                ],
            ),
        ],
        difficulty=4,
    ),

    MidCourseScenario(
        id="hc_flex_002",
        domain=Domain.HEALTHCARE,
        title="The Evolving Infection",
        initial_context="""Patient: 72-year-old male, nursing home resident
Chief complaint: Fever (38.9°C), productive cough, increased confusion x 2 days
PMH: Type 2 diabetes (A1c 8.1%), COPD (moderate), mild cognitive impairment, BPH
Medications: Metformin 1000mg BID, tiotropium, albuterol PRN, tamsulosin
Allergies: Penicillin (anaphylaxis)
Baseline: Ambulatory with walker, ADLs independent except bathing
CXR: Right lower lobe infiltrate
Labs: WBC 14,800, procalcitonin 1.8, creatinine 1.1 (baseline 0.9), lactate 1.4
Urinalysis: negative""",
        turns=[
            TurnInfo(
                turn_number=0,
                narrative="The patient presents with nursing home-acquired pneumonia. He is hemodynamically stable but confused (change from baseline).",
                new_information=None,
                shift_type=None,
                question="What is your initial antibiotic regimen and management plan?",
                expected_response_summary="Healthcare-associated pneumonia in penicillin-allergic patient: Consider respiratory fluoroquinolone (levofloxacin) or aztreonam + vancomycin for MRSA coverage given nursing home origin. Admit to general ward. Monitor closely given age and comorbidities.",
                elements_that_should_change=[],
                elements_that_should_stay=[],
                key_adaptations=[],
            ),
            TurnInfo(
                turn_number=1,
                narrative="""Day 2 update: Blood cultures from admission are growing gram-negative rods. The microbiology lab calls with a preliminary report: the organism is an ESBL-producing E. coli (resistant to 3rd-gen cephalosporins and fluoroquinolones). The patient's creatinine has risen to 1.8 (from 1.1 on admission). His urine output in the last 8 hours is 180mL (oliguria). He remains febrile at 39.2°C.""",
                new_information="ESBL E. coli bacteremia. Creatinine rising (1.1→1.8). Oliguria developing. Persistent fever.",
                shift_type=ShiftType.CONSTRAINT_CHANGE,
                question="How does this change your antibiotic choice and overall management?",
                expected_response_summary="Major antibiotic change: ESBL E. coli means carbapenems (meropenem preferred). BUT — developing AKI means renal dosing AND avoid nephrotoxins. Key adaptations: (1) Switch to meropenem (dose-adjusted for renal function). (2) Hold metformin (AKI risk of lactic acidosis). (3) Aggressive fluid resuscitation for sepsis + AKI. (4) Consider ICU transfer given organ dysfunction (sepsis-3 criteria likely met). (5) Source question: if blood cultures growing E. coli, reconsider urinary source despite negative UA (false negatives occur in elderly).",
                elements_that_should_change=[
                    "Antibiotic regimen (fluoroquinolone won't work against ESBL)",
                    "Renal dosing adjustments needed",
                    "Metformin should be held",
                    "Level of care (may need ICU)",
                    "Source investigation (reconsider urinary source)",
                ],
                elements_that_should_stay=[
                    "Respiratory support as needed",
                    "Monitoring frequency",
                    "Fluid management (though volume needs reassessment)",
                ],
                key_adaptations=[
                    "Recognize ESBL resistance pattern limits options to carbapenems",
                    "Adjust for developing AKI (dosing + hold nephrotoxins + hold metformin)",
                    "Escalate level of care for organ dysfunction",
                    "Question the pneumonia-only source — E. coli more commonly urinary",
                ],
            ),
            TurnInfo(
                turn_number=2,
                narrative="""Day 4: Repeat CT shows the lung infiltrate is improving on meropenem. However, CT also reveals a 4cm perinephric abscess on the right side — likely the true source of the E. coli bacteremia (seeded from a urinary source to kidney to bloodstream). Creatinine has stabilized at 1.6 but the patient now has new-onset atrial fibrillation with rapid ventricular response (HR 142). He is on a heparin drip for the new AF. His platelet count has dropped from 220,000 on admission to 68,000 today. His 4T score for HIT (heparin-induced thrombocytopenia) calculates to 6 (high probability).""",
                new_information="Perinephric abscess found (true source). New atrial fibrillation. Platelet drop 220K→68K. 4T score = 6 (likely HIT).",
                shift_type=ShiftType.CONTEXT_REVERSAL,
                question="How does this change your management plan?",
                expected_response_summary="Multiple simultaneous pivots: (1) Perinephric abscess needs drainage (IR-guided percutaneous vs surgical) — antibiotics alone won't clear it. (2) STOP HEPARIN IMMEDIATELY — HIT is a medical emergency. Switch to argatroban or bivalirudin for AF anticoagulation. (3) AF rate control: consider amiodarone given hemodynamic instability. (4) Send HIT antibody (PF4). (5) Continue meropenem. (6) Urology consult for abscess source investigation (obstruction? stone?). The clinical picture has shifted from 'pneumonia' to 'complicated urinary source sepsis with iatrogenic HIT.'",
                elements_that_should_change=[
                    "Source of infection (not pneumonia — perinephric abscess)",
                    "Treatment plan (need abscess drainage, not just antibiotics)",
                    "Anticoagulation (STOP heparin → switch to non-heparin)",
                    "Specialty consultations (IR, urology, hematology)",
                ],
                elements_that_should_stay=[
                    "Meropenem (still appropriate for ESBL E. coli)",
                    "Renal monitoring",
                    "ICU-level care",
                    "Metformin held",
                ],
                key_adaptations=[
                    "Recognize perinephric abscess changes treatment from medical to procedural",
                    "IMMEDIATELY stop heparin for suspected HIT",
                    "Manage new AF with non-heparin anticoagulation",
                    "Coordinate multiple new specialty consultations",
                ],
            ),
        ],
        difficulty=5,
    ),
]

# =============================================================================
# Finance Scenarios
# =============================================================================

FINANCE_SCENARIOS: List[MidCourseScenario] = [
    MidCourseScenario(
        id="fin_flex_001",
        domain=Domain.FINANCE,
        title="The Rate Regime Shift",
        initial_context="""Client Profile:
- 58-year-old executive, plans to retire at 62
- Portfolio: $4.2M across taxable brokerage and IRA
- Risk tolerance: Moderate-aggressive
- Current allocation: 60% equities / 30% fixed income / 10% alternatives
- Fixed income: Short duration (avg 2.1 years), overweight floating rate notes and bank loans
- Equity: Overweight financials (18%), energy (12%), underweight tech (8%)
- Income need: $15,000/month starting at retirement

Market Context (as of positioning):
- Fed funds rate: 5.25-5.50%
- Fed guidance: 2-3 additional rate hikes expected
- 10Y Treasury: 4.8%
- Yield curve: inverted
- Bank stocks rallying on NIM expansion expectations""",
        turns=[
            TurnInfo(
                turn_number=0,
                narrative="The client's portfolio is positioned for a continued rising rate environment. The Fed has signaled further tightening. Review the current positioning.",
                new_information=None,
                shift_type=None,
                question="Evaluate the current portfolio positioning. Is it appropriate given the market outlook and the client's profile?",
                expected_response_summary="Portfolio is well-positioned for rising rates: short duration protects fixed income, floating rate benefits from higher rates, financial sector benefits from NIM expansion. However, note the 4-year retirement horizon — should begin planning for transition to income-generating portfolio. The aggressive rate positioning is appropriate short-term but needs a glide path.",
                elements_that_should_change=[],
                elements_that_should_stay=[],
                key_adaptations=[],
            ),
            TurnInfo(
                turn_number=1,
                narrative="""BREAKING: A major regional bank (similar in size to SVB) has just collapsed due to a deposit run triggered by unrealized losses on its held-to-maturity bond portfolio. Two other regional banks are halted pending investigation. The KBW Bank Index is down 22% this week. The Fed has issued an emergency statement suggesting a potential pause in rate hikes and is considering emergency lending facilities.

The client calls in a panic: 'My bank stocks are getting crushed. Should I sell everything?'

Client's current bank stock holdings: $756K (18% of portfolio), down 28% from last week. Several positions are regional banks similar to the one that failed.""",
                new_information="Regional bank collapse. Bank stocks down 22-28%. Fed signaling rate pause. Client panicking.",
                shift_type=ShiftType.CONTEXT_REVERSAL,
                question="How should you advise the client? What changes to the portfolio are warranted?",
                expected_response_summary="Major regime shift requires significant adaptation: (1) DO NOT panic-sell everything — but DO reduce regional bank exposure to solvent, well-capitalized names only. (2) Reassess the rate thesis — if Fed pauses/cuts, the entire portfolio positioning is wrong (short duration hurts, floating rate income declines, financials face pressure). (3) Begin extending duration in fixed income to benefit from potential rate cuts. (4) The retirement timeline makes this MORE urgent — can't afford to be wrong for 4 years. (5) Address the client's emotions first — acknowledge the fear, then present a rational plan.",
                elements_that_should_change=[
                    "Bank stock overweight (reduce/restructure)",
                    "Rate-rising thesis (may need to reverse)",
                    "Fixed income duration (begin extending)",
                    "Floating rate overweight (reduce if rates peak)",
                ],
                elements_that_should_stay=[
                    "Overall equity/fixed income split (roughly)",
                    "Retirement timeline planning",
                    "Income need planning ($15K/month)",
                    "Tax-awareness in trading decisions",
                ],
                key_adaptations=[
                    "Distinguish between panic selling and rational risk reduction",
                    "Recognize the rate regime may be shifting",
                    "Address client emotions before portfolio mechanics",
                    "Consider tax implications of selling bank stocks at a loss (tax-loss harvesting opportunity)",
                ],
            ),
            TurnInfo(
                turn_number=2,
                narrative="""Two weeks later: The Fed has emergency-cut rates by 50bp and launched a new lending facility. Markets initially rallied but are now volatile. The client's employer (a regional bank) has just announced it is 'exploring strategic options' — widely interpreted as a potential sale or wind-down. The client may lose his job within 90 days.

His total compensation is $380K/year. His mortgage payment is $4,200/month. He has 8 months of cash reserves. His wife's income is $85K/year.

He asks: 'Should I retire early? Can we afford it?'""",
                new_information="Fed emergency cut 50bp. Client's employer (regional bank) may fail. Potential job loss in 90 days. Early retirement question.",
                shift_type=ShiftType.GOAL_CHANGE,
                question="How does this fundamentally change your financial planning advice?",
                expected_response_summary="The conversation has shifted from portfolio management to LIFE PLANNING: (1) Immediate: extend cash reserves — move from 8 months to 12+ months by reducing discretionary spending and pausing retirement contributions. (2) Early retirement at 58 vs planned 62 = 4 extra years of portfolio drawdown without Social Security — run updated Monte Carlo. (3) Healthcare: losing employer coverage before 65 means ACA marketplace or COBRA ($2-3K/month). (4) Severance negotiation strategy if termination comes. (5) Portfolio becomes the primary income source 4 years early — shift to more conservative allocation immediately. (6) Wife's $85K can cover mortgage but not full lifestyle. The entire risk profile has fundamentally changed from 'aggressive growth for 4 more years' to 'capital preservation for imminent income replacement.'",
                elements_that_should_change=[
                    "Risk tolerance (must decrease — portfolio is now primary income)",
                    "Time horizon (retirement may be NOW, not in 4 years)",
                    "Equity allocation (reduce given new risk profile)",
                    "Cash reserves strategy (extend runway)",
                    "Planning focus (portfolio → comprehensive financial plan)",
                ],
                elements_that_should_stay=[
                    "Tax-efficient management",
                    "Income need target ($15K/month, though may need to adjust)",
                    "Long-term investment discipline",
                ],
                key_adaptations=[
                    "Recognize this is no longer a portfolio question — it's a life transition",
                    "Address healthcare coverage gap (58 to 65)",
                    "Run updated retirement projections with forced early retirement",
                    "Consider severance/unemployment as bridge income",
                    "Shift allocation to reflect new reality (income > growth)",
                ],
            ),
        ],
        difficulty=4,
    ),
]


# =============================================================================
# Full Scenario Registry
# =============================================================================

ALL_SCENARIOS = HEALTHCARE_SCENARIOS + FINANCE_SCENARIOS


def get_scenarios(
    domain: Optional[Domain] = None,
) -> List[MidCourseScenario]:
    """Get scenarios optionally filtered by domain."""
    if domain:
        return [s for s in ALL_SCENARIOS if s.domain == domain]
    return ALL_SCENARIOS
