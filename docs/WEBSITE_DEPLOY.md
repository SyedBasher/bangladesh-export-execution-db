# Deploy the BEOED website with GitHub Pages

This package is designed for GitHub Pages served from the repository's `/docs` folder.

## Install the site files
Copy the contents of this package's `docs/` folder into the existing repository `docs/` folder. Keep the existing methodology PDFs and Markdown documentation. `index.html` will become the public landing page; the technical Markdown files remain available as direct links.

## Enable GitHub Pages
1. On GitHub open **Settings** for `bangladesh-export-execution-db`.
2. In the left menu choose **Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**.
4. Branch: **main**.
5. Folder: **/docs**.
6. Click **Save**.

The public address should become:

`https://syedbasher.github.io/bangladesh-export-execution-db/`

## Current public explorer
The site currently embeds the v0.3 firm-capability seed (28 firms / 104 observed firm-product links). These JSON files are generated only from the already-public, non-personal fields in the seed.

## When the full v0.1 build is ready
Do not redesign the site. Replace or add a product-market explorer backed by a compact JSON/CSV extract produced from the full Parquet database. Keep full Parquet/DuckDB files in GitHub Releases rather than loading them into the browser.

## Commercial boundary
Do not publish the private entry/survival probabilities, candidate-firm scores, constraint classifications or client-specific scenario outputs unless you make a deliberate release decision.
