<%
renew_pct = '{:.1f}'.format(ws.renewable_proportion)
total = '{:,.0f}'.format(ws.total_energy_gwh)
week_range = ws.week_start.strftime('%-d %b') + ' - ' + ws.week_end.strftime('%-d %b %Y')
%>\
Open Electricity weekly summary for ${ws.network} (${week_range}). Renewables proportion at ${renew_pct}% on ${total} GWh of total generation.
% if ws.milestones:

${ws.milestones[0].description or ws.milestones[0].record_id}
% endif

https://explore.openelectricity.org.au/energy/${ws.network.lower()}/
