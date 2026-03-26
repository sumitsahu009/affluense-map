"""
Affluense.ai — HNI Density Heatmap Dashboard
CSV schema: id, pin_code, networth

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import base64
import io
import os

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Affluense · HNI Density Map",
    page_icon="assets/affluense_logo.jpg",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# LOGO LOADER — embeds from file next to app.py
# ─────────────────────────────────────────────
def get_logo_b64() -> str:
    logo_path = os.path.join(os.path.dirname(__file__), "affluense_logo.jpg")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = get_logo_b64()
LOGO_HTML = (
    f'<img src="data:image/jpeg;base64,{LOGO_B64}" style="height:38px; object-fit:contain;">'
    if LOGO_B64 else
    '<span style="font-family:\'Syne\',sans-serif;font-size:22px;font-weight:800;color:#C9A84C;letter-spacing:-1px;">◈ AFFLUENSE</span>'
)

# ─────────────────────────────────────────────
# PINCODE → LAT/LON LOOKUP TABLE
# Covers major Indian pincodes. Extend as needed.
# ─────────────────────────────────────────────
@st.cache_data
def load_pincode_master():
    df_pin = pd.read_csv("india_pincode_latlng.csv")

    df_pin.columns = df_pin.columns.str.lower().str.strip()

    df_pin["pin_code"] = df_pin["pincode"].astype(str).str.zfill(6)
    df_pin["lat"] = df_pin["latitude"]
    df_pin["lon"] = df_pin["longitude"]

    # assumes your file already has 'state'
    df_pin["state"] = df_pin["state"]

    # city fallback
    if "officename" in df_pin.columns:
        df_pin["city"] = df_pin["officename"]
    elif "district" in df_pin.columns:
        df_pin["city"] = df_pin["district"]
    else:
        df_pin["city"] = "Unknown"

    return df_pin[["pin_code", "lat", "lon", "state", "city"]]


# ─────────────────────────────────────────────
# CUSTOM CSS — premium dark gold theme
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Mono', monospace;
    background-color: #07080D;
    color: #E8E4D8;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0D0F18 0%, #090B14 60%, #0A0C1A 100%);
    border-right: 1px solid #1C1F2E;
}}

/* Main background */
.stApp {{
    background: linear-gradient(145deg, #07080D 0%, #090C18 50%, #07090F 100%);
}}

/* Metrics */
.stMetric {{
    background: linear-gradient(135deg, #111420 0%, #0D1020 100%);
    border: 1px solid rgba(201,168,76,0.2);
    border-radius: 6px;
    padding: 14px !important;
    box-shadow: 0 2px 12px rgba(201,168,76,0.06);
}}
.stMetric label {{
    color: #8A8899 !important;
    font-size: 9px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase;
    font-family: 'DM Mono', monospace !important;
}}
.stMetric [data-testid="stMetricValue"] {{
    font-family: 'Syne', sans-serif !important;
    font-weight: 700;
    font-size: 24px !important;
    background: linear-gradient(135deg, #C9A84C, #F0D898);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.stMetric [data-testid="stMetricDelta"] {{
    font-size: 10px !important;
    color: #7A9C7A !important;
}}

/* Sidebar widgets */
.stSelectbox label, .stMultiSelect label, .stSlider label,
.stFileUploader label, .stCheckbox label {{
    color: #8A8899 !important;
    font-size: 9px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    font-family: 'DM Mono', monospace !important;
}}

/* Selectbox / input borders */
.stSelectbox > div > div,
.stMultiSelect > div > div {{
    background: #111420 !important;
    border-color: #1C1F2E !important;
}}

/* Slider accent */
.stSlider [data-baseweb="slider"] [data-testid="stSlider"] {{
    color: #C9A84C;
}}

/* Block container */
.block-container {{
    padding-top: 1.2rem;
    padding-bottom: 0.5rem;
    max-width: 100%;
}}

/* Headers */
h1, h2, h3 {{
    font-family: 'Syne', sans-serif !important;
    font-weight: 800;
    letter-spacing: -0.5px;
}}

/* Tag pill */
.tag {{
    display: inline-block;
    background: #131626;
    border: 1px solid #C9A84C44;
    color: #C9A84C;
    font-size: 9px;
    letter-spacing: 2px;
    padding: 2px 10px;
    border-radius: 2px;
    text-transform: uppercase;
    font-family: 'DM Mono', monospace;
}}

/* Divider */
hr {{ border-color: #1C1F2E; }}

/* Dataframe */
[data-testid="stDataFrameResizable"] {{
    background: #0D1020;
    border: 1px solid #1C1F2E;
    border-radius: 6px;
}}

/* Header bar */
.header-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0 8px 0;
    border-bottom: 1px solid #1C1F2E;
    margin-bottom: 16px;
}}

/* Upload area */
[data-testid="stFileUploader"] {{
    background: #0D1020;
    border: 1px dashed #C9A84C55;
    border-radius: 6px;
    padding: 4px;
}}

/* Expander */
[data-testid="stExpander"] {{
    background: #0D1020;
    border: 1px solid #1C1F2E;
    border-radius: 6px;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 4px; background: #07080D; }}
::-webkit-scrollbar-thumb {{ background: #C9A84C55; border-radius: 2px; }}

/* Section title */
.section-title {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 2.5px;
    color: #C9A84C;
    text-transform: uppercase;
    margin-bottom: 6px;
    margin-top: 12px;
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_csv(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(file_bytes))
    df.columns = df.columns.str.strip().str.lower()

    required = {"pin_code", "networth"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"❌ CSV missing required columns: {missing}. Found: {list(df.columns)}")
        st.stop()

    df["pin_code"] = df["pin_code"].astype(str).str.strip().str.zfill(6)
    df["networth"] = pd.to_numeric(df["networth"], errors="coerce").fillna(0)
    df["networth_cr"] = (df["networth"] / 1e7).round(2)

    # Wealth classification
    def classify(nw):
        if nw >= 1e8:   return "Ultra HNI (₹10Cr+)"
        elif nw >= 1e7: return "HNI (₹1–10Cr)"
        else:           return "Emerging Affluent (<₹1Cr)"
    df["wealth_band"] = df["networth"].apply(classify)

    # ✅ CORRECT: merge FIRST
    pincode_master = load_pincode_master()
    df = df.merge(pincode_master, on="pin_code", how="left")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    # ✅ Handle column collisions (bulletproof)
    if "state" not in df.columns:
        if "state_y" in df.columns:
            df["state"] = df["state_y"]
        elif "state_x" in df.columns:
            df["state"] = df["state_x"]

    if "city" not in df.columns:
        if "city_y" in df.columns:
            df["city"] = df["city_y"]
        elif "city_x" in df.columns:
            df["city"] = df["city_x"]

    # cleanup duplicates
    df = df.drop(columns=[c for c in ["state_x", "state_y", "city_x", "city_y"] if c in df.columns])

    # Now safe to check lat/lon
    matched = df["lat"].notna().sum()
    unmatched = df["lat"].isna().sum()

    if unmatched > 0:
        st.sidebar.warning(f"⚠ {unmatched:,} pincodes not mapped and will be skipped.")

    # ✅ drop AFTER merge
    df = df.dropna(subset=["lat", "lon"])

    return df

@st.cache_data
def aggregate_pincodes(df_bytes, filters_key) -> pd.DataFrame:
    # dummy wrapper to allow re-aggregation on filter change
    pass


def agg_by_pin(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("pin_code")
        .agg(
            hni_count      = ("pin_code",    "count"),
            total_networth = ("networth_cr", "sum"),
            avg_networth   = ("networth_cr", "mean"),
            lat            = ("lat",         "mean"),
            lon            = ("lon",         "mean"),
            state          = ("state",       lambda x: x.mode()[0]),
            city           = ("city",        lambda x: x.mode()[0]),
        )
        .reset_index()
        .round({"total_networth": 1, "avg_networth": 2})
    )


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown(
        f'<div style="padding:12px 0 10px 0;">{LOGO_HTML}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-title">HNI Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Data source
    st.markdown('<div class="section-title">Data Source</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        help="Required columns: pin_code, networth",
    )

    # Default to bundled t.csv if no upload
    default_csv = os.path.join(os.path.dirname(__file__), "t.csv")
    if uploaded:
        file_bytes = uploaded.read()
        data_label = uploaded.name
    elif os.path.exists(default_csv):
        with open(default_csv, "rb") as f:
            file_bytes = f.read()
        data_label = "t.csv (bundled)"
    else:
        st.info("Upload a CSV to begin.")
        st.stop()

    df_full = load_csv(file_bytes)
    st.markdown(
        f'<span class="tag">{len(df_full):,} records</span>&nbsp;<span class="tag">{df_full["pin_code"].nunique()} pincodes</span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Map view
    st.markdown('<div class="section-title">Map View</div>', unsafe_allow_html=True)
    map_view = st.radio(
        "Zoom Level",
        options=["India (All States)", "State / City"],
        index=0,
        horizontal=False,
    )

    # Geography filter — only shown for State/City view
    all_states = sorted(df_full["state"].dropna().unique())
    if map_view == "State / City" and all_states:
        selected_states = st.multiselect("State / Circle", options=all_states, default=all_states)
        if not selected_states:
            selected_states = all_states
    else:
        selected_states = all_states

    st.markdown("---")

    # Networth filter
    st.markdown('<div class="section-title">Net Worth Filter</div>', unsafe_allow_html=True)
    nw_min = float(df_full["networth_cr"].min())
    nw_max = float(df_full["networth_cr"].quantile(0.99))
    step = max(0.1, round((nw_max - nw_min) / 100, 1))

    nw_threshold = st.slider(
        "Min Net Worth (₹ Crore)",
        min_value=round(nw_min, 1),
        max_value=round(nw_max, 1),
        value=round(nw_min, 1),
        step=step,
        format="₹%.1fCr",
    )

    st.markdown("---")

    # Wealth band
    st.markdown('<div class="section-title">Wealth Segment</div>', unsafe_allow_html=True)
    all_bands = sorted(df_full["wealth_band"].unique())
    selected_bands = st.multiselect("Band", options=all_bands, default=all_bands)
    if not selected_bands:
        selected_bands = all_bands

    st.markdown("---")

    # Map style
    st.markdown('<div class="section-title">Map Style</div>', unsafe_allow_html=True)
    map_style = st.selectbox(
        "Base Map",
        ["carto-darkmatter", "carto-positron", "open-street-map"],
        index=0,
    )

    st.markdown("---")
    st.markdown(f'<span style="color:#3A3F55;font-size:10px;">📂 {data_label}</span>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────────
df = df_full[
    df_full["state"].isin(selected_states) &
    df_full["wealth_band"].isin(selected_bands) &
    (df_full["networth_cr"] >= nw_threshold)
].copy()

if df.empty:
    st.warning("No records match the current filters.")
    st.stop()

df_pin = agg_by_pin(df)


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if LOGO_B64:
        st.markdown(
            f'<div style="padding-top:18px;">'
            f'<img src="data:image/jpeg;base64,{LOGO_B64}" style="height:44px;object-fit:contain;">'
            f'</div>',
            unsafe_allow_html=True,
        )
with col_title:
    st.markdown(
    """
    <h2 style="
        margin: 0;
        padding-top: 18px;
        padding-bottom: 4px;
        line-height: 1.3;
        background: linear-gradient(135deg,#C9A84C,#F0D898);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    ">
        HNI Density · India Pincode Heatmap
    </h2>
    """,
    unsafe_allow_html=True,
    )

st.markdown(
    f'<span class="tag">{len(df_pin)} pincodes</span>&nbsp;&nbsp;'
    f'<span class="tag">{len(df):,} individuals</span>&nbsp;&nbsp;'
    f'<span class="tag">≥ ₹{nw_threshold:.1f}Cr networth</span>&nbsp;&nbsp;'
    f'<span class="tag">{map_view}</span>',
    unsafe_allow_html=True,
)
st.markdown("")


# ─────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)

top_pin     = df_pin.loc[df_pin["hni_count"].idxmax()]
total_nw    = df["networth_cr"].sum()
avg_nw      = df["networth_cr"].mean()
top_state   = df.groupby("state").size().idxmax() if not df["state"].isna().all() else "—"

m1.metric("Total Individuals",   f"{len(df):,}")
m2.metric("Pincodes Covered",    f"{len(df_pin):,}")
m3.metric("Total Networth",      f"₹{total_nw:,.0f} Cr")
m4.metric("Avg Networth",        f"₹{avg_nw:.1f} Cr")
m5.metric("Hottest Pincode",     top_pin["pin_code"],
          delta=f"{int(top_pin['hni_count'])} HNIs · {top_pin['city']}, {top_pin['state']}")

st.markdown("---")


# ─────────────────────────────────────────────
# MAP ZOOM SETTINGS
# ─────────────────────────────────────────────
if map_view == "India (All States)":
    center_lat, center_lon, zoom = 20.5937, 78.9629, 4.2
else:
    center_lat = df_pin["lat"].mean()
    center_lon = df_pin["lon"].mean()
    zoom = 5 if len(selected_states) > 2 else 8


# ─────────────────────────────────────────────
# MAP + TABLE
# ─────────────────────────────────────────────
map_col, table_col = st.columns([3, 1])

with map_col:
    fig = go.Figure()

    # Density heatmap layer
    fig.add_trace(go.Densitymapbox(
        lat=df_pin["lat"],
        lon=df_pin["lon"],
        z=df_pin["hni_count"],
        radius=35,
        colorscale=[
            [0.00, "rgba(201,168,76,0.0)"],
            [0.20, "rgba(201,140,40,0.35)"],
            [0.45, "rgba(210,100,20,0.60)"],
            [0.70, "rgba(210,50,15,0.82)"],
            [1.00, "rgba(190,10,10,1.0)"],
        ],
        showscale=True,
        colorbar=dict(
            title=dict(text="HNI Count", font=dict(color="#8A8899", size=10, family="DM Mono")),
            tickfont=dict(color="#8A8899", size=9, family="DM Mono"),
            bgcolor="rgba(13,16,32,0.85)",
            bordercolor="rgba(201,168,76,0.2)",
            borderwidth=1,
            len=0.5, thickness=10, x=1.01,
        ),
        zmin=max(1, df_pin["hni_count"].quantile(0.05)),
        zmax=df_pin["hni_count"].quantile(0.95),
        hoverinfo="skip",
    ))

    # Scatter dot layer with tooltip
    fig.add_trace(go.Scattermapbox(
        lat=df_pin["lat"],
        lon=df_pin["lon"],
        mode="markers",
        marker=dict(
            size=8 if map_view == "State / City" else 6,
            color=df_pin["hni_count"],
            colorscale=[
                [0.0, "#C9A84C"],
                [0.5, "#D45A20"],
                [1.0, "#B80A0A"],
            ],
            opacity=0.9,
            showscale=False,
        ),
        text=df_pin["pin_code"],
        customdata=df_pin[[
            "city", "state", "hni_count", "avg_networth", "total_networth"
        ]].values,
        hovertemplate=(
            "<b style='color:#C9A84C'>%{text}</b>  %{customdata[0]}<br>"
            "<span style='color:#8A8899'>%{customdata[1]}</span><br>"
            "─────────────────────<br>"
            "HNI Count      : <b>%{customdata[2]:,}</b><br>"
            "Avg Networth   : <b>₹%{customdata[3]:.2f} Cr</b><br>"
            "Total Networth : <b>₹%{customdata[4]:.1f} Cr</b>"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        mapbox=dict(
            style=map_style,
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom,
        ),
        paper_bgcolor="rgba(7,8,13,0)",
        plot_bgcolor="rgba(7,8,13,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=560,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})

with table_col:
    st.markdown(
        '<div class="section-title">Top Pincodes · HNI Count</div>',
        unsafe_allow_html=True,
    )
    top_table = (
        df_pin
        .sort_values("hni_count", ascending=False)
        .head(20)[["pin_code", "city", "state", "hni_count", "avg_networth", "total_networth"]]
        .rename(columns={
            "pin_code":      "PIN",
            "city":          "City",
            "state":         "State",
            "hni_count":     "HNIs",
            "avg_networth":  "Avg(Cr)",
            "total_networth":"Total(Cr)",
        })
        .reset_index(drop=True)
    )
    st.dataframe(top_table, use_container_width=True, height=520, hide_index=True)


# ─────────────────────────────────────────────
# BOTTOM ANALYTICS
# ─────────────────────────────────────────────
st.markdown("---")
b1, b2, b3 = st.columns(3)

CHART_BG   = "rgba(13,16,32,0.0)"
AXIS_COLOR = "#3A3F55"
FONT_COLOR = "#8A8899"
GOLD_START = "#1C1F2E"
GOLD_END   = "#C9A84C"

# State bar
with b1:
    state_agg = (
        df.groupby("state").size()
        .reset_index(name="count")
        .sort_values("count", ascending=True)
        .tail(10)
    )
    fig_bar = go.Figure(go.Bar(
        x=state_agg["count"],
        y=state_agg["state"],
        orientation="h",
        marker=dict(
            color=state_agg["count"],
            colorscale=[[0, GOLD_START], [1, GOLD_END]],
            showscale=False,
        ),
        text=state_agg["count"].apply(lambda x: f"{x:,}"),
        textposition="outside",
        textfont=dict(color=FONT_COLOR, size=10, family="DM Mono"),
    ))
    fig_bar.update_layout(
        title=dict(text="HNIs by State", font=dict(color="#E8E4D8", size=12, family="Syne")),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(color=FONT_COLOR, family="DM Mono"),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        margin=dict(l=0, r=55, t=36, b=10), height=260,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Wealth band donut
with b2:
    band_agg = df.groupby("wealth_band").size().reset_index(name="count")
    fig_pie = go.Figure(go.Pie(
        labels=band_agg["wealth_band"],
        values=band_agg["count"],
        hole=0.62,
        marker=dict(
            colors=["#C9A84C", "#8A6020", "#3A2810"],
            line=dict(color="#07080D", width=3),
        ),
        textfont=dict(color="#E8E4D8", size=10, family="DM Mono"),
        hovertemplate="<b>%{label}</b><br>%{value:,} individuals (%{percent})<extra></extra>",
    ))
    fig_pie.update_layout(
        title=dict(text="Wealth Band Mix", font=dict(color="#E8E4D8", size=12, family="Syne")),
        paper_bgcolor=CHART_BG,
        legend=dict(font=dict(color=FONT_COLOR, size=9, family="DM Mono"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=36, b=10), height=260,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Networth histogram
with b3:
    clip_val = df["networth_cr"].quantile(0.97)
    fig_hist = go.Figure(go.Histogram(
        x=df["networth_cr"].clip(upper=clip_val),
        nbinsx=30,
        marker=dict(
            color="#C9A84C",
            opacity=0.7,
            line=dict(color="#07080D", width=0.5),
        ),
    ))
    fig_hist.update_layout(
        title=dict(text="Networth Distribution (₹ Cr)", font=dict(color="#E8E4D8", size=12, family="Syne")),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(color=FONT_COLOR, family="DM Mono"),
        xaxis=dict(showgrid=False, title="₹ Crore", titlefont=dict(size=10), color=FONT_COLOR, linecolor=AXIS_COLOR),
        yaxis=dict(showgrid=False, title="Count",   titlefont=dict(size=10), color=FONT_COLOR),
        margin=dict(l=10, r=10, t=36, b=10), height=260, bargap=0.04,
    )
    st.plotly_chart(fig_hist, use_container_width=True)


# ─────────────────────────────────────────────
# RAW DATA EXPLORER
# ─────────────────────────────────────────────
with st.expander("📋  Raw Data Explorer", expanded=False):
    show_cols = [c for c in ["id", "pin_code", "city", "state", "networth_cr", "wealth_band"] if c in df.columns]
    display_df = (
        df[show_cols]
        .sort_values("networth_cr", ascending=False)
        .rename(columns={"networth_cr": "networth (₹Cr)", "pin_code": "pincode"})
        .reset_index(drop=True)
    )
    st.dataframe(display_df, use_container_width=True, height=280, hide_index=True)
    st.download_button(
        "⬇  Download filtered CSV",
        display_df.to_csv(index=False).encode("utf-8"),
        "affluense_filtered.csv",
        "text/csv",
    )


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<div style="display:flex;align-items:center;gap:14px;">'
    f'{LOGO_HTML}'
    f'<span style="color:#2E3250;font-size:10px;font-family:DM Mono,monospace;">'
    f'Pincode-level HNI Intelligence · {data_label} · {len(df):,} records plotted'
    f'</span></div>',
    unsafe_allow_html=True,
)
