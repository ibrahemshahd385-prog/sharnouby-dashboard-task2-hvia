import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('🗺️ Branch Intelligence & Expansion', '🗺️ ذكاء الفروع والتوسع'),
         t('Which channel creates value (not just sales), and where should the next store open?',
           'أي قناة تصنع قيمة (وليس مبيعات فقط)، وأين يجب أن يُفتح الفرع القادم؟'),
         '06_card03_channels')

GOV_AR = {'Greater Cairo': 'القاهرة الكبرى', 'Alexandria': 'الإسكندرية', 'Beheira': 'البحيرة', 'Dakahlia': 'الدقهلية', 'Gharbia': 'الغربية',
          'Sharqia': 'الشرقية', 'Monufia': 'المنوفية', 'Kafr El Sheikh': 'كفر الشيخ', 'Damietta': 'دمياط', 'Port Said': 'بورسعيد',
          'Suez': 'السويس', 'Other': 'أخرى'}
gn = lambda x: GOV_AR.get(x, x) if u.is_ar() else x

files = u.load()
s = files['Sales_Transactions']
ch = u.channel_fy()
p = ch.pivot(index='FY', columns='Channel', values='net_sales')
growth = p.pct_change().iloc[-1]
tot = ch.groupby('Channel')[['net_sales', 'gross_profit']].sum()
b2c_sales = tot.loc[['Online', 'Retail'], 'net_sales'].sum() / tot['net_sales'].sum()
b2c_gp = tot.loc[['Online', 'Retail'], 'gross_profit'].sum() / tot['gross_profit'].sum()

c = st.columns(5)
u.kpi(c[0], t('Online growth FY26', 'نمو الأونلاين FY26'), f"{growth['Online']:+.0%}")
u.kpi(c[1], t('Store growth FY26', 'نمو المتجر FY26'), f"{growth['Retail']:+.1%}")
u.kpi(c[2], t('Wholesale growth FY26', 'نمو الجملة FY26'), f"{growth['Wholesale']:+.1%}",
      help=t('Was +10.4% in FY25 — growth is slowing.', 'كان +10.4% في FY25 — النمو يتباطأ.'))
u.kpi(c[3], t('B2C share of sales', 'حصة التجزئة من المبيعات'), f'{b2c_sales:.1%}')
u.kpi(c[4], t('B2C share of profit', 'حصة التجزئة من الربح'), f'{b2c_gp:.1%}')

l, r = st.columns(2)
with l:
    fig = go.Figure()
    for name in ['Online', 'Retail']:
        fig.add_trace(go.Scatter(x=p.index, y=p[name] / 1e6, name=u.ch_name(name), mode='lines+markers+text',
                                 line=dict(color=u.CHANNEL_COLORS[name], width=3),
                                 text=[''] * (len(p) - 1) + [f'{p[name].iloc[-1] / 1e6:.1f}M'], textposition='middle right'))
    fig.update_xaxes(range=[-0.2, len(p) - 0.4])
    fig.update_yaxes(title=t('Net sales, EGP millions', 'صافي المبيعات، مليون جنيه'), range=[0, p[['Online', 'Retail']].max().max() / 1e6 * 1.25])
    u.show(u.style(fig, t('Online overtook the store in FY2025 and keeps growing', 'الأونلاين تجاوز المتجر في FY2025 ويواصل النمو'), legend=True))
with r:
    m = ch.pivot(index='FY', columns='Channel', values='margin') * 100
    fig = go.Figure()
    for name in ['Online', 'Retail', 'Wholesale']:
        fig.add_trace(go.Bar(x=m.index, y=m[name], name=u.ch_name(name), marker_color=u.CHANNEL_COLORS[name],
                             text=[f'{v:.0f}%' for v in m[name]], textposition='outside'))
    fig.update_layout(barmode='group')
    fig.update_yaxes(title=t('Gross margin %', 'هامش الربح %'), range=[0, m.max().max() * 1.25])
    mr, mo, mw = m['Retail'].iloc[-1], m['Online'].iloc[-1], m['Wholesale'].iloc[-1]
    u.show(u.style(fig, t(f"Store {mr:.0f}% and online {mo:.0f}% margin vs wholesale {mw:.0f}%",
                          f"هامش المتجر {mr:.0f}% والأونلاين {mo:.0f}% مقابل الجملة {mw:.0f}%"), legend=True))

st.subheader(t('📍 Where to open the next store', '📍 أين نفتح الفرع القادم'))
on = s[s['Channel'] == 'Online'].copy()
on['Region'] = on['Customer_Governorate'].replace({'Cairo': 'Greater Cairo', 'Giza': 'Greater Cairo'})
g = on.groupby('Region').agg(sales=('Net_Sales_EGP', 'sum'), customers=('Customer_ID', 'nunique'))
g26 = on[on['FY'] == 'FY2026'].groupby('Region')['Net_Sales_EGP'].sum()
g25 = on[on['FY'] == 'FY2025'].groupby('Region')['Net_Sales_EGP'].sum()
g['growth_FY26_%'] = (g26 / g25 - 1) * 100
g['has_store'] = np.where(g.index == 'Alexandria', t('Yes (Sidi Bishr)', 'نعم (سيدي بشر)'), t('No', 'لا'))
g = g.sort_values('sales', ascending=True)
l, r = st.columns([3, 2])
with l:
    fig = go.Figure(go.Bar(y=[gn(x) for x in g.index], x=g['sales'] / 1e6, orientation='h',
                           marker_color=[u.ORANGE if i == 'Greater Cairo' else (u.BLUE if i == 'Alexandria' else u.LIGHT_BLUE) for i in g.index],
                           text=[f'{v / 1e6:.1f}M' for v in g['sales']], textposition='outside'))
    fig.update_xaxes(title=t('Online sales, 3 years (EGP millions)', 'مبيعات الأونلاين، 3 سنوات (مليون جنيه)'), range=[0, g['sales'].max() / 1e6 * 1.2])
    u.show(u.style(fig, t('Greater Cairo buys online as much as Alexandria — with no store', 'القاهرة الكبرى تشتري أونلاين بقدر الإسكندرية — بدون أي فرع'), height=460))
