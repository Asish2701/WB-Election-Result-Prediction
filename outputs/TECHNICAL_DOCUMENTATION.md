# Margin Squeeze Analysis - Technical Documentation

## Overview

This document describes the methodology and implementation of the West Bengal 2026 election margin squeeze analysis, which quantifies how four major political developments impact TMC winning probabilities and seat predictions.

## 1. Squeeze Factor Components

Each constituency is assigned squeeze factors across four dimensions:

### 1.1 Voter Roll Purge Squeeze (`purge_squeeze`)

**Mechanism:** Special Intensive Revision (S.I.R.) deletion of voters from electoral rolls

**Geographic impact model:**
```python
Purge Squeeze by District:
  Murshidabad: 35%  # Lost 12.5 lakh voters; exceeds margins in 50+ seats
  Maldah:      30%  # Lost 10+ lakh voters
  Uttar Dinajpur: 28%  # Lost 7+ lakh voters  
  Dakshin Dinajpur: 15%  # Moderate impact
  Other districts: 5%  # Baseline default
```

**Rationale:** 
- Purge disproportionately affected minority-heavy constituencies (TMC strongholds)
- In 140+ constituencies, deleted voters > 2021 winning margin
- Historical voter lists show 2021 voters no longer in 2026 rolls

### 1.2 RG Kar Medical College Case Squeeze (`rgkar_squeeze`)

**Mechanism:** Symbolic candidacy of victim's mother (Ratna Debnath) from Panihati; disillusionment among women voters

**Geographic impact model:**
```python
if Constituency == Panihati (AC 111):
  RG Kar Squeeze = 12%  # Direct impact from symbolic candidacy

elif District in [Kolkata, North 24 PG, South 24 PG]:
  RG Kar Squeeze = 5%   # Urban women voter base more affected
  
else:
  RG Kar Squeeze = 2%   # Rural women voter impact lower
```

**Rationale:**
- Women ~49% of voters; traditionally TMC-aligned
- RG Kar case frame: "justice for victim" vs. "law & order"
- Urban women voters (higher education, social media exposure) more aware/affected
- Panihati specifically targeted; neighboring constituencies spillover effect

### 1.3 Corruption & Lawlessness Narrative Squeeze (`corruption_squeeze`)

**Mechanism:** PM Modi, Rajnath Singh frame election as "cut money culture vs. law & order"; gherao of judicial officers in Maldah; industrial flight narrative

**Geographic impact model:**
```python
Corruption Squeeze by District:
  Maldah:                   12%  # Gherao incident; symbolic
  Barddhaman (Industrial):   8%  # Asansol, Durgapur Belt
  Hugli (Industrial):        6%  # Hooghly industrial corridor
  North 24 Parganas:         4%  # Business/trading hub; mixed political base
  Kolkata:                   3%  # Professional class sensitive to governance
  Other districts:           2%  # Baseline default
```

**Rationale:**
- Industrial voters particularly receptive to "investor flight" narrative
- Border district residents sensitive to security/governance concerns
- Urban professionals in metros more engaged with "cut money" accusations

### 1.4 Sandeshkhali Aftermath Squeeze (`sandeshkhali_squeeze`)

**Mechanism:** Incarceration of Sheikh Shahjahan (TMC local strongman); removal of voter intimidation; freed opposition voters

**Geographic impact model:**
```python
if Constituency == Sandeshkhali (AC 123):
  Sandeshkhali Squeeze = 15%  # Epicenter; maximum impact

elif District == North 24 Parganas:
  Sandeshkhali Squeeze = 8%   # Riverine constituencies, neighboring areas

elif District == South 24 Parganas:
  Sandeshkhali Squeeze = 4%   # Some riverine areas affected

else:
  Sandeshkhali Squeeze = 1%   # Minimal spillover
```

**Rationale:**
- Sheikh Shahjahan was enforcer of TMC dominance through intimidation
- His incarceration is first time in decades residents could vote "freely"
- Effect concentrated in riverine constituencies with strong TMC local control
- Opposition (BJP) beneficiary of freed voters

---

## 2. Aggregate Squeeze Calculation

### 2.1 Component Summation

For each constituency:
$$\text{Total Squeeze} = \text{Purge} + \text{RG Kar} + \text{Corruption} + \text{Sandeshkhali}$$

**Capping mechanism:**
$$\text{Total Squeeze}_{\text{final}} = \min(\text{Total Squeeze}, 0.25)$$

**Rationale for 25% cap:**
- Realism constraint: margin squeeze cannot exceed 25% even in worst-case constituencies
- Prevents model from predicting implausibly large probability shifts
- Acknowledges that voters respond to multiple factors but not in perfectly additive manner

