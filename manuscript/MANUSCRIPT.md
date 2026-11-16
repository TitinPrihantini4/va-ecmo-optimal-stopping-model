# VA-ECMO Optimal Stopping Model — Manuscript Overview

> [!IMPORTANT]
> **Full manuscript currently retained by the author.** This research manuscript has **not yet been formally published**. The author is retaining the complete manuscript while the work remains open to further refinement, additional analyses, and potential research collaborations. This public document provides a high-level scientific overview only; it is **not the full manuscript, a peer-reviewed publication, or a clinically validated protocol**. Availability of the complete manuscript may be reconsidered by the author following publication or other research arrangements.

**Study title:** Optimal Stopping Model for VA-ECMO Liberation Based on LVOT VTI Derived Latent Physiological Reserve Under Recovery Uncertainty  
**Author:** Prihantini  
**Research status:** Unpublished, literature-parameterized computational proof-of-concept; no patient-level calibration or external validation.

## 1. Research question and motivation

Liberation from venoarterial extracorporeal membrane oxygenation (VA-ECMO) involves balancing potential native cardiac recovery against the consequences of premature liberation and continued support. Left ventricular outflow tract velocity–time integral (LVOT VTI) provides a clinically relevant observation, but a single value cannot represent all modeled changes in physiological reserve, oxygen debt, support dependence, and hemodynamic stability. This study explores whether a specified dynamical model and sequential stopping rule can produce interpretable **model-defined** liberation windows under assumed uncertainty.

## 2. Study design and evidence boundaries

- **Design:** Literature-informed mathematical and computational proof-of-concept, not an observational or interventional patient study.
- **Evidence use:** Published VA-ECMO literature provides clinical context and a **9.5 cm LVOT VTI reference anchor**; it does not supply fitted state trajectories or validated coefficients for this model.
- **Time origin:** Day 0 is a **hypothetical first formal readiness assessment**, not the day of VA-ECMO cannulation.
- **Horizon:** Seven simulation days, with a stopping grid of 0.05 day.
- **Interpretation:** Model scores, hazards, Markov occupancy, and stopping times are simulated quantities, not observed patient probabilities, clinical outcomes, or bedside recommendations.

## 3. Mathematical methods — overview

### 3.1 Nonlinear physiological state model

Four coupled, bounded nonlinear ordinary differential equations (ODEs) describe:

| State | Meaning |
|---|---|
| `R(t)` | Latent physiological reserve |
| `D(t)` | Oxygen-debt burden |
| `A(t)` | Dependence on ECMO support |
| `H(t)` | Hemodynamic stability |

A prescribed recovery drive and support fraction act as time-dependent inputs. A deterministic observation equation converts simulated states into **simulated LVOT VTI**; patient measurements are not used to infer individual latent states in this study.

### 3.2 Decision formulation

A logistic **model-implied liberation-feasibility score**, a dynamic **liberation margin**, and a provisional **failure-hazard-like term** accompany the ODE trajectories. A finite-horizon Bellman recursion compares immediate liberation utility with the value of continuing support. The first admissible stop requires **all** of the following:

1. Immediate liberation utility is no lower than continuation value, within numerical tolerance.
2. Liberation margin is nonnegative.
3. Simulated LVOT VTI is at least **9.5 cm**.
4. Hemodynamic stability is at least **0.55** on the model scale.
5. Model-implied feasibility score is at least **0.65**.

These eligibility values are part of the provisional model implementation, **not validated clinical thresholds**.

### 3.3 Additional mathematical analyses

- A four-state, state-dependent continuous-time Markov chain (CTMC) describes **support-dependent, recovering, liberation-ready, and relapse-risk** regime occupancy. It is propagated as a separate descriptive layer and **does not directly enter the Bellman decision**.
- Three fixed-environment equilibria are assessed using numerical root finding and Jacobian eigenvalues; a reduced reserve–oxygen-debt phase plane illustrates a conditional two-dimensional vector-field slice.
- Nine prespecified parameter scenarios test how the model's stopping rule responds to changes in assumed recovery and dependence coefficients.
- **500 Latin-hypercube parameter samples** support structural uncertainty and partial rank correlation coefficient (PRCC) analyses; a separate **500-run input-perturbation ensemble** varies selected coefficients and initial states.
- Local ±1% elasticities, RK45/DOP853/RK4 numerical checks, an **800-case internal synthetic comparison** of five logistic feature sets, and a VTI-only local identifiability experiment provide supplementary diagnostics.

## 4. Principal simulation results

