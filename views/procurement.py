import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

u.header('🚚 Procurement, Cost & Supplier Risk',
         'Which suppliers put production at risk, and how fast are material costs rising?',
         '12_card09_suppliers')

files = u.load()
po = files['Purchase_Orders'].copy()
po['FY'] = u.fiscal_year(po['Order_Date'])
po['Year'] = po['Order_Date'].dt.year
g = u.supplier_metrics()

c = st.columns(4)
u.kpi(c[0], 'Supplier on-time delivery', f"{po['On_Time'].mean():.1%}")
u.kpi(c[1], 'Average delay (all POs)', f"{po['Delay_Days'].mean():.1f} days", inverse=True)
u.kpi(c[2], 'Purchase orders', f'{len(po):,}')
u.kpi(c[3], 'Suppliers per material', f"{po.groupby('Material_ID')['Supplier_ID'].nunique().min()}",
      help='Every material can be bought from 12 suppliers → switching is easy.')

st.subheader('Supplier risk score')
st.caption('Each factor is scaled 0–1 (worst supplier = 1), then weighted. Change the weights to match what matters most to the company.')
a, b, c2, d = st.columns(4)
w_late = a.slider('Late deliveries', 0, 100, 35, step=5)
w_delay = b.slider('Average delay days', 0, 100, 25, step=5)
w_var = c2.slider('Unpredictable lead time (std)', 0, 100, 15, step=5)
w_spend = d.slider('Share of our spend (exposure)', 0, 100, 25, step=5)
g['risk'] = u.risk_score(g, w_late, w_delay, w_var, w_spend)
g = g.sort_values('risk', ascending=True)
l, r = st.columns([3, 2])
with l:
    fig = go.Figure(go.Bar(y=g['Supplier_ID'] + ' · ' + g['Primary_Category'], x=g['risk'], orientation='h',
                           marker_color=[u.RED if v >= 60 else (u.ORANGE if v >= 40 else u.LIGHT_BLUE) for v in g['risk']],
                           text=[f'{v:.0f}' for v in g['risk']], textposition='outside'))
    fig.update_xaxes(title='Risk score (0 = safest, 100 = riskiest)', range=[0, 110])
    top = g.iloc[-1]
    u.show(u.style(fig, f"{top['Supplier_ID']} and {g.iloc[-2]['Supplier_ID']} stand far above every other supplier", height=470))
with r:
    t = g.sort_values('risk', ascending=False)[['Supplier_ID', 'Primary_Category', 'Contracted', 'late_rate', 'avg_delay', 'lt_std', 'reject_rate', 'spend_share', 'risk']].copy()
    t['late_rate'] = (t['late_rate'] * 100).round(0)
    t['reject_rate'] = (t['reject_rate'] * 100).round(2)
    t['spend_share'] = (t['spend_share'] * 100).round(1)
    u.table(t.round(1).rename(columns={'Supplier_ID': 'Supplier', 'Primary_Category': 'Category', 'late_rate': 'Late %', 'avg_delay': 'Avg delay (days)', 'lt_std': 'Lead-time std (days)',
                                       'reject_rate': 'Reject %', 'spend_share': 'Spend share %', 'risk': 'Risk'}), height=470)

l, r = st.columns(2)
with l:
    y = po.groupby(['Year', 'Supplier_ID'])['On_Time'].mean().unstack()
    late = (1 - y) * 100
    others = late.drop(columns=['SUP04', 'SUP09']).mean(axis=1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=late.index, y=late['SUP09'], name='SUP09', mode='lines+markers', line=dict(color=u.RED, width=3)))
    fig.add_trace(go.Scatter(x=late.index, y=late['SUP04'], name='SUP04 (contracted)', mode='lines+markers', line=dict(color=u.ORANGE, width=3)))
    fig.add_trace(go.Scatter(x=late.index, y=others, name='Other 10 suppliers (avg)', mode='lines+markers', line=dict(color=u.GREY, width=2, dash='dot')))
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(title='% of orders late', range=[0, 100])
    u.show(u.style(fig, 'Since 2025, SUP09 and SUP04 are late most of the time', legend=True))
with r:
    mat = files['Materials'].set_index('Material_ID')['Material_Category']
    po['Category'] = po['Material_ID'].map(mat)
    cost = po.groupby(['FY', 'Category'])['Unit_Cost_EGP'].mean().unstack()
    idx = cost / cost.iloc[0] * 100
    fig = go.Figure()
    palette = [u.ORANGE, u.BLUE, u.AQUA, u.GREY, u.LIGHT_BLUE]
    for col, colr in zip(idx.columns, palette):
        fig.add_trace(go.Scatter(x=idx.index, y=idx[col], name=f'{col} ({idx[col].iloc[-1] - 100:+.1f}%)', mode='lines+markers', line=dict(color=colr, width=2.5)))
    fig.update_yaxes(title='Unit cost index (FY2024 = 100)')
    u.show(u.style(fig, f"Since FY2024: trims {idx['Trims'].iloc[-1] - 100:+.0f}%, printing {idx['Printing'].iloc[-1] - 100:+.0f}%, fabric {idx['Fabric'].iloc[-1] - 100:+.0f}%", legend=True))

u.insight('Supplier delays show up in the factory one quarter later: correlation 0.07 in the same quarter vs 0.48 with the previous quarter. '
          'This is an indicator, not proof — the crises also coincide with the start of peak season. '
          'Action: SLA penalties for late delivery, move volume from SUP09 to on-time suppliers (every material has 12 options), '
          'and safety stock for thread, labels and poly bags, which go into all 59 products.')
