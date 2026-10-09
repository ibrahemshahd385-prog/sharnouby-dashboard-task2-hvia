import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

u.header('📦 Smart Inventory & Replenishment',
         'Some products tie up cash while others run out — and nobody forecasts demand.',
         '07_card04_inventory')

inv = u.inventory()
snap = u.inventory_snapshot()
so = inv.groupby(['FY', 'Location'])['Stockout_Days_In_Month'].sum().unstack()
errors, future, std_daily, history = u.forecast_results()

c = st.columns(5)
u.kpi(c[0], 'Stock value (Sep 2026)', u.money(snap['stock_value'].sum() / 1e6))
u.kpi(c[1], 'Excess beyond 90 days', u.money(snap['excess_value'].sum() / 1e6),
      f"{snap['excess_value'].sum() / snap['stock_value'].sum():.0%} of stock", inverse=True)
u.kpi(c[2], 'Products below reorder point', f"{snap.loc[snap['below_reorder_point'], 'Product_ID'].nunique()} / {snap['Product_ID'].nunique()}")
u.kpi(c[3], 'Wholesale stockout days FY26', f"{so.loc['FY2026', 'Wholesale']:.0f}",
      f"{so.loc['FY2026', 'Wholesale'] / so.loc['FY2025', 'Wholesale'] - 1:+.0%} vs FY25", inverse=True)
u.kpi(c[4], 'AI forecast error (WAPE)', f"{errors['ai']:.1f}%", f"{errors['ai'] - errors['naive']:+.1f} pts vs last-year rule", inverse=True,
      help='Tested on Jul–Sep 2026, which the model never saw. Lower is better.')

tab1, tab2, tab3 = st.tabs(['Stock health', 'AI demand forecast', 'Replenishment plan'])

# ---------------------------------------------------------------- tab 1
with tab1:
    l, r = st.columns(2)
    with l:
        t = u.stock_turns()
        fig = go.Figure(go.Bar(x=t['Location'], y=t['days_of_stock'], marker_color=[u.CHANNEL_COLORS[x] for x in t['Location']],
                               text=[f'{d:.0f} days<br>({x:.1f} turns)' for d, x in zip(t['days_of_stock'], t['turns'])], textposition='outside'))
        fig.update_yaxes(title='Days of stock on hand (FY2026)', range=[0, t['days_of_stock'].max() * 1.25])
        u.show(u.style(fig, 'Store stock lasts 229 days, wholesale only 21'))
    with r:
        fig = go.Figure()
        for loc in ['Store', 'Online', 'Wholesale']:
            fig.add_trace(go.Bar(x=so.index, y=so[loc], name=loc, marker_color=u.CHANNEL_COLORS[loc]))
        fig.update_layout(barmode='group')
        fig.update_yaxes(title='Stockout days (all products)')
        u.show(u.style(fig, 'Wholesale stockouts almost quadrupled in two years', legend=True))

    l, r = st.columns(2)
    with l:
        ax = u.abc_xyz()
        ct = pd.crosstab(ax['ABC'], ax['XYZ']).reindex(index=['A', 'B', 'C'], columns=['X', 'Y', 'Z'], fill_value=0)
        fig = go.Figure(go.Heatmap(z=ct.values, x=['X (steady)', 'Y (seasonal)', 'Z (erratic)'], y=['A (80% of sales)', 'B (next 15%)', 'C (last 5%)'],
                                   text=ct.values, texttemplate='%{text}', colorscale=[[0, '#f4f8fd'], [1, u.BLUE]], showscale=False))
        fig.update_yaxes(autorange='reversed')
        u.show(u.style(fig, 'ABC / XYZ: no erratic products, so forecasting works'))
    with r:
        unmet = inv.groupby('FY')['unmet_units'].sum()
        fig = go.Figure(go.Bar(x=unmet.index, y=unmet.values, marker_color=u.ORANGE, text=[f'{v:,.0f}' for v in unmet.values], textposition='outside'))
        fig.update_yaxes(title='Units customers wanted but could not get', range=[0, unmet.max() * 1.2])
        u.show(u.style(fig, 'Unmet demand grew 7x in two years'))

    st.markdown('**Excess stock by product (Sep 2026)**')
    ex = snap.groupby(['Product_Name'])[['excess_units', 'excess_value']].sum().sort_values('excess_value', ascending=False).head(15).reset_index()
    ex['excess_value'] = (ex['excess_value'] / 1e3).round(0)
    u.table(ex.rename(columns={'Product_Name': 'Product', 'excess_units': 'Excess units', 'excess_value': 'Excess value (K EGP)'}))