### 2.2 Example Calculations

**Panihati (AC 111) - Worst Case:**
```
Purge Squeeze:        5% (North 24 Parganas, not in high-purge district)
RG Kar Squeeze:      12% (Direct impact - RG Kar case epicenter)
Corruption Squeeze:   4% (North 24 Parganas)
Sandeshkhali Squeeze: 8% (North 24 Parganas, neighboring Sandeshkhali)
─────────────────────────
Intermediate Total:  29%
Final Total:         25% (capped)
```

**Suti (AC 57, Murshidabad) - Purge-Heavy:**
```
Purge Squeeze:       35% (Murshidabad high-purge district)
RG Kar Squeeze:       2% (Rural)
Corruption Squeeze:   2% (Non-industrial)
Sandeshkhali Squeeze: 1% (Not in N-24PG/S-24PG)
─────────────────────────
Intermediate Total:  40%
Final Total:         25% (capped)
```

---

## 3. Probability Adjustment Mechanism

### 3.1 Core Algorithm

For each constituency with squeeze factor $s$:

**TMC probability reduction (30% retained):**
$$P_{\text{TMC, adjusted}} = P_{\text{TMC, baseline}} \times (1 - s \times 0.70)$$

**BJP probability increase (70% of TMC loss):**
$$P_{\text{BJP, adjusted}} = P_{\text{BJP, baseline}} + (P_{\text{TMC, baseline}} \times s \times 0.70)$$

**OTHER probability increase (30% of TMC loss):**
$$P_{\text{OTHER, adjusted}} = P_{\text{OTHER, baseline}} + (P_{\text{TMC, baseline}} \times s \times 0.30)$$

**Renormalization:**
$$P_{\text{party, normalized}} = \frac{P_{\text{party, adjusted}}}{\sum P_{\text{all parties, adjusted}}}$$

### 3.2 Interpretation

- **70% go to BJP:** Primary beneficiary of TMC losses (oppositional dynamics)
- **30% go to OTHER/abstention:** Some voters abstain or scatter to smaller parties
- **Renormalization:** Ensures probabilities sum to 1.0

### 3.3 Example Probability Adjustment

**Burdwan Dakshin (AC 260) - Corruption Narrative Impact:**

**Baseline probabilities:**
- P_TMC = 0.5742 (57.4%)
- P_BJP = 0.4114 (41.1%)
- P_OTHER = 0.0144 (1.4%)

**Squeeze factor:** s = 0.08 (8% - Barddhaman industrial district)

**Adjusted probabilities (before renormalization):**
- P_TMC = 0.5742 × (1 - 0.08 × 0.70) = 0.5742 × 0.944 = 0.5420 (54.2%)
- P_BJP = 0.4114 + (0.5742 × 0.08 × 0.70) = 0.4114 + 0.0322 = 0.4436 (44.4%)
- P_OTHER = 0.0144 + (0.5742 × 0.08 × 0.30) = 0.0144 + 0.0138 = 0.0282 (2.8%)
- Total = 0.5420 + 0.4436 + 0.0282 = 1.0138

**After renormalization:**
- P_TMC = 0.5420 / 1.0138 = 0.5345 (53.4%)
- P_BJP = 0.4436 / 1.0138 = 0.4374 (43.7%)
- P_OTHER = 0.0282 / 1.0138 = 0.0278 (2.8%)
- **Winner**: TMC (but probability reduced from 57.4% to 53.4%)

---

## 4. Model Outputs

### 4.1 Generated Files

| File | Format | Content |
|------|--------|---------|
| `wb_2026_margin_squeeze_analysis.csv` | CSV | Squeeze factors by constituency |
| `wb_2026_adjusted_for_squeeze.csv` | CSV | Adjusted probabilities and predictions |
| `wb_2026_adjusted_tally.csv` | CSV | Aggregate seat tally (TMC/BJP/OTHER) |
| `wb_2026_squeeze_flips.csv` | CSV | Constituencies where predicted winner changes |
| `wb_2026_comprehensive_risk_report.csv` | CSV | Full risk assessment with both baselines |

### 4.2 Key Output Metrics

**Party-Level Tally:**
```
Party,Seats
All India Trinamool Congress,194
Bharatiya Janta Party,98
OTHER,2
```

**Seat Changes:**
- TMC: 197 → 194 (-3 seats)
- BJP: 95 → 98 (+3 seats)
- Net: 3-seat swing to BJP

---

## 5. Validation & Sensitivity Analysis

### 5.1 Sanity Checks Implemented

