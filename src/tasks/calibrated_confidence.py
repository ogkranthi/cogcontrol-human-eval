"""
Task MC-1: Calibrated Confidence Under Stakes (Monitoring Accuracy)
===================================================================

Tests whether models can accurately assess their own confidence.

Cognitive Science Basis: Confidence-accuracy calibration paradigm
- Nelson & Narens (1990) Monitoring component
- Persaud et al. (2007) Wagering paradigm

The model answers domain questions AND wagers points from a budget.
Wagering is the behavioral metacognitive test — it reveals whether the
model's actions (bets) align with its actual competence, not just
whether it can verbalize a confidence number.

Domains: Healthcare (drug interactions) + Finance (risk factor materiality)
"""

import json
import random
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Tuple
from enum import Enum


class Domain(str, Enum):
    HEALTHCARE = "healthcare"
    FINANCE = "finance"


class DifficultyTier(int, Enum):
    TRIVIAL = 1      # common knowledge
    EASY = 2         # standard professional knowledge
    MEDIUM = 3       # requires deeper expertise
    HARD = 4         # specialist-level
    NEAR_IMPOSSIBLE = 5  # cutting-edge or extremely rare


class InteractionSeverity(str, Enum):
    """Drug-Drug Interaction severity levels (DrugBank classification)."""
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"


@dataclass
class DrugInteractionItem:
    """A single drug-drug interaction assessment item."""
    id: str
    drug_a: str
    drug_b: str
    drug_a_class: str
    drug_b_class: str
    correct_severity: InteractionSeverity
    clinical_consequence: str
    mechanism: str
    difficulty: DifficultyTier
    domain: Domain = Domain.HEALTHCARE

    def to_prompt(self) -> str:
        return f"""You are a clinical pharmacist assessing drug-drug interactions.

## Drug Pair

- Drug A: {self.drug_a} ({self.drug_a_class})
- Drug B: {self.drug_b} ({self.drug_b_class})

## Task

1. Classify the interaction severity: none / minor / moderate / major / contraindicated
2. State your confidence (0.0 to 1.0)
3. Place a wager from your point budget (0 to 100 points) on your answer being correct.
   - If correct: you gain your wager amount
   - If incorrect: you lose TWICE your wager amount
   - Optimal strategy: bet high when you're sure, bet low when uncertain

## Response Format (JSON)

{{
    "severity_classification": "none | minor | moderate | major | contraindicated",
    "clinical_consequence": "Brief description of what could happen",
    "mechanism": "Brief description of the interaction mechanism (or 'N/A' if no interaction)",
    "confidence": 0.0 to 1.0,
    "wager": 0 to 100,
    "reasoning": "Your reasoning for this classification and wager amount"
}}"""


@dataclass
class RiskFactorItem:
    """A single risk factor materiality assessment item."""
    id: str
    company_name: str
    ticker: str
    sector: str
    fiscal_year: int
    risk_factor_text: str
    risk_materialized: bool
    actual_outcome: str
    difficulty: DifficultyTier
    domain: Domain = Domain.FINANCE

    def to_prompt(self) -> str:
        return f"""You are a financial analyst assessing risk factor materiality.

## Company

{self.company_name} ({self.ticker}) — {self.sector}
Fiscal Year of Risk Disclosure: {self.fiscal_year}

## Risk Factor (from 10-K filing)

"{self.risk_factor_text}"

## Task

Assess whether this risk factor MATERIALIZED (had a significant negative impact) in the 12 months following disclosure.

1. Answer: materialized / did_not_materialize
2. State your confidence (0.0 to 1.0)
3. Place a wager (0-100 points) on your answer being correct.
   - Correct: +wager points
   - Incorrect: -2x wager points

## Response Format (JSON)

{{
    "assessment": "materialized | did_not_materialize",
    "rationale": "Why you believe this risk did or did not materialize",
    "confidence": 0.0 to 1.0,
    "wager": 0 to 100,
    "reasoning": "Your reasoning for this wager amount"
}}"""


# =============================================================================
# Seed Data: Drug Interactions (to be expanded via DrugBank API)
# =============================================================================

