# Nestwise — PBL Project Extended

Nestwise is an extended version of the Gurgaon real-estate PBL project. It keeps the original cleaned datasets, notebooks, analytics, feature engineering work, and trained price-prediction pipeline, then adds an explainable property recommender and a presentation-ready Streamlit interface.

## Problem statement

Property search is often a trade-off between a fixed location, a fixed budget, and many softer preferences. Nestwise first removes infeasible properties using hard constraints, then ranks the remaining real dataset records by preference fit.

## Two different systems

**Price prediction** uses the saved scikit-learn pipeline. Given property features, it estimates a market price in crores.

**Recommendation** is constraint-based. Location and maximum budget are mandatory filters. Property type, bedrooms, bathrooms, area, furnishing, luxury, floor, balcony, servant room, and store room are optional ranking preferences. No relaxed result is mixed into the exact result list.

```text
User constraints
      ↓
Hard filter: sector == selected sector AND price <= maximum budget
      ↓
Feasible candidates
      ↓
Weighted preference matching
      ↓
Score, explanation, and sorting
      ↓
Top 5 or top 10 exact recommendations
```

The score is intentionally transparent: location and budget are always active, while each selected preference contributes a documented weight. Every card's reasons and trade-offs are generated from those same comparisons.

## Features

- Modern Home landing page
- Original ML Price Predictor, loaded from `model selection/pipeline.pkl`
- Property Recommender with exact sector and budget constraints
- Best Match, Lowest Price, Largest Area, Most Bedrooms, Best Budget Fit, and Closest Location sorting
- Match percentages, budget utilization, score breakdown, comparisons, and property details
- Nearby-sector matching using the dataset's sector coordinates
- Session-only saved properties and explicitly labeled fallback budget flexibility
- Local illustrative demo images in `assets/images/`
- Clearly labelled demo location-search links instead of invented listing URLs
- Existing Analytics page with map, word cloud, area/price, BHK, price distribution, and summary views
- Cached data/model loading and portable `pathlib` paths
- Explicit relaxed alternatives for no-result searches

## Project structure

```text
Home/
  Home.py
  pages/
    Price_Predictor.py
    Property_Recommender.py
    Analysis_App.py
  utils/
    data_loader.py
    recommender.py
assets/images/                 # local illustrative demo images
model selection/               # original model, features, and model-selection notebook
Cleaning/ Data/ EDA/ ...       # original project workflow and datasets
requirements.txt
```

## Run locally

From the repository root:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run Home/Home.py
```

The saved pipeline was produced with scikit-learn 1.6.1, so keep that requirement pinned. The model file is stored with Git LFS in the extended repository.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud and choose **New app**.
3. Select the repository, the branch, and `Home/Home.py` as the main file.
4. Deploy. `requirements.txt`, the datasets, model, and local images are loaded from the repository.

## Limitations

The dataset is a historical/demo dataset and recommendation scores indicate feature fit, not a guarantee of availability or investment performance. The illustrative images are not photographs of individual dataset records. The demo location link opens a sector-level map search rather than an exact listing.

## Future improvements

Future versions could add live listing ingestion, user accounts, persistent saved searches, and a model registry for safer pipeline versioning.
