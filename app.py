import streamlit as st
import plotly.express as px
from dataclasses import dataclass
from strategy import Barrack, BaseTrainRate, BasePromoteRate, simulate

# --- App starts here ---
st.title('Last War Training Strategy')

# Goal
st.subheader('Training Goal')
goal = st.number_input('Enter total number of troops to train', value=5000)

# Strategy
st.subheader('Training Strategy')
strategy_options = {
    'Min level Minus One — train troops at one level less than lowest barrack level': 'min - 1',
    'Max barracks level — train troops at the maximum available level': 'max level'
}
display_choice = st.selectbox('Choose how to initially train troops', list(strategy_options.keys()))
strategy = strategy_options[display_choice]

# Barracks input
st.subheader('Barracks')
st.markdown('> Enter level and capacity of each barracks (set capacity to zero for fewer than 4 barracks)')
barracks = []
columns = st.columns(2)
for (index, (level_default, capacity_default)) in enumerate([(9,723),(8,647),(7,589),(6,561)]):
    with columns[index % 2]:
        st.markdown(f'**Barrack {index + 1}**')
        level = st.number_input(
            f'Level', min_value=1, max_value=10,
            value=level_default, key=f'level_{index}'
        )
        capacity = st.number_input(
            f'Capacity', min_value=0,
            value=capacity_default, key=f'capacity_{index}'
        )
        barracks.append(Barrack(level=level, capacity=capacity, index=index))

# Train rate input
st.subheader('Training Base Rate')
train_level = st.number_input('Troops trained at level', value=9)
train_capacity = st.number_input('Number of troops trained', value=723)
train_duration = st.text_input('Duration (e.g. "1d 07:45:09")', value='1d 07:45:09')
base_train_rate = BaseTrainRate(train_level, train_capacity, train_duration)

# Promote rate input
st.subheader('Promotion Base Rate')
st.markdown('> Enter details for promoting troops **one** level')
promote_capacity = st.number_input('Promote capacity', value=723)
promote_duration = st.text_input('Promote duration (e.g. "03:10:31")', value='03:10:31')
base_promote_rate = BasePromoteRate(promote_capacity, promote_duration)

# Submit
if st.button('Calculate Plan'):
    wall_time, dataframe, barrack_time = simulate(barracks, base_train_rate, base_promote_rate, goal, strategy)
    fig = px.timeline(
        dataframe,
        x_start='Start',
        x_end='Finish',
        y='Type',
        color='Type',
        facet_row='Barrack',
        hover_data={
            'Task': True,
            'Start@': True,
            'Finish@': True,
            'Duration': True,
            'Barrack': False,
            'Start': False,
            'Finish': False
        }
    )
    fig.update_yaxes(autorange='reversed',title='Activity')
    fig.update_layout(
        title='Training & Promotion Timeline',
        xaxis_title='Simulation Time',
        yaxis_title='Barracks',
        legend_title='Activity Type',
        height=600,
        showlegend=False
    )

    st.success(f'🕒 Total wall time to train {goal} troops: {wall_time}')
    st.info(f'🏗️  Total barrack time (sum of all activities): {barrack_time}')
    st.plotly_chart(fig, use_container_width=True)
    with st.expander('Show detailed activity table'):
        st.dataframe(dataframe)
