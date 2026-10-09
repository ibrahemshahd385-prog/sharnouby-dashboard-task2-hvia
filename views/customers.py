import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

u.header('👥 Customer 360 & Retention',
         'Who comes back, how much is each customer worth, and who are we losing?',
         '05_card02_customers · 14_ai_churn_test')

files = u.load()
s, cust = files['Sales_Transactions'], files['Customers'].set_index('Customer_ID')
retail = s[s['Customer_Type'] == 'Retail']
r = u.rfm()
top20 = r['monetary'].sort_values(ascending=False)
top20_share = top20.head(int(len(top20) * 0.2)).sum() / top20.sum()

c = st.columns(5)
u.kpi(c[0], 'Retail buyers', f'{len(r):,}', help=f"{(cust['Customer_Type'] == 'Retail').sum() - len(r):,} registered customers never bought.")
u.kpi(c[1], 'Bought more than once', f"{(r['frequency'] > 1).mean():.1%}")
u.kpi(c[2], 'Orders per customer', f"{r['frequency'].mean():.1f}")
u.kpi(c[3], 'Average order value', f"{r['monetary'].sum() / r['frequency'].sum():,.0f} EGP")
u.kpi(c[4], 'Top 20% customers = revenue', f'{top20_share:.0%}')

tab1, tab2, tab3 = st.tabs(['Segments (RFM)', 'Cohorts & channels', 'Customer lookup'])

with tab1:
    seg = r.groupby('segment').agg(customers=('monetary', 'size'), revenue=('monetary', 'sum'),
                                   recency=('recency', 'median'), orders=('frequency', 'mean')).reindex(u.SEGMENT_ORDER)
    seg['cust_%'] = seg['customers'] / seg['customers'].sum() * 100
    seg['rev_%'] = seg['revenue'] / seg['revenue'].sum() * 100
    fig = go.Figure()
    fig.add_trace(go.Bar(y=seg.index, x=seg['cust_%'], name='% of customers', orientation='h', marker_color=u.LIGHT_BLUE,
                         text=[f'{v:.0f}%' for v in seg['cust_%']], textposition='outside'))
    fig.add_trace(go.Bar(y=seg.index, x=seg['rev_%'], name='% of revenue', orientation='h', marker_color=u.BLUE,
                         text=[f'{v:.0f}%' for v in seg['rev_%']], textposition='outside'))
    fig.update_layout(barmode='group')
    fig.update_yaxes(autorange='reversed')
    fig.update_xaxes(title='%', range=[0, seg[['cust_%', 'rev_%']].max().max() * 1.2])
    u.show(u.style(fig, "\"At Risk (Can't Lose)\": 15% of customers, 31% of revenue — and they stopped buying", legend=True, height=430))
    st.warning("**Honest test (notebook 14):** we trained an AI churn model to predict who stops buying. AUC = **0.51** "
               "(0.5 = coin flip), and customers come back ~66% of the time whatever their recency. "
               "So these segments **describe** the past, they do **not predict** the future. "
               "→ The win-back campaign must start as a test: half the list gets the offer, half does not (control group).", icon='⚠️')
    seg_show = seg[['customers', 'cust_%', 'rev_%', 'recency', 'orders']].round(1).reset_index()
    u.table(seg_show.rename(columns={'segment': 'Segment', 'customers': 'Customers', 'cust_%': '% customers', 'rev_%': '% revenue',
                                     'recency': 'Days since last order (median)', 'orders': 'Avg orders'}))
    st.markdown('**Win-back test list** (At Risk, opted-in to messages)')
    wl = r[r['segment'].str.startswith('At Risk')].join(cust[['Consent_Status', 'Governorate']])
    wl = wl[wl['Consent_Status'] == 'Opted-in'].sort_values('monetary', ascending=False)
    rng = np.random.default_rng(42)
    wl['group'] = np.where(rng.random(len(wl)) < 0.5, 'TEST (send offer)', 'CONTROL (no offer)')
    st.caption(f"{len(wl):,} customers · randomly split 50/50 so we can measure the real effect of the campaign.")
    out = wl[['segment', 'recency', 'frequency', 'monetary', 'Governorate', 'group']].reset_index()
    out['monetary'] = out['monetary'].round(0)
    u.table(out.head(200), height=300)
    st.download_button('⬇️ Download the full test list (CSV)', out.to_csv(index=False).encode('utf-8-sig'), 'winback_test_list.csv', 'text/csv')

