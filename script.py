import streamlit as st

# Title and header
st.title("Welcome to My Streamlit App")
st.header("This is a basic example")

# Input widgets
name = st.text_input("Enter your name:")
age = st.slider("Select your age:", 0, 100, 25)

# Display user input
if st.button("Submit"):
    st.write(f"Hello {name}, you are {age} years old!")

# Data visualization example
import pandas as pd
import numpy as np

# Create sample data
data = pd.DataFrame(
    np.random.randn(50, 2),
    columns=['x', 'y']
)

st.line_chart(data)
