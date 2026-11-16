# VA-ECMO Optimal Stopping Model

## Optimal Stopping Model for VA-ECMO Liberation Based on LVOT VTI Derived Latent Physiological Reserve Across Competing Hemodynamic Regimes

**Literature-parameterized computational proof-of-concept, reproducible simulation, uncertainty analysis, and mathematical decision modeling**

![Status](https://img.shields.io/badge/status-theoretical%20proof--of--concept-blue) ![Python](https://img.shields.io/badge/Python-reproducible%20simulation-3776AB) ![Validation](https://img.shields.io/badge/clinical%20validation-not%20performed-lightgrey)

> **Manuscript availability.** The full manuscript is currently retained by the author because this study has not been formally published and may undergo further revision or collaboration. This public repository provides the computational materials (such as input parameter and outputs) and a manuscript outline. It should not be represented as a published or peer reviewed clinical study. For any collaboration, discussion or suggestion, kindly contact the author by Github.

---

## Overview

Liberation from venoarterial extracorporeal membrane oxygenation (VA-ECMO) requires repeated evaluation of native cardiac recovery while weighing the modeled consequences of premature liberation against continued extracorporeal support. Left ventricular outflow tract velocity time integral (LVOT VTI) is a relevant echocardiographic measurement, but it depends on loading and support conditions and cannot uniquely describe underlying recovery mechanisms.

This repository studies that sequential decision using four bounded nonlinear ordinary differential equations (ODEs), a simulated LVOT VTI observation layer, a model defined feasibility score and hazard like penalty, a supplementary four state continuous time Markov chain (CTMC), and finite horizon Bellman recursion.

The problem is **when the specified model first favors liberation over continued support while simultaneously satisfying all modelled eligibility constraints**. And the answer is conditional on provisional assumptions and is **not a clinical decannulation recommendation**.

## Background

**Literature-parameterized mathematical proof-of-concept, no patient level calibration or external validation.** Published literature informs clinical context and the illustrative LVOT VTI eligibility anchor. Most ODE coefficients, observation weights, CTMC intensities, hazard parameters, and decision utilities are provisional model inputs, not fitted biological constants.

- No individual patient outcomes were fitted, and no clinical treatment effect or survival benefit was estimated.
- The seven day simulation begins at a **hypothetical first formal readiness assessment**, not at ECMO cannulation.
- The simulated feasibility score is **not** an observed probability of successful decannulation.
- The hazard like term is **not** a fitted clinical event rate.
- The 9.5 cm LVOT VTI reference is an illustrative literature-parameterized eligibility literatures, **not** a validated cutoff.

---

## 1. Mathematical statements

A single LVOT VTI value can coexist with different combinations of physiological reserve, oxygen debt, support dependence, and hemodynamic stability. The model separates **observable measurements**, **assumed latent physiology**, **risk related decision quantities**, and **the choice to stop or continue support**.

Nonlinear dynamical systems describe the assumed recovery trajectory, local stability analysis examines equilibria under fixed inputs, CTMC dynamics summarize illustrative regime occupancy, and optimal stopping theory formalizes the sequential stop versus continue comparison. The financial engineering connection is the **mathematics of finite horizon sequential decisions**.

## 2. Parameters and Variables

All four physiological states are dimensionless and constrained to `[0, 1]`.

| Symbol | Model state | Interpretation |
|---|---|---|
| `R(t)` | Physiological reserve | Latent model construct representing recovery capacity |
| `D(t)` | Oxygen debt | Accumulated physiological burden |
| `A(t)` | Support dependence | Dependence on ECMO support and related vulnerability |
| `H(t)` | Hemodynamic stability | Model-defined stability state |

The prescribed recovery drive and support fraction are:

```text
G(t) = 0.34 + (0.82 - 0.34) exp(-0.18t)
S(t) = 0.82 - 0.35[1 - exp(-0.38t)]
```

The reference initial state is `X(0) = [0.34, 0.48, 0.62, 0.46]` in the order `[R, D, A, H]`. These inputs are not reconstructed from clinical flow records.

## 3. Nonlinear ODE System

```text
dR/dt = k_reserve_gain G(t)(1-R) - k_debt_inhibit D R - k_depend_inhibit A R

dD/dt = k_debt_gen(1-R)(1-D) - k_debt_clear R D

dA/dt = k_depend_gain S(t)(1-R)(1-A) - k_depend_release R A

dH/dt = k_stability_gain R(1-H)
        - k_stability_loss_debt D H - k_stability_loss_depend A H
```

The model's inward pointing boundary structure supports positivity and boundedness. The coefficients and parameters are documented in `data/Model_Parameters.csv`  where these files are included in the published repository files.

## 4. LVOT VTI Observation and Decision Quantities

The **implemented** observation equation is deterministic: simulated physiological states generate simulated VTI, no measured echocardiographic series is used to estimate the latent states.

```text
VTI(t) = 7.70 + 5.00 R(t) + 0.80 H(t) - 1.20 A(t)  [cm]

pi_L(t) = logistic[-4.40 + 0.48 VTI + 1.60 R + 1.00 H - 0.80 D - 0.60 A]

Psi(t) = 0.75 R + 0.35 H - 0.45 D - 0.35 A + 0.07(VTI - 9.5) - 0.28

lambda_F(t) = 0.035 exp(1.15 D + 0.80 A - 1.20 R - 0.85 H)
```

Here `pi_L` is a **model implied feasibility score**, `Psi` is the liberation margin, and `lambda_F` is a **provisional hazard like penalty**.

## 5. Finite Horizon Optimal Stopping

The model evaluates days `0` to `7` in increments of `0.05` days. Immediate liberation and continuation are compared using:

```text
U_L(t) = 2.60 pi_L - 1.80(1-pi_L) - 0.50 D - 0.35 A + 0.45 H - 0.18

C(t) = [0.14 + 0.055 D + 0.035 A + 0.30 lambda_F] Delta_t

U_C(t_i) = exp(-0.015 Delta_t) V(t_(i+1)) - C(t_i)

V(t_i) = max{U_L(t_i), U_C(t_i)}
V(7) = U_L(7)
```

The **first admissible stopping grid point** must satisfy **all five implemented conditions**:

1. `U_L >= U_C - 1e-10`
2. `Psi >= 0`
3. `VTI >= 9.5 cm`
4. `H >= 0.55`
5. `pi_L >= 0.65`

This is a deterministic Bellman calculation for each simulated trajectory, not a patient fitted stochastic control policy. The CTMC occupancy probabilities are descriptive and do **not** enter this stopping rule.

## 6. Four State CTMC Layer

A supplementary state dependent CTMC represents:

- Support dependent
- Recovering
- Liberation ready
- Relapse risk

Its generator depends on modelled favourable state, stress, margin, and hazard. The code propagates the regime probability vector using an **explicit Euler update with clipping and normalization**. These are simulated occupancies, not observed patient state frequencies.

## 7. Mathematical Analysis

The mathematical analysis include positivity and boundedness, three numerical equilibria under separately fixed recovery drive and support environments, centered finite difference Jacobians, eigenvalue based on **local** stability classification, and a reduced reserve oxygen debt phase plane slice.

| Fixed environment | Reserve `R` | Debt `D` | Dependence `A` | Stability `H` | VTI (cm) | Max Re(eigenvalue) |
|---|---:|---:|---:|---:|---:|---:|
| Decompensated | 0.114 | 0.770 | 0.725 | 0.155 | 7.522 | -0.098 |
| Compensated | 0.291 | 0.511 | 0.417 | 0.429 | 8.996 | -0.061 |
| Recovery dominant | 0.687 | 0.163 | 0.104 | 0.858 | 11.696 | -0.016 |

Negative maximum real eigenvalues support local asymptotic stability **only for the corresponding fixed autonomous systems**. The two dimensional phase plane is a conditional visualization, **no numerical basin of attraction estimate was performed**.

## 8. Numerical Solutions

| Component | Implemented setting |
|---|---|
| Reference horizon | 7 days from hypothetical readiness assessment |
| Decision/output grid | 0.05 day |
| Reference ODE solver | SciPy `solve_ivp`, RK45 |
| Reference tolerances | `rtol=1e-9`, `atol=1e-11` |
| Numerical checks | DOP853 and fixed-step RK4 |
| Prespecified scenarios | 9 |
| Latin-hypercube structural samples | 500 sets across 15 provisional parameters |
| Global sensitivity | PRCC of terminal liberation margin |
| Local elasticity | Symmetric ±1% parameter changes |
| Structural/initial state perturbation ensemble | 500 independently perturbed inputs |
| Synthetic internal model comparison | 800 model scenarios, five logistic feature sets |
| Practical identifiability | Serial VTI sensitivity matrix, four selected rates, SVD |
| Random seed | `20260824` |

The 500 run perturbation ensemble randomly varies inputs before integrating each deterministic trajectory, it does **not** solve a continuous time stochastic differential equation.

## 9. Reference Recovery and Stopping Result

The reference trajectory shows rising reserve and stability, falling oxygen debt and support dependence, and increasing simulated LVOT VTI.

| Output at first admissible stopping time | Model result |
|---|---:|
| Stopping time | **Day 3.65** |
| LVOT VTI | **10.68 cm** |
| Reserve `R` | 0.601 |
| Oxygen debt `D` | 0.341 |
| Support dependence `A` | 0.390 |
| Hemodynamic stability `H` | 0.551 |
| Liberation margin `Psi` | 0.156 |
| Model-implied feasibility `pi_L` | 0.850 |
| Hazard-like term `lambda_F` | 0.0215 |

**Interpretation:** The model first satisfies the Bellman comparison **and** all eligibility constraints at day 3.65. Reaching the VTI anchor alone is insufficient. 

## 10. Scenario Analysis

All nine prespecified scenarios reached an admissible stopping boundary within seven days. Selected results:

| Scenario | First stopping day |
|---|---:|
| Reference | 3.65 |
| Faster myocardial recovery | 3.40 |
| Slower myocardial recovery | 4.65 |
| Persistent oxygen debt | 4.00 |
| Rapid oxygen-debt resolution | 3.75 |
| High support dependence | 3.90 |
| Low support dependence | 3.70 |
| Hemodynamic fragility | 6.75 |
| Lower recovery volatility proxy | 3.65 |

The nonlinear stopping rule means that a physiologically favorable coefficient change does **not** necessarily produce an earlier discrete stopping time. These are model scenarios, not calibrated clinical subgroups or evidence of irreversible injury.

## 11. Uncertainty and Perturbation Results

Two distinct computational experiments were performed:

| Experiment | Reached an admissible boundary | Additional result |
|---|---:|---|
| 500 Latin-hypercube structural samples | 88.2% | Terminal margin median 0.352; empirical 2.5th–97.5th percentiles −0.041 to 0.674 |
| 500 randomized structural/initial state perturbations | 488/500 (97.6%) | Median stopping day 3.75 (IQR 3.35-4.50), median VTI at stop 10.76 cm, median feasibility 0.862 |

The Latin hypercube VTI fan illustrates variation from provisional structural coefficients. It is not a clinical prediction interval or observed patient variability.

## 12. Global Sensitivity and Numerical Robustness

Selected PRCCs with **terminal liberation margin** are:

| Parameter | PRCC |
|---|---:|
| `k_reserve_gain` | +0.952 |
| `margin_R` | +0.874 |
| `k_depend_inhibit` | −0.837 |
| `margin0` | −0.829 |
| `k_debt_inhibit` | −0.810 |
| `k_debt_clear` | +0.808 |
| `k_depend_release` | +0.800 |

The `k_depend_inhibit` parameter represents **inhibition of reserve by support dependence**, not dependence release. Directly defined margin weights naturally influence the margin output; these PRCCs should not be interpreted as independent clinical discoveries.

Reference terminal reserve and VTI were approximately `0.66152` and `11.25715 cm` across the tested solvers. Stopping time was `3.650` days for RK45, DOP853, and RK4 at `0.05`-day steps, versus `3.625` days for RK4 at finer `0.025`- and `0.0125`-day steps. Thus solver agreement is close, but stopping times are sensitive to decision grid resolution.

## 13. Internal Synthetic Model Comparison

Five logistic feature sets were fitted and evaluated **in sample** on model cases. The binary label represented reaching an admissible stopping boundary by day five, with an additional scripted **8% random label flip**. There was **no held out clinical test set**.

| Synthetic feature set | AIC | BIC | Internal AUC | Brier | Accuracy |
|---|---:|---:|---:|---:|---:|
| Full dynamic latent-state | 554.985 | 601.831 | 0.855 | 0.092 | 0.902 |
| Static physiological state | 574.085 | 602.193 | 0.848 | 0.097 | 0.891 |
| VTI plus terminal reserve | 672.785 | 686.839 | 0.773 | 0.128 | 0.835 |
| Dynamic slopes | 713.281 | 732.020 | 0.737 | 0.138 | 0.819 |
| LVOT VTI only | 730.638 | 740.007 | 0.703 | 0.143 | 0.816 |

The full representation best recovers labels generated by the model's own mechanism. **This does not establish superior clinical prediction.**

## 14. Practical Identifiability

Serial simulated LVOT VTI was differentiated with respect to four selected physiological rates, and the sensitivity matrix was analyzed by singular-value decomposition.

```text
Singular values: 13.6156, 1.3759, 0.1427, 0.000567
Condition number: approximately 24,007
```

The large condition number indicates weak local separability of certain parameter combinations **from simulated VTI alone**. It does not prove global non identifiability of the entire model. Longitudinal multimodal calibration is needed before any clinical interpretation.

## 15. Figures

The research package contains ten main figures:

| Figure | Subject |
|---|---|
| 1 | Literature to model computational architecture |
| 2 | Reference recovery trajectory and derived decision quantities |
| 3 | Finite horizon stopping comparison and VTI eligibility anchor |
| 4 | Reduced reserve oxygen debt phase plane |
| 5 | Latin hypercube LVOT VTI uncertainty fan |
| 6 | PRCC sensitivity of terminal liberation margin |
| 7 | Internal synthetic model comparison |
| 8 | Four state CTMC regime occupancy |
| 9 | Exploratory liberation decision surface |
| 10 | VTI only practical identifiability |

**Figure provenance note:** In the uploaded integrated package, Figures 4 and 5 are retained copies of supplied reference PNGs rather than images regenerated from the current CSVs by the revised figure script. Other main figures are produced by the figure workflow. The repository should retain this distinction.

## 16. Repository Structure

The intended public facing organization is:

```text
vaecmo-optimal-stopping-model/
├── README.md
├── CITATION.cff
├── LICENSE                     # if added by the repository owner
├── code/
│   ├── vaecmo_optimal_stopping_model.py
│   └── make_figures.py
├── data/
│   ├── Model_Parameters.csv
│   ├── LHS_Parameter_Samples.csv
│   └── PARAMETER_NOTES.md
├── results/
│   ├── RESULTS_NOTES.md
│   ├── Reference_Trajectory.csv
│   ├── Reference_Equilibria.csv
│   ├── Reference_Eigenvalues.csv
│   ├── Phase_Plane_Reserve_Debt.csv
│   ├── Scenario_Results.csv
│   ├── Uncertainty_Samples.csv
│   ├── Global_Sensitivity_PRCC.csv
│   ├── Local_Elasticity.csv
│   ├── Stochastic_Perturbation_Results.csv
│   ├── Numerical_Robustness.csv
│   ├── Synthetic_Model_Comparison_AIC.csv
│   └── Practical_Identifiability.csv
├── figures/
│   └── Figure_1_...png through Figure_10_...png
└── manuscript/
    ├── manuscript.md
    └── REFERENCES.md
```

**Important:** This is the proposed cleaned GitHub layout, not the literal directory structure of the uploaded integrated ZIP, which stores numerical outputs under `generated_output/`. The actual published file names and paths should be checked after upload. The main script in the integrated ZIP writes to `generated_output/` unless edited or its outputs are subsequently organized into `data/`, `results/`, and `figures/`.

## 17. Installation

Download the repository or clone it using the URL of your actual published VA-ECMO repository. From the repository root, install the scientific Python dependencies used by the scripts:

```bash
python -m pip install numpy pandas scipy matplotlib scikit-learn
```

This list is a practical dependency guide.

## 18. Reproducing the Analysis

**Using the original integrated package layout**:

```bash
python code/vaecmo_optimal_stopping_model.py
```

The integrated package describes generation of numerical outputs and figures. To redraw the figure set from existing output CSVs:

```bash
python code/make_figures.py --data-dir generated_output --output-dir generated_output/figures --originals-dir original_figures
```

**Using the cleaned GitHub layout:** ensure the main script's output paths and the figure script's `--data-dir`, `--output-dir`, and `--originals-dir` arguments correspond to the directories actually uploaded. Do not assume that a reorganization of CSVs alone automatically changes the script's paths. Figures 4 and 5 require their retained source PNGs if using the supplied figure workflow.

For numerical verification, compare generated outputs against the published CSVs and, where retained, `Analysis_Summary.json`. The seed is `20260824`. The summary JSON is present in the uploaded integrated package but is not listed in the cleaned public layout above unless the repository owner chooses to publish it.

## 19. Manuscript and References

The complete manuscript is retained by the author pending formal publication, possible additions, and potential collaborations. The public `manuscript/` directory is intended to provide a **high level study outline**, not the unpublished full manuscript.

- `manuscript/manuscript.md` — manuscript overview
- `manuscript/REFERENCES.md` — bibliographic references
- `CITATION.cff` — repository citation metadata

If a peer-reviewed article or archival DOI becomes available, the citation metadata and manuscript status should be updated accordingly.

## 20. Limitations

The model is based on provisional coefficients, assumed state equations, and synthetic inputs. It does not incorporate patient specific ECMO configuration, ventricular unloading, diagnostic heterogeneity, repeated measurement error, or clinically observed post-decannulation outcomes. The simulated seven day stopping time should not be interpreted as a treatment schedule. Multimodal longitudinal data, parameter estimation, clinical endpoint definition, and independent external validation would be required before evaluating bedside use.

## 21. Citation and Responsible Use

**Author:** Prihantini.

Please use the repository's `CITATION.cff` metadata when citing the computational materials. Do not describe the model outputs as patient level evidence, a clinically validated decision rule, or demonstrated treatment benefit.

**License:** Consult the actual `LICENSE` file if one is present in the published repository. A license is not inferred solely from the example repository's MIT badge.

---

*Research software and mathematical simulations for reproducibility and methodological evaluation only. Not intended for patient care or clinical decision making.*