with tab2:
    ret = u.cohort_table()
    cols = [k for k in ret.columns if k <= 8]
    z = ret[cols].values
    fig = go.Figure(go.Heatmap(z=z, x=[f'Q+{k}' for k in cols], y=ret.index, colorscale=[[0, '#f4f8fd'], [1, u.BLUE]],
                               text=np.where(np.isnan(z), '', np.vectorize(lambda v: f'{v:.0f}%')(np.nan_to_num(z))),
                               texttemplate='%{text}', showscale=False, hovertemplate='Cohort %{y}, %{x}: %{z:.0f}%<extra></extra>'))
    fig.update_yaxes(autorange='reversed', title='Join quarter')
    fig.update_xaxes(title='Quarters after joining', side='top')
    u.show(u.style(fig, 'Newer customers come back much less than the first ones', height=460))
    st.caption('Each cell = % of customers who joined in that quarter and bought again k quarters later.')

    l, rr = st.columns(2)
    with l:
        b2c = retail[retail['Channel'].isin(['Online', 'Retail'])]
        used = b2c.groupby('Customer_ID')['Channel'].agg(lambda x: 'Both' if x.nunique() > 1 else ('Store only' if x.iloc[0] == 'Retail' else 'Online only'))
        spend = r['monetary']
        omni = pd.DataFrame({'group': used}).join(spend.rename('spend')).groupby('group').agg(customers=('spend', 'size'), spend=('spend', 'mean'))
        omni = omni.reindex(['Store only', 'Online only', 'Both'])
        fig = go.Figure(go.Bar(x=omni.index, y=omni['spend'], marker_color=[u.BLUE, u.ORANGE, u.AQUA],
                               text=[f'{v:,.0f} EGP<br>{n:,} customers' for v, n in zip(omni['spend'], omni['customers'])], textposition='outside'))
        fig.update_yaxes(title='Average spend per customer (3 years)', range=[0, omni['spend'].max() * 1.3])
        ratio = omni.loc['Both', 'spend'] / omni.loc[['Store only', 'Online only'], 'spend'].max()
        u.show(u.style(fig, f'Customers who use store AND online spend ~{ratio:.0f}x more'))
    with rr:
        acq = r.join(cust['Acquisition_Channel']).groupby('Acquisition_Channel').agg(spend=('monetary', 'mean'), repeat=('frequency', lambda x: (x > 1).mean() * 100))
        acq = acq.sort_values('spend')
        fig = go.Figure(go.Bar(y=acq.index, x=acq['spend'], orientation='h', marker_color=u.GREY, text=[f'{v:,.0f}' for v in acq['spend']], textposition='outside'))
        fig.update_xaxes(title='Average spend per customer (EGP)', range=[0, acq['spend'].max() * 1.2])
        u.show(u.style(fig, 'How a customer was acquired makes no difference'))

with tab3:
    st.caption('Type a customer ID (for example one from the win-back list) to see the full profile.')
    default_id = r.sort_values('monetary', ascending=False).index[0]
    cid = st.text_input('Customer ID', value=default_id).strip().upper()
    if cid not in r.index:
        st.error('Customer not found among retail buyers.')
    else:
        p, info = r.loc[cid], cust.loc[cid]
        orders = retail[retail['Customer_ID'] == cid]
        k = st.columns(5)
        u.kpi(k[0], 'Segment', p['segment'].replace("At Risk (Can't Lose)", "Can't Lose"), help=p['segment'])
        u.kpi(k[1], 'Total spend', f"{p['monetary']:,.0f} EGP")
        u.kpi(k[2], 'Orders', f"{p['frequency']}")
        u.kpi(k[3], 'Days since last order', f"{p['recency']}")
        u.kpi(k[4], 'WhatsApp consent', info['Consent_Status'])
        st.markdown(f"**{info['Gender']}, {info['Age_Band']}, {info['Governorate']}** · joined {info['Join_Date']:%b %Y} via {info['Acquisition_Channel']} · "
                    f"channels used: {', '.join(sorted(orders['Channel'].replace({'Retail': 'Store'}).unique()))} · "
                    f"favourite family: {orders.groupby('Product_Family')['Quantity'].sum().idxmax()} · "
                    f"returns: {orders['is_return'].mean():.0%} of lines")
        hist = orders.groupby(['Invoice_ID', 'Order_Date', 'Channel']).agg(items=('Quantity', 'sum'), net=('Net_Sales_EGP', 'sum'),
                                                                           discount=('Discount_Pct', 'mean')).reset_index().sort_values('Order_Date', ascending=False)
        hist['Order_Date'] = hist['Order_Date'].dt.date
        hist['Channel'] = hist['Channel'].replace({'Retail': 'Store'})
        hist['discount'] = (hist['discount'] * 100).round(0).astype(int).astype(str) + '%'
        hist['net'] = hist['net'].round(0)
        u.table(hist.head(15).rename(columns={'Invoice_ID': 'Invoice', 'Order_Date': 'Date', 'items': 'Items', 'net': 'Net (EGP)', 'discount': 'Avg discount'}))