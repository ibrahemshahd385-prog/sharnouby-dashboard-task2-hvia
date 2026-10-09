import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('🎯 Executive Command Center', '🎯 مركز القيادة التنفيذي'),
         t('Revenue is growing — is it turning into profit, and where is margin leaking?',
           'الإيرادات تنمو — فهل يتحوّل هذا النمو إلى ربح، وأين يتسرّب الهامش؟'),
         '04_card01_sales · 06_card03_channels · 13_card10_story')

files = u.load()
fy = u.fy_summary()
fys = list(fy.index)
pick = st.selectbox(t('Fiscal year (Oct–Sep)', 'السنة المالية (أكتوبر–سبتمبر)'), fys, index=len(fys) - 1)
row = fy.loc[pick]
prev = fy.loc[fys[fys.index(pick) - 1]] if fys.index(pick) > 0 else None
ch = u.channel_fy()
chy = ch[ch['FY'] == pick].set_index('Channel')
online_share = chy.loc['Online', 'net_sales'] / chy.loc[['Online', 'Retail'], 'net_sales'].sum()
copq = u.copq_by_fy().loc[pick, 'total']


def delta(col, pct=True):
    if prev is None:
        return None
    return f'{(row[col] / prev[col] - 1):+.1%}' if pct else f"{(row[col] - prev[col]) * 100:+.1f} {t('pts', 'نقطة')}"


c = st.columns(6)
u.kpi(c[0], t('Net sales', 'صافي المبيعات'), u.money(row['net_sales'] / 1e6), delta('net_sales'))
u.kpi(c[1], t('Gross profit', 'إجمالي الربح'), u.money(row['gross_profit'] / 1e6), delta('gross_profit'))
u.kpi(c[2], t('Gross margin', 'هامش الربح'), f"{row['margin']:.1%}", delta('margin', pct=False))
u.kpi(c[3], t('Discounts given', 'الخصومات الممنوحة'), u.money(row['discount'] / 1e6), delta('discount'), inverse=True,
      help=t('Gross sales minus net sales. Over 3 years discounts were 2.8x gross profit.',
             'إجمالي المبيعات ناقص صافي المبيعات. على مدار 3 سنوات كانت الخصومات 2.8 ضعف إجمالي الربح.'))
u.kpi(c[4], t('Online share', 'حصة الأونلاين'), f'{online_share:.0%}',
      help=t('Online vs the Sidi Bishr store (wholesale excluded).', 'الأونلاين مقابل متجر سيدي بشر (بدون الجملة).'))
u.kpi(c[5], t('Poor quality cost', 'تكلفة الجودة الرديئة'), u.money(copq), inverse=True,
      help=t('QC scrap + quality refunds + print rework + reprint ink (Card 07).',
             'هالك فحص الجودة + مرتجعات الجودة + إعادة تشغيل الطباعة + حبر إعادة الطباعة (كارت 07).'))

# ---------------------------------------------------------------- trend + channel mix
left, right = st.columns([3, 2])
with left:
    m = u.monthly_sales()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m['Month'], y=m['net_sales'] / 1e6, name=t('Net sales', 'صافي المبيعات'), mode='lines',
                             line=dict(color=u.BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=m['Month'], y=m['gross_profit'] / 1e6, name=t('Gross profit', 'إجمالي الربح'), mode='lines',
                             line=dict(color=u.AQUA, width=2.5)))
    fig.update_yaxes(title=t('EGP millions per month', 'مليون جنيه شهريًا'))
    u.show(u.style(fig, t('Sales peak every December — profit stays a thin slice of it',
                          'المبيعات تبلغ ذروتها كل ديسمبر — والربح يبقى شريحة رفيعة منها'), legend=True))
