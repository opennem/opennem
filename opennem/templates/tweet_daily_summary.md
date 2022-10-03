```
Daily Summary for ${ds.trading_day.strftime("%a %-d %b %Y")} for ${ds.network}

% if ds.chart_url:
    ![${ds.chart_url}](${ds.chart_url})
% endif

% for row in ds.records:
${row.fueltech_label.rjust(24)}: ${'{:,}'.format(int(row.energy)).rjust(8)} GWh (${'{:03}'.format(round(row.demand_proportion, 2)).rjust(6)} %)
% endfor

                   Total:  ${'{:,}'.format(int(ds.total_energy)).rjust(6)} GWh

Renewable proportion: ${round(ds.renewable_proportion, 2)}%
```
