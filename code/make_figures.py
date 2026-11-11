#!/usr/bin/env python3
"""Rebuild VA-ECMO Figures 1-10 and TableFigures 1-6B from existing CSV outputs.
Usage: python make_figures_revised.py --data-dir ./data --output-dir ./figures
No patient-level calibration. All plotted numerical points come from supplied CSVs.
"""
import argparse, textwrap, shutil
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import TwoSlopeNorm

P={'plum':'#703A65','magenta':'#B34F81','violet':'#7651A1','wine':'#943D58','teal':'#337D82','slate':'#536078','gold':'#A98542','ink':'#2C2935','gray':'#74717C','light':'#F6F2F6','rose':'#E7B6CC'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'semibold','axes.labelcolor':P['ink'],'text.color':P['ink'],'axes.edgecolor':'#B5AEB9','figure.facecolor':'white','savefig.facecolor':'white','axes.grid':False})

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,default=Path('data'));ap.add_argument('--output-dir',type=Path,default=Path('figures_revised'));ap.add_argument('--originals-dir',type=Path,default=Path('original_figures'));a=ap.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 def df(n):return pd.read_csv(a.data_dir/(n+'.csv'))
 def save(fig,n):fig.savefig(a.output_dir/n,dpi=220,bbox_inches='tight',pad_inches=.18);plt.close(fig);print('Created',n)
 def title(ax,s):ax.set_title(s,fontsize=13,pad=3,loc='left')
 def clean(ax):ax.grid(alpha=.14,color='#8B7A8E',lw=.7);ax.set_axisbelow(True)
 def dotline(ax,x,y,color,label=None,markevery=10,**kw):return ax.plot(x,y,color=color,lw=2.2,marker='o',ms=3.5,markevery=markevery,mec='white',mew=.5,label=label,**kw)
 ref=df('Reference_Trajectory'); t=ref.time_day.to_numpy(); scen=df('Scenario_Results'); stop=float(scen.loc[scen.scenario=='Reference','stopping_day'].iloc[0]);
 # Figure 1: single hue, alternating snake with unambiguous connectors
 fig,ax=plt.subplots(figsize=(13.5,8));ax.set_xlim(0,12);ax.set_ylim(0,8.3);ax.axis('off');fig.text(.075,.96,'Uncertainty Aware Optimal Stopping Architecture for VA-ECMO Liberation',fontsize=16,weight='bold',color=P['ink']);fig.text(.075,.925,'Literature-parameterized computational proof-of-concept: no patient level calibration',fontsize=10.7,color=P['gray'])
 blocks=[('Literature evidence','Clinical VTI anchors; weaning context'),('Model assumptions','Provisional coefficients and initial states'),('Nonlinear state equations','Reserve, oxygen debt, dependence, stability'),('Derived observables','LVOT VTI; model probability; margin'),('Finite-horizon decision','Stop-versus-continue comparison'),('Uncertainty analysis','LHS, stochastic runs, sensitivity'),('Internal diagnostics','Model comparisons; identifiability'),('Interpretation','Exploratory, not a clinical decision rule')]
 coords=[(1,6.15),(4.2,6.15),(7.4,6.15),(7.4,4.15),(4.2,4.15),(1,4.15),(1,2.15),(4.2,2.15)]
 for i,((head,sub),(x,y)) in enumerate(zip(blocks,coords)):
  ax.add_patch(FancyBboxPatch((x,y),2.75,1.25,boxstyle='round,pad=.16,rounding_size=.2',facecolor='#F3E9F1',edgecolor=P['plum'],lw=1.7))
  ax.text(x+1.375,y+.87,head,ha='center',va='center',fontsize=10.3,color=P['plum'],weight='bold');ax.text(x+1.375,y+.40,'\n'.join(textwrap.wrap(sub,31)),ha='center',va='center',fontsize=8.6,color=P['ink'])
 def arr(xy1,xy2):ax.add_patch(FancyArrowPatch(xy1,xy2,arrowstyle='-|>',mutation_scale=16,color=P['plum'],lw=2,connectionstyle='arc3'))
 for i in range(7):
  x,y=coords[i];xx,yy=coords[i+1]
  if y==yy: arr((x+2.93,y+.625),(xx-.16,yy+.625)) if xx>x else arr((x-.16,y+.625),(xx+2.93,yy+.625))
  else:arr((x+1.375,y-.16),(xx+1.375,yy+1.42))
 ax.text(6.0,.75,'Outputs describe simulated model behavior; no individual-level clinical validation.',ha='center',fontsize=9.5,color=P['gray']);save(fig,'Figure_1_Model_Architecture.png')
 # Figure 2
 fig,axs=plt.subplots(2,2,figsize=(12,8),sharex=True);fig.suptitle('Reference Literature Anchored VA-ECMO Recovery Trajectory',fontsize=15,weight='bold',y=.965)
 for ax,(cols,ylab) in zip(axs.flat,[(['reserve','hemodynamic_stability'],'Normalized state'),(['oxygen_debt','support_dependence'],'Normalized burden'),(['lvot_vti_cm'],'LVOT VTI (cm)'),(['model_liberation_probability','liberation_margin'],'Model outputs')]):
  for j,c in enumerate(cols):dotline(ax,t,ref[c],list(P.values())[j+2 if ylab=='Normalized state' else j+3],c.replace('_',' ').title(),markevery=9+j*3)
  ax.axvline(stop,color=P['wine'],ls=':',lw=1.4,alpha=.65);ax.set_ylabel(ylab);ax.legend(fontsize=8,loc='best',frameon=False);clean(ax)
 for ax in axs[-1]:ax.set_xlabel('Simulation day');save(fig,'Figure_2_Reference_Trajectory.png')
 # Figure 3
 fig,axs=plt.subplots(2,1,figsize=(11.5,8),sharex=True);title(axs[0],'Finite Horizon Optimal Stopping Boundary');dotline(axs[0],t,ref.stop_advantage,P['plum'],'Stop advantage',markevery=8);axs[0].axhline(0,color=P['slate'],ls='--',lw=1);axs[0].axvline(stop,color=P['wine'],ls=':',label=f'Reference first eligible stop: {stop:.2f} d');axs[0].legend(frameon=False);axs[0].set_ylabel('Stop minus continuation value');clean(axs[0]);dotline(axs[1],t,ref.lvot_vti_cm,P['magenta'],'LVOT VTI',markevery=11);axs[1].axhline(9.5,color=P['slate'],ls='--',label='9.5 cm reference anchor');axs[1].axvline(stop,color=P['wine'],ls=':');axs[1].set_ylabel('LVOT VTI (cm)');axs[1].set_xlabel('Simulation day');axs[1].legend(frameon=False);clean(axs[1]);fig.text(.13,.01,'Eligibility also requires margin, hemodynamic stability and model probability thresholds.',fontsize=9,color=P['gray']);save(fig,'Figure_3_Optimal_Stopping_Boundary.png')
 # Figures 4 and 5: preserve the exact user-supplied original plot pixels.
 # These reference images are included in original_figures/ for reproducibility.
 # No re-simulation or substitution of the uncertainty trajectories occurs.
 for number, filename in [(4,'Figure_4_Phase_Plane.png'),(5,'Figure_5_Uncertainty_Fan.png')]:
  src=a.originals_dir/filename
  if not src.exists():
   raise FileNotFoundError(f'Original Figure {number} required: {src}. The original plots must not be reconstructed from incomplete CSVs.')
  shutil.copyfile(src,a.output_dir/filename)
  print('Preserved original plot:',filename)
 # Figure 6
 pr=df('Global_Sensitivity_PRCC').sort_values('PRCC_terminal_margin');fig,ax=plt.subplots(figsize=(11,8));title(ax,'Global Sensitivity of Terminal Liberation Margin');colors=[P['magenta'] if v>0 else P['violet'] for v in pr.PRCC_terminal_margin];ax.barh(np.arange(len(pr)),pr.PRCC_terminal_margin,color=colors,alpha=.84,height=.69);ax.set_yticks(np.arange(len(pr)),pr.parameter,fontsize=9);ax.axvline(0,color=P['ink'],lw=.9);ax.set_xlabel('Partial rank correlation coefficient (PRCC)');clean(ax);save(fig,'Figure_6_Global_Sensitivity_PRCC.png')
 # Figure 7
 comp=df('Synthetic_Model_Comparison_AIC').sort_values('AIC');fig,axs=plt.subplots(1,2,figsize=(13,6.6));fig.suptitle('Internal Model Recovery Comparion',fontsize=15,weight='bold',y=.965);labels=comp.model.str.replace('Full dynamic latent-state','Full dynamic').str.replace('Static physiologic state','Static state').str.replace('VTI plus terminal reserve','VTI + reserve');y=np.arange(len(comp));axs[0].barh(y,comp.AIC,color=P['plum'],alpha=.83);axs[0].set(yticks=y,yticklabels=labels,xlabel='AIC (lower is better)');axs[0].invert_yaxis();axs[1].scatter(comp.internal_AUC,y,s=90,color=P['magenta'],label='Internal AUC');axs[1].plot(comp.internal_AUC,y,color=P['rose'],lw=1.2);axs[1].set(xlabel='Internal AUC (higher is better)',yticks=y,yticklabels=[]);axs[1].invert_yaxis();axs[1].set_xlim(.65,.92);[clean(z) for z in axs];fig.text(.1,.01,'Comparison uses synthetic/internal model outcomes; not external clinical validation.',fontsize=9,color=P['gray']);save(fig,'Figure_7_Model_Comparison.png')
 # Figure 8: transparent overlapping areas ALL anchored at y=0 (not stacked).
 regime=df('Latent_Regime_Probabilities');fig,ax=plt.subplots(figsize=(11,6.5));title(ax,'Latent Regime Occupancy Across the Recovery Window')
 forcols=['p_support_dependent','p_recovering','p_liberation_ready','p_relapse_risk']
 palette=[P['plum'],P['magenta'],P['violet'],P['wine']]
 for i,c in enumerate(forcols):
  x=regime.time_day.to_numpy();y=regime[c].to_numpy()
  ax.fill_between(x,0,y,color=palette[i],alpha=.17,zorder=1)
  ax.plot(x,y,color=palette[i],lw=2.1,label=c[2:].replace('_',' ').title(),zorder=3)
 ax.axvline(stop,color=P['gray'],ls=':',label='Reference stop',zorder=4)
 ax.set(xlabel='Days',ylabel='Model state probability',ylim=(0,1.02))
 ax.legend(frameon=False,ncol=3,fontsize=9,loc='upper center');clean(ax)
 save(fig,'Figure_8_Regime_Probabilities.png')
 # Figure 9: clear decision advantage surface using exact policy grid; no heatmap blocks
 policy=df('Exploratory_Control_Policy');fig,axs=plt.subplots(1,2,figsize=(13,5.8));fig.suptitle('Exploratory Liberation Decision Surface and Threshold Interpretation',fontsize=14,weight='bold',y=.965);pv=policy.pivot_table(index='oxygen_debt',columns='reserve',values='stop_advantage',aggfunc='mean');xs=pv.columns.to_numpy();ys=pv.index.to_numpy();z=pv.to_numpy();xx,yy=np.meshgrid(xs,ys);norm=TwoSlopeNorm(vcenter=0,vmin=min(z.min(),-.01),vmax=max(z.max(),.01));cf=axs[0].contourf(xx,yy,z,levels=20,cmap='PuRd',alpha=.9);axs[0].contour(xx,yy,z,levels=[0],colors=P['ink'],linewidths=2);axs[0].set(xlabel='Latent reserve',ylabel='Oxygen debt',title='Stop advantage (averaged across other grid states)');fig.colorbar(cf,ax=axs[0],label='Stop advantage');axs[1].scatter(policy.stop_advantage,policy.margin,c=np.where(policy.stop_advantage>=0,P['magenta'],P['violet']),s=9,alpha=.25);axs[1].axvline(0,color=P['ink'],ls='--');axs[1].axhline(0,color=P['ink'],ls=':');axs[1].set(xlabel='Stop advantage',ylabel='Liberation margin',title='Positive advantage and margin: necessary, not sufficient');clean(axs[1]);fig.text(.08,.005,'Positive stop advantage favors stopping in this exploratory value model; other eligibility criteria must also hold.',fontsize=9,color=P['gray']);save(fig,'Figure_9_Decision_Surface.png')
 # Figure 10
 ident=df('Practical_Identifiability');fig,ax=plt.subplots(figsize=(10.5,6.2));title(ax,'Practical Identifiability from LVOT VTI Alone');x=ident.singular_value_index.to_numpy();sv=ident.singular_value.to_numpy();ax.semilogy(x,sv,color=P['plum'],lw=2.5,marker='o',ms=10,mec='white',mew=1.2);ax.fill_between(x,sv,min(sv)*.7,color=P['rose'],alpha=.18);ax.set_xticks(x);ax.set(xlabel='Singular value index',ylabel='Singular value (log scale)');clean(ax);ax.annotate('Smallest singular value: weakly constrained direction',xy=(x[-1],sv[-1]),xytext=(2.0,.012),arrowprops={'arrowstyle':'->','color':P['wine']},color=P['wine'],fontsize=9);save(fig,'Figure_10_Identifiability.png')
 # Tables: dynamic row height and wrapped text with clipping
 def table_fig(data,name,heading,cols=None,width=16,wrap=33,font=8.2):
  d=data.copy();
  if cols:d=d[cols]
  d=d.fillna('—').astype(str)
  for c in d.columns:d[c]=d[c].map(lambda v:'\n'.join(textwrap.wrap(v,wrap,break_long_words=False,break_on_hyphens=False)) if len(v)>wrap else v)
  heights=[max(1,max(str(d.iloc[i,j]).count('\n')+1 for j in range(len(d.columns)))) for i in range(len(d))]
  height=min(45,max(2.5,.62+sum(.23+.18*h for h in heights)))
  fig,ax=plt.subplots(figsize=(width,height));ax.axis('off');fig.subplots_adjust(top=.955,bottom=.025,left=.02,right=.98)
  ax.text(.5,1.003,heading,transform=ax.transAxes,ha='center',va='bottom',fontsize=13,weight='bold')
  tbl=ax.table(cellText=d.values,colLabels=[c.replace('_',' ').title() for c in d.columns],cellLoc='left',colLoc='left',loc='upper center',bbox=[0,0,1,.985]);tbl.auto_set_font_size(False);tbl.set_fontsize(font)
  total=1.0+sum(1.15+.68*h for h in heights);header_h=1.0/total
  for (i,j),cell in tbl.get_celld().items():
   cell.set_edgecolor('#D7CCD7');cell.set_linewidth(.65);cell.PAD=.035;cell.get_text().set_va('center');cell.get_text().set_wrap(True)
   if i==0:cell.set_facecolor(P['plum']);cell.get_text().set_color('white');cell.get_text().set_weight('bold');cell.set_height(header_h)
   else:cell.set_facecolor('#F8F4F8' if i%2==0 else 'white');cell.set_height((1.15+.68*heights[i-1])/total)
  save(fig,name)
 table_fig(df('Model_Parameters'),'TableFigure_1_Parameters.png','Table 1. Model Parameters and Provenance',width=15,wrap=44,font=8)
 table_fig(comp,'TableFigure_2_Model_Comparison.png','Synthetic Model Recovery Comparison',width=14,wrap=25,font=9)
 table_fig(df('Reference_Equilibria'),'TableFigure_3_Equilibria.png','Table 3. Reference Equilibria',width=17,wrap=25,font=8)
 table_fig(scen,'TableFigure_4_Scenarios.png','Table 4. Scenario Results',width=16,wrap=28,font=8.5)
 table_fig(df('Global_Sensitivity_PRCC'),'TableFigure_5_PRCC.png','Table 5. Global Sensitivity PRCC',width=12,wrap=34,font=9)
 lit=df('Literature_Parameter_Sources');cols=['source_id','citation','year','parameter_or_anchor','reported_anchor_or_role','status'];table_fig(lit.iloc[:9],'TableFigure_6A_Literature_1_9.png','Table 6A. Literature Evidence and Clinical Anchors (1–9)',cols=cols,width=20,wrap=40,font=8)
 table_fig(lit.iloc[9:],'TableFigure_6B_Literature_10_18.png','Table 6B. Literature Evidence and Clinical Anchors (10–18)',cols=cols,width=20,wrap=40,font=8)
 print('All 17 PNG files generated in',a.output_dir)
if __name__=='__main__':main()
