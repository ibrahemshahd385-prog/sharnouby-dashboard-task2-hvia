import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('📦 Smart Inventory & Replenishment', '📦 المخزون الذكي وإعادة الطلب'),
         t('Some products tie up cash while others run out — and nobody forecasts demand.',
           'منتجات تحبس السيولة وأخرى تنفد — ولا أحد يتوقّع الطلب.'),
         '07_card04_inventory')

ACTION_AR = {'REORDER NOW': 'اطلب الآن', 'OVERSTOCK - transfer / promote': 'مخزون زائد - انقل / روّج', 'OK': 'سليم'}
act_name = lambda x: ACTION_AR.get(x, x) if u.is_ar() else x

inv = u.inventory()
snap = u.inventory_snapshot()
so = inv.groupby(['FY', 'Location'])['Stockout_Days_In_Month'].sum().unstack()
errors, future, std_daily, history = u.forecast_results()

c = st.columns(5)
u.kpi(c[0], t('Stock value (Sep 2026)', 'قيمة المخزون (سبتمبر 2026)'), u.money(snap['stock_value'].sum() / 1e6))
u.kpi(c[1], t('Excess beyond 90 days', 'الزائد عن 90 يومًا'), u.money(snap['excess_value'].sum() / 1e6),
      t(f"{snap['excess_value'].sum() / snap['stock_value'].sum():.0%} of stock", f"{snap['excess_value'].sum() / snap['stock_value'].sum():.0%} من المخزون"), inverse=True)
u.kpi(c[2], t('Products below reorder point', 'منتجات تحت نقطة إعادة الطلب'),
      f"{snap.loc[snap['below_reorder_point'], 'Product_ID'].nunique()} / {snap['Product_ID'].nunique()}")
u.kpi(c[3], t('Wholesale stockout days FY26', 'أيام نفاد الجملة FY26'), f"{so.loc['FY2026', 'Wholesale']:.0f}",
      t(f"{so.loc['FY2026', 'Wholesale'] / so.loc['FY2025', 'Wholesale'] - 1:+.0%} vs FY25",
        f"{so.loc['FY2026', 'Wholesale'] / so.loc['FY2025', 'Wholesale'] - 1:+.0%} مقارنة بـ FY25"), inverse=True)
u.kpi(c[4], t('AI forecast error (WAPE)', 'خطأ توقّع الذكاء الاصطناعي (WAPE)'), f"{errors['ai']:.1f}%",
      t(f"{errors['ai'] - errors['naive']:+.1f} pts vs last-year rule", f"{errors['ai'] - errors['naive']:+.1f} نقطة مقارنة بقاعدة العام الماضي"), inverse=True,
      help=t('Tested on Jul–Sep 2026, which the model never saw. Lower is better.',
             'تم اختباره على يوليو–سبتمبر 2026 التي لم يرها النموذج. الأقل أفضل.'))

tab1, tab2, tab3 = st.tabs([t('Stock health', 'صحة المخزون'), t('AI demand forecast', 'توقّع الطلب بالذكاء الاصطناعي'),
                            t('Replenishment plan', 'خطة إعادة الطلب')])

