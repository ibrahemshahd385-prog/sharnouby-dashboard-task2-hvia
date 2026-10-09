"""
Shared code for every dashboard page:
  1) load the clean data once (cached)
  2) colors + chart style
  3) the calculations from the notebooks (cards 01-10 + App 8)
Every page imports from here, so a number is calculated in ONE place only.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- colors
BLUE, ORANGE, AQUA, INK = '#2a78d6', '#eb6834', '#1baf7a', '#52514e'
LIGHT_BLUE, GREY, RED = '#b9d3f2', '#9b9a96', '#d03b3b'
CHANNEL_COLORS = {'Online': ORANGE, 'Retail': BLUE, 'Store': BLUE, 'Wholesale': AQUA}
LOC = {'LOC001': 'Store', 'LOC002': 'Online', 'LOC003': 'Wholesale'}


# ---------------------------------------------------------------- language (English / العربية)
AR = 'العربية'


def is_ar():
    return st.session_state.get('lang', 'English') == AR


def t(en, ar):
    """Return the Arabic text when the user picked Arabic, else the English text."""
    return ar if is_ar() else en


CHANNEL_AR = {'Online': 'أونلاين', 'Retail': 'المتجر', 'Store': 'المتجر', 'Wholesale': 'الجملة'}
SEGMENT_AR = {'Champions': 'الأبطال', 'Loyal': 'الأوفياء', 'New / Promising': 'جدد / واعدون',
              "At Risk (Can't Lose)": 'معرّضون للخسارة (لا يمكن خسارتهم)', 'At Risk': 'معرّضون للخسارة',
              'Need Attention': 'يحتاجون اهتمامًا', 'Lost': 'مفقودون'}


def ch_name(x):
    """Channel name for display: 'Retail' is shown as 'Store'."""
    return CHANNEL_AR.get(x, x) if is_ar() else ('Store' if x == 'Retail' else x)


def seg_name(x):
    return SEGMENT_AR.get(x, x) if is_ar() else x


def apply_language_style():
    """Arabic: right-to-left text and an Arabic font. Charts and sliders keep their normal direction."""
    if not is_ar():
        return
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap');
h1, h2, h3, p, li, label, [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stWidgetLabel"], [data-testid="stSidebarNav"] a span {
    font-family: 'IBM Plex Sans Arabic', 'Segoe UI', sans-serif;
}
h1, h2, h3, [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], [data-testid="stMetricLabel"],
[data-testid="stWidgetLabel"], [data-testid="stAlert"], [data-testid="stExpander"] summary {
    direction: rtl; text-align: right;
}
[data-testid="stSidebarNav"], [data-testid="stSidebarUserContent"] { direction: rtl; text-align: right; }
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------- data
def _find_data_file():
    here = Path(__file__).resolve().parent
    for p in [here / 'data' / 'files_clean.pkl.gz', here / 'data' / 'files_clean.pkl', here.parent / 'clean' / 'files_clean.pkl']:
        if p.exists():
            return p
    st.error('Could not find the data. Put files_clean.pkl.gz in dashboard/data/ or keep clean/files_clean.pkl next to the dashboard folder.')
    st.stop()


@st.cache_resource(show_spinner='Loading data...')
def load():
    files = pd.read_pickle(_find_data_file())
    s = files['Sales_Transactions']
    s['is_return'] = s['Returned'] == 'Yes'
    s['is_size_return'] = s['Return_Reason'] == 'Size / fit'
    return files


def fiscal_year(dates):
    return 'FY' + (dates.dt.year + (dates.dt.month >= 10).astype(int)).astype(str)


# ---------------------------------------------------------------- chart helpers
def style(fig, title, height=380, legend=False):
    """Same look as the notebook charts: title = the insight, light grid, no clutter."""
    fig.update_layout(
        title=dict(text=f'<b>{title}</b>', x=1 if is_ar() else 0, xanchor='right' if is_ar() else 'left',
                   y=0.98, yanchor='top', yref='container',
                   font=dict(size=16, color='#0b0b0b')),
        height=height, margin=dict(l=70, r=20, t=88 if legend else 60, b=10),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(family='IBM Plex Sans Arabic, Inter, Segoe UI, sans-serif', size=13, color=INK),
        showlegend=legend,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
        hoverlabel=dict(bgcolor='white'),
    )
    fig.update_xaxes(showgrid=False, linecolor='#d6d5d0', ticks='')
    fig.update_yaxes(gridcolor='#ecebe7', zeroline=False, linecolor='#d6d5d0')
    return fig


def show(fig):
    """Draw a plotly chart full-width (works on old and new Streamlit versions)."""
    try:
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def table(df, **kwargs):
    try:
        st.dataframe(df, width='stretch', hide_index=True, **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True, **kwargs)


def kpi(col, label, value, delta=None, inverse=False, help=None):
    """One KPI card. inverse=True means 'going up is bad' (shown in red)."""
    value = str(value)
    if value.endswith(' EGP'):          # keep the card short: "148.3M" and put the unit in the label
        value, label = value[:-4], f"{label} ({t('EGP', 'جنيه')})"
    kw = dict(delta=delta, delta_color='inverse' if inverse else 'normal', help=help)
    try:
        col.metric(label, value, border=True, **kw)
    except TypeError:
        col.metric(label, value, **kw)


def header(title, question, source):
    apply_language_style()
    st.title(title)
    st.markdown(f"**{t('Business question:', 'سؤال العمل:')}** {question}")
    # \u2066 ... \u2069 keep the file names left-to-right inside Arabic text
    st.caption(f"{t('Source notebooks:', 'النوت بوكس المصدر:')} \u2066{source}\u2069")


def insight(text):
    st.info(text, icon='💡')


def money(x, unit='M'):
    return f'{x:,.1f}{unit} EGP'


# ================================================================ CARD 01 / 03 — sales
@st.cache_data
def fy_summary():
    s = load()['Sales_Transactions']
    g = s.groupby('FY').agg(net_sales=('Net_Sales_EGP', 'sum'), gross_profit=('Gross_Profit_EGP', 'sum'),
                            gross_sales=('Gross_Sales_EGP', 'sum'), units=('Quantity', 'sum'))
    g['discount'] = g['gross_sales'] - g['net_sales']
    g['margin'] = g['gross_profit'] / g['net_sales']
    g['growth'] = g['net_sales'].pct_change()
    return g


@st.cache_data
def monthly_sales():
    s = load()['Sales_Transactions']
    return s.groupby('Month').agg(net_sales=('Net_Sales_EGP', 'sum'), gross_profit=('Gross_Profit_EGP', 'sum')).reset_index()


@st.cache_data
def channel_fy():
    s = load()['Sales_Transactions']
    g = s.groupby(['FY', 'Channel']).agg(net_sales=('Net_Sales_EGP', 'sum'), gross_profit=('Gross_Profit_EGP', 'sum'),
                                          lines=('Invoice_ID', 'size'), returns=('is_return', 'sum')).reset_index()
    g['margin'] = g['gross_profit'] / g['net_sales']
    g['return_rate'] = g['returns'] / g['lines']
    return g


@st.cache_data
def discount_bands():
    s = load()['Sales_Transactions']
    band = pd.cut(s['Discount_Pct'], [-0.01, 0, 0.10, 0.20, 0.30, 1], labels=['0%', '5-10%', '15-20%', '25-30%', '32-38%'])
    g = s.groupby(band, observed=True).agg(net=('Net_Sales_EGP', 'sum'), gp=('Gross_Profit_EGP', 'sum'))
    g['margin'] = g['gp'] / g['net']
    return g.reset_index().rename(columns={'Discount_Pct': 'band'})


# ================================================================ CARD 02 — customers
SEGMENT_ORDER = ['Champions', 'Loyal', 'New / Promising', "At Risk (Can't Lose)", 'At Risk', 'Need Attention', 'Lost']


@st.cache_data
def rfm():
    s = load()['Sales_Transactions']
    r = s[s['Customer_Type'] == 'Retail']
    snapshot = r['Order_Date'].max() + pd.Timedelta(days=1)
    t = r.groupby('Customer_ID').agg(recency=('Order_Date', lambda x: (snapshot - x.max()).days),
                                     frequency=('Invoice_ID', 'nunique'), monetary=('Net_Sales_EGP', 'sum'),
                                     last_order=('Order_Date', 'max'), first_order=('Order_Date', 'min'),
                                     channels=('Channel', 'nunique'))
    t['R'] = pd.qcut(t['recency'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    t['F'] = pd.qcut(t['frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    t['M'] = pd.qcut(t['monetary'], 5, labels=[1, 2, 3, 4, 5]).astype(int)
    t['segment'] = np.select(
        [(t['R'] >= 4) & (t['F'] >= 4), (t['R'] >= 3) & (t['F'] >= 3), (t['R'] >= 4) & (t['F'] <= 2),
         (t['R'] <= 2) & (t['F'] >= 4), (t['R'] <= 2) & (t['F'] >= 2), t['R'] == 3],
        SEGMENT_ORDER[:6], default='Lost')
    return t


@st.cache_data
def cohort_table():
    s, c = load()['Sales_Transactions'], load()['Customers']
    r = s[s['Customer_Type'] == 'Retail'][['Customer_ID', 'Order_Date']].copy()
    cust = c[c['Customer_Type'] == 'Retail'][['Customer_ID', 'Join_Date']]
    r = r.merge(cust, on='Customer_ID')
    r['cohort'] = r['Join_Date'].dt.to_period('Q')
    r['k'] = (r['Order_Date'].dt.to_period('Q') - r['cohort']).apply(lambda x: x.n)
    r = r[r['k'] >= 0]
    size = cust.assign(cohort=cust['Join_Date'].dt.to_period('Q')).groupby('cohort').size()
    active = r.groupby(['cohort', 'k'])['Customer_ID'].nunique().unstack()
    ret = active.div(size, axis=0) * 100
    ret = ret[ret.index >= pd.Period('2023Q4')]
    ret.index = ret.index.astype(str)
    return ret


# ================================================================ CARD 04 — inventory + AI forecast
@st.cache_data
def inventory():
    files = load()
    s, inv = files['Sales_Transactions'], files['Inventory_History'].copy()
    unit_cost = (s.groupby('Product_ID')['Estimated_COGS_EGP'].sum() / s.groupby('Product_ID')['Quantity'].sum()).rename('unit_cost')
    inv = inv.merge(unit_cost, on='Product_ID')
    inv['FY'] = fiscal_year(inv['Snapshot_Month'])
    inv['Location'] = inv['Location_ID'].map(LOC)
    inv['unmet_units'] = (inv['Sold_Qty'] - (inv['Opening_Stock'] + inv['Received_Qty'] + inv['Returned_Qty'] - inv['Damaged_Qty'])).clip(lower=0)
    return inv


@st.cache_data
def inventory_snapshot():
    inv = inventory()
    last = inv[inv['Snapshot_Month'] == inv['Snapshot_Month'].max()].copy()
    last['needed_90d'] = last['Avg_Daily_Sales_90D'] * 90 + last['Safety_Stock_Units']
    last['excess_units'] = (last['Closing_Stock'] - last['needed_90d']).clip(lower=0)
    last['stock_value'] = last['Closing_Stock'] * last['unit_cost']
    last['excess_value'] = last['excess_units'] * last['unit_cost']
    last['below_reorder_point'] = last['Closing_Stock'] < last['Reorder_Point_Units']
    return last


@st.cache_data
def stock_turns(fy='FY2026'):
    inv = inventory()
    f = inv[inv['FY'] == fy].copy()
    f['cogs'] = f['Sold_Qty'] * f['unit_cost']
    f['stock_val'] = f['Closing_Stock'] * f['unit_cost']
    cogs = f.groupby('Location')['cogs'].sum()
    avg_stock = f.groupby(['Location', 'Snapshot_Month'])['stock_val'].sum().groupby('Location').mean()
    out = pd.DataFrame({'turns': cogs / avg_stock})
    out['days_of_stock'] = 365 / out['turns']
    return out.reset_index()


@st.cache_data
def abc_xyz():
    s, inv = load()['Sales_Transactions'], inventory()
    rev = s.groupby('Product_ID')['Net_Sales_EGP'].sum().sort_values(ascending=False)
    cum = rev.cumsum() / rev.sum()
    abc = pd.cut(cum, [0, 0.80, 0.95, 1.0001], labels=['A', 'B', 'C']).rename('ABC')
    mu = inv.groupby(['Product_ID', 'Snapshot_Month'])['Sold_Qty'].sum().unstack()
    cv = (mu.std(axis=1) / mu.mean(axis=1)).rename('CV')
    xyz = pd.cut(cv, [0, 0.5, 1.0, 99], labels=['X', 'Y', 'Z']).rename('XYZ')
    return pd.concat([abc, xyz, cv], axis=1)


FEATURES = ['lag1', 'lag2', 'lag3', 'lag12', 'avg_last3', 'month_num', 'Location_ID_code', 'Product_Family_code', 'Catalog_Season_code']


def _demand_table():
    inv, pm = inventory(), load()['Product_Master']
    d = inv[['Snapshot_Month', 'Location_ID', 'Product_ID', 'Sold_Qty']].merge(pm[['Product_ID', 'Product_Family', 'Catalog_Season']], on='Product_ID')
    d = d.sort_values(['Location_ID', 'Product_ID', 'Snapshot_Month']).rename(columns={'Snapshot_Month': 'month'})
    for col in ['Location_ID', 'Product_Family', 'Catalog_Season']:
        d[col + '_code'] = d[col].astype('category').cat.codes
    return d


def _add_features(table):
    t = table.sort_values(['Location_ID', 'Product_ID', 'month']).copy()
    g = t.groupby(['Location_ID', 'Product_ID'])['Sold_Qty']
    for k in [1, 2, 3, 12]:
        t[f'lag{k}'] = g.shift(k)
    t['avg_last3'] = t[['lag1', 'lag2', 'lag3']].mean(axis=1)
    t['month_num'] = t['month'].dt.month
    return t


def _forecast(history, months_ahead):
    from sklearn.ensemble import HistGradientBoostingRegressor
    hist = history.copy()
    model_data = _add_features(hist).dropna(subset=['lag12'])
    model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
    model.fit(model_data[FEATURES], np.log1p(model_data['Sold_Qty']))
    results = []
    for m in months_ahead:
        new_rows = hist[hist['month'] == hist['month'].max()].copy()
        new_rows['month'] = m
        new_rows['Sold_Qty'] = np.nan
        tmp = _add_features(pd.concat([hist, new_rows]))
        rows = tmp[tmp['month'] == m].copy()
        rows['forecast'] = np.expm1(model.predict(rows[FEATURES])).clip(0).round()
        results.append(rows)
        hist = pd.concat([hist, rows.assign(Sold_Qty=rows['forecast'])[hist.columns]])
    return pd.concat(results)


@st.cache_data(show_spinner='Training the AI forecast model...')
def forecast_results():
    """Backtest (Jul-Sep 2026) + future forecast (Oct-Dec 2026). Same model as notebook 07."""
    d = _demand_table()
    test_months = pd.to_datetime(['2026-07-01', '2026-08-01', '2026-09-01'])
    bt = _forecast(d[d['month'] < test_months[0]], test_months)
    bt = bt[['month', 'Location_ID', 'Product_ID', 'forecast']].merge(d[['month', 'Location_ID', 'Product_ID', 'Sold_Qty']], on=['month', 'Location_ID', 'Product_ID'])
    ly = d[['month', 'Location_ID', 'Product_ID', 'Sold_Qty']].copy()
    ly['month'] = ly['month'] + pd.DateOffset(years=1)
    bt = bt.merge(ly.rename(columns={'Sold_Qty': 'naive_last_year'}), on=['month', 'Location_ID', 'Product_ID'])
    wape = lambda a, p: (a - p).abs().sum() / a.sum() * 100
    errors = {'ai': wape(bt['Sold_Qty'], bt['forecast']), 'naive': wape(bt['Sold_Qty'], bt['naive_last_year'])}
    future = _forecast(d, pd.to_datetime(['2026-10-01', '2026-11-01', '2026-12-01']))
    future = future[['month', 'Location_ID', 'Product_ID', 'forecast']]
    std_daily = d.groupby(['Location_ID', 'Product_ID'])['Sold_Qty'].apply(lambda x: x.tail(12).std() / np.sqrt(30)).rename('std_daily').reset_index()
    history = d[['month', 'Location_ID', 'Product_ID', 'Sold_Qty']]
    return errors, future, std_daily, history


SERVICE_LEVEL_Z = {'90%': 1.28, '95%': 1.65, '98%': 2.05, '99%': 2.33}


@st.cache_data
def replenishment_plan(z=1.65):
    _, future, std_daily, _ = forecast_results()
    last = inventory_snapshot()
    w = future.pivot_table(index=['Location_ID', 'Product_ID'], columns='month', values='forecast')
    w.columns = ['Oct', 'Nov', 'Dec']
    w['forecast_30d'] = w['Oct']
    w['forecast_90d'] = w[['Oct', 'Nov', 'Dec']].sum(axis=1)
    w = w.reset_index()
    plan = last[['Location_ID', 'Location', 'Product_ID', 'Product_Name', 'Closing_Stock', 'Supplier_Lead_Time_Days', 'unit_cost']].merge(w, on=['Location_ID', 'Product_ID'])
    plan = plan.merge(std_daily, on=['Location_ID', 'Product_ID'])
    plan['daily_demand'] = plan['forecast_30d'] / 30
    plan['safety_stock'] = (z * plan['std_daily'] * np.sqrt(plan['Supplier_Lead_Time_Days'])).round()
    plan['reorder_point'] = (plan['daily_demand'] * plan['Supplier_Lead_Time_Days'] + plan['safety_stock']).round()
    plan['order_up_to'] = (plan['daily_demand'] * (plan['Supplier_Lead_Time_Days'] + 30) + plan['safety_stock']).round()
    plan['order_qty'] = np.where(plan['Closing_Stock'] <= plan['reorder_point'], (plan['order_up_to'] - plan['Closing_Stock']).clip(lower=0), 0)
    plan['excess_vs_90d'] = (plan['Closing_Stock'] - plan['forecast_90d'] - plan['safety_stock']).clip(lower=0)
    plan['excess_value'] = plan['excess_vs_90d'] * plan['unit_cost']
    plan['action'] = np.select([plan['order_qty'] > 0, plan['excess_vs_90d'] > 0], ['REORDER NOW', 'OVERSTOCK - transfer / promote'], 'OK')
    return plan


def transfers(plan):
    p = plan.pivot_table(index=['Product_ID', 'Product_Name'], columns='Location', values=['excess_vs_90d', 'order_qty'], aggfunc='sum').fillna(0)
    get = lambda a, b: p[(a, b)] if (a, b) in p.columns else 0
    t = pd.DataFrame({'wholesale_needs': get('order_qty', 'Wholesale'), 'store_excess': get('excess_vs_90d', 'Store'),
                      'online_excess': get('excess_vs_90d', 'Online')})
    t['transfer_qty'] = np.minimum(t['wholesale_needs'], t['store_excess'] + t['online_excess'])
    return t[t['transfer_qty'] > 0].sort_values('transfer_qty', ascending=False).reset_index()


# ================================================================ CARD 05 — marketing
@st.cache_data
def campaigns():
    s, m = load()['Sales_Transactions'], load()['Marketing'].copy()
    src = s[s['Channel'] != 'Wholesale'].groupby(['Product_ID', 'Order_Date'])['Net_Sales_EGP'].sum()
    during, base = [], []
    for _, c in m.iterrows():
        ps = src.loc[c['Product_ID']] if c['Product_ID'] in src.index.get_level_values(0) else pd.Series(dtype=float)
        days = (c['End_Date'] - c['Start_Date']).days + 1
        during.append(ps[(ps.index >= c['Start_Date']) & (ps.index <= c['End_Date'])].sum())
        base.append(ps[(ps.index >= c['Start_Date'] - pd.Timedelta(days=28)) & (ps.index < c['Start_Date'])].sum() / 28 * days)
    m['actual_sales'] = during
    m['baseline_sales'] = base
    m['roas_claimed'] = m['Attributed_Revenue_EGP'] / m['Spend_EGP']
    m['FY'] = fiscal_year(m['Start_Date'])
    return m


def platform_table(m):
    g = m.groupby('Platform').agg(spend=('Spend_EGP', 'sum'), revenue=('Attributed_Revenue_EGP', 'sum'), clicks=('Clicks', 'sum'),
                                  impressions=('Impressions', 'sum'), orders=('Orders_Attributed', 'sum'), campaigns=('Campaign_ID', 'size'))
    g['ROAS'] = g['revenue'] / g['spend']
    g['CPA'] = g['spend'] / g['orders']
    g['CTR_%'] = g['clicks'] / g['impressions'] * 100
    g['CVR_%'] = g['orders'] / g['clicks'] * 100
    return g.sort_values('ROAS', ascending=False).reset_index()


# ================================================================ CARD 06 / 07 / 08 — factory
@st.cache_data
def production():
    po = load()['Production_Orders'].copy()
    po['late'] = po['Delay_Days'] > 0
    po['quarter'] = po['Start_Date'].dt.to_period('Q').astype(str)
    po['FY'] = fiscal_year(po['Start_Date'])
    return po


@st.cache_data
def copq_by_fy():
    files = load()
    q, s, pb = files['Quality'].copy(), files['Sales_Transactions'], files['Printing_Batches'].copy()
    q['FY'] = fiscal_year(q['Inspection_Date'])
    pb['FY'] = fiscal_year(pb['Print_Date'])
    pb['reprint_cost'] = pb['Reprint_Qty'] * pb['Ink_or_Consumable_Cost_EGP'] / pb['Printed_Qty']
    out = pd.DataFrame({
        'QC rejects & scrap': q.groupby('FY')['Estimated_Loss_EGP'].sum(),
        'Quality-related refunds': s[s['Quality_Related_Return'] == 'Yes'].groupby('FY')['Refund_Value_EGP'].sum(),
        'Print rework': pb.groupby('FY')['Rework_Cost_EGP'].sum(),
        'Reprint ink': pb.groupby('FY')['reprint_cost'].sum(),
    }) / 1e6
    out['total'] = out.sum(axis=1)
    return out


@st.cache_data
def printing_machines():
    files = load()
    pb, dt = files['Printing_Batches'], files['Machine_Downtime']
    mc = pb.groupby('Machine_ID').agg(printed=('Printed_Qty', 'sum'), good=('Good_Qty', 'sum'), rejected=('Rejected_Qty', 'sum'),
                                      rework_cost=('Rework_Cost_EGP', 'sum'))
    mc['reject_rate_%'] = mc['rejected'] / mc['printed'] * 100
    p = dt[(dt['Business_Area'] == 'Printing') & (dt['Planned'] == 'No')]
    mc['unplanned_hours'] = p.groupby('Machine_ID')['Downtime_Hours'].sum()
    mc['unplanned_events'] = p.groupby('Machine_ID').size()
    mc['priority_score'] = (mc['reject_rate_%'].rank(ascending=False) + mc['unplanned_hours'].rank(ascending=False)
                            + mc['unplanned_events'].rank(ascending=False))
    mc = mc.sort_values(['priority_score', 'unplanned_hours'], ascending=[True, False]).reset_index()
    mc['fix_order'] = range(1, len(mc) + 1)
    return mc


# ================================================================ CARD 09 — suppliers
@st.cache_data
def supplier_metrics():
    files = load()
    po, sup = files['Purchase_Orders'].copy(), files['Suppliers']
    po['value'] = po['Ordered_Qty'] * po['Unit_Cost_EGP']
    g = po.groupby('Supplier_ID').agg(orders=('PO_ID', 'size'), late_rate=('On_Time', lambda x: 1 - x.mean()),
                                      avg_delay=('Delay_Days', 'mean'), lt_std=('Lead_Time_Days', 'std'), rejected=('Rejected_Qty', 'sum'),
                                      ordered=('Ordered_Qty', 'sum'), value=('value', 'sum'))
    g['reject_rate'] = g['rejected'] / g['ordered']
    g['spend_share'] = g['value'] / g['value'].sum()
    g = g.join(sup.set_index('Supplier_ID')[['Primary_Category', 'Contracted', 'Payment_Terms_Days']])
    return g.reset_index()


def risk_score(g, w_late, w_delay, w_var, w_spend):
    mm = lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else x * 0
    total = w_late + w_delay + w_var + w_spend
    if total == 0:
        return pd.Series(0, index=g.index)
    score = (w_late * mm(g['late_rate']) + w_delay * mm(g['avg_delay']) + w_var * mm(g['lt_std'])
             + w_spend * mm(g['spend_share'])) / total * 100
    return score.round(0)


# ================================================================ CARD 10 — profit bridge
@st.cache_data
def bridge_inputs():
    s = load()['Sales_Transactions']
    fy26 = s[s['FY'] == 'FY2026']
    b2c, wh = fy26[fy26['Channel'] != 'Wholesale'], fy26[fy26['Channel'] == 'Wholesale']
    inv = inventory()
    wh_price = wh.groupby('Product_ID')['Net_Sales_EGP'].sum() / wh.groupby('Product_ID')['Quantity'].sum()
    lost = inv[(inv['FY'] == 'FY2026') & (inv['Location_ID'] == 'LOC003')]
    m = load()['Marketing']
    return dict(
        base_sales=fy26['Net_Sales_EGP'].sum() / 1e6, base_profit=fy26['Gross_Profit_EGP'].sum() / 1e6,
        b2c_margin=b2c['Gross_Profit_EGP'].sum() / b2c['Net_Sales_EGP'].sum(),
        wh_margin=wh['Gross_Profit_EGP'].sum() / wh['Net_Sales_EGP'].sum(),
        wh_profit=wh['Gross_Profit_EGP'].sum() / 1e6,
        wh_gross=wh['Gross_Sales_EGP'].values, wh_disc=wh['Discount_Pct'].values, wh_net=wh['Net_Sales_EGP'].sum(),
        lost_sales=(lost['unmet_units'] * lost['Product_ID'].map(wh_price)).sum() / 1e6,
        influencer_yr=m.loc[m['Platform'] == 'Influencer', 'Spend_EGP'].sum() / 1e6 / 3,
        copq_yr=copq_by_fy().loc['FY2026', 'total'],
        size_refunds=fy26.loc[fy26['is_size_return'], 'Refund_Value_EGP'].sum() / 1e6,
        growth=fy26['Net_Sales_EGP'].sum() / s[s['FY'] == 'FY2025']['Net_Sales_EGP'].sum() - 1,
    )


def profit_bridge(cap=0.30, winback=0.20, at_risk_rev=10.1, holding=0.20, excess=7.4,
                  influencer_cut=0.70, copq_cut=0.20, size_cut=0.30, include_winback=True):
    b = bridge_inputs()
    cap_gain = ((b['wh_gross'] * (1 - np.minimum(b['wh_disc'], cap))).sum() - b['wh_net']) / 1e6
    rows = [
        [t('Cap wholesale discount', 'وضع سقف لخصم الجملة'), t('Discount cap', 'سقف الخصم'), t('Sales', 'المبيعات'), cap_gain],
        [t('Release excess stock', 'تصريف المخزون الزائد'), t('Excess stock', 'المخزون الزائد'), t('Supply chain', 'سلسلة الإمداد'), excess * holding],
        [t('Reduce cost of poor quality', 'خفض تكلفة الجودة الرديئة'), t('Quality', 'الجودة'), t('Factory', 'المصنع'), b['copq_yr'] * copq_cut],
        [t('Win back at-risk customers (needs test)', 'استعادة العملاء المعرّضين للخسارة (يحتاج تجربة)'), t('Win-back', 'الاستعادة'), 'CRM',
         at_risk_rev * winback * b['b2c_margin'] if include_winback else 0],
        [t('Cut Influencer spend', 'خفض إنفاق المؤثرين'), t('Influencers', 'المؤثرون'), t('Marketing', 'التسويق'), b['influencer_yr'] * influencer_cut],
        [t('Stop wholesale stockouts', 'منع نفاد مخزون الجملة'), t('Stockouts', 'النفاد'), t('Supply chain', 'سلسلة الإمداد'), b['lost_sales'] * b['wh_margin']],
        [t('Cut size/fit returns (App 8)', 'خفض مرتجعات المقاس (التطبيق 8)'), t('Size returns', 'مرتجعات المقاس'), t('Online', 'أونلاين'),
         b['size_refunds'] * size_cut * b['b2c_margin']],
    ]
    plan = pd.DataFrame(rows, columns=['action', 'short', 'owner', 'profit_M'])
    plan = plan[plan['profit_M'] > 0].sort_values('profit_M', ascending=False).reset_index(drop=True)
    breakeven = 1 - b['wh_profit'] / (b['wh_profit'] + cap_gain) if cap_gain > 0 else 0
    return plan, b, cap_gain, breakeven


# ================================================================ APP 8 — size & fit
KIDS_CHART = pd.DataFrame({  # illustrative chart: replace with Leo Moda's official measurements
    'size': ['4', '6', '8', '10', '12'],
    'age': ['3-4', '5-6', '7-8', '9-10', '11-12'],
    'height_min': [98, 110, 122, 134, 146], 'height_max': [110, 122, 134, 146, 158],
    'weight_max': [18, 23, 29, 37, 46],
})
WOMEN_CHART = pd.DataFrame({
    'size': ['M', 'L', 'XL', '2XL'],
    'weight_min': [0, 65, 75, 85], 'weight_max': [65, 75, 85, 200],
    'bust_cm': ['88-94', '94-100', '100-106', '106-114'],
})


def recommend_size(audience, height=None, weight=None, age=None, fit='Regular'):
    """Return (size, reason). Simple rules on an illustrative size chart."""
    if audience == 'Kids':
        ch = KIDS_CHART
        by_height = ch[(height >= ch['height_min']) & (height < ch['height_max'])]
        i = by_height.index[0] if len(by_height) else (0 if height < ch['height_min'].min() else len(ch) - 1)
        reason = t(f'Height {height} cm fits size {ch.loc[i, "size"]} ({ch.loc[i, "height_min"]}-{ch.loc[i, "height_max"]} cm).',
                   f'الطول {height} سم يناسب مقاس {ch.loc[i, "size"]} ({ch.loc[i, "height_min"]}-{ch.loc[i, "height_max"]} سم).')
        if weight is not None and weight > ch.loc[i, 'weight_max'] and i < len(ch) - 1:
            i += 1
            reason += t(f' Weight {weight} kg is above that size, so we go one size up.',
                        f' الوزن {weight} كجم أعلى من هذا المقاس، لذلك نرشّح مقاسًا أكبر.')
        if fit == 'Loose' and i < len(ch) - 1:
            i += 1
            reason += t(' Loose fit preferred: one size up.', ' تفضيل القَصّة الواسعة: مقاس أكبر.')
        return ch.loc[i, 'size'], reason
    ch = WOMEN_CHART
    i = ch[(weight >= ch['weight_min']) & (weight < ch['weight_max'])].index[0]
    reason = t(f'Weight {weight} kg fits size {ch.loc[i, "size"]} (bust {ch.loc[i, "bust_cm"]} cm).',
               f'الوزن {weight} كجم يناسب مقاس {ch.loc[i, "size"]} (محيط الصدر {ch.loc[i, "bust_cm"]} سم).')
    if height is not None and height >= 172 and i < len(ch) - 1:
        i += 1
        reason += t(' Tall height: one size up for length.', ' الطول كبير: مقاس أكبر من أجل الطول.')
    if fit == 'Loose' and i < len(ch) - 1:
        i += 1
        reason += t(' Loose fit preferred: one size up.', ' تفضيل القَصّة الواسعة: مقاس أكبر.')
    if fit == 'Snug' and i > 0:
        i -= 1
        reason += t(' Snug fit preferred: one size down.', ' تفضيل القَصّة الضيقة: مقاس أصغر.')
    return ch.loc[i, 'size'], reason
