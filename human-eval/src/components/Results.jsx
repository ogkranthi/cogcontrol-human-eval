import { computeECE, computeBrier, computeWWA, computeAbstentionScore, computeInterferenceEffect, formatDuration } from "../utils/scoring";
import { TASKS } from "../data/tasks";

export default function Results({ allResults }) {
  const ef1Results = allResults.ef1 || [];
  const mc1Results = allResults.mc1 || [];
  const mc2Results = allResults.mc2 || [];

  // EF-1 scoring
  const ef1Scored = ef1Results.map((r) => {
    const item = TASKS.ef1.items.find((i) => i.id === r.itemId);
    const assessLower = (r.assessment || "").toLowerCase();
    const kws = item.correctKeywords || [];
    const hits = kws.filter((kw) => assessLower.includes(kw.toLowerCase())).length;
    const isCorrect = hits >= Math.max(1, Math.floor(kws.length / 3));
    return { ...r, isCorrect };
  });
  const ie = computeInterferenceEffect(ef1Scored);

  // MC-1 scoring
  const mc1Scored = mc1Results.map((r) => {
    const item = TASKS.mc1.items.find((i) => i.id === r.itemId);
    const isCorrect = r.answer?.toLowerCase().replace(/ /g, "_") === item.correctAnswer.toLowerCase();
    return { ...r, isCorrect };
  });
  const mc1Confs = mc1Scored.map((r) => r.confidence);
  const mc1Accs = mc1Scored.map((r) => r.isCorrect);
  const mc1Wagers = mc1Scored.map((r) => r.wager);
  const ece = computeECE(mc1Confs, mc1Accs);
  const brier = computeBrier(mc1Confs, mc1Accs);
  const wwa = computeWWA(mc1Accs, mc1Wagers);
  const mc1Accuracy = mc1Accs.length > 0 ? mc1Accs.filter(Boolean).length / mc1Accs.length : 0;

  // MC-2 scoring
  const mc2Scored = mc2Results.map((r) => {
    const item = TASKS.mc2.items.find((i) => i.id === r.itemId);
    if (r.decision === "abstain") return { ...r, isCorrect: null };
    const ansLower = (r.answer || "").toLowerCase();
    const hits = (item.answerKeywords || []).filter((kw) => ansLower.includes(kw.toLowerCase())).length;
    return { ...r, isCorrect: hits >= 1 };
  });
  const absScore = computeAbstentionScore(mc2Scored);

  const totalTime = [...ef1Results, ...mc1Results, ...mc2Results].reduce((sum, r, i, arr) => {
    if (i === 0) return 0;
    return sum + (r.timestamp - arr[i - 1].timestamp);
  }, 0);

  const exportData = {
    participant: "human_baseline",
    timestamp: new Date().toISOString(),
    ef1: { results: ef1Scored, metrics: ie },
    mc1: { results: mc1Scored, metrics: { ece, brier, wwa, accuracy: mc1Accuracy } },
    mc2: { results: mc2Scored, metrics: absScore },
  };

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `human_baseline_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="results-page">
      <h1>Your Results</h1>
      <p className="results-subtitle">Human Baseline for CogControl-Stakes</p>

      <div className="results-grid">
        <div className="result-card">
          <h2>EF-1: Diagnostic Decoy</h2>
          <div className="metric-row">
            <span className="metric-label">Congruent Accuracy</span>
            <span className="metric-value">{(ie.congruentAccuracy * 100).toFixed(0)}%</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Incongruent Accuracy</span>
            <span className="metric-value">{(ie.incongruentAccuracy * 100).toFixed(0)}%</span>
          </div>
          <div className="metric-row highlight">
            <span className="metric-label">Interference Effect</span>
            <span className="metric-value">{ie.interferenceEffect.toFixed(4)}</span>
          </div>
          <p className="metric-note">Lower IE = better inhibitory control</p>
        </div>

        <div className="result-card">
          <h2>MC-1: Calibrated Confidence</h2>
          <div className="metric-row">
            <span className="metric-label">Accuracy</span>
            <span className="metric-value">{(mc1Accuracy * 100).toFixed(0)}%</span>
          </div>
          <div className="metric-row highlight">
            <span className="metric-label">ECE</span>
            <span className="metric-value">{ece.toFixed(4)}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Brier Score</span>
            <span className="metric-value">{brier.toFixed(4)}</span>
          </div>
          <div className="metric-row highlight">
            <span className="metric-label">Wager-Weighted Accuracy</span>
            <span className="metric-value">{wwa.toFixed(4)}</span>
          </div>
          <p className="metric-note">Lower ECE = better calibrated. Higher WWA = better behavioral metacognition.</p>
        </div>

        <div className="result-card">
          <h2>MC-2: Selective Abstention</h2>
          <div className="metric-row">
            <span className="metric-label">Total Score</span>
            <span className="metric-value">{absScore.totalScore}</span>
          </div>
          <div className="metric-row highlight">
            <span className="metric-label">Normalized Score</span>
            <span className="metric-value">{absScore.normalized.toFixed(4)}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Coverage</span>
            <span className="metric-value">{(absScore.coverage * 100).toFixed(0)}%</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Accuracy (answered)</span>
            <span className="metric-value">{(absScore.accuracyWhenAnswered * 100).toFixed(0)}%</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Breakdown</span>
            <span className="metric-value">{absScore.correct}C / {absScore.incorrect}W / {absScore.abstained}A</span>
          </div>
        </div>
      </div>

      <div className="export-section">
        <button onClick={handleExport} className="export-btn">
          Export Results as JSON
        </button>
        <p className="export-note">Download your human baseline data for comparison with LLM scores</p>
      </div>
    </div>
  );
}
