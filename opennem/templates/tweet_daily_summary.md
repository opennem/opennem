```
Daily Summary for ${ds.trading_day.strftime("%a %-d %b %Y")} for ${ds.network}

% for row in ds.records:
${row.fueltech_label.rjust(20)}: ${'{:,}'.format(int(row.energy)).rjust(8)} GWh (${row.demand_proportion} %)
% endfor

Renewable proportion: ${round(ds.renewable_proportion, 2)}%
```
