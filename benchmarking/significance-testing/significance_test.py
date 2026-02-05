#!/usr/bin/env python3
"""
Significance Testing for BFCL Evaluations using Bootstrap Resampling.

This script compares two BFCL configurations and determines if their
performance difference is statistically significant using task-level
bootstrap resampling.
"""

import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats

from bfcl_loader import load_bfcl_results, align_results
from bootstrap import (
    bootstrap_accuracy_difference,
    compute_confidence_interval,
    compute_p_value,
    scipy_paired_permutation_test,
)


@dataclass
class SignificanceResult:
    """Results from significance testing."""
    config_a_name: str
    config_b_name: str
    config_a_accuracy: float
    config_b_accuracy: float
    mean_difference: float
    ci_lower: float
    ci_upper: float
    p_value_bootstrap: float
    p_value_permutation: float
    n_bootstrap: int
    n_tasks: int
    is_significant: bool
    methods_agree: bool
    category_results: dict


def run_significance_test(
    config_a_path: Path,
    config_b_path: Path,
    n_bootstrap: int = 10000,
    confidence_level: float = 0.95,
    seed: Optional[int] = None,
) -> SignificanceResult:
    """
    Run significance test comparing two BFCL configurations.
    
    Args:
        config_a_path: Path to first configuration's score directory
        config_b_path: Path to second configuration's score directory
        n_bootstrap: Number of bootstrap iterations
        confidence_level: Confidence level for CI (default 0.95)
        seed: Random seed for reproducibility
    
    Returns:
        SignificanceResult with all statistics
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Load results from both configurations
    print(f"Loading results from {config_a_path}...")
    results_a = load_bfcl_results(config_a_path)
    
    print(f"Loading results from {config_b_path}...")
    results_b = load_bfcl_results(config_b_path)
    
    # Align results (ensure same tasks in both)
    print("Aligning task results...")
    aligned_a, aligned_b, category_labels = align_results(results_a, results_b)
    
    n_tasks = len(aligned_a)
    print(f"Aligned {n_tasks} tasks across {len(set(category_labels))} categories")
    
    if n_tasks == 0:
        raise ValueError("No aligned tasks found between configurations")
    
    # Compute observed accuracies
    acc_a = np.mean(aligned_a)
    acc_b = np.mean(aligned_b)
    observed_diff = acc_a - acc_b
    
    print(f"\nObserved accuracies:")
    print(f"  Config A: {acc_a:.4f} ({sum(aligned_a)}/{n_tasks})")
    print(f"  Config B: {acc_b:.4f} ({sum(aligned_b)}/{n_tasks})")
    print(f"  Difference (A - B): {observed_diff:+.4f}")
    
    # Run bootstrap
    print(f"\nRunning {n_bootstrap:,} bootstrap iterations...")
    
    bootstrap_diffs = bootstrap_accuracy_difference(
        aligned_a, aligned_b, category_labels, n_bootstrap
    )
    
    # Compute statistics
    ci_lower, ci_upper = compute_confidence_interval(
        bootstrap_diffs, confidence_level
    )
    p_value_bootstrap = compute_p_value(bootstrap_diffs, observed_diff)
    
    # Run scipy permutation test 
    print("Running scipy permutation test for cross-validation...")
    p_value_permutation = scipy_paired_permutation_test(
        aligned_a, aligned_b, n_resamples=n_bootstrap
    )
    
    # Per-category analysis
    category_results = compute_category_breakdown(
        aligned_a, aligned_b, category_labels, n_bootstrap
    )
    
    alpha = 1 - confidence_level
    # Consider significant if BOTH methods agree
    # Cast to native Python bool to avoid numpy.bool_ JSON serialization issues
    is_significant = bool((p_value_bootstrap < alpha) and (p_value_permutation < alpha))
    methods_agree = bool(abs(p_value_bootstrap - p_value_permutation) < 0.1)
    
    result = SignificanceResult(
        config_a_name=config_a_path.name,
        config_b_name=config_b_path.name,
        config_a_accuracy=float(acc_a),
        config_b_accuracy=float(acc_b),
        mean_difference=float(observed_diff),
        ci_lower=float(ci_lower),
        ci_upper=float(ci_upper),
        p_value_bootstrap=float(p_value_bootstrap),
        p_value_permutation=float(p_value_permutation),
        n_bootstrap=n_bootstrap,
        n_tasks=n_tasks,
        is_significant=is_significant,
        methods_agree=methods_agree,
        category_results=category_results,
    )
    
    return result


def compute_category_breakdown(
    results_a: np.ndarray,
    results_b: np.ndarray,
    category_labels: np.ndarray,
    n_bootstrap: int,
) -> dict:
    """Compute per-category statistics."""
    categories = np.unique(category_labels)
    breakdown = {}
    
    for cat in categories:
        mask = category_labels == cat
        cat_a = results_a[mask]
        cat_b = results_b[mask]
        
        acc_a = np.mean(cat_a)
        acc_b = np.mean(cat_b)
        diff = acc_a - acc_b
        
        # Quick bootstrap for this category
        cat_bootstrap_diffs = bootstrap_accuracy_difference(
            cat_a, cat_b, min(n_bootstrap, 1000)
        )
        ci_lower, ci_upper = compute_confidence_interval(cat_bootstrap_diffs, 0.95)
        
        # Use str(cat) to convert numpy string to native Python string
        breakdown[str(cat)] = {
            "n_tasks": int(sum(mask)),
            "accuracy_a": float(acc_a),
            "accuracy_b": float(acc_b),
            "difference": float(diff),
            "ci_95": [float(ci_lower), float(ci_upper)],
        }
    
    return breakdown


def print_results(result: SignificanceResult) -> None:
    """Print formatted results to console."""
    print("\n" + "=" * 60)
    print("SIGNIFICANCE TEST RESULTS")
    print("=" * 60)
    
    print(f"\nConfigurations:")
    print(f"  A: {result.config_a_name}")
    print(f"  B: {result.config_b_name}")
    
    print(f"\nOverall Accuracy:")
    print(f"  Config A: {result.config_a_accuracy:.4f}")
    print(f"  Config B: {result.config_b_accuracy:.4f}")
    
    print(f"\nDifference (A - B):")
    print(f"  Mean: {result.mean_difference:+.4f}")
    print(f"  95% CI: [{result.ci_lower:+.4f}, {result.ci_upper:+.4f}]")
    
    print(f"\nStatistical Significance:")
    print(f"  Bootstrap p-value:    {result.p_value_bootstrap:.4f}")
    print(f"  Permutation p-value:  {result.p_value_permutation:.4f}")
    print(f"  Methods agree:        {'YES ✓' if result.methods_agree else 'NO ✗'}")
    print(f"  Significant (α=0.05): {'YES ✓' if result.is_significant else 'NO ✗'}")
    
    print(f"\nPer-Category Breakdown:")
    print("-" * 60)
    print(f"{'Category':<25} {'A':>8} {'B':>8} {'Diff':>8} {'n':>6}")
    print("-" * 60)
    
    for cat, stats in sorted(result.category_results.items()):
        print(
            f"{cat:<25} "
            f"{stats['accuracy_a']:>8.3f} "
            f"{stats['accuracy_b']:>8.3f} "
            f"{stats['difference']:>+8.3f} "
            f"{stats['n_tasks']:>6}"
        )
    
    print("-" * 60)
    print(f"{'TOTAL':<25} "
          f"{result.config_a_accuracy:>8.3f} "
          f"{result.config_b_accuracy:>8.3f} "
          f"{result.mean_difference:>+8.3f} "
          f"{result.n_tasks:>6}")
    
    print("\n" + "=" * 60)


def save_results(result: SignificanceResult, output_path: Path) -> None:
    """Save results to JSON file."""
    output = {
        "config_a": result.config_a_name,
        "config_b": result.config_b_name,
        "accuracy": {
            "config_a": result.config_a_accuracy,
            "config_b": result.config_b_accuracy,
        },
        "difference": {
            "mean": result.mean_difference,
            "ci_95_lower": result.ci_lower,
            "ci_95_upper": result.ci_upper,
        },
        "significance": {
            "p_value_bootstrap": result.p_value_bootstrap,
            "p_value_permutation": result.p_value_permutation,
            "methods_agree": result.methods_agree,
            "is_significant_alpha_05": result.is_significant,
        },
        "metadata": {
            "n_bootstrap": result.n_bootstrap,
            "n_tasks": result.n_tasks,
        },
        "category_breakdown": result.category_results,
    }
    
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="BFCL Significance Testing using Bootstrap Resampling"
    )
    parser.add_argument(
        "--config-a", "-a",
        type=Path,
        required=True,
        help="Path to first configuration's score directory",
    )
    parser.add_argument(
        "--config-b", "-b",
        type=Path,
        required=True,
        help="Path to second configuration's score directory",
    )
    parser.add_argument(
        "--n-bootstrap", "-n",
        type=int,
        default=10000,
        help="Number of bootstrap iterations (default: 10000)",
    )
    parser.add_argument(
        "--confidence-level",
        type=float,
        default=0.95,
        help="Confidence level for CI (default: 0.95)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output JSON file path",
    )
    
    args = parser.parse_args()
    
    # Run test
    try:
        result = run_significance_test(
            config_a_path=args.config_a,
            config_b_path=args.config_b,
            n_bootstrap=args.n_bootstrap,
            confidence_level=args.confidence_level,
            seed=args.seed,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Print results
    print_results(result)
    
    # Save results
    if args.output:
        save_results(result, args.output)
    
    # Exit with appropriate code
    sys.exit(0 if result.is_significant else 1)


if __name__ == "__main__":
    main()

