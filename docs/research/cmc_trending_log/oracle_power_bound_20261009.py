import numpy as np
rng=np.random.default_rng(20261009)
sig=.03; out={}
for model in ("iid","overlap7","persistent"):
  for n in (90,180,365):
    for mu in (0,.005,.01):
      R=4000; z=rng.standard_normal((R,n+6))
      if model=="iid": x=sig*z[:,:n]; lrv=sig**2
      elif model=="overlap7":
        c=np.cumsum(np.pad(z,((0,0),(1,0))),axis=1); x=sig*(c[:,7:7+n]-c[:,:n])/np.sqrt(7); lrv=7*sig**2
      else:
        x=np.empty((R,n)); s=sig*rng.standard_normal(R)
        for t in range(n): s=.85*s+sig*np.sqrt(1-.85**2)*z[:,t]; x[:,t]=s
        lrv=sig**2*(1.85/.15)
      t=(x.mean(1)+mu)/np.sqrt(lrv/n)   # ORACLE: true long-run variance known
      out[(model,n,mu)]=(t>1.6449).mean()
for k,v in out.items(): print(k, round(v,3))
for model,lrvm in (("iid",1),("overlap7",7),("persistent",1.85/.15)):
  print(model,"days for 80% oracle power at 0.5%:",round(lrvm*sig**2*(1.6449+0.8416)**2/.005**2), "| min detectable mean at 365d:",round(np.sqrt(lrvm*sig**2*(1.6449+0.8416)**2/365),4))
