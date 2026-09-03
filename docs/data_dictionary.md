# Data dictionary

The canonical variable registry is `config/variables.yml`. Every field is tagged by:

- **layer**: source / derived / manufactured / model;
- **public**: whether it appears in the public research release;
- **definition**: precise interpretation;
- **source**: upstream source or BEOED calculation.

## Main tables

| Table | Grain | Purpose |
|---|---|---|
| `product_market_latest` | HS6 × destination | Latest research snapshot and screening layer |
| `bd_flows` | year × HS6 × destination | Bangladesh bilateral export history |
| `market_structure` | year × HS6 × destination | Destination market size and supplier structure |
| `bd_product` | year × HS6 | Bangladesh product experience |
| `bd_destination` | year × destination | Bangladesh destination familiarity |
| `execution_private` | HS6 × destination × vintage | Model probabilities, diagnostic flags and confidence fields |

See the Excel codebook included with the release for a spreadsheet-readable version.
