import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('📏 Size & Fit Intelligence', '📏 ذكاء المقاسات'),
         t('Size is #1 in returns, #1 in support questions and #1 in factory defects. Nobody asked — so we built it.',
           'المقاس هو السبب الأول للمرتجعات، والسؤال الأول لخدمة العملاء، والعيب الأول في المصنع. لم يطلبه أحد — فبنيناه.'),
         '15_app8_size_fit')

REASON_AR = {'Size / fit': 'المقاس', 'Fabric / stitching': 'القماش / الخياطة', 'Changed mind': 'غيّر رأيه', 'Color / appearance': 'اللون / الشكل',
             'Print issue': 'مشكلة طباعة', 'Delivery issue': 'مشكلة توصيل'}
TICKET_AR = {'Size guidance': 'استفسار عن المقاس', 'Order status': 'حالة الطلب', 'General product question': 'سؤال عام عن منتج',
             'Exchange request': 'طلب استبدال', 'Product quality': 'جودة المنتج', 'Wholesale inquiry': 'استفسار جملة',
             'Return request': 'طلب إرجاع', 'Payment': 'الدفع'}
rn = lambda x: REASON_AR.get(x, x) if u.is_ar() else x
tn = lambda x: TICKET_AR.get(x, x) if u.is_ar() else x

files = u.load()
s, cs, q = files['Sales_Transactions'], files['Customer_Service'].copy(), files['Quality']
b2c = s[s['Channel'] != 'Wholesale']
ret = s[s['is_return']]
size_t = cs[cs['Issue_Type'] == 'Size guidance']
rate = b2c.groupby('Channel')['is_size_return'].mean() * 100

c = st.columns(5)
u.kpi(c[0], t('Share of all refunds', 'حصته من كل المرتجعات'), f"{s.loc[s['is_size_return'], 'Refund_Value_EGP'].sum() / ret['Refund_Value_EGP'].sum():.0%}",
      help=t('Size / fit is the #1 return reason.', 'المقاس هو السبب الأول للإرجاع.'))
u.kpi(c[1], t('Online size-return rate', 'نسبة مرتجعات المقاس أونلاين'), f"{rate['Online']:.1f}%",
      t(f"{rate['Online'] / rate['Retail']:.1f}x the store", f"{rate['Online'] / rate['Retail']:.1f} ضعف المتجر"), inverse=True)
u.kpi(c[2], t('Tickets about size', 'تذاكر عن المقاس'), f"{len(size_t) / len(cs):.0%}",
      help=t('The #1 ticket type, the same share on every channel.', 'النوع الأول من التذاكر، وبنفس النسبة في كل القنوات.'))
u.kpi(c[3], t('Wait for a size answer', 'انتظار الرد عن المقاس'), f"{size_t['Resolution_Hours'].mean():.0f} {t('hours', 'ساعة')}", inverse=True)
u.kpi(c[4], t('#1 QC defect type', 'العيب الأول في الجودة'), t('Size', 'المقاس'),
      help=t('10,850 rejected units, 1.97M EGP — but only slightly above stitching.', '10,850 قطعة مرفوضة، 1.97 مليون جنيه — وأعلى بقليل فقط من عيوب الخياطة.'))

tab1, tab2, tab3 = st.tabs([t('🧠 Fit Assistant (prototype)', '🧠 مساعد المقاس (نموذج أولي)'), t('The evidence', 'الأدلة'), t('Business case', 'الجدوى الاقتصادية')])

