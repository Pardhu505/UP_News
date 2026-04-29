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
        font-size: 22px; font-weight: 700; letter-spacing: 0.01em; margin-bottom: 20px;
    }
    .keyword-tag {
        display: inline-block; background: #e3f2fd; color: #1565C0;
        border: 1px solid #90caf9; border-radius: 20px;
        padding: 3px 12px; margin: 3px; font-size: 13px; font-weight: 600;
    }

    /* ── Table wrapper — outer border ── */
    .tbl-wrap {
        border: 1.5px solid #b0c4de;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 8px;
    }

    /* ── Table header row ── */
    .tbl-header {
        display: grid;
        grid-template-columns: 38px 40px 3fr 1.1fr 1.3fr 0.8fr 0.9fr 1.5fr;
        background: linear-gradient(90deg, #1565C0, #0288D1);
        color: #fff; font-weight: 700; font-size: 12.5px;
        letter-spacing: 0.03em;
        align-items: center;
        border-bottom: 2px solid #0d47a1;
    }
    .tbl-header > div {
        padding: 10px 8px;
        border-right: 1px solid rgba(255,255,255,0.25);
        text-align: center;
    }
    .tbl-header > div:last-child { border-right: none; }

    /* ── Streamlit column rows — borders via adjacent divs ── */
    /* Each row rendered with st.columns gets a bottom border */
    div[data-testid="stHorizontalBlock"].tbl-data-row {
        border-bottom: 1px solid #dce6f0 !important;
    }

    /* Cell style applied to inner markdown divs */
    .tbl-cell {
        padding: 9px 8px;
        min-height: 48px;
        display: flex;
        align-items: center;        /* vertical middle */
        word-break: break-word;
        line-height: 1.45;
        border-right: 1px solid #dce6f0;
        height: 100%;
        box-sizing: border-box;
    }
    .tbl-cell:last-child { border-right: none; }

    /* Title cell keeps top-align since it can be multi-line */
    .tbl-cell-title {
        padding: 9px 8px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        word-break: break-word;
        line-height: 1.45;
        border-right: 1px solid #dce6f0;
        box-sizing: border-box;
    }

    /* Overall tone metrics */
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
    .metric-total    { background: linear-gradient(135deg, #1565C0, #0D47A1); }
    .metric-value { font-size: 26px; font-weight: 700; margin-bottom: 4px; }
    .metric-label { font-size: 13px; opacity: 0.88; }

    /* Remove default Streamlit column gap so grid columns touch */
    div[data-testid="stHorizontalBlock"] { gap: 0 !important; }
    /* Remove padding from column containers inside table rows */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        padding: 0 !important;
        border-right: 1px solid #dce6f0;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
        border-right: none;
    }
    /* Ensure even row striping via row wrapper */
    .tbl-even-row > div[data-testid="stHorizontalBlock"] { background: #f7f9fc; }
    .tbl-odd-row  > div[data-testid="stHorizontalBlock"] { background: #ffffff; }
    /* Checkbox centering */
    div[data-testid="stCheckbox"] { display:flex; justify-content:center; align-items:center; padding: 8px 0; }
    /* Selectbox spacing reset */
    div[data-testid="stSelectbox"] { margin-top: 4px !important; margin-bottom: 2px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='page-header'>📰 UP News Search and Analysis Portal</div>",
    unsafe_allow_html=True,
)

# ===================== Constants =====================
LANGS             = [("English", "en"), ("Hindi", "hi"), ("Marathi", "mr")]
COUNTRY           = "IN"
MAX_RESULTS       = 100
SENTIMENT_OPTIONS = ["—", "Positive", "Neutral", "Negative"]
SENTIMENT_COLORS  = {"Positive": "#2E7D32", "Negative": "#C62828",
                     "Neutral": "#546E7A", "—": "#9E9E9E"}


# ===================== Session State =====================
def _init():
    defs = {
        "all_results": [], "seen_keys": set(), "df": pd.DataFrame(),
        "sources_list": [], "selected_sources": [], "has_fetched": False,
        "keywords": ["Akhilesh Yadav"],
        "sentiments": {}, "selected_articles": {}, "summary_text": "",
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = (
                pd.DataFrame() if isinstance(v, pd.DataFrame)
                else set() if isinstance(v, set)
                else list(v) if isinstance(v, list)
                else dict(v) if isinstance(v, dict)
                else v
            )
_init()


# ===================== Helpers =====================
def reset_state():
    for k in ["all_results", "sources_list", "selected_sources"]:
        st.session_state[k] = []
    for k in ["sentiments", "selected_articles"]:
        st.session_state[k] = {}
    st.session_state["seen_keys"]    = set()
    st.session_state["df"]           = pd.DataFrame()
    st.session_state["has_fetched"]  = False
    st.session_state["summary_text"] = ""

def norm_pub(pub):
    if isinstance(pub, dict): return pub.get("title") or pub.get("name") or ""
    return "" if pub is None else str(pub)

def add_results(results, query, lang_label):
    for item in results:
        title = (item.get("title") or "").strip()
        desc  = (item.get("description") or "").strip()
        url   = (item.get("url") or "").strip()
        pub   = norm_pub(item.get("publisher"))
        published = item.get("published date")
        key = f"{title}||{pub}||{url}"
        if not title or key in st.session_state.seen_keys:
            continue
        st.session_state.seen_keys.add(key)
        st.session_state.all_results.append({
            "title": title, "desc": desc, "link": url, "media": pub,
            "published": "" if published is None else str(published),
            "query": query, "language": lang_label,
        })
        if pub and pub not in st.session_state.sources_list:
            st.session_state.sources_list.append(pub)

def parse_date(s):
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try: return datetime.strptime(s.strip(), fmt).date()
        except: pass
    return None

def fetch_one(query, lang_code, lang_label, days):
    gn = GNews(language=lang_code, country=COUNTRY,
               period=f"{days}d", max_results=MAX_RESULTS)
    add_results(gn.get_news(query) or [], query=query, lang_label=lang_label)

def claude_summary(articles_df):
    bullets = "\n".join(
        f"- [{r['language']} | {r['sentiment']}] {r['title']}. {r['desc']}"
        for _, r in articles_df.iterrows()
    )
    prompt = (
        f"You are a news analyst. Below are {len(articles_df)} selected headlines and descriptions. "
        "Write a concise 150–200 word executive summary of main themes, key events, and overall "
        "sentiment. Plain English, no bullet points.\n\nArticles:\n" + bullets
    )
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 1000,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        data = r.json()
        return " ".join(b["text"] for b in data.get("content", [])
                        if b.get("type") == "text").strip() or "No summary returned."
    except Exception as e:
        return f"Error: {e}"


# ===================== Sidebar =====================
with st.sidebar:
    st.header("🔍 Search Keywords")
    st.caption("Searched across EN / HI / MR.")
    kw_rm = None
    for kw in st.session_state.keywords:
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"<span class='keyword-tag'>{kw}</span>", unsafe_allow_html=True)
        if c2.button("✕", key=f"rm_{kw}"): kw_rm = kw
    if kw_rm:
        st.session_state.keywords.remove(kw_rm); st.rerun()
    nkw = st.text_input("Add keyword / phrase", placeholder="e.g. Yogi Adityanath")
    if st.button("➕ Add Keyword") and nkw.strip():
        if nkw.strip() not in st.session_state.keywords:
            st.session_state.keywords.append(nkw.strip()); st.rerun()
    st.divider()
    st.caption("📌 Languages: English · Hindi · Marathi  |  Country: India")


# ===================== Date Range & Fetch =====================
st.subheader("Date Range & Fetch")
c1, c2, c3 = st.columns([2, 2, 2])
with c1: from_date = st.date_input("From date", value=date.today()-timedelta(days=7), max_value=date.today())
with c2: to_date   = st.date_input("To date",   value=date.today(), min_value=from_date, max_value=date.today())
with c3:
    st.write(""); st.write("")
    fetch_btn = st.button("🚀 Fetch News", type="primary", use_container_width=True)

days_back = max(1, (date.today() - from_date).days + 1)

if fetch_btn:
    if not st.session_state.keywords:
        st.error("Add at least one keyword in the sidebar.")
    else:
        reset_state()
        st.session_state.has_fetched = True
        total = len(st.session_state.keywords) * len(LANGS)
        prog = st.progress(0); stat = st.empty(); step = 0
        with st.spinner("Fetching…"):
            for q in st.session_state.keywords:
                for (ll, lc) in LANGS:
                    step += 1
                    stat.write(f"🔎 [{step}/{total}]  {ll}  →  **{q}**")
                    try: fetch_one(q, lc, ll, days_back)
                    except Exception as e: st.warning(f"Failed '{q}' ({ll}): {e}")
                    prog.progress(step / total)
                    time.sleep(random.uniform(0.15, 0.35))
        stat.empty(); prog.empty()
        raw = pd.DataFrame(st.session_state.all_results)
        if not raw.empty:
            raw = raw.drop_duplicates(subset=["title","media","link"]).reset_index(drop=True)
        st.session_state.df = raw
        for idx in raw.index:
            st.session_state.sentiments[idx]        = "—"
            st.session_state.selected_articles[idx] = False


# ===================== Display =====================
if not st.session_state.df.empty:
    df = st.session_state.df.copy()

    # Date filter
    df["pub_date"] = df["published"].apply(parse_date)
    hd = df["pub_date"].notna()
    ir = df["pub_date"].ge(from_date) & df["pub_date"].le(to_date)
    df = df[~hd | ir].copy()

    # Source filter
    st.subheader("Filter by Source")
    st.session_state.selected_sources = st.multiselect(
        "Select news sources (blank = all)",
        options=sorted(st.session_state.sources_list), default=[],
    )
    if st.session_state.selected_sources:
        df = df[df["media"].isin(st.session_state.selected_sources)].copy()

    total_count = len(df)
    st.success(
        f"**{total_count}** articles  |  "
        f"{from_date.strftime('%d %b %Y')} → {to_date.strftime('%d %b %Y')}"
    )

    # Pagination
    PAGE_SIZE   = 25
    total_pages = max(1, (total_count - 1) // PAGE_SIZE + 1)
    page = st.number_input(f"Page (1–{total_pages})", min_value=1, max_value=total_pages, value=1, step=1)
    page_indices = df.index.tolist()[(page-1)*PAGE_SIZE : page*PAGE_SIZE]

    st.subheader(f"Search Results — Page {page} of {total_pages}")

    # Select-all checkbox
    sel_all = st.checkbox(f"☑️ Select all {len(page_indices)} articles on this page", key=f"selall_{page}")
    if sel_all:
        for idx in page_indices:
            st.session_state.selected_articles[idx] = True

    # ── TABLE HEADER (pure HTML) ──────────────────────────────────
    st.markdown("""
    <div class="tbl-wrap">
    <div class="tbl-header">
      <div style="text-align:center;">✓</div>
      <div style="text-align:center;">#</div>
      <div>Title &amp; Description</div>
      <div style="text-align:center;">Source</div>
      <div style="text-align:center;">Published</div>
      <div style="text-align:center;">Language</div>
      <div style="text-align:center;">Keyword</div>
      <div style="text-align:center;">Sentiment</div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # ── TABLE ROWS (one st.columns per row) ───────────────────────
    # ✓ | # | Title+Desc | Source | Published | Lang | Keyword | Sent-dropdown
    COL_WIDTHS = [0.4, 0.4, 3.2, 1.1, 1.3, 0.8, 0.9, 1.5]

    for row_num, idx in enumerate(page_indices):
        row = df.loc[idx]

        if idx not in st.session_state.sentiments:
            st.session_state.sentiments[idx] = "—"
        if idx not in st.session_state.selected_articles:
            st.session_state.selected_articles[idx] = False

        # Alternating row background
        bg = "#f7f9fc" if row_num % 2 == 0 else "#ffffff"
        border_style = "border-bottom:1px solid #dce6f0; border-left:1.5px solid #b0c4de; border-right:1.5px solid #b0c4de;"
        if row_num == len(page_indices) - 1:
            border_style += "border-bottom:1.5px solid #b0c4de;"

        st.markdown(
            f"<div style='background:{bg};{border_style}'></div>",
            unsafe_allow_html=True,
        )

        cols = st.columns(COL_WIDTHS)

        # ① Checkbox — centred
        with cols[0]:
            st.markdown(f"<div style='background:{bg};height:100%;'></div>", unsafe_allow_html=True)
            checked = st.checkbox(
                "", value=st.session_state.selected_articles.get(idx, False),
                key=f"chk_{idx}", label_visibility="collapsed"
            )
            st.session_state.selected_articles[idx] = checked

        # ② Row number — centred
        with cols[1]:
            st.markdown(
                f"<div class='tbl-cell' style='background:{bg};justify-content:center;"
                f"font-size:12px;color:#888;'>"
                f"{(page-1)*PAGE_SIZE + row_num + 1}</div>",
                unsafe_allow_html=True,
            )

        # ③ Title + Description — left aligned, vertically centred
        with cols[2]:
            title_html = (
                f"<a href='{row['link']}' target='_blank' "
                f"style='color:#1565C0;font-weight:600;font-size:13.5px;"
                f"text-decoration:none;line-height:1.4;'>{row['title']}</a>"
                if row["link"] else
                f"<span style='font-weight:600;font-size:13.5px;'>{row['title']}</span>"
            )
            desc_html = (
                f"<div style='color:#555;font-size:12px;margin-top:5px;line-height:1.4;'>"
                f"{row['desc']}</div>"
                if row["desc"] else ""
            )
            st.markdown(
                f"<div class='tbl-cell-title' style='background:{bg};'>"
                f"{title_html}{desc_html}</div>",
                unsafe_allow_html=True,
            )

        # ④ Source — centred
        with cols[3]:
            st.markdown(
                f"<div class='tbl-cell' style='background:{bg};justify-content:center;"
                f"font-size:12.5px;color:#333;text-align:center;'>{row['media']}</div>",
                unsafe_allow_html=True,
            )

        # ⑤ Published — centred
        with cols[4]:
            st.markdown(
                f"<div class='tbl-cell' style='background:{bg};justify-content:center;"
                f"font-size:12px;color:#555;text-align:center;'>{row['published']}</div>",
                unsafe_allow_html=True,
            )

        # ⑥ Language — centred + coloured
        with cols[5]:
            lang_color = {"English":"#1565C0","Hindi":"#E65100","Marathi":"#2E7D32"}.get(row["language"],"#333")
            st.markdown(
                f"<div class='tbl-cell' style='background:{bg};justify-content:center;"
                f"font-size:12px;font-weight:600;color:{lang_color};text-align:center;'>"
                f"{row['language']}</div>",
                unsafe_allow_html=True,
            )

        # ⑦ Keyword — centred
        with cols[6]:
            st.markdown(
                f"<div class='tbl-cell' style='background:{bg};justify-content:center;"
                f"font-size:12px;color:#555;text-align:center;'>{row['query']}</div>",
                unsafe_allow_html=True,
            )

        # ⑧ Sentiment dropdown — centred
        with cols[7]:
            cur = st.session_state.sentiments.get(idx, "—")
            new_sent = st.selectbox(
                "sent", options=SENTIMENT_OPTIONS,
                index=SENTIMENT_OPTIONS.index(cur) if cur in SENTIMENT_OPTIONS else 0,
                key=f"sent_{idx}", label_visibility="collapsed",
            )
            st.session_state.sentiments[idx] = new_sent
            color = SENTIMENT_COLORS.get(new_sent, "#9E9E9E")
            if new_sent != "—":
                st.markdown(
                    f"<div style='text-align:center;color:{color};"
                    f"font-weight:700;font-size:11px;margin-top:2px;'>● {new_sent}</div>",
                    unsafe_allow_html=True,
                )

    # Bottom border of table
    st.markdown(
        "<div style='border:1.5px solid #b0c4de;border-top:none;"
        "border-radius:0 0 8px 8px;height:4px;margin-bottom:12px;'></div>",
        unsafe_allow_html=True,
    )

    # ── Sync sentiment & selection ────────────────────────────────
    df["sentiment"] = df.index.map(lambda i: st.session_state.sentiments.get(i, "—"))
    df["selected"]  = df.index.map(lambda i: st.session_state.selected_articles.get(i, False))
    selected_rows   = df[df["selected"] == True]
    n_sel           = len(selected_rows)

    # ── Action bar ────────────────────────────────────────────────
    st.divider()
    ab1, ab2, ab3 = st.columns([3, 3, 4])

    with ab1:
        dl = df[["title","media","published","language","query","desc","link","sentiment"]].copy()
        dl.columns = ["Title","Source","Published","Language","Keyword","Description","URL","Sentiment"]
        st.download_button(
            "📥 Download CSV",
            data=dl.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"news_{from_date.strftime('%Y%m%d')}_to_{to_date.strftime('%Y%m%d')}.csv",
            mime="text/csv", key="dl-csv",
        )

    with ab2:
        gen_btn = st.button(
            f"✨ Generate Summary ({n_sel} selected)",
            type="primary", disabled=(n_sel == 0), key="gen_btn",
        )

    with ab3:
        st.caption(
            f"ℹ️ {n_sel} article(s) selected." if n_sel > 0
            else "☑️ Check articles to enable summary generation."
        )

    if gen_btn and n_sel > 0:
        with st.spinner(f"Generating AI summary for {n_sel} articles…"):
            st.session_state.summary_text = claude_summary(selected_rows)

    if st.session_state.summary_text:
        st.subheader("📋 Generated Summary")
        st.info(st.session_state.summary_text)
        st.download_button(
            "📄 Download Summary as TXT",
            data=st.session_state.summary_text.encode("utf-8"),
            file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain", key="dl-summary",
        )

    # ── Overall Tone Summary ──────────────────────────────────────
    st.subheader("Overall Tone Summary")
    st.caption("Updates live as you tag articles with sentiment above.")

    counts = df["sentiment"].value_counts().reindex(
        ["Positive", "Neutral", "Negative"], fill_value=0
    )
    labelled_count = int(counts.sum())

    st.markdown(f"""
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
      <div class="metric-box metric-total">
        <div class="metric-value">{total_count}</div>
        <div class="metric-label">📰 Total Articles</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    labelled = df[df["sentiment"] != "—"]
    if not labelled.empty:
        pie_col, _ = st.columns([1, 1])
        with pie_col:
            pc = labelled["sentiment"].value_counts().reindex(
                ["Positive", "Neutral", "Negative"], fill_value=0)
            pie = px.pie(
                names=pc.index, values=pc.values,
                title="Sentiment Distribution (labelled articles)",
                hole=0.55, color=pc.index,
                color_discrete_map={"Positive":"#43A047","Neutral":"#78909C","Negative":"#E53935"},
            )
            pie.update_traces(
                textinfo="percent+label",
                textfont=dict(size=14, family="Sora, sans-serif", color="white"),
                insidetextfont=dict(size=14, family="Sora, sans-serif", color="white"),
            )
            pie.update_layout(
                legend=dict(font=dict(size=13, family="Sora, sans-serif")),
                title_font=dict(size=15, family="Sora, sans-serif"),
            )
            st.plotly_chart(pie, use_container_width=True)
    else:
        st.info("Tag articles with a sentiment above to see the distribution chart.")

    # ── Trending Topics ───────────────────────────────────────────
    # Extract keywords from titles using simple word frequency
    import re
    from collections import Counter

    STOPWORDS = {
        "the","a","an","and","or","but","in","on","at","to","for","of","with",
        "is","was","are","were","be","been","being","have","has","had","do","does",
        "did","will","would","could","should","may","might","shall","can","need",
        "this","that","these","those","it","its","he","she","they","we","you","i",
        "his","her","their","our","your","my","by","from","as","up","about","into",
        "through","during","after","before","over","under","again","further","then",
        "once","here","there","when","where","why","how","all","both","each","few",
        "more","most","other","some","such","no","not","only","own","same","so",
        "than","too","very","just","भारत","india","news","says","say","said",
        "also","new","amid","after","latest","amid","amid","amid","amid",
    }

    TOPIC_MAP = {
        "yogi": "Yogi Adityanath", "adityanath": "Yogi Adityanath",
        "akhilesh": "Akhilesh Yadav", "yadav": "Akhilesh Yadav",
        "bjp": "BJP", "sp": "Samajwadi Party", "samajwadi": "Samajwadi Party",
        "modi": "Modi", "congress": "Congress", "rahul": "Rahul Gandhi",
        "up": "Uttar Pradesh", "election": "Elections", "elections": "Elections",
        "development": "Development", "scheme": "Government Scheme",
        "crime": "Crime", "communal": "Communal", "riot": "Communal",
        "farmer": "Farmers", "farmers": "Farmers", "agriculture": "Farmers",
        "police": "Law & Order", "arrest": "Law & Order",
        "hospital": "Health", "health": "Health",
        "road": "Infrastructure", "expressway": "Infrastructure",
        "economy": "Economy", "inflation": "Economy",
        "education": "Education", "school": "Education",
    }

    all_words = []
    for title in df["title"].dropna():
        words = re.findall(r"[a-zA-Z]{3,}", title.lower())
        for w in words:
            if w not in STOPWORDS:
                mapped = TOPIC_MAP.get(w)
                if mapped:
                    all_words.append(mapped)
                else:
                    all_words.append(w.capitalize())

    if all_words:
        topic_counts = Counter(all_words).most_common(10)
        topics_df = pd.DataFrame(topic_counts, columns=["Topic", "Count"])

        trending_fig = px.bar(
            topics_df, x="Topic", y="Count",
            title="Trending Topics",
            text="Count",
            color_discrete_sequence=["#1B5E20"],
        )
        trending_fig.update_traces(
            textposition="inside",
            textfont=dict(size=13, color="white", family="Sora, sans-serif"),
            marker_color="#1B5E20",
        )
        trending_fig.update_layout(
            xaxis_title="", yaxis_title="Mentions",
            title_font=dict(size=16, family="Sora, sans-serif"),
            xaxis_tickfont=dict(size=12, family="Sora, sans-serif"),
            plot_bgcolor="white",
            yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
            showlegend=False,
        )
        st.plotly_chart(trending_fig, use_container_width=True)
    else:
        st.info("Trending topics will appear once articles are loaded.")

elif st.session_state.has_fetched:
    st.warning("No articles found for the selected filters and date range.")
else:
    st.info("👈 Add keywords in the sidebar, set your date range, then click **Fetch News**.")
