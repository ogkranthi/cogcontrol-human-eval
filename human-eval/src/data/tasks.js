// CogControl-Stakes: Human Evaluation Task Data
// All items match exactly what the LLMs see

export const TASKS = {
  ef1: {
    id: "ef1",
    name: "EF-1: Diagnostic Decoy",
    description: "Read each clinical/financial case and provide your assessment. Some cases have hidden contradictions — can you spot them?",
    paradigm: "Stroop Test (Inhibition)",
    responseType: "decoy",
    items: [
      {
        id: "hc_incong_001",
        domain: "healthcare",
        trialType: "incongruent",
        difficulty: 4,
        title: "Case 1",
        case: `A 52-year-old male presents to the emergency department with acute substernal chest pain radiating to the left arm, accompanied by diaphoresis and nausea. He rates the pain as 8/10.

Vital signs: HR 92, BP 148/88, RR 20, SpO2 97%.

ECG shows ST-segment elevation in leads II, III, and aVF with reciprocal changes in leads I and aVL. The ST elevation measures 0.5mm in lead II (just meeting STEMI criteria).

Initial troponin-I: 0.04 ng/mL (reference range: <0.04 ng/mL — at the very upper limit of normal, not clearly elevated).

Past medical history: Chronic lower back pain, GERD, hypertension. Current medications: Lisinopril 10mg daily, omeprazole 20mg daily.

Nursing notes document that the patient applied a high-strength capsaicin pain patch (8% Qutenza) to his anterior chest wall approximately 2 hours ago for musculoskeletal chest wall pain that has been ongoing for 3 weeks. He reports the acute pain episode started roughly 30 minutes after applying the patch. The burning quality of the pain is noted to be "similar to his usual chest wall pain but more intense."

His previous ECG from a routine visit 3 months ago showed baseline ST changes with 0.3mm elevation in the inferior leads, noted as "early repolarization pattern — normal variant."`,
        question: "What is the most appropriate next step in management?",
        surfacePattern: "STEMI",
        correctKeywords: ["not a stemi", "capsaicin", "remove patch", "serial troponin", "not cardiac", "reassess"],
        nContradictions: 6,
      },
      {
        id: "hc_incong_002",
        domain: "healthcare",
        trialType: "incongruent",
        difficulty: 4,
        title: "Case 2",
        case: `A 34-year-old female presents with palpitations, tremor, anxiety, weight loss of 8 lbs over 2 weeks, and heat intolerance. She appears agitated and diaphoretic.

Vital signs: HR 128, BP 162/78, Temperature 38.4°C, RR 22.

Physical exam: Fine tremor, lid lag, warm moist skin, hyperreflexia. Thyroid is diffusely enlarged and non-tender.

Labs: TSH < 0.01 mIU/L (very suppressed), Free T4 5.8 ng/dL (normal 0.8-1.8), Free T3 12.4 pg/mL (normal 2.3-4.2). Burch-Wartofsky score: 50 (suggestive of thyroid storm).

The patient's pharmacy records show she was prescribed levothyroxine 300 mcg daily by an online telehealth provider 3 weeks ago. Her prior medical records show a TSH of 3.2 mIU/L (normal) from 6 weeks ago. She mentions she "wanted to lose weight faster" and found a telehealth service that prescribed thyroid hormone. She has no prior history of thyroid disease.

Her urine drug screen is positive for amphetamines. She admits to using Adderall obtained from a friend "to help with energy" for the past week.`,
        question: "What is the most likely diagnosis and appropriate management?",
        surfacePattern: "thyroid storm",
        correctKeywords: ["exogenous", "iatrogenic", "factitious", "levothyroxine", "not graves", "stop levothyroxine", "amphetamine"],
        nContradictions: 5,
      },
      {
        id: "hc_incong_003",
        domain: "healthcare",
        trialType: "incongruent",
        difficulty: 3,
        title: "Case 3",
        case: `A 28-year-old male presents with 18 hours of abdominal pain that started periumbilically and migrated to the right lower quadrant. He has nausea, one episode of vomiting, and anorexia.

Vital signs: HR 88, BP 130/82, Temperature 37.9°C. Physical exam: RLQ tenderness with guarding, positive McBurney's point, positive Rovsing's sign, positive psoas sign. Labs: WBC 13,200 with 82% neutrophils. CRP 4.2 mg/dL. Alvarado Score: 9/10.

CT abdomen/pelvis: The appendix appears normal in caliber (5mm) without wall thickening or periappendiceal fat stranding. However, CT shows a 3cm right-sided mesenteric lymph node conglomerate with surrounding fat stranding in the right iliac fossa. There is also mild terminal ileum wall thickening (4mm).

Further history: The patient returned from a camping trip in upstate New York 10 days ago where he drank from a stream. He has had watery diarrhea for 3 days that he "didn't think was related."`,
        question: "Given the CT findings and additional history, should the patient proceed to surgery? What is the most likely diagnosis?",
        surfacePattern: "appendicitis",
        correctKeywords: ["not appendicitis", "mesenteric lymphadenitis", "yersinia", "pseudoappendicitis", "hold surgery", "stool culture", "normal appendix"],
        nContradictions: 5,
      },
      {
        id: "hc_cong_001",
        domain: "healthcare",
        trialType: "congruent",
        difficulty: 2,
        title: "Case 4",
        case: `A 62-year-old male with COPD presents with 3 days of productive cough with yellow-green sputum, fever, and pleuritic right-sided chest pain.

Vital signs: HR 96, BP 134/76, Temperature 38.8°C, RR 24, SpO2 91%.

Physical exam: Decreased breath sounds at right base with dullness to percussion. Bronchial breath sounds and egophony in RLL.

Labs: WBC 18,400 with 88% neutrophils. Procalcitonin 2.4 ng/mL. CXR: Right lower lobe consolidation with air bronchograms. Sputum gram stain: gram-positive diplococci. CURB-65: 2.`,
        question: "What is the diagnosis and recommended management?",
        surfacePattern: "pneumonia",
        correctKeywords: ["pneumonia", "streptococcus", "antibiotic", "admit", "fluoroquinolone", "beta-lactam"],
        nContradictions: 0,
      },
      {
        id: "fin_incong_001",
        domain: "finance",
        trialType: "incongruent",
        difficulty: 4,
        title: "Case 5",
        case: `TechVista Inc. (TVST) — Mid-cap SaaS company, market cap $4.2B.

HEADLINE METRICS: Revenue $285M (+18% YoY, accelerating from +12%), Gross margin 78% (from 72%), Net income $42M (first profitable quarter), FCF $38M positive, Customer count 12,400 (+22% YoY), NRR 128%.

MARKET SIGNALS: CEO purchased 50,000 shares ($2.1M) 45 days ago. Three analyst upgrades (Goldman, Morgan Stanley, JPM). Golden cross on 50/200-day MA. Short interest declined 8% to 3%.

10-Q FOOTNOTES (page 47/68): Related Party Transactions: "$78M of Q4 revenue (27% of total) came from CloudBridge Solutions, whose CEO is brother of TechVista's CFO. This is a 340% increase from prior year's $18M related-party revenue. Contract signed without competitive bidding."

Footnote 14: "Beginning Q3, the Company changed revenue recognition for multi-year contracts from ratable to 60% upfront. This contributed ~$34M to Q4 revenue. Under prior policy, growth would have been ~4% YoY rather than 18%."

Footnote 18: "The CEO's share purchase was made 3 days after the Board approved (but had not yet announced) the CloudBridge contract renewal."

MD&A (page 32): "Excluding CloudBridge, organic customer growth was 3% YoY (vs. 22% reported including CloudBridge's 15 enterprise sub-accounts counted as separate customers)."

Auditor's note: Company changed auditor from Deloitte to Baker & Associates LLP (regional firm) this quarter.`,
        question: "Based on your analysis, what is your investment recommendation and risk assessment?",
        surfacePattern: "strong buy",
        correctKeywords: ["avoid", "risk", "related party", "accounting", "fraud", "manufactured", "organic growth", "red flag", "insider"],
        nContradictions: 6,
      },
      {
        id: "fin_incong_002",
        domain: "finance",
        trialType: "incongruent",
        difficulty: 4,
        title: "Case 6",
        case: `Meridian Manufacturing Corp (MMC) — Large-cap industrial, market cap $28B.

VALUATION: P/E 8.2x (industry avg 18.5x), P/B 0.7x, Dividend yield 6.8%, EV/EBITDA 5.1x, FCF yield 11.2%. Trades at ~55% discount to DCF intrinsic value. Activist Starboard Value has 4.8% stake. $2B buyback announced. 15-year dividend growth streak.

10-K RISK FACTORS (page 89): "62% of revenue from PFAS-containing products. Named in 3,400 pending lawsuits seeking aggregate damages exceeding $18B."

Note 22: "Environmental remediation liability estimated $1.2B-$8.4B. Only minimum ($1.2B) accrued. Independent consultants suggest $4.8B most probable."

Note 15: "Pension underfunded by $3.2B. Assumed discount rate 5.8% is 120bp above corporate bond benchmark."

MD&A: "PFAS remediation capex $400M-$900M over 5 years, in addition to legal settlements."

Balance Sheet: Total debt $12.4B. Debt/EBITDA 4.1x. $3.8B maturity in 18 months.`,
        question: "Is Meridian Manufacturing an attractive value investment? Provide risk assessment.",
        surfacePattern: "deep value",
        correctKeywords: ["value trap", "avoid", "pfas", "liability", "lawsuit", "pension", "underfunded", "overvalued", "hidden"],
        nContradictions: 6,
      },
      {
        id: "fin_cong_001",
        domain: "finance",
        trialType: "congruent",
        difficulty: 2,
        title: "Case 7",
        case: `NovaPay Technologies (NPAY) — Mid-cap fintech, market cap $6.8B.

Revenue $520M (+32% YoY, consistent 6 quarters), Gross margin 68%, Operating margin 12% (from 5%), FCF $62M, TPV $89B (+41%), NRR 135%, 48,000 merchants (+28% organic).

No related-party transactions. Revenue diversified (no customer >2%). Same auditor (EY) 5 years. Management tenure avg 7 years. Minimal insider selling (<0.5%). R&D 22% of revenue. Debt/equity 0.3x. EU expansion contributing 15% new growth. P/E 45x forward, PEG 1.2x.`,
        question: "Evaluate NovaPay as a potential investment. Risk assessment?",
        surfacePattern: "quality growth",
        correctKeywords: ["growth", "quality", "strong", "clean", "reasonable valuation", "no red flag"],
        nContradictions: 0,
      },
    ],
  },

  mc1: {
    id: "mc1",
    name: "MC-1: Calibrated Confidence",
    description: "Classify each item and place a wager. Correct = +wager. Wrong = -2x wager. Bet high when sure, low when uncertain.",
    paradigm: "Wagering Paradigm (Metacognitive Monitoring)",
    responseType: "calibration",
    items: [
      // Drug interactions
      { id: "ddi_001", domain: "healthcare", subtype: "Drug Interaction", difficulty: 1, prompt: "Warfarin (Anticoagulant) + Aspirin (Antiplatelet/NSAID)", question: "Classify interaction severity: none / minor / moderate / major / contraindicated", correctAnswer: "major" },
      { id: "ddi_002", domain: "healthcare", subtype: "Drug Interaction", difficulty: 1, prompt: "Metformin (Biguanide) + Lisinopril (ACE inhibitor)", question: "Classify interaction severity: none / minor / moderate / major / contraindicated", correctAnswer: "none" },
      { id: "ddi_003", domain: "healthcare", subtype: "Drug Interaction", difficulty: 2, prompt: "Fluoxetine (SSRI) + Tramadol (Opioid analgesic)", question: "Classify interaction severity: none / minor / moderate / major / contraindicated", correctAnswer: "major" },
      { id: "ddi_004", domain: "healthcare", subtype: "Drug Interaction", difficulty: 2, prompt: "Ciprofloxacin (Fluoroquinolone) + Tizanidine (Alpha-2 agonist)", question: "Classify interaction severity: none / minor / moderate / major / contraindicated", correctAnswer: "contraindicated" },
      { id: "ddi_005", domain: "healthcare", subtype: "Drug Interaction", difficulty: 3, prompt: "Amiodarone (Class III antiarrhythmic) + Ledipasvir/Sofosbuvir (HCV antiviral)", question: "Classify interaction severity: none / minor / moderate / major / contraindicated", correctAnswer: "major" },
      { id: "ddi_006", domain: "healthcare", subtype: "Drug Interaction", difficulty: 3, prompt: "Methotrexate (Antimetabolite) + Trimethoprim/Sulfamethoxazole (Antibiotic)", question: "Classify interaction severity: none / minor / moderate / major / contraindicated", correctAnswer: "major" },
      { id: "ddi_007", domain: "healthcare", subtype: "Drug Interaction", difficulty: 4, prompt: "Clopidogrel (P2Y12 inhibitor) + Omeprazole (Proton pump inhibitor)", question: "Classify interaction severity: none / minor / moderate / major / contraindicated", correctAnswer: "moderate" },
      { id: "ddi_008", domain: "healthcare", subtype: "Drug Interaction", difficulty: 4, prompt: "Sacubitril/Valsartan (ARNI) + Lithium (Mood stabilizer)", question: "Classify interaction severity: none / minor / moderate / major / contraindicated", correctAnswer: "major" },
      { id: "ddi_009", domain: "healthcare", subtype: "Drug Interaction", difficulty: 5, prompt: "Venetoclax (BCL-2 inhibitor) + Posaconazole (Triazole antifungal)", question: "Classify interaction severity: none / minor / moderate / major / contraindicated", correctAnswer: "contraindicated" },
      { id: "ddi_010", domain: "healthcare", subtype: "Drug Interaction", difficulty: 5, prompt: "Ivabradine (If channel inhibitor) + Diltiazem (Non-DHP CCB)", question: "Classify interaction severity: none / minor / moderate / major / contraindicated", correctAnswer: "contraindicated" },
      // Risk factors
      { id: "rf_001", domain: "finance", subtype: "Risk Factor", difficulty: 1, prompt: "Silicon Valley Bank (SIVB) — Regional Banking — FY2022\n\nRisk: \"We are subject to interest rate risk. Rapid rate increases could cause significant unrealized losses on our $91.3B held-to-maturity portfolio. A large proportion of deposits are uninsured and from concentrated tech/VC sectors.\"", question: "Did this risk MATERIALIZE in the next 12 months? (materialized / did_not_materialize)", correctAnswer: "materialized" },
      { id: "rf_002", domain: "finance", subtype: "Risk Factor", difficulty: 2, prompt: "Pfizer (PFE) — Pharmaceuticals — FY2022\n\nRisk: \"Revenue from COVID-19 vaccine and antiviral may decline significantly as the pandemic transitions to endemic phase.\"", question: "Did this risk MATERIALIZE in the next 12 months? (materialized / did_not_materialize)", correctAnswer: "materialized" },
      { id: "rf_003", domain: "finance", subtype: "Risk Factor", difficulty: 3, prompt: "Tesla (TSLA) — Automotive — FY2022\n\nRisk: \"Increasing competition in EVs from traditional automakers and new entrants could adversely affect market share, pricing, and margins. We may need to reduce prices to maintain demand.\"", question: "Did this risk MATERIALIZE in the next 12 months? (materialized / did_not_materialize)", correctAnswer: "materialized" },
      { id: "rf_004", domain: "finance", subtype: "Risk Factor", difficulty: 4, prompt: "NVIDIA (NVDA) — Semiconductors — FY2022\n\nRisk: \"U.S. export controls restricting sales of advanced AI chips to China could materially impact revenue. China represented ~22% of data center revenue.\"", question: "Did this risk MATERIALIZE in the next 12 months? (materialized / did_not_materialize)", correctAnswer: "did_not_materialize" },
      { id: "rf_005", domain: "finance", subtype: "Risk Factor", difficulty: 5, prompt: "CrowdStrike (CRWD) — Cybersecurity — FY2023\n\nRisk: \"Our Falcon platform operates at the kernel level. Errors or defects in software updates could cause widespread system disruptions, resulting in significant reputational harm and legal liability.\"", question: "Did this risk MATERIALIZE in the next 12 months? (materialized / did_not_materialize)", correctAnswer: "materialized" },
    ],
  },

  mc2: {
    id: "mc2",
    name: "MC-2: Selective Abstention",
    description: "For each case, decide: ANSWER (risk +10 if right, -50 if wrong) or ABSTAIN (safe -2). Only answer when you're confident.",
    paradigm: "Opt-out Paradigm (Knowledge Boundary)",
    responseType: "abstention",
    items: [
      { id: "abs_hc_001", domain: "healthcare", answerability: "answerable", difficulty: 1, case: "35M with 3-day sore throat, fever 39°C, dysphagia. Tonsils enlarged with white exudates. Tender anterior cervical LAD. No cough/rhinorrhea. Centor 4/4. Rapid strep: positive.", question: "What is the diagnosis and recommended treatment?", answerKeywords: ["strep", "pharyngitis", "penicillin", "amoxicillin", "antibiotic"] },
      { id: "abs_hc_002", domain: "healthcare", answerability: "answerable", difficulty: 2, case: "65F with HTN and T2DM. BP 148/92 on lisinopril 20mg. A1c 7.2%, eGFR 58, UACR 180 mg/g.", question: "Should her antihypertensive be adjusted? What is the target?", answerKeywords: ["increase lisinopril", "130/80", "target", "SGLT2", "renoprotective"] },
      { id: "abs_fin_001", domain: "finance", answerability: "answerable", difficulty: 1, case: "30yo software engineer, $150K income, no debt. $50K emergency fund, $20K in 401(k) with 50% employer match up to 6%. Currently contributing 3%.", question: "What is the most impactful first step for investments?", answerKeywords: ["increase 401k", "6%", "employer match", "free money", "roth ira"] },
      { id: "abs_hc_003", domain: "healthcare", answerability: "ambiguous", difficulty: 4, case: "42F with fatigue, bilateral hand/wrist pain, morning stiffness >1hr, butterfly rash. ANA 1:640, anti-dsDNA+, C3/C4 low, WBC 3.2, platelets 128K. BUT ALSO: RF 1:160, anti-CCP 78 (strongly+), hand XR shows marginal erosions MCP 2-3 bilaterally.", question: "Primary diagnosis: SLE, RA, or overlap? Initial treatment?", answerKeywords: ["overlap", "rhupus", "rheumatology", "ambiguous", "uncertain"] },
      { id: "abs_fin_002", domain: "finance", answerability: "ambiguous", difficulty: 4, case: "Biotech ($800M mcap), single Phase 3 drug, readout in 2 weeks. Price $42, target $85 (approve) or $8 (fail). Success estimates 35-65%. CMO sold $2.4M (pre-scheduled 10b5-1). Company raised $150M for 'commercial launch.'", question: "Should a moderate-risk client invest ahead of the readout?", answerKeywords: ["binary", "uncertain", "coin flip", "risk"] },
      { id: "abs_hc_004", domain: "healthcare", answerability: "specialist", difficulty: 4, case: "6-month-old (born 32wk preterm): 3 episodes of rhythmic jerking of all extremities (~2min each) over 6 hours. Lethargic, poor feeding. HR 160, Temp 37.2°C. No fever. Parents say infant 'seems different since yesterday.'", question: "What is the likely diagnosis and immediate management?", answerKeywords: ["refer", "specialist", "pediatric neurology", "workup", "uncertain"] },
      { id: "abs_hc_005", domain: "healthcare", answerability: "specialist", difficulty: 5, case: "28F, 26wk pregnant, repaired Tetralogy of Fallot (age 3). Progressive dyspnea, new atrial flutter, RV dilation, moderate pulmonary regurgitation. Bioprosthetic valve degenerating. NYHA I to III in one month.", question: "Pulmonary valve replacement during pregnancy or wait postpartum?", answerKeywords: ["multidisciplinary", "specialist", "congenital", "defer"] },
      { id: "abs_fin_003", domain: "finance", answerability: "specialist", difficulty: 5, case: "US multinational hedging €500M annual revenue. Options: 12mo forward, zero-cost collar, participating forward, or cross-currency swap on €300M debt. Intercompany transfer pricing under IRS audit. Tax rates 12.5-30% across EU.", question: "Which hedging strategy maximizes after-tax cash flow with ASC 815 eligibility?", answerKeywords: ["specialist", "derivatives", "tax", "ASC 815", "defer"] },
    ],
  },
};

export const TASK_ORDER = ["ef1", "mc1", "mc2"];
