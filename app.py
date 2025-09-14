import os
import json
import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# --- Authentication Setup ---
# Use Streamlit secrets to securely store and load the Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"

# --- BigQuery Function ---
# Encapsulate all the BigQuery logic in a function for clarity and reusability

def get_rag_response_from_bigquery(question: str):
    """
    Sends a question to BigQuery, runs the RAG SQL query, and returns the answer.
    """
    try:
        # Prefer credentials from Streamlit secrets if available
        credentials = None
        if "gcp_service_account" in st.secrets:
            # Best practice: store service account as a TOML table in secrets
            sa_info = dict(st.secrets["gcp_service_account"])  # already a dict, no json.loads
            credentials = service_account.Credentials.from_service_account_info(
                sa_info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        elif "GOOGLE_APPLICATION_CREDENTIALS" in st.secrets:
            # If stored as a JSON string, ensure newlines in private_key are escaped (\n)
            sa_json = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]
            sa_info = json.loads(sa_json)
            credentials = service_account.Credentials.from_service_account_info(
                sa_info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        else:
            # Fallback: local file
            credentials = service_account.Credentials.from_service_account_file(
                "google_credentials.json",
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )

        # Initialize the BigQuery client with explicit credentials and project
        project_id = "master-booster-469602-q2"
        client = bigquery.Client(credentials=credentials, project=project_id)

        # IMPORTANT: Use query parameters to prevent SQL injection!
        # This is the secure way to pass user input into a query.
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("new_question", "STRING", question)
            ]
        )

        # Your final, working SQL query, with a placeholder @new_question
        # for the user's input.
        sql_query = """
                                WITH
                          question_embedding AS (
                            SELECT
                              p.ml_generate_embedding_result AS embedding
                            FROM
                              ML.GENERATE_EMBEDDING(
                                MODEL `master-booster-469602-q2.kaggle.text_embedding_model`,
                                (SELECT @new_question AS content)
                              ) AS p
                          ),
                          retrieved_matches AS (
                            SELECT
                              base.ticket_id,
                              base.problem_description as question,
                              base.resolution_text AS answer,
                              distance
                            FROM
                              VECTOR_SEARCH(
                                TABLE `master-booster-469602-q2.kaggle.stackoverflow_with_embeddings`,
                                'embedding',
                                (SELECT embedding FROM question_embedding),
                                top_k => 3
                              )
                          ),
                          prompt_generation AS (
                            SELECT
                              CONCAT(
                                'You are an expert developer assistant. Your task is to answer the users question based STRICTLY and ONLY on the numbered context provided below. Do not use any other knowledge.',
                                'Provide your answer in CLEAR MARKDOWN FORMAT.',
                                'The answer must include:',
                                '1. A one-sentence **Summary** of the solution.',
                                '2. A numbered list of **Solution Steps**.',
                                '3. A `python` formatted **Code Example** if applicable.',
                                '4. **Cite your sources**. At the end of any sentence that uses information from a source, add the source ID, like this: [Source ID: 12345].',
                                '---',
                                'CONTEXT:',
                                IFNULL(STRING_AGG(CONCAT('[Source ID: ', ticket_id, '] ', answer), '' ORDER BY distance ASC), 'No relevant context found.'),
                                '---',
                                'QUESTION: ',
                                @new_question
                              ) AS prompt
                            FROM
                              retrieved_matches
                          )
                        
                        SELECT
                          p.ml_generate_text_result.candidates[0].content.parts[0].text AS generated_answer,
                          p.ml_generate_text_result AS full_model_response,
                          (SELECT ARRAY_AGG(STRUCT(ticket_id, question, answer) ORDER BY distance ASC) FROM retrieved_matches) AS top_matches
                        FROM
                          ML.GENERATE_TEXT(
                            MODEL `master-booster-469602-q2.kaggle.gemini`,
                            TABLE prompt_generation,
                            STRUCT(
                              8192 AS max_output_tokens,
                              0.5 AS temperature,
                              0.95 AS top_p
                            )
                          ) AS p;
        """

        # Execute the query
        query_job = client.query(sql_query, job_config=job_config)

        # Wait for the job to complete and get the results
        results = query_job.result()

        # Extract the first row's data
        for row in results:
            return {
                "generated_answer": row["generated_answer"],
                "top_matches": row["top_matches"],
                "full_model_response": row["full_model_response"]  # Optional, for debugging
            }
        
        # If no rows are returned
        return {
            "generated_answer": "Sorry, I could not generate an answer.",
            "top_matches": []
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            "generated_answer": f"An error occurred while querying BigQuery: {e}",
            "top_matches": []
        }


# --- Streamlit User Interface ---

st.set_page_config(layout="wide")
st.title("Support Sentinel 🛡️ - A Stack Whisper")
st.write("Ask a question about programming, and I'll search for solutions in a Stack Overflow dataset stored in BigQuery.")

# Create a text input box for the user's question
user_question = st.text_input("What is your question?", "")

# Create a button to submit the question
if st.button("Get Answer"):
    if user_question:
        # Show a spinner while the query is running
        with st.spinner("Searching for answers and generating a response..."):
            # Call the function to get the response from BigQuery
            response = get_rag_response_from_bigquery(user_question)
            # Display the answer
            st.markdown("### Answer:")
            st.markdown(response["generated_answer"])
            
            # Display top matching records
            if response["top_matches"]:
                st.markdown("### Top 3 Matching Records:")
                # Convert to DataFrame for easy display
                df_matches = pd.DataFrame(response["top_matches"])
                st.dataframe(df_matches)
            else:
                st.info("No matching records found.")
    else:
        st.warning("Please enter a question.")