with tab1:
    st.markdown(t('**What the customer sees on the product page or in WhatsApp:** 3 questions → the right size, with the reason.',
                  '**ما يراه العميل في صفحة المنتج أو على واتساب:** 3 أسئلة ← المقاس المناسب مع السبب.'))
    l, r = st.columns([2, 3])
    with l:
        audience = st.radio(t('Who is it for?', 'لمن؟'), ['Kids', 'Women'], horizontal=True,
                            format_func=lambda x: t(x, 'أطفال' if x == 'Kids' else 'سيدات'))
        if audience == 'Kids':
            age = st.slider(t('Child age (years)', 'عمر الطفل (سنوات)'), 2, 13, 7)
            height = st.slider(t('Height (cm)', 'الطول (سم)'), 90, 165, 125)
            weight = st.slider(t('Weight (kg)', 'الوزن (كجم)'), 12, 55, 24)
        else:
            age = None
            height = st.slider(t('Height (cm)', 'الطول (سم)'), 145, 185, 163)
            weight = st.slider(t('Weight (kg)', 'الوزن (كجم)'), 45, 110, 68)
        fit_ar = {'Snug': 'ضيّق', 'Regular': 'عادي', 'Loose': 'واسع'}
        fit = st.radio(t('Preferred fit', 'القَصّة المفضّلة'), ['Snug', 'Regular', 'Loose'], index=1, horizontal=True,
                       format_func=lambda x: t(x, fit_ar[x]))
    with r:
        size, reason = u.recommend_size(audience, height=height, weight=weight, age=age, fit=fit)
        direction = 'rtl' if u.is_ar() else 'ltr'
        st.markdown(f"<div dir='{direction}' style='border:2px solid {u.BLUE};border-radius:12px;padding:24px;text-align:center'>"
                    f"<div style='font-size:15px;color:{u.INK}'>{t('Recommended size', 'المقاس المقترح')}</div>"
                    f"<div style='font-size:64px;font-weight:700;color:{u.BLUE};line-height:1.1'>{size}</div>"
                    f"<div style='font-size:14px;color:{u.INK};margin-top:8px'>{reason}</div></div>", unsafe_allow_html=True)
        if audience == 'Kids' and age is not None:
            age_size = u.KIDS_CHART.iloc[int(np.clip(np.searchsorted([4.5, 6.5, 8.5, 10.5], age), 0, 4))]['size']
            if age_size != size:
                st.caption(t(f'Note: by age alone the size would be {age_size}. We trust height and weight first, because children grow at different speeds.',
                             f'ملاحظة: حسب العمر فقط سيكون المقاس {age_size}. نعتمد على الطول والوزن أولًا لأن الأطفال ينمون بسرعات مختلفة.'))
        st.markdown(t('**What we save with every recommendation** (this is the data the company does not have today):',
                      '**ما نحفظه مع كل اقتراح** (وهي بيانات لا تملكها الشركة اليوم):'))
        later = t('filled later', 'يُملأ لاحقًا')
        log = pd.DataFrame([{t('order_id', 'رقم الطلب'): 'INV-xxxxx', t('product', 'المنتج'): t('any product', 'أي منتج'),
                             t('audience', 'الفئة'): t(audience, 'أطفال' if audience == 'Kids' else 'سيدات'),
                             t('height', 'الطول'): height, t('weight', 'الوزن'): weight, t('fit', 'القَصّة'): t(fit, fit_ar[fit]),
                             t('recommended', 'المقترح'): size, t('returned?', 'تم إرجاعه؟'): later, t('too small / too big', 'صغير / كبير'): later}])
        u.table(log)
    with st.expander(t('Size chart used by the prototype (illustrative — replace with the official Leo Moda chart)',
                       'جدول المقاسات المستخدم في النموذج (توضيحي — يُستبدل بجدول Leo Moda الرسمي)')):
        a, b = st.columns(2)
        a.markdown(t('**Kids**', '**أطفال**'))
        u.table(u.KIDS_CHART.rename(columns={'size': t('Size', 'المقاس'), 'age': t('Age', 'العمر'), 'height_min': t('Height from (cm)', 'الطول من (سم)'),
                                             'height_max': t('Height to (cm)', 'الطول إلى (سم)'), 'weight_max': t('Max weight (kg)', 'أقصى وزن (كجم)')}))
        b.markdown(t('**Women**', '**سيدات**'))
        u.table(u.WOMEN_CHART.rename(columns={'size': t('Size', 'المقاس'), 'weight_min': t('Weight from (kg)', 'الوزن من (كجم)'),
                                              'weight_max': t('Weight to (kg)', 'الوزن إلى (كجم)'), 'bust_cm': t('Bust (cm)', 'محيط الصدر (سم)')}))
    st.caption(t('How it gets smarter: every recommendation is linked to the order. When an item comes back as "too small" or "too big", '
                 'that product\'s size rule is adjusted. After a few months the assistant knows which products run small.',
                 'كيف يتعلّم: كل اقتراح يُربط بالطلب. عندما ترجع قطعة لأنها "صغيرة" أو "كبيرة" تُعدَّل قاعدة المقاس لهذا المنتج. '
                 'وبعد بضعة أشهر يعرف المساعد أي المنتجات مقاسها أصغر من المعتاد.'))

