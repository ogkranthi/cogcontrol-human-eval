"""
CogControl-Stakes: Scoring Metrics

Novel metrics for measuring cognitive control in LLMs, grounded in:
- Stroop Test (interference effect)
- WCST (perseverative errors)
- Nelson & Narens (1990) monitoring-control framework
- Type 2 Signal Detection Theory (metacognitive sensitivity)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional


# =============================================================================
# Executive Functions Metrics
# =============================================================================

def interference_effect(
    congruent_accuracies: List[float],
    incongruent_accuracies: List[float],
) -> Dict[str, float]:
    """
    LLM Stroop Interference Effect — the first Stroop analog for language models.

    Measures the performance drop when surface-level pattern conflicts with
    the correct answer (incongruent) vs. when it aligns (congruent).

    Based on: Stroop (1935), adapted for LLM evaluation.

    Returns:
        ie: Interference Effect (lower = better inhibitory control)
        congruent_acc: Mean accuracy on congruent trials
        incongruent_acc: Mean accuracy on incongruent trials
        effect_size: Cohen's d for the difference
    """
    cong = np.array(congruent_accuracies, dtype=float)
    incong = np.array(incongruent_accuracies, dtype=float)

    cong_mean = float(np.mean(cong))
    incong_mean = float(np.mean(incong))
    ie = cong_mean - incong_mean

    # Cohen's d effect size
    pooled_std = np.sqrt((np.var(cong, ddof=1) + np.var(incong, ddof=1)) / 2)
    effect_size = ie / pooled_std if pooled_std > 0 else 0.0

    return {
        "interference_effect": round(ie, 4),
        "congruent_accuracy": round(cong_mean, 4),
        "incongruent_accuracy": round(incong_mean, 4),
        "effect_size_cohens_d": round(effect_size, 4),
    }


def inhibition_score(
    gave_prepotent_response: bool,
    noted_uncertainty: bool,
    identified_contradictions: bool,
    final_answer_correct: bool,
) -> int:
    """
    Score inhibitory control on a single trial (0-3 scale).

    0 = Full inhibition failure (prepotent response, high confidence)
    1 = Prepotent response but noted some uncertainty
    2 = Identified contradictions but still leaned prepotent
    3 = Correctly inhibited prepotent response, gave right answer
    """
    if final_answer_correct and identified_contradictions:
        return 3
    if identified_contradictions and not final_answer_correct:
        return 2
    if gave_prepotent_response and noted_uncertainty:
        return 1
    return 0


def perseverative_error_rate(
    old_plan_elements: List[str],
    new_plan_elements: List[str],
    elements_that_should_change: List[str],
    elements_that_should_stay: List[str],
) -> Dict[str, float]:
    """
    WCST-inspired Perseverative Error Rate for cognitive flexibility.

    Measures whether the model inappropriately retains elements of an old plan
    when conditions have changed, OR gratuitously changes elements that should stay.

    Based on: Wisconsin Card Sorting Test (Milner, 1963; Miyake et al., 2000)

    Returns:
        perseverative_error_rate: Fraction of elements wrongly retained
        gratuitous_change_rate: Fraction of stable elements wrongly changed
        flexibility_score: Combined score (0-1, higher = better)
    """
    # Elements that should have changed but were retained
    retained_set = set(new_plan_elements) & set(old_plan_elements)
    should_change_set = set(elements_that_should_change)
    wrongly_retained = retained_set & should_change_set

    per = len(wrongly_retained) / len(should_change_set) if should_change_set else 0.0

    # Elements that were stable but got changed anyway
    should_stay_set = set(elements_that_should_stay)
    still_present = set(new_plan_elements) & should_stay_set
    wrongly_changed = should_stay_set - still_present

    gcr = len(wrongly_changed) / len(should_stay_set) if should_stay_set else 0.0

    # Combined flexibility score: penalize both perseveration and over-switching
    flexibility = 1.0 - (per + gcr) / 2.0

    return {
        "perseverative_error_rate": round(per, 4),
        "gratuitous_change_rate": round(gcr, 4),
        "flexibility_score": round(max(0.0, flexibility), 4),
    }


def planning_score(
    constraint_violations: int,
    total_constraints: int,
    optimality_score: float,
    lookahead_depth: int,
    tradeoff_articulation: int,
    max_lookahead: int = 5,
    max_tradeoff: int = 3,
) -> Dict[str, float]:
    """
    Tower of London-inspired planning score.

    Composite metric for multi-step planning under constraints.

    Returns:
        violation_rate: Fraction of constraints violated
        composite_score: Weighted composite (0-1)
        component_scores: Individual component breakdowns
    """
    violation_rate = constraint_violations / total_constraints if total_constraints > 0 else 0.0
    norm_optimality = optimality_score / 100.0
    norm_lookahead = lookahead_depth / max_lookahead
    norm_tradeoff = tradeoff_articulation / max_tradeoff

    composite = (
        (1 - violation_rate) * 0.4
        + norm_optimality * 0.3
        + norm_lookahead * 0.2
        + norm_tradeoff * 0.1
    )

    return {
        "violation_rate": round(violation_rate, 4),
        "optimality": round(norm_optimality, 4),
        "lookahead": round(norm_lookahead, 4),
        "tradeoff_articulation": round(norm_tradeoff, 4),
        "composite_score": round(composite, 4),
    }


# =============================================================================
# Metacognition Metrics
# =============================================================================

def expected_calibration_error(
    confidences: List[float],
    accuracies: List[bool],
    n_bins: int = 10,
) -> Dict[str, float]:
    """
    Expected Calibration Error (ECE) — standard metacognitive calibration metric.

    Measures alignment between stated confidence and actual accuracy.
    Lower ECE = better calibrated.

    Based on: Naeini et al. (2015)
    """
    confs = np.array(confidences, dtype=float)
    accs = np.array(accuracies, dtype=float)

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    bin_details = []

    for i in range(n_bins):
        lo, hi = bin_boundaries[i], bin_boundaries[i + 1]
        mask = (confs > lo) & (confs <= hi)
        if not np.any(mask):
            continue

        bin_conf = float(np.mean(confs[mask]))
        bin_acc = float(np.mean(accs[mask]))
        bin_size = int(np.sum(mask))
        bin_weight = bin_size / len(confs)

        ece += bin_weight * abs(bin_acc - bin_conf)
        bin_details.append({
            "bin": f"({lo:.1f}, {hi:.1f}]",
            "avg_confidence": round(bin_conf, 4),
            "avg_accuracy": round(bin_acc, 4),
            "count": bin_size,
            "gap": round(abs(bin_acc - bin_conf), 4),
        })

    return {
        "ece": round(ece, 4),
        "n_bins": n_bins,
        "n_samples": len(confs),
        "bin_details": bin_details,
    }


def brier_score(
    confidences: List[float],
    outcomes: List[bool],
) -> float:
    """
    Brier Score — combined measure of calibration and discrimination.
    Lower is better. Range: 0 (perfect) to 1 (worst).
    """
    confs = np.array(confidences, dtype=float)
    outs = np.array(outcomes, dtype=float)
    return round(float(np.mean((confs - outs) ** 2)), 4)


def wager_weighted_accuracy(
    accuracies: List[bool],
    wagers: List[float],
    max_wager: float = 100.0,
    wrong_penalty_multiplier: float = 2.0,
) -> Dict[str, float]:
    """
    Wager-Weighted Accuracy (NOVEL METRIC).

    Rewards confident correct answers, penalizes confident wrong answers
    exponentially more. Mirrors real-world consequences where overconfidence
    in high-stakes domains (healthcare, finance) is catastrophic.

    Based on: Gambling paradigms in metacognition research (Persaud et al., 2007)

    Score = sum(wager_i * correct_i - wrong_penalty * wager_i * (1 - correct_i)) / max_possible
    """
    accs = np.array(accuracies, dtype=float)
    wags = np.array(wagers, dtype=float)

    # Normalize wagers to [0, 1]
    norm_wagers = wags / max_wager

    gains = norm_wagers * accs
    losses = wrong_penalty_multiplier * norm_wagers * (1 - accs)
    raw_score = float(np.sum(gains - losses))
    max_possible = float(np.sum(norm_wagers))  # perfect score if all correct

    # Normalize to [-1, 1] range
    wwa = raw_score / max_possible if max_possible > 0 else 0.0

    return {
        "wager_weighted_accuracy": round(wwa, 4),
        "total_gain": round(float(np.sum(gains)), 4),
        "total_loss": round(float(np.sum(losses)), 4),
        "mean_wager_correct": round(float(np.mean(wags[accs == 1])) if np.any(accs == 1) else 0.0, 4),
        "mean_wager_incorrect": round(float(np.mean(wags[accs == 0])) if np.any(accs == 0) else 0.0, 4),
    }


def selective_abstention_score(
    predictions: List[Optional[str]],
    ground_truths: List[str],
    correct_reward: float = 10.0,
    incorrect_penalty: float = -50.0,
    abstention_cost: float = -2.0,
) -> Dict[str, float]:
    """
    Risk-Adjusted Score for selective abstention under asymmetric payoff.

    Models must decide: answer (risk being wrong) or defer (small certain cost).
    Optimal strategy requires accurate self-knowledge of one's own competence.

    Based on: Opt-out paradigms in metacognition (Koriat & Goldsmith, 1996)
    """
    total_score = 0.0
    n_answered = 0
    n_abstained = 0
    n_correct = 0
    n_incorrect = 0

    for pred, truth in zip(predictions, ground_truths):
        if pred is None:
            total_score += abstention_cost
            n_abstained += 1
        elif pred == truth:
            total_score += correct_reward
            n_correct += 1
            n_answered += 1
        else:
            total_score += incorrect_penalty
            n_incorrect += 1
            n_answered += 1

    n_total = len(predictions)
    coverage = n_answered / n_total if n_total > 0 else 0.0
    accuracy_when_answered = n_correct / n_answered if n_answered > 0 else 0.0

    # Max possible score (answer everything correctly)
    max_score = n_total * correct_reward
    normalized_score = total_score / max_score if max_score > 0 else 0.0

    return {
        "risk_adjusted_score": round(total_score, 2),
        "normalized_score": round(normalized_score, 4),
        "coverage": round(coverage, 4),
        "accuracy_when_answered": round(accuracy_when_answered, 4),
        "abstention_rate": round(n_abstained / n_total if n_total > 0 else 0.0, 4),
        "n_correct": n_correct,
        "n_incorrect": n_incorrect,
        "n_abstained": n_abstained,
    }


def type2_auroc(
    confidences: List[float],
    accuracies: List[bool],
) -> float:
    """
    Type 2 AUROC — metacognitive sensitivity metric from Signal Detection Theory.

    Measures whether the model's confidence discriminates between its own
    correct and incorrect responses. Higher = better metacognitive sensitivity.

    Based on: Fleming & Lau (2014), Maniscalco & Lau (2012)
    """
    from sklearn.metrics import roc_auc_score

    confs = np.array(confidences, dtype=float)
    accs = np.array(accuracies, dtype=float)

    if len(np.unique(accs)) < 2:
        return 0.5  # Cannot compute if all correct or all incorrect

    return round(float(roc_auc_score(accs, confs)), 4)


def cross_domain_transfer_index(
    domain_a_scores: Dict[str, float],
    domain_b_scores: Dict[str, float],
) -> Dict[str, float]:
    """
    Cross-Domain Transfer Index (NOVEL METRIC).

    Measures whether cognitive abilities transfer across domains.
    High correlation = domain-general ability.
    Low correlation = domain-specific calibration artifact.

    This metric addresses a fundamental question: Is metacognition a
    cognitive ability or a domain-specific fine-tuning artifact?
    """
    common_keys = set(domain_a_scores.keys()) & set(domain_b_scores.keys())
    if len(common_keys) < 3:
        return {"transfer_index": None, "reason": "insufficient common metrics"}

    a_vals = np.array([domain_a_scores[k] for k in sorted(common_keys)])
    b_vals = np.array([domain_b_scores[k] for k in sorted(common_keys)])

    correlation = float(np.corrcoef(a_vals, b_vals)[0, 1])
    mean_gap = float(np.mean(np.abs(a_vals - b_vals)))

    return {
        "transfer_index": round(correlation, 4),
        "mean_absolute_gap": round(mean_gap, 4),
        "interpretation": (
            "domain-general" if correlation > 0.7
            else "partially transferable" if correlation > 0.4
            else "domain-specific"
        ),
    }


def cognitive_coherence(
    metacognition_scores: List[float],
    ef_scores: List[float],
) -> Dict[str, float]:
    """
    Cognitive Coherence Score (NOVEL METRIC).

    In humans, metacognitive accuracy predicts executive function performance.
    This metric tests whether the same relationship holds in LLMs.

    High coherence = the model's self-knowledge aligns with its actual control.
    Low coherence = disconnect between self-assessment and behavior.
    """
    mc = np.array(metacognition_scores, dtype=float)
    ef = np.array(ef_scores, dtype=float)

    if len(mc) < 3 or len(ef) < 3:
        return {"coherence": None, "reason": "insufficient data points"}

    correlation = float(np.corrcoef(mc, ef)[0, 1])

    return {
        "cognitive_coherence": round(correlation, 4),
        "interpretation": (
            "strong coherence" if correlation > 0.6
            else "moderate coherence" if correlation > 0.3
            else "weak coherence (metacognition-behavior gap)"
        ),
    }
