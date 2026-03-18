"""
CogControl-Stakes: Evaluation Harness
======================================

Runs the full benchmark suite against LLMs and computes all metrics.

This is designed to work both:
1. Locally (for development/testing) using API calls
2. On Kaggle Community Benchmarks (using @kbench.task decorators)

The harness orchestrates all tasks, collects responses, and computes
the full scoring profile including novel metrics.
"""

import json
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Callable

from src.scoring.metrics import (
    interference_effect,
    inhibition_score,
    perseverative_error_rate,
    planning_score,
    expected_calibration_error,
    brier_score,
    wager_weighted_accuracy,
    selective_abstention_score,
    type2_auroc,
    cross_domain_transfer_index,
    cognitive_coherence,
)

from src.tasks.diagnostic_decoy import (
    ALL_VIGNETTES as DECOY_VIGNETTES,
    TrialType,
    Domain as DecoyDomain,
)
from src.tasks.mid_course_correction import (
    ALL_SCENARIOS as FLEX_SCENARIOS,
)
from src.tasks.calibrated_confidence import (
    DRUG_INTERACTION_ITEMS,
    RISK_FACTOR_ITEMS,
)
from src.tasks.selective_abstention import (
    ALL_ITEMS as ABSTENTION_ITEMS,
)


# =============================================================================
# Model Interface (abstract — swap for Kaggle SDK or API client)
# =============================================================================

class ModelInterface:
    """Abstract interface for LLM interaction. Subclass for specific backends."""

    def prompt(self, message: str, system: Optional[str] = None) -> str:
        raise NotImplementedError

    def multi_turn(self, messages: List[Dict[str, str]]) -> str:
        raise NotImplementedError


class MockModel(ModelInterface):
    """Mock model for testing the harness."""

    def prompt(self, message: str, system: Optional[str] = None) -> str:
        return json.dumps({
            "initial_impression": "Mock response",
            "key_observations": ["observation 1"],
            "contradictory_evidence": [],
            "final_assessment": "Mock assessment",
            "confidence": 0.5,
            "reasoning": "Mock reasoning",
        })

    def multi_turn(self, messages: List[Dict[str, str]]) -> str:
        return self.prompt(messages[-1]["content"])


# =============================================================================
# Response Parsing
# =============================================================================

def parse_json_response(response: str) -> Dict[str, Any]:
    """Extract JSON from model response, handling markdown code blocks."""
    text = response.strip()

    # Try to extract JSON from code blocks
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()

    # Find JSON object boundaries
    if "{" in text:
        start = text.index("{")
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    text = text[start:i + 1]
                    break

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_parse_error": True, "_raw_response": response}


# =============================================================================
# Task Runners
# =============================================================================

def run_diagnostic_decoy(model: ModelInterface) -> Dict[str, Any]:
    """Run EF-1: Diagnostic Decoy (Stroop) evaluation."""
    results = []
    congruent_accuracies = []
    incongruent_accuracies = []

    for vignette in DECOY_VIGNETTES:
        prompt = vignette.to_prompt()
        raw_response = model.prompt(prompt)
        parsed = parse_json_response(raw_response)

        # Determine accuracy
        is_correct = not parsed.get("_parse_error", False)
        # For incongruent trials: check if model identified contradictions
        identified_contradictions = bool(parsed.get("contradictory_evidence", []))
        gave_prepotent = False
        noted_uncertainty = False

        if not parsed.get("_parse_error"):
            confidence = parsed.get("confidence", 0.5)
            noted_uncertainty = confidence < 0.7

            # Check if final assessment aligns with surface pattern (prepotent) or correct answer
            final = parsed.get("final_assessment", "").lower()
            if vignette.trial_type == TrialType.INCONGRUENT:
                # For incongruent: if response aligns with surface pattern, it's prepotent
                gave_prepotent = vignette.surface_pattern_label.lower().split()[0] in final
                is_correct = not gave_prepotent and identified_contradictions

        inh_score = inhibition_score(
            gave_prepotent_response=gave_prepotent,
            noted_uncertainty=noted_uncertainty,
            identified_contradictions=identified_contradictions,
            final_answer_correct=is_correct,
        )

        acc = 1.0 if is_correct else 0.0
        if vignette.trial_type == TrialType.CONGRUENT:
            congruent_accuracies.append(acc)
        else:
            incongruent_accuracies.append(acc)

        results.append({
            "vignette_id": vignette.id,
            "domain": vignette.domain.value,
            "trial_type": vignette.trial_type.value,
            "difficulty": vignette.difficulty,
            "is_correct": is_correct,
            "inhibition_score": inh_score,
            "gave_prepotent": gave_prepotent,
            "identified_contradictions": identified_contradictions,
            "confidence": parsed.get("confidence", None),
        })

    ie_metrics = interference_effect(congruent_accuracies, incongruent_accuracies)

    return {
        "task": "EF-1_diagnostic_decoy",
        "summary": ie_metrics,
        "per_item_results": results,
        "n_congruent": len(congruent_accuracies),
        "n_incongruent": len(incongruent_accuracies),
    }