| Analysis | Manuscript-reported finding | Interpretation boundary |
|---|---|---|
| Reference stopping time | **Day 3.65** | Measured from the hypothetical readiness assessment, not ECMO initiation |
| Reference state at stop | VTI **10.68 cm**; reserve **0.601**; oxygen debt **0.341**; support dependence **0.390**; stability **0.551** | All are model outputs |
| Reference decision quantities | Margin **0.156**; model feasibility **0.850**; hazard-like term **0.0215** | Neither clinical event probabilities nor fitted hazards |
| Fixed-regime equilibria | Three converged equilibria, each with a negative maximum real Jacobian eigenvalue | Local stability under its own fixed environment only |
| Prespecified scenarios | All **9/9** reached an admissible stop; range **3.40–6.75 days** | No clinical reversibility classification was established |
| Latin-hypercube experiment | **88.2%** of 500 sets reached a stop; terminal-margin median **0.352**, empirical 2.5th–97.5th percentiles **−0.041 to 0.674** | Distribution across assumed parameter ranges, not a patient confidence interval |
| Separate input-perturbation ensemble | **488/500 (97.6%)** reached a stop; median stop **3.75 days** (IQR **3.35–4.50**) | Randomized inputs, not a continuous-time stochastic physiology model |
| Strongest global sensitivity | Reserve-gain PRCC **+0.952** with terminal margin | Conditional on the specified equations and sampled ranges |
| Internal synthetic model comparison | Full dynamic: AIC **554.985**, internal AUC **0.855**; VTI only: AIC **730.638**, internal AUC **0.703** | In-sample recovery of synthetic labels; **not** clinical predictive performance |
| VTI-only local identifiability | Sensitivity-matrix condition number approximately **24,007** | Weakly constrained local combination among four selected rates; not proof of global non-identifiability |

### How to read the findings

The simulated VTI rises as reserve and stability increase and oxygen debt and support dependence decline. Nevertheless, **crossing the VTI anchor alone does not determine the stopping day**: the complete Bellman comparison and additional model eligibility conditions must also hold. In the nine scenarios, favorable-looking parameter changes did not always produce earlier discrete stopping times, illustrating the interaction of nonlinear trajectories and the stopping grid.

The Latin-hypercube and separate perturbation experiments probe different forms of **assumed input uncertainty**. Their reported percentages should not be translated into probabilities of successful clinical liberation. The internal synthetic comparison favors the full dynamic feature set for reproducing labels generated by the simulation itself, without demonstrating clinical superiority over LVOT VTI alone.

## 5. Figures and output organization

The full manuscript contains a workflow figure and simulation visualizations covering:

- **Figure 1:** Computational workflow and evidence/model separation.
- **Figures 2–3:** Reference recovery trajectory and first admissible stopping boundary.
- **Figure 4:** Reduced reserve–oxygen-debt phase plane under fixed conditions.
- **Figure 5:** Latin-hypercube variation in simulated LVOT VTI trajectories.
- **Figure 6:** Global PRCC sensitivity of the terminal liberation margin.
- **Figure 7:** In-sample synthetic model comparison.
- **Figure 8:** Simulated CTMC regime occupancy.
- **Figure 9:** Exploratory decision surface; positive stop advantage and margin are necessary but not sufficient.
- **Figure 10:** VTI-only local practical-identifiability singular-value spectrum.

The repository's `code/`, `data/`, `results/`, and `figures/` directories are intended to document the numerical implementation and corresponding outputs. Numerical tables and figures in the complete manuscript should be interpreted with their methodological qualifications.

## 6. Discussion — key implications

The mathematical contribution is the explicit separation of **simulated physiological states**, **LVOT VTI as an observation**, **provisional risk and feasibility quantities**, and a **constrained sequential stopping action**. The equilibrium and phase-plane analyses characterize model behavior under restricted conditions, not clinical recovery categories. The sensitivity analyses identify influential assumed coefficients, while the VTI-only identifiability analysis shows why simulated VTI by itself cannot tightly distinguish all four selected rate effects under the reference parameterization.

## 7. Limitations

The model has **no patient-level fitting, observed decannulation outcomes, or external validation**. Its structural coefficients, observation weights, Markov transition rates, hazard-like function, and utility parameters are provisional. The ODEs omit several clinically relevant mechanisms and support interventions, and the current simulated VTI series has no empirically fitted measurement-error model.

The seven-day horizon and discrete stopping grid are modeling choices. The CTMC is descriptive and separate from the stopping calculation; fixed-regime eigenvalue results do not establish stability of the nonautonomous reference trajectory. The uncertainty distributions are assumed rather than learned from patient cohorts. Synthetic model-comparison metrics were computed in sample against generated labels and are not estimates of clinical performance.

