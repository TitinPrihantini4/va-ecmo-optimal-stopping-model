from pathlib import Path
import json, math, re, shutil, textwrap
import numpy as np, pandas as pd
from scipy.integrate import solve_ivp
from scipy.optimize import root
from scipy.stats import qmc, rankdata, pearsonr
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, brier_score_loss, accuracy_score
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from zipfile import ZipFile, ZIP_DEFLATED

BASE=Path(__file__).resolve().parents[1] / 'generated_output'
FIG=BASE/'figures'; CODE=BASE/'code'
BASE.mkdir(parents=True,exist_ok=True)
FIG.mkdir(parents=True,exist_ok=True); CODE.mkdir(parents=True,exist_ok=True)
SEED=20260824
rng=np.random.default_rng(SEED)

TITLE='Optimal Stopping Model for VA-ECMO Liberation Based on LVOT VTI Derived Latent Physiological Reserve Under Recovery Uncertainty'
ALT2='Regime Switching Optimal Stopping for VA-ECMO Liberation Using LVOT VTI Derived Latent Cardiac Reserve Under Hemodynamic Uncertainty'
ALT3='Sequential Decision Modeling of VA-ECMO Liberation from LVOT VTI Trajectories and Latent Myocardial Reserve Under Recovery Uncertainty'
KEYWORDS=['VA-ECMO Liberation','LVOT VTI','Latent Physiological Reserve','Optimal Stopping','Regime Switching','Uncertainty Quantification']

# ------------------------- Evidence ledger -------------------------
sources=[
[1,'Aissaoui N, et al. Predictors of successful ECMO weaning after assistance for refractory cardiogenic shock. Intensive Care Med.',2011,'VTI/LVEF/TDSa and minimal-flow anchors','Flow reduction to <1.5 L/min; VTI >=10 cm; LVEF >20-25%; TDSa >=6 cm/s.','https://pubmed.ncbi.nlm.nih.gov/21965097/','Clinical anchor'],
[2,'Aissaoui N, El-Banayosy A, Combes A. How to wean a patient from veno-arterial extracorporeal membrane oxygenation. Intensive Care Med.',2015,'Bedside liberation framework','Staged clinical, hemodynamic and echocardiographic assessment; emphasizes successful weaning is not equivalent to survival.','https://pubmed.ncbi.nlm.nih.gov/25619488/','Clinical framework'],
[3,'Lusebrink E, et al. Update on Weaning from Veno-Arterial Extracorporeal Membrane Oxygenation. J Clin Med.',2020,'Flow-reduction protocol context','Stepwise reduction and multiparametric echocardiographic/hemodynamic assessment during VA-ECMO weaning.','https://pmc.ncbi.nlm.nih.gov/articles/PMC7230450/','Protocol context'],
[4,'Ortuño S, et al. Weaning from veno-arterial extra-corporeal membrane oxygenation which strategy to use. Ann Cardiothorac Surg.',2019,'Weaning strategy and outcome context','Reviews staged flow reduction, RV-LV interaction and post-weaning mortality; reported weaning rates vary widely.','https://pmc.ncbi.nlm.nih.gov/articles/PMC6379199/','Clinical framework'],
[5,'Kim D, et al. Echocardiographic Predictors of Successful Extracorporeal Membrane Oxygenation Weaning After Refractory Cardiogenic Shock. J Am Soc Echocardiogr.',2021,'Dynamic flow-study reserve concept','n=92; flow reduced 30-50% for 15 min; dynamic tissue-Doppler changes outperformed conventional fixed criteria.','https://pubmed.ncbi.nlm.nih.gov/33321165/','Dynamic reserve rationale'],
[6,'Sawada K, et al. Predicting Parameters for Successful Weaning from Veno-Arterial Extracorporeal Membrane Oxygenation in Cardiogenic Shock. ESC Heart Fail.',2021,'Low-flow hemodynamic comparator','n=50; assessment at 1.5-2.0 L/min; LVETc/PAWP AUC 0.82.','https://pmc.ncbi.nlm.nih.gov/articles/PMC7835592/','Comparator anchor'],
[7,'Alonso-Fernandez-Gatta M, et al. Echocardiographic Prediction of Successful Weaning From Venoarterial Extracorporeal Membrane Oxygenation. Am J Crit Care.',2022,'Observed VTI separation','n=85; 61% successful; LVOT VTI 15 vs 11 cm in success vs failure groups.','https://pubmed.ncbi.nlm.nih.gov/36316178/','Observed VTI range'],
[8,'Huang KC, et al. Three-Dimensional Echocardiography-Derived Right Ventricular Ejection Fraction Correlates with Success of Decannulation. J Am Soc Echocardiogr.',2018,'RV recovery context','n=46; 3D RVEF AUC 0.90; cutoff 24.6% associated with weaning success.','https://pubmed.ncbi.nlm.nih.gov/29079045/','Biventricular context'],
[9,'Cavarocchi NC, et al. Weaning of extracorporeal membrane oxygenation using continuous hemodynamic transesophageal echocardiography. J Thorac Cardiovasc Surg.',2013,'Continuous hemodynamic monitoring','n=21 standardized hTEE-guided protocol; ventricular recovery assessment under staged weaning.','https://pubmed.ncbi.nlm.nih.gov/23993027/','Monitoring context'],
[10,'Aissaoui N, et al. Right-left ventricular interdependence as a predictor of successful ECMO weaning. Intensive Care Med.',2017,'Ventricular interaction','Highlights RV-LV interdependence during flow reduction as a potential negative prognostic signal.','https://pubmed.ncbi.nlm.nih.gov/28011989/','Mechanistic context'],
[11,'Lorusso R, et al. ELSO Interim Guidelines for Venoarterial Extracorporeal Membrane Oxygenation in Adult Cardiac Patients. ASAIO J.',2021,'VA-ECMO standards','ELSO adult cardiac guidance for VA-ECMO management and liberation context.','https://pubmed.ncbi.nlm.nih.gov/34339398/','Guideline context'],
[12,'Parameters associated with successful weaning of veno-arterial extracorporeal membrane oxygenation a systematic review. Crit Care.',2022,'Threshold heterogeneity','Most commonly reported LVOT VTI threshold >9.5 cm; reported AUROC 0.85 and 0.74 across studies; 8.6-cm threshold had sensitivity 75% and specificity 72% in one study.','https://pmc.ncbi.nlm.nih.gov/articles/PMC9724323/','Threshold/uncertainty anchor'],
[13,'Hsu HR, et al. Predictors of successful weaning from V-A ECMO a systematic review and meta-analysis. PLoS One.',2025,'Meta-analytic effect anchor','20 studies; higher LVEF and LVOT VTI associated with successful weaning; VTI mean difference 1.35 cm.','https://pmc.ncbi.nlm.nih.gov/articles/PMC11922212/','Evidence synthesis'],
[14,'Meta-analysis of the predictive value of critical care echocardiography for weaning outcomes in VA-ECMO-assisted cardiogenic shock. Front Med.',2026,'Contemporary echo evidence','22 studies, 1,986 patients for LVOT VTI; pooled SMD 0.89; aortic valve opening SMD 1.57.','https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1835564/full','Evidence synthesis'],
[15,'Dettling A, et al. Incidence and predictors of weaning failure from VA-ECMO therapy in patients with cardiogenic shock. Eur J Heart Fail.',2025,'Failure-rate and post-weaning risk context','n=685 from 23 centres; 59.9% successfully weaned; 40.1% weaning failure; post-weaning in-hospital death remained substantial.','https://pmc.ncbi.nlm.nih.gov/articles/PMC12103957/','Outcome context'],
[16,'Jeong JH, et al. Predictors of in-hospital mortality after successful weaning of VA-ECMO in cardiogenic shock. Sci Rep.',2023,'Post-liberation outcome separation','Among 262 successfully weaned patients, in-hospital mortality was 18.3%; successful liberation and survival are distinct endpoints.','https://pmc.ncbi.nlm.nih.gov/articles/PMC10579350/','Outcome context'],
[17,'Clinical Significance of Change in Left Atrial Strain during Weaning from VA-ECMO. J Am Soc Echocardiogr.',2025,'Dynamic echocardiographic reserve','n=120; success 55%; adding relative LARS change improved AUC from 0.75 to 0.83.','https://pubmed.ncbi.nlm.nih.gov/41167351/','Dynamic-measurement context'],
[18,'Mongkolpun W, et al. Cutaneous blood flow as a predictor of successful weaning from VA-ECMO. Crit Care abstract.',2019,'Short low-flow challenge','Flow reduced to 1 L/min for 10 min; aortic VTI >10 cm used as a weaning criterion.','https://pmc.ncbi.nlm.nih.gov/articles/PMC6423782/','Low-flow challenge context'],
]
sources_df=pd.DataFrame(sources,columns=['source_id','citation','year','parameter_or_anchor','reported_anchor_or_role','open_access_or_download_link','status'])
sources_df.to_csv(BASE/'Literature_Parameter_Sources.csv',index=False)

