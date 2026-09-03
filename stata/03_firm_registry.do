* BEOED firm-capability seed: public professional/company data only
clear all
set more off

use "data/public/firm_registry/firm_registry_seed.dta", clear

describe
summarize n_observed_codes n_observed_hs4 capability_breadth_index

tab district
list company_name sector_tags district n_observed_hs4 in 1/15, noobs abbreviate(28)
