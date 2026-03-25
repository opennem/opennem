*Weekly Summary — ${ws.network} — Week ${ws.week_number} (${ws.week_start.strftime('%d %b')} - ${ws.week_end.strftime('%d %b %Y')})*

*Fueltech Mix*
% for row in ws.records:
<%
    arrow = ""
    if row.wow_change is not None:
        if row.wow_change > 1:
            arrow = "↑ +" + str(round(row.wow_change, 1)) + "%"
        elif row.wow_change < -1:
            arrow = "↓ " + str(round(row.wow_change, 1)) + "%"
        else:
            arrow = "→"
%>\
`${row.fueltech_label.ljust(20)}` ${'{:>8}'.format('{:,.1f}'.format(row.energy_gwh))} GWh  (${'{:>5}'.format('{:.1f}'.format(row.demand_proportion))}%)  ${arrow}
% endfor

*Total:* ${'{:,.1f}'.format(ws.total_energy_gwh)} GWh | *Renewables:* ${'{:.1f}'.format(ws.renewable_proportion)}%

% if ws.price_results:
*Price by Region*
% for pr in ws.price_results:
`${pr.network_region.ljust(8)}` $${'{:,.2f}'.format(pr.avg_price)}/MWh  (${'{:,.1f}'.format(pr.demand_energy_gwh)} GWh)
% endfor
% endif

% if ws.milestones:
*Notable Milestones*
% for m in ws.milestones[:5]:
• ${m.description or m.record_id} (significance: ${m.significance})
% endfor
% endif
