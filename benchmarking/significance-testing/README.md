# Significance Testing for BFCL

This POC implements statistical significance testing for BFCL evaluations using bootstrap resampling and permutation testing for cross-validation.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run example with synthetic data
python example_usage.py

# Run significance test between two BFCL configurations
python significance_test.py \
    --config-a /path/to/score/model_a \
    --config-b /path/to/score/model_b \
    --n-bootstrap 10000 \
    --output results.json
```

## Example Output

```
============================================================
SIGNIFICANCE TEST RESULTS
============================================================

Configurations:
  A: gpt-oss-120b-vllm-responses
  B: gpt-oss-120b-lls-responses

Overall Accuracy:
  Config A: 0.8500
  Config B: 0.8200

Difference (A - B):
  Mean: +0.0300
  95% CI: [+0.0050, +0.0550]

Statistical Significance
  Bootstrap p-value:    0.0234
  Permutation p-value:  0.0198
  Methods agree:        YES ✓
  Significant (α=0.05): YES ✓
```

## How It Works

### Bootstrap Resampling
1. Load per-task results from BFCL score files
2. Bootstrap resample tasks (stratified by category)
3. Compute accuracy difference for each bootstrap sample
4. Build 95% confidence interval and compute p-value

### Scipy Permutation Test
1. Use `scipy.stats.permutation_test` with paired samples
2. Under H₀, task labels (A vs B) are exchangeable
3. Compute p-value from permutation distribution

### Cross-Validation
- Both methods should give similar p-values
- If they disagree significantly (>0.1 difference), investigate
- Result is considered significant only if **both** methods agree
