import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('👥 Customer 360 & Retention', '👥 العميل 360 والاحتفاظ بالعملاء'),
         t('Who comes back, how much is each customer worth, and who are we losing?',
           'من يعود للشراء، وكم تساوي قيمة كل عميل، ومن نخسر؟'),
         '05_card02_customers · 14_ai_churn_test')

files = u.load()
s, cust = files['Sales_Transactions'], files['Customers'].set_index('Customer_ID')
retail = s[s['Customer_Type'] == 'Retail']
r = u.rfm()
top20 = r['monetary'].sort_values(ascending=False)
top20_share = top20.head(int(len(top20) * 0.2)).sum() / top20.sum()
never = (cust['Customer_Type'] == 'Retail').sum() - len(r)

c = st.columns(5)
u.kpi(c[0], t('Retail buyers', 'عملاء التجزئة المشترون'), f'{len(r):,}',
      help=t(f"{never:,} registered customers never bought.", f"{never:,} عميلًا مسجّلًا لم يشتروا أبدًا."))
u.kpi(c[1], t('Bought more than once', 'اشتروا أكثر من مرة'), f"{(r['frequency'] > 1).mean():.1%}")
u.kpi(c[2], t('Orders per customer', 'طلبات لكل عميل'), f"{r['frequency'].mean():.1f}")
u.kpi(c[3], t('Average order value', 'متوسط قيمة الطلب'), f"{r['monetary'].sum() / r['frequency'].sum():,.0f} EGP")
u.kpi(c[4], t('Top 20% customers = revenue', 'أعلى 20% من العملاء = من الإيراد'), f'{top20_share:.0%}')

tab1, tab2, tab3 = st.tabs([t('Segments (RFM)', 'الشرائح (RFM)'), t('Cohorts & channels', 'الدفعات والقنوات'), t('Customer lookup', 'البحث عن عميل')])

with tab1:
    seg = r.groupby('segment').agg(customers=('monetary', 'size'), revenue=('monetary', 'sum'),
                                   recency=('recency', 'median'), orders=('frequency', 'mean')).reindex(u.SEGMENT_ORDER)
    seg['cust_%'] = seg['customers'] / seg['customers'].sum() * 100
    seg['rev_%'] = seg['revenue'] / seg['revenue'].sum() * 100
    labels = [u.seg_name(x) for x in seg.index]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=seg['cust_%'], name=t('% of customers', 'نسبة العملاء'), orientation='h', marker_color=u.LIGHT_BLUE,
                         text=[f'{v:.0f}%' for v in seg['cust_%']], textposition='outside'))
    fig.add_trace(go.Bar(y=labels, x=seg['rev_%'], name=t('% of revenue', 'نسبة الإيراد'), orientation='h', marker_color=u.BLUE,
                         text=[f'{v:.0f}%' for v in seg['rev_%']], textposition='outside'))
    fig.update_layout(barmode='group')
    fig.update_yaxes(autorange='reversed')
    fig.update_xaxes(title='%', range=[0, seg[['cust_%', 'rev_%']].max().max() * 1.2])
    u.show(u.style(fig, t("\"At Risk (Can't Lose)\": 15% of customers, 31% of revenue — and they stopped buying",
                          '"لا يمكن خسارتهم": 15% من العملاء و31% من الإيراد — وتوقّفوا عن الشراء'), legend=True, height=430))
    st.warning(t("**Honest test (notebook 14):** we trained an AI churn model to predict who stops buying. AUC = **0.51** "
                 "(0.5 = coin flip), and customers come back ~66% of the time whatever their recency. "
                 "So these segments **describe** the past, they do **not predict** the future. "
                 "→ The win-back campaign must start as a test: half the list gets the offer, half does not (control group).",
                 "**اختبار صادق (النوت بوك 14):** درّبنا نموذج ذكاء اصطناعي لتوقّع من سيتوقف عن الشراء. AUC = **0.51** "
                 "(0.5 = رمي عملة)، والعملاء يعودون بنسبة ~66% مهما كان تاريخ آخر شراء. "
                 "إذن هذه الشرائح **تصف** الماضي ولا **تتنبأ** بالمستقبل. "
                 "← حملة الاستعادة يجب أن تبدأ كتجربة: نصف القائمة يحصل على العرض والنصف الآخر لا (مجموعة ضابطة)."), icon='⚠️')
    seg_show = seg[['customers', 'cust_%', 'rev_%', 'recency', 'orders']].round(1).reset_index()
    seg_show['segment'] = seg_show['segment'].map(u.seg_name)
    u.table(seg_show.rename(columns={'segment': t('Segment', 'الشريحة'), 'customers': t('Customers', 'العملاء'), 'cust_%': t('% customers', 'نسبة العملاء'),
                                     'rev_%': t('% revenue', 'نسبة الإيراد'), 'recency': t('Days since last order (median)', 'أيام منذ آخر طلب (الوسيط)'),
                                     'orders': t('Avg orders', 'متوسط الطلبات')}))
    st.markdown(t('**Win-back test list** (At Risk, opted-in to messages)', '**قائمة تجربة الاستعادة** (المعرّضون للخسارة، الموافقون على الرسائل)'))
    wl = r[r['segment'].str.startswith('At Risk')].join(cust[['Consent_Status', 'Governorate']])
    wl = wl[wl['Consent_Status'] == 'Opted-in'].sort_values('monetary', ascending=False)
    rng = np.random.default_rng(42)
    wl['group'] = np.where(rng.random(len(wl)) < 0.5, t('TEST (send offer)', 'تجربة (أرسل العرض)'), t('CONTROL (no offer)', 'ضابطة (بدون عرض)'))
    st.caption(t(f"{len(wl):,} customers · randomly split 50/50 so we can measure the real effect of the campaign.",
                 f"{len(wl):,} عميلًا · مقسّمون عشوائيًا 50/50 حتى نقيس الأثر الحقيقي للحملة."))
    out = wl[['segment', 'recency', 'frequency', 'monetary', 'Governorate', 'group']].reset_index()
    out['monetary'] = out['monetary'].round(0)
    out['segment'] = out['segment'].map(u.seg_name)
    out = out.rename(columns={'Customer_ID': t('Customer', 'العميل'), 'segment': t('Segment', 'الشريحة'), 'recency': t('Days since last order', 'أيام منذ آخر طلب'),
                              'frequency': t('Orders', 'الطلبات'), 'monetary': t('Spend (EGP)', 'الإنفاق (جنيه)'), 'Governorate': t('Governorate', 'المحافظة'),
                              'group': t('Group', 'المجموعة')})
    u.table(out.head(200), height=300)
    st.download_button(t('⬇️ Download the full test list (CSV)', '⬇️ تنزيل قائمة التجربة كاملة (CSV)'), out.to_csv(index=False).encode('utf-8-sig'),
                       'winback_test_list.csv', 'text/csv')

