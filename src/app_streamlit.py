# app_streamlit.py
import streamlit as st
import requests
import numpy as np
import pandas as pd

st.title("Flood Prediction Demo (North Cyprus)")

st.write("Enter last 7 days rainfall (mm) and temperature (°C).")

cols = st.columns(2)
with cols[0]:
    tp_input = []
    for i in range(7):
        tp_input.append(st.number_input(f"tp t-{7-i}", min_value=0.0, value=0.0, step=0.1, key=f"tp{i}"))
with cols[1]:
    t2m_input = []
    for i in range(7):
        t2m_input.append(st.number_input(f"t2m t-{7-i}", min_value=-50.0, value=15.0, step=0.1, key=f"t2m{i}"))

if st.button("Predict"):
    payload = {"tp_history": tp_input, "t2m_history": t2m_input}
    try:
        res = requests.post("http://127.0.0.1:8000/predict", json=payload, timeout=10)
        data = res.json()
        st.metric("Predicted rainfall (mm)", f"{data['next_day_rainfall_mm']:.2f}")
        st.metric("Flood probability", f"{data['flood_probability']:.2%}")
    except Exception as e:
        st.error(f"API Error: {e}")