# ---------------------------------------------------------------- tab 2
with tab2:
    pm = u.load()['Product_Master'].set_index('Product_ID')['Product_Name']
    l, r = st.columns(2)
    loc_pick = l.selectbox('Location', ['All', 'Store', 'Online', 'Wholesale'])
    names = ['All products'] + sorted(pm.unique())
    prod_pick = r.selectbox('Product', names)
    h, f = history.copy(), future.copy()
    h['Location'], f['Location'] = h['Location_ID'].map(u.LOC), f['Location_ID'].map(u.LOC)
    h['Product'], f['Product'] = h['Product_ID'].map(pm), f['Product_ID'].map(pm)
    if loc_pick != 'All':
        h, f = h[h['Location'] == loc_pick], f[f['Location'] == loc_pick]
    if prod_pick != 'All products':
        h, f = h[h['Product'] == prod_pick], f[f['Product'] == prod_pick]
    ht, ft = h.groupby('month')['Sold_Qty'].sum(), f.groupby('month')['forecast'].sum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ht.index, y=ht.values, name='Actual', mode='lines', line=dict(color=u.BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=[ht.index[-1]] + list(ft.index), y=[ht.values[-1]] + list(ft.values), name='AI forecast',
                             mode='lines+markers', line=dict(color=u.ORANGE, width=3, dash='dash')))
    fig.update_yaxes(title='Units sold per month')
    u.show(u.style(fig, 'AI forecast for the next 90 days (Oct–Dec 2026)', legend=True, height=420))
    a, b, c2 = st.columns(3)
    u.kpi(a, 'Next 30 days', f"{ft.iloc[0]:,.0f} units")
    u.kpi(b, 'Next 60 days', f"{ft.iloc[:2].sum():,.0f} units")
    u.kpi(c2, 'Next 90 days', f"{ft.sum():,.0f} units")
    st.caption(f"How we know it works: we hid Jul–Sep 2026 from the model and asked it to predict them. Error {errors['ai']:.1f}% vs "
               f"{errors['naive']:.1f}% for 'same as last year' → about {1 - errors['ai'] / errors['naive']:.0%} more accurate. "
               'Model: gradient boosting on last 1, 2, 3 and 12 months + month + location + product family + season.')

# ---------------------------------------------------------------- tab 3
with tab3:
    l, m_, r = st.columns(3)
    sl = l.selectbox('Service level (chance of NOT running out)', list(u.SERVICE_LEVEL_Z), index=1)
    loc_f = m_.multiselect('Location', ['Store', 'Online', 'Wholesale'], default=['Store', 'Online', 'Wholesale'])
    act_f = r.multiselect('Action', ['REORDER NOW', 'OVERSTOCK - transfer / promote', 'OK'], default=['REORDER NOW', 'OVERSTOCK - transfer / promote'])
    plan = u.replenishment_plan(u.SERVICE_LEVEL_Z[sl])
    view = plan[plan['Location'].isin(loc_f) & plan['action'].isin(act_f)]
    k = st.columns(4)
    u.kpi(k[0], 'Units to reorder now', f"{view['order_qty'].sum():,.0f}")
    u.kpi(k[1], 'Excess stock value', u.money(view['excess_value'].sum() / 1e6))
    u.kpi(k[2], 'Rows to reorder', f"{(view['action'] == 'REORDER NOW').sum()}")
    u.kpi(k[3], 'Rows overstocked', f"{(view['action'] == 'OVERSTOCK - transfer / promote').sum()}")
    cols = ['Location', 'Product_Name', 'Closing_Stock', 'forecast_30d', 'forecast_90d', 'safety_stock', 'reorder_point', 'order_qty', 'excess_vs_90d', 'action']
    out = view[cols].sort_values(['action', 'order_qty'], ascending=[False, False])
    u.table(out.rename(columns={'Product_Name': 'Product', 'Closing_Stock': 'Stock now', 'forecast_30d': 'Forecast 30d', 'forecast_90d': 'Forecast 90d',
                                'safety_stock': 'Safety stock', 'reorder_point': 'Reorder point', 'order_qty': 'Order qty', 'excess_vs_90d': 'Excess units',
                                'action': 'Action'}), height=380)
    st.download_button('⬇️ Download the replenishment plan (CSV)', out.to_csv(index=False).encode('utf-8-sig'), 'replenishment_plan.csv', 'text/csv')
    st.markdown('**Before buying: move stock between locations**')
    tr = u.transfers(plan)
    st.caption(f'{len(tr)} products / {tr["transfer_qty"].sum():,.0f} units that wholesale needs are sitting as excess in the store or online.')
    u.table(tr.head(15).rename(columns={'Product_Name': 'Product', 'wholesale_needs': 'Wholesale needs', 'store_excess': 'Store excess',
                                        'online_excess': 'Online excess', 'transfer_qty': 'Transfer'}).drop(columns='Product_ID'))
    st.caption('Safety stock = Z × daily demand variation × √lead time. Reorder point = daily demand × lead time + safety stock. '
               'Order up to = demand for (lead time + 30 days) + safety stock.')
