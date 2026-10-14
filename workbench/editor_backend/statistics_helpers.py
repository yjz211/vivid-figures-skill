"""Small deterministic statistics used by original-template data adapters."""
import numpy as np
from scipy.stats import chi2

def calibration(y,p):
    b=np.minimum((p*10).astype(int),9);xs=[];ys=[];width=[]
    for i in range(10):
        m=b==i
        if not m.any():continue
        q=y[m].mean();n=m.sum();xs.append(p[m].mean());ys.append(q);width.append(1.96*np.sqrt(q*(1-q)/n))
    return np.array(xs),np.array(ys),np.array(width)

def kaplan(time,event):
    xs=[0.];surv=[1.];low=[1.];high=[1.];s=1.;g=0.
    for ti in np.unique(time):
        n=np.sum(time>=ti);d=np.sum((time==ti)&(event==1))
        s*=1-d/n
        if 0<d<n:g+=d/(n*(n-d))
        se=s*np.sqrt(g);xs.append(ti);surv.append(s);low.append(max(0,s-1.96*se));high.append(min(1,s+1.96*se))
    return tuple(np.array(a) for a in [xs,surv,low,high])

def logrank(t1,e1,t2,e2):
    obs=exp=var=0.
    for ti in np.unique(np.r_[t1[e1==1],t2[e2==1]]):
        n1=np.sum(t1>=ti);n2=np.sum(t2>=ti);n=n1+n2
        d1=np.sum((t1==ti)&(e1==1));d2=np.sum((t2==ti)&(e2==1));d=d1+d2
        obs+=d1;exp+=n1*d/n
        if n>1:var+=n1*n2*d*(n-d)/(n*n*(n-1))
    return float(chi2.sf((obs-exp)**2/var,1)) if var>0 else 1.

def split_rhat(chains):
    n=chains.shape[1]//2
    if n<2 or chains.shape[0]<2:return float('nan')
    split=np.concatenate([chains[:,:n],chains[:,-n:]],axis=0)
    w=np.var(split,axis=1,ddof=1).mean();b=n*np.var(split.mean(axis=1),ddof=1)
    return float(np.sqrt(((n-1)/n*w+b/n)/w)) if w>0 else float('nan')

def egger(effects,se):
    from scipy.stats import t
    n=len(effects);X=np.column_stack([np.ones(n),1/se]);y=effects/se
    if n<3 or np.linalg.matrix_rank(X)<2:return 'Egger检验：样本不足或精度无变化'
    beta=np.linalg.lstsq(X,y,rcond=None)[0];sigma2=np.sum((y-X@beta)**2)/(n-2)
    err=np.sqrt(sigma2*np.linalg.inv(X.T@X)[0,0])
    if err<=0:return 'Egger检验：退化拟合'
    stat=beta[0]/err;p=2*t.sf(abs(stat),n-2)
    return f'Egger 检验：t={stat:.3f}, p={p:.4g}'
