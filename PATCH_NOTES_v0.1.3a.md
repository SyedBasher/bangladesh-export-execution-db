# BEOED v0.1.3a — source-download resilience patch

This patch does **not** change BEOED analytical semantics or the v0.1.3 data schema.
It addresses an external infrastructure failure observed on 3 September 2026:
CEPII returned HTTP 403 to a GitHub-hosted runner while fetching the official
`BACI_HS12_V202601.zip` archive.

## Changes

1. `src/beod/download.py`
   - browser-like request headers and CEPII landing-page session priming;
   - retries HTTP 403 rather than immediately treating it as an analytical failure;
   - validates ZIP archives before accepting an existing/cached file;
   - retains range-resume support;
   - clearer failure message and `BEOED_BACI_URL` override remains available.

2. `.github/workflows/full_build.yml`
   - restores the immutable BACI 202601 ZIP from GitHub Actions cache;
   - if absent, downloads and validates it in a dedicated step;
   - saves the successful source ZIP immediately, before analytical build steps;
   - subsequent v0.1.3 rebuilds should therefore not contact CEPII at all.

## Versioning

Keep `beoed_schema_version = v0.1.3`. This is an infrastructure patch only.
