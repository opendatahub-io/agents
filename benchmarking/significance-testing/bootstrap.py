"""
Bootstrap Resampling and Permutation Testing for Significance Testing

Implements bootstrap methods for computing confidence intervals
and p-values for accuracy differences between configurations.
"""

import math
import numpy as np
from typing import Optional
from tqdm import tqdm
from scipy.stats import permutation_test as scipy_permutation_test


def bootstrap_accuracy_difference(
    results_a: np.ndarray,
    results_b: np.ndarray,
    category_labels: np.ndarray,
    n_bootstrap: int = 10000,
    show_progress: bool = True,
) -> np.ndarray:
    """
    Stratified bootstrap that preserves category proportions.
    
    Samples within each category separately, then aggregates.
    This provides more accurate estimates when categories have
    different difficulties or sample sizes.
    
    Args:
        results_a: Binary array of pass/fail for config A
        results_b: Binary array of pass/fail for config B
        category_labels: Category label for each task
        n_bootstrap: Number of bootstrap iterations
        show_progress: Whether to show progress bar
    
    Returns:
        Array of bootstrap accuracy differences
    """
    categories = np.unique(category_labels)
    n_tasks = len(results_a)
    bootstrap_diffs = np.zeros(n_bootstrap)
    
    # Pre-compute category masks and sizes
    category_masks = {cat: category_labels == cat for cat in categories}
    category_sizes = {cat: np.sum(mask) for cat, mask in category_masks.items()}
    
    # Pre-extract category-specific results
    cat_results_a = {cat: results_a[mask] for cat, mask in category_masks.items()}
    cat_results_b = {cat: results_b[mask] for cat, mask in category_masks.items()}
    
    iterator = range(n_bootstrap)
    if show_progress:
        iterator = tqdm(iterator, desc="Stratified Bootstrap")
    
    for i in iterator:
        total_correct_a = 0
        total_correct_b = 0
        total_samples = 0
        
        for cat in categories:
            cat_size = category_sizes[cat]
            
            # Sample within category with replacement
            indices = np.random.choice(cat_size, size=cat_size, replace=True)
            
            # Sum correct predictions
            total_correct_a += np.sum(cat_results_a[cat][indices])
            total_correct_b += np.sum(cat_results_b[cat][indices])
            total_samples += cat_size
        
        # Compute overall accuracy difference
        acc_a = total_correct_a / total_samples
        acc_b = total_correct_b / total_samples
        bootstrap_diffs[i] = acc_a - acc_b
    
    return bootstrap_diffs


def paired_bootstrap(
    results_a: np.ndarray,
    results_b: np.ndarray,
    n_bootstrap: int = 10000,
) -> np.ndarray:
    """
    Paired bootstrap that maintains task correspondence.
    
    This is useful when tasks have varying difficulty - by keeping
    the pairing, we control for task-specific variance.
    
    Args:
        results_a: Binary array of pass/fail for config A
        results_b: Binary array of pass/fail for config B
        n_bootstrap: Number of bootstrap iterations
    
    Returns:
        Array of bootstrap accuracy differences
    """
    # Compute per-task differences
    task_diffs = results_a - results_b  # +1 if A better, -1 if B better, 0 if same
    
    n_tasks = len(task_diffs)
    bootstrap_diffs = np.zeros(n_bootstrap)
    
    for i in range(n_bootstrap):
        # Sample tasks with replacement
        indices = np.random.choice(n_tasks, size=n_tasks, replace=True)
        
        # Mean difference on bootstrap sample
        bootstrap_diffs[i] = np.mean(task_diffs[indices])
    
    return bootstrap_diffs


def compute_confidence_interval(
    bootstrap_samples: np.ndarray,
    confidence_level: float = 0.95,
    method: str = "percentile",
) -> tuple[float, float]:
    """
    Compute confidence interval from bootstrap samples.
    
    Args:
        bootstrap_samples: Array of bootstrap statistics
        confidence_level: Confidence level (default 0.95 for 95% CI)
        method: CI method - "percentile" or "bca" (bias-corrected)
    
    Returns:
        Tuple of (lower, upper) bounds
    """
    alpha = 1 - confidence_level
    
    if method == "percentile":
        lower = np.percentile(bootstrap_samples, 100 * alpha / 2)
        upper = np.percentile(bootstrap_samples, 100 * (1 - alpha / 2))
    elif method == "bca":
        # Bias-corrected and accelerated (simplified version)
        # For full BCa, would need jackknife estimates
        lower = np.percentile(bootstrap_samples, 100 * alpha / 2)
        upper = np.percentile(bootstrap_samples, 100 * (1 - alpha / 2))
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return lower, upper


