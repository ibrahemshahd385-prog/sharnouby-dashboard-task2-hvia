import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('🚚 Procurement, Cost & Supplier Risk', '🚚 المشتريات والتكلفة ومخاطر الموردين'),
         t('Which suppliers put production at risk, and how fast are material costs rising?',
           'أي الموردين يعرّضون الإنتاج للخطر، وما سرعة ارتفاع تكلفة الخامات؟'),
         '12_card09_suppliers')

CAT_AR = {'Fabric': 'الأقمشة', 'Packaging': 'التغليف', 'Printing': 'الطباعة', 'Trims': 'الإكسسوارات', 'Printing Consumables': 'مستلزمات الطباعة'}
cn = lambda x: CAT_AR.get(x, x) if u.is_ar() else x

files = u.load()
po = files['Purchase_Orders'].copy()
po['FY'] = u.fiscal_year(po['Order_Date'])
po['Year'] = po['Order_Date'].dt.year
g = u.supplier_metrics()

c = st.columns(4)
u.kpi(c[0], t('Supplier on-time delivery', 'التسليم في الموعد من الموردين'), f"{po['On_Time'].mean():.1%}")
u.kpi(c[1], t('Average delay (all POs)', 'متوسط التأخير (كل أوامر الشراء)'), f"{po['Delay_Days'].mean():.1f} {t('days', 'يوم')}", inverse=True)
u.kpi(c[2], t('Purchase orders', 'أوامر الشراء'), f'{len(po):,}')
u.kpi(c[3], t('Suppliers per material', 'موردون لكل خامة'), f"{po.groupby('Material_ID')['Supplier_ID'].nunique().min()}",
      help=t('Every material can be bought from 12 suppliers → switching is easy.', 'كل خامة يمكن شراؤها من 12 موردًا ← التبديل سهل.'))

st.subheader(t('Supplier risk score', 'درجة خطر المورد'))
st.caption(t('Each factor is scaled 0–1 (worst supplier = 1), then weighted. Change the weights to match what matters most to the company.',
             'كل عامل يُحوَّل لمقياس 0–1 (أسوأ مورد = 1) ثم يُوزن. غيّر الأوزان حسب ما يهم الشركة أكثر.'))
a, b, c2, d = st.columns(4)
w_late = a.slider(t('Late deliveries', 'التسليمات المتأخرة'), 0, 100, 35, step=5)
w_delay = b.slider(t('Average delay days', 'متوسط أيام التأخير'), 0, 100, 25, step=5)
w_var = c2.slider(t('Unpredictable lead time (std)', 'عدم انتظام مدة التوريد (std)'), 0, 100, 15, step=5)
w_spend = d.slider(t('Share of our spend (exposure)', 'حصته من مشترياتنا (التعرّض)'), 0, 100, 25, step=5)
g['risk'] = u.risk_score(g, w_late, w_delay, w_var, w_spend)
g = g.sort_values('risk', ascending=True)
l, r = st.columns([3, 2])
with l:
    fig = go.Figure(go.Bar(y=g['Supplier_ID'] + ' · ' + g['Primary_Category'].map(cn), x=g['risk'], orientation='h',
                           marker_color=[u.RED if v >= 60 else (u.ORANGE if v >= 40 else u.LIGHT_BLUE) for v in g['risk']],
                           text=[f'{v:.0f}' for v in g['risk']], textposition='outside'))
    fig.update_xaxes(title=t('Risk score (0 = safest, 100 = riskiest)', 'درجة الخطر (0 = الأكثر أمانًا، 100 = الأخطر)'), range=[0, 110])
    s1, s2 = g.iloc[-1]['Supplier_ID'], g.iloc[-2]['Supplier_ID']
    u.show(u.style(fig, t(f"{s1} and {s2} stand far above every other supplier", f"{s1} و {s2} أعلى بكثير من بقية الموردين"), height=470))