# ------------------------- Model -------------------------
BASEP=dict(
 recovery0=0.82,recovery_floor=0.34,k_recovery_decay=0.18,
 k_reserve_gain=0.48,k_debt_inhibit=0.22,k_depend_inhibit=0.18,
 k_debt_gen=0.18,k_debt_clear=0.42,
 k_depend_gain=0.12,k_depend_release=0.32,
 k_stability_gain=0.34,k_stability_loss_debt=0.16,k_stability_loss_depend=0.12,
 vti_intercept=7.70,vti_R=5.00,vti_H=0.80,vti_A=1.20,
 p_intercept=-4.40,p_VTI=0.48,p_R=1.60,p_H=1.00,p_D=0.80,p_A=0.60,
 margin_R=0.75,margin_H=0.35,margin_D=0.45,margin_A=0.35,margin_VTI=0.07,margin0=0.28,
 u_success=2.60,u_fail=1.80,u_D=0.50,u_A=0.35,u_H=0.45,liberation_cost=0.18,
 continuation_base=0.14,continuation_D=0.055,continuation_A=0.035,discount=0.015,
 lambda0=0.035,hazard_D=1.15,hazard_A=0.80,hazard_R=1.20,hazard_H=0.85,
 q01=0.32,q12=0.38,q23=0.22,q10=0.09,q21=0.11,q32=0.05,
)
X0=np.array([0.34,0.48,0.62,0.46],float) # reserve, oxygen debt, support dependence, hemodynamic stability
HORIZON=7.0; DT=0.05; T=np.arange(0,HORIZON+1e-12,DT)

def sigmoid(x): return 1/(1+np.exp(-np.clip(x,-50,50)))
def recovery_drive(t,p=BASEP): return p['recovery_floor']+(p['recovery0']-p['recovery_floor'])*np.exp(-p['k_recovery_decay']*t)
def support_fraction(t): return 0.82-0.35*(1-np.exp(-0.38*t))
def rhs(t,y,p=BASEP):
    R,D,A,H=y; G=recovery_drive(t,p); S=support_fraction(t)
    dR=p['k_reserve_gain']*G*(1-R)-p['k_debt_inhibit']*D*R-p['k_depend_inhibit']*A*R
    dD=p['k_debt_gen']*(1-R)*(1-D)-p['k_debt_clear']*R*D
    dA=p['k_depend_gain']*S*(1-R)*(1-A)-p['k_depend_release']*R*A
    dH=p['k_stability_gain']*R*(1-H)-p['k_stability_loss_debt']*D*H-p['k_stability_loss_depend']*A*H
    return np.array([dR,dD,dA,dH])
def integrate(p=BASEP,x0=X0,method='RK45',rtol=1e-9,atol=1e-11,t_eval=T):
    sol=solve_ivp(lambda t,y:rhs(t,y,p),(float(t_eval[0]),float(t_eval[-1])),x0,t_eval=t_eval,method=method,rtol=rtol,atol=atol)
    if not sol.success: raise RuntimeError(sol.message)
    return sol.y.T

def derived(X,p=BASEP):
    R,D,A,H=X.T
    vti=p['vti_intercept']+p['vti_R']*R+p['vti_H']*H-p['vti_A']*A
    prob=sigmoid(p['p_intercept']+p['p_VTI']*vti+p['p_R']*R+p['p_H']*H-p['p_D']*D-p['p_A']*A)
    margin=p['margin_R']*R+p['margin_H']*H-p['margin_D']*D-p['margin_A']*A+p['margin_VTI']*(vti-9.5)-p['margin0']
    hazard=p['lambda0']*np.exp(p['hazard_D']*D+p['hazard_A']*A-p['hazard_R']*R-p['hazard_H']*H)
    return vti,prob,margin,hazard

def optimal_stop(X,p=BASEP):
    vti,prob,margin,hazard=derived(X,p)
    R,D,A,H=X.T; n=len(X)
    ustop=p['u_success']*prob-p['u_fail']*(1-prob)-p['u_D']*D-p['u_A']*A+p['u_H']*H-p['liberation_cost']
    V=np.zeros(n); cont=np.zeros(n)
    V[-1]=ustop[-1]; cont[-1]=ustop[-1]
    for i in range(n-2,-1,-1):
        c=(p['continuation_base']+p['continuation_D']*D[i]+p['continuation_A']*A[i]+0.30*hazard[i])*DT
        cont[i]=math.exp(-p['discount']*DT)*V[i+1]-c
        V[i]=max(ustop[i],cont[i])
    adv=ustop-cont
    eligible=(vti>=9.5)&(margin>=0)&(H>=0.55)&(prob>=0.65)&(adv>=-1e-10)
    ids=np.where(eligible)[0]
    idx=int(ids[0]) if len(ids) else None
    return dict(vti=vti,prob=prob,margin=margin,hazard=hazard,ustop=ustop,continue_value=cont,value=V,adv=adv,idx=idx)

X=integrate(); der=optimal_stop(X); idx=der['idx']
if idx is None: raise RuntimeError('Reference stopping boundary not reached')
ref=pd.DataFrame({'time_day':T,'reserve':X[:,0],'oxygen_debt':X[:,1],'support_dependence':X[:,2],'hemodynamic_stability':X[:,3],
                  'recovery_drive':[recovery_drive(t) for t in T],'support_fraction':[support_fraction(t) for t in T],
                  'lvot_vti_cm':der['vti'],'model_liberation_probability':der['prob'],'liberation_margin':der['margin'],'failure_hazard':der['hazard'],
                  'immediate_liberation_value':der['ustop'],'continuation_value':der['continue_value'],'stop_advantage':der['adv']})
ref.to_csv(BASE/'Reference_Trajectory.csv',index=False)

# latent Markov regime probabilities using state-dependent CTMC and Euler propagation
# states: support-dependent, recovering, liberation-ready, relapse-risk
P=np.zeros((len(T),4)); P[0]=[0.75,0.22,0.02,0.01]
for i in range(len(T)-1):
    R,D,A,H=X[i]; m=der['margin'][i]; h=der['hazard'][i]
    favorable=np.clip(0.55*R+0.45*H,0,1); stress=np.clip(0.45*D+0.40*A+0.15*(1-H),0,1)
    Q=np.zeros((4,4))
    Q[0,1]=BASEP['q01']*(0.25+1.35*favorable)
    Q[1,0]=BASEP['q10']*(0.20+1.1*stress)
    Q[1,2]=BASEP['q12']*(0.15+1.55*max(0,m+0.28))
    Q[2,1]=BASEP['q21']*(0.20+0.8*stress)
    Q[2,3]=BASEP['q23']*(0.15+1.8*stress+2.0*h)
    Q[3,2]=BASEP['q32']*(0.15+0.95*favorable)
    for a in range(4): Q[a,a]=-Q[a].sum()
    pn=P[i] + DT*P[i].dot(Q)
    P[i+1]=np.clip(pn,0,None); P[i+1]/=P[i+1].sum()
reg=pd.DataFrame(P,columns=['p_support_dependent','p_recovering','p_liberation_ready','p_relapse_risk']); reg.insert(0,'time_day',T); reg.to_csv(BASE/'Latent_Regime_Probabilities.csv',index=False)

# equilibria under fixed recovery drive and support fraction
EQS=[]; EIG=[]
def rhs_fixed(y,G,S,p=BASEP):
    R,D,A,H=y
    return np.array([
        p['k_reserve_gain']*G*(1-R)-p['k_debt_inhibit']*D*R-p['k_depend_inhibit']*A*R,
        p['k_debt_gen']*(1-R)*(1-D)-p['k_debt_clear']*R*D,
        p['k_depend_gain']*S*(1-R)*(1-A)-p['k_depend_release']*R*A,
        p['k_stability_gain']*R*(1-H)-p['k_stability_loss_debt']*D*H-p['k_stability_loss_depend']*A*H])
for name,G,S,guess in [('Decompensated',0.08,0.90,[.12,.77,.72,.16]),('Compensated',0.16,0.78,[.30,.51,.42,.43]),('Recovery-dominant',0.25,0.68,[.69,.16,.10,.86])]:
    rt=root(lambda y:rhs_fixed(y,G,S),guess)
    z=np.clip(rt.x,0,1)
    # numeric Jacobian
    eps=1e-6; J=np.zeros((4,4))
    for j in range(4):
        yp=z.copy(); ym=z.copy(); yp[j]+=eps; ym[j]-=eps
        J[:,j]=(rhs_fixed(yp,G,S)-rhs_fixed(ym,G,S))/(2*eps)
    vals=np.linalg.eigvals(J)
    vti,prob,margin,haz=derived(z.reshape(1,-1))
    EQS.append([name,G,S,*z,vti[0],prob[0],margin[0],bool(rt.success)])
    for k,v in enumerate(vals): EIG.append([name,k+1,v.real,v.imag])
eq_df=pd.DataFrame(EQS,columns=['regime','fixed_recovery_drive','fixed_support_fraction','reserve','oxygen_debt','support_dependence','hemodynamic_stability','lvot_vti_cm','model_liberation_probability','liberation_margin','root_success']); eq_df.to_csv(BASE/'Reference_Equilibria.csv',index=False)
eig_df=pd.DataFrame(EIG,columns=['regime','eigenvalue','real','imag']); eig_df.to_csv(BASE/'Reference_Eigenvalues.csv',index=False)

# phase plane R-D near reference stop holding A,H fixed
A0,H0=X[idx,2],X[idx,3]; G0=recovery_drive(T[idx]); S0=support_fraction(T[idx])
rows=[]
for Rv in np.linspace(.08,.92,55):
    for Dv in np.linspace(.05,.90,55):
        y=np.array([Rv,Dv,A0,H0]); d=rhs_fixed(y,G0,S0)
        rows.append([Rv,Dv,d[0],d[1]])
