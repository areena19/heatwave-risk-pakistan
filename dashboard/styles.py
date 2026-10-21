"""Custom Glassmorphic Theme & CSS for PakHeat Platform."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    max-width: 1320px;
}
/* Executive Header */
.brand-banner {
    background: linear-gradient(135deg, #09172A 0%, #11294D 60%, #B83B26 100%);
    border-radius: 16px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.5rem;
    color: #ffffff;
    box-shadow: 0 10px 25px -5px rgba(11, 31, 58, 0.25);
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.brand-title { font-size: 1.75rem; font-weight: 800; margin: 0; line-height: 1.2; }
.brand-subtitle { font-size: 0.92rem; color: #cbd5e1; margin-top: 0.35rem; }
.system-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 999px;
    padding: 0.35rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: #f8fafc;
}
.pulse-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background-color: #10b981;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3);
}

/* Metric Cards */
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
}
.metric-label { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 0.4rem; }
.metric-value { font-size: 2rem; font-weight: 800; color: #0f172a; line-height: 1.1; }
.metric-sub { font-size: 0.82rem; font-weight: 500; margin-top: 0.45rem; }

/* Custom Seamless Dark Tabs */
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(15, 23, 42, 0.65) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    padding: 6px;
    border-radius: 12px;
    backdrop-filter: blur(12px);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 9px 20px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    color: #94a3b8 !important;
    background: transparent !important;
    border: 1px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0.07) 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border: 1px solid rgba(255, 255, 255, 0.22) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
}

/* Risk Badges */
.risk-pill { display: inline-flex; align-items: center; gap: 8px; padding: 0.45rem 1rem; border-radius: 8px; font-weight: 700; font-size: 0.95rem; }
.risk-normal { background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }
.risk-caution { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }
.risk-extreme-caution { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.risk-danger { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }

.app-footer {
    margin-top: 3.5rem; padding-top: 1.2rem;
    border-top: 1px solid #e2e8f0; font-size: 0.82rem; color: #64748b;
    display: flex; justify-content: space-between; align-items: center;
}
</style>
"""