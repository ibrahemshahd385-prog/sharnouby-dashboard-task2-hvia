import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

u.header('📏 Size & Fit Intelligence',
         'Size is #1 in returns, #1 in support questions and #1 in factory defects. Nobody asked — so we built it.',
         '15_app8_size_fit')

files = u.load()
s, cs, q = files['Sales_Transactions'], files['Customer_Service'].copy(), files['Quality']
b2c = s[s['Channel'] != 'Wholesale']
ret = s[s['is_return']]
size_t = cs[cs['Issue_Type'] == 'Size guidance']
rate = b2c.groupby('Channel')['is_size_return'].mean() * 100

c = st.columns(5)
u.kpi(c[0], 'Share of all refunds', f"{s.loc[s['is_size_return'], 'Refund_Value_EGP'].sum() / ret['Refund_Value_EGP'].sum():.0%}",
      help='Size / fit is the #1 return reason.')
u.kpi(c[1], 'Online size-return rate', f"{rate['Online']:.1f}%", f"{rate['Online'] / rate['Retail']:.1f}x the store", inverse=True)
u.kpi(c[2], 'Tickets about size', f"{len(size_t) / len(cs):.0%}", help='The #1 ticket type, the same share on every channel.')
u.kpi(c[3], 'Wait for a size answer', f"{size_t['Resolution_Hours'].mean():.0f} hours", inverse=True)
u.kpi(c[4], '#1 QC defect type', 'Size', help='10,850 rejected units, 1.97M EGP — but only slightly above stitching.')

tab1, tab2, tab3 = st.tabs(['🧠 Fit Assistant (prototype)', 'The evidence', 'Business case'])

with tab1:
    st.markdown('**What the customer sees on the product page or in WhatsApp:** 3 questions → the right size, with the reason.')
    l, r = st.columns([2, 3])
    with l:
        audience = st.radio('Who is it for?', ['Kids', 'Women'], horizontal=True)
        if audience == 'Kids':
            age = st.slider('Child age (years)', 2, 13, 7)
            height = st.slider('Height (cm)', 90, 165, 125)
            weight = st.slider('Weight (kg)', 12, 55, 24)
        else:
            age = None
            height = st.slider('Height (cm)', 145, 185, 163)
            weight = st.slider('Weight (kg)', 45, 110, 68)
        fit = st.radio('Preferred fit', ['Snug', 'Regular', 'Loose'], index=1, horizontal=True)
    with r:
        size, reason = u.recommend_size(audience, height=height, weight=weight, age=age, fit=fit)
        st.markdown(f"<div style='border:2px solid {u.BLUE};border-radius:12px;padding:24px;text-align:center'>"
                    f"<div style='font-size:15px;color:{u.INK}'>Recommended size</div>"
                    f"<div style='font-size:64px;font-weight:700;color:{u.BLUE};line-height:1.1'>{size}</div>"
                    f"<div style='font-size:14px;color:{u.INK};margin-top:8px'>{reason}</div></div>", unsafe_allow_html=True)
        if audience == 'Kids' and age is not None:
            age_size = u.KIDS_CHART.iloc[int(np.clip(np.searchsorted([4.5, 6.5, 8.5, 10.5], age), 0, 4))]['size']
            if age_size != size:
                st.caption(f'Note: by age alone the size would be {age_size}. We trust height and weight first, because children grow at different speeds.')
        st.markdown('**What we save with every recommendation** (this is the data the company does not have today):')
        log = pd.DataFrame([{'order_id': 'INV-xxxxx', 'product': 'any product', 'audience': audience, 'height': height, 'weight': weight,
                             'fit': fit, 'recommended': size, 'returned?': 'filled later', 'too small / too big': 'filled later'}])
        u.table(log)
    with st.expander('Size chart used by the prototype (illustrative — replace with the official Leo Moda chart)'):
        a, b = st.columns(2)
        a.markdown('**Kids**')
        u.table(u.KIDS_CHART.rename(columns={'size': 'Size', 'age': 'Age', 'height_min': 'Height from (cm)', 'height_max': 'Height to (cm)', 'weight_max': 'Max weight (kg)'}))
        b.markdown('**Women**')
        u.table(u.WOMEN_CHART.rename(columns={'size': 'Size', 'weight_min': 'Weight from (kg)', 'weight_max': 'Weight to (kg)', 'bust_cm': 'Bust (cm)'}))
    st.caption('How it gets smarter: every recommendation is linked to the order. When an item comes back as "too small" or "too big", '
               'that product\'s size rule is adjusted. After a few months the assistant knows which products run small.')

