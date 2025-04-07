import pandas as pd
import requests
import sqlparse
import streamlit as st

URL = st.secrets["URL"]
API_KEY = st.secrets["API_KEY"]

st.title("Flexline.Text2SQL")

# Add a toggle button for sql_only parameter
show_results = st.toggle("Show Results", value=False)
sql_only = not show_results

user_input = st.text_input("Enter your question:", key="user_input")

# Define token pricing constants
INPUT_TOKEN_PRICE = 0.003 / 1000  # $0.003 per 1000 input tokens
OUTPUT_TOKEN_PRICE = 0.015 / 1000  # $0.015 per 1000 output tokens

if user_input:
    response = requests.get(
        f"{URL}/api/v1/query",
        params={"query": user_input, "sql_only": sql_only},
        headers={
            "accept": "application/json",
            "X-API-KEY": API_KEY,
        },
    )

    if response.status_code == 200:
        response_data = response.json()

        # Extract SQL query and read-only flag
        sql_query = response_data.get("sql_query")
        read_only = response_data.get("read_only", False)

        formatted_sql = sqlparse.format(sql_query, reindent=True, keyword_case="upper")

        # Display the formatted SQL query
        st.code(formatted_sql, language="sql")

        # Display execution time if available
        process_time = response.headers.get("x-process-time")
        if process_time:
            st.write(f"**Execution Time:** {float(process_time):.4f} seconds")

        # Extract token counts and calculate cost
        prompt_tokens = response.headers.get("x-prompt-tokens")
        completion_tokens = response.headers.get("x-completion-tokens")

        if prompt_tokens and completion_tokens:
            prompt_tokens = int(prompt_tokens)
            completion_tokens = int(completion_tokens)
            total_tokens = prompt_tokens + completion_tokens

            # Calculate cost
            input_cost = prompt_tokens * INPUT_TOKEN_PRICE
            output_cost = completion_tokens * OUTPUT_TOKEN_PRICE
            total_cost = input_cost + output_cost

            # Create a collapsible section for token usage and cost
            with st.expander("📊 Token Usage & Cost Details"):
                # Create a DataFrame for the token metrics
                token_data = {
                    "Category": ["Input", "Output", "Total"],
                    "Tokens": [
                        f"{prompt_tokens:,}",
                        f"{completion_tokens:,}",
                        f"{total_tokens:,}",
                    ],
                    "Cost": [
                        f"${input_cost:.6f}",
                        f"${output_cost:.6f}",
                        f"${total_cost:.6f}",
                    ],
                }
                df = pd.DataFrame(token_data)
                # Use st.table with hide_index=True to remove the index column
                st.table(df.set_index("Category"))

        # Display a status indicator for read-only
        if read_only:
            st.success("🔒 Read-Only Query")
        else:
            st.error("🔓 Read-Write Query")

        # Display query results if sql_only is False (moved to the end)
        if not sql_only and "result" in response_data and response_data["result"]:
            st.subheader("Query Results")
            results_df = pd.DataFrame(response_data["result"])

            # Format numeric columns with thousand separators
            for col in results_df.columns:
                if pd.api.types.is_numeric_dtype(results_df[col]):
                    results_df[col] = results_df[col].apply(lambda x: f"{x:,}")

            st.dataframe(
                results_df, hide_index=True
            )  # hide_index=True removes the index column
    else:
        # Display error message from the API
        error_message = response.json().get("detail", "An unknown error occurred.")
        st.error(f"Error {response.status_code}: {error_message}")
