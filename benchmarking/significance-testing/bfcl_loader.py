"""
BFCL Result Loader

Loads per-task results from BFCL score files and prepares them for
significance testing.
"""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import numpy as np


@dataclass
class TaskResult:
    """Single task result."""
    task_id: str
    category: str
    passed: bool
    error_type: Optional[str] = None


def load_score_file(file_path: Path) -> tuple[list[TaskResult], dict, str, set]:
    """
    Load a single BFCL score file (JSONL format).
    
    BFCL score files are JSONL (newline-delimited JSON) with format:
        Line 1: {"accuracy": 0.95, "correct_count": 95, "total_count": 100}  # header
        Line 2: {"id": "multi_turn_base_2", "valid": false, "error": {...}, ...}
        Line 3: {"id": "multi_turn_base_4", "valid": false, "error": {...}, ...}
        ...
    
    Note: BFCL only writes failed tests to the score file. We need to
    reconstruct which tasks passed by looking at the header stats and
    the corresponding result file.
    """
    with open(file_path) as f:
        lines = f.readlines()
    
    if not lines:
        return [], {}, "", set()
    
    # First line is the header with aggregate stats
    header = json.loads(lines[0])
    
    # Extract category from filename (e.g., BFCL_v4_multi_turn_base_score.json)
    filename = file_path.stem
    # Remove prefix and suffix - support both v3 and v4
    category = filename.replace("BFCL_v4_", "").replace("_score", "")
    
    # Remaining lines are failed tests
    failed_ids = set()
    results = []
    
    for line in lines[1:]:
        if not line.strip():
            continue
        entry = json.loads(line)
        task_id = entry.get("id", "")
        # Error type is nested in BFCL format: {"error": {"error_type": "...", ...}}
        error_info = entry.get("error", {})
        if isinstance(error_info, dict):
            error_type = error_info.get("error_type", "unknown")
        else:
            error_type = "unknown"
        
        failed_ids.add(task_id)
        results.append(TaskResult(
            task_id=task_id,
            category=category,
            passed=False,
            error_type=error_type,
        ))
    
    return results, header, category, failed_ids


def load_result_file(file_path: Path) -> list[str]:
    """
    Load task IDs from a BFCL result file (JSONL format).
    
    Result files are JSONL and contain all tasks that were evaluated.
    Each line is: {"id": "multi_turn_base_0", "result": [...], ...}
    """
    task_ids = []
    with open(file_path) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if "id" in entry:
                    task_ids.append(entry["id"])
            except json.JSONDecodeError:
                continue
    return task_ids


def load_bfcl_results(
    score_dir: Path,
) -> dict[str, TaskResult]:
    """
    Load all BFCL results from a score directory.
    
    Args:
        score_dir: Path to the model's score directory
    
    Returns:
        Dictionary mapping task_id -> TaskResult
    """
    score_dir = Path(score_dir)
    if not score_dir.exists():
        raise FileNotFoundError(f"Score directory not found: {score_dir}")
    
    results = {}
    
    # Find all score files recursively
    score_files = list(score_dir.rglob("*_score.json"))
    
    if not score_files:
        raise ValueError(f"No score files found in {score_dir}")
    
    for score_file in score_files:
        try:
            failed_results, header, category, failed_ids = load_score_file(score_file)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse {score_file}: {e}")
            continue
        
        # Try to find corresponding result file to get all task IDs
        result_file = find_result_file(score_file, score_dir)
        
        if result_file and result_file.exists():
            all_task_ids = load_result_file(result_file)
        else:
            # Fall back to reconstructing from header stats
            # This uses BFCL's standard ID naming convention
            total_count = header.get("total_count", 0)
            correct_count = header.get("correct_count", 0)
            
            print(f"  Warning: Result file not found for {score_file.name}")
            print(f"    Reconstructing {total_count} task IDs from naming convention")
            
            # BFCL uses sequential IDs like: multi_turn_base_0, multi_turn_base_1, ...
            # Generate all possible IDs based on total_count
            all_task_ids = []
            for i in range(total_count):
                # Use the category name as the base for ID generation
                task_id = f"{category}_{i}"
                all_task_ids.append(task_id)
        
        # Mark all tasks - passed unless in failed_ids
        for task_id in all_task_ids:
            if task_id in failed_ids:
                # Find the failed result
                for fr in failed_results:
                    if fr.task_id == task_id:
                        results[task_id] = fr
                        break
            else:
                results[task_id] = TaskResult(
                    task_id=task_id,
                    category=category,
                    passed=True,
                )
    
    return results


def find_result_file(score_file: Path, score_dir: Path) -> Optional[Path]:
    """
    Find the corresponding result file for a score file, assuming BFCL's
    directory structure
    i.e. given:
        <BFCL_PROJECT_ROOT>/score/<model_name>/<category>/BFCL_v4_*_score.json
    find:
        <BFCL_PROJECT_ROOT>/result/<model_name>/<category>/BFCL_v4_*_result.json
    """
    result_filename = score_file.name.replace("_score.json", "_result.json")

    parts = score_file.resolve().parts
    # Find 'score' directory in path parts
    if "score" not in parts:
        raise ValueError("No 'score' dir in path")
    result_parts = list(parts)
    result_parts[parts.index("score")] = "result"
    result_parts[-1] = result_filename

    candidate = Path(*result_parts)
    if not candidate.exists():
        raise FileNotFoundError(f"Result file not found: {candidate} for score file {score_file}")
    
    return candidate


def align_results(
    results_a: dict[str, TaskResult],
    results_b: dict[str, TaskResult],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Align results from two configurations to have matching task IDs.
    
    Args:
        results_a: Results from configuration A
        results_b: Results from configuration B
    
    Returns:
        Tuple of (passed_a, passed_b, categories) as numpy arrays
        where passed_* is 1 for pass, 0 for fail
    """
    # Find common task IDs
    common_ids = set(results_a.keys()) & set(results_b.keys())
    
    if not common_ids:
        print("Warning: No common task IDs found!")
        print(f"  Config A has {len(results_a)} tasks")
        print(f"  Config B has {len(results_b)} tasks")
        print(f"  Sample A IDs: {list(results_a.keys())[:5]}")
        print(f"  Sample B IDs: {list(results_b.keys())[:5]}")
    
    # Sort for reproducibility
    common_ids = sorted(common_ids)
    
    passed_a = np.array([1 if results_a[tid].passed else 0 for tid in common_ids])
    passed_b = np.array([1 if results_b[tid].passed else 0 for tid in common_ids])
    categories = np.array([results_a[tid].category for tid in common_ids])
    
    return passed_a, passed_b, categories


def summarize_results(results: dict[str, TaskResult]) -> dict:
    """Generate summary statistics for results."""
    if not results:
        return {"total": 0, "passed": 0, "accuracy": 0.0, "categories": {}}
    
    total = len(results)
    passed = sum(1 for r in results.values() if r.passed)
    
    # Per-category breakdown
    categories = {}
    for r in results.values():
        if r.category not in categories:
            categories[r.category] = {"total": 0, "passed": 0}
        categories[r.category]["total"] += 1
        if r.passed:
            categories[r.category]["passed"] += 1
    
    for cat in categories:
        categories[cat]["accuracy"] = (
            categories[cat]["passed"] / categories[cat]["total"]
        )
    
    return {
        "total": total,
        "passed": passed,
        "accuracy": passed / total,
        "categories": categories,
    }

