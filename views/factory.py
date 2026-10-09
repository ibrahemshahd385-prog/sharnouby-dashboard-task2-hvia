import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

u.header('🏭 Factory Digital Twin & Production Control',
         'Where does production get stuck, what does poor quality cost, and what happens if we fix it?',
         '09_card06_factory · 10_card07_quality · 11_card08_printing')

files = u.load()
po = u.production()
late = po[po['late']]

c = st.columns(5)
u.kpi(c[0], 'Plan attainment', f"{po['Produced_Qty'].sum() / po['Planned_Qty'].sum():.1%}", help='Produced ÷ planned quantity.')
u.kpi(c[1], 'Orders on time', f"{1 - po['late'].mean():.1%}")
u.kpi(c[2], 'Average delay (late orders)', f"{late['Delay_Days'].mean():.1f} days", inverse=True)
u.kpi(c[3], 'Production reject rate', f"{po['Rejected_Qty'].sum() / po['Produced_Qty'].sum():.2%}", inverse=True)
u.kpi(c[4], 'Overtime hours', f"{po['Overtime_Hours'].sum():,.0f}", inverse=True)

tab1, tab2, tab3, tab4 = st.tabs(['Production', 'Digital twin: what-if', 'Quality & COPQ', 'Printing & machines'])

with tab1:
    l, r = st.columns(2)
    with l:
        q = po.groupby('quarter')['late'].mean() * 100
        colors = [u.ORANGE if v > 25 else u.BLUE for v in q.values]
        fig = go.Figure(go.Bar(x=q.index, y=q.values, marker_color=colors, text=[f'{v:.0f}%' for v in q.values], textposition='outside'))
        fig.update_yaxes(title='% of orders late', range=[0, q.max() * 1.2])
        u.show(u.style(fig, 'Two crises: 46% late in Q2-2025, 34% in Q1-2026'))
    with r:
        st_ = late.groupby('Primary_Bottleneck')['Delay_Days'].sum().sort_values(ascending=False)
        share = st_ / st_.sum() * 100
        fig = go.Figure(go.Bar(x=st_.index, y=share.values, marker_color=[u.ORANGE, u.ORANGE] + [u.LIGHT_BLUE] * (len(st_) - 2),
                               text=[f'{v:.0f}%' for v in share.values], textposition='outside'))
        fig.update_yaxes(title='% of all delay days', range=[0, share.max() * 1.2])
        u.show(u.style(fig, f'Sewing + finishing = {share.iloc[:2].sum():.0f}% of all delay days'))
    ot = po.groupby('late')['Overtime_Hours'].mean()
    st.caption(f"Late orders burn {ot.loc[True]:.1f} overtime hours on average vs {ot.loc[False]:.1f} for on-time orders — "
               "overtime is a symptom of the bottleneck, not a cure.")
    lines = po.groupby('Line_ID').agg(orders=('Production_Order_ID', 'size'), on_time=('late', lambda x: (1 - x.mean()) * 100),
                                      efficiency=('Efficiency_Pct', 'mean'), overtime=('Overtime_Hours', 'sum')).round(1).reset_index()
    u.table(lines.rename(columns={'Line_ID': 'Line', 'orders': 'Orders', 'on_time': 'On time %', 'efficiency': 'Avg efficiency %', 'overtime': 'Overtime h'}))

with tab2:
    st.markdown('**What if we fix part of the late orders caused by each stage?** Move the sliders and watch on-time delivery change.')
    stages = late['Primary_Bottleneck'].value_counts()
    cols = st.columns(len(stages))
    fixed = 0
    for col, (stage, n) in zip(cols, stages.items()):
        default = 50 if stage in ('Sewing', 'Finishing') else 0
        pct = col.slider(f'{stage} ({n} late orders)', 0, 100, default, step=10, key=f'fix_{stage}')
        fixed += n * pct / 100
    now = 1 - po['late'].mean()
    new = (len(po) - len(late) + fixed) / len(po)
    k = st.columns(3)
    u.kpi(k[0], 'On time today', f'{now:.1%}')
    u.kpi(k[1], 'On time after fixes', f'{new:.1%}', f'{(new - now) * 100:+.1f} pts')
    u.kpi(k[2], 'Late orders avoided', f'{fixed:.0f}')
    fig = go.Figure(go.Bar(x=['Today', 'After fixes'], y=[now * 100, new * 100], marker_color=[u.GREY, u.AQUA],
                           text=[f'{now:.1%}', f'{new:.1%}'], textposition='outside'))
    fig.update_yaxes(title='% of orders on time', range=[0, 105])
    u.show(u.style(fig, 'Fixing half the sewing & finishing delays → ~89% on time', height=340))
    st.caption('How fixes happen: a second shift or one extra line at sewing in the peak months, SMED (faster changeovers) at finishing, '
               'and starting peak-season orders earlier. A full digital twin would simulate every line hour by hour — this is the "lite" version.')