def run_mid_course_correction(model: ModelInterface) -> Dict[str, Any]:
    """Run EF-2: Mid-Course Correction (WCST) evaluation."""
    results = []

    for scenario in FLEX_SCENARIOS:
        scenario_results = {"scenario_id": scenario.id, "domain": scenario.domain.value, "turns": []}
        messages = []

        for turn_idx, turn in enumerate(scenario.turns):
            prompt = scenario.get_turn_prompt(
                turn_number=turn_idx,
                prior_response=messages[-1]["content"] if messages else None,
            )
            messages.append({"role": "user", "content": prompt})
            raw_response = model.multi_turn(messages)
            parsed = parse_json_response(raw_response)
            messages.append({"role": "assistant", "content": raw_response})

            turn_result = {
                "turn_number": turn_idx,
                "shift_type": turn.shift_type.value if turn.shift_type else None,
                "response": parsed,
            }

            # Score flexibility for turns > 0
            if turn_idx > 0 and turn.elements_that_should_change:
                detected_changes = parsed.get("changes_detected", [])
                elements_retained = parsed.get("elements_retained", [])
                elements_abandoned = parsed.get("elements_abandoned", [])

                change_detection_rate = min(
                    len(detected_changes) / len(turn.key_adaptations),
                    1.0,
                ) if turn.key_adaptations else 0.0

                turn_result["change_detection_rate"] = round(change_detection_rate, 4)
                turn_result["n_changes_detected"] = len(detected_changes)
                turn_result["n_expected_changes"] = len(turn.key_adaptations)

            scenario_results["turns"].append(turn_result)

        results.append(scenario_results)

    return {
        "task": "EF-2_mid_course_correction",
        "scenarios": results,
        "n_scenarios": len(results),
    }


def run_calibrated_confidence(model: ModelInterface) -> Dict[str, Any]:
    """Run MC-1: Calibrated Confidence evaluation."""
    healthcare_results = []
    finance_results = []

    # Healthcare: Drug interactions
    for item in DRUG_INTERACTION_ITEMS:
        prompt = item.to_prompt()
        raw_response = model.prompt(prompt)
        parsed = parse_json_response(raw_response)

        is_correct = (
            parsed.get("severity_classification", "").lower()
            == item.correct_severity.value
        )

        healthcare_results.append({
            "item_id": item.id,
            "difficulty": item.difficulty.value,
            "is_correct": is_correct,
            "confidence": parsed.get("confidence", 0.5),
            "wager": parsed.get("wager", 50),
            "predicted": parsed.get("severity_classification", ""),
            "actual": item.correct_severity.value,
        })

    # Finance: Risk factors
    for item in RISK_FACTOR_ITEMS:
        prompt = item.to_prompt()
        raw_response = model.prompt(prompt)
        parsed = parse_json_response(raw_response)

        predicted = parsed.get("assessment", "").lower()
        actual = "materialized" if item.risk_materialized else "did_not_materialize"
        is_correct = predicted == actual

        finance_results.append({
            "item_id": item.id,
            "difficulty": item.difficulty.value,
            "is_correct": is_correct,
            "confidence": parsed.get("confidence", 0.5),
            "wager": parsed.get("wager", 50),
            "predicted": predicted,
            "actual": actual,
        })

    # Compute metrics for each domain
    def compute_domain_metrics(results):
        confs = [r["confidence"] for r in results]
        accs = [r["is_correct"] for r in results]
        wagers = [r["wager"] for r in results]

        return {
            "ece": expected_calibration_error(confs, accs),
            "brier": brier_score(confs, accs),
            "wager_weighted": wager_weighted_accuracy(accs, wagers),
            "type2_auroc": type2_auroc(confs, accs),
            "accuracy": round(sum(accs) / len(accs), 4) if accs else 0,
        }

    hc_metrics = compute_domain_metrics(healthcare_results)
    fin_metrics = compute_domain_metrics(finance_results)

    # Cross-domain transfer
    transfer = cross_domain_transfer_index(
        {k: v for k, v in hc_metrics.items() if isinstance(v, (int, float))},
        {k: v for k, v in fin_metrics.items() if isinstance(v, (int, float))},
    )

    return {
        "task": "MC-1_calibrated_confidence",
        "healthcare": {"metrics": hc_metrics, "per_item": healthcare_results},
        "finance": {"metrics": fin_metrics, "per_item": finance_results},
        "cross_domain_transfer": transfer,
    }


