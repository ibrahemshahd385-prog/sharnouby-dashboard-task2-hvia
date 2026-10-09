import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

u.header('📣 Marketing Attribution & Growth',
         'How efficient is the marketing money really — and what do the platforms over-claim?',
         '08_card05_marketing')

files = u.load()
m = u.campaigns()
pt = u.platform_table(m)

c = st.columns(5)
u.kpi(c[0], 'Marketing spend (3 years)', u.money(m['Spend_EGP'].sum() / 1e6))
u.kpi(c[1], 'Revenue claimed by platforms', u.money(m['Attributed_Revenue_EGP'].sum() / 1e6))
u.kpi(c[2], 'Claimed vs what really sold', f"{m['Attributed_Revenue_EGP'].sum() / m['actual_sales'].sum():.1f}x", inverse=True,
      help='Revenue the platforms claim ÷ the actual store + online sales of that product during the campaign.')
u.kpi(c[3], 'Campaigns that over-claim', f"{(m['Attributed_Revenue_EGP'] > m['actual_sales']).mean():.0%}", inverse=True)
u.kpi(c[4], 'Real sales lift during campaigns', f"{m['actual_sales'].sum() / m['baseline_sales'].sum() - 1:+.1%}",
      help='Product sales during the campaign vs the 4 weeks before. ~0% means the campaigns did not add sales we can see.')

l, r = st.columns(2)
with l:
    p = pt.sort_values('ROAS')
    fig = go.Figure(go.Bar(y=p['Platform'], x=p['ROAS'], orientation='h',
                           marker_color=[u.ORANGE if v < 2 else u.BLUE for v in p['ROAS']],
                           text=[f'{v:.1f}x' for v in p['ROAS']], textposition='outside'))
    fig.update_xaxes(title='Claimed ROAS (revenue ÷ spend)', range=[0, p['ROAS'].max() * 1.2])
    u.show(u.style(fig, 'WhatsApp/CRM returns 67x; Influencers barely 1x'))
with r:
    g = m.groupby('Platform')[['Attributed_Revenue_EGP', 'actual_sales']].sum().sort_values('Attributed_Revenue_EGP') / 1e6
    fig = go.Figure()
    fig.add_trace(go.Bar(y=g.index, x=g['Attributed_Revenue_EGP'], name='Claimed by platform', orientation='h', marker_color=u.LIGHT_BLUE))
    fig.add_trace(go.Bar(y=g.index, x=g['actual_sales'], name='Actually sold', orientation='h', marker_color=u.BLUE))
    fig.update_layout(barmode='group')
    fig.update_xaxes(title='EGP millions')
    u.show(u.style(fig, 'Every platform claims far more than really sold', legend=True))

show_pt = pt[['Platform', 'campaigns', 'spend', 'revenue', 'ROAS', 'CPA', 'CTR_%', 'CVR_%']].copy()
show_pt[['spend', 'revenue']] = (show_pt[['spend', 'revenue']] / 1e6).round(2)
u.table(show_pt.round(2).rename(columns={'campaigns': 'Campaigns', 'spend': 'Spend (M)', 'revenue': 'Claimed revenue (M)',
                                         'CPA': 'Cost per order (EGP)', 'CTR_%': 'Click rate %', 'CVR_%': 'Conversion %'}))

st.subheader('🔀 Budget simulator')
st.caption('Move money away from Influencers. Claimed ROAS is inflated, so use this to rank options — then prove it with a holdout test.')
a, b = st.columns(2)
cut = a.slider('Cut Influencer budget by (%)', 0, 100, 70, step=10) / 100
to_wa = b.slider('Share of the freed money that goes to WhatsApp/CRM (rest is saved)', 0, 100, 50, step=10) / 100
infl_yr = m.loc[m['Platform'] == 'Influencer', 'Spend_EGP'].sum() / 3
freed = infl_yr * cut
roas = pt.set_index('Platform')['ROAS']
k = st.columns(3)
u.kpi(k[0], 'Money freed per year', f'{freed / 1e6:.2f}M EGP')
u.kpi(k[1], 'Saved (straight to profit)', f'{freed * (1 - to_wa) / 1e6:.2f}M EGP')
u.kpi(k[2], 'Moved to WhatsApp/CRM', f'{freed * to_wa / 1e6:.2f}M EGP',
      help=f"At the claimed ROAS ({roas.get('WhatsApp / CRM', 0):.0f}x) this would 'bring' {freed * to_wa * roas.get('WhatsApp / CRM', 0) / 1e6:.1f}M — but WhatsApp only reaches customers who opted in, so returns will fall as spend grows.")