1. **Squeeze factor range:** All final squeeze factors ≤ 25% (capped)
2. **Geographic coverage:** All 294 constituencies assigned squeeze factors
3. **Probability conservation:** Probabilities renormalize to sum = 1.0 per seat
4. **Winner logic:** Predicted winner = argmax(P_TMC, P_BJP, P_OTHER)
5. **Tally consistency:** Sum of individual winner predictions = party seat totals

### 5.2 Sensitivity Considerations

**If purge impact is overstated:**
- Squeeze reduces to ~18%, primarily from RG Kar + corruption + Sandeshkhali
- Tally would be TMC 196, BJP 96 (only 1-seat swing)

**If Sandeshkhali impact is understated:**
- Current model applies only to N-24PG; if state-wide, squeeze increases
- Could push 2-3 additional constituencies to BJP

**If women voter response to RG Kar is lower:**
- Squeeze reduces by 2-5% in urban constituencies
- 1-2 additional seats retained by TMC

---

## 6. Interpretation Guidance

### 6.1 When Squeeze Factors Are High

**Constituencies with 25% squeeze:**
- Multiple negative factors compounded (e.g., Panihati: RG Kar + Sandeshkhali + urban corruption narrative)
- Baseline winner probability should be viewed as **upper bound**
- Actual outcome likely lower; may flip to runner-up if margin <5%

### 6.2 When Squeeze Factors Are Low (5%)

**Constituencies with low squeeze:**
- Primarily from default baseline values
- Minimal evidence of vulnerability
- Baseline predictions more reliable

### 6.3 District-Level Patterns

**High squeeze districts (Murshidabad, Maldah, Uttar Dinajpur):**
- Expect 2-3 TMC seat losses in each
- Most vulnerable: seats with <30% 2021 margin

**Low squeeze districts (Darjiling, Jalpaiguri, Birbhum):**
- Baseline predictions hold; minimal adjustment needed

---

## 7. Implementation Details

### 7.1 Python Implementation

**Key modules:**
```python
from src.model.margin_squeeze_analysis import (
    analyze_squeeze(),           # Calculate squeeze factors
    apply_squeeze_adjustments(), # Apply to probabilities
    generate_adjusted_predictions()  # Create output files
)
```

**Core functions:**
- `_identify_purge_vulnerable()` - District-based purge squeeze
- `_identify_rgkar_vulnerable()` - AC & district-based RG Kar squeeze
- `_identify_corruption_narrative_vulnerable()` - District-based corruption squeeze
- `_identify_sandeshkhali_vulnerable()` - AC & district-based Sandeshkhali squeeze
- `_aggregate_squeeze_factor()` - Sum with 25% cap
- `apply_squeeze_adjustments()` - Probability modification algorithm

### 7.2 Running the Analysis

```bash
python -m src.model.margin_squeeze_analysis
```

**Output:**
- Loads calibrated predictions
- Calculates squeeze factors
- Applies adjustments
- Generates CSVs and summary statistics

---

## 8. Limitations & Caveats

1. **Historical data assumption:** Assumes 2021 voting patterns hold despite demographic shifts
2. **Narrative effect assumption:** Assumes narratives translate uniformly to vote share shifts
3. **No interaction terms:** Model does not capture how factors interact (e.g., overlapping effects)
4. **Candidate effects not included:** Strong/weak nominees not separately modeled
5. **Campaign dynamics:** Cannot predict election-eve developments
6. **Media coverage:** Media amplification of these narratives not quantified
7. **Cross-cutting identities:** Assumes voters respond primarily to one narrative dimension

---

## 9. Comparison with Baseline Model

| Dimension | Baseline | Squeeze-Adjusted | Difference |
|-----------|----------|------------------|-----------|
| TMC seats | 197 | 194 | -3 |
| BJP seats | 95 | 98 | +3 |
| TMC majority cushion | 22 | 19 | -3 |
| Concentrated risk | Low | High | In Murshidabad, Maldah |
| High-risk seats | 0 | 13 | Panihati, Sandeshkhali, Suti, etc. |

---

## 10. Recommendations for Use

**For analysts:**
- Use as **sensitivity test**, not primary prediction
- Cross-reference with exit polls when available
- Monitor actual vote counts in high-squeeze constituencies

**For stakeholders:**
- View 194-seat prediction as **realistic floor**, not ceiling
- Assume additional uncertainty from unmeasured factors
- 19-seat majority still comfortable but less secure than 22-seat baseline

**For election night:**
- Watch Murshidabad (9 seats) and Maldah (5 seats) early
- If TMC underperforms in these, expect cascading losses
- Barddhaman (19 seats) is bellwether for industrial narrative

---

**Model Version:** 1.0  
**Last Updated:** May 1, 2026  
**Next Update:** Post-election validation (May 5, 2026)