with r:
    tb = g.sort_values('risk', ascending=False)[['Supplier_ID', 'Primary_Category', 'Contracted', 'late_rate', 'avg_delay', 'lt_std', 'reject_rate', 'spend_share', 'risk']].copy()
    tb['late_rate'] = (tb['late_rate'] * 100).round(0)
    tb['reject_rate'] = (tb['reject_rate'] * 100).round(2)
    tb['spend_share'] = (tb['spend_share'] * 100).round(1)
    tb['Primary_Category'] = tb['Primary_Category'].map(cn)
    tb['Contracted'] = tb['Contracted'].map(lambda x: t(x, 'نعم' if x == 'Yes' else 'لا'))
    u.table(tb.round(1).rename(columns={'Supplier_ID': t('Supplier', 'المورد'), 'Primary_Category': t('Category', 'الفئة'), 'Contracted': t('Contracted', 'متعاقد'),
                                        'late_rate': t('Late %', 'التأخير %'), 'avg_delay': t('Avg delay (days)', 'متوسط التأخير (يوم)'),
                                        'lt_std': t('Lead-time std (days)', 'تذبذب مدة التوريد (يوم)'), 'reject_rate': t('Reject %', 'المرفوض %'),
                                        'spend_share': t('Spend share %', 'حصة المشتريات %'), 'risk': t('Risk', 'الخطر')}), height=470)

l, r = st.columns(2)
with l:
    y = po.groupby(['Year', 'Supplier_ID'])['On_Time'].mean().unstack()
    late = (1 - y) * 100
    others = late.drop(columns=['SUP04', 'SUP09']).mean(axis=1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=late.index, y=late['SUP09'], name='SUP09', mode='lines+markers', line=dict(color=u.RED, width=3)))
    fig.add_trace(go.Scatter(x=late.index, y=late['SUP04'], name=t('SUP04 (contracted)', 'SUP04 (متعاقد)'), mode='lines+markers', line=dict(color=u.ORANGE, width=3)))
    fig.add_trace(go.Scatter(x=late.index, y=others, name=t('Other 10 suppliers (avg)', 'بقية الموردين الـ 10 (متوسط)'), mode='lines+markers',
                             line=dict(color=u.GREY, width=2, dash='dot')))
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(title=t('% of orders late', 'نسبة الطلبات المتأخرة'), range=[0, 100])
    u.show(u.style(fig, t('Since 2025, SUP09 and SUP04 are late most of the time', 'منذ 2025، المورّدان SUP09 و SUP04 يتأخران في معظم الطلبات'), legend=True))
with r:
    mat = files['Materials'].set_index('Material_ID')['Material_Category']
    po['Category'] = po['Material_ID'].map(mat)
    cost = po.groupby(['FY', 'Category'])['Unit_Cost_EGP'].mean().unstack()
    idx = cost / cost.iloc[0] * 100
    fig = go.Figure()
    palette = [u.ORANGE, u.BLUE, u.AQUA, u.GREY, u.LIGHT_BLUE]
    for col, colr in zip(idx.columns, palette):
        fig.add_trace(go.Scatter(x=idx.index, y=idx[col], name=f'{cn(col)} ({idx[col].iloc[-1] - 100:+.1f}%)', mode='lines+markers', line=dict(color=colr, width=2.5)))
    fig.update_yaxes(title=t('Unit cost index (FY2024 = 100)', 'مؤشر تكلفة الوحدة (FY2024 = 100)'))
    tr_, pr_, fa_ = idx['Trims'].iloc[-1] - 100, idx['Printing'].iloc[-1] - 100, idx['Fabric'].iloc[-1] - 100
    u.show(u.style(fig, t(f"Since FY2024: trims {tr_:+.0f}%, printing {pr_:+.0f}%, fabric {fa_:+.0f}%",
                          f"منذ FY2024: الإكسسوارات {tr_:+.0f}%، الطباعة {pr_:+.0f}%، الأقمشة {fa_:+.0f}%"), legend=True))

u.insight(t('Supplier delays show up in the factory one quarter later: correlation 0.07 in the same quarter vs 0.48 with the previous quarter. '
            'This is an indicator, not proof — the crises also coincide with the start of peak season. '
            'Action: SLA penalties for late delivery, move volume from SUP09 to on-time suppliers (every material has 12 options), '
            'and safety stock for thread, labels and poly bags, which go into all 59 products.',
            'تأخير الموردين يظهر في المصنع بعد ربع سنة: الارتباط 0.07 في نفس الربع مقابل 0.48 مع الربع السابق. '
            'هذا مؤشر وليس دليلًا — فالأزمات تتزامن أيضًا مع بداية موسم الذروة. '
            'الإجراء: غرامات تأخير (SLA)، ونقل الطلبات من SUP09 إلى موردين ملتزمين (لكل خامة 12 خيارًا)، '
            'ومخزون أمان للخيط والتيكيتات والأكياس لأنها تدخل في كل المنتجات الـ 59.'))