with right:
    shares = ch[ch['FY'] == pick].set_index('Channel').reindex(['Wholesale', 'Retail', 'Online'])
    sales_pct = shares['net_sales'] / shares['net_sales'].sum() * 100
    gp_pct = shares['gross_profit'] / shares['gross_profit'].sum() * 100
    names = [u.ch_name(x) for x in ['Wholesale', 'Retail', 'Online']]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=sales_pct, name=t('% of sales', 'نسبة المبيعات'), marker_color=u.LIGHT_BLUE,
                         text=[f'{v:.0f}%' for v in sales_pct], textposition='outside'))
    fig.add_trace(go.Bar(x=names, y=gp_pct, name=t('% of gross profit', 'نسبة إجمالي الربح'), marker_color=u.BLUE,
                         text=[f'{v:.0f}%' for v in gp_pct], textposition='outside'))
    fig.update_layout(barmode='group')
    fig.update_yaxes(title='%', range=[0, 105])
    u.show(u.style(fig, t('Store + online: small in sales, big in profit', 'المتجر + الأونلاين: صغير في المبيعات، كبير في الربح'), legend=True))

# ---------------------------------------------------------------- alerts
st.subheader(t('🚨 What needs attention now', '🚨 ما يحتاج إلى انتباه الآن'))
inv = u.inventory()
so = inv[inv['Location'] == 'Wholesale'].groupby('FY')['Stockout_Days_In_Month'].sum()
snap = u.inventory_snapshot()
below = snap.loc[snap['below_reorder_point'], 'Product_ID'].nunique()
sup = u.supplier_metrics().set_index('Supplier_ID')
camp = u.campaigns()
infl = camp[camp['Platform'] == 'Influencer']
s = files['Sales_Transactions']
size_share = s.loc[s['is_size_return'], 'Refund_Value_EGP'].sum() / s.loc[s['is_return'], 'Refund_Value_EGP'].sum()
disc_total, disc_x = fy['discount'].sum() / 1e6, fy['discount'].sum() / fy['gross_profit'].sum()
claim_x = camp['Attributed_Revenue_EGP'].sum() / camp['actual_sales'].sum()
infl_roas = infl['Attributed_Revenue_EGP'].sum() / infl['Spend_EGP'].sum()
copq_total = u.copq_by_fy()['total'].sum()
copq_pct = copq_total / (fy['gross_profit'].sum() / 1e6)
l09, l04 = sup.loc['SUP09', 'late_rate'], sup.loc['SUP04', 'late_rate']
alerts = [
    (t('Sales', 'المبيعات'),
     t(f"Discounts ({disc_total:.0f}M) are **{disc_x:.1f}x gross profit** over 3 years. Orders with 32–38% discount earn only 8.6% margin.",
       f"الخصومات ({disc_total:.0f} مليون) تساوي **{disc_x:.1f} ضعف إجمالي الربح** على مدار 3 سنوات. الطلبات بخصم 32–38% هامشها 8.6% فقط."),
     t('Executive (this page)', 'هذه الصفحة')),
    (t('Inventory', 'المخزون'),
     t(f"Wholesale stockout days went **{so.iloc[0]:.0f} → {so.iloc[-1]:.0f}** while half the stock (7.9M) is excess. **{below} products** are below their reorder point.",
       f"أيام نفاد مخزون الجملة ارتفعت من **{so.iloc[0]:.0f} إلى {so.iloc[-1]:.0f}** بينما نصف المخزون (7.9 مليون) زائد. **{below} منتجًا** تحت نقطة إعادة الطلب."),
     t('Smart Inventory', 'المخزون الذكي')),
    (t('Suppliers', 'الموردون'),
     t(f"SUP09 is late **{l09:.0%}** of the time and SUP04 (contracted) **{l04:.0%}** — vs ~30% for the rest.",
       f"المورد SUP09 يتأخر في **{l09:.0%}** من الطلبات، و SUP04 (المتعاقد معه) في **{l04:.0%}** — مقابل نحو 30% لبقية الموردين."),
     t('Procurement & Supplier Risk', 'المشتريات ومخاطر الموردين')),
    (t('Marketing', 'التسويق'),
     t(f"Platforms claim **{claim_x:.1f}x** the sales that actually happened. Influencer ROAS is only **{infl_roas:.2f}**.",
       f"المنصات تنسب لنفسها **{claim_x:.1f} ضعف** المبيعات التي حدثت فعلًا. عائد إنفاق المؤثرين (ROAS) **{infl_roas:.2f}** فقط."),
     t('Marketing', 'التسويق')),
    (t('Factory', 'المصنع'),
     t(f"Cost of poor quality is **{copq_total:.1f}M** in 3 years = {copq_pct:.0%} of gross profit. Sewing + finishing cause 68% of delay days.",
       f"تكلفة الجودة الرديئة **{copq_total:.1f} مليون** في 3 سنوات = {copq_pct:.0%} من إجمالي الربح. الخياطة والتشطيب يسببان 68% من أيام التأخير."),
     t('Factory Digital Twin', 'التوأم الرقمي للمصنع')),
    (t('Customers', 'العملاء'),
     t(f"Size / fit is **{size_share:.0%} of all refunds** and the #1 support question — online returns 2x more for size than the store.",
       f"المقاس هو **{size_share:.0%} من كل المرتجعات** والسؤال الأول لخدمة العملاء — والأونلاين يرتجع بسبب المقاس ضعف المتجر."),
     t('Size & Fit Intelligence', 'ذكاء المقاسات')),
]
for area, text, page in alerts:
    st.markdown(f'- **{area}:** {text} → *{page}*')

