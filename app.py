"""
El-Sharnouby Group — BI & AI dashboard.
Run it from inside the dashboard folder:
    cd dashboard
    streamlit run app.py
This file only builds the menu and the language switch. Each page lives in views/.
"""
import streamlit as st
import utils as u

st.set_page_config(page_title='El-Sharnouby BI & AI', page_icon='📊', layout='wide')

# language switch: the choice is saved in st.session_state['lang'] and every page reads it through u.t()
with st.sidebar:
    st.radio('Language / اللغة', ['English', u.AR], key='lang', horizontal=True)
t = u.t

pages = {
    t('Overview', 'نظرة عامة'): [
        st.Page('views/exec_center.py', title=t('1 · Executive Command Center', '1 · مركز القيادة التنفيذي'), icon='🎯', default=True),
    ],
    t('Apps', 'التطبيقات'): [
        st.Page('views/inventory.py', title=t('2 · Smart Inventory & Replenishment', '2 · المخزون الذكي وإعادة الطلب'), icon='📦'),
        st.Page('views/customers.py', title=t('3 · Customer 360 & Retention', '3 · العميل 360 والاحتفاظ'), icon='👥'),
        st.Page('views/factory.py', title=t('4 · Factory Digital Twin', '4 · التوأم الرقمي للمصنع'), icon='🏭'),
        st.Page('views/marketing.py', title=t('5 · Marketing Attribution & Growth', '5 · قياس أثر التسويق والنمو'), icon='📣'),
        st.Page('views/branches.py', title=t('6 · Branch Intelligence & Expansion', '6 · ذكاء الفروع والتوسع'), icon='🗺️'),
        st.Page('views/procurement.py', title=t('7 · Procurement & Supplier Risk', '7 · المشتريات ومخاطر الموردين'), icon='🚚'),
    ],
    t('Built without being asked', 'بنيناه دون أن يُطلب'): [
        st.Page('views/size_fit.py', title=t('8 · Size & Fit Intelligence', '8 · ذكاء المقاسات'), icon='📏'),
    ],
}

nav = st.navigation(pages)
with st.sidebar:
    st.caption('El-Sharnouby Group · LEO MODA')
    st.caption(t('Data: Oct 2023 – Sep 2026 · Fiscal year Oct–Sep', 'البيانات: أكتوبر 2023 – سبتمبر 2026 · السنة المالية أكتوبر–سبتمبر'))
    st.caption(t('Built by Shahd Ibrahim · HVIA Task 02', 'إعداد: شهد إبراهيم · HVIA Task 02'))
nav.run()