def compute_p_value(
    bootstrap_samples: np.ndarray,
    observed_statistic: float,
    alternative: str = "two-sided",
) -> float:
    """
    Compute p-value for the null hypothesis that the true difference is zero.
    
    Uses the bootstrap distribution centered at zero to compute the probability
    of observing a difference as extreme as the observed one.
    
    Args:
        bootstrap_samples: Array of bootstrap statistics
        observed_statistic: The observed difference
        alternative: "two-sided", "greater", or "less"
    
    Returns:
        p-value
    """
    # Center bootstrap distribution at zero for null hypothesis
    centered_samples = bootstrap_samples - np.mean(bootstrap_samples)
    
    if alternative == "two-sided":
        # Proportion of bootstrap samples more extreme than observed
        p_value = np.mean(np.abs(centered_samples) >= np.abs(observed_statistic))
    elif alternative == "greater":
        p_value = np.mean(centered_samples >= observed_statistic)
    elif alternative == "less":
        p_value = np.mean(centered_samples <= observed_statistic)
    else:
        raise ValueError(f"Unknown alternative: {alternative}")
    
    # Ensure p-value is not exactly 0 (use conservative estimate)
    if p_value == 0:
        p_value = 1 / (len(bootstrap_samples) + 1)
    
    return p_value


def permutation_test(
    results_a: np.ndarray,
    results_b: np.ndarray,
    n_permutations: int = 10000,
) -> float:
    """
    Permutation test for comparing two configurations (manual implementation).
    
    Under the null hypothesis, labels (A vs B) are exchangeable.
    We randomly swap labels and compute the difference.
    
    Args:
        results_a: Binary array of pass/fail for config A
        results_b: Binary array of pass/fail for config B
        n_permutations: Number of permutations
    
    Returns:
        Two-sided p-value
    """
    observed_diff = np.mean(results_a) - np.mean(results_b)
    n_tasks = len(results_a)
    
    # Stack results
    combined = np.vstack([results_a, results_b])
    
    extreme_count = 0
    
    for _ in range(n_permutations):
        # Random permutation of labels for each task
        perm_a = np.zeros(n_tasks)
        perm_b = np.zeros(n_tasks)
        
        for j in range(n_tasks):
            if np.random.random() < 0.5:
                perm_a[j] = combined[0, j]
                perm_b[j] = combined[1, j]
            else:
                perm_a[j] = combined[1, j]
                perm_b[j] = combined[0, j]
        
        perm_diff = np.mean(perm_a) - np.mean(perm_b)
        
        if np.abs(perm_diff) >= np.abs(observed_diff):
            extreme_count += 1
    
    p_value = (extreme_count + 1) / (n_permutations + 1)
    
    return p_value


def scipy_paired_permutation_test(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    n_resamples: int = 10000,
) -> float:
    """
    Performs a permutation test using scipy's implementation.
    
    Uses scipy.stats.permutation_test with "samples" permutation type.
    
    Args:
        scores_a: Scores/results for configuration A
        scores_b: Scores/results for configuration B  
        n_resamples: Number of permutation resamples
    
    Returns:
        Two-sided p-value
    """
    def _statistic(x, y, axis):
        return np.mean(x, axis=axis) - np.mean(y, axis=axis)

    result = scipy_permutation_test(
        data=(scores_a, scores_b),
        statistic=_statistic,
        n_resamples=n_resamples,
        alternative="two-sided",
        permutation_type="samples",
    )
    return float(result.pvalue)


def print_significance_summary(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    overview_label: str,
    label_a: str,
    label_b: str,
) -> tuple[bool, float, float, float]:
    """
    Runs permutation test, prints results, returns significance info.
    
    Args:
        scores_a: Scores/results for configuration A
        scores_b: Scores/results for configuration B
        overview_label: Label for the comparison being made
        label_a: Name of configuration A
        label_b: Name of configuration B
    
    Returns:
        Tuple of (is_significant, p_value, mean_a, mean_b)
    """
    mean_score_a = np.mean(scores_a)
    mean_score_b = np.mean(scores_b)

    p_value = scipy_paired_permutation_test(scores_a, scores_b)
    
    print(overview_label)
    print(f" {label_a:<50}: {mean_score_a:>10.4f}")
    print(f" {label_b:<50}: {mean_score_b:>10.4f}")
    print(f" {'p_value':<50}: {p_value:>10.4f}")

    if p_value < 0.05:
        print("  p_value<0.05 so this result is statistically significant")
        higher_model_id = label_a if mean_score_a >= mean_score_b else label_b
        print(f"  You can conclude that {higher_model_id} generation is better on data of this sort")
        return True, p_value, mean_score_a, mean_score_b
    else:
        print("  p_value>=0.05 so this result is NOT statistically significant.")
        print("  You can conclude that there is not enough data to tell which is better.")
        num_samples = len(scores_a)
        margin_of_error = 1 / math.sqrt(num_samples)
        print(
            f"  Note that this data includes {num_samples} questions which typically produces "
            f"a margin of error of around +/-{margin_of_error:.1%}."
        )
        print("  So the two are probably roughly within that margin of error or so.")
        return False, p_value, mean_score_a, mean_score_b
