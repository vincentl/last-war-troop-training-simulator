import streamlit as st

# Read query parameters from the URL
params = st.experimental_get_query_params()
default_rate = params.get("rate", [""])[0]
default_goal = params.get("goal", [""])[0]

st.title("📌 Bookmarkable Streamlit App")

# Input fields
rate = st.text_input("Enter rate:", value=default_rate)
goal = st.text_input("Enter goal:", value=default_goal)

if rate and goal:
    st.write(f"📈 **Rate**: {rate}")
    st.write(f"🎯 **Goal**: {goal}")

    # Build a bookmarkable URL
    base_url = st.request.host_url.rstrip("/")
    new_url = f"{base_url}/?rate={rate}&goal={goal}"

    st.markdown("### 🔗 Shareable Link")
    st.markdown(f"[Click here to bookmark this version]({new_url})", unsafe_allow_html=True)

    # Open in new tab with a button
    js = f"window.open('{new_url}', '_blank').focus();"
    st.components.v1.html(f"<script>{js}</script>", height=0)
    st.button("Open in New Tab", on_click=lambda: None)
else:
    st.info("Enter both a rate and a goal to generate a bookmarkable link.")
