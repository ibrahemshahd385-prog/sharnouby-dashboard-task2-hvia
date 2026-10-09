import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('📣 Marketing Attribution & Growth', '📣 قياس أثر التسويق والنمو'),
         t('How efficient is the marketing money really — and what do the platforms over-claim?',
           'ما الكفاءة الحقيقية للإنفاق التسويقي — وكم تبالغ المنصات في نسب المبيعات لنفسها؟'),
         '08_card05_marketing')

PLAT_AR = {'WhatsApp / CRM': 'واتساب / CRM', 'Google': 'جوجل', 'TikTok': 'تيك توك', 'Meta': 'ميتا', 'Influencer': 'المؤثرون'}
pn = lambda x: PLAT_AR.get(x, x) if u.is_ar() else x

files = u.load()
m = u.campaigns()
pt = u.platform_table(m)

c = st.columns(5)
u.kpi(c[0], t('Marketing spend (3 years)', 'الإنفاق التسويقي (3 سنوات)'), u.money(m['Spend_EGP'].sum() / 1e6))
u.kpi(c[1], t('Revenue claimed by platforms', 'الإيراد الذي تنسبه المنصات'), u.money(m['Attributed_Revenue_EGP'].sum() / 1e6))
u.kpi(c[2], t('Claimed vs what really sold', 'المُعلَن مقابل المُباع فعلًا'), f"{m['Attributed_Revenue_EGP'].sum() / m['actual_sales'].sum():.1f}x", inverse=True,
      help=t('Revenue the platforms claim ÷ the actual store + online sales of that product during the campaign.',
             'الإيراد الذي تنسبه المنصات ÷ مبيعات المنتج الفعلية في المتجر والأونلاين خلال الحملة.'))
u.kpi(c[3], t('Campaigns that over-claim', 'حملات تبالغ في النسب'), f"{(m['Attributed_Revenue_EGP'] > m['actual_sales']).mean():.0%}", inverse=True)
u.kpi(c[4], t('Real sales lift during campaigns', 'الزيادة الحقيقية في المبيعات أثناء الحملات'), f"{m['actual_sales'].sum() / m['baseline_sales'].sum() - 1:+.1%}",
      help=t('Product sales during the campaign vs the 4 weeks before. ~0% means the campaigns did not add sales we can see.',
             'مبيعات المنتج أثناء الحملة مقابل الأسابيع الأربعة السابقة. ~0% يعني أن الحملات لم تُضف مبيعات ملحوظة.'))

l, r = st.columns(2)
with l:
    p = pt.sort_values('ROAS')
    fig = go.Figure(go.Bar(y=[pn(x) for x in p['Platform']], x=p['ROAS'], orientation='h',
                           marker_color=[u.ORANGE if v < 2 else u.BLUE for v in p['ROAS']],
                           text=[f'{v:.1f}x' for v in p['ROAS']], textposition='outside'))
    fig.update_xaxes(title=t('Claimed ROAS (revenue ÷ spend)', 'العائد المُعلَن ROAS (الإيراد ÷ الإنفاق)'), range=[0, p['ROAS'].max() * 1.2])
    u.show(u.style(fig, t('WhatsApp/CRM returns 67x; Influencers barely 1x', 'واتساب/CRM يعود 67 ضعفًا؛ والمؤثرون بالكاد 1 ضعف')))
with r:
    g = m.groupby('Platform')[['Attributed_Revenue_EGP', 'actual_sales']].sum().sort_values('Attributed_Revenue_EGP') / 1e6
    plats = [pn(x) for x in g.index]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=plats, x=g['Attributed_Revenue_EGP'], name=t('Claimed by platform', 'ما تنسبه المنصة'), orientation='h', marker_color=u.LIGHT_BLUE))
    fig.add_trace(go.Bar(y=plats, x=g['actual_sales'], name=t('Actually sold', 'المُباع فعلًا'), orientation='h', marker_color=u.BLUE))
    fig.update_layout(barmode='group')
    fig.update_xaxes(title=t('EGP millions', 'مليون جنيه'))
    u.show(u.style(fig, t('Every platform claims far more than really sold', 'كل منصة تنسب لنفسها أكثر بكثير مما بيع فعلًا'), legend=True))