with tab2:
    ret = u.cohort_table()
    cols = [k for k in ret.columns if k <= 8]
    z = ret[cols].values
    fig = go.Figure(go.Heatmap(z=z, x=[f'Q+{k}' for k in cols], y=ret.index, colorscale=[[0, '#f4f8fd'], [1, u.BLUE]],
                               text=np.where(np.isnan(z), '', np.vectorize(lambda v: f'{v:.0f}%')(np.nan_to_num(z))),
                               texttemplate='%{text}', showscale=False,
                               hovertemplate=t('Cohort %{y}, %{x}: %{z:.0f}%', 'دفعة %{y}، %{x}: %{z:.0f}%') + '<extra></extra>'))
    fig.update_yaxes(autorange='reversed', title=t('Join quarter', 'ربع التسجيل'))
    fig.update_xaxes(title=t('Quarters after joining', 'الأرباع بعد التسجيل'), side='top')
    u.show(u.style(fig, t('Newer customers come back much less than the first ones', 'العملاء الجدد يعودون أقل بكثير من الأوائل'), height=460))
    st.caption(t('Each cell = % of customers who joined in that quarter and bought again k quarters later.',
                 'كل خانة = نسبة العملاء الذين سجّلوا في ذلك الربع واشتروا مرة أخرى بعد k ربعًا.'))

    l, rr = st.columns(2)
    with l:
        b2c = retail[retail['Channel'].isin(['Online', 'Retail'])]
        used = b2c.groupby('Customer_ID')['Channel'].agg(lambda x: 'Both' if x.nunique() > 1 else ('Store only' if x.iloc[0] == 'Retail' else 'Online only'))
        spend = r['monetary']
        omni = pd.DataFrame({'group': used}).join(spend.rename('spend')).groupby('group').agg(customers=('spend', 'size'), spend=('spend', 'mean'))
        omni = omni.reindex(['Store only', 'Online only', 'Both'])
        omni_lbl = {'Store only': t('Store only', 'المتجر فقط'), 'Online only': t('Online only', 'الأونلاين فقط'), 'Both': t('Both', 'الاثنان')}
        fig = go.Figure(go.Bar(x=[omni_lbl[i] for i in omni.index], y=omni['spend'], marker_color=[u.LIGHT_BLUE, u.LIGHT_BLUE, u.ORANGE],
                               text=[t(f'{v:,.0f} EGP<br>{n:,} customers', f'{v:,.0f} جنيه<br>{n:,} عميل') for v, n in zip(omni['spend'], omni['customers'])],
                               textposition='outside'))
        fig.update_yaxes(title=t('Average spend per customer (3 years)', 'متوسط إنفاق العميل (3 سنوات)'), range=[0, omni['spend'].max() * 1.3])
        ratio = omni.loc['Both', 'spend'] / omni.loc[['Store only', 'Online only'], 'spend'].max()
        u.show(u.style(fig, t(f'Customers who use store AND online spend ~{ratio:.0f}x more', f'من يشتري من المتجر والأونلاين معًا ينفق ~{ratio:.0f} أضعاف')))
    with rr:
        acq = r.join(cust['Acquisition_Channel']).groupby('Acquisition_Channel').agg(spend=('monetary', 'mean'), repeat=('frequency', lambda x: (x > 1).mean() * 100))
        acq = acq.sort_values('spend')
        fig = go.Figure(go.Bar(y=acq.index, x=acq['spend'], orientation='h', marker_color=u.GREY, text=[f'{v:,.0f}' for v in acq['spend']], textposition='outside'))
        fig.update_xaxes(title=t('Average spend per customer (EGP)', 'متوسط إنفاق العميل (جنيه)'), range=[0, acq['spend'].max() * 1.2])
        u.show(u.style(fig, t('How a customer was acquired makes no difference', 'طريقة اكتساب العميل لا تُحدث فرقًا')))

