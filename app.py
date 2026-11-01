
"""VendorWatch — Neon cybersecurity dashboard."""

import json
import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from vendorwatch.models import VendorProfile
from vendorwatch.pipeline import run, summarize
from vendorwatch import config


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="VendorWatch | Privacy Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #080B14;
        --panel: #111827;
        --border: #263247;
        --cyan: #00E5FF;
        --purple: #8B5CF6;
        --muted: #94A3B8;
        --white: #F8FAFC;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 10% 0%, rgba(0,229,255,.08), transparent 35%),
            radial-gradient(ellipse at 90% 5%, rgba(139,92,246,.10), transparent 30%),
            #080B14;
        color: #F8FAFC;
    }

    [data-testid="stHeader"] {
        background: rgba(8,11,20,.75);
    }

    [data-testid="stSidebar"] {
        background: #0D1321;
        border-right: 1px solid #263247;
    }

    [data-testid="stSidebar"] * {
        color: #E2E8F0;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    h1, h2, h3 {
        color: #F8FAFC !important;
        letter-spacing: -0.5px;
    }

    p, label, .stCaption {
        color: #A8B5C8;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }

    .brand-icon {
        width: 46px;
        height: 46px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 25px;
        background: linear-gradient(135deg, #123B48, #202044);
        border: 1px solid rgba(0,229,255,.35);
        box-shadow: 0 0 22px rgba(0,229,255,.12);
    }

    .brand-name {
        font-size: 25px;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: 1.5px;
    }

    .brand-sub {
        color: #8B9AAF;
        font-size: 10px;
        letter-spacing: 2px;
        margin-top: -3px;
    }

    .top-status {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        border: 1px solid rgba(34,197,94,.35);
        background: rgba(34,197,94,.08);
        color: #4ADE80;
        padding: 7px 12px;
        border-radius: 30px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    .status-dot {
        height: 7px;
        width: 7px;
        border-radius: 50%;
        background: #22C55E;
        box-shadow: 0 0 9px #22C55E;
    }

    .hero {
        padding: 22px 0 18px 0;
    }

    .hero-kicker {
        color: #00E5FF;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }

    .hero-title {
        font-size: clamp(27px, 3vw, 38px);
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.2;
    }

    .hero-desc {
        color: #94A3B8;
        font-size: 14px;
        margin-top: 8px;
        max-width: 650px;
    }

    .panel {
        background: linear-gradient(145deg, #131D2D, #0F1725);
        border: 1px solid #263247;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 10px 35px rgba(0,0,0,.14);
    }

    .panel-title {
        font-size: 15px;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 4px;
    }

    .panel-subtitle {
        font-size: 11px;
        color: #8190A6;
    }

    .metric-card {
        background: linear-gradient(145deg, #141F30, #0F1725);
        border: 1px solid #29374D;
        border-radius: 15px;
        padding: 18px 18px 16px 18px;
        min-height: 112px;
        box-shadow: 0 8px 25px rgba(0,0,0,.15);
    }

    .metric-label {
        font-size: 11px;
        color: #9AAAC0;
        font-weight: 600;
        letter-spacing: .8px;
        text-transform: uppercase;
    }

    .metric-value {
        font-size: 31px;
        font-weight: 800;
        margin-top: 10px;
        line-height: 1;
    }

    .metric-note {
        font-size: 10px;
        color: #718198;
        margin-top: 8px;
    }

    .cyan { color: #00E5FF; }
    .purple { color: #A78BFA; }
    .red { color: #FB7185; }
    .green { color: #4ADE80; }
    .orange { color: #FBBF24; }

    .demo-banner {
        background: rgba(139,92,246,.10);
        border: 1px solid rgba(139,92,246,.35);
        color: #C4B5FD;
        border-radius: 10px;
        padding: 11px 14px;
        font-size: 12px;
        font-weight: 600;
        margin: 12px 0 18px 0;
    }

    .privacy-note {
        background: rgba(0,229,255,.045);
        border: 1px solid rgba(0,229,255,.20);
        border-radius: 12px;
        padding: 13px 15px;
        color: #AFC4D5;
        font-size: 11px;
        line-height: 1.6;
        margin-top: 15px;
    }

    .section-heading {
        font-size: 18px;
        font-weight: 750;
        color: #F8FAFC;
        margin: 22px 0 12px 0;
    }

    .vendor-domain {
        color: #F1F5F9;
        font-weight: 650;
        font-size: 13px;
    }

    .vendor-company {
        color: #8493A8;
        font-size: 11px;
    }

    div.stButton > button {
        background: linear-gradient(100deg, #00BFD6, #4777FF);
        color: #06111B;
        border: none;
        border-radius: 10px;
        font-weight: 800;
        min-height: 44px;
        transition: .2s ease;
    }

    div.stButton > button:hover {
        box-shadow: 0 0 22px rgba(0,229,255,.25);
        border: none;
        color: #06111B;
        transform: translateY(-1px);
    }

    div.stDownloadButton > button {
        background: #172338;
        color: #00E5FF;
        border: 1px solid #24516A;
        border-radius: 9px;
        font-weight: 700;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #263247;
        border-radius: 12px;
        overflow: hidden;
    }

    .footer {
        border-top: 1px solid #263247;
        margin-top: 40px;
        padding-top: 18px;
        color: #64748B;
        font-size: 10px;
        text-align: center;
        letter-spacing: 1px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def load_demo() -> list[VendorProfile]:
    path = Path(__file__).parent / "data" / "demo_results.json"

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    return [VendorProfile(**item) for item in data]


def risk_color(risk: str) -> str:
    return {
        "low": "#22C55E",
        "medium": "#F59E0B",
        "high": "#F43F5E",
        "unknown": "#94A3B8",
    }.get(str(risk).lower(), "#94A3B8")


def metric_card(label: str, value: int, color: str, note: str):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {color}">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def profile_to_row(p: VendorProfile) -> dict:
    return {
        "Domain": p.registrable,
        "Company": p.company,
        "Category": p.category.title(),
        "Risk": p.risk.title(),
        "Data sharing": (
            "Yes" if p.sells_or_shares_data is True
            else "No" if p.sells_or_shares_data is False
            else "Unknown"
        ),
        "Hits": p.hits,
        "Policy source": p.method,
        "Policy URL": p.policy_url or "",
    }


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">🛡️</div>
            <div>
                <div class="brand-name">VENDORWATCH</div>
                <div class="brand-sub">PRIVACY INTELLIGENCE</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### ⚙️ Audit Controls")

    demo_mode = st.toggle(
        "Demo mode",
        value=False,
        help="Load illustrative sample results without making API calls.",
    )

    st.caption("Use demo mode for a quick presentation without live API calls.")

    st.markdown("---")
    st.markdown("### 🧩 Configuration")

    st.caption(
        f"Gemini model: `{config.GEMINI_MODEL}`"
    )

    st.caption(
        f"Agent fallback: {'Enabled' if config.ALLOW_AGENT_FALLBACK else 'Disabled'}"
    )

    st.markdown("---")
    st.markdown("### 📁 Capture Settings")

    own_domains_text = st.text_input(
        "Exclude your own domains",
        placeholder="myapp.com, api.myapp.com",
        help="These domains will be treated as first-party.",
    )

    st.markdown("---")
    st.caption("VENDORWATCH • HACKATHON EDITION")


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

header_left, header_right = st.columns([5, 1])

with header_left:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">CYBERSECURITY / PRIVACY MONITORING</div>
            <div class="hero-title">Security Command Center</div>
            <div class="hero-desc">
                Discover third-party vendors, inspect privacy policies,
                and understand potential data-sharing risks.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_right:
    st.markdown(
        """
        <div style="text-align:right; padding-top:22px;">
            <span class="top-status">
                <span class="status-dot"></span> READY
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# UPLOAD / AUDIT PANEL
# ---------------------------------------------------------

st.markdown('<div class="panel">', unsafe_allow_html=True)
upload_left, upload_right = st.columns([3, 1])

with upload_left:
    st.markdown('<div class="panel-title">Network Capture Audit</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-subtitle">Upload a PCAP or PCAPNG file to investigate contacted vendors.</div>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Choose network capture",
        type=["pcap", "pcapng"],
        label_visibility="collapsed",
        disabled=demo_mode,
    )

with upload_right:
    st.markdown("<br>", unsafe_allow_html=True)
    run_clicked = st.button(
        "⚡ RUN AUDIT",
        type="primary",
        use_container_width=True,
        disabled=(not demo_mode and uploaded is None),
    )

st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# AUDIT EXECUTION
# ---------------------------------------------------------

if run_clicked:
    profiles = []

    if demo_mode:
        try:
            profiles = load_demo()
            st.session_state["profiles"] = [
                p.to_dict() for p in profiles
            ]
            st.session_state["demo_mode"] = True
            st.success("Illustrative demo report loaded successfully.")

        except Exception as exc:
            st.error(f"Could not load demo data: {type(exc).__name__}: {exc}")

    elif uploaded is not None:
        suffix = (
            ".pcapng"
            if uploaded.name.lower().endswith(".pcapng")
            else ".pcap"
        )

        capture_path = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
            ) as temp:
                temp.write(uploaded.getbuffer())
                capture_path = temp.name

            progress = st.progress(
                0,
                text="Preparing network capture...",
            )

            status = st.empty()

            def update(done: int, total: int, name: str):
                percent = done / total if total else 1.0
                progress.progress(
                    percent,
                    text=f"Investigating vendors: {done}/{total}",
                )
                status.caption(f"Latest vendor: {name}")

            own_domains = [
                x.strip()
                for x in own_domains_text.split(",")
                if x.strip()
            ]

            profiles = run(
                capture_path,
                own_domains,
                on_progress=update,
            )

            st.session_state["profiles"] = [
                p.to_dict() for p in profiles
            ]
            st.session_state["demo_mode"] = False

            progress.progress(1.0, text="Audit completed.")
            status.success("Network audit completed.")

        except Exception as exc:
            st.error(
                f"Audit failed: {type(exc).__name__}: {exc}"
            )

        finally:
            if capture_path:
                Path(capture_path).unlink(missing_ok=True)


# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------

if "profiles" in st.session_state:

    profiles = [
        VendorProfile(**item)
        for item in st.session_state["profiles"]
    ]

    is_demo = st.session_state.get("demo_mode", False)

    summary = summarize(profiles)

    third_party = [
        p for p in profiles
        if p.category != "first-party"
    ]

    # DEMO LABEL
    if is_demo:
        st.markdown(
            """
            <div class="demo-banner">
                ◈ ILLUSTRATIVE DEMO DATA — These are sample results for presentation,
                not findings from a live network capture.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # KPI CARDS
    st.markdown(
        '<div class="section-heading">Overview Metrics</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Third-party domains",
            summary["third_party"],
            "cyan",
            "External registrable domains",
        )

    with c2:
        metric_card(
            "High risk",
            summary["high_risk"],
            "red",
            "Vendors marked high risk",
        )

    with c3:
        metric_card(
            "Sharing detected",
            summary["sell_or_share"],
            "purple",
            "Explicit policy verdicts",
        )

    with c4:
        policies_found = sum(
            bool(p.policy_url) for p in third_party
        )

        metric_card(
            "Policies found",
            policies_found,
            "green",
            "Vendors with policy links",
        )

    st.markdown(
        f"""
        <div class="panel-subtitle" style="margin:10px 2px 20px 2px;">
            {summary['total_domains']} total registrable domains observed
            &nbsp; • &nbsp;
            {summary['policy_not_found']} policies unavailable
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CHARTS
    st.markdown(
        '<div class="section-heading">Risk Intelligence</div>',
        unsafe_allow_html=True,
    )

    chart_left, chart_right = st.columns(2)

    risk_order = ["low", "medium", "high", "unknown"]

    risk_counts = (
        pd.Series([p.risk.lower() for p in third_party])
        .value_counts()
        .reindex(risk_order, fill_value=0)
        .rename_axis("Risk")
        .reset_index(name="Vendors")
    )

    risk_palette = {
        "low": "#22C55E",
        "medium": "#F59E0B",
        "high": "#F43F5E",
        "unknown": "#64748B",
    }

    with chart_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("**Risk Distribution**")

        if len(third_party):
            fig = px.pie(
                risk_counts,
                names="Risk",
                values="Vendors",
                hole=0.68,
                color="Risk",
                color_discrete_map=risk_palette,
            )

            fig.update_traces(
                textposition="inside",
                textinfo="percent",
                marker=dict(
                    line=dict(color="#111827", width=3)
                ),
            )

            fig.update_layout(
                height=300,
                margin=dict(t=15, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#DCE6F2"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.12,
                    xanchor="center",
                    x=0.5,
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False},
            )
        else:
            st.info("No third-party vendors to display.")

        st.markdown("</div>", unsafe_allow_html=True)

    category_counts = (
        pd.Series([p.category.lower() for p in third_party])
        .value_counts()
        .rename_axis("Category")
        .reset_index(name="Vendors")
    )

    with chart_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("**Vendor Categories**")

        if not category_counts.empty:
            fig2 = px.bar(
                category_counts,
                x="Vendors",
                y="Category",
                orientation="h",
                color="Category",
                color_discrete_sequence=[
                    "#00E5FF",
                    "#8B5CF6",
                    "#4777FF",
                    "#22C55E",
                    "#F59E0B",
                    "#64748B",
                ],
            )

            fig2.update_layout(
                height=300,
                margin=dict(t=15, b=10, l=5, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#DCE6F2"),
                showlegend=False,
                xaxis=dict(
                    title="Vendor count",
                    gridcolor="#263247",
                    zerolinecolor="#263247",
                ),
                yaxis=dict(
                    title="",
                    autorange="reversed",
                ),
            )

            st.plotly_chart(
                fig2,
                use_container_width=True,
                config={"displayModeBar": False},
            )
        else:
            st.info("No category information available.")

        st.markdown("</div>", unsafe_allow_html=True)

    # FILTERS
    st.markdown(
        '<div class="section-heading">Vendor Intelligence</div>',
        unsafe_allow_html=True,
    )

    filter_col, search_col = st.columns([1, 2])

    with filter_col:
        selected_risk = st.selectbox(
            "Filter by risk",
            ["All", "High", "Medium", "Low", "Unknown"],
        )

    with search_col:
        search_text = st.text_input(
            "Search vendors",
            placeholder="Search domain or company...",
        )

    filtered = third_party

    if selected_risk != "All":
        filtered = [
            p for p in filtered
            if p.risk.lower() == selected_risk.lower()
        ]

    if search_text.strip():
        term = search_text.strip().lower()

        filtered = [
            p for p in filtered
            if term in p.registrable.lower()
            or term in p.company.lower()
        ]

    rows = [profile_to_row(p) for p in filtered]

    if rows:
        df = pd.DataFrame(rows)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=390,
            column_config={
                "Risk": st.column_config.TextColumn("Risk"),
                "Policy URL": st.column_config.LinkColumn(
                    "Privacy Policy",
                    display_text="Open policy",
                ),
                "Hits": st.column_config.NumberColumn(
                    "Network hits",
                    format="%d",
                ),
            },
        )

        st.caption(
            f"Showing {len(filtered)} of {len(third_party)} third-party vendors."
        )
    else:
        st.info("No vendors match the selected filter.")

    # EVIDENCE INSPECTOR
    st.markdown(
        '<div class="section-heading">Evidence & Policy Inspector</div>',
        unsafe_allow_html=True,
    )

    if filtered:
        for p in filtered:
            risk = p.risk.lower()
            color = risk_color(risk)

            title = (
                f"{p.registrable}  |  {p.company}  |  {risk.upper()}"
            )

            with st.expander(title):

                left, right = st.columns([3, 1])

                with left:
                    st.markdown(
                        f"""
                        <div style="color:{color};font-weight:800;font-size:12px;">
                            {risk.upper()} RISK
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(f"**Category:** {p.category.title()}")
                    st.markdown(f"**Country:** {p.country or 'Unknown'}")
                    st.markdown(f"**Network hits:** {p.hits}")
                    st.markdown(f"**Policy retrieval:** {p.method}")

                with right:
                    sharing = (
                        "Yes" if p.sells_or_shares_data is True
                        else "No" if p.sells_or_shares_data is False
                        else "Unknown"
                    )

                    st.metric("Data sharing", sharing)

                st.markdown("**Analysis explanation**")
                st.write(p.reason or "No explanation available.")

                st.markdown("**Policy evidence**")

                if p.evidence:
                    if p.evidence_verified:
                        st.success("Quote verified in retrieved policy text.")
                    else:
                        st.warning("Quote could not be verified.")

                    st.write(f"> {p.evidence}")
                else:
                    st.caption("No verbatim evidence quote available.")

                if p.policy_url:
                    st.link_button(
                        "↗ Open Privacy Policy",
                        p.policy_url,
                    )

    else:
        st.info("No vendor evidence available for the current filter.")

    # DOWNLOAD REPORT
    st.markdown(
        '<div class="section-heading">Export Audit Report</div>',
        unsafe_allow_html=True,
    )

    payload = json.dumps(
        [p.to_dict() for p in profiles],
        indent=2,
        ensure_ascii=False,
    )

    st.download_button(
        label="⬇ Download Complete JSON Report",
        data=payload,
        file_name="vendorwatch-report.json",
        mime="application/json",
        use_container_width=True,
    )

else:
    # EMPTY STATE
    st.markdown(
        """
        <div class="panel" style="text-align:center;padding:45px 20px;">
            <div style="font-size:48px;">🛡️</div>
            <div style="font-size:21px;font-weight:800;color:#F8FAFC;margin-top:12px;">
                Ready to investigate?
            </div>
            <div style="font-size:13px;color:#94A3B8;margin-top:8px;">
                Upload a PCAP capture or enable Demo mode from the sidebar,
                then click RUN AUDIT.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# PRIVACY NOTICE + FOOTER
# ---------------------------------------------------------

st.markdown(
    """
    <div class="privacy-note">
        <b>Privacy & evidence notice:</b>
        HTTPS payloads are encrypted. VendorWatch observes DNS names and TLS SNI
        (which destinations were contacted), not the actual data sent.
        A network contact alone does not prove tracking, collection, sale,
        theft, or leakage. Policy conclusions require supporting policy evidence.
        Analyze only captures from your own device or authorized sample captures.
    </div>

    <div class="footer">
        VENDORWATCH &nbsp;•&nbsp; PRIVACY INTELLIGENCE &nbsp;•&nbsp; HACKATHON EDITION
    </div>
    """,
    unsafe_allow_html=True,
)