with tab2:
    l, r = st.columns(2)
    with l:
        reasons = ret.groupby('Return_Reason')['Refund_Value_EGP'].sum().sort_values() / 1e6
        fig = go.Figure(go.Bar(y=[rn(x) for x in reasons.index], x=reasons.values, orientation='h',
                               marker_color=[u.ORANGE if i == 'Size / fit' else u.LIGHT_BLUE for i in reasons.index],
                               text=[f'{v:.2f}M' for v in reasons.values], textposition='outside'))
        fig.update_xaxes(title=t('Refunds over 3 years, EGP millions', 'المرتجعات خلال 3 سنوات، مليون جنيه'), range=[0, reasons.max() * 1.2])
        u.show(u.style(fig, t('Size / fit is the #1 return reason: 37% of all refunds', 'المقاس هو السبب الأول للإرجاع: 37% من كل المرتجعات')))
    with r:
        tr = b2c.pivot_table(index='FY', columns='Channel', values='is_size_return', aggfunc='mean') * 100
        share = b2c.groupby('FY')['Channel'].apply(lambda x: (x == 'Online').mean() * 100)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tr.index, y=tr['Online'], name=u.ch_name('Online'), mode='lines+markers', line=dict(color=u.ORANGE, width=3)))
        fig.add_trace(go.Scatter(x=tr.index, y=tr['Retail'], name=u.ch_name('Retail'), mode='lines+markers', line=dict(color=u.BLUE, width=3)))
        fig.update_yaxes(title=t('Lines returned for size / fit, %', 'البنود المرتجعة بسبب المقاس، %'), range=[0, 3.5])
        u.show(u.style(fig, t(f'Online returns 2x more for size — and online is now {share.iloc[-1]:.0f}% of B2C',
                              f'الأونلاين يرتجع بسبب المقاس ضعف المتجر — والأونلاين الآن {share.iloc[-1]:.0f}% من التجزئة'), legend=True))

    ch = s.groupby('Channel').agg(lines=('Invoice_ID', 'size'), size_lines=('is_size_return', 'sum'))
    ch['units'] = s[s['is_size_return']].groupby('Channel')['Quantity'].sum()
    ch['refund_M'] = s[s['is_size_return']].groupby('Channel')['Refund_Value_EGP'].sum() / 1e6
    ch['rate_%'] = ch['size_lines'] / ch['lines'] * 100
    st.markdown(t('**Two different problems:** online & store have a high *rate* (customers cannot try on); wholesale has a low rate but the biggest *money*, because one order is hundreds of pieces.',
                  '**مشكلتان مختلفتان:** الأونلاين والمتجر *نسبتهما* عالية (العميل لا يستطيع القياس)؛ والجملة نسبتها منخفضة لكن *قيمتها* الأكبر لأن الطلب الواحد مئات القطع.'))
    ch_tbl = ch[['rate_%', 'units', 'refund_M']].round(2).reset_index()
    ch_tbl['Channel'] = ch_tbl['Channel'].map(u.ch_name)
    u.table(ch_tbl.rename(columns={'Channel': t('Channel', 'القناة'), 'rate_%': t('Size-return rate %', 'نسبة مرتجعات المقاس %'),
                                   'units': t('Units returned for size', 'قطع مرتجعة بسبب المقاس'), 'refund_M': t('Refunds (M EGP)', 'المرتجعات (مليون جنيه)')}))

    l, r = st.columns(2)
    with l:
        bp = b2c.groupby('Product_ID').agg(lines=('is_size_return', 'size'), rate=('is_size_return', 'mean'))
        avg = b2c['is_size_return'].mean()
        noise = np.sqrt(avg * (1 - avg) / bp['lines'].mean())
        fig = go.Figure(go.Histogram(x=bp['rate'] * 100, nbinsx=15, marker_color=u.LIGHT_BLUE))
        fig.add_vline(x=avg * 100, line_color=u.BLUE, line_width=2)
        fig.update_xaxes(title=t('Size-return rate per product, %', 'نسبة مرتجعات المقاس لكل منتج، %'))
        fig.update_yaxes(title=t('Number of products', 'عدد المنتجات'))
        u.show(u.style(fig, t('No "bad product": all 59 sit close to the average', 'لا يوجد "منتج سيئ": المنتجات الـ 59 كلها قريبة من المتوسط')))
        st.caption(t(f"Spread between products {bp['rate'].std():.2%} vs {noise:.2%} expected from pure chance → "
                     'it is an information problem at purchase, not a pattern problem.',
                     f"التفاوت بين المنتجات {bp['rate'].std():.2%} مقابل {noise:.2%} متوقّع بالصدفة وحدها ← "
                     'إنها مشكلة معلومات وقت الشراء، وليست مشكلة باترون.'))
    with r:
        tk = cs['Issue_Type'].value_counts().sort_values()
        fig = go.Figure(go.Bar(y=[tn(x) for x in tk.index], x=tk.values, orientation='h',
                               marker_color=[u.ORANGE if i == 'Size guidance' else u.LIGHT_BLUE for i in tk.index],
                               text=[f'{v:,}' for v in tk.values], textposition='outside'))
        fig.update_xaxes(title=t('Support tickets (3 years)', 'تذاكر خدمة العملاء (3 سنوات)'), range=[0, tk.max() * 1.2])
        u.show(u.style(fig, t('"Which size?" is the #1 customer question', '"أي مقاس؟" هو السؤال الأول للعملاء')))

    pm = files['Product_Master'][['Product_ID', 'Audience']]
    sc = s.merge(pm, on='Product_ID', how='left')
    curve = pd.crosstab(sc['Audience'], sc['Size'], values=sc['Quantity'], aggfunc='sum', normalize='index') * 100
    curve = curve[[k for k in ['4', '6', '8', '10', '12', 'M', 'L', 'XL', '2XL'] if k in curve.columns]].round(1)
    st.markdown(t('**Size curve** (share of units sold per size) — use it to split production and to build size packs for wholesale traders:',
                  '**منحنى المقاسات** (نسبة القطع المباعة لكل مقاس) — يُستخدم لتقسيم الإنتاج وتجهيز باكدجات المقاسات لتجار الجملة:'))
    curve_tbl = curve.reset_index()
    curve_tbl['Audience'] = curve_tbl['Audience'].map(lambda x: t(x, 'أطفال' if x == 'Kids' else 'سيدات'))
    u.table(curve_tbl.rename(columns={'Audience': t('Audience', 'الفئة')}))

