# Biome Analysis Notebooks

Interactive Jupyter notebooks for analyzing and tuning Valheim world biome classification parameters.

## 🎯 Purpose

This notebook ecosystem provides **modular, focused tools** for fast-iteration analysis of biome classification logic. Instead of rebuilding Docker containers and regenerating samples for every parameter change (15-20 minutes), you can now adjust parameters and see results in **5-10 seconds**.

---

## 📁 Structure

```
notebooks/
├── README.md                          ← You are here
├── requirements.txt                   ← Python dependencies
├── config.py                          ← Shared constants and configuration
├── biome_utils.py                     ← Shared utility functions
├── 01_data_exploration.ipynb          ← Start here: Load and explore data
├── 02_sea_level_analysis.ipynb        ← Tune sea level thresholds
├── 03_polar_filter_tuning.ipynb       ← Optimize polar biome filters
├── 04_noise_threshold_analysis.ipynb  ← Analyze noise thresholds
├── 05_filter_comparison.ipynb         ← Compare filter strategies
├── 06_heightmap_visualization.ipynb   ← Visualize terrain heights
└── 07_parameter_export.ipynb          ← Export optimized params
```

---

## 🏗️ Design Philosophy

### Focused Scope
**Each notebook has ONE clear purpose.** No 2000-line monolithic notebooks.
- `01` - Explore data
- `02` - Tune sea level
- `03` - Tune polar filters
- etc.

### Shared Setup
**Common code lives in `biome_utils.py` and `config.py`.**
- Update once → affects all notebooks
- No code duplication
- Consistent behavior

### Fast Iteration
**Adjust parameters, see results in seconds.**
- Load data once
- Pure Python/NumPy processing
- No Docker rebuilds
- No sample regeneration

### Reproducible
**All analysis can be re-run deterministically.**
- Same input → same output
- Versioned parameters in `config.py`
- Documented transformations

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Jupyter Notebook or JupyterLab
- Sample data: `../output/samples/hkLycKKCMI-samples-1024.json`

### Installation

```bash
cd procedural-export/notebooks

# Install dependencies
pip install -r requirements.txt

# Enable Jupyter widgets (for interactive sliders)
jupyter nbextension enable --py widgetsnbextension

# Start Jupyter
jupyter notebook
```

**Or use JupyterLab:**
```bash
jupyter lab
```

### First Run

1. **Open `01_data_exploration.ipynb`**
2. **Run all cells** (Cell → Run All)
3. **Verify data loads correctly**
4. **Review basic statistics**
5. **Proceed to specialized notebooks as needed**

---

## 📚 Notebook Guide

### Recommended Order

| # | Notebook | Purpose | Time | Prerequisites |
|---|----------|---------|------|---------------|
| **1** | `data_exploration` | Load and understand raw data | 5 min | Sample data file |
| **2** | `sea_level_analysis` | Tune sea level threshold | 10 min | Notebook 01 |
| **3** | `polar_filter_tuning` | Optimize polar biome filters | 15 min | Notebook 01 |
| **4** | `noise_threshold_analysis` | Analyze noise thresholds | 10 min | Notebook 01 |
| **5** | `filter_comparison` | Compare different strategies | 10 min | Notebooks 02-04 |
| **6** | `heightmap_visualization` | 3D terrain visualization | 5 min | Notebook 01 |
| **7** | `parameter_export` | Export optimized parameters | 5 min | Notebooks 02-06 |

**Total Time:** ~60 minutes for full analysis cycle

---

### Notebook Details

#### 01 - Data Exploration
**Purpose:** Initial data loading and exploration

**What You'll See:**
- Sample count and resolution
- Raw biome distribution (pie chart)
- Height distribution (histogram)
- Spatial overview (heatmap)
- Basic statistics

**Key Outputs:**
- Understanding of current biome balance
- Identification of problem areas
- Baseline for comparison

---

#### 02 - Sea Level Analysis
**Purpose:** Tune sea level threshold for ocean/land classification

**Interactive Elements:**
- Sea level slider (20-50m)
- Shoreline depth slider (-10 to 0m)
- Live updates of ocean/land percentages

**What You'll Learn:**
- Optimal sea level threshold
- Impact of threshold changes
- Shoreline gradient behavior

**Typical Finding:**
> "Current 30m threshold misclassifies 18,985 samples (1.8%) as Ocean when they're actually above-water land. Raising to 35m reduces this to 2,341 samples."

