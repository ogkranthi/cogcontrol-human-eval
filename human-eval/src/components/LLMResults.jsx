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

        <div className="result-card">
          <h2>MC-1: Calibrated Confidence</h2>
          <p className="card-subtitle">Wagering Paradigm — Metacognitive Monitoring</p>
          <div className="metric-row">
            <span className="metric-label">Accuracy</span>
            <span className="metric-value">{(mc1.accuracy * 100).toFixed(0)}%</span>
          </div>
          <div className="metric-row highlight">
            <span className="metric-label">ECE</span>
            <span className="metric-value">{mc1.ece.toFixed(4)}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Brier Score</span>
            <span className="metric-value">{mc1.brier.toFixed(4)}</span>
          </div>
          <div className="metric-row highlight">
            <span className="metric-label">Wager-Weighted Accuracy</span>
            <span className="metric-value">{mc1.wwa.toFixed(4)}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Cyber ECE / Finance ECE</span>
            <span className="metric-value">{mc1.cyberECE.toFixed(2)} / {mc1.financeECE.toFixed(2)}</span>
          </div>
          <p className="metric-note">Model wagers 90-100 on nearly every item (including wrong answers). ECE of 0.21 reveals systematic overconfidence. {mc1.cyberItems + mc1.financeItems} items across 5 difficulty tiers.</p>
        </div>

        <div className="result-card">
          <h2>MC-2: Selective Abstention</h2>
          <p className="card-subtitle">Asymmetric Payoffs — Metacognitive Control</p>
          <div className="metric-row highlight">
            <span className="metric-label">Total Score</span>
            <span className="metric-value">{mc2.totalScore} / {mc2.maxScore}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Coverage</span>
            <span className="metric-value">{(mc2.coverage * 100).toFixed(1)}%</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Accuracy (answered)</span>
            <span className="metric-value">{(mc2.accuracyAnswered * 100).toFixed(1)}%</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Correct / Wrong / Abstained</span>
            <span className="metric-value">{mc2.correct} / {mc2.wrong} / {mc2.abstained}</span>
          </div>

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
          <p className="metric-note">Model attempts 7/10 specialist questions at 0.90+ confidence but scores only 28.6% (2/7). Rational strategy: abstain when P(correct) &lt; 16.7%.</p>
        </div>
      </div>

      <div className="key-findings">
        <h2>Key Findings</h2>
        <ul>
          <li><strong>Stroop interference transfers to LLMs</strong> — 7.5% accuracy drop when surface features conflict with correct answer (EF-1)</li>
          <li><strong>Mid-task flexibility is a bottleneck</strong> — model adapts to only ~50% of required changes (EF-2)</li>
          <li><strong>Systematic overconfidence</strong> — model states 0.95+ confidence on items where it achieves 78% accuracy (MC-1)</li>
          <li><strong>Catastrophic metacognitive control failure</strong> — specialist errors alone cost -250 points, overwhelming correct answers on easy items (MC-2)</li>
          <li><strong>Domain knowledge is not the bottleneck</strong> — 10/10 on answerable items; failures are purely in executive function and metacognition</li>
        </ul>
      </div>
    </div>
  );
}