pd.DataFrame(rows,columns=['reserve','oxygen_debt','dR','dD']).to_csv(BASE/'Phase_Plane_Reserve_Debt.csv',index=False)

# scenario analysis
scenarios={
'Reference':{},'Faster myocardial recovery':{'k_reserve_gain':0.60},'Slower myocardial recovery':{'k_reserve_gain':0.36},
'Persistent oxygen debt':{'k_debt_clear':0.28},'Rapid oxygen-debt resolution':{'k_debt_clear':0.56},
'High support dependence':{'k_depend_release':0.22},'Low support dependence':{'k_depend_release':0.44},
'Hemodynamic fragility':{'k_stability_gain':0.25,'k_stability_loss_debt':0.22},'Lower recovery volatility proxy':{'k_recovery_decay':0.13}
}
sc=[]
for nm,upd in scenarios.items():
    p=BASEP.copy(); p.update(upd); xx=integrate(p=p); dd=optimal_stop(xx,p); j=dd['idx']
    sc.append([nm, np.nan if j is None else T[j], xx[-1,0], dd['vti'][-1], dd['margin'][-1], np.nan if j is None else dd['vti'][j], np.nan if j is None else dd['prob'][j]])
sc_df=pd.DataFrame(sc,columns=['scenario','stopping_day','terminal_reserve','terminal_vti_cm','terminal_margin','vti_at_stop_cm','model_probability_at_stop']); sc_df.to_csv(BASE/'Scenario_Results.csv',index=False)

# LHS sensitivity ranges
RANGES={
'k_recovery_decay':(.12,.26),'k_reserve_gain':(.34,.64),'k_debt_inhibit':(.14,.31),'k_depend_inhibit':(.10,.27),
'k_debt_gen':(.12,.27),'k_debt_clear':(.28,.58),'k_depend_gain':(.07,.18),'k_depend_release':(.22,.45),
'k_stability_gain':(.24,.46),'k_stability_loss_debt':(.10,.24),'k_stability_loss_depend':(.07,.19),
'margin_R':(.58,.92),'margin_D':(.30,.62),'margin_A':(.22,.48),'margin0':(.20,.38)
}
N_LHS=500; names=list(RANGES)
sampler=qmc.LatinHypercube(d=len(names),seed=SEED); u=sampler.random(N_LHS)
vals=qmc.scale(u,[RANGES[n][0] for n in names],[RANGES[n][1] for n in names])
lhs=pd.DataFrame(vals,columns=names); lhs.to_csv(BASE/'LHS_Parameter_Samples.csv',index=False)
unc=[]
for rid,row in lhs.iterrows():
    p=BASEP.copy(); p.update(row.to_dict()); xx=integrate(p=p,rtol=2e-7,atol=1e-9); dd=optimal_stop(xx,p); j=dd['idx']
    unc.append([rid,dd['margin'][-1],xx[-1,0],dd['vti'][-1],np.nan if j is None else T[j],0 if j is None else 1])
unc_df=pd.DataFrame(unc,columns=['sample_id','terminal_margin','terminal_reserve','terminal_vti_cm','stopping_day','boundary_reached']); unc_df.to_csv(BASE/'Uncertainty_Samples.csv',index=False)

# PRCC via residualized ranked correlation
def prcc_for(xdf,y):
    Xr=np.column_stack([rankdata(xdf[c]) for c in xdf.columns]); yr=rankdata(y); out=[]
    for j,c in enumerate(xdf.columns):
        others=[k for k in range(Xr.shape[1]) if k!=j]
        A=np.column_stack([np.ones(len(Xr)),Xr[:,others]])
        bx=np.linalg.lstsq(A,Xr[:,j],rcond=None)[0]; by=np.linalg.lstsq(A,yr,rcond=None)[0]
        rx=Xr[:,j]-A@bx; ry=yr-A@by
        rr,pv=pearsonr(rx,ry); out.append([c,rr,pv])
    return pd.DataFrame(out,columns=['parameter','PRCC_terminal_margin','p_value']).sort_values('PRCC_terminal_margin',key=lambda s:s.abs(),ascending=False)
prcc=prcc_for(lhs,unc_df['terminal_margin'].values); prcc.to_csv(BASE/'Global_Sensitivity_PRCC.csv',index=False)

# local elasticity ±1%
base_outputs={'terminal_margin':der['margin'][-1],'terminal_reserve':X[-1,0],'terminal_vti_cm':der['vti'][-1],'stopping_day':T[idx]}
local=[]
for nm in names[:11]:
    p0=BASEP[nm]
    outs=[]
    for mult in [0.99,1.01]:
        pp=BASEP.copy(); pp[nm]=p0*mult; xx=integrate(p=pp); dd=optimal_stop(xx,pp); j=dd['idx']
        outs.append({'terminal_margin':dd['margin'][-1],'terminal_reserve':xx[-1,0],'terminal_vti_cm':dd['vti'][-1],'stopping_day':np.nan if j is None else T[j]})
    for outnm in base_outputs:
        if np.isfinite(outs[0][outnm]) and np.isfinite(outs[1][outnm]) and base_outputs[outnm]!=0:
            el=((outs[1][outnm]-outs[0][outnm])/(0.02*p0))*(p0/base_outputs[outnm])
        else: el=np.nan
        local.append([nm,outnm,el])
local_df=pd.DataFrame(local,columns=['parameter','output','elasticity']); local_df.to_csv(BASE/'Local_Elasticity.csv',index=False)

# stochastic structural/initial-state perturbation
N_STO=500; sto=[]
perturb_names=['k_reserve_gain','k_debt_clear','k_depend_release','k_stability_gain','k_recovery_decay']
for i in range(N_STO):
    pp=BASEP.copy()
    for nm in perturb_names: pp[nm]*=float(np.exp(rng.normal(0,0.18)))
    x0=np.clip(X0+rng.normal(0,[.055,.075,.085,.060]),.03,.97)
    xx=integrate(p=pp,x0=x0,rtol=3e-7,atol=1e-9); dd=optimal_stop(xx,pp); j=dd['idx']
    sto.append([i,np.nan if j is None else T[j],0 if j is None else 1,dd['vti'][-1],xx[-1,0],dd['margin'][-1],np.nan if j is None else dd['vti'][j],np.nan if j is None else dd['prob'][j]])
sto_df=pd.DataFrame(sto,columns=['run','stopping_day','boundary_reached','terminal_vti_cm','terminal_reserve','terminal_margin','vti_at_stop_cm','model_probability_at_stop']); sto_df.to_csv(BASE/'Stochastic_Perturbation_Results.csv',index=False)

# Numerical robustness
rob=[]
for method in ['RK45','DOP853']:
    xx=integrate(method=method); dd=optimal_stop(xx); j=dd['idx']; rob.append([method,xx[-1,0],dd['vti'][-1],T[j] if j is not None else np.nan])
# fixed-step RK4
def rk4(dt):
    tt=np.arange(0,HORIZON+1e-12,dt); yy=np.zeros((len(tt),4)); yy[0]=X0
    for i in range(len(tt)-1):
        h=tt[i+1]-tt[i]; y=yy[i]; ti=tt[i]
        k1=rhs(ti,y); k2=rhs(ti+h/2,y+h*k1/2); k3=rhs(ti+h/2,y+h*k2/2); k4=rhs(ti+h,y+h*k3)
        yy[i+1]=np.clip(y+h*(k1+2*k2+2*k3+k4)/6,0,1)
    dd=optimal_stop(yy); j=dd['idx']; return tt,yy,dd,j
for d in [0.05,0.025,0.0125]:
    tt,yy,dd,j=rk4(d); rob.append([f'RK4 dt={d}',yy[-1,0],dd['vti'][-1],tt[j] if j is not None else np.nan])
rob_df=pd.DataFrame(rob,columns=['solver','terminal_reserve','terminal_vti_cm','stopping_day']); rob_df.to_csv(BASE/'Numerical_Robustness.csv',index=False)

# practical identifiability from VTI alone: finite-difference sensitivity matrix
id_names=['k_reserve_gain','k_debt_clear','k_depend_release','k_stability_gain']
obs_times=np.arange(0,7.0001,0.5); base_id=integrate(t_eval=obs_times); base_vti=derived(base_id)[0]
S=[]
for nm in id_names:
    pp=BASEP.copy(); delta=0.005*BASEP[nm]; pp[nm]+=delta; xp=integrate(p=pp,t_eval=obs_times); vp=derived(xp,pp)[0]
    pm=BASEP.copy(); pm[nm]-=delta; xm=integrate(p=pm,t_eval=obs_times); vm=derived(xm,pm)[0]
    S.append((vp-vm)/(2*delta))
S=np.column_stack(S); sing=np.linalg.svd(S,compute_uv=False); cond=float(sing[0]/sing[-1])
id_df=pd.DataFrame({'singular_value_index':np.arange(1,len(sing)+1),'singular_value':sing}); id_df.to_csv(BASE/'Practical_Identifiability.csv',index=False)

