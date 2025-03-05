# styling.py

import streamlit as st

def apply_styling():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #FF4B4B;
            text-align: center;
        }
        .sub-header {
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        .chinese-text {
            font-size: 2rem;
            color: #FF4B4B;
            margin: 1rem 0;
        }
        .pinyin-text {
            font-size: 1.2rem;
            color: #636EFA;
            margin-bottom: 1.5rem;
        }
        .instruction-text {
            font-size: 1rem;
            color: #7F7F7F;
            margin: 1rem 0;
        }
        .grade-s {color: #00CC96;}
        .grade-a {color: #636EFA;}
        .grade-b {color: #FFA15A;}
        .grade-c {color: #EF553B;}
        .grade-d {color: #AB63FA;}
        .char-correct {
            color: #00CC96;
            font-weight: bold;
        }
        .char-incorrect {
            color: #EF553B;
            text-decoration: line-through;
        }
        .stApp {
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)