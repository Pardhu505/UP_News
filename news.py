import streamlit as st
from gnews import GNews
import pandas as pd
from textblob import TextBlob
from datetime import datetime, date, timedelta
import plotly.express as px
import time
import random
import nltk

nltk.download("punkt", quiet=True)
nltk.download("brown", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("averaged_perceptron_tagger", quiet=True)
nltk.download("conll2000", quiet=True)
nltk.download("movie_reviews", quiet=True)

st.set_page_config(page_title="UP News Search & Analysis", layout="wide")

# ===================== Custom CSS =====================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

    .news-table {
        font-family: 'Sora', sans-serif;
        border-collapse: collapse;
        width: 100%;
        font-size: 13.5px;
    }
    .news-table td, .news-table th {
        border: 1px solid #e0e0e0;
        padding: 9px 11px;
        vertical-align: top;
    }
    .news-table tr:nth-child(even) { background-color: #f7f9fc; }
    .news-table tr:hover { background-color: #eaf1fb; }
    .news-table th {
        padding-top: 12px;
        padding-bottom: 12px;
        text-align: left;
        background: linear-gradient(90deg, #1565C0, #0288D1);
        color: white;
        letter-spacing: 0.03em;
    }

    .metrics-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
        gap: 15px;
        flex-wrap: wrap;
    }
    .metric-box {
        flex: 1;
        min-width: 160px;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        text-align: center;
        color: white;
    }
    .metric-positive { background: linear-gradient(135deg, #43A047, #1B5E20); }
    .metric-neutral  { background: linear-gradient(135deg, #78909C, #37474F); }
    .metric-negative { background: linear-gradient(135deg, #E53935, #B71C1C); }
    .metric-non      { background: linear-gradient(135deg, #8D6E63, #4E342E); }
    .metric-total    { background: linear-gradient(135deg, #1565C0, #0D47A1); }
    .metric-value { font-size: 26px; font-weight: 700; margin-bottom: 4px; }
    .metric-label { font-size: 13px; opacity: 0.88; }

    .keyword-tag {
        display: inline-block;
        background: #e3f2fd;
        color: #1565C0;
        border: 1px solid #90caf9;
        border-radius: 20px;
        padding: 3px 12px;
        margin: 3px;
        font-size: 13px;
        font-weight: 600;
    }

    .page-header {
        text-align: center;
        color: #fff;
        background: linear-gradient(90deg, #1565C0, #0288D1);
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 0.01em;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='page-header'>📰 UP News Search and Analysis Portal</div>",
    unsafe_allow_html=True,
)

# ===================== Constants =====================
LANGS = [("English", "en"), ("Hindi", "hi"), ("Marathi", "mr")]
COUNTRY = "IN"
MAX_RESULTS_PER_QUERY = 100   # high ceiling — fetch as many as GNews allows


# ===================== Session State =====================
defaults = {
    "all_results": [],
    "seen_keys": set(),
    "df": pd.DataFrame(),
    "sources_list": [],
    "selected_sources": [],
    "has_fetched": False,
    "keywords": ["Akhilesh Yadav"],   # default seed keyword
    "new_kw_input": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ===================== Helpers =====================
def reset_state():
    for k, v in defaults.items():
        if k not in ("keywords",):   # preserve user's keyword list
            st.session_state[k] = v if not isinstance(v, (set, list, dict)) else type(v)()
    st.session_state["df"] = pd.DataFrame()

def normalize_publisher(pub):
    if isinstance(pub, dict):
        return pub.get("title") or pub.get("name") or ""
    return "" if pub is None else str(pub)

def add_results(results, query: str, lang_label: str):
    for item in results:
        title     = (item.get("title") or "").strip()
        desc      = (item.get("description") or "").strip()
        url       = (item.get("url") or "").strip()
        publisher = normalize_publisher(item.get("publisher"))
        published = item.get("published date")

        key = f"{title}||{publisher}||{url}"
        if not title or key in st.session_state.seen_keys:
            continue
        st.session_state.seen_keys.add(key)

        st.session_state.all_results.append({
            "title":     title,
            "desc":      desc,
            "link":      url,
            "media":     publisher,
            "published": "" if published is None else str(published),
            "query":     query,
            "language":  lang_label,
        })
        if publisher and publisher not in st.session_state.sources_list:
            st.session_state.sources_list.append(publisher)

def parse_pub_date(date_str: str):
    """Try to parse a published date string into a date object."""
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except Exception:
            pass
    return None

def fetch_one_query(query: str, lang_code: str, lang_label: str, days: int):
    gn = GNews(
        language=lang_code,
        country=COUNTRY,
        period=f"{days}d",
        max_results=MAX_RESULTS_PER_QUERY,
    )
    results = gn.get_news(query) or []
    add_results(results, query=query, lang_label=lang_label)


# ===================== Sidebar — Keyword Manager =====================
with st.sidebar:
    st.header("🔍 Search Keywords")
    st.caption("Add or remove keywords. These are searched across EN / HI / MR.")

    # Show existing keywords as removable tags
    kw_to_remove = None
    for kw in st.session_state.keywords:
        col1, col2 = st.columns([4, 1])
        col1.markdown(f"<span class='keyword-tag'>{kw}</span>", unsafe_allow_html=True)
        if col2.button("✕", key=f"rm_{kw}"):
            kw_to_remove = kw
    if kw_to_remove:
        st.session_state.keywords.remove(kw_to_remove)
        st.rerun()

    new_kw = st.text_input("Add keyword / phrase", placeholder="e.g. Yogi Adityanath")
    if st.button("➕ Add Keyword") and new_kw.strip():
        kw_clean = new_kw.strip()
        if kw_clean not in st.session_state.keywords:
            st.session_state.keywords.append(kw_clean)
        st.rerun()

    st.divider()
    st.caption("📌 Languages: English · Hindi · Marathi  |  Country: India")


# ===================== Main — Filters =====================
st.subheader("Date Range & Fetch")

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    from_date = st.date_input(
        "From date",
        value=date.today() - timedelta(days=7),
        max_value=date.today(),
    )
with col2:
    to_date = st.date_input(
        "To date",
        value=date.today(),
        min_value=from_date,
        max_value=date.today(),
    )
with col3:
    st.write("")   # spacer
    st.write("")
    fetch_btn = st.button("🚀 Fetch News", type="primary", use_container_width=True)

# Compute days span for GNews period param
days_span = max(1, (to_date - from_date).days + 1)
# GNews period goes back N days from today, so we use days from today → from_date
days_from_today = max(1, (date.today() - from_date).days + 1)


# ===================== Fetch Runner =====================
if fetch_btn:
    if not st.session_state.keywords:
        st.error("Please add at least one keyword in the sidebar.")
    else:
        reset_state()
        st.session_state.has_fetched = True

        total_steps = len(st.session_state.keywords) * len(LANGS)
        progress = st.progress(0)
        status   = st.empty()
        step     = 0

        with st.spinner("Fetching articles across all keywords & languages…"):
            for q in st.session_state.keywords:
                for (lang_label, lang_code) in LANGS:
                    step += 1
                    status.write(f"🔎 [{step}/{total_steps}]  {lang_label}  →  **{q}**")
                    try:
                        fetch_one_query(q, lang_code=lang_code, lang_label=lang_label, days=days_from_today)
                    except Exception as e:
                        st.warning(f"Failed for '{q}' ({lang_label}): {e}")
                    progress.progress(step / total_steps)
                    time.sleep(random.uniform(0.15, 0.35))

        status.empty()
        progress.empty()

        st.session_state.df = pd.DataFrame(st.session_state.all_results)
        if not st.session_state.df.empty:
            st.session_state.df = (
                st.session_state.df
                .drop_duplicates(subset=["title", "media", "link"])
                .reset_index(drop=True)
            )


# ===================== Display =====================
if not st.session_state.df.empty:
    display_df = st.session_state.df.copy()

    # ── Date range filter ──────────────────────────────────────────
    display_df["pub_date"] = display_df["published"].apply(parse_pub_date)

    # Filter rows that have a parseable date within the selected range
    has_date_mask = display_df["pub_date"].notna()
    in_range_mask = (
        display_df["pub_date"].ge(from_date) &
        display_df["pub_date"].le(to_date)
    )
    # Keep articles within range OR those with unparseable dates (don't silently drop them)
    display_df = display_df[~has_date_mask | in_range_mask].copy()

    # ── Source filter ──────────────────────────────────────────────
    st.subheader("Filter by Source")
    st.session_state.selected_sources = st.multiselect(
        "Select news sources to display (leave blank for all)",
        options=sorted(st.session_state.sources_list),
        default=[],
    )
    if st.session_state.selected_sources:
        display_df = display_df[display_df["media"].isin(st.session_state.selected_sources)].copy()

    # ── Sentiment ─────────────────────────────────────────────────
    display_df["polarity"]  = None
    display_df["sentiment"] = "Non"

    mask_en = display_df["language"].eq("English")
    display_df.loc[mask_en, "polarity"] = (
        display_df.loc[mask_en, "title"].fillna("") + ". " +
        display_df.loc[mask_en, "desc"].fillna("")
    ).apply(lambda x: TextBlob(str(x)).sentiment.polarity)

    display_df.loc[mask_en, "sentiment"] = display_df.loc[mask_en, "polarity"].apply(
        lambda x: "Positive" if x > 0 else ("Negative" if x < 0 else "Neutral")
    )

    sentiment_colors = {
        "Positive": "#2E7D32",
        "Negative": "#C62828",
        "Neutral":  "#546E7A",
        "Non":      "#6D4C41",
    }

    total_count = len(display_df)
    st.success(
        f"**{total_count}** articles found  |  "
        f"Date range: {from_date.strftime('%d %b %Y')} → {to_date.strftime('%d %b %Y')}"
    )

    # ── Pagination ────────────────────────────────────────────────
    PAGE_SIZE = 50
    total_pages = max(1, (total_count - 1) // PAGE_SIZE + 1)
    page = st.number_input(
        f"Page (1 – {total_pages})", min_value=1, max_value=total_pages, value=1, step=1
    )
    page_df = display_df.iloc[(page - 1) * PAGE_SIZE : page * PAGE_SIZE].copy()

    # ── Build HTML table ──────────────────────────────────────────
    page_df["Sentiment_html"] = page_df["sentiment"].apply(
        lambda x: f"<span style='color:{sentiment_colors.get(x,'black')};font-weight:600'>{x}</span>"
    )
    page_df["Title_html"] = page_df.apply(
        lambda row: (
            f"<a href='{row['link']}' target='_blank'>{row['title']}</a>"
            if row["link"] else row["title"]
        ),
        axis=1,
    )

    table_df = page_df[[
        "Title_html", "media", "published", "language", "query", "desc", "Sentiment_html"
    ]].rename(columns={
        "Title_html":    "Title",
        "media":         "Source",
        "published":     "Published",
        "language":      "Language",
        "query":         "Keyword",
        "desc":          "Description",
        "Sentiment_html": "Sentiment",
    })

    st.subheader(f"Search Results — Page {page} of {total_pages}")
    st.markdown(
        table_df.to_html(escape=False, index=False, classes="news-table"),
        unsafe_allow_html=True,
    )

    # ── CSV download (full filtered set) ─────────────────────────
    download_df = display_df[[
        "title", "media", "published", "language", "query", "desc", "link", "sentiment"
    ]].copy().rename(columns={
        "title":     "Title",
        "media":     "Source",
        "published": "Published",
        "language":  "Language",
        "query":     "Keyword",
        "desc":      "Description",
        "link":      "URL",
        "sentiment": "Sentiment",
    })

    csv_bytes = download_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Download All Results as CSV",
        data=csv_bytes,
        file_name=(
            f"news_{from_date.strftime('%Y%m%d')}_to_{to_date.strftime('%Y%m%d')}"
            f"_{datetime.now().strftime('%H%M')}.csv"
        ),
        mime="text/csv",
        key="download-csv",
    )

    # ── Charts ────────────────────────────────────────────────────
    st.subheader("Overall Tone Summary")

    counts = display_df["sentiment"].value_counts().reindex(
        ["Positive", "Neutral", "Negative", "Non"], fill_value=0
    )

    metric_html = f"""
    <div class="metrics-container">
        <div class="metric-box metric-positive">
            <div class="metric-value">{int(counts['Positive'])}</div>
            <div class="metric-label">Positive (EN)</div>
        </div>
        <div class="metric-box metric-neutral">
            <div class="metric-value">{int(counts['Neutral'])}</div>
            <div class="metric-label">Neutral (EN)</div>
        </div>
        <div class="metric-box metric-negative">
            <div class="metric-value">{int(counts['Negative'])}</div>
            <div class="metric-label">Negative (EN)</div>
        </div>
        <div class="metric-box metric-non">
            <div class="metric-value">{int(counts['Non'])}</div>
            <div class="metric-label">Non (HI/MR)</div>
        </div>
        <div class="metric-box metric-total">
            <div class="metric-value">{total_count}</div>
            <div class="metric-label">Total Articles</div>
        </div>
    </div>
    """
    st.markdown(metric_html, unsafe_allow_html=True)

    col_pie, col_bar = st.columns(2)

    with col_pie:
        pie_fig = px.pie(
            names=counts.index,
            values=counts.values,
            title="Sentiment Distribution",
            hole=0.55,
            color=counts.index,
            color_discrete_map={
                "Positive": "#43A047",
                "Neutral":  "#78909C",
                "Negative": "#E53935",
                "Non":      "#8D6E63",
            },
        )
        pie_fig.update_traces(textinfo="percent+label")
        st.plotly_chart(pie_fig, use_container_width=True)

    with col_bar:
        lang_counts = display_df["language"].value_counts().reset_index()
        lang_counts.columns = ["Language", "Count"]
        bar_fig = px.bar(
            lang_counts,
            x="Language",
            y="Count",
            title="Articles by Language",
            color="Language",
            color_discrete_sequence=["#1565C0", "#E65100", "#2E7D32"],
        )
        bar_fig.update_layout(showlegend=False)
        st.plotly_chart(bar_fig, use_container_width=True)

    # Keyword breakdown
    if len(st.session_state.keywords) > 1:
        kw_counts = display_df["query"].value_counts().reset_index()
        kw_counts.columns = ["Keyword", "Count"]
        kw_fig = px.bar(
            kw_counts, x="Keyword", y="Count",
            title="Articles per Keyword",
            color="Count",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(kw_fig, use_container_width=True)

elif st.session_state.has_fetched:
    st.warning("No articles found for the selected filters and date range.")
else:
    st.info("👈 Add keywords in the sidebar, set your date range above, then click **Fetch News**.")