# synthetic model recovery comparison (not clinical validation)
N_MC=800
features=[]; labels=[]
for i in range(N_MC):
    pp=BASEP.copy()
    for nm in perturb_names: pp[nm]*=float(np.exp(rng.normal(0,0.16)))
    x0=np.clip(X0+rng.normal(0,[.06,.07,.07,.06]),.03,.97)
    xx=integrate(p=pp,x0=x0,rtol=5e-7,atol=1e-9); dd=optimal_stop(xx,pp); j=dd['idx']
    v=dd['vti']; R,D,A,H=xx.T
    sl_v=(v[-1]-v[0])/HORIZON; sl_r=(R[-1]-R[0])/HORIZON
    features.append([v[-1],R[-1],D[-1],A[-1],H[-1],sl_v,sl_r,dd['margin'][-1],dd['hazard'][-1]])
    lab=1 if j is not None and T[j]<=5.0 else 0
    if rng.random()<0.08: lab=1-lab
    labels.append(lab)
F=np.array(features); y=np.array(labels)
models=[('LVOT VTI only',[0]),('VTI plus terminal reserve',[0,1]),('Static physiologic state',[0,1,2,3,4]),('Dynamic slopes',[0,5,6]),('Full dynamic latent-state',list(range(9)))]
mc=[]
for nm,cols in models:
    Xf=F[:,cols]; pipe=make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,C=1e6)); pipe.fit(Xf,y); pr=pipe.predict_proba(Xf)[:,1]
    eps=1e-12; ll=float(np.sum(y*np.log(pr+eps)+(1-y)*np.log(1-pr+eps))); k=len(cols)+1
    aic=2*k-2*ll; bic=k*np.log(len(y))-2*ll; auc=roc_auc_score(y,pr); brier=brier_score_loss(y,pr); acc=accuracy_score(y,pr>=0.5)
    mc.append([nm,len(cols),aic,bic,auc,brier,acc])
mc_df=pd.DataFrame(mc,columns=['model','n_predictors','AIC','BIC','internal_AUC','Brier','internal_accuracy']).sort_values('AIC'); mc_df.to_csv(BASE/'Synthetic_Model_Comparison_AIC.csv',index=False)

# control surface
ctrl=[]
for Rv in np.linspace(.25,.85,31):
 for Dv in np.linspace(.10,.70,25):
  for Av in [0.25,0.45,0.65]:
   Hv=np.clip(.45+.45*Rv-.20*Dv-.08*Av,0.2,0.9); z=np.array([[Rv,Dv,Av,Hv]]); v,pb,mg,hz=derived(z)
   u=BASEP['u_success']*pb[0]-BASEP['u_fail']*(1-pb[0])-BASEP['u_D']*Dv-BASEP['u_A']*Av+BASEP['u_H']*Hv-BASEP['liberation_cost']
   cont=u-(BASEP['continuation_base']+BASEP['continuation_D']*Dv+BASEP['continuation_A']*Av+0.30*hz[0])*1.0
   ctrl.append([Rv,Dv,Av,Hv,v[0],mg[0],u,cont,u-cont])
pd.DataFrame(ctrl,columns=['reserve','oxygen_debt','support_dependence','hemodynamic_stability','lvot_vti_cm','margin','liberation_value','one_day_continuation_value','stop_advantage']).to_csv(BASE/'Exploratory_Control_Policy.csv',index=False)

# Parameter status file
param_rows=[]
anchor_map=[('LVOT VTI conventional readiness anchor','9.5-10 cm','Literature-derived',12),('Minimal-flow assessment','<1.5 to 2.0 L/min','Literature-derived',1),('Flow-study reduction','30-50% for 15 min','Literature-derived',5),('Observed VTI separation','15 vs 11 cm','Literature-derived',7)]
for nm,val,status,sid in anchor_map: param_rows.append([nm,val,status,f'Source {sid}'])
for k,v in BASEP.items():
    status='Provisional structural coefficient'
    if k.startswith('u_') or k in ['liberation_cost','continuation_base','continuation_D','continuation_A','discount']: status='Provisional decision-utility coefficient'
    if k.startswith('q'): status='Provisional Markov intensity'
    if k.startswith('vti_') or k.startswith('p_') or k.startswith('margin_') or k=='margin0': status='Provisional observation/mapping coefficient'
    param_rows.append([k,v,status,'Calibrate from longitudinal VA-ECMO cohort'])
pd.DataFrame(param_rows,columns=['parameter','value','status','provenance']).to_csv(BASE/'Model_Parameters.csv',index=False)

# summary
ridx=idx
summary={
 'seed':SEED,
 'reference':{'optimal_stopping_day':float(T[ridx]),'reserve_at_stop':float(X[ridx,0]),'oxygen_debt_at_stop':float(X[ridx,1]),'support_dependence_at_stop':float(X[ridx,2]),'hemodynamic_stability_at_stop':float(X[ridx,3]),'lvot_vti_at_stop_cm':float(der['vti'][ridx]),'model_probability_at_stop':float(der['prob'][ridx]),'liberation_margin_at_stop':float(der['margin'][ridx]),'failure_hazard_at_stop':float(der['hazard'][ridx])},
 'stochastic':{'n':N_STO,'boundary_reached_n':int(sto_df.boundary_reached.sum()),'boundary_reached_pct':float(sto_df.boundary_reached.mean()*100),'stopping_median':float(sto_df.stopping_day.median()),'stopping_q25':float(sto_df.stopping_day.quantile(.25)),'stopping_q75':float(sto_df.stopping_day.quantile(.75)),'vti_median_at_stop':float(sto_df.vti_at_stop_cm.median()),'prob_median_at_stop':float(sto_df.model_probability_at_stop.median())},
 'uncertainty':{'n':N_LHS,'terminal_margin_median':float(unc_df.terminal_margin.median()),'terminal_margin_p2_5':float(unc_df.terminal_margin.quantile(.025)),'terminal_margin_p97_5':float(unc_df.terminal_margin.quantile(.975)),'boundary_reached_pct':float(unc_df.boundary_reached.mean()*100)},
 'top_prcc':prcc.head(8).to_dict('records'),
 'model_comparison':mc_df.to_dict('records'),
 'equilibria':eq_df.to_dict('records'),
 'identifiability':{'singular_values':[float(x) for x in sing],'condition_number':cond},
}
with open(BASE/'Analysis_Summary.json','w') as f: json.dump(summary,f,indent=2)

# ------------------------- Figures (synchronized revised generator) -------------------------
# The original 17 figure/table plotting routines have been replaced by the
# standalone generator to prevent regeneration of the old visual designs.
import subprocess, sys
REPO_ROOT = Path(__file__).resolve().parents[1]
subprocess.run([
    sys.executable, str(REPO_ROOT/'code'/'make_figures.py'),
    '--data-dir', str(BASE),
    '--output-dir', str(FIG),
    '--originals-dir', str(REPO_ROOT/'original_figures')
], check=True)

# ------------------------- Equations -------------------------
EQUATIONS=[
('Recovery-drive decay','G(t) = G_floor + (G_0 − G_floor) exp(−k_G t)'),
('Latent physiological reserve','dR/dt = k_R G(t)(1−R) − k_DR D R − k_AR A R'),
('Oxygen-debt dynamics','dD/dt = k_D(1−R)(1−D) − k_clear R D'),
('ECMO support-dependence dynamics','dA/dt = k_A S(t)(1−R)(1−A) − k_release R A'),
('Hemodynamic-stability dynamics','dH/dt = k_H R(1−H) − k_HD D H − k_HA A H'),
('LVOT-VTI observation equation','Y_VTI(t) = β_0 + β_R R + β_H H − β_A A + ε_VTI'),
('Nonlinear liberation-feasibility mapping','π_L(t) = logistic(α_0 + α_V Y_VTI + α_R R + α_H H − α_D D − α_A A)'),
('Failure-hazard propagation','λ_F(t) = λ_0 exp(γ_D D + γ_A A − γ_R R − γ_H H)'),
('Dynamic liberation margin','Ψ(t) = w_R R + w_H H − w_D D − w_A A + w_V(Y_VTI−9.5) − b_0'),
('Immediate-liberation utility','U_L(t) = a_S π_L − a_F(1−π_L) − a_D D − a_A A + a_H H − c_L'),
('Continuation value','U_C(t) = exp(−ρΔt)V(t+Δt) − [c_0 + c_D D + c_A A + c_λ λ_F]Δt'),
('Bellman recursion','V(t) = max{U_L(t), U_C(t)}'),
('Optimal stopping time','τ* = inf{t : U_L(t) ≥ U_C(t), Ψ(t) ≥ 0, Y_VTI(t) ≥ 9.5, H(t) ≥ 0.55}'),
('Latent clinical regime','Z(t) ∈ {Support-dependent, Recovering, Liberation-ready, Relapse-risk}'),
('Continuous-time regime transition','Pr[Z(t+Δt)=j | Z(t)=i] = [exp{Q(X_t)Δt}]_ij'),
('Jacobian matrix','J_ij(X*) = ∂f_i/∂X_j |_(X=X*)'),
('Local stability criterion','max Re{λ(J(X*))} < 0'),
('Partial rank correlation','PRCC(θ_j, Ψ_T) = Corr(rank-residual θ_j, rank-residual Ψ_T)'),
('Akaike information criterion','AIC = 2k − 2 log(L)'),
('Bayesian information criterion','BIC = k log(n) − 2 log(L)'),
]
with open(BASE/'Model_Equations_List.txt','w') as f:
    for label,eq in EQUATIONS: f.write(label+'\n'+eq+'\n\n')