# ---------------------------------------------------------------- profit bridge (what-if)
st.subheader(t('💰 Action plan: how much profit is on the table?', '💰 خطة العمل: كم من الربح يمكن تحقيقه؟'))
with st.expander(t('Adjust the assumptions (every number below updates live)', 'عدّل الافتراضات (كل الأرقام بالأسفل تتحدّث فورًا)'), expanded=False):
    a, b, c3 = st.columns(3)
    cap = a.slider(t('Wholesale discount cap (%)', 'سقف خصم الجملة (%)'), 20, 40, 30, step=1) / 100
    holding = a.slider(t('Yearly holding cost of excess stock (%)', 'تكلفة الاحتفاظ السنوية بالمخزون الزائد (%)'), 10, 30, 20) / 100
    copq_cut = b.slider(t('Reduce cost of poor quality by (%)', 'خفض تكلفة الجودة الرديئة بنسبة (%)'), 0, 40, 20) / 100
    infl_cut = b.slider(t('Cut Influencer spend by (%)', 'خفض إنفاق المؤثرين بنسبة (%)'), 0, 100, 70, step=10) / 100
    size_cut = c3.slider(t('Cut size/fit returns by (%)', 'خفض مرتجعات المقاس بنسبة (%)'), 0, 50, 30, step=5) / 100
    winback = c3.slider(t('At-risk customers won back (%)', 'نسبة استعادة العملاء المعرّضين للخسارة (%)'), 0, 40, 20, step=5) / 100
    include_wb = c3.toggle(t('Include win-back (needs a control-group test first)', 'تضمين الاستعادة (تحتاج تجربة بمجموعة ضابطة أولًا)'), value=True)

at_risk_rev = u.rfm().loc[lambda d: d['segment'].str.startswith('At Risk'), 'monetary'].sum() / 3 / 1e6
plan, b_in, cap_gain, breakeven = u.profit_bridge(cap=cap, winback=winback, at_risk_rev=at_risk_rev, holding=holding,
                                                  excess=7.4, influencer_cut=infl_cut, copq_cut=copq_cut, size_cut=size_cut,
                                                  include_winback=include_wb)
base = b_in['base_profit']
total = plan['profit_M'].sum()

