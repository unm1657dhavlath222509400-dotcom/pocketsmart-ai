"""PocketSmart AI - GenAI budget-based recommendation system (Streamlit + Gemini)."""
import json, os
from urllib.parse import quote_plus
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PocketSmart AI", page_icon="💰", layout="wide")

# ---------- Platform search links (real links, no invented product URLs) ----------
LINKS = {
    "Amazon": "https://www.amazon.in/s?k={q}",
    "Flipkart": "https://www.flipkart.com/search?q={q}",
    "IKEA": "https://www.ikea.com/in/en/search/?q={q}",
    "Swiggy": "https://www.swiggy.com/search?query={q}",
    "Zomato": "https://www.zomato.com/search?q={q}",
    "OYO": "https://www.oyorooms.com/search?query={q}",
}
PLATFORMS = {
    "Interior Design": ["IKEA", "Amazon", "Flipkart"],
    "Party / Event": ["Swiggy", "Zomato", "Amazon", "Flipkart", "OYO"],
    "Jewelry Matching": ["Amazon", "Flipkart"],
}
# Default budget split used as fallback / guidance
SPLITS = {
    "Interior Design": {"Furniture": 40, "Lighting": 15, "Soft furnishings": 15, "Wall decor": 15, "Storage": 5, "Buffer": 10},
    "Party / Event": {"Food & drinks": 40, "Venue / stay": 20, "Decorations": 20, "Return gifts": 10, "Buffer": 10},
    "Jewelry Matching": {"Necklace / set": 40, "Earrings": 25, "Bangles / bracelets": 20, "Accessories": 5, "Buffer": 10},
}

def link(platform, query):
    return LINKS.get(platform, "https://www.google.com/search?q={q}").format(q=quote_plus(query))

# ---------- Gemini ----------
def get_client(key):
    from google import genai
    return genai.Client(api_key=key)

def build_prompt(planner, budget, answers):
    return f"""You are PocketSmart AI, a budget planning assistant for Indian shoppers. Currency: INR.
Planner: {planner}. Total budget: {budget}. Allowed platforms: {PLATFORMS[planner]}.
User details: {json.dumps(answers)}.
Suggested split (adapt if the details justify it): {json.dumps(SPLITS[planner])}.
Rules: total of all item est_price MUST be <= {budget}; keep a Buffer category; give 2-3 items per
non-buffer category; est_price is an approximate market price, not a live price; search_query must be
a short product search phrase (3-6 words).
Return ONLY JSON in this exact shape:
{{"allocations":[{{"category":"","percent":0,"amount":0}}],
 "items":[{{"category":"","name":"","platform":"","est_price":0,"reason":"","search_query":""}}],
 "tips":["",""]}}"""

def call_gemini(key, model, prompt):
    client = get_client(key)
    resp = client.models.generate_content(
        model=model, contents=prompt,
        config={"response_mime_type": "application/json", "temperature": 0.6})
    text = resp.text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(text)

# ---------- Offline fallback (demo mode, no API key) ----------
def fallback(planner, budget, answers):
    theme = answers.get("style") or answers.get("theme") or answers.get("outfit_color") or "classic"
    plats = PLATFORMS[planner]
    allocs, items = [], []
    for i, (cat, pct) in enumerate(SPLITS[planner].items()):
        amt = round(budget * pct / 100)
        allocs.append({"category": cat, "percent": pct, "amount": amt})
        if cat == "Buffer":
            continue
        for j in range(2):
            plat = plats[(i + j) % len(plats)]
            price = round(amt * (0.55 if j == 0 else 0.4))
            q = f"{theme} {cat}".lower()
            items.append({"category": cat, "name": f"{cat} option {j+1} ({theme})", "platform": plat,
                          "est_price": price, "reason": "Fits the category budget and chosen style (demo mode).",
                          "search_query": q})
    return {"allocations": allocs, "items": items,
            "tips": ["Demo mode: add a Gemini API key in the sidebar for personalised AI picks.",
                     "Compare at least two platforms before buying."]}