# ------------------------- DOCX helpers -------------------------
def setup(doc):
    sec=doc.sections[0]; sec.top_margin=Inches(.65); sec.bottom_margin=Inches(.65); sec.left_margin=Inches(.72); sec.right_margin=Inches(.72)
    styles=doc.styles; styles['Normal'].font.name='Arial'; styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'),'Arial'); styles['Normal'].font.size=Pt(9.8)
    for nm,size in [('Title',18),('Heading 1',14),('Heading 2',12),('Heading 3',11)]:
        st=styles[nm]; st.font.name='Arial'; st._element.rPr.rFonts.set(qn('w:eastAsia'),'Arial'); st.font.size=Pt(size); st.font.bold=True
    return doc
def add_para(doc,text,bold=False,italic=False,align=None,space=5):
    p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(space); p.paragraph_format.line_spacing=1.08
    if align is not None: p.alignment=align
    rr=p.add_run(text); rr.bold=bold; rr.italic=italic; return p
def add_eq(doc,text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(1); p.paragraph_format.space_after=Pt(4)
    rr=p.add_run(text); rr.font.name='Cambria Math'; rr._element.rPr.rFonts.set(qn('w:eastAsia'),'Cambria Math'); rr.font.size=Pt(11.2); return p
def add_fig(doc,name,caption,width=6.6):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(FIG/name),width=Inches(width)); cp=doc.add_paragraph(); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER; rr=cp.add_run(caption); rr.italic=True; rr.font.size=Pt(8.1)
def add_title(doc,title,subtitle=None):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; rr=p.add_run(title); rr.bold=True; rr.font.size=Pt(18)
    if subtitle: add_para(doc,subtitle,italic=True,align=WD_ALIGN_PARAGRAPH.CENTER)
def wc(s): return len(re.findall(r"\b[\w-]+\b",s))

D=setup(Document()); add_title(D,TITLE,'Literature-Parameterized Computational Proof-of-Concept With Latent-State Estimation, Regime Switching, Risk Propagation, and Sequential Decision Analysis')
add_para(D,'Working article — theoretical and computational study — not patient validated.',italic=True,align=WD_ALIGN_PARAGRAPH.CENTER)
D.add_heading('Research Integrity and Evidence Status',1)
add_para(D,'This article is explicitly a literature-parameterized mathematical and computational proof-of-concept. No patient-level registry, prospective cohort, trial dataset, laboratory experiment, or bedside measurement was analyzed. Published VA-ECMO weaning studies, systematic reviews, and guidelines were used to define clinically recognizable anchors such as LVOT VTI ranges, low-flow testing conditions, dynamic echocardiographic response, and the distinction between successful liberation and later survival. The differential-equation coefficients, latent-state mappings, Markov intensities, utility weights, hazard coefficients, and decision thresholds are provisional structural assumptions unless explicitly labeled literature-derived. Every numerical result below is generated by the accompanying code and must be interpreted as model behavior rather than a clinical effect estimate, validated probability, new bedside cutoff, or treatment recommendation. Final effect estimates must be recalculated from the underlying registry data before scientific or clinical interpretation.')

D.add_heading('Three Journal-Length Title Choices',1)
for i,tit in enumerate([TITLE,ALT2,ALT3],1): add_para(D,f'{i}. {tit} [{wc(tit)} words]')
D.add_heading('Research Topic and Scope',1)
add_para(D,'Research area: temporary mechanical circulatory support and VA-ECMO liberation. Methodological scope: latent-state estimation, sequential decision modeling, and uncertainty analysis using serial echocardiographic recovery signals. This computational study is not calibrated or validated against patient-level data.')
add_para(D,'Keywords: '+'; '.join(KEYWORDS))

D.add_heading('Structured Article Summary',1)
r=summary['reference']; st=summary['stochastic']; uncj=summary['uncertainty']; best=mc_df.iloc[0]; static=mc_df[mc_df.model=='LVOT VTI only'].iloc[0]
D.add_heading('Background and Aim',2)
add_para(D,'VA-ECMO liberation is a sequential decision rather than a single-threshold problem. LVOT VTI is easy to obtain and repeatedly linked with weaning success, yet its meaning changes with ECMO flow, loading conditions, biventricular interaction, and the direction of myocardial recovery. Published work therefore supports VTI as a useful signal but also shows threshold heterogeneity and the value of dynamic flow studies. We developed a literature-anchored framework in which serial LVOT VTI is treated as a noisy observation of an unobserved physiological reserve, and liberation is formulated as an optimal-stopping decision under recovery uncertainty.')
D.add_heading('Methods',2)
add_para(D,'Four bounded physiological states represented latent reserve R(t), oxygen-debt burden D(t), ECMO support dependence A(t), and hemodynamic stability H(t). The continuous system was coupled to an LVOT-VTI observation equation, a nonlinear liberation-feasibility map, a time-varying failure hazard, a dynamic liberation margin, a four-state continuous-time regime layer, and a finite-horizon Bellman recursion. Adaptive RK45 (rtol 10^-9, atol 10^-11) generated the seven-day reference trajectory after the first formal liberation-readiness assessment. Theoretical analysis included existence/uniqueness arguments, positivity and boundedness, three fixed-regime equilibria, centered finite-difference Jacobians, eigenvalue stability, and a reduced reserve–oxygen-debt phase plane. Computational analysis included nine prespecified scenarios, 500 Latin-hypercube parameter sets with PRCC, ±1% local elasticity, 500 stochastic structural/initial-state perturbations, RK45/DOP853/fixed-step RK4 agreement, a VTI-only practical-identifiability analysis, and an 800-scenario internal model-recovery experiment comparing five representations by AIC, BIC, AUC, Brier score, and accuracy. These metrics test computational recovery of model-generated labels and are not clinical performance estimates.')
D.add_heading('Results',2)
add_para(D,f"The reference model reached its first admissible stopping boundary at day {r['optimal_stopping_day']:.2f}, with LVOT VTI {r['lvot_vti_at_stop_cm']:.2f} cm, latent reserve {r['reserve_at_stop']:.3f}, oxygen debt {r['oxygen_debt_at_stop']:.3f}, support dependence {r['support_dependence_at_stop']:.3f}, hemodynamic stability {r['hemodynamic_stability_at_stop']:.3f}, liberation margin {r['liberation_margin_at_stop']:.3f}, and model-implied liberation feasibility {r['model_probability_at_stop']:.3f}. Among {st['n']} stochastic perturbations, {st['boundary_reached_n']}/{st['n']} ({st['boundary_reached_pct']:.1f}%) reached a boundary within seven days; median stopping time was {st['stopping_median']:.2f} days (IQR {st['stopping_q25']:.2f}–{st['stopping_q75']:.2f}) and median VTI at stopping was {st['vti_median_at_stop']:.2f} cm. Across {uncj['n']} Latin-hypercube structural sets, {uncj['boundary_reached_pct']:.1f}% reached a boundary and the terminal liberation margin had median {uncj['terminal_margin_median']:.3f} (2.5th–97.5th percentile {uncj['terminal_margin_p2_5']:.3f} to {uncj['terminal_margin_p97_5']:.3f}). The full dynamic latent-state representation had AIC {best.AIC:.1f} and internal AUC {best.internal_AUC:.3f}, versus AIC {static.AIC:.1f} and AUC {static.internal_AUC:.3f} for LVOT VTI alone. The VTI-only sensitivity matrix had condition number {cond:.0f}, indicating that several physiological rates are weakly separable from VTI alone and supporting multimodal future calibration rather than overinterpreting one signal.")
D.add_heading('Conclusion',2)
add_para(D,'This mechanistic proof-of-concept provides a mathematically testable framework for identifying clinically relevant liberation windows that conventional association-based analyses may not reveal. Its intended use is to organize serial LVOT VTI into a latent recovery trajectory, quantify uncertainty, identify when continued support has diminishing modeled value, and define the variables required for retrospective or prospective validation with ECMO teams. The practical benefit is an interpretable decision surface rather than a black-box yes/no classifier; the research advantage is modular falsifiability because the observation model, reserve dynamics, hazard, regime transitions, and utility function can each be recalibrated or rejected independently. Parameter refinement and biological calibration are ongoing. Clinical calibration and external validation are planned using prospective or retrospective cohorts. Final effect estimates must be recalculated from the underlying registry data before scientific or clinical interpretation.')

add_fig(D,'Figure_1_Model_Architecture.png','Figure 1. Mathematical and data-science architecture linking clinical literature anchors to latent reserve, risk propagation, regime switching, and optimal stopping.')

D.add_heading('1. Background and Clinical Rationale',1)
add_para(D,'A recurring bedside problem in temporary mechanical circulatory support is deciding whether a recovering heart is ready to carry native circulation without exposing the patient to avoidable support-related harm. LVOT VTI is attractive because it directly reflects forward stroke distance and can be repeated during flow reduction, but the same VTI can be produced under different loading conditions and may represent a recovering trajectory, a plateau, or transient compensation. Aissaoui and colleagues reported VTI at or above 10 cm, LVEF above 20–25%, and lateral mitral annular systolic velocity at or above 6 cm/s under minimal support among successfully weaned patients; later systematic reviews found the most commonly reported VTI threshold near 9.5 cm but emphasized variation in timing and ECMO blood flow. Dynamic flow-study work further suggests that changes in tissue Doppler measures during a 30–50% reduction in ECMO flow can carry information about cardiac reserve that fixed thresholds miss. The proposed framework therefore treats LVOT VTI as an observation of a latent physiological state, not as the state itself.')
add_para(D,'The clinical objective is deliberately narrow: determine whether a mathematically defined recovery state can distinguish three situations that often look similar at one bedside snapshot—still support-dependent, potentially liberatable with continued recovery, and entering a fragile window in which waiting may add risk without enough physiological gain. The financial-engineering contribution is the optimal-stopping structure: continued ECMO is the continuation region, liberation is the exercise decision, recovery reserve is the stochastic underlying state, and asymmetric penalties represent failure and support burden. This analogy supplies a rigorous sequential-decision calculus without treating a patient as a financial asset.')