fig = go.Figure(go.Waterfall(
    x=[t('FY2026 profit', 'ربح FY2026')] + list(plan['short']) + [t('Potential', 'المتوقع')],
    hovertext=[t('FY2026 gross profit', 'إجمالي ربح FY2026')] + list(plan['action']) + [t('Potential gross profit', 'إجمالي الربح المتوقع')],
    y=[base] + list(plan['profit_M']) + [0],
    measure=['absolute'] + ['relative'] * len(plan) + ['total'],
    text=[f'{base:.1f}M'] + [f'+{v:.1f}' for v in plan['profit_M']] + [f'{base + total:.1f}M'],
    textposition='outside',
    increasing=dict(marker=dict(color=u.AQUA)), totals=dict(marker=dict(color=u.BLUE)),
    connector=dict(line=dict(color='#d6d5d0'))))
fig.update_yaxes(title=t('Gross profit, EGP millions / year', 'إجمالي الربح، مليون جنيه / سنة'), range=[0, (base + total) * 1.15])
u.show(u.style(fig, t(f'{len(plan)} actions could lift gross profit by ~{total:.1f}M EGP a year (+{total / base:.0%})',
                      f'{len(plan)} إجراءات يمكن أن ترفع إجمالي الربح بنحو {total:.1f} مليون جنيه سنويًا (+{total / base:.0%})'), height=440))

k = st.columns(4)
u.kpi(k[0], t('Profit today (FY2026)', 'الربح الحالي (FY2026)'), u.money(base))
u.kpi(k[1], t('Potential uplift / year', 'الزيادة المتوقعة / سنة'), u.money(total), f'+{total / base:.0%}')
u.kpi(k[2], t('Biggest lever', 'أكبر رافعة'), plan.iloc[0]['short'] if len(plan) else '-', help=plan.iloc[0]['action'] if len(plan) else None)
u.kpi(k[3], t('Discount cap break-even', 'نقطة تعادل سقف الخصم'), f'{breakeven:.0%}',
      help=t('The cap stays profitable unless wholesale volume drops by more than this.',
             'يظل السقف مربحًا ما لم تنخفض كميات الجملة بأكثر من هذه النسبة.'))

growth = b_in['growth']
fy27 = b_in['base_sales'] * (1 + growth) * (base / b_in['base_sales'])
wh_after = (b_in['wh_profit'] + cap_gain) * (1 + growth)
col_s, col_gp, col_vs = t('Scenario', 'السيناريو'), t('Gross profit FY2027 (M EGP)', 'إجمالي ربح FY2027 (مليون جنيه)'), t('vs FY2026', 'مقارنة بـ FY2026')
scen = pd.DataFrame({
    col_s: [t('A. Do nothing', 'أ. عدم اتخاذ أي إجراء'), t('B. Action plan', 'ب. تنفيذ خطة العمل'),
            t('C. Action plan, wholesale loses 10% volume', 'ج. خطة العمل مع خسارة 10% من كميات الجملة')],
    col_gp: [fy27, fy27 + total, fy27 + total - 0.10 * wh_after],
})
scen[col_vs] = (scen[col_gp] / base - 1).map('{:+.0%}'.format)
scen[col_gp] = scen[col_gp].round(1)
u.table(scen)
st.caption(t(f'FY2027 assumes sales grow {growth:.1%} (same as FY2026) with the same margin. '
             'Every action has its assumption written next to it in notebook 13_card10_story.',
             f'يفترض FY2027 نمو المبيعات بنسبة {growth:.1%} (مثل FY2026) بنفس الهامش. '
             'كل إجراء مكتوب بجانبه افتراضه في النوت بوك 13_card10_story.'))
u.insight(t('The company sells a lot but does not manage profit: discounts, excess stock, suppliers and quality all leak margin. '
            f'The discount cap alone is worth {cap_gain:.1f}M a year — the single biggest lever.',
            'الشركة تبيع كثيرًا لكنها لا تدير الربح: الخصومات والمخزون الزائد والموردون والجودة كلها تسرّب الهامش. '
            f'سقف الخصم وحده يساوي {cap_gain:.1f} مليون سنويًا — وهو أكبر رافعة منفردة.'))
