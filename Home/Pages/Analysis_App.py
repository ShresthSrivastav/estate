import streamlit as st
import pandas as pd
import plotly.express as px
import pickle
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(page_title="Plotting Demo")
st.title('Analytics')

# Load CSV file
new_df = pd.read_csv('data_viz1.csv')

# Check if 'feature_text.pkl' exists, if not, create it
if not os.path.exists("feature_text.pkl"):
    feature_text = """
    Spacious rooms, modern design, prime location, affordable pricing, 
    excellent connectivity, high security, luxury amenities, nearby schools, 
    parks, hospitals, shopping malls, metro access, earthquake-resistant, 
    24/7 water supply, gated community, eco-friendly, smart home features
    """
    with open("feature_text.pkl", "wb") as file:
        pickle.dump(feature_text, file)

# Load the feature text from the pickle file
feature_text = pickle.load(open("feature_text.pkl", "rb"))

# Grouping data by sector
numeric_cols = ['price', 'price_per_sqft', 'built_up_area', 'latitude', 'longitude']
group_df = new_df.groupby('sector', as_index=False)[numeric_cols].mean()

# ---- Geomap ----
st.header('Sector Price per Sqft Geomap')
fig = px.scatter_mapbox(group_df, lat="latitude", lon="longitude", color="price_per_sqft", size='built_up_area',
                        color_continuous_scale=px.colors.cyclical.IceFire, zoom=10,
                        mapbox_style="open-street-map", width=1200, height=700, hover_name=group_df["sector"])
st.plotly_chart(fig, use_container_width=True)

# ---- Word Cloud ----
st.header('Features Wordcloud')
wordcloud = WordCloud(width=800, height=800, background_color='black', min_font_size=10).generate(feature_text)

plt.figure(figsize=(8, 8), facecolor=None)
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.tight_layout(pad=0)
st.pyplot()

# ---- Area vs Price Scatter Plot ----
st.header('Area Vs Price')
property_type = st.selectbox('Select Property Type', ['flat', 'house'])

filtered_df = new_df[new_df['property_type'] == property_type]
fig1 = px.scatter(filtered_df, x="built_up_area", y="price", color="bedRoom", title="Area Vs Price")
st.plotly_chart(fig1, use_container_width=True)

# ---- BHK Pie Chart ----
st.header('BHK Pie Chart')
sector_options = ['overall'] + new_df['sector'].unique().tolist()
selected_sector = st.selectbox('Select Sector', sector_options)

sector_df = new_df if selected_sector == 'overall' else new_df[new_df['sector'] == selected_sector]
fig2 = px.pie(sector_df, names='bedRoom')
st.plotly_chart(fig2, use_container_width=True)

# ---- BHK Price Comparison ----
st.header('Side by Side BHK price comparison')
fig3 = px.box(new_df[new_df['bedRoom'] <= 4], x='bedRoom', y='price', title='BHK Price Range')
st.plotly_chart(fig3, use_container_width=True)

# ---- Property Type Price Distribution ----
st.header('Side by Side Distplot for property type')
fig4 = plt.figure(figsize=(10, 4))
sns.histplot(new_df[new_df['property_type'] == 'house']['price'], label='house', kde=True)
sns.histplot(new_df[new_df['property_type'] == 'flat']['price'], label='flat', kde=True)
plt.legend()
st.pyplot(fig4)

# ---- Data Summary ----
st.write("## Data Summary")
st.write(new_df.describe())
