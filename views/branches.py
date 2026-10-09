import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

u.header('🗺️ Branch Intelligence & Expansion',
         'Which channel creates value (not just sales), and where should the next store open?',
         '06_card03_channels')

files = u.load()
s = files['Sales_Transactions']
ch = u.channel_fy()
p = ch.pivot(index='FY', columns='Channel', values='net_sales')
growth = p.pct_change().iloc[-1]
tot = ch.groupby('Channel')[['net_sales', 'gross_profit']].sum()
b2c_sales = tot.loc[['Online', 'Retail'], 'net_sales'].sum() / tot['net_sales'].sum()
b2c_gp = tot.loc[['Online', 'Retail'], 'gross_profit'].sum() / tot['gross_profit'].sum()

c = st.columns(5)
u.kpi(c[0], 'Online growth FY26', f"{growth['Online']:+.0%}")
u.kpi(c[1], 'Store growth FY26', f"{growth['Retail']:+.1%}")
u.kpi(c[2], 'Wholesale growth FY26', f"{growth['Wholesale']:+.1%}", help='Was +10.4% in FY25 — growth is slowing.')
u.kpi(c[3], 'B2C share of sales', f'{b2c_sales:.1%}')
u.kpi(c[4], 'B2C share of profit', f'{b2c_gp:.1%}')

l, r = st.columns(2)
with l:
    fig = go.Figure()
    for name in ['Online', 'Retail']:
        fig.add_trace(go.Scatter(x=p.index, y=p[name] / 1e6, name='Store' if name == 'Retail' else name, mode='lines+markers+text',
                                 line=dict(color=u.CHANNEL_COLORS[name], width=3),
                                 text=[''] * (len(p) - 1) + [f'{p[name].iloc[-1] / 1e6:.1f}M'], textposition='middle right'))
    fig.update_xaxes(range=[-0.2, len(p) - 0.4])
    fig.update_yaxes(title='Net sales, EGP millions', range=[0, p[['Online', 'Retail']].max().max() / 1e6 * 1.25])
    u.show(u.style(fig, 'Online overtook the store in FY2025 and keeps growing', legend=True))
with r:
    m = ch.pivot(index='FY', columns='Channel', values='margin') * 100
    fig = go.Figure()
    for name in ['Online', 'Retail', 'Wholesale']:
        fig.add_trace(go.Bar(x=m.index, y=m[name], name='Store' if name == 'Retail' else name, marker_color=u.CHANNEL_COLORS[name],
                             text=[f'{v:.0f}%' for v in m[name]], textposition='outside'))
    fig.update_layout(barmode='group')
    fig.update_yaxes(title='Gross margin %', range=[0, m.max().max() * 1.25])
    u.show(u.style(fig, f"Store {m['Retail'].iloc[-1]:.0f}% and online {m['Online'].iloc[-1]:.0f}% margin vs wholesale {m['Wholesale'].iloc[-1]:.0f}%", legend=True))

st.subheader('📍 Where to open the next store')
on = s[s['Channel'] == 'Online'].copy()
on['Region'] = on['Customer_Governorate'].replace({'Cairo': 'Greater Cairo', 'Giza': 'Greater Cairo'})
g = on.groupby('Region').agg(sales=('Net_Sales_EGP', 'sum'), customers=('Customer_ID', 'nunique'))
g26 = on[on['FY'] == 'FY2026'].groupby('Region')['Net_Sales_EGP'].sum()
g25 = on[on['FY'] == 'FY2025'].groupby('Region')['Net_Sales_EGP'].sum()
g['growth_FY26_%'] = (g26 / g25 - 1) * 100
g['has_store'] = np.where(g.index == 'Alexandria', 'Yes (Sidi Bishr)', 'No')
g = g.sort_values('sales', ascending=True)
l, r = st.columns([3, 2])
with l:
    fig = go.Figure(go.Bar(y=g.index, x=g['sales'] / 1e6, orientation='h',
                           marker_color=[u.ORANGE if i == 'Greater Cairo' else (u.BLUE if i == 'Alexandria' else u.LIGHT_BLUE) for i in g.index],
                           text=[f'{v / 1e6:.1f}M' for v in g['sales']], textposition='outside'))
    fig.update_xaxes(title='Online sales, 3 years (EGP millions)', range=[0, g['sales'].max() / 1e6 * 1.2])
    u.show(u.style(fig, 'Greater Cairo buys online as much as Alexandria — with no store', height=460))
with r:
    t = g.sort_values('sales', ascending=False).head(6).copy()
    t['sales'] = (t['sales'] / 1e6).round(2)
    u.table(t.round(1).reset_index().rename(columns={'Region': 'Region', 'sales': 'Online sales (M)', 'customers': 'Online customers',
                                                      'growth_FY26_%': 'Growth FY26 %', 'has_store': 'Store?'}))
    u.insight('Greater Cairo (Cairo + Giza) = the same online sales as Alexandria, without a single store. '
              'Next step: a pop-up store or shop-in-shop in Cairo for 3 months, then measure sales vs a similar city.')

st.subheader('Returns and wholesale accounts')
l, r = st.columns(2)
with l:
    rr = ch.groupby('Channel')[['returns', 'lines']].sum()
    rr['rate'] = rr['returns'] / rr['lines'] * 100
    fig = go.Figure(go.Bar(x=['Store' if i == 'Retail' else i for i in rr.index], y=rr['rate'], marker_color=[u.CHANNEL_COLORS[i] for i in rr.index],
                           text=[f'{v:.1f}%' for v in rr['rate']], textposition='outside'))
    fig.update_yaxes(title='% of lines returned', range=[0, rr['rate'].max() * 1.3])
    u.show(u.style(fig, 'Online returns 2x the store (size is the #1 reason)'))
with r:
    w = s[s['Channel'] == 'Wholesale']
    acc = w.groupby('Customer_ID').agg(type=('Customer_Type', 'first'), orders=('Invoice_ID', 'nunique'), net=('Net_Sales_EGP', 'sum'),
                                       gp=('Gross_Profit_EGP', 'sum'), disc=('Discount_Pct', 'mean'), last=('Order_Date', 'max'))
    loss = acc[acc['gp'] < 0]
    k = st.columns(2)
    u.kpi(k[0], 'Wholesale-channel accounts losing money', f'{len(loss)}', inverse=True)
    u.kpi(k[1], 'Of them: real wholesale customers', f"{(loss['type'] == 'Wholesale').sum()}")
    st.caption(f"{(acc['type'] == 'Retail').sum():,} customers registered as *retail* bought wholesale quantities (12–60 pieces) at wholesale discounts "
               f"between Oct 2023 and Jul 2024 — {(loss['type'] == 'Retail').sum()} of the loss-making accounts are these. "
               'It stopped after Jul 2024. Today the problem is the discount level, not the accounts.')
    show_loss = loss.sort_values('gp').head(10).reset_index()
    show_loss[['net', 'gp']] = show_loss[['net', 'gp']].round(0)
    show_loss['last'] = show_loss['last'].dt.date
    u.table(show_loss.round(2).rename(columns={'Customer_ID': 'Account', 'type': 'Registered as', 'orders': 'Orders', 'net': 'Net sales',
                                               'gp': 'Gross profit', 'disc': 'Avg discount', 'last': 'Last order'}))
