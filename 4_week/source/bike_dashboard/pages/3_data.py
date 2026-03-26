# pages/3_data.py
import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.data_loader import load_bike_data, get_station_summary

st.title('🔍 데이터 조회')

df = load_bike_data()
summary = get_station_summary(df)

tab1, tab2 = st.tabs(['대여소 요약', '원본 데이터'])

with tab1:
    st.subheader('대여소별 요약 통계')

    # 행 선택 가능한 데이터프레임
    event = st.dataframe(
        summary,
        on_select="rerun",
        selection_mode="multi-row",
        use_container_width=True,
        column_config={
            '총대여건수': st.column_config.NumberColumn(format="%d 건"),
            '평균이용시간': st.column_config.NumberColumn(format="%.1f 분"),
            '일평균대여': st.column_config.ProgressColumn(
                min_value=0,
                max_value=summary['일평균대여'].max(),
                format="%.0f건/일"
            )
        }
    )

    # 선택한 대여소 상세 정보
    selected = event.selection.rows
    if selected:
        selected_stations = summary.iloc[selected]['대여소'].tolist()
        st.subheader(f'선택한 대여소: {", ".join(selected_stations)}')

        detail = df[df['대여소'].isin(selected_stations)]
        hourly_detail = detail.groupby(['대여소', '시간대'])['대여건수'].mean().reset_index()

        import plotly.express as px
        fig = px.line(hourly_detail, x='시간대', y='대여건수',
                      color='대여소', markers=True,
                      title='선택 대여소 시간대별 평균 대여 패턴')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader('원본 데이터')

    # Form으로 필터 모아서 적용 (1교시에서 배운 패턴)
    with st.form('data_filter'):
        col1, col2 = st.columns(2)
        with col1:
            station_filter = st.multiselect('대여소', df['대여소'].unique(), default=df['대여소'].unique())
        with col2:
            hour_range = st.slider('시간대 범위', 0, 23, (0, 23))

        submitted = st.form_submit_button('필터 적용', use_container_width=True)

    filtered = df[
        (df['대여소'].isin(station_filter)) &
        (df['시간대'] >= hour_range[0]) &
        (df['시간대'] <= hour_range[1])
    ]

    st.write(f'검색 결과: **{len(filtered):,}건**')
    st.dataframe(filtered, use_container_width=True, height=400)

    # CSV 다운로드
    csv = filtered.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label='📥 CSV 다운로드',
        data=csv,
        file_name='bike_data_filtered.csv',
        mime='text/csv'
    )
