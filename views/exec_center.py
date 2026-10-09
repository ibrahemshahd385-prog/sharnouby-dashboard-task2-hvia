import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

u.header('🎯 Executive Command Center',
         'Revenue is growing — is it turning into profit, and where is margin leaking?',
         '04_card01_sales · 06_card03_channels · 13_card10_story')

files = u.load()
fy = u.fy_summary()
fys = list(fy.index)
pick = st.selectbox('Fiscal year (Oct–Sep)', fys, index=len(fys) - 1)
row = fy.loc[pick]
prev = fy.loc[fys[fys.index(pick) - 1]] if fys.index(pick) > 0 else None
ch = u.channel_fy()
chy = ch[ch['FY'] == pick].set_index('Channel')
online_share = chy.loc['Online', 'net_sales'] / chy.loc[['Online', 'Retail'], 'net_sales'].sum()
copq = u.copq_by_fy().loc[pick, 'total']


def delta(col, pct=True):
    if prev is None:
        return None
    return f'{(row[col] / prev[col] - 1):+.1%}' if pct else f'{(row[col] - prev[col]) * 100:+.1f} pts'


c = st.columns(6)
u.kpi(c[0], 'Net sales', u.money(row['net_sales'] / 1e6), delta('net_sales'))
u.kpi(c[1], 'Gross profit', u.money(row['gross_profit'] / 1e6), delta('gross_profit'))
u.kpi(c[2], 'Gross margin', f"{row['margin']:.1%}", delta('margin', pct=False))
u.kpi(c[3], 'Discounts given', u.money(row['discount'] / 1e6), delta('discount'), inverse=True,
      help='Gross sales minus net sales. Over 3 years discounts were 2.8x gross profit.')
u.kpi(c[4], 'Online share', f'{online_share:.0%}', help='Online vs the Sidi Bishr store (wholesale excluded).')
u.kpi(c[5], 'Poor quality cost', u.money(copq), inverse=True,
      help='QC scrap + quality refunds + print rework + reprint ink (Card 07).')

# ---------------------------------------------------------------- trend + channel mix
left, right = st.columns([3, 2])
with left:
    m = u.monthly_sales()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m['Month'], y=m['net_sales'] / 1e6, name='Net sales', mode='lines', line=dict(color=u.BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=m['Month'], y=m['gross_profit'] / 1e6, name='Gross profit', mode='lines', line=dict(color=u.AQUA, width=2.5)))
    fig.update_yaxes(title='EGP millions per month')
    show_title = 'Sales peak every December — profit stays a thin slice of it'
    u.show(u.style(fig, show_title, legend=True))
with right:
    shares = ch[ch['FY'] == pick].set_index('Channel').reindex(['Wholesale', 'Retail', 'Online'])
    sales_pct = shares['net_sales'] / shares['net_sales'].sum() * 100
    gp_pct = shares['gross_profit'] / shares['gross_profit'].sum() * 100
    names = ['Wholesale', 'Store', 'Online']
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=sales_pct, name='% of sales', marker_color=u.LIGHT_BLUE,
                         text=[f'{v:.0f}%' for v in sales_pct], textposition='outside'))
    fig.add_trace(go.Bar(x=names, y=gp_pct, name='% of gross profit', marker_color=u.BLUE,
                         text=[f'{v:.0f}%' for v in gp_pct], textposition='outside'))
    fig.update_layout(barmode='group')
    fig.update_yaxes(title='%', range=[0, 105])
    u.show(u.style(fig, 'Store + online: small in sales, big in profit', legend=True))

# ---------------------------------------------------------------- alerts
st.subheader('🚨 What needs attention now')
inv = u.inventory()
so = inv[inv['Location'] == 'Wholesale'].groupby('FY')['Stockout_Days_In_Month'].sum()
snap = u.inventory_snapshot()
below = snap.loc[snap['below_reorder_point'], 'Product_ID'].nunique()
sup = u.supplier_metrics().set_index('Supplier_ID')
camp = u.campaigns()
infl = camp[camp['Platform'] == 'Influencer']
s = files['Sales_Transactions']
size_share = s.loc[s['is_size_return'], 'Refund_Value_EGP'].sum() / s.loc[s['is_return'], 'Refund_Value_EGP'].sum()
alerts = [
    ('Sales', f"Discounts ({fy['discount'].sum() / 1e6:.0f}M) are **{fy['discount'].sum() / fy['gross_profit'].sum():.1f}x gross profit** over 3 years. Orders with 32–38% discount earn only 8.6% margin.", 'Executive (this page)'),
    ('Inventory', f"Wholesale stockout days went **{so.iloc[0]:.0f} → {so.iloc[-1]:.0f}** while half the stock (7.9M) is excess. **{below} products** are below their reorder point.", 'Smart Inventory'),
    ('Suppliers', f"SUP09 is late **{sup.loc['SUP09', 'late_rate']:.0%}** of the time and SUP04 (contracted) **{sup.loc['SUP04', 'late_rate']:.0%}** — vs ~30% for the rest.", 'Procurement & Supplier Risk'),
    ('Marketing', f"Platforms claim **{camp['Attributed_Revenue_EGP'].sum() / camp['actual_sales'].sum():.1f}x** the sales that actually happened. Influencer ROAS is only **{infl['Attributed_Revenue_EGP'].sum() / infl['Spend_EGP'].sum():.2f}**.", 'Marketing'),
    ('Factory', f"Cost of poor quality is **{u.copq_by_fy()['total'].sum():.1f}M** in 3 years = {u.copq_by_fy()['total'].sum() / (fy['gross_profit'].sum() / 1e6):.0%} of gross profit. Sewing + finishing cause 68% of delay days.", 'Factory Digital Twin'),
    ('Customers', f"Size / fit is **{size_share:.0%} of all refunds** and the #1 support question — online returns 2x more for size than the store.", 'Size & Fit Intelligence'),
]
for area, text, page in alerts:
    st.markdown(f'- **{area}:** {text} → *{page}*')

