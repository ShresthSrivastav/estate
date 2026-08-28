from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "model selection"
HOME_DIR = PROJECT_ROOT / "Home"
ASSET_DIR = PROJECT_ROOT / "assets" / "images"

RECOMMENDER_DATA = MODEL_DIR / "gurgaon_properties_post_feature_selection_v2.csv"
PREDICTOR_FEATURES = MODEL_DIR / "df.pkl"
PREDICTOR_PIPELINE = MODEL_DIR / "pipeline.pkl"
ANALYTICS_DATA = HOME_DIR / "data_viz1.csv"
FEATURE_TEXT = HOME_DIR / "feature_text.pkl"


def load_recommender_data() -> pd.DataFrame:
    """Load the cleaned, feature-selected records used by the project."""
    return pd.read_csv(RECOMMENDER_DATA)


def load_predictor_features() -> pd.DataFrame:
    return pd.read_pickle(PREDICTOR_FEATURES)