with tab3:
    st.caption(t('Type a customer ID (for example one from the win-back list) to see the full profile.',
                 'اكتب رقم عميل (مثلًا من قائمة الاستعادة) لعرض ملفه الكامل.'))
    default_id = r.sort_values('monetary', ascending=False).index[0]
    cid = st.text_input(t('Customer ID', 'رقم العميل'), value=default_id).strip().upper()
    if cid not in r.index:
        st.error(t('Customer not found among retail buyers.', 'العميل غير موجود ضمن مشتري التجزئة.'))
    else:
        p, info = r.loc[cid], cust.loc[cid]
        orders = retail[retail['Customer_ID'] == cid]
        short_seg = t(p['segment'].replace("At Risk (Can't Lose)", "Can't Lose"),
                      'لا يمكن خسارتهم' if p['segment'] == "At Risk (Can't Lose)" else u.seg_name(p['segment']))
        consent = t(info['Consent_Status'], 'موافق' if info['Consent_Status'] == 'Opted-in' else 'غير موافق')
        k = st.columns(5)
        u.kpi(k[0], t('Segment', 'الشريحة'), short_seg, help=u.seg_name(p['segment']))
        u.kpi(k[1], t('Total spend', 'إجمالي الإنفاق'), f"{p['monetary']:,.0f} EGP")
        u.kpi(k[2], t('Orders', 'الطلبات'), f"{p['frequency']}")
        u.kpi(k[3], t('Days since last order', 'أيام منذ آخر طلب'), f"{p['recency']}")
        u.kpi(k[4], t('WhatsApp consent', 'موافقة واتساب'), consent)
        channels = ', '.join(sorted({u.ch_name(x) for x in orders['Channel'].unique()}))
        fav = orders.groupby('Product_Family')['Quantity'].sum().idxmax()
        st.markdown(t(f"**{info['Gender']}, {info['Age_Band']}, {info['Governorate']}** · joined {info['Join_Date']:%b %Y} via {info['Acquisition_Channel']} · "
                      f"channels used: {channels} · favourite family: {fav} · returns: {orders['is_return'].mean():.0%} of lines",
                      f"**{info['Gender']}، {info['Age_Band']}، {info['Governorate']}** · سجّل في {info['Join_Date']:%m/%Y} عبر {info['Acquisition_Channel']} · "
                      f"القنوات: {channels} · العائلة المفضّلة: {fav} · المرتجعات: {orders['is_return'].mean():.0%} من البنود"))
        hist = orders.groupby(['Invoice_ID', 'Order_Date', 'Channel']).agg(items=('Quantity', 'sum'), net=('Net_Sales_EGP', 'sum'),
                                                                           discount=('Discount_Pct', 'mean')).reset_index().sort_values('Order_Date', ascending=False)
        hist['Order_Date'] = hist['Order_Date'].dt.date
        hist['Channel'] = hist['Channel'].map(u.ch_name)
        hist['discount'] = (hist['discount'] * 100).round(0).astype(int).astype(str) + '%'
        hist['net'] = hist['net'].round(0)
        u.table(hist.head(15).rename(columns={'Invoice_ID': t('Invoice', 'الفاتورة'), 'Order_Date': t('Date', 'التاريخ'), 'Channel': t('Channel', 'القناة'),
                                              'items': t('Items', 'القطع'), 'net': t('Net (EGP)', 'الصافي (جنيه)'), 'discount': t('Avg discount', 'متوسط الخصم')}))