## 8. Conclusion and next research steps

Under the specified reference assumptions, the model produced a first admissible stopping time of **3.65 days** after a hypothetical readiness assessment. Its principal use at this stage is as a **reproducible mathematical research example** for exploring sequential liberation decisions and their sensitivity to uncertain model assumptions. Further work would require longitudinal multimodal clinical data, parameter calibration, identifiability assessment, clinically defined outcomes, and independent validation before any decision-support application could be considered. These steps are **future research needs**, not completed or ongoing clinical validation activities.

## 9. Availability and collaboration

The **complete unpublished manuscript is retained by the author** because the research may be revised, extended, or developed with additional collaborators prior to formal publication. This overview is shared to communicate the study's scope and simulation findings without representing the full manuscript as publicly released or peer reviewed. Any collaboration, citation of unpublished material, or request for the full manuscript should be discussed with the author.

## 10. References

The bibliography is reproduced below and also maintained as a standalone **[REFERENCES.md](REFERENCES.md)** file. Abbreviated author lists are flagged as requiring final APA 7 completion before journal submission. Clinical citations provide background and literature anchors; they **do not** validate the provisional mathematical coefficients or simulated stopping policy.

Aissaoui, N., Caudron, J., Leprince, P., et al. (2017). Right–left ventricular interdependence: A promising predictor of successful extracorporeal membrane oxygenation (ECMO) weaning after assistance for refractory cardiogenic shock. Intensive Care Medicine, 43, 592–594. https://doi.org/10.1007/s00134-016-4657-0

Aissaoui, N., El-Banayosy, A., & Combes, A. (2015). How to wean a patient from veno-arterial extracorporeal membrane oxygenation. Intensive Care Medicine, 41(5), 902–905. https://doi.org/10.1007/s00134-015-3663-y

Aissaoui, N., Luyt, C.-E., Leprince, P., Trouillet, J.-L., Léger, P., Pavie, A., Diebold, B., Chastre, J., & Combes, A. (2011). Predictors of successful extracorporeal membrane oxygenation (ECMO) weaning after assistance for refractory cardiogenic shock. Intensive Care Medicine, 37(11), 1738–1745. https://doi.org/10.1007/s00134-011-2358-2

Akaike, H. (1974). A new look at the statistical model identification. IEEE Transactions on Automatic Control, 19(6), 716–723. https://doi.org/10.1109/TAC.1974.1100705

Bellman, R. (1957). Dynamic programming. Princeton University Press.

Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. Monthly Weather Review, 78(1), 1–3. https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2

Cavarocchi, N. C., Pitcher, H. T., Yang, Q., Karbowski, P., Miessau, J., Hastings, H. M., & Hirose, H. (2013). Weaning of extracorporeal membrane oxygenation using continuous hemodynamic transesophageal echocardiography. The Journal of Thoracic and Cardiovascular Surgery, 146(6), 1474–1479. https://doi.org/10.1016/j.jtcvs.2013.06.055

Charbonneau, F., Chahinian, K., Bebawi, E., Lavigueur, O., Lévesque, É., Lamarche, Y., Serri, K., Albert, M., Noly, P.-E., Cournoyer, A., & Cavayas, Y. A. (2022). Parameters associated with successful weaning of veno-arterial extracorporeal membrane oxygenation: A systematic review. Critical Care, 26, Article 375. https://doi.org/10.1186/s13054-022-04249-w

Dettling, A., Kellner, C., Sundermeyer, J., et al. (2025). Incidence and predictors of weaning failure from veno-arterial extracorporeal membrane oxygenation therapy in patients with cardiogenic shock. European Journal of Heart Failure, 27(5), 832–841. https://doi.org/10.1002/ejhf.3583

Hairer, E., Nørsett, S. P., & Wanner, G. (1993). Solving ordinary differential equations I: Nonstiff problems (2nd ed.). Springer. https://doi.org/10.1007/978-3-540-78862-1

Hsu, H. R., Sekhar, P., Grover, J., Tian, D. H., Downey, C., Maudlin, B., Dissanayake, C., & Dennis, M. (2025). Predictors of successful weaning from veno-arterial extracorporeal membrane oxygenation (V-A ECMO): A systematic review and meta-analysis. PLOS ONE, 20(3), Article e0310289. https://doi.org/10.1371/journal.pone.0310289