show_pt = pt[['Platform', 'campaigns', 'spend', 'revenue', 'ROAS', 'CPA', 'CTR_%', 'CVR_%']].copy()
show_pt[['spend', 'revenue']] = (show_pt[['spend', 'revenue']] / 1e6).round(2)
show_pt['Platform'] = show_pt['Platform'].map(pn)
u.table(show_pt.round(2).rename(columns={'Platform': t('Platform', 'المنصة'), 'campaigns': t('Campaigns', 'الحملات'), 'spend': t('Spend (M)', 'الإنفاق (مليون)'),
                                         'revenue': t('Claimed revenue (M)', 'الإيراد المُعلَن (مليون)'), 'CPA': t('Cost per order (EGP)', 'تكلفة الطلب (جنيه)'),
                                         'CTR_%': t('Click rate %', 'معدل النقر %'), 'CVR_%': t('Conversion %', 'معدل التحويل %')}))

st.subheader(t('🔀 Budget simulator', '🔀 محاكي الميزانية'))
st.caption(t('Move money away from Influencers. Claimed ROAS is inflated, so use this to rank options — then prove it with a holdout test.',
             'انقل الميزانية بعيدًا عن المؤثرين. العائد المُعلَن مبالغ فيه، فاستخدم هذا للمقارنة بين الخيارات — ثم أثبته بتجربة holdout.'))
a, b = st.columns(2)
cut = a.slider(t('Cut Influencer budget by (%)', 'خفض ميزانية المؤثرين بنسبة (%)'), 0, 100, 70, step=10) / 100
to_wa = b.slider(t('Share of the freed money that goes to WhatsApp/CRM (rest is saved)', 'نسبة المبلغ الموفَّر التي تذهب لواتساب/CRM (والباقي يُدَّخر)'),
                 0, 100, 50, step=10) / 100
infl_yr = m.loc[m['Platform'] == 'Influencer', 'Spend_EGP'].sum() / 3
freed = infl_yr * cut
roas = pt.set_index('Platform')['ROAS']
wa_roas = roas.get('WhatsApp / CRM', 0)
k = st.columns(3)
u.kpi(k[0], t('Money freed per year', 'المبلغ الموفَّر سنويًا'), f'{freed / 1e6:.2f}M EGP')
u.kpi(k[1], t('Saved (straight to profit)', 'مُدَّخر (يذهب للربح مباشرة)'), f'{freed * (1 - to_wa) / 1e6:.2f}M EGP')
u.kpi(k[2], t('Moved to WhatsApp/CRM', 'منقول إلى واتساب/CRM'), f'{freed * to_wa / 1e6:.2f}M EGP',
      help=t(f"At the claimed ROAS ({wa_roas:.0f}x) this would 'bring' {freed * to_wa * wa_roas / 1e6:.1f}M — but WhatsApp only reaches customers who opted in, so returns will fall as spend grows.",
             f"بالعائد المُعلَن ({wa_roas:.0f}x) سيجلب هذا {freed * to_wa * wa_roas / 1e6:.1f} مليون — لكن واتساب يصل فقط للموافقين على الرسائل، لذا سينخفض العائد كلما زاد الإنفاق."))
st.markdown(t('**How to prove it — holdout test:** keep 10% of opted-in customers out of every WhatsApp campaign for 8 weeks. '
              'The difference in sales between the two groups is the real effect. Same idea for one Meta region switched off.',
              '**كيف نثبت ذلك — تجربة holdout:** نستبعد 10% من العملاء الموافقين من كل حملات واتساب لمدة 8 أسابيع. '
              'الفرق في المبيعات بين المجموعتين هو الأثر الحقيقي. ونفس الفكرة بإيقاف إعلانات ميتا في منطقة واحدة.'))

