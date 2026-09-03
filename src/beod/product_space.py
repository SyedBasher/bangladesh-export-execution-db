from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd


def zscore(x):
    x=np.asarray(x,dtype=float)
    sd=np.nanstd(x)
    return (x-np.nanmean(x))/sd if sd>0 else x*0


def compute_latest_complexity(country_product_file:Path, bd_code:int=50) -> tuple[pd.DataFrame,pd.DataFrame]:
    """Replicate a transparent Hausmann-Hidalgo style RCA/ECI/PCI layer.

    Uses the latest BACI country x HS6 export matrix. PCI/density are derived
    variables and should be cross-checked against an independent implementation
    before external publication.
    """
    d=pd.read_parquet(country_product_file,columns=['country_code','hs6','export_value_usd'])
    d['hs6']=d['hs6'].astype(str).str.zfill(6)
    countries=np.sort(d['country_code'].unique())
    products=np.sort(d['hs6'].unique())
    ci={c:i for i,c in enumerate(countries)}; pi={p:i for i,p in enumerate(products)}
    X=np.zeros((len(countries),len(products)),dtype=np.float64)
    rr=d['country_code'].map(ci).to_numpy(); cc=d['hs6'].map(pi).to_numpy()
    np.add.at(X,(rr,cc),d['export_value_usd'].to_numpy(float))
    ctot=X.sum(axis=1); ptot=X.sum(axis=0); world=X.sum()
    expected=np.outer(ctot,ptot)/world
    rca=np.divide(X,expected,out=np.zeros_like(X),where=expected>0)
    M=(rca>=1.0).astype(np.float64)
    kc=M.sum(axis=1); kp=M.sum(axis=0)
    valid_c=kc>0; valid_p=kp>0
    B=np.zeros_like(M)
    B[np.ix_(valid_c,valid_p)]=M[np.ix_(valid_c,valid_p)]/np.sqrt(np.outer(kc[valid_c],kp[valid_p]))
    U,S,Vt=np.linalg.svd(B,full_matrices=False)
    idx=1 if len(S)>1 else 0
    eci_raw=np.divide(U[:,idx],np.sqrt(kc),out=np.full(len(kc),np.nan),where=kc>0)
    pci_raw=np.divide(Vt[idx,:],np.sqrt(kp),out=np.full(len(kp),np.nan),where=kp>0)
    corr=np.corrcoef(np.nan_to_num(eci_raw),kc)[0,1]
    if np.isfinite(corr) and corr<0: eci_raw*=-1; pci_raw*=-1
    eci=zscore(eci_raw); pci=zscore(pci_raw)

    cdf=pd.DataFrame({'country_code':countries,'eci':eci,'diversity_rca1':kc.astype(int),'total_exports_usd':ctot})
    pdf=pd.DataFrame({'hs6':products,'pci':pci,'ubiquity_rca1':kp.astype(int),'world_exports_usd':ptot})
    pdf['pci_rank']=pdf['pci'].rank(method='min',ascending=False).astype('Int64')

    if bd_code in ci:
        b=ci[bd_code]
        active=M[b,:]
        density=np.full(len(products),np.nan,dtype=float)
        # Chunked co-occurrence avoids allocating a full P x P float matrix.
        M16=M.astype(np.uint16)
        for start in range(0,len(products),300):
            end=min(start+300,len(products))
            co=M16[:,start:end].T @ M16
            den=np.maximum(kp[start:end,None],kp[None,:])
            phi=np.divide(co,den,out=np.zeros_like(co,dtype=float),where=den>0)
            for local,pidx in enumerate(range(start,end)):
                phi[local,pidx]=0.0
            denom=phi.sum(axis=1)
            numer=phi @ active
            density[start:end]=np.divide(numer,denom,out=np.zeros_like(numer,dtype=float),where=denom>0)
        pdf['density_bd']=density
        pdf['rca_bd']=rca[b,:]
        pdf['bd_rca1']=active.astype(bool)
        pdf['bd_exports_usd']=X[b,:]
    return cdf,pdf