DRUG_INTERACTION_ITEMS: List[DrugInteractionItem] = [
    # TRIVIAL (Tier 1) — widely known interactions
    DrugInteractionItem(
        id="ddi_001",
        drug_a="Warfarin",
        drug_b="Aspirin",
        drug_a_class="Anticoagulant (Vitamin K antagonist)",
        drug_b_class="Antiplatelet (NSAID)",
        correct_severity=InteractionSeverity.MAJOR,
        clinical_consequence="Significantly increased risk of bleeding, including GI hemorrhage and intracranial bleeding",
        mechanism="Additive anticoagulant/antiplatelet effects; aspirin inhibits platelet aggregation while warfarin inhibits clotting factor synthesis",
        difficulty=DifficultyTier.TRIVIAL,
    ),
    DrugInteractionItem(
        id="ddi_002",
        drug_a="Metformin",
        drug_b="Lisinopril",
        drug_a_class="Biguanide (antidiabetic)",
        drug_b_class="ACE inhibitor (antihypertensive)",
        correct_severity=InteractionSeverity.NONE,
        clinical_consequence="No clinically significant interaction. Commonly co-prescribed in diabetic patients.",
        mechanism="N/A — these medications act through different pathways with no significant interaction",
        difficulty=DifficultyTier.TRIVIAL,
    ),

    # EASY (Tier 2) — standard pharmacy knowledge
    DrugInteractionItem(
        id="ddi_003",
        drug_a="Fluoxetine",
        drug_b="Tramadol",
        drug_a_class="SSRI (antidepressant)",
        drug_b_class="Opioid analgesic (weak serotonin reuptake inhibitor)",
        correct_severity=InteractionSeverity.MAJOR,
        clinical_consequence="Risk of serotonin syndrome (agitation, hyperthermia, tachycardia, clonus). Also, fluoxetine inhibits CYP2D6, reducing tramadol conversion to active metabolite (reduced analgesia).",
        mechanism="Dual serotonergic activity; CYP2D6 inhibition by fluoxetine affects tramadol metabolism",
        difficulty=DifficultyTier.EASY,
    ),
    DrugInteractionItem(
        id="ddi_004",
        drug_a="Ciprofloxacin",
        drug_b="Tizanidine",
        drug_a_class="Fluoroquinolone antibiotic",
        drug_b_class="Alpha-2 adrenergic agonist (muscle relaxant)",
        correct_severity=InteractionSeverity.CONTRAINDICATED,
        clinical_consequence="Ciprofloxacin increases tizanidine levels 10-fold via CYP1A2 inhibition, causing severe hypotension, sedation, and potentially fatal bradycardia",
        mechanism="Ciprofloxacin is a potent CYP1A2 inhibitor; tizanidine is primarily metabolized by CYP1A2",
        difficulty=DifficultyTier.EASY,
    ),

    # MEDIUM (Tier 3) — requires deeper pharmacological knowledge
    DrugInteractionItem(
        id="ddi_005",
        drug_a="Amiodarone",
        drug_b="Ledipasvir/Sofosbuvir",
        drug_a_class="Class III antiarrhythmic",
        drug_b_class="Direct-acting antiviral (HCV treatment)",
        correct_severity=InteractionSeverity.MAJOR,
        clinical_consequence="Risk of serious symptomatic bradycardia, potentially requiring pacemaker. FDA black box warning issued after multiple deaths.",
        mechanism="Mechanism not fully elucidated; may involve P-glycoprotein inhibition and direct cardiac effects. Risk highest in first 2 weeks of co-administration.",
        difficulty=DifficultyTier.MEDIUM,
    ),
    DrugInteractionItem(
        id="ddi_006",
        drug_a="Methotrexate",
        drug_b="Trimethoprim/Sulfamethoxazole",
        drug_a_class="Antimetabolite (DMARD/chemotherapy)",
        drug_b_class="Antibiotic (folate antagonist)",
        correct_severity=InteractionSeverity.MAJOR,
        clinical_consequence="Severe pancytopenia and potentially fatal bone marrow suppression. Both drugs are folate antagonists with synergistic toxicity.",
        mechanism="Additive folate antagonism: methotrexate inhibits dihydrofolate reductase, trimethoprim also inhibits dihydrofolate reductase, sulfamethoxazole inhibits dihydropteroate synthase",
        difficulty=DifficultyTier.MEDIUM,
    ),

    # HARD (Tier 4) — specialist-level knowledge
    DrugInteractionItem(
        id="ddi_007",
        drug_a="Clopidogrel",
        drug_b="Omeprazole",
        drug_a_class="Antiplatelet (P2Y12 inhibitor prodrug)",
        drug_b_class="Proton pump inhibitor",
        correct_severity=InteractionSeverity.MODERATE,
        clinical_consequence="Omeprazole inhibits CYP2C19-mediated activation of clopidogrel, potentially reducing antiplatelet effect by 25-40%. FDA warning issued, though clinical significance is debated.",
        mechanism="Omeprazole is a CYP2C19 inhibitor; clopidogrel requires CYP2C19 for conversion to active metabolite. Note: pantoprazole has less CYP2C19 inhibition and is preferred.",
        difficulty=DifficultyTier.HARD,
    ),
    DrugInteractionItem(
        id="ddi_008",
        drug_a="Sacubitril/Valsartan",
        drug_b="Lithium",
        drug_a_class="ARNI (neprilysin inhibitor + ARB)",
        drug_b_class="Mood stabilizer",
        correct_severity=InteractionSeverity.MAJOR,
        clinical_consequence="Increased lithium levels leading to toxicity (tremor, confusion, seizures, renal failure). The neprilysin inhibition component (sacubitril) reduces renal lithium clearance beyond what ARBs alone cause.",
        mechanism="Sacubitril inhibits neprilysin which affects natriuretic peptide metabolism, impacting renal sodium/lithium handling. Valsartan component also reduces lithium clearance via reduced GFR.",
        difficulty=DifficultyTier.HARD,
    ),

    # NEAR-IMPOSSIBLE (Tier 5) — cutting-edge or extremely rare
    DrugInteractionItem(
        id="ddi_009",
        drug_a="Venetoclax",
        drug_b="Posaconazole",
        drug_a_class="BCL-2 inhibitor (oncology)",
        drug_b_class="Triazole antifungal",
        correct_severity=InteractionSeverity.CONTRAINDICATED,
        clinical_consequence="Posaconazole increases venetoclax exposure by approximately 6-8 fold during the dose ramp-up phase, leading to potentially fatal tumor lysis syndrome.",
        mechanism="Posaconazole is a strong CYP3A4 inhibitor; venetoclax is a CYP3A4 substrate with a narrow therapeutic index. During ramp-up, the dose reduction required (75% reduction) makes therapeutic dosing impractical.",
        difficulty=DifficultyTier.NEAR_IMPOSSIBLE,
    ),
    DrugInteractionItem(
        id="ddi_010",
        drug_a="Ivabradine",
        drug_b="Diltiazem",
        drug_a_class="Funny channel (If) inhibitor",
        drug_b_class="Non-dihydropyridine calcium channel blocker",
        correct_severity=InteractionSeverity.CONTRAINDICATED,
        clinical_consequence="Severe bradycardia, heart block, and hemodynamic compromise. Both drugs reduce heart rate through different mechanisms with synergistic effect.",
        mechanism="Additive negative chronotropy: ivabradine slows SA node via If channel inhibition, diltiazem slows AV conduction and SA node via calcium channel blockade. Additionally, diltiazem inhibits CYP3A4, increasing ivabradine levels.",
        difficulty=DifficultyTier.NEAR_IMPOSSIBLE,
    ),
]


