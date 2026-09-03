clear all
set more off

* Point this macro to the release folder.
global BEOED "data/public"

use "$BEOED/beoed_public_latest.dta", clear
format destination_market_usd bd_exports_to_destination_usd %15.0fc
format bd_market_share market_cagr_5y supplier_hhi top_supplier_share %9.3f
format market_attractiveness readiness_index %9.1f

describe
summarize destination_market_usd bd_market_share market_attractiveness readiness_index
