import pickle
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.data_loader import ANALYTICS_DATA, FEATURE_TEXT

try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
except ImportError:
    WordCloud = None
    plt = None


st.set_page_config(page_title="Analytics | Nestwise", page_icon="📊", layout="wide")

REQUIRED_COLUMNS = {
    "property_type",
    "sector",
    "price",
    "price_per_sqft",
    "bedRoom",
    "built_up_area",
    "latitude",
    "longitude",
}
NUMERIC_COLUMNS = [
    "price",
    "price_per_sqft",
    "bedRoom",
    "built_up_area",
    "latitude",
    "longitude",
]
FALLBACK_WORDS = (
    "Spacious rooms modern design prime location affordable pricing "
    "connectivity security amenities schools parks hospitals metro access"
)


@st.cache_data(show_spinner=False)
def load_analytics_data():
    data = pd.read_csv(ANALYTICS_DATA)
    missing = sorted(REQUIRED_COLUMNS.difference(data.columns))
    if missing:
        raise ValueError(f"Missing analytics columns: {', '.join(missing)}")

    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    if data.empty:
        raise ValueError("The analytics dataset is empty.")
    return data


@st.cache_data(show_spinner=False)
def load_feature_text():
    try:
        with FEATURE_TEXT.open("rb") as file:
            return str(pickle.load(file))
    except (FileNotFoundError, OSError, EOFError, pickle.UnpicklingError, ValueError):
        return FALLBACK_WORDS


@st.cache_data(show_spinner=False)
def make_wordcloud(text):
    if WordCloud is None or not text.strip():
        return None
    return WordCloud(
        width=800,
        height=500,
        background_color="#102a43",
        colormap="Pastel2",
    ).generate(text).to_array()


try:
    new_df = load_analytics_data()
except (FileNotFoundError, OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as error:
    st.error(f"Analytics data could not be loaded: {error}")
    st.stop()

st.title("Market Analytics")
st.caption("A visual view of the same Gurgaon dataset used by the application.")

map_df = new_df.dropna(
    subset=["sector", "price_per_sqft", "built_up_area", "latitude", "longitude"]
)
st.subheader("Sector price-per-sqft map")
if map_df.empty:
    st.info("The dataset has no complete location records for the map.")
else:
    group_df = map_df.groupby("sector", as_index=False)[
        ["price", "price_per_sqft", "built_up_area", "latitude", "longitude"]
    ].mean()
    fig = px.scatter_map(
        group_df,
        lat="latitude",
        lon="longitude",
        color="price_per_sqft",
        size="built_up_area",
        color_continuous_scale=px.colors.cyclical.IceFire,
        zoom=10,
        map_style="open-street-map",
        hover_name="sector",
    )
    st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("Property language")
    wordcloud = make_wordcloud(load_feature_text())
    if wordcloud is not None and plt is not None:
        fig_wc, axis = plt.subplots(figsize=(8, 4.5), facecolor="#102a43")
        axis.imshow(wordcloud, interpolation="bilinear")
        axis.axis("off")
        st.pyplot(fig_wc, width="stretch")
        plt.close(fig_wc)
    else:
        st.info("The word cloud is unavailable because its optional dependency is not installed.")
with right:
    st.subheader("Area vs price")
    property_types = sorted(new_df["property_type"].dropna().astype(str).unique().tolist())
    if not property_types:
        st.info("No property types are available for this chart.")
    else:
        property_type = st.selectbox("Property type", property_types)
        filtered_df = new_df[
            new_df["property_type"].astype("string") == property_type
        ].dropna(subset=["built_up_area", "price", "bedRoom"])
        if filtered_df.empty:
            st.info("No complete area and price records are available for this property type.")
        else:
            st.plotly_chart(
                px.scatter(filtered_df, x="built_up_area", y="price", color="bedRoom"),
                width="stretch",
            )

st.subheader("Bedrooms by sector")
sector_options = ["overall"] + sorted(
    new_df["sector"].dropna().astype(str).unique().tolist()
)
selected_sector = st.selectbox("Sector", sector_options)
sector_df = new_df if selected_sector == "overall" else new_df[
    new_df["sector"].astype("string") == selected_sector
]
sector_df = sector_df.dropna(subset=["bedRoom"])
if sector_df.empty:
    st.info("No bedroom records are available for this selection.")
else:
    pie_df = sector_df.assign(bedRoom=sector_df["bedRoom"].astype(str))
    st.plotly_chart(
        px.pie(pie_df, names="bedRoom", title="Bedroom mix"),
        width="stretch",
    )

left, right = st.columns(2)
with left:
    st.subheader("BHK price ranges")
    box_df = new_df.dropna(subset=["bedRoom", "price"])
    box_df = box_df[box_df["bedRoom"] <= 4]
    if box_df.empty:
        st.info("No complete bedroom and price records are available.")
    else:
        st.plotly_chart(px.box(box_df, x="bedRoom", y="price"), width="stretch")
with right:
    st.subheader("Flat vs house prices")
    histogram_df = new_df.dropna(subset=["price", "property_type"])
    if histogram_df.empty:
        st.info("No complete price and property-type records are available.")
    else:
        st.plotly_chart(
            px.histogram(
                histogram_df,
                x="price",
                color="property_type",
                marginal="box",
                barmode="overlay",
            ),
            width="stretch",
        )

st.subheader("Data summary")
st.dataframe(new_df.describe(include="all").transpose(), width="stretch")