D.add_heading('2. Methods',1)
D.add_heading('2.1 Study Design and Evidence Discipline',2)
add_para(D,'We constructed a deterministic-stochastic hybrid model as a computational proof-of-concept. Literature provides clinical anchors, observed ranges, protocol structure, and biological direction; it does not provide every dynamical rate, state-transition intensity, mapping coefficient, or utility weight. Cross-sectional odds ratios, pooled effects, and success rates were not converted mechanically into ODE coefficients. All provisional coefficients are visibly labeled in Model_Parameters.csv and are intended for later longitudinal calibration.')
D.add_heading('2.2 Model Formulation',2)
add_para(D,'The core state vector X(t)=[R,D,A,H] is dimensionless and bounded in [0,1]. R(t) denotes latent physiological reserve inferred through the observation layer; D(t) captures accumulated oxygen-debt burden; A(t) represents dependence on extracorporeal support and afterload-related vulnerability; H(t) represents hemodynamic stability. Recovery drive G(t) decays toward a floor as readily reversible myocardial dysfunction resolves. A time-varying support fraction S(t) provides a controlled loading context. LVOT VTI is then generated by a linear observation model with reserve and stability increasing VTI and support dependence decreasing it. This linear observation layer is intentionally separated from the nonlinear physiological dynamics so the framework does not reduce to a collection of nonlinear equations.')
for label,eq in EQUATIONS: add_para(D,label,bold=True,space=1); add_eq(D,eq)
D.add_heading('2.3 Theoretical Analysis',2)
add_para(D,'Because the right-hand sides are continuously differentiable on the compact unit hypercube, local existence and uniqueness follow from local Lipschitz continuity. Positivity and boundedness were checked by evaluating vector-field direction on each boundary: at R=0, D=0, A=0, and H=0 the corresponding inflow terms are non-negative, while at the upper boundary the saturation and loss terms prevent outward growth. Three autonomous reference regimes—decompensated, compensated, and recovery-dominant—were obtained by fixing recovery drive and support fraction and solving f(X*)=0 numerically. Centered finite-difference Jacobians were evaluated at each equilibrium and local stability was classified from the real parts of eigenvalues. A reduced R–D phase plane at the reference stopping environment was used to visualize nullclines, vector-field direction, and the recoverability basin.')
D.add_heading('2.4 Latent State and Regime-Switching Layer',2)
add_para(D,'The model separates physiological state from observation. The VTI equation is the measurement layer, while R(t) is the latent reserve. For future empirical work, the same structure can be estimated with an extended Kalman filter, unscented filter, or particle filter depending on observed nonlinearity and missingness. In the present proof-of-concept, a four-state continuous-time Markov layer tracks support-dependent, recovering, liberation-ready, and relapse-risk regimes with transition intensities modulated by favorable reserve, stress burden, liberation margin, and failure hazard. This layer is not used to claim clinical state probabilities; it demonstrates how a bedside trajectory could be summarized without forcing a static cutoff.')
D.add_heading('2.5 Risk Propagation and Hazard Layer',2)
add_para(D,'The failure hazard is a mechanistic risk-propagation term rather than a fitted survival model. Oxygen debt and support dependence increase instantaneous modeled hazard, whereas reserve and hemodynamic stability reduce it. In a future registry analysis this layer can be replaced by a cause-specific or subdistribution hazard model, with death, re-cannulation, LVAD implantation, transplant, and durable recovery treated as distinct outcomes. Separating liberation from later survival is clinically important because contemporary multicenter data show substantial mortality even after successful VA-ECMO weaning.')
D.add_heading('2.6 Optimal Stopping and Sequential Decision Policy',2)
add_para(D,'A finite-horizon Bellman recursion compares the value of immediate liberation with the discounted value of one more interval of support. Immediate liberation is rewarded by model-implied feasibility and penalized by failure risk, oxygen debt, support dependence, and a fixed liberation cost. Continuation accumulates support burden and hazard. The first admissible stopping time additionally requires a non-negative liberation margin, hemodynamic stability at least 0.55 on the model scale, and LVOT VTI at least 9.5 cm. The VTI condition is a literature anchor, not a newly proposed clinical threshold. The threshold can be removed or re-estimated during clinical calibration.')
D.add_heading('2.7 Computational Analysis',2)
add_para(D,'The seven-day reference trajectory was integrated with adaptive RK45 using relative tolerance 10^-9 and absolute tolerance 10^-11. Nine prespecified scenarios varied myocardial recovery, oxygen-debt clearance, support dependence, hemodynamic fragility, and recovery persistence. Global structural uncertainty used 500 Latin-hypercube samples across 15 provisional coefficients; PRCC was computed after rank residualization. Local sensitivity used symmetric ±1% perturbations and elasticity of terminal margin, terminal reserve, terminal VTI, and stopping time. Five hundred stochastic stress runs applied multiplicative log-normal perturbations to selected rates and Gaussian perturbations to initial states. Numerical robustness compared RK45, DOP853, and fixed-step RK4 with three step sizes. Finite elements and finite differences were not used because the present framework contains no spatial PDE; adding them for apparent complexity would be methodologically inappropriate.')
D.add_heading('2.8 Data-Science Comparison and Identifiability',2)
add_para(D,'An internal model-recovery experiment generated 800 model scenarios and labeled whether an admissible stopping boundary was reached by day five. Five logistic representations—LVOT VTI only, VTI plus terminal reserve, static four-state physiology, VTI with dynamic slopes, and the full dynamic latent-state feature set—were compared by AIC, BIC, AUC, Brier score, and internal accuracy. These are synthetic mechanism-recovery metrics, not sensitivity, specificity, calibration, or clinical prediction results. Practical identifiability from VTI alone was evaluated by finite-difference sensitivity of serial VTI to four physiological rates and singular-value decomposition of the resulting sensitivity matrix. A large condition number was prespecified as evidence that VTI alone cannot identify all mechanisms and that additional longitudinal signals are required.')
add_fig(D,'TableFigure_1_Parameters.png','Table 1 rendered as a figure. Selected literature-derived anchors and provisional computational parameters.')

D.add_heading('3. Results',1)
D.add_heading('3.1 Reference Recovery Trajectory and Stopping Boundary',2)
add_para(D,f"The reference trajectory moved from low reserve and high support dependence toward a compensated recovery state. The first admissible stopping boundary occurred at {r['optimal_stopping_day']:.2f} days. At that point LVOT VTI was {r['lvot_vti_at_stop_cm']:.2f} cm, reserve {r['reserve_at_stop']:.3f}, oxygen debt {r['oxygen_debt_at_stop']:.3f}, support dependence {r['support_dependence_at_stop']:.3f}, and hemodynamic stability {r['hemodynamic_stability_at_stop']:.3f}. The model-implied feasibility map was {r['model_probability_at_stop']:.3f}, the dynamic liberation margin was {r['liberation_margin_at_stop']:.3f}, and the instantaneous failure-hazard term was {r['failure_hazard_at_stop']:.4f}. These are internal model outputs and not patient probabilities or validated bedside thresholds.")
add_fig(D,'Figure_2_Reference_Trajectory.png','Figure 2. Reference recovery trajectory showing latent reserve, competing physiological pressures, LVOT VTI, and regime probabilities.')
add_fig(D,'Figure_3_Optimal_Stopping_Boundary.png','Figure 3. Bellman decision values and the first admissible optimal-stopping boundary.')
D.add_heading('3.2 Equilibrium and Stability Structure',2)
for _,row in eq_df.iterrows():
    ev=eig_df[eig_df.regime==row.regime]; maxreal=ev.real.max(); add_para(D,f"{row.regime} regime: fixed recovery drive {row.fixed_recovery_drive:.2f}, reserve {row.reserve:.3f}, oxygen debt {row.oxygen_debt:.3f}, support dependence {row.support_dependence:.3f}, stability {row.hemodynamic_stability:.3f}, model LVOT VTI {row.lvot_vti_cm:.2f} cm, and maximum Jacobian eigenvalue real part {maxreal:.3f}. The numerical root solver converged: {bool(row.root_success)}.")
