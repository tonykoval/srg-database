# Constructed SRG catalogs (graph6)

Strongly regular graphs constructed by cascading Godsil–McKay switching (see [`../paper/`](../paper/)),
bundled in **`srg_constructed_catalogs.tar.gz`** (one graph per line, **graph6** format).

```bash
tar xzf srg_constructed_catalogs.tar.gz
```

| File (inside the archive) | Parameter | Graphs | Note |
|---|---|---|---|
| `new_srg_50_21_8_9.g6` | SRG(50,21,8,9) | 16,939 | full catalog (cascade saturated) |
| `new_srg_50_28_15_16.g6` | SRG(50,28,15,16) | 16,939 | full catalog (complements) |
| `sample_srg_49_24_11_12.g6` | SRG(49,24,11,12) | 2,000 | sample — full catalog 379,000+ and still growing |
| `sample_srg_57_24_11_9.g6` | SRG(57,24,11,9) | 2,000 | sample — full catalog 209,000+ and still growing |

Load with nauty (`labelg`, `dreadnaut`), SageMath (`Graph(line, format="graph6")`), networkx, etc.

Every graph was verified valid (degree, λ, μ) and asymmetric (`|Aut|` = 1, except 48 of the
SRG(50,21,8,9) graphs which have `|Aut|` = 2). The two large families (SRG(49,24,11,12) exceeds
70 MB and is still growing) are shipped here only as samples; the full catalogs are regenerable
from the seeds and scripts in the [orbit-gen](https://github.com/tonykoval/orbit-gen) repository,
or available on request.

*(The graphs are bundled as a compressed archive because raw graph6 text — random-looking ASCII —
trips GitHub's secret-scanning false positives.)*

## Quick check (SageMath)

```python
for line in open("new_srg_50_21_8_9.g6"):
    G = Graph(line.strip(), format="graph6")
    assert G.is_strongly_regular(parameters=True) == (21, 8, 9)   # (k, λ, μ)
```