# ---------- Adaptive forms ----------
def adaptive_form(planner):
    a = {}
    if planner == "Interior Design":
        a["room"] = st.selectbox("Room", ["Living room", "Bedroom", "Kitchen", "Study / office", "Kids room"])
        a["size_sqft"] = st.slider("Room size (sq ft)", 40, 500, 150)
        a["style"] = st.selectbox("Style", ["Modern minimal", "Scandinavian", "Traditional Indian", "Boho", "Industrial"])
        a["colors"] = st.text_input("Wall / existing colors", "white and beige")
        if a["room"] == "Bedroom":
            a["bed_size"] = st.selectbox("Bed size", ["Single", "Queen", "King"])
        if a["room"] == "Kids room":
            a["child_age"] = st.slider("Child age", 1, 16, 6)
        a["priorities"] = st.multiselect("Priorities", ["Storage", "Lighting", "Comfort", "Aesthetics", "Durability"])
    elif planner == "Party / Event":
        a["event"] = st.selectbox("Event", ["Birthday", "Anniversary", "Baby shower", "House warming", "Farewell"])
        a["guests"] = st.slider("Guests", 5, 200, 30)
        a["theme"] = st.text_input("Theme", "colourful")
        a["food"] = st.selectbox("Food", ["Veg", "Non-veg", "Mixed", "Jain"])
        a["venue"] = st.radio("Venue", ["Home", "Rent a place / stay"], horizontal=True)
        if a["event"] == "Birthday":
            a["age"] = st.number_input("Age of birthday person", 1, 100, 10)
    else:
        a["occasion"] = st.selectbox("Occasion", ["Wedding guest", "Festival", "Office", "Party", "Engagement"])
        a["outfit"] = st.selectbox("Outfit", ["Saree", "Lehenga", "Salwar / kurta", "Western dress", "Sherwani / kurta (men)"])
        a["outfit_color"] = st.text_input("Outfit color", "maroon")
        a["metal"] = st.selectbox("Preferred look", ["Gold tone", "Silver tone", "Rose gold", "Oxidised", "Kundan / Polki style"])
        a["skin_tone"] = st.selectbox("Skin tone (optional)", ["Fair", "Medium", "Wheatish", "Dark", "Prefer not to say"])
    return a

# ---------- UI ----------
st.title("💰 PocketSmart AI")
st.caption("GenAI-powered, cross-platform, budget-based recommendations for home decor, events and jewelry.")

with st.sidebar:
    st.header("Settings")
    key = st.text_input("Gemini API key", type="password", value=os.getenv("GEMINI_API_KEY", ""),
                        help="Get a free key at aistudio.google.com. Leave blank for demo mode.")
    model = st.text_input("Gemini model", value=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                          help="Use a Flash model for speed or a Pro model for deeper planning.")
    st.info("Prices are AI estimates. Always verify on the platform.")

planner = st.radio("Choose a planner", list(PLATFORMS), horizontal=True)
left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Your details")
    budget = st.number_input("Total budget (INR)", 1000, 1_000_000, 30000, step=1000)
    answers = adaptive_form(planner)
    go = st.button("Generate my plan", type="primary", use_container_width=True)

if go:
    with right, st.spinner("Planning within your budget..."):
        try:
            if key:
                plan = call_gemini(key, model, build_prompt(planner, budget, answers))
            else:
                plan = fallback(planner, budget, answers)
        except Exception as e:
            st.warning(f"Gemini call failed ({e}). Showing demo-mode plan instead.")
            plan = fallback(planner, budget, answers)
    st.session_state["plan"] = plan
    st.session_state["budget"] = budget

if "plan" in st.session_state:
    plan, budget = st.session_state["plan"], st.session_state["budget"]
    with right:
        st.subheader("Budget allocation")
        adf = pd.DataFrame(plan["allocations"])
        st.bar_chart(adf.set_index("category")["amount"])

        st.subheader("Recommended items")
        st.caption("Tick the items you pick. The tracker updates automatically.")
        rows = []
        for it in plan["items"]:
            rows.append({"Pick": False, "Category": it["category"], "Item": it["name"], "Platform": it["platform"],
                         "Est. price (INR)": int(it["est_price"]), "Why": it["reason"],
                         "Search": link(it["platform"], it["search_query"])})
        edited = st.data_editor(
            pd.DataFrame(rows), use_container_width=True, hide_index=True,
            disabled=["Category", "Item", "Platform", "Est. price (INR)", "Why", "Search"],
            column_config={"Search": st.column_config.LinkColumn("Open", display_text="Search")})
        spent = int(edited.loc[edited["Pick"], "Est. price (INR)"].sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Budget", f"Rs. {budget:,}")
        c2.metric("Selected", f"Rs. {spent:,}")
        c3.metric("Remaining", f"Rs. {budget - spent:,}", delta=None if spent <= budget else "Over budget",
                  delta_color="inverse")
        if spent > budget:
            st.error("Selected items exceed your budget. Swap an item for a cheaper option.")
        st.progress(min(spent / budget, 1.0))
        st.subheader("Smart tips")
        for t in plan.get("tips", []):
            st.write("• " + t)
        st.download_button("Download plan (JSON)", json.dumps(plan, indent=2), "pocketsmart_plan.json")
else:
    with right:
        st.info("Fill in the details on the left and click **Generate my plan**.")
