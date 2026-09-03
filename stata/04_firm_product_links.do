* Observed EPB firm-product links. These are registry relationships, not capacity claims.
clear all
set more off

use "data/public/firm_registry/firm_product_links_seed.dta", clear

tab hs2
bysort epb_exporter_id: egen n_hs4 = nvals(hs4)
list company_name observed_hs_code hs4 link_type in 1/25, noobs abbreviate(28)