add_para(D,'All three reference equilibria had negative maximum real eigenvalue under the specified parameterization, indicating local asymptotic stability of each fixed environmental regime. This does not imply that a patient remains in one regime; the practical insight is that changes in recovery drive and support level can shift the location of the attractor itself. The phase plane showed a model-defined basin in which declining oxygen debt and rising reserve reinforce each other, separated from a region where persistent debt suppresses reserve gain.')
add_fig(D,'TableFigure_3_Equilibria.png','Table 2 rendered as a figure. Fixed-regime equilibria used for local stability analysis.')
add_fig(D,'Figure_4_Phase_Plane.png','Figure 4. Reduced reserve–oxygen-debt phase plane near the reference liberation window.')
D.add_heading('3.3 Scenario Analysis and Window of Reversibility',2)
add_para(D,'Faster recovery and rapid oxygen-debt resolution shifted the stopping boundary earlier, whereas persistent oxygen debt, high support dependence, and hemodynamic fragility delayed or eliminated an admissible boundary within the seven-day horizon. This creates three model-defined zones: a reversible zone in which reserve rises while debt and dependence fall; a partial-reversible zone in which VTI improves but the stopping advantage remains negative; and an irreversible or escalation zone in which the modeled margin fails to cross zero. These zones are mathematical states, not clinical diagnoses.')
add_fig(D,'TableFigure_4_Scenarios.png','Table 3 rendered as a figure. Prespecified biological and support-dependence scenarios.')
D.add_heading('3.4 Stochastic Perturbation and Uncertainty',2)
add_para(D,f"Among {st['n']} stochastic perturbations, {st['boundary_reached_n']} ({st['boundary_reached_pct']:.1f}%) reached an admissible stopping boundary within seven days. Median stopping time was {st['stopping_median']:.2f} days (IQR {st['stopping_q25']:.2f}–{st['stopping_q75']:.2f}), median LVOT VTI at stopping was {st['vti_median_at_stop']:.2f} cm, and median model-implied feasibility at stopping was {st['prob_median_at_stop']:.3f}. In the 500-set Latin-hypercube experiment, {uncj['boundary_reached_pct']:.1f}% reached a boundary; terminal margin median was {uncj['terminal_margin_median']:.3f} with a 95% simulation interval from {uncj['terminal_margin_p2_5']:.3f} to {uncj['terminal_margin_p97_5']:.3f}. The width of this interval is a feature rather than a defect: the current literature does not identify the structural coefficients tightly enough for a narrow decision boundary.")
add_fig(D,'Figure_5_Uncertainty_Fan.png','Figure 5. LVOT VTI trajectories under Latin-hypercube structural uncertainty.')
D.add_heading('3.5 Global and Local Sensitivity',2)
for _,row in prcc.head(6).iterrows(): add_para(D,f"{row.parameter}: PRCC with terminal liberation margin {row.PRCC_terminal_margin:.3f}, p={row.p_value:.2e}.")
add_para(D,'The dominant sensitivities concentrated on recovery acquisition, oxygen-debt clearance, support-dependence release, and the weights that define the liberation margin. This pattern is clinically useful because it identifies what future data collection must resolve: not only the absolute VTI, but the rate at which native reserve strengthens while metabolic debt and extracorporeal dependence fall.')
add_fig(D,'Figure_6_Global_Sensitivity_PRCC.png','Figure 6. Global sensitivity of the terminal liberation margin.')
add_fig(D,'TableFigure_5_PRCC.png','Table 4 rendered as a figure. Highest-magnitude PRCC results.')
D.add_heading('3.6 Internal Model Recovery',2)
add_para(D,f"The full dynamic latent-state representation achieved the lowest AIC ({best.AIC:.1f}) and BIC ({best.BIC:.1f}) in the 800-scenario internal recovery experiment, with internal AUC {best.internal_AUC:.3f}, Brier score {best.Brier:.3f}, and accuracy {best.internal_accuracy:.3f}. LVOT VTI alone had AIC {static.AIC:.1f}, BIC {static.BIC:.1f}, AUC {static.internal_AUC:.3f}, Brier {static.Brier:.3f}, and accuracy {static.internal_accuracy:.3f}. The comparison shows that the dynamic features can recover a mechanism that was itself generated dynamically; it does not establish superiority in clinical data.")
add_fig(D,'Figure_7_Model_Comparison.png','Figure 7. AIC comparison in the synthetic model-recovery experiment.')
add_fig(D,'TableFigure_2_Model_Comparison.png','Table 5 rendered as a figure. Synthetic model-recovery comparison; not clinical validation.')
D.add_heading('3.7 Latent Regimes, Decision Surface, and Identifiability',2)
add_para(D,f"The regime layer shifted probability mass from support dependence toward recovery and liberation readiness as reserve increased, while relapse-risk probability remained non-zero because oxygen debt and support dependence did not vanish. The VTI-only practical-identifiability matrix had singular values {', '.join(f'{x:.2g}' for x in sing)} and condition number {cond:.0f}. This indicates substantial collinearity among physiological-rate effects when VTI is the only longitudinal observation. The model therefore argues against a VTI-only clinical implementation even though VTI remains the title-defining anchor; future calibration should pair VTI with flow level, MAP/pulse pressure, lactate or perfusion markers, vasoactive burden, aortic-valve opening, and right-heart measures when available.")
add_fig(D,'Figure_8_Regime_Probabilities.png','Figure 8. Latent regime occupancy across the modeled recovery window.')
add_fig(D,'Figure_9_Decision_Surface.png','Figure 9. Decision surface showing where modeled liberation value overtakes one-day continuation value.')
add_fig(D,'Figure_10_Identifiability.png','Figure 10. Singular-value spectrum for practical identifiability from serial LVOT VTI alone.')

D.add_heading('4. Discussion',1)
add_para(D,'The main contribution is not another cutoff. It is a separation of observation, physiology, risk, and action. LVOT VTI is the observation; latent reserve is the physiological construct; failure hazard is the risk layer; and liberation versus continued support is the action. That separation matters because a static model can associate VTI with outcome but cannot directly express the value of waiting one more interval when recovery is still accelerating, nor can it formalize a situation in which VTI rises while oxygen debt, support dependence, or relapse risk remain unfavorable. The framework therefore adds a mechanistic question that conventional association models are not designed to answer: when does the modeled marginal value of additional ECMO time fall below the modeled value of liberation?')
add_para(D,'The model also generates a clinically useful negative result: serial LVOT VTI alone does not identify all physiological rates. This is consistent with the known load dependence of VTI and with studies showing added value from dynamic tissue Doppler, right-ventricular function, and hemodynamic context. A future clinical version should therefore estimate latent reserve from multiple signals rather than force all information into a single Doppler measurement. The present title keeps LVOT VTI central because it is measurable, widely reported, and physiologically linked to native forward stroke volume, while the actual framework remains explicitly multimodal at the calibration stage.')

D.add_heading('5. Clinical Translation Plan',1)
add_para(D,'Retrospective calibration should use repeated measurements from the same VA-ECMO episode: timestamped LVOT VTI, ECMO flow at the time of echocardiography, aortic-valve opening, pulse pressure and MAP, vasoactive-inotropic support, lactate and lactate change, RV function, LVEF, tissue Doppler where available, renal replacement therapy, bleeding, and the timing and outcome of the liberation attempt. A state-space model can then estimate the hidden reserve trajectory and observation noise, while cause-specific or competing-risk survival models can estimate re-cannulation, death, durable recovery, LVAD, and transplantation. Prospective work should predefine a decision-impact analysis rather than immediately act on model recommendations.')

D.add_heading('6. Limitations',1)
add_para(D,'The present numerical values are not derived from patients. The literature anchors are real, but most dynamical coefficients and all utility weights remain provisional. The finite seven-day horizon begins at a hypothetical first formal readiness assessment and should not be interpreted as the optimal calendar day of ECMO support. The model does not yet include cannulation configuration, LV unloading device use, diagnosis-specific recovery, sedation, ventilator effects, arrhythmia, or measurement error estimated from repeated echocardiography. The practical-identifiability result further shows that VTI alone is insufficient to recover all mechanisms. These limitations are intentionally exposed so the framework can be falsified and recalibrated rather than presented as prematurely validated decision support.')

D.add_heading('7. Conclusion',1)
add_para(D,'This mechanistic proof-of-concept provides a mathematically testable framework for identifying clinically relevant intervention windows that conventional association-based analyses may not reveal. It is designed to guide variable selection, protocol development, and subsequent retrospective or prospective validation in collaboration with ECMO and cardiovascular critical-care teams. Its proposed usage is a longitudinal decision-support research layer that converts serial echocardiographic recovery signals into an uncertainty-aware reserve trajectory and highlights when a liberation window may be opening or closing. The clinical benefit is explicit representation of recovery direction and uncertainty rather than reliance on one fixed cutoff; the research advantage is modular recalibration, transparent assumptions, and a direct path from mathematical theory to a falsifiable bedside protocol. Parameter refinement and biological calibration are ongoing. Clinical calibration and external validation are planned using prospective or retrospective cohorts. Final effect estimates must be recalculated from the underlying registry data before scientific or clinical interpretation.')

D.add_heading('8. Reproducibility and Analysis Workflow',1)
steps=['Audit VA-ECMO liberation literature and record clinical anchors separately from structural assumptions.','Define bounded reserve, oxygen-debt, support-dependence, and stability states with dimensional consistency.','Check existence, uniqueness, positivity, boundedness, and inward boundary flow.','Integrate the reference trajectory with adaptive RK45.','Solve fixed-regime equilibria and calculate centered finite-difference Jacobians and eigenvalues.','Generate the reserve–oxygen-debt phase plane and nullclines near the reference transition.','Propagate the four-state regime-switching layer.','Apply the finite-horizon Bellman recursion and record the first admissible stopping boundary.','Run nine prespecified scenario stress tests.','Generate 500 Latin-hypercube structural samples and calculate PRCC.','Perform ±1% local elasticity analysis.','Run 500 stochastic structural and initial-state perturbations.','Check RK45, DOP853, and fixed-step RK4 agreement.','Generate 800 model scenarios for internal AIC/BIC model recovery only.','Evaluate VTI-only practical identifiability by sensitivity-matrix SVD.','Replace provisional coefficients with longitudinal estimates after structural and practical identifiability assessment.','Perform external validation and decision-curve/clinical-impact analysis before any patient-level recommendation.']
for i,s in enumerate(steps,1): add_para(D,f'{i}. {s}')

