const state = { firms: [], links: [], search: '', district: '', sector: '' };
const $ = (s) => document.querySelector(s);

async function loadData(){
  try{
    const [firms, links] = await Promise.all([
      fetch('assets/firm_registry.json').then(r=>r.json()),
      fetch('assets/firm_product_links.json').then(r=>r.json())
    ]);
    state.firms = firms; state.links = links;
    populateFilters(); render();
  } catch(err){
    $('#firmTable').innerHTML = `<tr><td colspan="5">The public explorer could not load. View the CSV downloads below.</td></tr>`;
    $('#resultCount').textContent = 'Explorer unavailable';
    console.error(err);
  }
}

function populateFilters(){
  const districts=[...new Set(state.firms.map(d=>d.district).filter(Boolean))].sort();
  const sectors=[...new Set(state.firms.flatMap(d=>String(d.sector_tags||'').split(/[;,]/)).map(s=>s.trim()).filter(Boolean))].sort();
  districts.forEach(v=>$('#district').insertAdjacentHTML('beforeend',`<option>${escapeHtml(v)}</option>`));
  sectors.forEach(v=>$('#sector').insertAdjacentHTML('beforeend',`<option>${escapeHtml(v)}</option>`));
}
function linksFor(id){ return state.links.filter(d=>String(d.epb_exporter_id)===String(id)); }
function matches(f){
  const links=linksFor(f.epb_exporter_id);
  const q=state.search.toLowerCase().trim();
  const hay=[f.company_name,f.sector_tags,f.district,...links.map(x=>x.observed_hs_code),...links.map(x=>x.hs4)].join(' ').toLowerCase();
  const sectorMatch=!state.sector || String(f.sector_tags||'').toLowerCase().includes(state.sector.toLowerCase());
  return (!q||hay.includes(q)) && (!state.district||f.district===state.district) && sectorMatch;
}
function render(){
  const rows=state.firms.filter(matches).sort((a,b)=>a.company_name.localeCompare(b.company_name));
  $('#resultCount').textContent=`${rows.length} firms · ${rows.reduce((n,f)=>n+linksFor(f.epb_exporter_id).length,0)} observed links`;
  $('#firmTable').innerHTML=rows.length?rows.map(f=>{
    const ls=linksFor(f.epb_exporter_id).sort((a,b)=>String(a.hs4).localeCompare(String(b.hs4)));
    const pills=ls.slice(0,9).map(x=>`<span class="hs-pill">${escapeHtml(String(x.observed_hs_code))}</span>`).join('') + (ls.length>9?` <span class="hs-pill">+${ls.length-9}</span>`:'');
    return `<tr>
      <td class="company-cell"><strong>${escapeHtml(f.company_name)}</strong><small>${escapeHtml(f.thana||'')}${f.thana&&f.district?', ':''}${escapeHtml(f.district||'')}</small></td>
      <td>${escapeHtml(f.sector_tags||'—')}</td>
      <td>${escapeHtml(f.district||'—')}</td>
      <td>${pills||'—'}</td>
      <td><span class="grade">${escapeHtml(f.confidence_grade||'A')}</span></td>
    </tr>`;
  }).join(''):`<tr><td colspan="5">No matching firms.</td></tr>`;
}
function escapeHtml(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));}

$('#search').addEventListener('input',e=>{state.search=e.target.value;render()});
$('#district').addEventListener('change',e=>{state.district=e.target.value;render()});
$('#sector').addEventListener('change',e=>{state.sector=e.target.value;render()});
$('#reset').addEventListener('click',()=>{state.search='';state.district='';state.sector='';$('#search').value='';$('#district').value='';$('#sector').value='';render()});
loadData();