def run_selective_abstention(model: ModelInterface) -> Dict[str, Any]:
    """Run MC-2: Selective Abstention evaluation."""
    results = []
    predictions = []
    ground_truths = []

    for item in ABSTENTION_ITEMS:
        prompt = item.to_prompt()
        raw_response = model.prompt(prompt)
        parsed = parse_json_response(raw_response)

        decision = parsed.get("decision", "answer")
        answer = parsed.get("answer") if decision == "answer" else None

        predictions.append(answer)
        ground_truths.append(item.correct_answer or "__UNANSWERABLE__")

        results.append({
            "item_id": item.id,
            "domain": item.domain.value,
            "answerability": item.answerability.value,
            "decision": decision,
            "answer": answer,
            "confidence": parsed.get("confidence", 0.5),
            "specialist_referral": parsed.get("specialist_referral"),
        })

    # Compute abstention metrics
    abs_metrics = selective_abstention_score(predictions, ground_truths)

    return {
        "task": "MC-2_selective_abstention",
        "metrics": abs_metrics,
        "per_item": results,
    }


# =============================================================================
# Full Benchmark Runner
# =============================================================================

def run_full_benchmark(model: ModelInterface) -> Dict[str, Any]:
    """Run the complete CogControl-Stakes benchmark suite."""
    print("=" * 60)
    print("CogControl-Stakes: Full Benchmark Suite")
    print("=" * 60)

    all_results = {}

    # EF-1: Diagnostic Decoy
    print("\n[1/4] Running EF-1: Diagnostic Decoy (Stroop)...")
    all_results["ef1_diagnostic_decoy"] = run_diagnostic_decoy(model)
    print(f"  Interference Effect: {all_results['ef1_diagnostic_decoy']['summary']['interference_effect']}")

    # EF-2: Mid-Course Correction
    print("\n[2/4] Running EF-2: Mid-Course Correction (WCST)...")
    all_results["ef2_mid_course_correction"] = run_mid_course_correction(model)
    print(f"  Scenarios evaluated: {all_results['ef2_mid_course_correction']['n_scenarios']}")

    # MC-1: Calibrated Confidence
    print("\n[3/4] Running MC-1: Calibrated Confidence...")
    all_results["mc1_calibrated_confidence"] = run_calibrated_confidence(model)
    hc_ece = all_results["mc1_calibrated_confidence"]["healthcare"]["metrics"]["ece"]["ece"]
    fin_ece = all_results["mc1_calibrated_confidence"]["finance"]["metrics"]["ece"]["ece"]
    print(f"  Healthcare ECE: {hc_ece} | Finance ECE: {fin_ece}")

    # MC-2: Selective Abstention
    print("\n[4/4] Running MC-2: Selective Abstention...")
    all_results["mc2_selective_abstention"] = run_selective_abstention(model)
    ras = all_results["mc2_selective_abstention"]["metrics"]["risk_adjusted_score"]
    print(f"  Risk-Adjusted Score: {ras}")

    # Composite scores
    print("\n" + "=" * 60)
    print("COMPOSITE SCORES")
    print("=" * 60)

    ef_score = all_results["ef1_diagnostic_decoy"]["summary"]["incongruent_accuracy"]
    mc_score = 1.0 - all_results["mc1_calibrated_confidence"]["healthcare"]["metrics"]["ece"]["ece"]

    coherence = cognitive_coherence([mc_score], [ef_score])
    all_results["composite"] = {
        "ef_headline": all_results["ef1_diagnostic_decoy"]["summary"],
        "mc_headline_ece_healthcare": hc_ece,
        "mc_headline_ece_finance": fin_ece,
        "cognitive_coherence": coherence,
        "cross_domain_transfer": all_results["mc1_calibrated_confidence"]["cross_domain_transfer"],
    }

    print(f"  EF Interference Effect: {all_results['ef1_diagnostic_decoy']['summary']['interference_effect']}")
    print(f"  MC ECE (Healthcare): {hc_ece}")
    print(f"  MC ECE (Finance): {fin_ece}")
    print(f"  Cross-Domain Transfer: {all_results['mc1_calibrated_confidence']['cross_domain_transfer']}")

    return all_results


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    print("Running with MockModel for harness validation...\n")
    mock = MockModel()
    results = run_full_benchmark(mock)

    output_path = "data/processed/benchmark_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {output_path}")