---

#### 03 - Polar Filter Tuning
**Purpose:** Optimize polar biome filter parameters

**Interactive Elements:**
- Polar threshold slider (5000-9000m)
- Outer ring min/max sliders
- Mistlands recovery rate display

**What You'll Learn:**
- How polar threshold affects Mistlands recovery
- Trade-off between polar crescent purity and Mistlands coverage
- Optimal balance point

**Typical Finding:**
> "Polar threshold of 7500m recovers 285k samples to Mistlands (27.2% of world) while maintaining clear polar crescents. Current 7000m threshold leaves too much contamination in non-polar quadrants."

---

#### 04 - Noise Threshold Analysis
**Purpose:** Simulate different biome noise threshold effects

**What You'll Explore:**
- Current thresholds (Swamp=0.6, others=0.4)
- Estimated impact of lowering thresholds
- Biome coverage projections

**Limitations:**
- **Cannot regenerate actual noise** (would require C# plugin rebuild)
- **Can estimate impact** based on threshold pass rates
- **Recommendations only** - requires plugin modification to implement

**Typical Finding:**
> "Lowering Swamp threshold from 0.6 → 0.5 would increase coverage by ~50% (2.97% → 4.5%), bringing it in line with expected distribution."

---

#### 05 - Filter Comparison
**Purpose:** Compare multiple filter strategies side-by-side

**What You Can Compare:**
- Raw API data (no filters)
- Current filters (renderer.js)
- Alternative strategies
- Custom combinations

**Interactive Elements:**
- Checkboxes to enable/disable filters
- Parameter override sliders
- Side-by-side visualizations

**Key Output:**
- Statistical comparison table
- Visual diff heatmaps
- Recommendation summary

---

#### 06 - Heightmap Visualization
**Purpose:** Terrain height analysis and 3D visualization

**What You'll See:**
- 3D terrain surface
- Contour lines
- Slope analysis
- Height vs biome correlation

**Interactive Elements:**
- 3D rotation controls
- Contour interval slider
- Height range filters

**Use Cases:**
- Understand terrain topology
- Validate height data accuracy
- Identify unusual elevation patterns

---

#### 07 - Parameter Export
**Purpose:** Export optimized parameters back to code

**What It Does:**
- Reviews all tuned parameters
- Generates JavaScript code for `renderer.js`
- Creates JSON config files
- Documents changes made

**Outputs:**
```javascript
// Generated JavaScript snippet:
const FILTER_THRESHOLDS = {
    outer_ring_min: 6000,
    outer_ring_max: 10000,
    polar_threshold: 7500,  // Optimized from 7000
    sea_level: 35           // Optimized from 30
};
```

---

## 💡 Common Patterns

### Loading Data

**Always use `load_samples()` from `biome_utils.py`:**

```python
from biome_utils import load_samples

# Load sample data
df = load_samples('../output/samples/hkLycKKCMI-samples-1024.json')

# Data is now a pandas DataFrame with columns:
# - X, Z: World coordinates (meters)
# - Biome: Biome ID (1, 2, 4, 8, 16, 32, 64, 256, 512)
# - Height: Terrain height (meters)
# - Distance: Distance from center (computed)
```

---

### Applying Filters

**Chain filters for complex transformations:**

```python
from biome_utils import *

# Apply multiple filters in sequence
df_transformed = (df
    .pipe(apply_ocean_land_fix, sea_level=30)
    .pipe(apply_polar_water_fix, sea_level=30)
    .pipe(apply_mistlands_recovery, polar_threshold=7000)
)

# Compare before/after
print(f"Mistlands before: {count_biome(df, 64)}")
print(f"Mistlands after: {count_biome(df_transformed, 64)}")
```

---

### Visualization

**Use consistent plotting functions:**

```python
from biome_utils import plot_biome_distribution, plot_spatial_heatmap

# Distribution pie chart
plot_biome_distribution(df, "Raw API Data")

# Spatial heatmap for specific biome
plot_spatial_heatmap(df, biome_id=64, title="Mistlands Distribution")

# Height histogram
plot_height_histogram(df)
```

---

### Interactive Widgets

**Use `@interact` for parameter tuning:**

```python
from ipywidgets import interact, IntSlider

@interact(polar_threshold=IntSlider(min=5000, max=9000, step=500, value=7000))
def test_polar_filter(polar_threshold):
    # Apply filter with current slider value
    df_filtered = apply_mistlands_recovery(df, polar_threshold=polar_threshold)

    # Show results
    plot_biome_distribution(df_filtered, f"Polar Threshold: {polar_threshold}m")

    # Print statistics
    mistlands_pct = count_biome(df_filtered, 64) / len(df_filtered) * 100
    print(f"Mistlands: {mistlands_pct:.1f}% of world")
```

**Result:** Move slider → instant visual update + statistics

---

### Comparing Distributions

**Side-by-side comparison:**

```python
from biome_utils import compare_distributions

# Compare two DataFrames
stats_raw, stats_filtered = compare_distributions(df_raw, df_filtered)

# Output:
# | Biome       | Raw %  | Filtered % | Change   |
# |-------------|--------|------------|----------|
# | Mistlands   | 5.5%   | 19.0%      | +13.5% ↑ |
# | DeepNorth   | 31.1%  | 0.0%       | -31.1% ↓ |
# | ...         | ...    | ...        | ...      |
```

---

## 🔧 Troubleshooting

### "Module not found: biome_utils"

**Cause:** Running notebook from wrong directory

**Fix:**
```bash
# Must be in notebooks/ directory
cd procedural-export/notebooks
jupyter notebook
```

**Or add to notebook:**
```python
import sys
sys.path.append('.')  # Add current directory to path
```

---

### "Sample file not found"

**Cause:** Sample data doesn't exist or path is wrong

**Fix:**
```bash
# Check if file exists
ls ../output/samples/hkLycKKCMI-samples-1024.json

# Or use absolute path
from pathlib import Path
SAMPLE_PATH = Path('/home/steve/projects/valhem-world-engine/procedural-export/output/samples/hkLycKKCMI-samples-1024.json')
df = load_samples(str(SAMPLE_PATH))
```

---

### "Widget not displaying"

**Cause:** ipywidgets not installed or enabled

**Fix:**
```bash
# Install ipywidgets
pip install ipywidgets

# Enable extension (Jupyter Notebook)
jupyter nbextension enable --py widgetsnbextension

# For JupyterLab, also install:
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```

---

### "Plot not showing"

**Cause:** Matplotlib backend issue

**Fix:**
```python
# Add to top of notebook
%matplotlib inline

# Or for interactive plots:
%matplotlib widget
```

---

### "Slow performance"

**Cause:** Large dataset, unoptimized operations

**Fixes:**
```python
# 1. Use smaller sample for testing
df_small = df.sample(n=10000)  # Random 10k samples

# 2. Cache expensive computations
from functools import lru_cache

# 3. Use NumPy instead of Python loops
# Bad:
for i, row in df.iterrows():  # SLOW
    ...

# Good:
df['NewColumn'] = df['X'] ** 2  # FAST (vectorized)
```

---

## 🎓 Advanced Usage

### Custom Filter Development

**Create your own filter function:**

```python
def apply_custom_filter(df, param1=100, param2=0.5):
    """
    Custom filter: Your logic here

    Args:
        df: Input DataFrame
        param1: Description
        param2: Description

    Returns:
        Filtered DataFrame
    """
    df = df.copy()  # Always copy to avoid modifying original

    # Your transformation logic
    mask = (df['Height'] > param1) & (df['Distance'] < param2)
    df.loc[mask, 'Biome'] = 64  # Example: Convert to Mistlands

    return df

# Use in pipeline
df_custom = df.pipe(apply_custom_filter, param1=150, param2=0.6)
```

---

### Batch Analysis (Multiple Seeds)

**Analyze multiple worlds:**

```python
from pathlib import Path

# Find all sample files
sample_files = Path('../output/samples/').glob('*-samples-1024.json')

results = {}
for sample_file in sample_files:
    world_name = sample_file.stem.split('-')[0]
    df = load_samples(str(sample_file))

    # Analyze
    df_filtered = apply_all_filters(df)
    mistlands_pct = count_biome(df_filtered, 64) / len(df_filtered) * 100

    results[world_name] = mistlands_pct

# Compare results across worlds
print(results)
```

---

### Exporting Analysis Results

**Save results to file:**

```python
# Save DataFrame to CSV
df_filtered.to_csv('filtered_biomes.csv', index=False)

# Save statistics to JSON
import json

stats = calculate_biome_distribution(df_filtered)
with open('biome_stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

# Save figure
import matplotlib.pyplot as plt

fig = plot_biome_distribution(df_filtered, "Final Result")
fig.savefig('biome_distribution.png', dpi=300, bbox_inches='tight')
```

---

## 📊 Expected Results

### Typical Analysis Findings

Based on `hkLycKKCMI` world (1,048,576 samples):

**Raw API Data:**
- DeepNorth: 31.07% (over-represented)
- Ashlands: 15.62% (over-represented)
- Mistlands: 5.50% (**under-represented**)
- Ocean: 18.01%

**After Optimal Filters:**
- DeepNorth: ~20% (polar crescent in far north)
- Ashlands: ~1% (polar crescent in far south)
- Mistlands: ~27% (**recovered!**)
- Ocean: ~50% (includes edge water)

**Improvement:** Mistlands goes from 5.5% → 27% (491% increase)

---

## 🤝 Contributing

### Adding New Notebooks

When creating new analysis notebooks:

1. **Keep focused** - One purpose per notebook
2. **Use shared utilities** - Import from `biome_utils.py`
3. **Follow naming** - `NN_descriptive_name.ipynb`
4. **Add documentation** - Start with purpose/scope section
5. **Include examples** - Show expected outputs
6. **Update README** - Add to notebook guide above

**Template:**
```python
"""
Notebook: 08_new_analysis.ipynb
Purpose: Brief description of what this notebook does
Scope: What's included and what's NOT

Prerequisites:
- List prerequisites here

Outputs:
- What users will get

Estimated Time: X minutes
"""

# Standard setup (copy from other notebooks)
# ... imports, load data, etc.

# Your analysis here
```

---

### Updating Shared Code

**If you modify `biome_utils.py` or `config.py`:**

1. **Test all notebooks** - Ensure changes don't break existing analysis
2. **Update docstrings** - Keep documentation current
3. **Add tests** - If adding new functions
4. **Increment version** - Add note in comments about what changed

---

## 📖 Reference Documentation

### Related Files
- **Decompiled Code:** `../decompiled/WorldGenerator.decompiled.cs`
- **Filter Implementation:** `../client/renderer.js`
- **Sample Data:** `../output/samples/`
- **Analysis Reports:** `../BIOME_DECISION_ANALYSIS_REPORT.md`
- **Recent Fixes:** `../MISTLANDS_RECOVERY_FIX.md`

### External Resources
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Gallery](https://matplotlib.org/stable/gallery/)
- [Jupyter Widgets](https://ipywidgets.readthedocs.io/)
- [Seaborn Tutorial](https://seaborn.pydata.org/tutorial.html)

---

## ⏱️ Performance Tips

### Speed Comparisons

| Operation | Old Method | New Method | Speedup |
|-----------|------------|------------|---------|
| Parameter change | Rebuild Docker + regenerate samples | Adjust slider in notebook | **~100x** |
| Visual comparison | Export → viewer → refresh | Cell re-run | **~50x** |
| Testing 10 values | 150-200 minutes | 50-100 seconds | **~120x** |

### Optimization Strategies

1. **Cache loaded data** - Load once, use many times
2. **Use vectorized operations** - NumPy/Pandas, not Python loops
3. **Sample for exploration** - Use subset for parameter tuning, full set for final validation
4. **Limit plot resolution** - 512×512 sufficient for visual inspection
5. **Profile slow cells** - Use `%%time` magic to identify bottlenecks

---

## 🎯 Success Metrics

**You've successfully used these notebooks when:**

- ✅ You can test a parameter change in < 10 seconds
- ✅ You understand the impact of each filter
- ✅ You've found optimal parameters for your use case
- ✅ You've exported results to `renderer.js`
- ✅ Visual map quality improved vs reference images

---

## 📝 License & Credits

Part of the Valheim World Engine (VWE) project.

**Data Source:** Valheim WorldGenerator API (lloesche/valheim-server Docker image)
**Decompiled Code:** ILSpy extraction from `assembly_valheim.dll`
**Analysis Framework:** Created for procedural-export biome classification optimization

---

## 💬 Questions?

See the main project documentation:
- `../README.md` - Project overview
- `../BIOME_REFERENCE.md` - Biome constants and thresholds
- `../BIOME_DECISION_ANALYSIS_REPORT.md` - Detailed decision tree analysis

For issues with notebooks specifically, check the Troubleshooting section above.

---

**Happy Analyzing! 🗺️**