with tab2:
    l, r = st.columns(2)
    with l:
        reasons = ret.groupby('Return_Reason')['Refund_Value_EGP'].sum().sort_values() / 1e6
        fig = go.Figure(go.Bar(y=reasons.index, x=reasons.values, orientation='h',
                               marker_color=[u.ORANGE if i == 'Size / fit' else u.LIGHT_BLUE for i in reasons.index],
                               text=[f'{v:.2f}M' for v in reasons.values], textposition='outside'))
        fig.update_xaxes(title='Refunds over 3 years, EGP millions', range=[0, reasons.max() * 1.2])
        u.show(u.style(fig, 'Size / fit is the #1 return reason: 37% of all refunds'))
    with r:
        t = b2c.pivot_table(index='FY', columns='Channel', values='is_size_return', aggfunc='mean') * 100
        share = b2c.groupby('FY')['Channel'].apply(lambda x: (x == 'Online').mean() * 100)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t.index, y=t['Online'], name='Online', mode='lines+markers', line=dict(color=u.ORANGE, width=3)))
        fig.add_trace(go.Scatter(x=t.index, y=t['Retail'], name='Store', mode='lines+markers', line=dict(color=u.BLUE, width=3)))
        fig.update_yaxes(title='Lines returned for size / fit, %', range=[0, 3.5])
        u.show(u.style(fig, f'Online returns 2x more for size — and online is now {share.iloc[-1]:.0f}% of B2C', legend=True))

    ch = s.groupby('Channel').agg(lines=('Invoice_ID', 'size'), size_lines=('is_size_return', 'sum'))
    ch['units'] = s[s['is_size_return']].groupby('Channel')['Quantity'].sum()
    ch['refund_M'] = s[s['is_size_return']].groupby('Channel')['Refund_Value_EGP'].sum() / 1e6
    ch['rate_%'] = ch['size_lines'] / ch['lines'] * 100
    st.markdown('**Two different problems:** online & store have a high *rate* (customers cannot try on); wholesale has a low rate but the biggest *money*, because one order is hundreds of pieces.')
    u.table(ch[['rate_%', 'units', 'refund_M']].round(2).reset_index().replace({'Retail': 'Store'})
            .rename(columns={'rate_%': 'Size-return rate %', 'units': 'Units returned for size', 'refund_M': 'Refunds (M EGP)'}))

    l, r = st.columns(2)
    with l:
        bp = b2c.groupby('Product_ID').agg(lines=('is_size_return', 'size'), rate=('is_size_return', 'mean'))
        avg = b2c['is_size_return'].mean()
        noise = np.sqrt(avg * (1 - avg) / bp['lines'].mean())
        fig = go.Figure(go.Histogram(x=bp['rate'] * 100, nbinsx=15, marker_color=u.LIGHT_BLUE))
        fig.add_vline(x=avg * 100, line_color=u.BLUE, line_width=2)
        fig.update_xaxes(title='Size-return rate per product, %')
        fig.update_yaxes(title='Number of products')
        u.show(u.style(fig, 'No "bad product": all 59 sit close to the average'))
        st.caption(f"Spread between products {bp['rate'].std():.2%} vs {noise:.2%} expected from pure chance → "
                   'it is an information problem at purchase, not a pattern problem.')
    with r:
        tk = cs['Issue_Type'].value_counts().sort_values()
        fig = go.Figure(go.Bar(y=tk.index, x=tk.values, orientation='h', marker_color=[u.ORANGE if i == 'Size guidance' else u.LIGHT_BLUE for i in tk.index],
                               text=[f'{v:,}' for v in tk.values], textposition='outside'))
        fig.update_xaxes(title='Support tickets (3 years)', range=[0, tk.max() * 1.2])
        u.show(u.style(fig, '"Which size?" is the #1 customer question'))

    pm = files['Product_Master'][['Product_ID', 'Audience']]
    sc = s.merge(pm, on='Product_ID', how='left')
    curve = pd.crosstab(sc['Audience'], sc['Size'], values=sc['Quantity'], aggfunc='sum', normalize='index') * 100
    curve = curve[[k for k in ['4', '6', '8', '10', '12', 'M', 'L', 'XL', '2XL'] if k in curve.columns]].round(1)
    st.markdown('**Size curve** (share of units sold per size) — use it to split production and to build size packs for wholesale traders:')
    u.table(curve.reset_index())

with tab3:
    fy26 = s[s['FY'] == 'FY2026']
    b26, w26 = fy26[fy26['Channel'] != 'Wholesale'], fy26[fy26['Channel'] == 'Wholesale']
    a, b = st.columns(2)
    cut_b2c = a.slider('Fit assistant cuts online + store size returns by (%)', 0, 60, 30, step=5) / 100
    cut_wh = b.slider('Size packs cut wholesale size returns by (%)', 0, 60, 20, step=5) / 100
    rows = pd.DataFrame([
        ['Fit assistant (web + WhatsApp)', b26.loc[b26['is_size_return'], 'Refund_Value_EGP'].sum() / 1e6, cut_b2c,
         b26['Gross_Profit_EGP'].sum() / b26['Net_Sales_EGP'].sum()],
        ['Size-curve packs for wholesale', w26.loc[w26['is_size_return'], 'Refund_Value_EGP'].sum() / 1e6, cut_wh,
         w26['Gross_Profit_EGP'].sum() / w26['Net_Sales_EGP'].sum()],
    ], columns=['Action', 'Size refunds FY26 (M)', 'Assumed cut', 'Margin'])
    rows['Refunds avoided (M)'] = rows['Size refunds FY26 (M)'] * rows['Assumed cut']
    rows['Profit impact (M)'] = rows['Refunds avoided (M)'] * rows['Margin']
    k = st.columns(3)
    u.kpi(k[0], 'Refunds avoided / year', f"{rows['Refunds avoided (M)'].sum():.2f}M EGP")
    u.kpi(k[1], 'Gross-profit impact / year', f"{rows['Profit impact (M)'].sum():.2f}M EGP")
    u.kpi(k[2], 'Size questions answered instantly', f"~{len(size_t) // 3:,} / year")
    u.table(rows.round(3))
    st.warning('**Honest framing:** the direct money is modest. The real value is (1) protecting online, the channel growing 26% a year '
               'with 2x the size returns, (2) answering customers in seconds instead of 18 hours, and (3) building size data the company does not have.', icon='🧭')
    st.markdown('**How we prove it — A/B test for 3 months:** half of website visitors see the Fit Assistant, half do not. '
                'Compare size-return rates. Targets: online size returns 2.8% → 2.0%, size tickets −50%, answer time 18 h → seconds.')
