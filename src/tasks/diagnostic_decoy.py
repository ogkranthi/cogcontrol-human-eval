"""
Task EF-1: The Diagnostic Decoy (Inhibition)
=============================================

The first operationalization of the Stroop paradigm for LLMs.

Cognitive Science Basis: Stroop Test (Stroop, 1935)
- Congruent trials: surface pattern matches correct answer
- Incongruent trials: surface pattern conflicts with correct answer
- Interference Effect = accuracy_congruent - accuracy_incongruent

The model must suppress a dominant, automatic pattern-matching response
triggered by surface features and instead engage controlled processing.

Domains: Healthcare (clinical diagnosis) + Finance (investment analysis)
"""

import json
import random
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum


class TrialType(str, Enum):
    CONGRUENT = "congruent"      # surface pattern matches correct answer
    INCONGRUENT = "incongruent"  # surface pattern conflicts with correct answer


class Domain(str, Enum):
    HEALTHCARE = "healthcare"
    FINANCE = "finance"


class DecoyStrength(str, Enum):
    HIGH = "high"      # textbook-perfect misleading pattern
    MEDIUM = "medium"  # strong but not textbook misleading pattern


class ContradictionSalience(str, Enum):
    BURIED = "buried"      # hard to spot — deep in the text
    MODERATE = "moderate"  # present but not highlighted
    OBVIOUS = "obvious"    # clearly stated


@dataclass
class DiagnosticDecoyVignette:
    """A single Diagnostic Decoy trial."""
    id: str
    domain: Domain
    trial_type: TrialType
    title: str
    case_presentation: str
    surface_pattern_label: str  # what the surface pattern suggests
    correct_answer: str
    correct_reasoning: str
    contradictory_evidence: List[str]
    decoy_strength: DecoyStrength
    contradiction_salience: ContradictionSalience
    question: str
    difficulty: int  # 1-5

    def to_prompt(self) -> str:
        """Generate the prompt sent to the model."""
        return f"""You are an expert advisor. Read the following case carefully and answer the question.

## Case

{self.case_presentation}

## Question

{self.question}

## Instructions

Provide your response in the following JSON format:
{{
    "initial_impression": "What does the case appear to be at first glance?",
    "key_observations": ["List ALL relevant details you noticed, including any that might complicate the initial impression"],
    "contradictory_evidence": ["List any details that conflict with or complicate the initial impression"],
    "final_assessment": "Your final answer/recommendation based on ALL evidence",
    "confidence": 0.0 to 1.0,
    "reasoning": "Step-by-step reasoning explaining how you arrived at your final assessment"
}}"""

    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# Healthcare Vignettes
# =============================================================================

