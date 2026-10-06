from urllib.parse import quote_plus
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.data_loader import ASSET_DIR, load_recommender_data, load_sector_coordinates
from utils.recommender import (
    FURNISHING_LABELS,
    alternative_properties,
    display_furnishing,
    format_price,
    recommend_properties,
    sector_options,
)


st.set_page_config(page_title="Nestwise | Property Recommender", page_icon="🏠", layout="wide")

st.markdown(
    """
    <style>
    .block-container { max-width: 1180px; padding-top: 1.5rem; }
    .reco-hero {
        padding: 1.8rem 2rem; border-radius: 24px;
        background: linear-gradient(120deg, #e7f5f1, #f4fbf8);
        border: 1px solid #d5e9e2; margin-bottom: 1rem;
    }
    .reco-hero h1 { color: #102a43; margin: 0; font-size: clamp(2rem, 4vw, 3rem); }
    .reco-hero p { color: #476172; margin: .45rem 0 0; }
    .tag {
        display: inline-block; padding: .25rem .65rem; border-radius: 100px;
        background: #d5f3e8; color: #12614d; font-size: .78rem; font-weight: 700;
        letter-spacing: .04em; margin-bottom: .45rem;
    }
    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
        div[data-testid="column"] {
            flex: 1 1 100% !important; width: 100% !important;
            min-width: 100% !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_data():
    return load_recommender_data()


@st.cache_data(show_spinner=False)
def load_coordinates():
    return load_sector_coordinates()


def numeric_choices(column):
    values = pd.to_numeric(df[column], errors="coerce").dropna().unique().tolist()
    return sorted({int(value) if float(value).is_integer() else float(value) for value in values})


def display_number(value):
    number = pd.to_numeric(value, errors="coerce")
    return str(int(number)) if pd.notna(number) and float(number).is_integer() else str(value)


df = load_data()
sector_coordinates = load_coordinates()
st.session_state.setdefault("favorites", set())

st.markdown(
    """
    <section class="reco-hero">
      <span class="tag">GURGAON PROPERTY DISCOVERY</span>
      <h1>Find a home that fits your life.</h1>
      <p>Choose a location and budget first. Then narrow the results with the preferences that matter to you.</p>
    </section>
    """,
    unsafe_allow_html=True,
)
st.info(
    "**Demo dataset:** these are historical property records, not active listings. "
    "The images are illustrative, and match scores describe preference fit—not investment or purchase likelihood."
)

property_types = ["Any"] + sorted(df["property_type"].dropna().astype(str).unique().tolist())
bedroom_values = numeric_choices("bedRoom")
bedroom_options = ["Any"] + [str(value) for value in bedroom_values if value < 4]
if any(value >= 4 for value in bedroom_values):
    bedroom_options.append("4+")
bathroom_options = ["Any"] + [str(value) for value in numeric_choices("bathroom")]
balcony_values = df["balcony"].dropna().astype(str).unique().tolist()
balcony_values.sort(key=lambda value: float("inf") if not value[:1].isdigit() else int(value.split("+")[0]))
balcony_options = ["Any"] + balcony_values
furnishing_options = ["Any"] + [
    FURNISHING_LABELS.get(value, str(value))
    for value in numeric_choices("furnishing_type")
]
luxury_options = ["Any"] + sorted(df["luxury_category"].dropna().astype(str).unique().tolist())
floor_options = ["Any"] + sorted(df["floor_category"].dropna().astype(str).unique().tolist())

with st.form("property_search"):
    st.subheader("Where and what is your budget?")
    location_col, budget_col = st.columns(2)
    with location_col:
        selected_sector = st.selectbox(
            "Location / sector",
            sector_options(df),
            format_func=lambda value: value.title(),
        )
        location_radius = st.slider(
            "Include nearby sectors",
            min_value=0,
            max_value=20,
            value=0,
            format="%d km",
            help="Zero searches only the selected sector. Increase this to include nearby sectors.",
        )
    with budget_col:
        max_budget = st.number_input(
            "Maximum budget (₹ crore)",
            min_value=0.05,
            max_value=100.0,
            value=1.50,
            step=0.05,
            format="%.2f",
            help="For example, ₹1.50 crore is ₹150 lakh.",
        )
        st.caption(f"That is approximately ₹{max_budget * 100:.0f} lakh.")

    with st.expander("More preferences (optional)", expanded=False):
        st.caption("Preferences rank eligible homes; they do not relax the location or budget limits.")
        first, second = st.columns(2)
        with first:
            property_type = st.selectbox(
                "Property type", property_types, format_func=str.title
            )
            bedrooms = st.selectbox("Bedrooms", bedroom_options)
            bathrooms = st.selectbox("Minimum bathrooms", bathroom_options)
            min_area = st.number_input(
                "Minimum built-up area (sq.ft.)",
                min_value=0.0,
                max_value=float(pd.to_numeric(df["built_up_area"], errors="coerce").max()),
                value=0.0,
                step=50.0,
                help="Leave at 0 for no area preference.",
            )
            furnishing = st.selectbox("Furnishing", furnishing_options)
        with second:
            luxury = st.selectbox("Luxury category", luxury_options)
            floor = st.selectbox("Floor category", floor_options)
            balconies = st.selectbox("Minimum balconies", balcony_options)
            servant_room = st.checkbox("Servant room")
            store_room = st.checkbox("Store room")
            sort_by = st.selectbox(
                "Sort results by",
                [
                    "Best Match",
                    "Lowest Price",
                    "Largest Area",
                    "Most Bedrooms",
                    "Best Budget Fit",
                    "Closest Location",
                ],
            )
            result_limit = st.select_slider(
                "Number of recommendations", options=[5, 10], value=5
            )

    submitted = st.form_submit_button(
        "Find matching homes", type="primary", width="stretch"
    )

if submitted:
    st.session_state.pop("selected_property", None)
    preferences = {
        "property_type": property_type,
        "bedrooms": bedrooms,
        "bathrooms": None if bathrooms == "Any" else bathrooms,
        "min_area": None if min_area == 0 else min_area,
        "furnishing_type": next(
            (
                key
                for key, label in FURNISHING_LABELS.items()
                if label == furnishing
            ),
            None,
        )
        if furnishing != "Any"
        else None,
        "luxury_category": luxury,
        "floor_category": floor,
        "balcony": None if balconies == "Any" else balconies,
        "servant_room": 1 if servant_room else None,
        "store_room": 1 if store_room else None,
    }
    st.session_state["search"] = {
        "sector": selected_sector,
        "budget": max_budget,
        "preferences": preferences,
        "sort_by": sort_by,
        "limit": result_limit,
        "location_radius": location_radius,
    }

search = st.session_state.get("search")
if search:
    results = recommend_properties(
        df,
        search["sector"],
        search["budget"],
        search["preferences"],
        search["limit"],
        search["sort_by"],
        location_radius_km=search.get("location_radius", 0),
        coordinates=sector_coordinates,
    )
    st.divider()

    if results.empty:
        st.subheader("No exact matches yet")
        st.warning(
            f"No homes match {search['sector'].title()} within "
            f"{format_price(search['budget'])}."
        )
        st.caption(
            "You can widen the location search above or view clearly labeled alternatives below."
        )
        with st.expander("Adjust fallback suggestions", expanded=True):
            budget_tolerance = st.slider(
                "Allow alternatives up to this much over budget",
                min_value=0,
                max_value=20,
                value=10,
                format="%d%%",
                help="This only affects the labeled alternatives. Exact matches always stay within your budget.",
            )
        alternatives = alternative_properties(
            df,
            search["sector"],
            search["budget"],
            budget_tolerance=budget_tolerance,
        )
        same_sector = alternatives["same_sector_over_budget"]
        other_sector = alternatives["other_sector_within_budget"]
        if not same_sector.empty:
            st.markdown("#### Same sector · over budget")
            st.dataframe(
                same_sector[
                    ["sector", "property_type", "price", "bedRoom", "bathroom", "built_up_area"]
                ].rename(
                    columns={
                        "price": "price_cr",
                        "bedRoom": "bedrooms",
                        "built_up_area": "area_sqft",
                    }
                ),
                hide_index=True,
                width="stretch",
            )
        if not other_sector.empty:
            st.markdown("#### Other sectors · within budget")
            st.dataframe(
                other_sector[
                    ["sector", "property_type", "price", "bedRoom", "bathroom", "built_up_area"]
                ].rename(
                    columns={
                        "price": "price_cr",
                        "bedRoom": "bedrooms",
                        "built_up_area": "area_sqft",
                    }
                ),
                hide_index=True,
                width="stretch",
            )
        if same_sector.empty and other_sector.empty:
            st.info("There are no alternatives in the current dataset for this budget.")

    else:
        location_label = (
            search["sector"].title()
            if not search.get("location_radius")
            else f"within {search['location_radius']} km of {search['sector'].title()}"
        )
        st.subheader(f"{len(results)} homes match your search")
        st.caption(
            f"{location_label} · up to {format_price(search['budget'])} · "
            f"sorted by {search['sort_by'].lower()}"
        )
        if st.session_state["favorites"]:
            st.caption(
                f"{len(st.session_state['favorites'])} home(s) saved in this session."
            )

        for _, row in results.iterrows():
            image_number = int(row["_index"]) % 6 + 1
            with st.container(border=True):
                image_col, card_col = st.columns([0.9, 2.1])
                with image_col:
                    st.image(str(ASSET_DIR / f"property-{image_number}.svg"))
                    st.caption("Illustrative image")
                with card_col:
                    st.metric("Asking price", format_price(float(row["price"])))
                    st.markdown(
                        f"**{display_number(row['bedRoom'])} BHK "
                        f"{str(row['property_type']).title()}** · "
                        f"{str(row['sector']).title()}"
                    )
                    st.caption(
                        f"{float(row['built_up_area']):,.0f} sq.ft. · "
                        f"{display_number(row['bathroom'])} bathrooms · "
                        f"{display_furnishing(row['furnishing_type'])}"
                    )
                    st.progress(
                        min(float(row["match_score"]) / 100, 1),
                        text=f"{row['match_score']:.0f}% preference match",
                    )
                    reasons = [
                        reason
                        for reason in row["match_reasons"]
                        if reason != "Within maximum budget"
                    ]
                    if reasons:
                        st.caption("Why it fits: " + " · ".join(reasons[:2]))

                    save_col, detail_col = st.columns(2)
                    with save_col:
                        favorite = row["_index"] in st.session_state["favorites"]
                        if st.button(
                            "Saved" if favorite else "Save home",
                            key=f"save-{row['_index']}",
                            width="stretch",
                        ):
                            if favorite:
                                st.session_state["favorites"].remove(row["_index"])
                            else:
                                st.session_state["favorites"].add(row["_index"])
                            st.rerun()
                    with detail_col:
                        if st.button(
                            "View details",
                            key=f"view-{row['_index']}",
                            width="stretch",
                        ):
                            st.session_state["selected_property"] = row.to_dict()
                            st.rerun()

        with st.expander("Compare matching homes"):
            comparison = results[
                [
                    "property_type",
                    "sector",
                    "price",
                    "bedRoom",
                    "bathroom",
                    "built_up_area",
                    "match_score",
                ]
            ].rename(
                columns={
                    "price": "price_cr",
                    "bedRoom": "bedrooms",
                    "built_up_area": "area_sqft",
                    "match_score": "match_percent",
                }
            )
            st.dataframe(comparison, hide_index=True, width="stretch")

        saved_indices = sorted(st.session_state["favorites"])
        if saved_indices:
            with st.expander(f"Saved homes ({len(saved_indices)})"):
                saved = df.loc[saved_indices].reset_index(names="record")
                st.dataframe(
                    saved[
                        [
                            "record",
                            "property_type",
                            "sector",
                            "price",
                            "bedRoom",
                            "bathroom",
                            "built_up_area",
                        ]
                    ].rename(
                        columns={
                            "record": "record_id",
                            "price": "price_cr",
                            "bedRoom": "bedrooms",
                            "built_up_area": "area_sqft",
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )

selected = st.session_state.get("selected_property")
if selected:
    st.divider()
    with st.container(border=True):
        st.subheader("Property details")
        detail_col, score_col = st.columns([1.2, 1])
        with detail_col:
            image_number = int(selected["_index"]) % 6 + 1
            st.image(str(ASSET_DIR / f"property-{image_number}.svg"))
            st.caption("Illustrative image—not a photograph of this dataset record.")
            st.link_button(
                "Search this sector on Maps",
                f"https://www.google.com/maps/search/{quote_plus(str(selected['sector']) + ' Gurgaon')}",
                width="stretch",
            )
        with score_col:
            st.metric("Asking price", format_price(float(selected["price"])))
            st.markdown(
                f"**{display_number(selected['bedRoom'])} BHK "
                f"{str(selected['property_type']).title()}** · "
                f"{str(selected['sector']).title()}"
            )
            st.progress(
                min(float(selected["match_score"]) / 100, 1),
                text=f"{selected['match_score']:.0f}% preference match",
            )
            st.caption(
                f"Budget used: {selected['budget_utilization']:.0f}% · "
                f"{float(selected['built_up_area']):,.0f} sq.ft."
            )

        details = {
            "Price": format_price(float(selected["price"])),
            "Price per sq.ft. (derived)": (
                f"₹{float(selected['price']) * 10000000 / float(selected['built_up_area']):,.0f}"
                if float(selected.get("built_up_area", 0))
                else "Not available"
            ),
            "Bathrooms": display_number(selected["bathroom"]),
            "Balconies": str(selected["balcony"]),
            "Property age": str(selected["agePossession"]),
            "Furnishing": display_furnishing(selected["furnishing_type"]),
            "Luxury": str(selected["luxury_category"]),
            "Floor": str(selected["floor_category"]),
            "Servant room": "Yes" if float(selected["servant room"]) else "No",
            "Store room": "Yes" if float(selected["store room"]) else "No",
        }
        st.dataframe(
            pd.DataFrame(details.items(), columns=["Property detail", "Value"]),
            hide_index=True,
            width="stretch",
        )
        with st.expander("Why this home was recommended"):
            for reason in selected["match_reasons"]:
                st.markdown(f"- {reason}")
            if selected["tradeoffs"]:
                st.markdown("**Preference trade-offs**")
                for tradeoff in selected["tradeoffs"]:
                    st.markdown(f"- {tradeoff}")
            st.caption(
                "The score summarizes how listed preferences match this record; it is not a probability or valuation."
            )
            st.json(selected["score_breakdown"])
        if st.button("Close details"):
            st.session_state.pop("selected_property", None)
            st.rerun()
