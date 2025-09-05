import os
import streamlit as st
from google.cloud import bigquery

# --- Authentication Setup ---
# Set the environment variable for Google Cloud credentials
# This line points the BigQuery client to your service account key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "GOOGLE_CREDENTIALS.json"

# --- BigQuery Function ---
# Encapsulate all the BigQuery logic in a function for clarity and reusability
def get_rag_response_from_bigquery(question: str):
    """
    Sends a question to BigQuery, runs the RAG SQL query, and returns the answer.
    """
    try:
        # Initialize the BigQuery client
        client = bigquery.Client()

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
        WITH question_embedding AS (
          SELECT
            p.ml_generate_embedding_result AS embedding
          FROM
            ML.GENERATE_EMBEDDING(
              MODEL `master-booster-469602-q2.kaggle.text_embedding_model`,
              (SELECT @new_question AS content)
            ) AS p
        ),
        prompt_generation AS (
          SELECT
            CONCAT(
              'You are a helpful expert Python programmer. Answer the following question based ONLY on the context provided. Provide a clear, actionable solution with code examples. \\n\\n',
              'CONTEXT: \\n',
              IFNULL(STRING_AGG(retrieved_solutions.base.resolution_text, '\\n---\\n'), 'No relevant context found.'),
              '\\n\\nQUESTION: ',
              @new_question
            ) AS prompt
          FROM (
            SELECT base
            FROM VECTOR_SEARCH(
              TABLE `master-booster-469602-q2.kaggle.stackoverflow_with_embeddings`,
              'embedding',
              (SELECT embedding FROM question_embedding),
              top_k => 3
            )
          ) AS retrieved_solutions
        )
        SELECT
          ml_generate_text_result.candidates[0].content.parts[0].text AS generated_answer
        FROM
          ML.GENERATE_TEXT(
            MODEL `master-booster-469602-q2.kaggle.gemini`,
            TABLE prompt_generation,
            STRUCT(
              8192 AS max_output_tokens,
              0.5 AS temperature,
              0.95 AS top_p
            )
          );
        """

        # Execute the query
        query_job = client.query(sql_query, job_config=job_config)

        # Wait for the job to complete and get the results
        results = query_job.result()

        # Extract the first row and the 'generated_answer' column
        for row in results:
            return row["generated_answer"]
        
        # If no rows are returned
        return "Sorry, I could not generate an answer."

    except Exception as e:
        # Handle potential errors (e.g., API errors, no results)
        print(f"An error occurred: {e}")
        return f"An error occurred while querying BigQuery: {e}"


# --- Streamlit User Interface ---

st.set_page_config(layout="wide")
st.title("🐍 BigQuery Python RAG Assistant")
st.write("Ask a question about Python, and I'll search for solutions in a Stack Overflow dataset stored in BigQuery.")

# Create a text input box for the user's question
user_question = st.text_input("What is your Python question?", "")

# Create a button to submit the question
if st.button("Get Answer"):
    if user_question:
        # Show a spinner while the query is running
        with st.spinner("Searching for answers and generating a response..."):
            # Call the function to get the answer from BigQuery
            answer = get_rag_response_from_bigquery(user_question)
            # Display the answer
            st.markdown("### Answer:")
            st.markdown(answer)
    else:
        st.warning("Please enter a question.")