HEALTHCARE_VIGNETTES: List[DiagnosticDecoyVignette] = [
    # --- INCONGRUENT: Surface pattern suggests wrong answer ---

    DiagnosticDecoyVignette(
        id="hc_incong_001",
        domain=Domain.HEALTHCARE,
        trial_type=TrialType.INCONGRUENT,
        title="The Capsaicin STEMI Mimic",
        case_presentation="""A 52-year-old male presents to the emergency department with acute substernal chest pain radiating to the left arm, accompanied by diaphoresis and nausea. He rates the pain as 8/10.

Vital signs: HR 92, BP 148/88, RR 20, SpO2 97%.

ECG shows ST-segment elevation in leads II, III, and aVF with reciprocal changes in leads I and aVL. The ST elevation measures 0.5mm in lead II (just meeting STEMI criteria).

Initial troponin-I: 0.04 ng/mL (reference range: <0.04 ng/mL — at the very upper limit of normal, not clearly elevated).

Past medical history: Chronic lower back pain, GERD, hypertension.

Current medications: Lisinopril 10mg daily, omeprazole 20mg daily.

Nursing notes document that the patient applied a high-strength capsaicin pain patch (8% Qutenza) to his anterior chest wall approximately 2 hours ago for musculoskeletal chest wall pain that has been ongoing for 3 weeks. He reports the acute pain episode started roughly 30 minutes after applying the patch. The burning quality of the pain is noted to be "similar to his usual chest wall pain but more intense."

His previous ECG from a routine visit 3 months ago showed baseline ST changes with 0.3mm elevation in the inferior leads, noted as "early repolarization pattern — normal variant." """,
        surface_pattern_label="ST-Elevation Myocardial Infarction (STEMI)",
        correct_answer="This is likely NOT a STEMI. The presentation is better explained by capsaicin-induced chest pain mimicking cardiac symptoms. Serial troponins, pain reassessment after patch removal, and comparison with prior ECG should be performed before cath lab activation.",
        correct_reasoning="Multiple factors argue against true STEMI: (1) The capsaicin patch was applied 2 hours before onset — known to cause severe burning chest pain that can mimic cardiac pain. (2) Troponin is at the very upper limit of normal, not clearly elevated as expected in true STEMI. (3) The ST elevation is only 0.5mm, barely meeting criteria. (4) Prior ECG showed baseline 0.3mm inferior ST elevation (early repolarization), meaning the incremental change is only 0.2mm. (5) The patient has a history of chest wall pain. The appropriate next step is: remove capsaicin patch, reassess pain in 30 minutes, obtain serial troponins at 3 and 6 hours, and compare current ECG to prior baseline.",
        contradictory_evidence=[
            "Capsaicin patch applied to chest 2 hours before symptom onset",
            "Troponin at upper limit of normal (0.04), not clearly elevated",
            "ST elevation only 0.5mm (minimally meeting criteria)",
            "Prior ECG showed 0.3mm baseline ST elevation (early repolarization)",
            "History of chronic chest wall pain",
            "Pain described as 'similar to usual chest wall pain but more intense'",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.BURIED,
        question="What is the most appropriate next step in management?",
        difficulty=4,
    ),

    DiagnosticDecoyVignette(
        id="hc_incong_002",
        domain=Domain.HEALTHCARE,
        trial_type=TrialType.INCONGRUENT,
        title="The Thyroid Storm That Isn't",
        case_presentation="""A 34-year-old female presents to the ED with palpitations, tremor, anxiety, weight loss of 8 lbs over 2 weeks, and heat intolerance. She appears agitated and diaphoretic.

Vital signs: HR 128, BP 162/78 (wide pulse pressure), Temperature 38.4°C (101.1°F), RR 22.

Physical exam: Fine tremor of outstretched hands, lid lag present, warm moist skin, hyperreflexia in all extremities. Thyroid is diffusely enlarged and non-tender.

Labs: TSH < 0.01 mIU/L (very suppressed), Free T4 5.8 ng/dL (normal 0.8-1.8), Free T3 12.4 pg/mL (normal 2.3-4.2).

The Burch-Wartofsky score calculates to 50 (suggestive of thyroid storm).

The patient's medication list from her pharmacy records shows she was prescribed levothyroxine 300 mcg daily (an unusually high dose) by an online telehealth provider 3 weeks ago. Her prior medical records show a TSH of 3.2 mIU/L (normal) from 6 weeks ago. She mentions she "wanted to lose weight faster" and found a telehealth service that prescribed thyroid hormone. She has no prior history of thyroid disease.

Additionally, her urine drug screen is positive for amphetamines. She admits to using Adderall obtained from a friend "to help with energy" for the past week.""",
        surface_pattern_label="Thyroid Storm (Graves' Disease)",
        correct_answer="This is exogenous thyrotoxicosis (iatrogenic/factitious) from inappropriate levothyroxine supplementation, compounded by amphetamine use — NOT primary thyroid storm from Graves' disease. Treatment differs significantly: stop levothyroxine, supportive care, beta-blockade for symptom control, and substance use counseling. Thionamides (PTU/methimazole) are NOT indicated as there is no endogenous thyroid hormone overproduction.",
        correct_reasoning="Key distinguishing factors: (1) Normal TSH 6 weeks ago rules out pre-existing Graves'. (2) She started high-dose levothyroxine 3 weeks ago — the timeline matches symptom onset. (3) 300mcg levothyroxine is a supratherapeutic dose even for thyroid cancer suppression. (4) Amphetamine use explains additional sympathomimetic symptoms. (5) While the Burch-Wartofsky score is elevated, this scoring system does not differentiate between endogenous and exogenous thyrotoxicosis. Treatment for exogenous thyrotoxicosis is fundamentally different — thionamides won't help because the thyroid gland itself isn't overproducing.",
        contradictory_evidence=[
            "Normal TSH (3.2) just 6 weeks ago — no prior thyroid disease",
            "Started high-dose levothyroxine (300mcg) from telehealth 3 weeks ago",
            "Motivated by weight loss, not medical indication",
            "Positive urine drug screen for amphetamines",
            "Adderall use for past week contributes to sympathomimetic presentation",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.MODERATE,
        question="What is the most likely diagnosis and appropriate management?",
        difficulty=4,
    ),

    DiagnosticDecoyVignette(
        id="hc_incong_003",
        domain=Domain.HEALTHCARE,
        trial_type=TrialType.INCONGRUENT,
        title="The Appendicitis Confounder",
        case_presentation="""A 28-year-old male presents with 18 hours of abdominal pain that started periumbilically and migrated to the right lower quadrant. He has nausea, one episode of vomiting, and anorexia.

Vital signs: HR 88, BP 130/82, Temperature 37.9°C (100.2°F).

Physical exam: RLQ tenderness with guarding, positive McBurney's point tenderness, positive Rovsing's sign, positive psoas sign.

Labs: WBC 13,200 with 82% neutrophils (left shift). CRP 4.2 mg/dL (elevated).

Alvarado Score: 9/10 (highly suggestive of acute appendicitis).

The surgical team is consulted and recommends proceeding to the OR.

CT abdomen/pelvis (obtained per ED protocol before surgical consult arrived): The appendix appears normal in caliber (5mm) without wall thickening, periappendiceal fat stranding, or appendicolith. However, the CT incidentally shows a 3cm right-sided mesenteric lymph node conglomerate with surrounding fat stranding centered in the right iliac fossa. There is also mild terminal ileum wall thickening (4mm).

Further history obtained while awaiting OR: The patient mentions he returned from a camping trip in upstate New York 10 days ago where he drank from a stream. He has had watery diarrhea for 3 days that he "didn't think was related" and didn't initially mention.""",
        surface_pattern_label="Acute Appendicitis",
        correct_answer="This is mesenteric lymphadenitis, most likely from Yersinia enterocolitica infection (pseudoappendicitis syndrome), NOT acute appendicitis. The CT shows a normal appendix. Appropriate management: hold surgery, stool cultures, blood cultures, supportive care, and antibiotics if Yersinia confirmed.",
        correct_reasoning="Despite a classic appendicitis presentation and high Alvarado score: (1) CT shows a NORMAL appendix — this is the most important finding. (2) Mesenteric lymphadenopathy with terminal ileum thickening is classic for Yersinia pseudoappendicitis. (3) Camping trip with stream water exposure 10 days ago is the epidemiological link. (4) The watery diarrhea (which the patient didn't mention initially) supports enteric infection. (5) Yersinia enterocolitica is notorious for mimicking appendicitis — 'pseudoappendicitis syndrome' — with RLQ pain, fever, leukocytosis, and even positive peritoneal signs. Unnecessary appendectomy would expose the patient to surgical risk for a medical condition.",
        contradictory_evidence=[
            "CT shows normal appendix (5mm, no inflammation)",
            "3cm mesenteric lymph node conglomerate on CT",
            "Terminal ileum wall thickening (4mm)",
            "Camping trip 10 days ago with stream water exposure",
            "3 days of watery diarrhea (initially unreported)",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.MODERATE,
        question="Given the CT findings and additional history, should the patient proceed to surgery? What is the most likely diagnosis?",
        difficulty=3,
    ),

    # --- CONGRUENT: Surface pattern matches correct answer ---

    DiagnosticDecoyVignette(
        id="hc_cong_001",
        domain=Domain.HEALTHCARE,
        trial_type=TrialType.CONGRUENT,
        title="Classic Community-Acquired Pneumonia",
        case_presentation="""A 62-year-old male with a history of COPD presents with 3 days of productive cough with yellow-green sputum, fever, and pleuritic chest pain on the right side.

Vital signs: HR 96, BP 134/76, Temperature 38.8°C (101.8°F), RR 24, SpO2 91% on room air.

Physical exam: Decreased breath sounds at the right base with dullness to percussion. Bronchial breath sounds and egophony present in the right lower lobe. No wheezing.

Labs: WBC 18,400 with 88% neutrophils. Procalcitonin 2.4 ng/mL (elevated, suggestive of bacterial infection). BMP normal. Lactate 1.2 mmol/L.

Chest X-ray: Right lower lobe consolidation with air bronchograms. No pleural effusion. No mass lesion.

The patient's CURB-65 score is 2 (age >65 would not apply, but confusion absent, urea normal, RR ≥30 no, BP systolic ≥90). PSI/PORT score class III.

Sputum gram stain shows gram-positive diplococci. The patient received his annual influenza vaccine but has not received the pneumococcal vaccine.""",
        surface_pattern_label="Community-Acquired Pneumonia (CAP)",
        correct_answer="Classic community-acquired pneumonia, likely Streptococcus pneumoniae based on gram stain. Admit to general ward (CURB-65=2, PSI class III). Start empiric antibiotics per ATS/IDSA guidelines: respiratory fluoroquinolone OR beta-lactam plus macrolide. Pneumococcal vaccination before discharge.",
        correct_reasoning="This is a straightforward case: (1) Classic presentation — productive cough, fever, pleuritic pain. (2) Physical exam consistent with consolidation. (3) CXR confirms RLL consolidation. (4) Gram-positive diplococci = Streptococcus pneumoniae until proven otherwise. (5) Elevated procalcitonin supports bacterial etiology. (6) CURB-65/PSI scores indicate inpatient but not ICU-level care. No contradictory findings.",
        contradictory_evidence=[],  # congruent trial — no contradictions
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.OBVIOUS,
        question="What is the diagnosis and recommended management?",
        difficulty=2,
    ),

    DiagnosticDecoyVignette(
        id="hc_cong_002",
        domain=Domain.HEALTHCARE,
        trial_type=TrialType.CONGRUENT,
        title="Classic Diabetic Ketoacidosis",
        case_presentation="""A 19-year-old female with no significant past medical history presents with 1 week of polyuria, polydipsia, and 12-pound unintentional weight loss. For the past 2 days she has had nausea, vomiting, and diffuse abdominal pain.

Vital signs: HR 118, BP 98/62, Temperature 37.1°C, RR 28 (deep, rapid — Kussmaul breathing pattern), SpO2 99%.

Physical exam: Appears dehydrated with dry mucous membranes, poor skin turgor. Fruity odor on breath. Abdomen diffusely tender but soft, no peritoneal signs. She is alert but appears fatigued.

Labs:
- Glucose: 486 mg/dL
- Sodium: 131 mEq/L (corrected sodium: 138 mEq/L)
- Potassium: 5.6 mEq/L
- Chloride: 98 mEq/L
- Bicarbonate: 8 mEq/L
- BUN: 32 mg/dL, Creatinine: 1.4 mg/dL
- Anion gap: 25
- pH: 7.14 (venous blood gas)
- Beta-hydroxybutyrate: 6.8 mmol/L (markedly elevated)
- HbA1c: 13.2%

Urinalysis: Glucose 3+, Ketones 3+.""",
        surface_pattern_label="Diabetic Ketoacidosis (DKA)",
        correct_answer="New-onset Type 1 Diabetes presenting with Diabetic Ketoacidosis. Severity: Severe (pH <7.24, bicarb <10). Management: aggressive IV fluid resuscitation (NS initially), continuous insulin infusion, potassium monitoring and replacement (hold K+ supplementation until K+ <5.3 given current 5.6), serial BMPs every 2-4 hours, ICU admission for severe DKA.",
        correct_reasoning="Textbook DKA: (1) Classic triad of polyuria, polydipsia, weight loss in a young patient = new-onset T1DM. (2) Hyperglycemia (486), high anion gap metabolic acidosis (AG=25, bicarb=8, pH 7.14), ketosis (BHB 6.8). (3) HbA1c 13.2% confirms chronic hyperglycemia. (4) All findings are consistent — no contradictory evidence.",
        contradictory_evidence=[],  # congruent
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.OBVIOUS,
        question="What is the diagnosis and immediate management plan?",
        difficulty=2,
    ),
]


# =============================================================================
# Finance Vignettes
# =============================================================================

FINANCE_VIGNETTES: List[DiagnosticDecoyVignette] = [
    # --- INCONGRUENT: Surface pattern suggests wrong answer ---

    DiagnosticDecoyVignette(
        id="fin_incong_001",
        domain=Domain.FINANCE,
        trial_type=TrialType.INCONGRUENT,
        title="The Manufactured Growth Story",
        case_presentation="""TechVista Inc. (TVST) — Mid-cap SaaS company, current market cap $4.2B.

HEADLINE METRICS (Last Quarter):
- Revenue: $285M (+18% YoY, accelerating from +12% prior quarter)
- Gross margin: 78% (expanded from 72% YoY)
- Net income: $42M (first profitable quarter after years of losses)
- Free cash flow: $38M positive
- Customer count: 12,400 (+22% YoY)
- Net Revenue Retention: 128%

MARKET SIGNALS:
- CEO purchased 50,000 shares ($2.1M) in the open market 45 days ago
- Three analyst upgrades in the past 30 days (Goldman Sachs, Morgan Stanley, JP Morgan)
- Golden cross: 50-day MA crossed above 200-day MA last week
- Short interest declined from 8% to 3% over past quarter

BURIED IN THE 10-Q (page 47 of 68):
Related Party Transactions note: "$78M of Q4 revenue (27% of total) came from CloudBridge Solutions, a company whose CEO is the brother of TechVista's CFO. This represents a 340% increase from the prior year's related-party revenue of $18M. The contract was signed without competitive bidding."

Footnote 14 — Revenue Recognition Changes: "Beginning Q3, the Company changed its revenue recognition policy for multi-year contracts from ratably over the contract term to recognizing 60% of total contract value upon signing. This change contributed approximately $34M to Q4 revenue. Had the prior policy been applied, revenue growth would have been approximately 4% YoY rather than 18%."

Footnote 18 — Insider Trading: "The CEO's share purchase was made 3 days after the Company's board approved (but had not yet publicly announced) the CloudBridge contract renewal at expanded terms."

MD&A Section (page 32): "Excluding the CloudBridge contract, organic customer growth was 3% YoY (vs. 22% reported including CloudBridge's 15 enterprise sub-accounts counted as separate customers)."

Auditor's note: The company changed its external auditor from Deloitte to a regional firm (Baker & Associates LLP) during the quarter, citing 'cost optimization.' """,
        surface_pattern_label="Strong Buy — accelerating growth, profitability inflection, insider buying, analyst upgrades",
        correct_answer="HIGH RISK — AVOID/SHORT. The surface metrics are manufactured through: (1) related-party revenue (27% from CFO's brother's company), (2) aggressive revenue recognition change adding $34M (organic growth only ~4%), (3) potentially illegal insider trading (CEO bought shares after non-public board approval), (4) inflated customer count (one related party counted as 15 customers), (5) auditor change is a major red flag. This has characteristics of potential accounting fraud.",
        correct_reasoning="Every headline metric is misleading: (1) 18% revenue growth is actually ~4% organic — the rest is a related-party contract and an accounting policy change. (2) The CFO's brother's company providing 27% of revenue is a massive conflict of interest and concentration risk. (3) CEO share purchase 3 days after non-public board approval of the related-party deal may constitute insider trading. (4) Customer count inflation (15 sub-accounts from one related party) makes growth metrics unreliable. (5) Switching from Big 4 (Deloitte) to a regional auditor during a period of aggressive accounting changes is a classic fraud red flag. (6) Analyst upgrades may be based on the manufactured metrics. This situation warrants SEC scrutiny.",
        contradictory_evidence=[
            "27% of revenue from CFO's brother's company (related party)",
            "Revenue recognition change added $34M — organic growth only ~4%",
            "CEO purchased shares 3 days after non-public board approval of related-party deal",
            "22% customer growth includes 15 sub-accounts from one related party (organic: 3%)",
            "Auditor switch from Deloitte to regional firm mid-year",
            "Related-party contract signed without competitive bidding",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.BURIED,
        question="Based on your analysis of TechVista's financial profile, what is your investment recommendation and risk assessment?",
        difficulty=4,
    ),

    DiagnosticDecoyVignette(
        id="fin_incong_002",
        domain=Domain.FINANCE,
        trial_type=TrialType.INCONGRUENT,
        title="The Value Trap",
        case_presentation="""Meridian Manufacturing Corp (MMC) — Large-cap industrial conglomerate, market cap $28B.

VALUATION METRICS:
- P/E ratio: 8.2x (industry average: 18.5x) — appears deeply undervalued
- P/B ratio: 0.7x (trading below book value)
- Dividend yield: 6.8% (vs industry avg 2.1%)
- EV/EBITDA: 5.1x (industry avg: 12.3x)
- Free cash flow yield: 11.2%

BULLISH SIGNALS:
- Buffett-style "margin of safety" — trading at ~55% discount to intrinsic value per DCF
- Activist investor Starboard Value disclosed 4.8% stake, pushing for board changes
- Company announced $2B share buyback program (7% of market cap)
- 15-year consecutive dividend increase history

FOOTNOTES AND FINE PRINT:

10-K Risk Factors (page 89): "Approximately 62% of our revenue is derived from products containing PFAS compounds. The EPA's final PFAS National Primary Drinking Water Regulation, effective 2024, designates PFOA and PFOS as hazardous substances under CERCLA. The Company has been named in 3,400 pending lawsuits related to PFAS contamination, with plaintiffs seeking aggregate damages exceeding $18B."

Note 22 — Contingent Liabilities: "The Company's total environmental remediation liability is estimated at $1.2B-$8.4B. Due to the uncertainty range, only the minimum ($1.2B) is accrued on the balance sheet. Independent analysis by environmental consultants suggests the mid-range estimate of $4.8B is most probable."

Note 15 — Pension: "The Company's defined benefit pension plan is underfunded by $3.2B on a projected benefit obligation basis. The assumed discount rate of 5.8% is 120 basis points above the corporate bond benchmark."

MD&A: "Capital expenditure requirements for PFAS remediation at 14 manufacturing sites are estimated at $400M-$900M over the next 5 years, in addition to legal settlement costs."

Balance Sheet: Total debt: $12.4B. Debt-to-EBITDA: 4.1x. Next major maturity: $3.8B in 18 months.""",
        surface_pattern_label="Deep Value — strong buy at 55% discount to intrinsic value",
        correct_answer="VALUE TRAP — AVOID. The low valuation reflects massive unrecognized liabilities: (1) $18B in pending PFAS lawsuits with probable cost of ~$4.8B (vs. only $1.2B accrued), (2) $3.2B pension underfunding masked by aggressive discount rate assumptions, (3) 62% revenue exposure to PFAS products facing regulatory phase-out, (4) $3.8B debt maturity in 18 months with 4.1x leverage. Adjusted for probable liabilities, the stock is NOT cheap — it may be overvalued.",
        correct_reasoning="The 'cheap' valuation is an illusion: (1) $4.8B probable PFAS liability (mid-range estimate) minus $1.2B already accrued = $3.6B unrecognized liability = ~13% of market cap. (2) If pension discount rate were at benchmark (4.6% vs assumed 5.8%), underfunding would be significantly larger. (3) 62% of revenue from PFAS products means the core business is facing existential regulatory risk. (4) $3.8B debt maturity in 18 months with already-high leverage creates refinancing risk. (5) The buyback and dividend may be unsustainable if PFAS settlements materialize. (6) The DCF 'intrinsic value' calculation likely doesn't account for litigation costs. This is a classic value trap where headline metrics look cheap but the balance sheet has hidden bombs.",
        contradictory_evidence=[
            "3,400 pending PFAS lawsuits seeking $18B in damages",
            "Probable environmental liability of $4.8B vs only $1.2B accrued",
            "62% of revenue from products facing PFAS regulation",
            "Pension underfunded by $3.2B with aggressive discount rate assumption",
            "$3.8B debt maturing in 18 months with 4.1x leverage",
            "PFAS remediation capex of $400M-$900M additional",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.BURIED,
        question="Is Meridian Manufacturing an attractive value investment at current levels? Provide your risk assessment and recommendation.",
        difficulty=4,
    ),

    # --- CONGRUENT: Surface pattern matches correct answer ---

    DiagnosticDecoyVignette(
        id="fin_cong_001",
        domain=Domain.FINANCE,
        trial_type=TrialType.CONGRUENT,
        title="Straightforward Growth Stock",
        case_presentation="""NovaPay Technologies (NPAY) — Mid-cap fintech, market cap $6.8B.

METRICS:
- Revenue: $520M (+32% YoY, consistent for 6 consecutive quarters)
- Gross margin: 68% (stable)
- Operating margin: 12% (expanding from 5% two years ago)
- Free cash flow: $62M (first full year of positive FCF)
- Total Payment Volume: $89B (+41% YoY)
- Net Revenue Retention: 135%
- Customer count: 48,000 merchants (+28% YoY, all organic)

FUNDAMENTALS:
- No related-party transactions
- Revenue diversified across 48,000 merchants, no customer >2% of revenue
- Same auditor (EY) for 5 consecutive years, clean opinions
- Management team has average tenure of 7 years
- Insider selling: minimal (<0.5% of holdings by any executive in past 12 months)
- R&D spend: 22% of revenue, up from 18% (investing in new products)
- Debt-to-equity: 0.3x (conservative balance sheet)
- International expansion to EU contributing 15% of new merchant growth

VALUATION: P/E 45x forward (elevated but justified by growth), PEG ratio 1.2x.""",
        surface_pattern_label="Strong Growth — quality compounder with clean fundamentals",
        correct_answer="Quality growth stock with strong fundamentals. Revenue acceleration is organic, margins expanding, balance sheet clean, no red flags in footnotes. Valuation is elevated (P/E 45x) but PEG ratio of 1.2x is reasonable for the growth rate. Suitable for growth-oriented portfolios with appropriate position sizing.",
        correct_reasoning="All signals align: (1) Consistent 32% growth over 6 quarters with no accounting gimmicks. (2) Clean revenue diversification — no customer concentration or related-party risk. (3) Same Big 4 auditor for 5 years with clean opinions. (4) Minimal insider selling. (5) Strong unit economics (135% NRR, expanding margins). (6) Conservative balance sheet. No contradictory evidence in the footnotes.",
        contradictory_evidence=[],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.OBVIOUS,
        question="Evaluate NovaPay as a potential investment. What is your risk assessment?",
        difficulty=2,
    ),

    DiagnosticDecoyVignette(
        id="fin_cong_002",
        domain=Domain.FINANCE,
        trial_type=TrialType.CONGRUENT,
        title="Clear Distressed Credit",
        case_presentation="""RetailMax Holdings (RMAX) — Brick-and-mortar retail chain, market cap $380M (down 78% from 52-week high).

METRICS:
- Revenue: $2.1B (-18% YoY, accelerating decline from -8% prior year)
- Same-store sales: -22% YoY
- Operating margin: -8% (was +4% two years ago)
- Free cash flow: -$340M (massive cash burn)
- Net debt: $4.2B on a declining $380M equity base
- Debt-to-EBITDA: 14.8x (severe leverage)
- Interest coverage ratio: 0.6x (cannot cover interest payments from operations)

DISTRESS SIGNALS:
- Moody's downgraded to Caa2 (substantial credit risk)
- CDS spreads at 2,800 bps (market pricing ~60% probability of default)
- Supplier payment terms shortened from Net-60 to COD (cash on delivery)
- Three C-suite departures in 6 months
- Going concern qualification from auditor in latest 10-K
- Revolving credit facility drawn to 95% of capacity""",
        surface_pattern_label="Severe distress — near-certain default",
        correct_answer="Distressed credit on path to bankruptcy. Interest coverage below 1x, going concern qualification, and supplier COD terms all indicate the company cannot sustain operations. Equity is likely worthless. Avoid all positions; if holding debt, evaluate recovery scenarios for the restructuring.",
        correct_reasoning="All indicators consistent with imminent default: (1) Cannot cover interest payments (0.6x coverage). (2) Going concern audit opinion is the strongest warning. (3) Suppliers demanding cash = loss of trade credit, a death spiral for retail. (4) Management exodus. (5) Credit facility nearly exhausted. No contradictory positive signals exist.",
        contradictory_evidence=[],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.OBVIOUS,
        question="Assess the creditworthiness and investment outlook for RetailMax Holdings.",
        difficulty=2,
    ),
]


# =============================================================================
# Full Vignette Registry
# =============================================================================

ALL_VIGNETTES = HEALTHCARE_VIGNETTES + FINANCE_VIGNETTES


def get_vignettes(
    domain: Optional[Domain] = None,
    trial_type: Optional[TrialType] = None,
) -> List[DiagnosticDecoyVignette]:
    """Filter vignettes by domain and/or trial type."""
    results = ALL_VIGNETTES
    if domain:
        results = [v for v in results if v.domain == domain]
    if trial_type:
        results = [v for v in results if v.trial_type == trial_type]
    return results


def get_balanced_set(n_per_condition: int = 5) -> List[DiagnosticDecoyVignette]:
    """Get a balanced set of congruent/incongruent trials across domains."""
    balanced = []
    for domain in Domain:
        for trial_type in TrialType:
            pool = get_vignettes(domain=domain, trial_type=trial_type)
            balanced.extend(pool[:n_per_condition])
    random.shuffle(balanced)
    return balanced
