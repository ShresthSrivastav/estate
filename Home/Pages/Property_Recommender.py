from urllib.parse import quote_plus
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.data_loader import ASSET_DIR, load_recommender_data
from utils.recommender import (
    FURNISHING_LABELS,
    alternative_properties,
    display_furnishing,
    format_price,
    recommend_properties,
    sector_options,
)


st.set_page_config(page_title="Property Recommender | Nestwise", page_icon="🏠", layout="wide")

st.markdown(
    """
    <style>
    .block-container { max-width: 1180px; padding-top: 2rem; }
    .reco-hero { padding: 2rem 2.2rem; border-radius: 24px; background: #e7f5f1; margin-bottom: 1.4rem; }
    .reco-hero h1 { color: #102a43; margin: 0; }
    .reco-hero p { color: #476172; margin: .4rem 0 0; }
    .tag { display: inline-block; padding: .25rem .65rem; border-radius: 100px; background: #d5f3e8; color: #12614d; font-size: .82rem; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_data():
    return load_recommender_data()


df = load_data()
st.markdown(
    """
    <section class="reco-hero">
      <span class="tag">EXPLAINABLE MATCHING</span>
      <h1>Find your next property</h1>
      <p>Choose what cannot change first. Then use preferences to rank the properties that remain.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.info("**How it works:** location and maximum budget are hard constraints. Optional preferences only rank properties that already satisfy both constraints.")

with st.form("property_search"):
    st.subheader("Hard constraints")
    hard_left, hard_right = st.columns(2)
    with hard_left:
        selected_sector = st.selectbox("Location / sector", sector_options(df), format_func=lambda value: value.title())
    with hard_right:
        max_budget = st.number_input("Maximum budget (₹ Cr)", min_value=0.05, max_value=100.0, value=1.50, step=0.05, format="%.2f")

    st.subheader("Optional preferences")
    first, second, third = st.columns(3)
    with first:
        property_type = st.selectbox("Property type", ["Any", "flat", "house"], format_func=lambda value: value.title())
        bedrooms = st.selectbox("Bedrooms", ["Any", "1", "2", "3", "4+"])
        bathrooms = st.selectbox("Minimum bathrooms", ["Any"] + [str(value) for value in range(1, 7)])
        min_area = st.number_input("Minimum built-up area (sq.ft.)", min_value=0.0, value=0.0, step=50.0)
    with second:
        furnishing = st.selectbox("Furnishing", ["Any", "Unfurnished", "Semi-Furnished", "Furnished"])
        luxury = st.selectbox("Luxury category", ["Any", "Low", "Medium", "High"])
        floor = st.selectbox("Floor category", ["Any", "Low Floor", "Mid Floor", "High Floor"])
        balconies = st.selectbox("Minimum balconies", ["Any", "0", "1", "2", "3"])
    with third:
        servant_room = st.checkbox("Servant room")
        store_room = st.checkbox("Store room")
        sort_by = st.selectbox("Sort results by", ["Best Match", "Lowest Price", "Largest Area", "Most Bedrooms", "Best Budget Fit"])
        result_limit = st.select_slider("Recommendations", options=[5, 10], value=5)
    submitted = st.form_submit_button("Find my property", type="primary", use_container_width=True)

if submitted:
    st.session_state.pop("selected_property", None)
    preferences = {
        "property_type": property_type,
        "bedrooms": bedrooms,
        "bathrooms": None if bathrooms == "Any" else bathrooms,
        "min_area": None if min_area == 0 else min_area,
        "furnishing_type": next((key for key, label in FURNISHING_LABELS.items() if label == furnishing), None) if furnishing != "Any" else None,
        "luxury_category": luxury,
        "floor_category": floor,
        "balcony": None if balconies == "Any" else balconies,
        "servant_room": 1 if servant_room else None,
        "store_room": 1 if store_room else None,
    }
    st.session_state["search"] = {"sector": selected_sector, "budget": max_budget, "preferences": preferences, "sort_by": sort_by, "limit": result_limit}

search = st.session_state.get("search")
if search:
    results = recommend_properties(df, search["sector"], search["budget"], search["preferences"], search["limit"], search["sort_by"])
    st.divider()
    if results.empty:
        st.subheader("No exact matches")
        st.warning(f"No properties found in {search['sector'].title()} within your maximum budget of {format_price(search['budget'])}.")
        st.caption("The recommendations below are explicitly relaxed alternatives. They do not satisfy the original location-and-budget constraints.")
        alternatives = alternative_properties(df, search["sector"], search["budget"])
        same_sector = alternatives["same_sector_over_budget"]
        other_sector = alternatives["other_sector_within_budget"]
        if not same_sector.empty:
            st.markdown("#### Same sector · over budget")
            st.dataframe(same_sector[["sector", "property_type", "price", "bedRoom", "bathroom", "built_up_area"]].rename(columns={"price": "price_cr", "bedRoom": "bedrooms"}), hide_index=True, use_container_width=True)
        if not other_sector.empty:
            st.markdown("#### Other sectors · within budget")
            st.dataframe(other_sector[["sector", "property_type", "price", "bedRoom", "bathroom", "built_up_area"]].rename(columns={"price": "price_cr", "bedRoom": "bedrooms"}), hide_index=True, use_container_width=True)
        if same_sector.empty and other_sector.empty:
            st.info("There are no relaxed alternatives in the current dataset for this budget.")
    else:
        st.subheader(f"Recommended properties · {len(results)} exact matches")
        st.caption(f"All results satisfy {search['sector'].title()} and price ≤ {format_price(search['budget'])}. Ranked by {search['sort_by'].lower()}.")
        for _, row in results.iterrows():
            image_number = int(row["_index"]) % 6 + 1
            with st.container(border=True):
                image_col, detail_col, action_col = st.columns([1, 1.65, .7])
                with image_col:
                    st.image(ASSET_DIR / f"property-{image_number}.svg", use_container_width=True)
                    st.caption("Illustrative demo image")
                with detail_col:
                    st.markdown(f"### {format_price(float(row['price']))}")
                    st.markdown(f"**{str(row['bedRoom']).replace('.0', '')} BHK {str(row['property_type']).title()}** · {str(row['sector']).title()}")
                    st.write(f"{float(row['built_up_area']):,.0f} sq.ft.  ·  {str(row['bathroom']).replace('.0', '')} bathrooms  ·  {display_furnishing(row['furnishing_type'])}")
                    st.progress(min(float(row["match_score"]) / 100, 1), text=f"{row['match_score']:.1f}% match")
                with action_col:
                    st.metric("Budget used", f"{row['budget_utilization']:.0f}%")
                    if st.button("View property", key=f"view-{row['_index']}", use_container_width=True):
                        st.session_state["selected_property"] = row.to_dict()
                        st.rerun()
                    st.caption("Demo detail view")

        st.markdown("#### Compare these matches")
        comparison = results[["property_type", "sector", "price", "bedRoom", "bathroom", "built_up_area", "match_score"]].rename(columns={"price": "price_cr", "bedRoom": "bedrooms", "match_score": "match_%"})
        st.dataframe(comparison, hide_index=True, use_container_width=True)

selected = st.session_state.get("selected_property")
if selected:
    st.divider()
    st.subheader("Property detail")
    detail_col, score_col = st.columns([1.2, 1])
    with detail_col:
        st.image(ASSET_DIR / f"property-{int(selected['_index']) % 6 + 1}.svg", use_container_width=True)
        st.caption("Illustrative local demo image · this is not a photograph of the exact dataset record")
    with score_col:
        st.markdown(f"### {format_price(float(selected['price']))}")
        st.markdown(f"**{str(selected['bedRoom']).replace('.0', '')} BHK {str(selected['property_type']).title()}** · {str(selected['sector']).title()}")
        st.progress(min(float(selected["match_score"]) / 100, 1), text=f"{selected['match_score']:.1f}% recommendation match")
        st.write(f"Budget utilization: **{selected['budget_utilization']:.1f}%**")
        st.link_button("Open demo location search", f"https://www.google.com/maps/search/{quote_plus(str(selected['sector']) + ' Gurgaon')}", use_container_width=True)

    details = {
        "Price": format_price(float(selected["price"])),
        "Price per sq.ft. (derived)": f"₹{float(selected['price']) * 10000000 / float(selected['built_up_area']):,.0f}" if float(selected.get("built_up_area", 0)) else "Not available",
        "Sector": str(selected["sector"]).title(),
        "Property type": str(selected["property_type"]).title(),
        "Bedrooms": str(selected["bedRoom"]).replace(".0", ""),
        "Bathrooms": str(selected["bathroom"]).replace(".0", ""),
        "Balconies": str(selected["balcony"]),
        "Built-up area": f"{float(selected['built_up_area']):,.0f} sq.ft.",
        "Property age": str(selected["agePossession"]),
        "Furnishing": display_furnishing(selected["furnishing_type"]),
        "Luxury": str(selected["luxury_category"]),
        "Floor": str(selected["floor_category"]),
        "Servant room": "Yes" if float(selected["servant room"]) else "No",
        "Store room": "Yes" if float(selected["store room"]) else "No",
    }
    st.dataframe(pd.DataFrame(details.items(), columns=["Attribute", "Value"]), hide_index=True, use_container_width=True)
    st.markdown("#### Why this property was recommended")
    for reason in selected["match_reasons"]:
        st.markdown(f"✓ {reason}")
    if selected["tradeoffs"]:
        st.markdown("**Preference trade-offs**")
        for tradeoff in selected["tradeoffs"]:
            st.markdown(f"· {tradeoff}")
    with st.expander("Show score calculation"):
        st.write("Each active component contributes its configured weight. The displayed percentage is the weighted average of those components; location and budget always remain active.")
        st.json(selected["score_breakdown"])
    if st.button("Close property detail"):
        st.session_state.pop("selected_property", None)
        st.rerun()