Huang, K.-C., Lin, L.-Y., Chen, Y.-S., et al. (2018). Three-dimensional echocardiography-derived right ventricular ejection fraction correlates with success of decannulation and prognosis in patients stabilized by venoarterial extracorporeal life support. Journal of the American Society of Echocardiography, 31, 169–179. https://doi.org/10.1016/j.echo.2017.09.004

Jeong, J. H., Kook, H., Lee, S. H., et al. (2023). Predictors of in-hospital mortality after successful weaning of venoarterial extracorporeal membrane oxygenation in cardiogenic shock. Scientific Reports, 13, Article 17529. https://doi.org/10.1038/s41598-023-44679-2

Khalil, H. K. (2002). Nonlinear systems (3rd ed.). Prentice Hall.

Kim, D., Jang, W. J., Park, T. K., Cho, Y. H., Choi, J.-O., Jeon, E.-S., & Yang, J. H. (2021). Echocardiographic predictors of successful extracorporeal membrane oxygenation weaning after refractory cardiogenic shock. Journal of the American Society of Echocardiography, 34(4), 414–422.e4. https://doi.org/10.1016/j.echo.2020.12.002

Lorusso, R., Shekar, K., MacLaren, G., Schmidt, M., Pellegrino, V., Meyns, B., Haft, J., Vercaemst, L., Pappalardo, F., Bermudez, C., Belohlavek, J., Hou, X., Boeken, U., Castillo, R., Donker, D. W., Abrams, D., Ranucci, M., Hryniewicz, K., Chavez, I., … Whitman, G. (2021). ELSO interim guidelines for venoarterial extracorporeal membrane oxygenation in adult cardiac patients. ASAIO Journal, 67(8), 827–844. https://doi.org/10.1097/MAT.0000000000001510

Lüsebrink, E., et al. (2020). Update on weaning from veno-arterial extracorporeal membrane oxygenation. Journal of Clinical Medicine, 9(4), Article 992. https://doi.org/10.3390/jcm9040992

Marino, S., Hogue, I. B., Ray, C. J., & Kirschner, D. E. (2008). A methodology for performing global uncertainty and sensitivity analysis in systems biology. Journal of Theoretical Biology, 254(1), 178–196. https://doi.org/10.1016/j.jtbi.2008.04.011

McKay, M. D., Beckman, R. J., & Conover, W. J. (1979). A comparison of three methods for selecting values of input variables in the analysis of output from a computer code. Technometrics, 21(2), 239–245. https://doi.org/10.1080/00401706.1979.10489755

Niu, M., & Feng, Y. (2026). Meta-analysis of the predictive value of critical care echocardiography for weaning outcomes in patients with VA-ECMO-assisted cardiogenic shock. Frontiers in Medicine, 13, Article 1835564. https://doi.org/10.3389/fmed.2026.1835564

Norris, J. R. (1997). Markov chains. Cambridge University Press. https://doi.org/10.1017/CBO9780511810633

Ortuño, S., Delmas, C., Diehl, J.-L., Bailleul, C., Lancelot, A., Naili, M., Cholley, B., Pirracchio, R., & Aissaoui, N. (2019). Weaning from veno-arterial extra-corporeal membrane oxygenation: Which strategy to use? Annals of Cardiothoracic Surgery, 8(1), E1–E8. https://doi.org/10.21037/acs.2018.08.05

Peskir, G., & Shiryaev, A. (2006). Optimal stopping and free-boundary problems. Birkhäuser. https://doi.org/10.1007/978-3-7643-7390-0

Raue, A., Kreutz, C., Maiwald, T., Bachmann, J., Schilling, M., Klingmüller, U., & Timmer, J. (2009). Structural and practical identifiability analysis of partially observed dynamical models by exploiting the profile likelihood. Bioinformatics, 25(15), 1923–1929. https://doi.org/10.1093/bioinformatics/btp358

Sawada, K., Kawakami, S., Murata, S., et al. (2021). Predicting parameters for successful weaning from veno-arterial extracorporeal membrane oxygenation in cardiogenic shock. ESC Heart Failure, 8(1), 471–480. https://doi.org/10.1002/ehf2.13097

Schwarz, G. (1978). Estimating the dimension of a model. The Annals of Statistics, 6(2), 461–464. https://doi.org/10.1214/aos/1176344136

Shin, H., Kim, J., Hong, D., Bak, M., Kim, D., Choi, J.-O., Cho, Y. H., Ahn, J. H., & Yang, J. H. (2026). Clinical significance of change in left atrial strain during weaning from venoarterial extracorporeal membrane oxygenation. Journal of the American Society of Echocardiography, 39(2), 146–155. https://doi.org/10.1016/j.echo.2025.10.012