# ---------------------------------------------------------------- profit bridge (what-if)
st.subheader('💰 Action plan: how much profit is on the table?')
with st.expander('Adjust the assumptions (every number below updates live)', expanded=False):
    a, b, c3 = st.columns(3)
    cap = a.slider('Wholesale discount cap (%)', 20, 40, 30, step=1) / 100
    holding = a.slider('Yearly holding cost of excess stock (%)', 10, 30, 20) / 100
    copq_cut = b.slider('Reduce cost of poor quality by (%)', 0, 40, 20) / 100
    infl_cut = b.slider('Cut Influencer spend by (%)', 0, 100, 70, step=10) / 100
    size_cut = c3.slider('Cut size/fit returns by (%)', 0, 50, 30, step=5) / 100
    winback = c3.slider('At-risk customers won back (%)', 0, 40, 20, step=5) / 100
    include_wb = c3.toggle('Include win-back (needs a control-group test first)', value=True)

at_risk_rev = u.rfm().loc[lambda d: d['segment'].str.startswith('At Risk'), 'monetary'].sum() / 3 / 1e6
plan, b_in, cap_gain, breakeven = u.profit_bridge(cap=cap, winback=winback, at_risk_rev=at_risk_rev, holding=holding,
                                                  excess=7.4, influencer_cut=infl_cut, copq_cut=copq_cut, size_cut=size_cut,
                                                  include_winback=include_wb)
base = b_in['base_profit']
total = plan['profit_M'].sum()

fig = go.Figure(go.Waterfall(
    x=['FY2026 profit'] + list(plan['short']) + ['Potential'],
    hovertext=['FY2026 gross profit'] + list(plan['action']) + ['Potential gross profit'],
    y=[base] + list(plan['profit_M']) + [0],
    measure=['absolute'] + ['relative'] * len(plan) + ['total'],
    text=[f'{base:.1f}M'] + [f'+{v:.1f}' for v in plan['profit_M']] + [f'{base + total:.1f}M'],
    textposition='outside',
    increasing=dict(marker=dict(color=u.AQUA)), totals=dict(marker=dict(color=u.BLUE)),
    connector=dict(line=dict(color='#d6d5d0'))))
fig.update_yaxes(title='Gross profit, EGP millions / year', range=[0, (base + total) * 1.15])
u.show(u.style(fig, f'{len(plan)} actions could lift gross profit by ~{total:.1f}M EGP a year (+{total / base:.0%})', height=440))

k = st.columns(4)
u.kpi(k[0], 'Profit today (FY2026)', u.money(base))
u.kpi(k[1], 'Potential uplift / year', u.money(total), f'+{total / base:.0%}')
u.kpi(k[2], 'Biggest lever', plan.iloc[0]['short'] if len(plan) else '-', help=plan.iloc[0]['action'] if len(plan) else None)
u.kpi(k[3], 'Discount cap break-even', f'{breakeven:.0%}',
      help='The cap stays profitable unless wholesale volume drops by more than this.')

growth = b_in['growth']
fy27 = b_in['base_sales'] * (1 + growth) * (base / b_in['base_sales'])
wh_after = (b_in['wh_profit'] + cap_gain) * (1 + growth)
scen = pd.DataFrame({
    'Scenario': ['A. Do nothing', 'B. Action plan', 'C. Action plan, wholesale loses 10% volume'],
    'Gross profit FY2027 (M EGP)': [fy27, fy27 + total, fy27 + total - 0.10 * wh_after],
})
scen['vs FY2026'] = (scen['Gross profit FY2027 (M EGP)'] / base - 1).map('{:+.0%}'.format)
scen['Gross profit FY2027 (M EGP)'] = scen['Gross profit FY2027 (M EGP)'].round(1)
u.table(scen)
st.caption(f'FY2027 assumes sales grow {growth:.1%} (same as FY2026) with the same margin. '
           'Every action has its assumption written next to it in notebook 13_card10_story.')
u.insight('The company sells a lot but does not manage profit: discounts, excess stock, suppliers and quality all leak margin. '
          f'The discount cap alone is worth {cap_gain:.1f}M a year — the single biggest lever.')
