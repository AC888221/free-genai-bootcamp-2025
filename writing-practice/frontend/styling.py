# styling.py

import streamlit as st

ddef apply_styling():
    st.markdown("""
    <style>
        .main-header {
            font-size: 3.75rem;  /* Increased by 25% */
            color: #4B0082;
            text-align: center;
            margin-bottom: 2rem;
        }
        .sub-header {
            font-size: 2.5rem;  /* Increased by 25% */
            color: #4B0082;
            margin-bottom: 1rem;
        }
        .chinese-text {
            font-size: 3.125rem;  /* Increased by 25% */
            color: #FF4500;
            margin: 1rem 0;
        }
        .pinyin-text {
            font-size: 1.875rem;  /* Increased by 25% */
            color: #1E90FF;
            margin-bottom: 1.5rem;
        }
        .instruction-text {
            font-size: 1.5rem;  /* Increased by 25% */
            color: #696969;
            margin: 1rem 0;
        }
        .grade-s {color: #00CC96;}
        .grade-a {color: #1E90FF;}
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
        .word-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 2rem;
        }
        .word-table th, .word-table td {
            border: 1px solid #DDDDDD;
            padding: 0.5rem;
            text-align: left;
        }
        .word-table th {
            font-size: 1.875rem;  /* Increased by 25% */
            color: #4B0082;
            background-color: #F0F8FF;
        }
        .word-table td {
            font-size: 1.5rem;  /* Increased by 25% */
            color: #333333;
        }
    </style>
    """, unsafe_allow_html=True)