st.markdown('**How to prove it — holdout test:** keep 10% of opted-in customers out of every WhatsApp campaign for 8 weeks. '
            'The difference in sales between the two groups is the real effect. Same idea for one Meta region switched off.')

st.subheader('Campaign list')
f1, f2 = st.columns(2)
plat = f1.multiselect('Platform', sorted(m['Platform'].unique()), default=sorted(m['Platform'].unique()))
loss_only = f2.toggle('Show only campaigns with claimed ROAS < 1', value=False)
view = m[m['Platform'].isin(plat)]
if loss_only:
    view = view[view['roas_claimed'] < 1]
st.caption(f"{len(view)} campaigns · spend {view['Spend_EGP'].sum() / 1e6:.2f}M EGP")
out = view[['Campaign_Name', 'Platform', 'Start_Date', 'Spend_EGP', 'Attributed_Revenue_EGP', 'actual_sales', 'roas_claimed', 'Discount_Pct']].copy()
out['Start_Date'] = out['Start_Date'].dt.date
out[['Attributed_Revenue_EGP', 'actual_sales']] = out[['Attributed_Revenue_EGP', 'actual_sales']].round(0)
u.table(out.sort_values('roas_claimed').round(2).rename(columns={'Campaign_Name': 'Campaign', 'Start_Date': 'Start', 'Spend_EGP': 'Spend',
                                                                 'Attributed_Revenue_EGP': 'Claimed revenue', 'actual_sales': 'Actual sales',
                                                                 'roas_claimed': 'Claimed ROAS', 'Discount_Pct': 'Discount'}), height=320)

st.subheader('Website: conversion is slipping')
w = files['Web_Traffic_Daily'].copy()
w['FY'] = u.fiscal_year(w['Date'])
l, r = st.columns(2)
with l:
    mm = w.set_index('Date').resample('MS')[['Orders', 'Sessions']].sum()
    mm['cr'] = mm['Orders'] / mm['Sessions'] * 100
    fig = go.Figure(go.Scatter(x=mm.index, y=mm['cr'], mode='lines', line=dict(color=u.BLUE, width=2.5)))
    fig.update_yaxes(title='Conversion rate %')
    g = w.groupby('FY')[['Orders', 'Sessions']].sum()
    by_fy = g['Orders'] / g['Sessions'] * 100
    u.show(u.style(fig, f'Conversion fell from {by_fy.iloc[0]:.2f}% to {by_fy.iloc[-1]:.2f}%'))
with r:
    w['load'] = pd.cut(w['Avg_Page_Load_Sec'], [0, 2.5, 3.0, 3.5, 99], labels=['< 2.5s', '2.5–3s', '3–3.5s', '> 3.5s'])
    g = w.groupby('load', observed=True)[['Orders', 'Sessions']].sum()
    lb = g['Orders'] / g['Sessions'] * 100
    fig = go.Figure(go.Bar(x=lb.index.astype(str), y=lb.values, marker_color=[u.BLUE] * (len(lb) - 1) + [u.ORANGE],
                           text=[f'{v:.2f}%' for v in lb.values], textposition='outside'))
    fig.update_yaxes(title='Conversion rate %', range=[0, lb.max() * 1.25])
    fig.update_xaxes(title='Average page load time that day')
    u.show(u.style(fig, 'Slow pages (> 3.5s) convert worst'))
