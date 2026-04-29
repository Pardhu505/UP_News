import streamlit as st
from gnews import GNews
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import time
import random
import requests

st.set_page_config(page_title="UP News Search & Analysis", layout="wide")

# ===================== Custom CSS =====================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

    .page-header {
        text-align: center; color: #fff;
        background: linear-gradient(90deg, #1565C0, #0288D1);
        padding: 14px 20px; border-radius: 12px;
        font-size: 22px; font-weight: 700;
        letter-spacing: 0.01em; margin-bottom: 20px;
    }
    .keyword-tag {
        display: inline-block; background: #e3f2fd; color: #1565C0;
        border: 1px solid #90caf9; border-radius: 20px;
        padding: 3px 12px; margin: 3px; font-size: 13px; font-weight: 600;
    }
    .metrics-container {
        display: flex; justify-content: space-between;
        margin-bottom: 20px; gap: 15px; flex-wrap: wrap;
    }
    .metric-box {
        flex: 1; min-width: 160px; padding: 15px 20px;
        border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        text-align: center; color: white;
    }
    .metric-positive { background: linear-gradient(135deg, #43A047, #1B5E20); }
    .metric-neutral  { background: linear-gradient(135deg, #78909C, #37474F); }
    .metric-negative { background: linear-gradient(135deg, #E53935, #B71C1C); }
    .metric-non      { background: linear-gradient(135deg, #8D6E63, #4E342E); }
    .metric-total    { background: linear-gradient(135deg, #1565C0, #0D47A1); }
    .metric-value { font-size: 26px; font-weight: 700; margin-bottom: 4px; }
    .metric-label { font-size: 13px; opacity: 0.88; }

    .article-card {
        border: 1px solid #e0e0e0; border-radius: 10px;
        padding: 14px 16px; margin-bottom: 8px;
        background: #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }
    .article-title { font-size: 14.5px; font-weight: 600; color: #1565C0; }
    .article-meta  { font-size: 12px; color: #666; margin-top: 4px; }
    .article-desc  { font-size: 13px; color: #444; margin-top: 6px; line-height: 1.5; }
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
MAX_RESULTS_PER_QUERY = 100
SENTIMENT_OPTIONS = ["Unset", "Positive", "Neutral", "Negative", "Non"]
SENTIMENT_COLORS = {
    "Positive": "#2E7D32",
    "Negative": "#C62828",
    "Neutral":  "#546E7A",
    "Non":      "#6D4C41",
    "Unset":    "#9E9E9E",
}


# ===================== Session State =====================
def _init_state():
    defaults = {
        "all_results":       [],
        "seen_keys":         set(),
        "df":                pd.DataFrame(),
        "sources_list":      [],
        "selected_sources":  [],
        "has_fetched":       False,
        "keywords":          ["Akhilesh Yadav"],
        "sentiments":        {},
        "selected_articles": {},
        "summary_text":      "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            if isinstance(v, dict):
                st.session_state[k] = {}
            elif isinstance(v, set):
                st.session_state[k] = set()
            elif isinstance(v, list):
                st.session_state[k] = list(v)
            elif isinstance(v, pd.DataFrame):
                st.session_state[k] = pd.DataFrame()
            else:
                st.session_state[k] = v

_init_state()


# ===================== Helpers =====================
def reset_state():
    preserve = {"keywords"}
    for k in list(st.session_state.keys()):
        if k in preserve:
            continue
        if k in ("all_results", "sources_list", "selected_sources"):
            st.session_state[k] = []
        elif k in ("seen_keys",):
            st.session_state[k] = set()
        elif k in ("sentiments", "selected_articles"):
            st.session_state[k] = {}
        elif k == "df":
            st.session_state[k] = pd.DataFrame()
        elif k == "has_fetched":
            st.session_state[k] = False
        elif k == "summary_text":
            st.session_state[k] = ""

def normalize_publisher(pub):
    if isinstance(pub, dict):
        return pub.get("title") or pub.get("name") or ""
    return "" if pub is None else str(pub)

def add_results(results, query, lang_label):
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
            "title": title, "desc": desc, "link": url, "media": publisher,
            "published": "" if published is None else str(published),
            "query": query, "language": lang_label,
        })
        if publisher and publisher not in st.session_state.sources_list:
            st.session_state.sources_list.append(publisher)

def parse_pub_date(date_str):
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except Exception:
            pass
    return None

def fetch_one_query(query, lang_code, lang_label, days):
    gn = GNews(language=lang_code, country=COUNTRY,
               period=f"{days}d", max_results=MAX_RESULTS_PER_QUERY)
    results = gn.get_news(query) or []
    add_results(results, query=query, lang_label=lang_label)

def call_claude_summary(articles_df):
    bullet_list = "\n".join(
        f"- [{r['language']} | {r['sentiment']}] {r['title']}. {r['desc']}"
        for _, r in articles_df.iterrows()
    )
    prompt = (
        f"You are a news analyst. Below are {len(articles_df)} selected news headlines and descriptions. "
        "Write a concise 150–200 word executive summary covering the main themes, key events, "
        "and overall sentiment. Use plain English, no bullet points.\n\n"
        f"Articles:\n{bullet_list}"
    )
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        data = resp.json()
        texts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        return " ".join(texts).strip() or "No summary returned."
    except Exception as e:
        return f"Error calling Claude API: {e}"


# ===================== Sidebar =====================
with st.sidebar:
    st.header("🔍 Search Keywords")
    st.caption("Searched across EN / HI / MR.")
    kw_to_remove = None
    for kw in st.session_state.keywords:
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"<span class='keyword-tag'>{kw}</span>", unsafe_allow_html=True)
        if c2.button("✕", key=f"rm_{kw}"):
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


# ===================== Date Range & Fetch =====================
st.subheader("Date Range & Fetch")
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    from_date = st.date_input("From date", value=date.today() - timedelta(days=7), max_value=date.today())
with col2:
    to_date   = st.date_input("To date",   value=date.today(), min_value=from_date, max_value=date.today())
with col3:
    st.write(""); st.write("")
    fetch_btn = st.button("🚀 Fetch News", type="primary", use_container_width=True)

days_from_today = max(1, (date.today() - from_date).days + 1)

if fetch_btn:
    if not st.session_state.keywords:
        st.error("Please add at least one keyword in the sidebar.")
    else:
        reset_state()
        st.session_state.has_fetched = True
        total_steps = len(st.session_state.keywords) * len(LANGS)
        progress = st.progress(0); status = st.empty(); step = 0
        with st.spinner("Fetching articles…"):
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
        status.empty(); progress.empty()
        raw_df = pd.DataFrame(st.session_state.all_results)
        if not raw_df.empty:
            raw_df = raw_df.drop_duplicates(subset=["title", "media", "link"]).reset_index(drop=True)
        st.session_state.df = raw_df
        # Init per-article state
        for idx in raw_df.index:
            st.session_state.sentiments[idx]        = "Unset"
            st.session_state.selected_articles[idx] = False


# ===================== Display =====================
if not st.session_state.df.empty:
    display_df = st.session_state.df.copy()

    # Date filter
    display_df["pub_date"] = display_df["published"].apply(parse_pub_date)
    has_date = display_df["pub_date"].notna()
    in_range = display_df["pub_date"].ge(from_date) & display_df["pub_date"].le(to_date)
    display_df = display_df[~has_date | in_range].copy()

    # Source filter
    st.subheader("Filter by Source")
    st.session_state.selected_sources = st.multiselect(
        "Select news sources (leave blank for all)",
        options=sorted(st.session_state.sources_list), default=[],
    )
    if st.session_state.selected_sources:
        display_df = display_df[display_df["media"].isin(st.session_state.selected_sources)].copy()

    total_count = len(display_df)
    st.success(
        f"**{total_count}** articles  |  "
        f"{from_date.strftime('%d %b %Y')} → {to_date.strftime('%d %b %Y')}"
    )

    # ── Pagination ─────────────────────────────────────────────
    PAGE_SIZE   = 25
    total_pages = max(1, (total_count - 1) // PAGE_SIZE + 1)
    page = st.number_input(f"Page (1–{total_pages})", min_value=1, max_value=total_pages, value=1, step=1)
    page_indices = display_df.index.tolist()[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    # ── Article list header ─────────────────────────────────────
    st.subheader(f"Search Results — Page {page} of {total_pages}")

    # Select-all for current page
    if st.checkbox(f"☑️ Select all {len(page_indices)} articles on this page", key=f"selall_{page}"):
        for idx in page_indices:
            st.session_state.selected_articles[idx] = True

    st.markdown("---")

    # ── Render each article as a card ──────────────────────────
    for idx in page_indices:
        row = display_df.loc[idx]

        if idx not in st.session_state.sentiments:
            st.session_state.sentiments[idx] = "Unset"
        if idx not in st.session_state.selected_articles:
            st.session_state.selected_articles[idx] = False

        c_check, c_content, c_sent = st.columns([0.5, 8, 2])

        with c_check:
            checked = st.checkbox(
                "", value=st.session_state.selected_articles.get(idx, False),
                key=f"chk_{idx}"
            )
            st.session_state.selected_articles[idx] = checked

        with c_content:
            title_link = (
                f"<a href='{row['link']}' target='_blank' class='article-title'>{row['title']}</a>"
                if row["link"] else f"<span class='article-title'>{row['title']}</span>"
            )
            meta = (
                f"<div class='article-meta'>"
                f"📰 <b>{row['media']}</b> &nbsp;|&nbsp; "
                f"🕒 {row['published']} &nbsp;|&nbsp; "
                f"🌐 {row['language']} &nbsp;|&nbsp; "
                f"🔑 {row['query']}"
                f"</div>"
            )
            desc = f"<div class='article-desc'>{row['desc']}</div>" if row["desc"] else ""
            st.markdown(
                f"<div class='article-card'>{title_link}{meta}{desc}</div>",
                unsafe_allow_html=True,
            )

        with c_sent:
            st.write("")
            cur = st.session_state.sentiments.get(idx, "Unset")
            new_sent = st.selectbox(
                "Sentiment",
                options=SENTIMENT_OPTIONS,
                index=SENTIMENT_OPTIONS.index(cur),
                key=f"sent_{idx}",
                label_visibility="collapsed",
            )
            st.session_state.sentiments[idx] = new_sent
            color = SENTIMENT_COLORS.get(new_sent, "#9E9E9E")
            st.markdown(
                f"<div style='text-align:center;color:{color};"
                f"font-weight:700;font-size:13px;margin-top:4px;'>● {new_sent}</div>",
                unsafe_allow_html=True,
            )

    # ── Sync sentiment & selection back to display_df ───────────
    display_df["sentiment"] = display_df.index.map(
        lambda i: st.session_state.sentiments.get(i, "Unset")
    )
    display_df["selected"] = display_df.index.map(
        lambda i: st.session_state.selected_articles.get(i, False)
    )
    selected_rows = display_df[display_df["selected"] == True]
    n_selected    = len(selected_rows)

    # ── Action bar: Download CSV | Generate Summary ─────────────
    st.divider()
    ab1, ab2, ab3 = st.columns([3, 3, 4])

    with ab1:
        dl_df = display_df[[
            "title", "media", "published", "language", "query", "desc", "link", "sentiment"
        ]].copy().rename(columns={
            "title": "Title", "media": "Source", "published": "Published",
            "language": "Language", "query": "Keyword",
            "desc": "Description", "link": "URL", "sentiment": "Sentiment",
        })
        csv_bytes = dl_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 Download CSV", data=csv_bytes,
            file_name=f"news_{from_date.strftime('%Y%m%d')}_to_{to_date.strftime('%Y%m%d')}.csv",
            mime="text/csv", key="dl-csv",
        )

    with ab2:
        gen_btn = st.button(
            f"✨ Generate Summary ({n_selected} selected)",
            type="primary",
            disabled=(n_selected == 0),
            key="gen_btn",
        )

    with ab3:
        if n_selected > 0:
            st.caption(f"ℹ️ {n_selected} article(s) selected across all pages.")
        else:
            st.caption("☑️ Check articles above to enable summary generation.")

    if gen_btn and n_selected > 0:
        with st.spinner(f"Generating AI summary for {n_selected} articles…"):
            st.session_state.summary_text = call_claude_summary(selected_rows)

    if st.session_state.summary_text:
        st.subheader("📋 Generated Summary")
        st.info(st.session_state.summary_text)
        st.download_button(
            "📄 Download Summary as TXT",
            data=st.session_state.summary_text.encode("utf-8"),
            file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain", key="dl-summary",
        )

    # ── Overall Tone Summary (manual sentiments) ─────────────────
    st.subheader("Overall Tone Summary")
    st.caption("Reflects your manual sentiment selections — updates live as you tag articles.")

    counts = display_df["sentiment"].value_counts().reindex(
        ["Positive", "Neutral", "Negative", "Non", "Unset"], fill_value=0
    )
    metric_html = f"""
    <div class="metrics-container">
        <div class="metric-box metric-positive">
            <div class="metric-value">{int(counts['Positive'])}</div>
            <div class="metric-label">✅ Positive</div>
        </div>
        <div class="metric-box metric-neutral">
            <div class="metric-value">{int(counts['Neutral'])}</div>
            <div class="metric-label">➖ Neutral</div>
        </div>
        <div class="metric-box metric-negative">
            <div class="metric-value">{int(counts['Negative'])}</div>
            <div class="metric-label">❌ Negative</div>
        </div>
        <div class="metric-box metric-non">
            <div class="metric-value">{int(counts['Non'])}</div>
            <div class="metric-label">🔵 Non (HI/MR)</div>
        </div>
        <div class="metric-box metric-total">
            <div class="metric-value">{total_count}</div>
            <div class="metric-label">📰 Total Articles</div>
        </div>
    </div>
    """
    st.markdown(metric_html, unsafe_allow_html=True)

    labelled = display_df[display_df["sentiment"] != "Unset"]
    if not labelled.empty:
        col_pie, col_bar = st.columns(2)
        with col_pie:
            pc = labelled["sentiment"].value_counts().reindex(
                ["Positive", "Neutral", "Negative", "Non"], fill_value=0
            )
            pie = px.pie(
                names=pc.index, values=pc.values,
                title="Sentiment Distribution (labelled only)",
                hole=0.55, color=pc.index,
                color_discrete_map={
                    "Positive": "#43A047", "Neutral": "#78909C",
                    "Negative": "#E53935", "Non": "#8D6E63",
                },
            )
            pie.update_traces(textinfo="percent+label")
            st.plotly_chart(pie, use_container_width=True)

        with col_bar:
            lc = display_df["language"].value_counts().reset_index()
            lc.columns = ["Language", "Count"]
            bar = px.bar(lc, x="Language", y="Count", title="Articles by Language",
                         color="Language",
                         color_discrete_sequence=["#1565C0", "#E65100", "#2E7D32"])
            bar.update_layout(showlegend=False)
            st.plotly_chart(bar, use_container_width=True)
    else:
        st.info("Tag articles with a sentiment above to see the distribution chart.")

    if len(st.session_state.keywords) > 1:
        kc = display_df["query"].value_counts().reset_index()
        kc.columns = ["Keyword", "Count"]
        kf = px.bar(kc, x="Keyword", y="Count", title="Articles per Keyword",
                    color="Count", color_continuous_scale="Blues")
        st.plotly_chart(kf, use_container_width=True)

elif st.session_state.has_fetched:
    st.warning("No articles found for the selected filters and date range.")
else:
    st.info("👈 Add keywords in the sidebar, set your date range, then click **Fetch News**.")