# ---------------------------------------------------------------- tab 1
with tab1:
    l, r = st.columns(2)
    with l:
        tt = u.stock_turns()
        fig = go.Figure(go.Bar(x=[u.ch_name(x) for x in tt['Location']], y=tt['days_of_stock'], marker_color=[u.CHANNEL_COLORS[x] for x in tt['Location']],
                               text=[t(f'{d:.0f} days<br>({x:.1f} turns)', f'{d:.0f} يوم<br>({x:.1f} دورة)') for d, x in zip(tt['days_of_stock'], tt['turns'])],
                               textposition='outside'))
        fig.update_yaxes(title=t('Days of stock on hand (FY2026)', 'أيام تغطية المخزون (FY2026)'), range=[0, tt['days_of_stock'].max() * 1.25])
        u.show(u.style(fig, t('Store stock lasts 229 days, wholesale only 21', 'مخزون المتجر يكفي 229 يومًا، والجملة 21 يومًا فقط')))
    with r:
        fig = go.Figure()
        for loc in ['Store', 'Online', 'Wholesale']:
            fig.add_trace(go.Bar(x=so.index, y=so[loc], name=u.ch_name(loc), marker_color=u.ORANGE if loc == 'Wholesale' else u.CHANNEL_COLORS[loc]))
        fig.update_layout(barmode='group')
        fig.update_yaxes(title=t('Stockout days (all products)', 'أيام النفاد (كل المنتجات)'))
        u.show(u.style(fig, t('Wholesale stockouts almost quadrupled in two years', 'نفاد مخزون الجملة تضاعف نحو 4 مرات في عامين'), legend=True))

    l, r = st.columns(2)
    with l:
        ax = u.abc_xyz()
        ct = pd.crosstab(ax['ABC'], ax['XYZ']).reindex(index=['A', 'B', 'C'], columns=['X', 'Y', 'Z'], fill_value=0)
        fig = go.Figure(go.Heatmap(z=ct.values,
                                   x=[t('X (steady)', 'X (مستقر)'), t('Y (seasonal)', 'Y (موسمي)'), t('Z (erratic)', 'Z (متذبذب)')],
                                   y=[t('A (80% of sales)', 'A (80% من المبيعات)'), t('B (next 15%)', 'B (الـ 15% التالية)'), t('C (last 5%)', 'C (آخر 5%)')],
                                   text=ct.values, texttemplate='%{text}', colorscale=[[0, '#f4f8fd'], [1, u.BLUE]], showscale=False))
        fig.update_yaxes(autorange='reversed')
        u.show(u.style(fig, t('ABC / XYZ: no erratic products, so forecasting works', 'ABC / XYZ: لا توجد منتجات متذبذبة، لذلك التوقّع ممكن')))
    with r:
        unmet = inv.groupby('FY')['unmet_units'].sum()
        fig = go.Figure(go.Bar(x=unmet.index, y=unmet.values, marker_color=u.ORANGE, text=[f'{v:,.0f}' for v in unmet.values], textposition='outside'))
        fig.update_yaxes(title=t('Units customers wanted but could not get', 'قطع طلبها العملاء ولم يحصلوا عليها'), range=[0, unmet.max() * 1.2])
        u.show(u.style(fig, t('Unmet demand grew 7x in two years', 'الطلب غير المُلبّى زاد 7 أضعاف في عامين')))

    st.markdown(t('**Excess stock by product (Sep 2026)**', '**المخزون الزائد حسب المنتج (سبتمبر 2026)**'))
    ex = snap.groupby(['Product_Name'])[['excess_units', 'excess_value']].sum().sort_values('excess_value', ascending=False).head(15).reset_index()
    ex['excess_value'] = (ex['excess_value'] / 1e3).round(0)
    u.table(ex.rename(columns={'Product_Name': t('Product', 'المنتج'), 'excess_units': t('Excess units', 'القطع الزائدة'),
                               'excess_value': t('Excess value (K EGP)', 'القيمة الزائدة (ألف جنيه)')}))

# ---------------------------------------------------------------- tab 2
with tab2:
    pm = u.load()['Product_Master'].set_index('Product_ID')['Product_Name']
    l, r = st.columns(2)
    loc_pick = l.selectbox(t('Location', 'المكان'), ['All', 'Store', 'Online', 'Wholesale'],
                           format_func=lambda x: t('All', 'الكل') if x == 'All' else u.ch_name(x))
    names = ['All products'] + sorted(pm.unique())
    prod_pick = r.selectbox(t('Product', 'المنتج'), names, format_func=lambda x: t('All products', 'كل المنتجات') if x == 'All products' else x)
    h, f = history.copy(), future.copy()
    h['Location'], f['Location'] = h['Location_ID'].map(u.LOC), f['Location_ID'].map(u.LOC)
    h['Product'], f['Product'] = h['Product_ID'].map(pm), f['Product_ID'].map(pm)
    if loc_pick != 'All':
        h, f = h[h['Location'] == loc_pick], f[f['Location'] == loc_pick]
    if prod_pick != 'All products':
        h, f = h[h['Product'] == prod_pick], f[f['Product'] == prod_pick]
    ht, ft = h.groupby('month')['Sold_Qty'].sum(), f.groupby('month')['forecast'].sum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ht.index, y=ht.values, name=t('Actual', 'الفعلي'), mode='lines', line=dict(color=u.BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=[ht.index[-1]] + list(ft.index), y=[ht.values[-1]] + list(ft.values), name=t('AI forecast', 'توقّع الذكاء الاصطناعي'),
                             mode='lines+markers', line=dict(color=u.ORANGE, width=3, dash='dash')))
    fig.update_yaxes(title=t('Units sold per month', 'القطع المباعة شهريًا'))
    u.show(u.style(fig, t('AI forecast for the next 90 days (Oct–Dec 2026)', 'توقّع الذكاء الاصطناعي للـ 90 يومًا القادمة (أكتوبر–ديسمبر 2026)'), legend=True, height=420))
    units = t('units', 'قطعة')
    a, b, c2 = st.columns(3)
    u.kpi(a, t('Next 30 days', 'الـ 30 يومًا القادمة'), f"{ft.iloc[0]:,.0f} {units}")
    u.kpi(b, t('Next 60 days', 'الـ 60 يومًا القادمة'), f"{ft.iloc[:2].sum():,.0f} {units}")
    u.kpi(c2, t('Next 90 days', 'الـ 90 يومًا القادمة'), f"{ft.sum():,.0f} {units}")
    better = 1 - errors['ai'] / errors['naive']
    st.caption(t(f"How we know it works: we hid Jul–Sep 2026 from the model and asked it to predict them. Error {errors['ai']:.1f}% vs "
                 f"{errors['naive']:.1f}% for 'same as last year' → about {better:.0%} more accurate. "
                 'Model: gradient boosting on last 1, 2, 3 and 12 months + month + location + product family + season.',
                 f"كيف نعرف أنه يعمل: أخفينا يوليو–سبتمبر 2026 عن النموذج وطلبنا منه توقّعها. الخطأ {errors['ai']:.1f}% مقابل "
                 f"{errors['naive']:.1f}% لقاعدة 'مثل العام الماضي' ← أدق بنحو {better:.0%}. "
                 'النموذج: Gradient Boosting على مبيعات آخر 1 و 2 و 3 و 12 شهرًا + الشهر + المكان + عائلة المنتج + الموسم.'))

