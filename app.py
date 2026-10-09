"""
El-Sharnouby Group — BI & AI dashboard.
Run it from inside the dashboard folder:
    cd dashboard
    streamlit run app.py
This file only builds the menu. Each page lives in views/.
"""
import streamlit as st

st.set_page_config(page_title='El-Sharnouby BI & AI', page_icon='📊', layout='wide')

pages = {
    'Overview': [
        st.Page('views/exec_center.py', title='1 · Executive Command Center', icon='🎯', default=True),
    ],
    'Apps': [
        st.Page('views/inventory.py', title='2 · Smart Inventory & Replenishment', icon='📦'),
        st.Page('views/customers.py', title='3 · Customer 360 & Retention', icon='👥'),
        st.Page('views/factory.py', title='4 · Factory Digital Twin', icon='🏭'),
        st.Page('views/marketing.py', title='5 · Marketing Attribution & Growth', icon='📣'),
        st.Page('views/branches.py', title='6 · Branch Intelligence & Expansion', icon='🗺️'),
        st.Page('views/procurement.py', title='7 · Procurement & Supplier Risk', icon='🚚'),
    ],
    'Built without being asked': [
        st.Page('views/size_fit.py', title='8 · Size & Fit Intelligence', icon='📏'),
    ],
}

nav = st.navigation(pages)
with st.sidebar:
    st.caption('El-Sharnouby Group · LEO MODA')
    st.caption('Data: Oct 2023 – Sep 2026 · Fiscal year Oct–Sep')
    st.caption('Built by Shahd Ibrahim · HVIA Task 02')
nav.run()
