# Support Sentinel 🛡️ - A BigQuery Python RAG Assistant

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://stake-sage.streamlit.app/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?logo=googlecloud)](https://cloud.google.com/bigquery)

**Submission for the Google Cloud & Kaggle BigQuery AI Hackathon**

This project demonstrates a sophisticated, end-to-end Retrieval-Augmented Generation (RAG) application built entirely on Google Cloud's BigQuery. It acts as an intelligent assistant for Python developers, providing high-quality, context-aware answers to technical questions by leveraging a curated dataset from Stack Overflow.

---

## 🚀 Live Demo

The application is deployed and publicly accessible using Streamlit Community Cloud.

### **[➡️ Click here to run the live app: https://stake-sage.streamlit.app/](https://stake-sage.streamlit.app/)**

<img width="1600" height="879" alt="image" src="https://github.com/user-attachments/assets/2229ac30-834e-413b-a53f-2b05167bdbf2" />
<img width="1592" height="239" alt="image" src="https://github.com/user-attachments/assets/d031e15b-311a-4f2f-b720-c967e47dd6e1" />


---

## ✨ Features

* **Semantic Search:** Utilizes BigQuery's native `VECTOR_SEARCH` to find the most relevant solutions based on meaning, not just keywords.
* **Retrieval-Augmented Generation (RAG):** Dynamically retrieves relevant context from a knowledge base to provide grounded, factual answers.
* **Structured & Cited Responses:** The AI is prompted to deliver answers in a clean, readable Markdown format, including summaries, code examples, and citations pointing back to the original source data.
* **Serverless AI Infrastructure:** The entire AI pipeline—from embedding generation to the final LLM call—is executed through serverless BigQuery ML models, showcasing a scalable and manageable architecture.
* **Interactive UI:** A user-friendly interface built with Streamlit allows for easy interaction and demonstration.

---

## 🏛️ Architecture

The application follows a classic RAG pattern, orchestrated entirely within Google Cloud and served via Streamlit.

```mermaid
graph TD
    A[User via Streamlit App] --> B{BigQuery};
    B --> C["1. Embed Question<br>(BQML Embedding Model)"];
    C --> D["2. Find Similar Docs<br>(VECTOR_SEARCH)"];
    D --> E["3. Build Prompt<br>(With Retrieved Context)"];
    E --> F["4. Generate Answer<br>(BQML Gemini Model)"];
    F --> B;
    B --> A;

    style B fill:#E8F0FE,stroke:#4285F4,stroke-width:2px
    style A fill:#E6F4EA,stroke:#34A853,stroke-width:2px
```


---

## 🛠️ Implementation Details

This project was built in a series of steps, all centered around BigQuery's cutting-edge AI capabilities.

### 1. Data Preparation

The knowledge base was created from the public `stackoverflow` dataset available in BigQuery. We curated a high-quality subset of Python-related questions and answers with the following query:

```sql
CREATE OR REPLACE TABLE `kaggle.stackoverflow_python_qa` AS
WITH questions AS (
  SELECT id, title, body AS question_body, accepted_answer_id
  FROM `bigquery-public-data.stackoverflow.posts_questions`
  WHERE tags LIKE '%|python|%'
    AND accepted_answer_id IS NOT NULL
    AND score > 5
),
answers AS (
  SELECT id, body AS answer_body
  FROM `bigquery-public-data.stackoverflow.posts_answers`
)
SELECT
  q.id AS ticket_id,
  CONCAT(q.title, '\n\n', REGEXP_REPLACE(q.question_body, r'<[^>]*>', '')) AS problem_description,
  REGEXP_REPLACE(a.answer_body, r'<[^>]*>', '') AS resolution_text
FROM questions q
JOIN answers a ON q.accepted_answer_id = a.id
LIMIT 50000;
```

This gave us a clean table with `ticket_id`, `problem_description`, and `resolution_text`.

### 2. Model Creation in BigQuery ML

Two core models were registered within our BigQuery dataset, allowing all AI operations to be called with simple SQL.

**A. The Embedding Model**
We registered a model that points to the Universal Sentence Encoder, which is excellent for semantic search tasks. This model is used to convert text questions into vector embeddings.

```sql
CREATE OR REPLACE MODEL `kaggle.text_embedding_model`
OPTIONS (
  MODEL_TYPE = 'TENSORFLOW',
  MODEL_PATH = 'gs://tfhub-modules/google/universal-sentence-encoder-multilingual/3'
);
```

**B. The Generation Model (Gemini)**
We registered another model that points to Google's powerful Gemini Pro foundation model. This allows us to call Gemini directly from BigQuery without needing a separate API call.

```sql
CREATE OR REPLACE MODEL `kaggle.gemini`
REMOTE WITH CONNECTION `us.vertexai` -- Assumes a connection named 'vertexai' in the 'us' region
OPTIONS (endpoint = 'gemini-1.0-pro');
```
We then generated embeddings for our entire dataset using this model and stored them in the `stackoverflow_with_embeddings` table.

### 3. The Final RAG Query

The core logic is encapsulated in a single, powerful SQL query. This query performs the entire RAG pipeline in a series of steps using Common Table Expressions (CTEs):
1.  **`question_embedding`**: Takes the user's question and uses our registered `text_embedding_model` to generate a vector.
2.  **`retrieved_matches`**: Uses `VECTOR_SEARCH` to compare the question vector against the pre-calculated embeddings in our knowledge base, returning the `top_k=3` most similar documents.
3.  **`prompt_generation`**: Dynamically constructs a detailed prompt. It commands the Gemini model to act as an expert, answer *only* based on the retrieved context, structure its output in Markdown, and cite its sources.
4.  **Final `SELECT`**: Calls our registered `gemini` model with the generated prompt and returns both the final answer and the source documents that were used as context.

---

## 💻 How to Run Locally

To run this application on your own machine, follow these steps:

### Prerequisites
* Python 3.9+
* A Google Cloud Platform (GCP) project with the BigQuery API enabled.
* The `gcloud` CLI installed and authenticated (`gcloud auth application-default login`).
* You have already run the SQL queries above to create the datasets and models in your own BigQuery project.

### Setup Instructions
1.  **Clone the Repository:**
    ```bash
    git clone [URL_OF_YOUR_GITHUB_REPO]
    cd [REPO_NAME]
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Authentication:**
    * Create a Service Account in your GCP project with **BigQuery User** and **Vertex AI User** roles.
    * Create a JSON key for this service account and download it.
    * Create a folder named `.streamlit` in your project's root directory.
    * Inside that folder, create a file named `secrets.toml`.
    * Paste the entire content of your downloaded JSON key into `secrets.toml` like this:

    ```toml
    # .streamlit/secrets.toml

    [gcp_service_account]
    type = "service_account"
    project_id = "your-gcp-project-id"
    private_key_id = "your-private-key-id"
    private_key = "-----BEGIN PRIVATE KEY-----\n...your-private-key...\n-----END PRIVATE KEY-----\n"
    client_email = "your-service-account-email"
    client_id = "your-client-id"
    auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
    token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
    auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
    client_x509_cert_url = "your-client-cert-url"
    ```
    *Make sure to properly format the `private_key` with `\n` for newlines if copying directly.*

5.  **Run the App:**
    ```bash
    streamlit run app.py
    ```