# =============================================================================
# Seed Data: Risk Factor Materiality (to be expanded via EDGAR API)
# =============================================================================

RISK_FACTOR_ITEMS: List[RiskFactorItem] = [
    # TRIVIAL — obvious risks that clearly materialized
    RiskFactorItem(
        id="rf_001",
        company_name="Silicon Valley Bank",
        ticker="SIVB",
        sector="Regional Banking",
        fiscal_year=2022,
        risk_factor_text="We are subject to interest rate risk. A rapid increase in interest rates could result in significant unrealized losses on our held-to-maturity securities portfolio, which totaled $91.3 billion as of December 31, 2022. A large proportion of our deposits are uninsured and from concentrated technology and venture capital sectors, which may be subject to rapid withdrawal in stressed conditions.",
        risk_materialized=True,
        actual_outcome="SVB collapsed in March 2023 due to exactly this risk — a bank run triggered by unrealized bond losses and deposit concentration in the tech sector.",
        difficulty=DifficultyTier.TRIVIAL,
    ),

    # EASY — common risk disclosures
    RiskFactorItem(
        id="rf_002",
        company_name="Pfizer Inc.",
        ticker="PFE",
        sector="Pharmaceuticals",
        fiscal_year=2022,
        risk_factor_text="Revenue from our COVID-19 vaccine and antiviral treatment may decline significantly as the pandemic transitions to an endemic phase. Demand for COVID-19 products is inherently uncertain and dependent on government purchasing decisions, variant emergence, and vaccination rates.",
        risk_materialized=True,
        actual_outcome="Pfizer's COVID product revenue dropped from $56.7B in 2022 to approximately $12.5B in 2023, a 78% decline. The company took $5.6B in inventory write-offs.",
        difficulty=DifficultyTier.EASY,
    ),

    # MEDIUM — requires analysis to assess
    RiskFactorItem(
        id="rf_003",
        company_name="Tesla Inc.",
        ticker="TSLA",
        sector="Automotive / Clean Energy",
        fiscal_year=2022,
        risk_factor_text="Increasing competition in the electric vehicle market from both traditional automakers and new entrants could adversely affect our market share, pricing, and margins. We may need to reduce prices to maintain demand, which could negatively impact our profitability.",
        risk_materialized=True,
        actual_outcome="Tesla engaged in aggressive price cuts throughout 2023 (up to 25% on some models globally), automotive gross margin fell from 28.5% to 18.2%. Price war with Chinese EV makers intensified.",
        difficulty=DifficultyTier.MEDIUM,
    ),

    # HARD — risks that did NOT materialize despite seeming likely
    RiskFactorItem(
        id="rf_004",
        company_name="NVIDIA Corporation",
        ticker="NVDA",
        sector="Semiconductors",
        fiscal_year=2022,
        risk_factor_text="U.S. government export controls restricting sales of advanced AI chips to China could materially impact our revenue. China represented approximately 22% of our data center revenue in fiscal year 2023. Additional restrictions or retaliatory measures could further limit our addressable market.",
        risk_materialized=False,
        actual_outcome="Despite China export restrictions, NVIDIA's total revenue nearly tripled in FY2024 ($60.9B vs $27B) as explosive AI/data center demand from Western markets more than compensated. Data center revenue grew 217% YoY.",
        difficulty=DifficultyTier.HARD,
    ),

    # NEAR-IMPOSSIBLE — subtle risk that materialized unexpectedly
    RiskFactorItem(
        id="rf_005",
        company_name="CrowdStrike Holdings",
        ticker="CRWD",
        sector="Cybersecurity",
        fiscal_year=2023,
        risk_factor_text="Our Falcon platform operates at the kernel level of customer operating systems. Errors, vulnerabilities, or defects in our software updates could cause widespread system disruptions for our customers, resulting in significant reputational harm, customer loss, and potential legal liability.",
        risk_materialized=True,
        actual_outcome="In July 2024, a faulty CrowdStrike Falcon sensor update caused approximately 8.5 million Windows devices to crash worldwide, grounding flights, disrupting hospitals, and causing an estimated $5.4B in direct losses to Fortune 500 companies.",
        difficulty=DifficultyTier.NEAR_IMPOSSIBLE,
    ),
]


# =============================================================================
# Task Runner
# =============================================================================

def get_calibration_items(
    domain: Optional[Domain] = None,
    difficulty: Optional[DifficultyTier] = None,
) -> list:
    """Get calibration items filtered by domain and difficulty."""
    if domain == Domain.HEALTHCARE:
        items = DRUG_INTERACTION_ITEMS
    elif domain == Domain.FINANCE:
        items = RISK_FACTOR_ITEMS
    else:
        items = DRUG_INTERACTION_ITEMS + RISK_FACTOR_ITEMS

    if difficulty:
        items = [i for i in items if i.difficulty == difficulty]

    return items


def get_stratified_set(n_per_tier: int = 2) -> list:
    """Get a difficulty-stratified set of items across both domains."""
    result = []
    for tier in DifficultyTier:
        healthcare = [i for i in DRUG_INTERACTION_ITEMS if i.difficulty == tier]
        finance = [i for i in RISK_FACTOR_ITEMS if i.difficulty == tier]
        result.extend(healthcare[:n_per_tier])
        result.extend(finance[:n_per_tier])
    random.shuffle(result)
    return result
