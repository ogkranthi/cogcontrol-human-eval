// CogControl-Stakes: Scoring utilities (mirrors Python metrics.py)

export function computeECE(confidences, accuracies, nBins = 10) {
  const n = confidences.length;
  if (n === 0) return 0;
  let ece = 0;
  for (let i = 0; i < nBins; i++) {
    const lo = i / nBins;
    const hi = (i + 1) / nBins;
    const mask = confidences.map((c, j) => c > lo && c <= hi);
    const count = mask.filter(Boolean).length;
    if (count === 0) continue;
    const binConf = mask.reduce((s, m, j) => s + (m ? confidences[j] : 0), 0) / count;
    const binAcc = mask.reduce((s, m, j) => s + (m ? (accuracies[j] ? 1 : 0) : 0), 0) / count;
    ece += (count / n) * Math.abs(binAcc - binConf);
  }
  return Math.round(ece * 10000) / 10000;
}

export function computeBrier(confidences, accuracies) {
  const n = confidences.length;
  if (n === 0) return 0;
  const sum = confidences.reduce((s, c, i) => s + Math.pow(c - (accuracies[i] ? 1 : 0), 2), 0);
  return Math.round((sum / n) * 10000) / 10000;
}

export function computeWWA(accuracies, wagers, penaltyMult = 2.0) {
  const n = accuracies.length;
  if (n === 0) return 0;
  let gains = 0, losses = 0, maxPossible = 0;
  for (let i = 0; i < n; i++) {
    const w = wagers[i] / 100;
    maxPossible += w;
    if (accuracies[i]) gains += w;
    else losses += penaltyMult * w;
  }
  if (maxPossible === 0) return 0;
  return Math.round(((gains - losses) / maxPossible) * 10000) / 10000;
}

export function computeAbstentionScore(results) {
  let total = 0, correct = 0, incorrect = 0, abstained = 0;
  for (const r of results) {
    if (r.decision === "abstain") {
      total -= 2;
      abstained++;
    } else if (r.isCorrect) {
      total += 10;
      correct++;
    } else {
      total -= 50;
      incorrect++;
    }
  }
  const n = results.length;
  const maxScore = n * 10;
  return {
    totalScore: total,
    normalized: maxScore > 0 ? Math.round((total / maxScore) * 10000) / 10000 : 0,
    coverage: n > 0 ? (correct + incorrect) / n : 0,
    accuracyWhenAnswered: (correct + incorrect) > 0 ? correct / (correct + incorrect) : 0,
    correct, incorrect, abstained,
  };
}

export function computeInterferenceEffect(results) {
  const cong = results.filter(r => r.trialType === "congruent");
  const incong = results.filter(r => r.trialType === "incongruent");
  const congAcc = cong.length > 0 ? cong.filter(r => r.isCorrect).length / cong.length : 0;
  const incongAcc = incong.length > 0 ? incong.filter(r => r.isCorrect).length / incong.length : 0;
  return {
    congruentAccuracy: Math.round(congAcc * 10000) / 10000,
    incongruentAccuracy: Math.round(incongAcc * 10000) / 10000,
    interferenceEffect: Math.round((congAcc - incongAcc) * 10000) / 10000,
  };
}

export function formatDuration(ms) {
  if (ms < 1000) return `${ms}ms`;
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}
