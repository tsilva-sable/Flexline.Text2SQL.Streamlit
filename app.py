import requests
import sqlparse
import streamlit as st

URL = st.secrets["URL"]
API_KEY = st.secrets["API_KEY"]  # Add this line to retrieve your API key

st.title("Flexline.Text2SQL")

user_input = st.text_input("Enter your question:", key="user_input")

if user_input:
    response = requests.get(
        f"{URL}/api/v1/query",
        params={"query": user_input},
        headers={
            "accept": "application/json",
            "X-API-KEY": API_KEY,  # Include the API key in the headers
        },
    )
    if response.status_code == 200:
        # Extract SQL query and read-only flag
        sql_query = response.json().get("sql_query")
        read_only = response.json().get(
            "read_only", False
        )  # Default to False if not present
        formatted_sql = sqlparse.format(sql_query, reindent=True, keyword_case="upper")

        # Display the formatted SQL query
        st.code(formatted_sql, language="sql")

        # Display execution time if available
        process_time = response.headers.get("x-process-time")
        if process_time:
            st.write(f"**Execution Time:** {float(process_time):.4f} seconds")

        # Display a status indicator for read-only
        if read_only:
            st.success("🔒 Read-Only Query")
        else:
            st.error("🔓 Read-Write Query")

    else:
        # Display error message from the API
        error_message = response.json().get("detail", "An unknown error occurred.")
        st.error(f"Error {response.status_code}: {error_message}")
