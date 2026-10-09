import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('🏭 Factory Digital Twin & Production Control', '🏭 التوأم الرقمي للمصنع والتحكم في الإنتاج'),
         t('Where does production get stuck, what does poor quality cost, and what happens if we fix it?',
           'أين يتعطّل الإنتاج، وكم تكلّف الجودة الرديئة، وماذا يحدث لو أصلحناها؟'),
         '09_card06_factory · 10_card07_quality · 11_card08_printing')

AR_NAMES = {
    # production stages / business areas
    'Sewing': 'الخياطة', 'Finishing': 'التشطيب', 'Packing': 'التعبئة', 'Cutting': 'القص', 'Printing': 'الطباعة',
    # QC defects
    'Size Variance': 'اختلاف المقاس', 'Stitch Defect': 'عيب خياطة', 'Packing Error': 'خطأ تعبئة', 'Fabric Defect': 'عيب قماش',
    'Finishing Defect': 'عيب تشطيب', 'Color Misalignment': 'عدم تطابق اللون', 'Ink Smudge': 'تلطّخ الحبر', 'Print Cracking': 'تشقّق الطباعة',
    # downtime reasons
    'Mechanical fault': 'عطل ميكانيكي', 'Planned maintenance': 'صيانة مخططة', 'Setup / changeover': 'تجهيز / تغيير',
    'Material wait': 'انتظار الخامات', 'Electrical fault': 'عطل كهربائي', 'Operator shortage': 'نقص العمالة',
    # COPQ parts
    'QC rejects & scrap': 'هالك فحص الجودة', 'Quality-related refunds': 'مرتجعات بسبب الجودة', 'Print rework': 'إعادة تشغيل الطباعة',
    'Reprint ink': 'حبر إعادة الطباعة',
}
nm = lambda x: AR_NAMES.get(x, x) if u.is_ar() else x

files = u.load()
po = u.production()
late = po[po['late']]

c = st.columns(5)
u.kpi(c[0], t('Plan attainment', 'تحقيق الخطة'), f"{po['Produced_Qty'].sum() / po['Planned_Qty'].sum():.1%}",
      help=t('Produced ÷ planned quantity.', 'الكمية المنتجة ÷ الكمية المخططة.'))
u.kpi(c[1], t('Orders on time', 'الطلبات في موعدها'), f"{1 - po['late'].mean():.1%}")
u.kpi(c[2], t('Average delay (late orders)', 'متوسط التأخير (الطلبات المتأخرة)'), f"{late['Delay_Days'].mean():.1f} {t('days', 'يوم')}", inverse=True)
u.kpi(c[3], t('Production reject rate', 'نسبة المرفوض في الإنتاج'), f"{po['Rejected_Qty'].sum() / po['Produced_Qty'].sum():.2%}", inverse=True)
u.kpi(c[4], t('Overtime hours', 'ساعات العمل الإضافي'), f"{po['Overtime_Hours'].sum():,.0f}", inverse=True)

tab1, tab2, tab3, tab4 = st.tabs([t('Production', 'الإنتاج'), t('Digital twin: what-if', 'التوأم الرقمي: ماذا لو'),
                                  t('Quality & COPQ', 'الجودة وتكلفتها'), t('Printing & machines', 'الطباعة والماكينات')])

with tab1:
    l, r = st.columns(2)
    with l:
        q = po.groupby('quarter')['late'].mean() * 100
        colors = [u.ORANGE if v > 25 else u.BLUE for v in q.values]
        fig = go.Figure(go.Bar(x=q.index, y=q.values, marker_color=colors, text=[f'{v:.0f}%' for v in q.values], textposition='outside'))
        fig.update_yaxes(title=t('% of orders late', 'نسبة الطلبات المتأخرة'), range=[0, q.max() * 1.2])
        u.show(u.style(fig, t('Two crises: 46% late in Q2-2025, 34% in Q1-2026', 'أزمتان: 46% متأخرة في Q2-2025 و34% في Q1-2026')))
    with r:
        st_ = late.groupby('Primary_Bottleneck')['Delay_Days'].sum().sort_values(ascending=False)
        share = st_ / st_.sum() * 100
        fig = go.Figure(go.Bar(x=[nm(x) for x in st_.index], y=share.values, marker_color=[u.ORANGE, u.ORANGE] + [u.LIGHT_BLUE] * (len(st_) - 2),
                               text=[f'{v:.0f}%' for v in share.values], textposition='outside'))
        fig.update_yaxes(title=t('% of all delay days', 'نسبة أيام التأخير'), range=[0, share.max() * 1.2])
        u.show(u.style(fig, t(f'Sewing + finishing = {share.iloc[:2].sum():.0f}% of all delay days',
                              f'الخياطة + التشطيب = {share.iloc[:2].sum():.0f}% من كل أيام التأخير')))
    ot = po.groupby('late')['Overtime_Hours'].mean()
    st.caption(t(f"Late orders burn {ot.loc[True]:.1f} overtime hours on average vs {ot.loc[False]:.1f} for on-time orders — "
                 "overtime is a symptom of the bottleneck, not a cure.",
                 f"الطلبات المتأخرة تستهلك {ot.loc[True]:.1f} ساعة إضافية في المتوسط مقابل {ot.loc[False]:.1f} للطلبات في موعدها — "
                 "العمل الإضافي عَرَض لعنق الزجاجة وليس علاجًا له."))
    lines = po.groupby('Line_ID').agg(orders=('Production_Order_ID', 'size'), on_time=('late', lambda x: (1 - x.mean()) * 100),
                                      efficiency=('Efficiency_Pct', 'mean'), overtime=('Overtime_Hours', 'sum')).round(1).reset_index()
    u.table(lines.rename(columns={'Line_ID': t('Line', 'الخط'), 'orders': t('Orders', 'الطلبات'), 'on_time': t('On time %', 'في الموعد %'),
                                  'efficiency': t('Avg efficiency %', 'متوسط الكفاءة %'), 'overtime': t('Overtime h', 'ساعات إضافية')}))