with r:
    top = g.sort_values('sales', ascending=False).head(6).copy()
    top['sales'] = (top['sales'] / 1e6).round(2)
    top.index = [gn(x) for x in top.index]
    top.index.name = 'Region'
    u.table(top.round(1).reset_index().rename(columns={'Region': t('Region', 'المنطقة'), 'sales': t('Online sales (M)', 'مبيعات الأونلاين (مليون)'),
                                                        'customers': t('Online customers', 'عملاء الأونلاين'), 'growth_FY26_%': t('Growth FY26 %', 'النمو FY26 %'),
                                                        'has_store': t('Store?', 'يوجد فرع؟')}))
    u.insight(t('Greater Cairo (Cairo + Giza) = the same online sales as Alexandria, without a single store. '
                'Next step: a pop-up store or shop-in-shop in Cairo for 3 months, then measure sales vs a similar city.',
                'القاهرة الكبرى (القاهرة + الجيزة) = نفس مبيعات الأونلاين في الإسكندرية، بدون فرع واحد. '
                'الخطوة التالية: متجر مؤقت أو ركن داخل متجر في القاهرة لمدة 3 أشهر، ثم مقارنة المبيعات بمدينة مشابهة.'))

st.subheader(t('Returns and wholesale accounts', 'المرتجعات وحسابات الجملة'))
l, r = st.columns(2)
with l:
    rr = ch.groupby('Channel')[['returns', 'lines']].sum()
    rr['rate'] = rr['returns'] / rr['lines'] * 100
    fig = go.Figure(go.Bar(x=[u.ch_name(i) for i in rr.index], y=rr['rate'], marker_color=[u.CHANNEL_COLORS[i] for i in rr.index],
                           text=[f'{v:.1f}%' for v in rr['rate']], textposition='outside'))
    fig.update_yaxes(title=t('% of lines returned', 'نسبة البنود المرتجعة'), range=[0, rr['rate'].max() * 1.3])
    u.show(u.style(fig, t('Online returns 2x the store (size is the #1 reason)', 'مرتجعات الأونلاين ضعف المتجر (والمقاس هو السبب الأول)')))
with r:
    w = s[s['Channel'] == 'Wholesale']
    acc = w.groupby('Customer_ID').agg(type=('Customer_Type', 'first'), orders=('Invoice_ID', 'nunique'), net=('Net_Sales_EGP', 'sum'),
                                       gp=('Gross_Profit_EGP', 'sum'), disc=('Discount_Pct', 'mean'), last=('Order_Date', 'max'))
    loss = acc[acc['gp'] < 0]
    k = st.columns(2)
    u.kpi(k[0], t('Wholesale-channel accounts losing money', 'حسابات قناة الجملة الخاسرة'), f'{len(loss)}', inverse=True)
    u.kpi(k[1], t('Of them: real wholesale customers', 'منها: تجار جملة حقيقيون'), f"{(loss['type'] == 'Wholesale').sum()}")
    n_ret, n_loss_ret = (acc['type'] == 'Retail').sum(), (loss['type'] == 'Retail').sum()
    st.caption(t(f"{n_ret:,} customers registered as *retail* bought wholesale quantities (12–60 pieces) at wholesale discounts "
                 f"between Oct 2023 and Jul 2024 — {n_loss_ret} of the loss-making accounts are these. "
                 'It stopped after Jul 2024. Today the problem is the discount level, not the accounts.',
                 f"{n_ret:,} عميلًا مسجّلين *كتجزئة* اشتروا كميات جملة (12–60 قطعة) بخصومات الجملة "
                 f"بين أكتوبر 2023 ويوليو 2024 — ومنهم {n_loss_ret} من الحسابات الخاسرة. "
                 'توقّف ذلك بعد يوليو 2024. المشكلة اليوم في مستوى الخصم وليست في الحسابات.'))
    show_loss = loss.sort_values('gp').head(10).reset_index()
    show_loss[['net', 'gp']] = show_loss[['net', 'gp']].round(0)
    show_loss['last'] = show_loss['last'].dt.date
    show_loss['type'] = show_loss['type'].map(lambda x: t(x, 'تجزئة' if x == 'Retail' else 'جملة'))
    u.table(show_loss.round(2).rename(columns={'Customer_ID': t('Account', 'الحساب'), 'type': t('Registered as', 'مسجّل كـ'), 'orders': t('Orders', 'الطلبات'),
                                               'net': t('Net sales', 'صافي المبيعات'), 'gp': t('Gross profit', 'إجمالي الربح'),
                                               'disc': t('Avg discount', 'متوسط الخصم'), 'last': t('Last order', 'آخر طلب')}))