st.subheader(t('Campaign list', 'قائمة الحملات'))
f1, f2 = st.columns(2)
all_p = sorted(m['Platform'].unique())
plat = f1.multiselect(t('Platform', 'المنصة'), all_p, default=all_p, format_func=pn)
loss_only = f2.toggle(t('Show only campaigns with claimed ROAS < 1', 'اعرض فقط الحملات بعائد مُعلَن أقل من 1'), value=False)
view = m[m['Platform'].isin(plat)]
if loss_only:
    view = view[view['roas_claimed'] < 1]
st.caption(t(f"{len(view)} campaigns · spend {view['Spend_EGP'].sum() / 1e6:.2f}M EGP", f"{len(view)} حملة · إنفاق {view['Spend_EGP'].sum() / 1e6:.2f} مليون جنيه"))
out = view[['Campaign_Name', 'Platform', 'Start_Date', 'Spend_EGP', 'Attributed_Revenue_EGP', 'actual_sales', 'roas_claimed', 'Discount_Pct']].copy()
out['Start_Date'] = out['Start_Date'].dt.date
out['Platform'] = out['Platform'].map(pn)
out[['Attributed_Revenue_EGP', 'actual_sales']] = out[['Attributed_Revenue_EGP', 'actual_sales']].round(0)
u.table(out.sort_values('roas_claimed').round(2).rename(columns={
    'Campaign_Name': t('Campaign', 'الحملة'), 'Platform': t('Platform', 'المنصة'), 'Start_Date': t('Start', 'البداية'), 'Spend_EGP': t('Spend', 'الإنفاق'),
    'Attributed_Revenue_EGP': t('Claimed revenue', 'الإيراد المُعلَن'), 'actual_sales': t('Actual sales', 'المبيعات الفعلية'),
    'roas_claimed': t('Claimed ROAS', 'العائد المُعلَن'), 'Discount_Pct': t('Discount', 'الخصم')}), height=320)

st.subheader(t('Website: conversion is slipping', 'الموقع: معدل التحويل يتراجع'))
w = files['Web_Traffic_Daily'].copy()
w['FY'] = u.fiscal_year(w['Date'])
l, r = st.columns(2)
with l:
    mm = w.set_index('Date').resample('MS')[['Orders', 'Sessions']].sum()
    mm['cr'] = mm['Orders'] / mm['Sessions'] * 100
    fig = go.Figure(go.Scatter(x=mm.index, y=mm['cr'], mode='lines', line=dict(color=u.BLUE, width=2.5)))
    fig.update_yaxes(title=t('Conversion rate %', 'معدل التحويل %'))
    g = w.groupby('FY')[['Orders', 'Sessions']].sum()
    by_fy = g['Orders'] / g['Sessions'] * 100
    u.show(u.style(fig, t(f'Conversion fell from {by_fy.iloc[0]:.2f}% to {by_fy.iloc[-1]:.2f}%', f'معدل التحويل انخفض من {by_fy.iloc[0]:.2f}% إلى {by_fy.iloc[-1]:.2f}%')))
with r:
    w['load'] = pd.cut(w['Avg_Page_Load_Sec'], [0, 2.5, 3.0, 3.5, 99], labels=['< 2.5s', '2.5–3s', '3–3.5s', '> 3.5s'])
    g = w.groupby('load', observed=True)[['Orders', 'Sessions']].sum()
    lb = g['Orders'] / g['Sessions'] * 100
    fig = go.Figure(go.Bar(x=lb.index.astype(str), y=lb.values, marker_color=[u.BLUE] * (len(lb) - 1) + [u.ORANGE],
                           text=[f'{v:.2f}%' for v in lb.values], textposition='outside'))
    fig.update_yaxes(title=t('Conversion rate %', 'معدل التحويل %'), range=[0, lb.max() * 1.25])
    fig.update_xaxes(title=t('Average page load time that day', 'متوسط زمن تحميل الصفحة في ذلك اليوم'))
    u.show(u.style(fig, t('Slow pages (> 3.5s) convert worst', 'الصفحات البطيئة (أكثر من 3.5 ثانية) تحوّل أقل')))