with tab2:
    st.markdown(t('**What if we fix part of the late orders caused by each stage?** Move the sliders and watch on-time delivery change.',
                  '**ماذا لو أصلحنا جزءًا من الطلبات المتأخرة بسبب كل مرحلة؟** حرّك المؤشرات وشاهد نسبة التسليم في الموعد تتغيّر.'))
    stages = late['Primary_Bottleneck'].value_counts()
    cols = st.columns(len(stages))
    fixed = 0
    for col, (stage, n) in zip(cols, stages.items()):
        default = 50 if stage in ('Sewing', 'Finishing') else 0
        pct = col.slider(t(f'{stage} ({n} late orders)', f'{nm(stage)} ({n} طلب متأخر)'), 0, 100, default, step=10, key=f'fix_{stage}')
        fixed += n * pct / 100
    now = 1 - po['late'].mean()
    new = (len(po) - len(late) + fixed) / len(po)
    k = st.columns(3)
    u.kpi(k[0], t('On time today', 'في الموعد اليوم'), f'{now:.1%}')
    u.kpi(k[1], t('On time after fixes', 'في الموعد بعد الإصلاح'), f'{new:.1%}', f"{(new - now) * 100:+.1f} {t('pts', 'نقطة')}")
    u.kpi(k[2], t('Late orders avoided', 'طلبات متأخرة تم تجنّبها'), f'{fixed:.0f}')
    fig = go.Figure(go.Bar(x=[t('Today', 'اليوم'), t('After fixes', 'بعد الإصلاح')], y=[now * 100, new * 100], marker_color=[u.GREY, u.AQUA],
                           text=[f'{now:.1%}', f'{new:.1%}'], textposition='outside'))
    fig.update_yaxes(title=t('% of orders on time', 'نسبة الطلبات في الموعد'), range=[0, 105])
    u.show(u.style(fig, t('Fixing half the sewing & finishing delays → ~89% on time', 'إصلاح نصف تأخير الخياطة والتشطيب ← ~89% في الموعد'), height=340))
    st.caption(t('How fixes happen: a second shift or one extra line at sewing in the peak months, SMED (faster changeovers) at finishing, '
                 'and starting peak-season orders earlier. A full digital twin would simulate every line hour by hour — this is the "lite" version.',
                 'كيف يتم الإصلاح: وردية ثانية أو خط إضافي للخياطة في أشهر الذروة، و SMED (تغيير أسرع) في التشطيب، '
                 'وبدء طلبات موسم الذروة مبكرًا. التوأم الرقمي الكامل يحاكي كل خط ساعة بساعة — وهذه نسخة مبسّطة.'))

with tab3:
    copq = u.copq_by_fy()
    gp = u.fy_summary()['gross_profit'] / 1e6
    l, r = st.columns(2)
    with l:
        fig = go.Figure()
        palette = [u.BLUE, u.ORANGE, u.AQUA, u.GREY]
        for col, colr in zip(copq.columns[:-1], palette):
            fig.add_trace(go.Bar(x=copq.index, y=copq[col], name=nm(col), marker_color=colr))
        fig.update_layout(barmode='stack')
        for fy_, tot in copq['total'].items():
            fig.add_annotation(x=fy_, y=tot, text=f'<b>{tot:.2f}M</b>', showarrow=False, yshift=12)
        fig.update_yaxes(title=t('EGP millions', 'مليون جنيه'), range=[0, copq['total'].max() * 1.2])
        u.show(u.style(fig, t(f"Poor quality costs {copq['total'].sum():.1f}M = {copq['total'].sum() / gp.sum():.0%} of gross profit",
                              f"الجودة الرديئة تكلّف {copq['total'].sum():.1f} مليون = {copq['total'].sum() / gp.sum():.0%} من إجمالي الربح"),
                       legend=True, height=420))
    with r:
        qc = files['Quality'].dropna(subset=['Defect_Type']).groupby('Defect_Type')['Rejected_Qty'].sum().sort_values()
        fig = go.Figure(go.Bar(y=[nm(x) for x in qc.index], x=qc.values, orientation='h',
                               marker_color=[u.ORANGE if i == 'Size Variance' else u.LIGHT_BLUE for i in qc.index],
                               text=[f'{v:,.0f}' for v in qc.values], textposition='outside'))
        fig.update_xaxes(title=t('Rejected units (QC)', 'القطع المرفوضة (فحص الجودة)'), range=[0, qc.max() * 1.2])
        u.show(u.style(fig, t('No single defect dominates — the top 3 are only 40%', 'لا يوجد عيب واحد مسيطر — أعلى 3 عيوب 40% فقط'), height=420))
    st.caption(t('COPQ is counted conservatively: QC scrap loss + refunds for quality returns + print rework + reprint ink. No double counting.',
                 'تكلفة الجودة محسوبة بتحفّظ: هالك فحص الجودة + مرتجعات الجودة + إعادة تشغيل الطباعة + حبر إعادة الطباعة. بدون احتساب مزدوج.'))

