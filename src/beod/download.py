from __future__ import annotations

from pathlib import Path
import os
import time
import zipfile
from urllib.parse import urlparse

import requests

DEFAULT_BACI_URL = 'https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS12_V202601.zip'
BACI_URL = os.getenv('BEOED_BACI_URL', DEFAULT_BACI_URL)
BACI_LANDING_PAGE = 'https://www2.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37'

_BROWSER_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/152.0 Safari/537.36'
    ),
    'Accept': 'application/zip,application/octet-stream;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'identity',
    'Referer': BACI_LANDING_PAGE,
    'Connection': 'keep-alive',
}


def _valid_zip(path: Path) -> bool:
    """Return True for a readable, non-empty ZIP archive.

    This protects the Actions cache from preserving a partial/HTML error body
    under the BACI .zip filename.
    """
    if not path.exists() or path.stat().st_size <= 0:
        return False
    try:
        if not zipfile.is_zipfile(path):
            return False
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            if not names:
                return False
            # BACI HS12 archives contain annual CSVs and metadata.  We avoid a
            # hard-coded byte size because CEPII releases change over time.
            has_baci_csv = any('BACI_HS12_Y' in n and n.endswith('.csv') for n in names)
            return has_baci_csv
    except (OSError, zipfile.BadZipFile):
        return False


def _prime_cepii_session(session: requests.Session) -> None:
    """Best-effort visit to the BACI landing page before requesting the ZIP.

    CEPII occasionally rejects direct automated downloads from cloud-runner IPs
    with HTTP 403.  Priming supplies ordinary browser headers/cookies when the
    site expects them.  Failure here is non-fatal; the actual download is still
    attempted and retried.
    """
    try:
        session.get(BACI_LANDING_PAGE, timeout=(20, 60), allow_redirects=True)
    except requests.RequestException:
        pass


def download_file(
    url: str,
    dest: Path,
    chunk_size: int = 8 * 1024 * 1024,
    retries: int = 8,
) -> Path:
    """Stream a source file with retry, resume, validation and CEPII hardening.

    The source URL can be overridden with ``BEOED_BACI_URL``.  For ZIP files,
    an existing file is retained only if it is a readable BACI archive; a
    corrupt cache entry is removed and downloaded again.

    HTTP 403 is treated as an upstream-access problem rather than as a BEOED
    model failure.  The request is retried with browser-like headers and a
    primed CEPII session.  The GitHub workflow additionally caches the official
    BACI ZIP so successful future builds no longer depend on CEPII availability.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    is_zip = dest.suffix.lower() == '.zip'
    if dest.exists():
        if (not is_zip and dest.stat().st_size > 0) or (is_zip and _valid_zip(dest)):
            return dest
        dest.unlink(missing_ok=True)

    tmp = dest.with_suffix(dest.suffix + '.part')
    session = requests.Session()
    session.headers.update(_BROWSER_HEADERS)
    if 'cepii.fr' in urlparse(url).netloc.lower():
        _prime_cepii_session(session)

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        start = tmp.stat().st_size if tmp.exists() else 0
        headers = {'Range': f'bytes={start}-'} if start else {}
        try:
            with session.get(
                url,
                stream=True,
                timeout=(30, 900),
                headers=headers,
                allow_redirects=True,
            ) as r:
                # Cloud/CDN protection can be transient. Re-prime and retry.
                if r.status_code == 403:
                    raise requests.HTTPError(
                        f'403 Forbidden from upstream source {r.url}', response=r
                    )

                # A server may ignore Range and return 200; restart cleanly.
                if start and r.status_code == 200:
                    tmp.unlink(missing_ok=True)
                    start = 0
                elif start and r.status_code == 416:
                    # A completed .part can occur after an interrupted rename.
                    if is_zip and _valid_zip(tmp):
                        tmp.replace(dest)
                        return dest
                    tmp.unlink(missing_ok=True)
                    raise requests.HTTPError('HTTP 416 on incomplete partial download', response=r)

                r.raise_for_status()
                mode = 'ab' if start and r.status_code == 206 else 'wb'
                with tmp.open(mode) as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)

            if is_zip and not _valid_zip(tmp):
                tmp.unlink(missing_ok=True)
                raise ValueError(f'Downloaded file is not a valid BACI ZIP: {url}')

            tmp.replace(dest)
            return dest

        except Exception as exc:
            last_error = exc
            if attempt == retries:
                break
            # A fresh landing-page request can obtain/update anti-bot cookies.
            if isinstance(exc, requests.HTTPError) and getattr(exc.response, 'status_code', None) == 403:
                _prime_cepii_session(session)
            time.sleep(min(120, 10 * attempt))

    hint = (
        f'Unable to download {url} after {retries} attempts. '
        'The upstream server may be temporarily refusing GitHub-hosted runner IPs. '
        'Re-run the workflow later, or set BEOED_BACI_URL to an authorized mirror/copy. '
        'Once a download succeeds, the Full BEOED workflow caches the BACI release '
        'and subsequent builds reuse it.'
    )
    if last_error is not None:
        raise RuntimeError(hint) from last_error
    raise RuntimeError(hint)
