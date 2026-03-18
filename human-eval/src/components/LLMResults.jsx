export default function LLMResults() {
  const ef1 = {
    congruentAccuracy: 0.625,
    incongruentAccuracy: 0.55,
    interferenceEffect: 0.075,
    congruentTrials: 16,
    incongruentTrials: 20,
  };

  const ef2 = {
    meanFlexibility: 0.5125,
    adaptationTurns: 16,
    scenarios: 8,
  };

  const mc1 = {
    accuracy: 0.78,
    ece: 0.2084,
    brier: 0.2063,
    wwa: 0.3609,
    cyberECE: 0.2577,
    financeECE: 0.1345,
    crossDomainGap: 0.1232,
    cyberItems: 30,
    financeItems: 20,
  };

  const mc1Human = {
    accuracy: 0.6667,
    ece: 0.2727,
    brier: 0.2777,
    wwa: 0.0008,
    items: 15,
  };

  const mc2 = {
    totalScore: -188,
    maxScore: 280,
    normalized: -0.6714,
    coverage: 0.8571,
    accuracyAnswered: 0.7083,
    correct: 17,
    wrong: 7,
    abstained: 4,
    tiers: [
      { name: "Answerable", total: 10, answered: 10, correct: 10, wrong: 0, abstained: 0 },
      { name: "Ambiguous", total: 8, answered: 7, correct: 5, wrong: 2, abstained: 1 },
      { name: "Specialist", total: 10, answered: 7, correct: 2, wrong: 5, abstained: 3 },
    ],
  };

  const mc2Human = {
    totalScore: -28,
    coverage: 0.5,
    accuracyAnswered: 0.75,
    correct: 3,
    wrong: 1,
    abstained: 4,
    items: 8,
  };

  return (
    <div className="llm-results">
      <p className="llm-results-model">Model: <strong>Gemini 2.5 Flash</strong> via Kaggle Community Benchmarks</p>

      <div className="results-grid">
        <div className="result-card">
          <h2>EF-1: Diagnostic Decoy</h2>
          <p className="card-subtitle">Stroop Test for LLMs — Inhibitory Control</p>
          <div className="metric-row">
            <span className="metric-label">Congruent Accuracy</span>
            <span className="metric-value">{(ef1.congruentAccuracy * 100).toFixed(1)}%</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Incongruent Accuracy</span>
            <span className="metric-value">{(ef1.incongruentAccuracy * 100).toFixed(1)}%</span>
          </div>
          <div className="metric-row highlight">
            <span className="metric-label">Interference Effect</span>
            <span className="metric-value">{ef1.interferenceEffect.toFixed(4)}</span>
          </div>
          <p className="metric-note">Positive IE = model performs worse when surface features conflict with correct answer. {ef1.congruentTrials + ef1.incongruentTrials} trials ({ef1.incongruentTrials} incongruent, {ef1.congruentTrials} congruent).</p>
        </div>

        <div className="result-card">
          <h2>EF-2: Mid-Course Correction</h2>
          <p className="card-subtitle">WCST for LLMs — Cognitive Flexibility</p>
          <div className="metric-row highlight">
            <span className="metric-label">Mean Flexibility Score</span>
            <span className="metric-value">{ef2.meanFlexibility.toFixed(4)}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Adaptation Turns</span>
            <span className="metric-value">{ef2.adaptationTurns}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Scenarios</span>
            <span className="metric-value">{ef2.scenarios}</span>
          </div>
          <p className="metric-note">Score of 0.51 = model adapts to ~half of required changes. Measures perseverative errors and gratuitous changes independently.</p>
        </div>

        {/* MC-1 with human comparison */}
        <div className="result-card">
          <h2>MC-1: Calibrated Confidence</h2>
          <p className="card-subtitle">Wagering Paradigm — Metacognitive Monitoring</p>

          <table className="comparison-table">
            <thead>
              <tr><th>Metric</th><th>Gemini 2.5 Flash</th><th>Human Baseline</th></tr>
            </thead>
            <tbody>
              <tr>
                <td>Accuracy</td>
                <td>{(mc1.accuracy * 100).toFixed(0)}%</td>
                <td>{(mc1Human.accuracy * 100).toFixed(1)}%</td>
              </tr>
              <tr className="highlight-row">
                <td>ECE</td>
                <td>{mc1.ece.toFixed(4)}</td>
                <td>{mc1Human.ece.toFixed(4)}</td>
              </tr>
              <tr>
                <td>Brier Score</td>
                <td>{mc1.brier.toFixed(4)}</td>
                <td>{mc1Human.brier.toFixed(4)}</td>
              </tr>
              <tr className="highlight-row">
                <td>Wager-Weighted Accuracy</td>
                <td>{mc1.wwa.toFixed(4)}</td>
                <td>{mc1Human.wwa.toFixed(4)}</td>
              </tr>
            </tbody>
          </table>

          <div className="metric-row">
            <span className="metric-label">Cyber ECE / Finance ECE</span>
            <span className="metric-value">{mc1.cyberECE.toFixed(2)} / {mc1.financeECE.toFixed(2)}</span>
          </div>
          <p className="metric-note">
            Both LLM and human show overconfidence (ECE &gt; 0.20). The human's near-zero WWA was driven by
            high-confidence wrong answers on severity classification (answered "high" instead of "critical" for 3 items) —
            illustrating how the wagering paradigm brutally penalizes miscalibration regardless of whether the respondent is
            human or machine.
          </p>
        </div>

        {/* MC-2 with human comparison */}
        <div className="result-card">
          <h2>MC-2: Selective Abstention</h2>
          <p className="card-subtitle">Asymmetric Payoffs — Metacognitive Control</p>

          <table className="comparison-table">
            <thead>
              <tr><th>Metric</th><th>Gemini 2.5 Flash</th><th>Human Baseline</th></tr>
            </thead>
            <tbody>
              <tr className="highlight-row">
                <td>Total Score</td>
                <td className="bad">{mc2.totalScore} / {mc2.maxScore}</td>
                <td>{mc2Human.totalScore} / {mc2.maxScore}</td>
              </tr>
              <tr>
                <td>Coverage</td>
                <td>{(mc2.coverage * 100).toFixed(1)}%</td>
                <td>{(mc2Human.coverage * 100).toFixed(0)}%</td>
              </tr>
              <tr>
                <td>Accuracy (answered)</td>
                <td>{(mc2.accuracyAnswered * 100).toFixed(1)}%</td>
                <td>{(mc2Human.accuracyAnswered * 100).toFixed(0)}%</td>
              </tr>
              <tr>
                <td>Correct / Wrong / Abstained</td>
                <td>{mc2.correct} / {mc2.wrong} / {mc2.abstained}</td>
                <td>{mc2Human.correct} / {mc2Human.wrong} / {mc2Human.abstained}</td>
              </tr>
            </tbody>
          </table>

          <h3 className="section-subhead">LLM Per-Tier Breakdown</h3>
          <table className="tier-table">
            <thead>
              <tr><th>Tier</th><th>Correct</th><th>Wrong</th><th>Abstained</th></tr>
            </thead>
            <tbody>
              {mc2.tiers.map((t) => (
                <tr key={t.name}>
                  <td>{t.name} ({t.total})</td>
                  <td className="good">{t.correct}</td>
                  <td className="bad">{t.wrong}</td>
                  <td>{t.abstained}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="metric-note">
            The human scored -28 vs. the LLM's -188 — a 160-point gap driven entirely by abstention strategy.
            The human abstained on all 3 specialist items and the binary-outcome biotech question (4/8 abstained),
            while the LLM attempted 7/10 specialist questions at 0.90+ stated confidence but scored only 28.6% (2/7).
            Specialist errors alone cost the LLM -250 points. This demonstrates the core thesis: metacognitive control
            (knowing when NOT to answer) is a separable capability from domain knowledge.
          </p>
        </div>
      </div>

      <div className="key-findings">
        <h2>Key Findings</h2>
        <ul>
          <li><strong>Stroop interference transfers to LLMs</strong> — 7.5% accuracy drop when surface features conflict with correct answer (EF-1)</li>
          <li><strong>Mid-task flexibility is a bottleneck</strong> — model adapts to only ~50% of required changes (EF-2)</li>
          <li><strong>Systematic overconfidence</strong> — model states 0.95+ confidence on items where it achieves 78% accuracy (MC-1)</li>
          <li><strong>Catastrophic metacognitive control failure</strong> — specialist errors alone cost -250 points, overwhelming correct answers on easy items (MC-2)</li>
          <li><strong>Human metacognitive control is superior</strong> — human scored -28 vs LLM's -188 on MC-2, despite lower domain accuracy, by correctly abstaining on specialist items</li>
          <li><strong>Domain knowledge is not the bottleneck</strong> — 10/10 on answerable items; failures are purely in executive function and metacognition</li>
        </ul>
      </div>

      <div className="limitations-section">
        <h2>Limitations & Scoring Caveats</h2>
        <ul>
          <li>
            <strong>Keyword-based scoring underestimates free-text accuracy.</strong> EF-1 and MC-2 use keyword overlap
            to judge correctness. A human who writes "this looks like a value trap, avoid" scores as incorrect if the
            keyword list expects "fraud" or "manufactured." The human EF-1 results (33% incongruent accuracy) are
            artificially low — manual review shows 3 of the 4 "incorrect" incongruent responses contained correct
            reasoning but used different terminology. This is a known limitation of automated scoring for open-ended responses.
          </li>
          <li>
            <strong>Severity granularity creates false negatives.</strong> In MC-1, the human answered "high" instead of
            "critical" for 3 cybersecurity items (default creds on router, Log4Shell, SSRF to metadata). These are
            defensible judgments (reasonable experts might disagree on high vs. critical), but binary keyword matching
            treats them as fully wrong, destroying the WWA score via the -2x penalty on high-confidence wrong answers.
          </li>
          <li>
            <strong>Small human sample size.</strong> The human baseline is a single evaluator (n=1) completing a reduced
            item set (9 EF-1, 15 MC-1, 8 MC-2 vs. 36/50/28 in the full LLM benchmark). This provides directional
            signal, not a statistically robust human baseline. A proper baseline would require 30+ participants.
          </li>
          <li>
            <strong>LLM structured output vs. human free text.</strong> LLMs respond via constrained JSON schemas,
            producing exact keyword matches by design. Humans produce natural language that is semantically correct
            but lexically different. This asymmetry systematically favors LLM scores on keyword-based metrics,
            making direct comparison on EF-1 misleading. MC-1's multiple-choice format and MC-2's abstain/answer
            decision are more directly comparable.
          </li>
        </ul>
      </div>
    </div>
  );
}
