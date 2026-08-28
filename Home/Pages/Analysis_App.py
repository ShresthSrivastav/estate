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


st.set_page_config(page_title="Analytics | Nestwise", page_icon="📊", layout="wide")


@st.cache_data(show_spinner=False)
def load_analytics_data():
    return pd.read_csv(ANALYTICS_DATA)


@st.cache_data(show_spinner=False)
def load_feature_text():
    try:
        with FEATURE_TEXT.open("rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return "Spacious rooms modern design prime location affordable pricing connectivity security amenities schools parks hospitals metro access"


new_df = load_analytics_data()
st.title("Market Analytics")
st.caption("A visual view of the same Gurgaon dataset used by the application.")

group_df = new_df.groupby("sector", as_index=False)[["price", "price_per_sqft", "built_up_area", "latitude", "longitude"]].mean()
st.subheader("Sector price-per-sqft map")
fig = px.scatter_mapbox(group_df, lat="latitude", lon="longitude", color="price_per_sqft", size="built_up_area", color_continuous_scale=px.colors.cyclical.IceFire, zoom=10, mapbox_style="open-street-map", hover_name="sector")
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Property language")
    if WordCloud is not None:
        wordcloud = WordCloud(width=800, height=500, background_color="#102a43", colormap="Pastel2").generate(load_feature_text())
        fig_wc, axis = plt.subplots(figsize=(8, 4.5), facecolor="#102a43")
        axis.imshow(wordcloud, interpolation="bilinear")
        axis.axis("off")
        st.pyplot(fig_wc, use_container_width=True)
    else:
        st.info("Install the requirements to render the word cloud.")
with right:
    st.subheader("Area vs price")
    property_type = st.selectbox("Property type", ["flat", "house"])
    filtered_df = new_df[new_df["property_type"] == property_type]
    st.plotly_chart(px.scatter(filtered_df, x="built_up_area", y="price", color="bedRoom"), use_container_width=True)

st.subheader("Bedrooms by sector")
sector_options = ["overall"] + sorted(new_df["sector"].dropna().unique().tolist())
selected_sector = st.selectbox("Sector", sector_options)
sector_df = new_df if selected_sector == "overall" else new_df[new_df["sector"] == selected_sector]
st.plotly_chart(px.pie(sector_df, names="bedRoom", title="Bedroom mix"), use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("BHK price ranges")
    st.plotly_chart(px.box(new_df[new_df["bedRoom"] <= 4], x="bedRoom", y="price"), use_container_width=True)
with right:
    st.subheader("Flat vs house prices")
    st.plotly_chart(px.histogram(new_df, x="price", color="property_type", marginal="box", barmode="overlay"), use_container_width=True)

st.subheader("Data summary")
st.dataframe(new_df.describe(include="all").transpose(), use_container_width=True)
