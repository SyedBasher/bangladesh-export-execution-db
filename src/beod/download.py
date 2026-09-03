from __future__ import annotations
from pathlib import Path
import os, time, requests

DEFAULT_BACI_URL='https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS12_V202601.zip'
BACI_URL=os.getenv('BEOED_BACI_URL',DEFAULT_BACI_URL)


def download_file(url:str,dest:Path,chunk_size:int=8*1024*1024,retries:int=5)->Path:
    """Stream a source file with retry and optional HTTP range resume.

    The source URL can be overridden with BEOED_BACI_URL for mirrors or a
    manually hosted copy. Existing complete/non-empty files are retained.
    """
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and dest.stat().st_size>0: return dest
    tmp=dest.with_suffix(dest.suffix+'.part')
    for attempt in range(1,retries+1):
        start=tmp.stat().st_size if tmp.exists() else 0
        headers={'Range':f'bytes={start}-'} if start else {}
        try:
            with requests.get(url,stream=True,timeout=(30,900),headers=headers) as r:
                # A server may ignore Range and return 200; then restart cleanly.
                if start and r.status_code==200:
                    tmp.unlink(missing_ok=True); start=0
                r.raise_for_status()
                mode='ab' if start and r.status_code==206 else 'wb'
                with tmp.open(mode) as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk: f.write(chunk)
            tmp.replace(dest)
            return dest
        except Exception:
            if attempt==retries: raise
            time.sleep(min(60,5*attempt))
    return dest