with tab3:
    copq = u.copq_by_fy()
    gp = u.fy_summary()['gross_profit'] / 1e6
    l, r = st.columns(2)
    with l:
        fig = go.Figure()
        palette = [u.BLUE, u.ORANGE, u.AQUA, u.GREY]
        for col, colr in zip(copq.columns[:-1], palette):
            fig.add_trace(go.Bar(x=copq.index, y=copq[col], name=col, marker_color=colr))
        fig.update_layout(barmode='stack')
        for fy_, tot in copq['total'].items():
            fig.add_annotation(x=fy_, y=tot, text=f'<b>{tot:.2f}M</b>', showarrow=False, yshift=12)
        fig.update_yaxes(title='EGP millions', range=[0, copq['total'].max() * 1.2])
        u.show(u.style(fig, f"Poor quality costs {copq['total'].sum():.1f}M = {copq['total'].sum() / gp.sum():.0%} of gross profit", legend=True, height=420))
    with r:
        qc = files['Quality'].dropna(subset=['Defect_Type']).groupby('Defect_Type')['Rejected_Qty'].sum().sort_values()
        fig = go.Figure(go.Bar(y=qc.index, x=qc.values, orientation='h', marker_color=[u.ORANGE if i == 'Size Variance' else u.LIGHT_BLUE for i in qc.index],
                               text=[f'{v:,.0f}' for v in qc.values], textposition='outside'))
        fig.update_xaxes(title='Rejected units (QC)', range=[0, qc.max() * 1.2])
        u.show(u.style(fig, 'No single defect dominates — the top 3 are only 40%', height=420))
    st.caption('COPQ is counted conservatively: QC scrap loss + refunds for quality returns + print rework + reprint ink. No double counting.')

with tab4:
    mc = u.printing_machines()
    st.markdown('**Which printing machine to fix first?** Rank on reject rate + unplanned downtime hours + unplanned stops (1 = worst).')
    show_mc = mc[['fix_order', 'Machine_ID', 'reject_rate_%', 'unplanned_hours', 'unplanned_events', 'priority_score']].round(2)
    u.table(show_mc.rename(columns={'fix_order': 'Fix order', 'Machine_ID': 'Machine', 'reject_rate_%': 'Reject %',
                                    'unplanned_hours': 'Unplanned downtime h', 'unplanned_events': 'Unplanned stops', 'priority_score': 'Score (lower = worse)'}))
    dt = files['Machine_Downtime'].copy()
    dt['FY'] = u.fiscal_year(dt['Date'])
    l, r = st.columns(2)
    with l:
        a = dt.pivot_table(index='Business_Area', columns='Planned', values='Downtime_Hours', aggfunc='sum').fillna(0)
        a = a.loc[a.sum(axis=1).sort_values().index]
        fig = go.Figure()
        fig.add_trace(go.Bar(y=a.index, x=a.get('No', 0), name='Unplanned', orientation='h', marker_color=u.ORANGE))
        fig.add_trace(go.Bar(y=a.index, x=a.get('Yes', 0), name='Planned', orientation='h', marker_color=u.LIGHT_BLUE))
        fig.update_layout(barmode='stack')
        fig.update_xaxes(title='Downtime hours (3 years)')
        unpl = dt.loc[dt['Planned'] == 'No', 'Downtime_Hours'].sum() / dt['Downtime_Hours'].sum()
        u.show(u.style(fig, f'{unpl:.0%} of downtime is unplanned — printing is the biggest area', legend=True))
    with r:
        rs = dt.groupby('Reason')['Downtime_Hours'].sum().sort_values()
        fig = go.Figure(go.Bar(y=rs.index, x=rs.values, orientation='h', marker_color=u.GREY, text=[f'{v:,.0f} h' for v in rs.values], textposition='outside'))
        fig.update_xaxes(title='Downtime hours (3 years)', range=[0, rs.max() * 1.25])
        u.show(u.style(fig, 'Mechanical faults lead — preventive maintenance pays'))
    pb = files['Printing_Batches']
    st.caption(f"Printing yield {pb['Good_Qty'].sum() / pb['Printed_Qty'].sum():.2%}. Material-wait downtime by year: "
               + ', '.join(f'{k} {v:.0f} h' for k, v in dt[dt['Reason'] == 'Material wait'].groupby('FY')['Downtime_Hours'].sum().items())
               + ' → links to supplier delays (page 7).')