with tab4:
    mc = u.printing_machines()
    st.markdown(t('**Which printing machine to fix first?** Rank on reject rate + unplanned downtime hours + unplanned stops (1 = worst).',
                  '**أي ماكينة طباعة نصلح أولًا؟** ترتيب حسب نسبة المرفوض + ساعات التوقف المفاجئ + عدد التوقفات المفاجئة (1 = الأسوأ).'))
    show_mc = mc[['fix_order', 'Machine_ID', 'reject_rate_%', 'unplanned_hours', 'unplanned_events', 'priority_score']].round(2)
    u.table(show_mc.rename(columns={'fix_order': t('Fix order', 'ترتيب الإصلاح'), 'Machine_ID': t('Machine', 'الماكينة'), 'reject_rate_%': t('Reject %', 'المرفوض %'),
                                    'unplanned_hours': t('Unplanned downtime h', 'ساعات توقف مفاجئ'), 'unplanned_events': t('Unplanned stops', 'توقفات مفاجئة'),
                                    'priority_score': t('Score (lower = worse)', 'الدرجة (الأقل = الأسوأ)')}))
    dt = files['Machine_Downtime'].copy()
    dt['FY'] = u.fiscal_year(dt['Date'])
    l, r = st.columns(2)
    with l:
        a = dt.pivot_table(index='Business_Area', columns='Planned', values='Downtime_Hours', aggfunc='sum').fillna(0)
        a = a.loc[a.sum(axis=1).sort_values().index]
        areas = [nm(x) for x in a.index]
        fig = go.Figure()
        fig.add_trace(go.Bar(y=areas, x=a.get('No', 0), name=t('Unplanned', 'مفاجئ'), orientation='h', marker_color=u.ORANGE))
        fig.add_trace(go.Bar(y=areas, x=a.get('Yes', 0), name=t('Planned', 'مخطط'), orientation='h', marker_color=u.LIGHT_BLUE))
        fig.update_layout(barmode='stack')
        fig.update_xaxes(title=t('Downtime hours (3 years)', 'ساعات التوقف (3 سنوات)'))
        unpl = dt.loc[dt['Planned'] == 'No', 'Downtime_Hours'].sum() / dt['Downtime_Hours'].sum()
        u.show(u.style(fig, t(f'{unpl:.0%} of downtime is unplanned — printing is the biggest area', f'{unpl:.0%} من التوقف مفاجئ — والطباعة أكبر منطقة'), legend=True))
    with r:
        rs = dt.groupby('Reason')['Downtime_Hours'].sum().sort_values()
        fig = go.Figure(go.Bar(y=[nm(x) for x in rs.index], x=rs.values, orientation='h', marker_color=u.GREY,
                               text=[f"{v:,.0f} {t('h', 'س')}" for v in rs.values], textposition='outside'))
        fig.update_xaxes(title=t('Downtime hours (3 years)', 'ساعات التوقف (3 سنوات)'), range=[0, rs.max() * 1.25])
        u.show(u.style(fig, t('Mechanical faults lead — preventive maintenance pays', 'الأعطال الميكانيكية في المقدمة — الصيانة الوقائية تستحق')))
    pb = files['Printing_Batches']
    waits = ', '.join(f"{k} {v:.0f} {t('h', 'س')}" for k, v in dt[dt['Reason'] == 'Material wait'].groupby('FY')['Downtime_Hours'].sum().items())
    yld = pb['Good_Qty'].sum() / pb['Printed_Qty'].sum()
    st.caption(t(f"Printing yield {yld:.2%}. Material-wait downtime by year: {waits} → links to supplier delays (page 7).",
                 f"إنتاجية الطباعة {yld:.2%}. التوقف بسبب انتظار الخامات حسب السنة: {waits} ← مرتبط بتأخير الموردين (صفحة 7)."))
