import streamlit as st

st.set_page_config(
    page_title="졸음 감지 서비스",
    page_icon="😴",
    layout="wide",
)

pages = [
    st.Page("pages/1_EDA.py",         title="데이터 탐색",        icon="🔍"),
    st.Page("pages/2_시각화.py",       title="데이터 시각화",      icon="📊"),
    st.Page("pages/3_모델학습.py",     title="CNN 모델 학습",      icon="🏋️"),
    st.Page("pages/3_1_ViT학습.py",    title="ViT 모델 학습",      icon="🤖"),
    st.Page("pages/4_모델_서비스.py",  title="졸음 감지 서비스",   icon="😴"),
]

pg = st.navigation(pages)
pg.run()
