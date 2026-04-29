# ============================================================================
# REPLACEMENT FOR THE "Trending Topics" SECTION
# ============================================================================
# In your existing script, find this block and DELETE everything from:
#
#     # ── Trending Topics ───────────────────────────────────────────
#     # Extract keywords from titles using simple word frequency
#     import re
#     from collections import Counter
#     ...
#     else:
#         st.info("Trending topics will appear once articles are loaded.")
#
# Replace it with the code below.
# ============================================================================


    # ── Trending Topics by Content Category ──────────────────────
    st.subheader("Trending Topics")
    st.caption("Articles classified by analysing title + description content.")

    # Predefined categories — each maps to a list of trigger keywords.
    # Includes English + Hindi + Marathi terms since the app fetches all 3.
    CATEGORY_KEYWORDS = {
        "Politics & Governance": [
            "bjp", "congress", "samajwadi", "bsp", "aap", "rld", "shiv sena",
            "election", "elections", "vote", "voter", "voting", "poll", "polls",
            "minister", "chief minister", "prime minister", "modi", "yogi",
            "adityanath", "akhilesh", "rahul gandhi", "mayawati", "priyanka",
            "mla", "parliament", "assembly", "lok sabha", "rajya sabha",
            "government", "govt", "cabinet", "rally", "campaign", "manifesto",
            "alliance", "coalition", "opposition", "ruling party", "political",
            "policy", "bill passed", "ordinance",
            "चुनाव", "मंत्री", "मुख्यमंत्री", "प्रधानमंत्री", "सरकार", "नेता",
            "भाजपा", "कांग्रेस", "सपा", "बसपा", "विधानसभा", "रैली", "राजनीति",
            "निवडणूक", "मुख्यमंत्री", "सरकार",
        ],
        "Crime & Law": [
            "crime", "criminal", "murder", "killed", "killing", "rape", "raped",
            "assault", "molest", "molested", "abuse", "attack", "attacked",
            "arrest", "arrested", "police", "fir filed", "booked under",
            "loot", "robbery", "theft", "stolen", "fraud", "scam", "cheating",
            "kidnap", "abduct", "shot dead", "shooting", "encounter", "gang",
            "court", "judge", "verdict", "sentence", "jail", "prison",
            "custody", "raid", "investigation", "accused", "victim", "suicide",
            "lynching", "lynched", "harassment",
            "हत्या", "बलात्कार", "गिरफ्तार", "पुलिस", "अपराध", "लूट", "चोरी",
            "केस", "मामला", "जेल", "अदालत", "धोखाधड़ी",
            "गुन्हा", "पोलीस", "अटक",
        ],
        "Economy & Business": [
            "economy", "economic", "gdp", "inflation", "market", "stock",
            "sensex", "nifty", "rupee", "dollar", "bank", "banking", "loan",
            "investment", "investor", "business", "company", "trade", "export",
            "import", "industry", "industrial", "factory", "manufacturing",
            "startup", "tax", "gst", "budget", "revenue", "profit", "fiscal",
            "fund", "finance", "financial", "salary", "price hike", "msme",
            "अर्थव्यवस्था", "बाजार", "महंगाई", "कीमत", "बैंक", "व्यापार",
            "कर", "बजट", "उद्योग",
            "अर्थव्यवस्था", "बाजार",
        ],
        "Health": [
            "health", "hospital", "doctor", "patient", "medical", "medicine",
            "disease", "infection", "virus", "covid", "vaccine", "vaccination",
            "dengue", "malaria", "cancer", "diabetes", "outbreak", "epidemic",
            "pandemic", "treatment", "surgery", "clinic", "pharma", "ayushman",
            "mental health", "drug overdose",
            "स्वास्थ्य", "अस्पताल", "डॉक्टर", "बीमारी", "इलाज", "दवा",
            "मरीज", "टीका",
            "आरोग्य", "रुग्णालय", "डॉक्टर",
        ],
        "Education": [
            "education", "school", "schools", "college", "university",
            "student", "students", "teacher", "exam", "exams", "examination",
            "result", "results", "admission", "scholarship", "syllabus",
            "neet", "jee", "upsc", "board exam", "cbse", "icse", "academic",
            "degree", "course", "literacy", "coaching", "iit",
            "शिक्षा", "स्कूल", "कॉलेज", "विश्वविद्यालय", "छात्र", "परीक्षा",
            "शिक्षक", "रिजल्ट",
            "शिक्षण", "शाळा", "विद्यार्थी", "परीक्षा",
        ],
        "Infrastructure": [
            "infrastructure", "road", "roads", "highway", "expressway",
            "bridge", "flyover", "metro", "railway", "rail line", "train",
            "airport", "construction", "built", "project", "smart city",
            "housing", "real estate", "power plant", "electricity",
            "water supply", "sewage",
            "सड़क", "पुल", "मेट्रो", "रेलवे", "हवाई अड्डा", "निर्माण",
            "विकास", "एक्सप्रेसवे",
            "रस्ता", "पूल", "मेट्रो", "रेल्वे",
        ],
        "Agriculture & Farmers": [
            "farmer", "farmers", "agriculture", "agricultural", "crop",
            "crops", "harvest", "wheat", "rice", "paddy", "sugarcane",
            "cotton", "msp", "minimum support price", "mandi", "kisan",
            "irrigation", "fertilizer", "pesticide", "monsoon", "rainfall",
            "drought",
            "किसान", "कृषि", "फसल", "गेहूं", "धान", "गन्ना", "मंडी",
            "खेती", "सिंचाई",
            "शेतकरी", "शेती", "पीक",
        ],
        "Religion & Communal": [
            "temple", "mosque", "masjid", "church", "religion", "religious",
            "hindu", "muslim", "sikh", "christian", "communal", "riot",
            "festival", "puja", "namaz", "diwali", "holi", "eid", "ramadan",
            "ram mandir", "ayodhya", "kashi", "mathura", "yatra", "kumbh",
            "मंदिर", "मस्जिद", "धर्म", "हिंदू", "मुस्लिम", "त्योहार",
            "पूजा", "यात्रा",
            "मंदिर", "धर्म",
        ],
        "Sports": [
            "cricket", "football", "hockey", "kabaddi", "olympic", "olympics",
            "match", "tournament", "team", "player", "captain", "coach",
            "world cup", "ipl", "ranji", "score", "champion", "medal",
            "gold medal", "silver medal", "bronze medal", "wicket",
            "क्रिकेट", "मैच", "खिलाड़ी", "टीम", "जीत", "विश्व कप",
            "क्रिकेट", "सामना",
        ],
        "Weather & Disaster": [
            "rain", "rainfall", "flood", "floods", "drought", "storm",
            "cyclone", "earthquake", "landslide", "fire breaks", "fire broke",
            "accident", "disaster", "weather", "heatwave", "cold wave",
            "fog", "lightning", "drowned",
            "बारिश", "बाढ़", "तूफान", "भूकंप", "आग", "दुर्घटना", "मौसम",
            "पाऊस", "पूर", "वादळ", "अपघात",
        ],
        "Social Issues & Protests": [
            "women safety", "girl child", "dalit", "caste", "tribal",
            "minority", "protest", "march", "demonstration", "strike",
            "discrimination", "rights", "ngo", "activist", "dharna",
            "andolan",
            "महिला", "दलित", "जाति", "प्रदर्शन", "हड़ताल", "धरना", "आंदोलन",
            "महिला", "आंदोलन",
        ],
        "Technology": [
            "technology", "artificial intelligence", " ai ", "internet",
            "digital", "app launch", "software", "cyber", "online",
            "smartphone", " 5g ", "telecom", "data leak", "hacking",
            "तकनीक", "इंटरनेट", "डिजिटल", "साइबर",
        ],
        "Entertainment": [
            "film", "movie", "actor", "actress", "bollywood", "music",
            "song", "album", "concert", "celebrity", "trailer released",
            "box office",
            "फिल्म", "अभिनेता", "अभिनेत्री", "संगीत", "गाना",
            "चित्रपट", "अभिनेता",
        ],
    }

    def categorize_article(title: str, desc: str) -> str:
        """Score each category by keyword hits; return the top one."""
        text = f" {title or ''} {desc or ''} ".lower()
        scores = {}
        for cat, kws in CATEGORY_KEYWORDS.items():
            hits = 0
            for kw in kws:
                if kw.lower() in text:
                    hits += 1
            if hits > 0:
                scores[cat] = hits
        if not scores:
            return "Other / Uncategorised"
        # Tie-break: highest hit count, then category name (stable)
        return max(scores.items(), key=lambda x: (x[1], -len(x[0])))[0]

    # Apply categorisation
    df["category"] = df.apply(
        lambda r: categorize_article(r.get("title", ""), r.get("desc", "")),
        axis=1,
    )

    cat_counts = df["category"].value_counts()

    if not cat_counts.empty:
        # Push "Other / Uncategorised" to the end regardless of count
        ordered = cat_counts.drop(labels=["Other / Uncategorised"], errors="ignore")
        cat_df = pd.DataFrame({
            "Category": ordered.index.tolist(),
            "Articles": ordered.values.tolist(),
        })
        if "Other / Uncategorised" in cat_counts.index:
            cat_df = pd.concat([
                cat_df,
                pd.DataFrame({
                    "Category": ["Other / Uncategorised"],
                    "Articles": [int(cat_counts["Other / Uncategorised"])],
                }),
            ], ignore_index=True)

        # Top 12 visible categories
        cat_df = cat_df.head(12)

        trending_fig = px.bar(
            cat_df,
            x="Category",
            y="Articles",
            title="Trending Topics by Content Category",
            text="Articles",
            color="Articles",
            color_continuous_scale=[[0, "#90CAF9"], [1, "#0D47A1"]],
        )
        trending_fig.update_traces(
            textposition="outside",
            textfont=dict(size=13, color="#333", family="Sora, sans-serif"),
            cliponaxis=False,
        )
        trending_fig.update_layout(
            xaxis_title="",
            yaxis_title="Number of Articles",
            title_font=dict(size=16, family="Sora, sans-serif"),
            xaxis_tickfont=dict(size=11, family="Sora, sans-serif"),
            yaxis_tickfont=dict(size=11, family="Sora, sans-serif"),
            plot_bgcolor="white",
            yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
            xaxis=dict(tickangle=-25),
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(t=60, b=120),
        )
        st.plotly_chart(trending_fig, use_container_width=True)

        # Optional: a small expandable table so the user can audit
        # which articles fell into which bucket.
        with st.expander("🔍 See articles per category"):
            for cat in cat_df["Category"].tolist():
                sub = df[df["category"] == cat][
                    ["title", "media", "language", "published"]
                ]
                st.markdown(f"**{cat}** — {len(sub)} article(s)")
                st.dataframe(sub, use_container_width=True, hide_index=True)
    else:
        st.info("Trending topics will appear once articles are loaded.")