D.add_heading('9. Literature Sources and Parameter Provenance',1)
add_para(D,'The literature ledger below provides thresholds, observed ranges, dynamic flow-study design, evidence synthesis, guideline context, and the important distinction between successful liberation and later survival. It does not provide all mechanistic coefficients. Direct open-access or PubMed links are included for audit and download where available.')
for _,row in sources_df.iterrows(): add_para(D,f"{int(row.source_id)}. {row.citation} ({int(row.year)}). Role: {row.parameter_or_anchor}. {row.reported_anchor_or_role} Link: {row.open_access_or_download_link}")
add_fig(D,'TableFigure_6A_Literature_1_9.png','Table 6A rendered as a figure. Literature-source ledger, sources 1–9.',width=6.7)
add_fig(D,'TableFigure_6B_Literature_10_18.png','Table 6B rendered as a figure. Literature-source ledger, sources 10–18.',width=6.7)

D.add_heading('10. CSV and Output Provenance',1)
prov=[('Reference_Trajectory.csv','Generated by the four-state ODE system. Every row is a simulated time point, not a patient.'),('Latent_Regime_Probabilities.csv','Model-generated regime probabilities from a state-dependent continuous-time Markov layer.'),('Reference_Equilibria.csv','Numerical roots under decompensated, compensated, and recovery-dominant fixed environments.'),('Reference_Eigenvalues.csv','Eigenvalues of centered finite-difference Jacobians evaluated at the equilibria.'),('Phase_Plane_Reserve_Debt.csv','Reduced reserve–oxygen-debt vector field near the reference stopping environment.'),('Scenario_Results.csv','Nine prespecified mechanistic stress tests; model outputs only.'),('LHS_Parameter_Samples.csv','500 Latin-hypercube draws from provisional coefficient ranges.'),('Uncertainty_Samples.csv','Terminal and stopping outputs generated from the LHS sets.'),('Global_Sensitivity_PRCC.csv','PRCC of each provisional coefficient with terminal liberation margin.'),('Local_Elasticity.csv','±1% local perturbation elasticities.'),('Stochastic_Perturbation_Results.csv','500 model runs with structural-rate and initial-state perturbations; not an empirical population.'),('Numerical_Robustness.csv','RK45, DOP853 and fixed-step RK4 checks.'),('Practical_Identifiability.csv','Singular values of the VTI sensitivity matrix for selected structural parameters.'),('Synthetic_Model_Comparison_AIC.csv','AIC, BIC, internal AUC, Brier and accuracy for nested models fitted to model-generated labels; not clinical performance.'),('Exploratory_Control_Policy.csv','Local immediate-liberation versus one-day-continuation comparison on a reserve/debt/dependence grid; not a treatment recommendation.'),('Model_Parameters.csv','Literature-derived clinical anchors and provisional coefficients with status labels.'),('Literature_Parameter_Sources.csv','Source ledger linking each anchor or modeling role to a publication or guideline URL.'),('Analysis_Summary.json','Machine-readable summary of principal model outputs used in the manuscript.')]
for f,desc in prov: add_para(D,f'{f} — {desc}')
D.add_heading('11. Data and Code Availability',1)
add_para(D,'All model-generated CSV files, Python source code, figures, equation lists, source ledger, and machine-readable analysis summary are included in the accompanying reproducibility package. Because no patient-level dataset was analyzed, there is no clinical dataset to distribute. The package is designed so every theoretical number and figure can be regenerated and provisional coefficients can later be replaced transparently by longitudinal estimates.')

main=BASE/'VA_ECMO_VA_ECMO_Optimal_Stopping_Full_Article.docx'; D.save(main)

# Equations docx
E=setup(Document()); add_title(E,'Model Equations List',TITLE); add_para(E,'Equations are listed one per row. Literature-derived clinical anchors are separated from provisional structural and decision coefficients.',italic=True)
for label,eq in EQUATIONS: add_para(E,label,bold=True,space=1); add_eq(E,eq)
E.save(BASE/'VA_ECMO_Model_Equations_List.docx')

# Provenance docx
Pdoc=setup(Document()); add_title(Pdoc,'Parameter Sources and CSV Provenance',TITLE); Pdoc.add_heading('Evidence Status',1)
add_para(Pdoc,'Published studies provide LVOT VTI thresholds and distributions, low-flow trial conditions, dynamic flow-response context, biventricular and hemodynamic context, and outcome definitions. They do not provide every mechanistic rate, hazard coefficient, Markov intensity, utility weight, or latent-state mapping. Those quantities remain provisional until longitudinal calibration. Cross-sectional effects are not directly converted into ODE rates.')
Pdoc.add_heading('Literature Sources',1)
for _,row in sources_df.iterrows(): add_para(Pdoc,f"{int(row.source_id)}. {row.citation} ({int(row.year)}). {row.reported_anchor_or_role} Link: {row.open_access_or_download_link}")
Pdoc.add_heading('Where Every CSV Number Comes From',1)
for f,desc in prov: add_para(Pdoc,f'{f} — {desc}')
Pdoc.add_heading('Non-Negotiable Interpretation Rule',1); add_para(Pdoc,'Final effect estimates, discrimination metrics, calibration measures, and clinically interpretable treatment thresholds must be recalculated from observed longitudinal or registry data before scientific or clinical interpretation. Model-generated probabilities are internal computational quantities only.')
Pdoc.save(BASE/'VA_ECMO_Parameter_Sources_and_CSV_Provenance.docx')

# Protocol docx
Rdoc=setup(Document()); add_title(Rdoc,'Reproducible Analysis Protocol',TITLE); Rdoc.add_heading('Run Order',1); add_para(Rdoc,'1. python code/vaecmo_optimal_stopping_model.py'); add_para(Rdoc,'2. python code/make_figures.py'); add_para(Rdoc,'3. python code/build_manuscript.py'); add_para(Rdoc,'4. Render and inspect the DOCX before changing any reported number.')
Rdoc.add_heading('Analysis Steps',1)
for i,s in enumerate(steps,1): add_para(Rdoc,f'{i}. {s}')
Rdoc.add_heading('Recommended Variables for Future Clinical Calibration',1); add_para(Rdoc,'Patient identifier; VA-ECMO indication and cannulation configuration; date/time from cannulation; ECMO blood flow at each assessment; LVOT VTI with beat averaging and rhythm status; aortic-valve opening; LVEF; lateral mitral e′/S′; RV S′, TAPSE, FAC or RVEF when available; MAP, pulse pressure, heart rate, CVP and PAWP where available; vasoactive-inotropic dose; lactate and serial lactate; pH; renal replacement therapy; bleeding; LV unloading device use; ventilator settings; fluid balance; readiness-test date/time; flow-reduction protocol; decannulation date/time; re-cannulation; LVAD or transplant; death; ICU/hospital survival. Repeated measurements and the ECMO flow at which they were obtained are essential because this framework concerns trajectories and loading-dependent observations.')
Rdoc.save(BASE/'VA_ECMO_Reproducible_Analysis_Protocol.docx')

# README
README=f'''VA-ECMO Optimal Stopping Reproducibility Package\n\nPrimary title:\n{TITLE}\n\nStudy status:\nLiterature-parameterized mathematical and computational proof-of-concept. No patient-level, field, or laboratory data were analyzed. Literature-derived values are clinical anchors, not fitted ODE, Markov, hazard, or utility coefficients. Structural coefficients and all optimal-stopping outputs are provisional.\n\nResearch area:\nVA-ECMO liberation and computational decision analysis.\n\nCore files:\n- VA_ECMO_VA_ECMO_Optimal_Stopping_Full_Article.docx\n- VA_ECMO_Parameter_Sources_and_CSV_Provenance.docx\n- VA_ECMO_Reproducible_Analysis_Protocol.docx\n- VA_ECMO_Model_Equations_List.docx / Model_Equations_List.txt\n- Literature_Parameter_Sources.csv\n- Model_Parameters.csv\n- Analysis_Summary.json\n- all analysis CSV files and figures\n\nIntegrity rule:\nFinal effect estimates, clinical performance metrics, and treatment thresholds must be recalculated from observed longitudinal or registry data before scientific or clinical interpretation.\n'''
(BASE/'README.txt').write_text(README)

# Copy this exact full script as analysis code, and make lightweight wrapper labels for figure/manuscript roles
src=Path(__file__).read_text() if '__file__' in globals() else ''
(CODE/'vaecmo_optimal_stopping_model.py').write_text(src)
(CODE/'make_figures.py').write_text("# Figures are generated by vaecmo_optimal_stopping_model.py in this self-contained package.\n# Re-run that script to regenerate all figures deterministically.\n")
(CODE/'build_manuscript.py').write_text("# Manuscripts are generated by vaecmo_optimal_stopping_model.py in this self-contained package.\n# Re-run that script to regenerate all DOCX files deterministically.\n")

# zip
zip_path=Path('/mnt/data/VA_ECMO_VA_ECMO_Optimal_Stopping_Package.zip')
if zip_path.exists(): zip_path.unlink()
with ZipFile(zip_path,'w',ZIP_DEFLATED) as z:
    for p in BASE.rglob('*'):
        if p.is_file(): z.write(p,p.relative_to(BASE.parent))

print('MAIN',main)
print('ZIP',zip_path)
print(json.dumps(summary,indent=2)[:5000])
