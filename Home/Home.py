import streamlit as st


st.set_page_config(page_title="Nestwise | Gurgaon homes", page_icon="🏠", layout="wide")

st.markdown(
    """
    <style>
    .block-container { max-width: 1180px; padding-top: 2rem; }
    .hero { padding: 3.5rem 3rem; border-radius: 28px; background: linear-gradient(120deg, #102a43, #176b87); color: white; margin-bottom: 2rem; }
    .eyebrow { color: #a7e8d0; letter-spacing: .14em; font-size: .75rem; font-weight: 700; }
    .hero h1 { font-size: clamp(2.2rem, 5vw, 4.5rem); line-height: 1; margin: .8rem 0 1rem; }
    .hero p { color: #d9f3f0; font-size: 1.1rem; max-width: 660px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="hero">
      <div class="eyebrow">NESTWISE · GURGAON PROPERTY DISCOVERY</div>
      <h1>Find a home that fits<br>the way you live.</h1>
      <p>Explore data-backed property prices and get transparent recommendations that respect your location and budget first.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.write("### A smarter way to explore real estate")
st.write("Nestwise combines the original price prediction model with an explainable recommendation workflow built on the project's cleaned property data.")

first, second, third = st.columns(3)
first.metric("3,554", "cleaned property records")
second.metric("2", "core tools")
third.metric("100%", "location + budget first")

st.divider()
left, right = st.columns([1.2, 1])
with left:
    st.subheader("Start with your brief")
    st.write("Set a hard location and maximum budget, then let preference matching bring the most relevant options to the top.")
    st.page_link("Pages/Property_Recommender.py", label="Find my property →", icon="🏠")
with right:
    st.info("**Demo dataset**\n\nProperty cards use local illustrative images. Prices and attributes come from the project's real cleaned dataset; they are not active listings.")

st.write("### Explore the project")
a, b = st.columns(2)
with a:
    st.page_link("Pages/Price_Predictor.py", label="Estimate a property's price", icon="💰")
with b:
    st.page_link("Pages/Analysis_App.py", label="View market analytics", icon="📊")
