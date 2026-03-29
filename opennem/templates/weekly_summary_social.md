<%
renew_pct = '{:.1f}'.format(ws.renewable_proportion)
total = '{:,.0f}'.format(ws.total_energy_gwh)
top = ws.records[0] if ws.records else None
%>\
${ws.network} Week ${ws.week_number} energy summary: ${total} GWh generated, ${renew_pct}% from renewables.\
% if top:
 ${top.fueltech_label} led at ${'{:.0f}'.format(top.demand_proportion)}% of the mix.\
% endif

% if ws.milestones:

${ws.milestones[0].description or ws.milestones[0].record_id}\
% endif

openelectricity.org.au