with tab3:
    fy26 = s[s['FY'] == 'FY2026']
    b26, w26 = fy26[fy26['Channel'] != 'Wholesale'], fy26[fy26['Channel'] == 'Wholesale']
    a, b = st.columns(2)
    cut_b2c = a.slider(t('Fit assistant cuts online + store size returns by (%)', 'مساعد المقاس يخفض مرتجعات المقاس في الأونلاين والمتجر بنسبة (%)'),
                       0, 60, 30, step=5) / 100
    cut_wh = b.slider(t('Size packs cut wholesale size returns by (%)', 'باكدجات المقاسات تخفض مرتجعات مقاس الجملة بنسبة (%)'), 0, 60, 20, step=5) / 100
    c_act, c_ref, c_cut, c_mar = t('Action', 'الإجراء'), t('Size refunds FY26 (M)', 'مرتجعات المقاس FY26 (مليون)'), t('Assumed cut', 'التخفيض المفترض'), t('Margin', 'الهامش')
    c_av, c_pi = t('Refunds avoided (M)', 'مرتجعات تم تجنّبها (مليون)'), t('Profit impact (M)', 'الأثر على الربح (مليون)')
    rows = pd.DataFrame([
        [t('Fit assistant (web + WhatsApp)', 'مساعد المقاس (الموقع + واتساب)'), b26.loc[b26['is_size_return'], 'Refund_Value_EGP'].sum() / 1e6, cut_b2c,
         b26['Gross_Profit_EGP'].sum() / b26['Net_Sales_EGP'].sum()],
        [t('Size-curve packs for wholesale', 'باكدجات مقاسات لتجار الجملة'), w26.loc[w26['is_size_return'], 'Refund_Value_EGP'].sum() / 1e6, cut_wh,
         w26['Gross_Profit_EGP'].sum() / w26['Net_Sales_EGP'].sum()],
    ], columns=[c_act, c_ref, c_cut, c_mar])
    rows[c_av] = rows[c_ref] * rows[c_cut]
    rows[c_pi] = rows[c_av] * rows[c_mar]
    k = st.columns(3)
    u.kpi(k[0], t('Refunds avoided / year', 'مرتجعات تم تجنّبها / سنة'), f"{rows[c_av].sum():.2f}M EGP")
    u.kpi(k[1], t('Gross-profit impact / year', 'الأثر على إجمالي الربح / سنة'), f"{rows[c_pi].sum():.2f}M EGP")
    u.kpi(k[2], t('Size questions answered instantly', 'أسئلة مقاس تُجاب فورًا'), t(f"~{len(size_t) // 3:,} / year", f"~{len(size_t) // 3:,} / سنة"))
    u.table(rows.round(3))
    st.warning(t('**Honest framing:** the direct money is modest. The real value is (1) protecting online, the channel growing 26% a year '
                 'with 2x the size returns, (2) answering customers in seconds instead of 18 hours, and (3) building size data the company does not have.',
                 '**بصراحة:** العائد المالي المباشر محدود. القيمة الحقيقية هي (1) حماية الأونلاين، القناة التي تنمو 26% سنويًا '
                 'ومرتجعات المقاس فيها الضعف، (2) الرد على العملاء في ثوانٍ بدل 18 ساعة، و(3) بناء بيانات مقاسات لا تملكها الشركة.'), icon='🧭')
    st.markdown(t('**How we prove it — A/B test for 3 months:** half of website visitors see the Fit Assistant, half do not. '
                  'Compare size-return rates. Targets: online size returns 2.8% → 2.0%, size tickets −50%, answer time 18 h → seconds.',
                  '**كيف نثبت ذلك — تجربة A/B لمدة 3 أشهر:** نصف زوار الموقع يرون مساعد المقاس والنصف الآخر لا. '
                  'نقارن نسبة مرتجعات المقاس. الأهداف: مرتجعات المقاس أونلاين 2.8% ← 2.0%، تذاكر المقاس −50%، زمن الرد 18 ساعة ← ثوانٍ.'))
