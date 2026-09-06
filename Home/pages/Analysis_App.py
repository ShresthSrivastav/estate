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


@st.cache_data(show_spinner=False)
def make_wordcloud(text):
    return WordCloud(width=800, height=500, background_color="#102a43", colormap="Pastel2").generate(text).to_array()


new_df = load_analytics_data()
st.title("Market Analytics")
st.caption("A visual view of the same Gurgaon dataset used by the application.")

group_df = new_df.groupby("sector", as_index=False)[["price", "price_per_sqft", "built_up_area", "latitude", "longitude"]].mean()
st.subheader("Sector price-per-sqft map")
fig = px.scatter_map(group_df, lat="latitude", lon="longitude", color="price_per_sqft", size="built_up_area", color_continuous_scale=px.colors.cyclical.IceFire, zoom=10, map_style="open-street-map", hover_name="sector")
st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("Property language")
    if WordCloud is not None:
        wordcloud = make_wordcloud(load_feature_text())
        fig_wc, axis = plt.subplots(figsize=(8, 4.5), facecolor="#102a43")
        axis.imshow(wordcloud, interpolation="bilinear")
        axis.axis("off")
        st.pyplot(fig_wc, width="stretch")
        plt.close(fig_wc)
    else:
        st.info("Install the requirements to render the word cloud.")
with right:
    st.subheader("Area vs price")
    property_type = st.selectbox("Property type", ["flat", "house"])
    filtered_df = new_df[new_df["property_type"] == property_type]
    st.plotly_chart(px.scatter(filtered_df, x="built_up_area", y="price", color="bedRoom"), width="stretch")

st.subheader("Bedrooms by sector")
sector_options = ["overall"] + sorted(new_df["sector"].dropna().unique().tolist())
selected_sector = st.selectbox("Sector", sector_options)
sector_df = new_df if selected_sector == "overall" else new_df[new_df["sector"] == selected_sector]
st.plotly_chart(px.pie(sector_df, names="bedRoom", title="Bedroom mix"), width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("BHK price ranges")
    st.plotly_chart(px.box(new_df[new_df["bedRoom"] <= 4], x="bedRoom", y="price"), width="stretch")
with right:
    st.subheader("Flat vs house prices")
    st.plotly_chart(px.histogram(new_df, x="price", color="property_type", marginal="box", barmode="overlay"), width="stretch")

st.subheader("Data summary")
st.dataframe(new_df.describe(include="all").transpose(), width="stretch")