# ---------------------------------------------------------------- tab 3
with tab3:
    l, m_, r = st.columns(3)
    sl = l.selectbox(t('Service level (chance of NOT running out)', 'مستوى الخدمة (احتمال عدم النفاد)'), list(u.SERVICE_LEVEL_Z), index=1)
    loc_f = m_.multiselect(t('Location', 'المكان'), ['Store', 'Online', 'Wholesale'], default=['Store', 'Online', 'Wholesale'], format_func=u.ch_name)
    act_f = r.multiselect(t('Action', 'الإجراء'), ['REORDER NOW', 'OVERSTOCK - transfer / promote', 'OK'],
                          default=['REORDER NOW', 'OVERSTOCK - transfer / promote'], format_func=act_name)
    plan = u.replenishment_plan(u.SERVICE_LEVEL_Z[sl])
    view = plan[plan['Location'].isin(loc_f) & plan['action'].isin(act_f)]
    k = st.columns(4)
    u.kpi(k[0], t('Units to reorder now', 'قطع يجب طلبها الآن'), f"{view['order_qty'].sum():,.0f}")
    u.kpi(k[1], t('Excess stock value', 'قيمة المخزون الزائد'), u.money(view['excess_value'].sum() / 1e6))
    u.kpi(k[2], t('Rows to reorder', 'بنود يجب طلبها'), f"{(view['action'] == 'REORDER NOW').sum()}")
    u.kpi(k[3], t('Rows overstocked', 'بنود بها مخزون زائد'), f"{(view['action'] == 'OVERSTOCK - transfer / promote').sum()}")
    cols = ['Location', 'Product_Name', 'Closing_Stock', 'forecast_30d', 'forecast_90d', 'safety_stock', 'reorder_point', 'order_qty', 'excess_vs_90d', 'action']
    out = view[cols].sort_values(['action', 'order_qty'], ascending=[False, False]).copy()
    out['Location'] = out['Location'].map(u.ch_name)
    out['action'] = out['action'].map(act_name)
    out = out.rename(columns={'Location': t('Location', 'المكان'), 'Product_Name': t('Product', 'المنتج'), 'Closing_Stock': t('Stock now', 'المخزون الحالي'),
                              'forecast_30d': t('Forecast 30d', 'توقّع 30 يوم'), 'forecast_90d': t('Forecast 90d', 'توقّع 90 يوم'),
                              'safety_stock': t('Safety stock', 'مخزون الأمان'), 'reorder_point': t('Reorder point', 'نقطة إعادة الطلب'),
                              'order_qty': t('Order qty', 'كمية الطلب'), 'excess_vs_90d': t('Excess units', 'القطع الزائدة'), 'action': t('Action', 'الإجراء')})
    u.table(out, height=380)
    st.download_button(t('⬇️ Download the replenishment plan (CSV)', '⬇️ تنزيل خطة إعادة الطلب (CSV)'), out.to_csv(index=False).encode('utf-8-sig'),
                       'replenishment_plan.csv', 'text/csv')
    st.markdown(t('**Before buying: move stock between locations**', '**قبل الشراء: انقل المخزون بين الأماكن**'))
    tr = u.transfers(plan)
    st.caption(t(f'{len(tr)} products / {tr["transfer_qty"].sum():,.0f} units that wholesale needs are sitting as excess in the store or online.',
                 f'{len(tr)} منتجًا / {tr["transfer_qty"].sum():,.0f} قطعة تحتاجها الجملة موجودة كمخزون زائد في المتجر أو الأونلاين.'))
    u.table(tr.head(15).drop(columns='Product_ID').rename(columns={
        'Product_Name': t('Product', 'المنتج'), 'wholesale_needs': t('Wholesale needs', 'احتياج الجملة'), 'store_excess': t('Store excess', 'زائد المتجر'),
        'online_excess': t('Online excess', 'زائد الأونلاين'), 'transfer_qty': t('Transfer', 'كمية النقل')}))
    st.caption(t('Safety stock = Z × daily demand variation × √lead time. Reorder point = daily demand × lead time + safety stock. '
                 'Order up to = demand for (lead time + 30 days) + safety stock.',
                 'مخزون الأمان = Z × تذبذب الطلب اليومي × √مدة التوريد. نقطة إعادة الطلب = الطلب اليومي × مدة التوريد + مخزون الأمان. '
                 'الطلب حتى = الطلب لمدة (مدة التوريد + 30 يومًا) + مخزون الأمان.'))
