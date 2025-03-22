

import streamlit as st
from urllib.parse import urlencode

def get_query_params_url(params_list, params_dict, **kwargs):
    """
    Generate a query string from selected parameters.
    Produced by ChatGPT o3-mini-high based on https://discuss.streamlit.io/t/get-url-from-streamlit-app/33419/12

    Args:
        params_list (list): A list of parameter names to include.
        params_dict (dict): A dictionary containing parameter values.
        **kwargs: Additional parameters to include.
    
    Returns:
        str: A query string starting with '?'.
    """
    # Merge params_dict with any additional keyword args
    combined = {**params_dict, **kwargs}
    # Only include keys specified in params_list
    filtered = {k: v for k, v in combined.items() if k in params_list}
    return "?" + urlencode(filtered, doseq=True)

# Access query parameters (using the new API: st.query_params as a property)
params = st.query_params  
default_rate = params.get("rate", [""])
default_goal = params.get("goal", [""])

st.title("📌 Bookmarkable Streamlit App")

# Input fields for rate and goal
rate = st.text_input("Enter rate:", value=default_rate)
goal = st.text_input("Enter goal:", value=default_goal)


st.header("Dataset 1: Up to 4 Rows (Level & Capacity)")
# Create a default DataFrame with 4 rows and two columns.
default_df1 = pd.DataFrame({
    "level": ["", "", "", ""],
    "capacity": ["", "", "", ""]
})
# Using a fixed number of rows so users see exactly 4 rows.
data1 = st.data_editor(default_df1, num_rows="fixed", key="dataset1")

st.header("Dataset 2: 10 Rows (Count & Time)")
# Create a DataFrame with an index from 10 down to 1.
default_df2 = pd.DataFrame({
    "count": ["" for _ in range(10)],
    "time": ["" for _ in range(10)]
}, index=list(range(10, 0, -1)))
# Fixed rows so users can only edit the provided rows.
data2 = st.data_editor(default_df2, num_rows="fixed", key="dataset2")


if rate and goal:
    # Create the query string
    query_string = get_query_params_url(["rate", "goal"], {"rate": rate, "goal": goal})
    
    st.markdown("### 🔗 Bookmarkable Link")
    st.markdown("You can copy the query string below and bookmark or share this specific state:")
    st.code(query_string, language="text")
    
    # Using a relative link; when clicked, it reloads the current page with the new query parameters.
    st.markdown(f"[Open Bookmarkable Link]({query_string})")

    st.write(f"**Rate:** {rate}")
    st.write(f"**Goal:** {goal}")
else:
    st.info("Enter both a rate and a goal to generate a bookmarkable link.")
