import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# Streamlit adds the script directory to imports; this also keeps direct page tests portable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.data_loader import PREDICTOR_PIPELINE, load_predictor_features


st.set_page_config(page_title="Price Predictor | Nestwise", page_icon="💰", layout="wide")


@st.cache_resource(show_spinner=False)
def load_pipeline():
    if PREDICTOR_PIPELINE.stat().st_size < 1024:
        raise RuntimeError("The model is a Git-LFS pointer. Pull Git-LFS assets before deploying.")
    with PREDICTOR_PIPELINE.open("rb") as file:
        return pickle.load(file)


@st.cache_data(show_spinner=False)
def load_features():
    return load_predictor_features()


st.title("Price Predictor")
st.caption("The original machine-learning component estimates a property's market price from its features.")

try:
    df = load_features()
    pipeline = load_pipeline()
except AttributeError:
    st.error("The saved model needs scikit-learn 1.6.1. Install the pinned requirements and restart the app.")
    st.stop()
except RuntimeError as error:
    st.error(str(error))
    st.info("Run `git lfs install` and `git lfs pull` locally, then push the Git-LFS object to GitHub.")
    st.stop()
except (FileNotFoundError, ModuleNotFoundError) as error:
    st.error(f"Price prediction assets could not be loaded: {error}")
    st.stop()
except (EOFError, ValueError, pickle.UnpicklingError) as error:
    st.error(f"The saved model could not be read: {error}")
    st.info("Confirm that the Git-LFS model was downloaded and committed through Git LFS.")
    st.stop()


def options(column):
    values = df[column].dropna().unique().tolist()
    return sorted(values, key=lambda value: str(value))


with st.form("price_prediction"):
    st.subheader("Property details")
    first, second, third = st.columns(3)
    with first:
        property_type = st.selectbox("Property type", ["flat", "house"])
        sector = st.selectbox("Sector", options("sector"))
        bedrooms = float(st.selectbox("Bedrooms", sorted(df["bedRoom"].dropna().unique().tolist())))
        bathroom = float(st.selectbox("Bathrooms", sorted(df["bathroom"].dropna().unique().tolist())))
    with second:
        balcony = st.selectbox("Balconies", options("balcony"))
        property_age = st.selectbox("Property age", options("agePossession"))
        built_up_area = st.number_input("Built-up area (sq.ft.)", min_value=100.0, value=1200.0, step=50.0)
        furnishing_type = st.selectbox("Furnishing type", options("furnishing_type"))
    with third:
        servant_room = float(st.selectbox("Servant room", [0.0, 1.0]))
        store_room = float(st.selectbox("Store room", [0.0, 1.0]))
        luxury_category = st.selectbox("Luxury category", options("luxury_category"))
        floor_category = st.selectbox("Floor category", options("floor_category"))
    submitted = st.form_submit_button("Estimate price", type="primary", width="stretch")

if submitted:
    columns = [
        "property_type", "sector", "bedRoom", "bathroom", "balcony", "agePossession",
        "built_up_area", "servant room", "store room", "furnishing_type", "luxury_category", "floor_category",
    ]
    values = [[property_type, sector, bedrooms, bathroom, balcony, property_age, built_up_area, servant_room, store_room, furnishing_type, luxury_category, floor_category]]
    one_df = pd.DataFrame(values, columns=columns)
    expected = list(getattr(pipeline, "feature_names_in_", columns))
    for column in expected:
        if column not in one_df:
            one_df[column] = 0
    one_df = one_df[expected]
    try:
        base_price = max(float(np.expm1(pipeline.predict(one_df))[0]), 0)
        st.success(f"Estimated price: ₹{base_price:.2f} Cr")
        low, high = base_price * 0.9, base_price * 1.1
        st.caption(f"Indicative range: ₹{low:.2f} Cr – ₹{high:.2f} Cr · model estimate, not a valuation or offer")
    except Exception as error:
        st.error(f"Prediction failed: {error}")
