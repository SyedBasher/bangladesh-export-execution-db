clear all
set more off
global BEOED "data/public"
use "$BEOED/beoed_public_latest.dta", clear

* Illustrative screen: large/growing markets where Bangladesh's current share is low
keep if destination_market_usd >= 50000000
keep if market_cagr_5y > 0
keep if bd_market_share < .01

gsort -market_attractiveness -readiness_index
list hs6 product_name destination_name destination_market_usd market_cagr_5y bd_market_share ///
     market_attractiveness readiness_index in 1/25, noobs clean
