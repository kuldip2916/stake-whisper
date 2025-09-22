# Support Sentinel 🛡️ - A Stack Whisper

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://stake-whisper.streamlit.app/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?logo=googlecloud)](https://cloud.google.com/bigquery)

**Submission for the Google Cloud & Kaggle BigQuery AI Hackathon**

This project demonstrates a sophisticated, end-to-end Retrieval-Augmented Generation (RAG) application built entirely on Google Cloud's BigQuery. It acts as an intelligent assistant for developers and tech professionals, providing high-quality, context-aware answers to technical questions by leveraging the vast knowledge base of Stack Overflow.

---

## 🎯 The Problem

In fast-paced software development environments, developers frequently encounter technical roadblocks. Sifting through vast platforms like Stack Overflow for accurate solutions is time-consuming and inefficient. Support teams and individual developers need a tool that can quickly surface the most relevant, high-quality answers from a trusted knowledge base, reducing downtime and accelerating development cycles.

## 💡 The Solution

Support Sentinel is a Retrieval-Augmented Generation (RAG) agent that acts as an intelligent assistant for developers. Built entirely on Google Cloud BigQuery, it leverages a curated dataset of high-quality Stack Overflow questions and answers. When a developer asks a question, the application uses BigQuery's vector search to find the top 3 most semantically similar solutions from the past. It then uses a powerful language model (Gemini) to generate a concise, structured answer, complete with code examples and citations that link back to the original Stack Overflow posts. This provides developers with quick, reliable, and contextually-aware solutions.

---

## 🚀 Live Demo

The application is deployed and publicly accessible using Streamlit Community Cloud.

### **➡️ Click here to run the live app [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://stake-whisper.streamlit.app/)**

<img width="1683" height="919" alt="image" src="https://github.com/user-attachments/assets/33aa93fb-7a6d-4f98-8c48-6d17a6f76ab9" />
<img width="1683" height="522" alt="image" src="https://github.com/user-attachments/assets/4711dd09-9dc0-46b4-8f54-53a602fa20ac" />





---

## ✨ Features

* **Semantic Search:** Utilizes BigQuery's native `VECTOR_SEARCH` to find the most relevant solutions based on meaning, not just keywords.
* **Retrieval-Augmented Generation (RAG):** Dynamically retrieves relevant context from a knowledge base to provide grounded, factual answers.
* **Structured & Cited Responses:** The AI is prompted to deliver answers in a clean, readable Markdown format, including summaries, code examples, and citations pointing back to the original source data.
* **Serverless AI Infrastructure:** The entire AI pipeline—from embedding generation to the final LLM call—is executed through serverless BigQuery ML models, showcasing a scalable and manageable architecture.
* **Interactive UI:** A user-friendly interface built with Streamlit allows for easy interaction and demonstration.

---

## 🌐 Use Cases

While this demo focuses on Stack Overflow, the underlying RAG architecture can be adapted for various enterprise and commercial use cases:
*   **Internal Knowledge Base for Enterprises:** Employees could ask questions in natural language about company policies, technical documentation, or internal processes and get answers sourced directly from internal documents.
*   **Customer Support Automation:** Power a chatbot on a company's website to answer customer questions based on product manuals, FAQs, and historical support tickets.
*   **Healthcare Information Systems:** Assist doctors and nurses by quickly finding relevant information from medical journals, patient history (with privacy safeguards), and clinical guidelines.
*   **Financial Research:** Help financial analysts query large volumes of reports, market data, and news articles to get summarized insights.
*   **Legal Document Analysis:** Allow lawyers and paralegals to rapidly search through case law, contracts, and legal precedents.

---

## 🏛️ Architecture

The application follows a classic RAG pattern, orchestrated entirely within Google Cloud and served via Streamlit.

```mermaid
graph TD
    %% Style Definitions for nodes
    classDef ui fill:#e3f2fd,stroke:#64b5f6,stroke-width:2px,color:#333;
    classDef bqai fill:#ede7f6,stroke:#9575cd,stroke-width:2px,color:#333;
    classDef data fill:#e0f2f1,stroke:#4db6ac,stroke-width:2px,color:#333;
    classDef result fill:#e8f5e9,stroke:#81c784,stroke-width:2px,color:#333;

    subgraph "💡 **User Interface (Streamlit)**"
        A[User Enters Question]
    end

    subgraph "⚙️ **BigQuery - AI Platform**"
        B[1. Embed User Question]
        C[2. Vector Search]
        D[3. Prompt Engineering]
        E[4. Generate Answer]
    end

    subgraph "📚 **Data & Models in BigQuery**"
        F["Stack Overflow Knowledge Base<br>with Embeddings"]
        G["BQML Embedding Model<br>(text-embedding-004)"]
        H["BQML Generation Model<br>(gemini-2.0-flash-001)"]
    end

    I[✅ Answer Displayed to User]

    %% Connection definitions (order matters for styling below)
    A --> B;
    B -- "Uses" --> G;
    B -- "Generates Question Vector" --> C;
    C -- "Searches in" --> F;
    C -- "Finds Top 3 Matches" --> D;
    A -- "Original Question" --> D;
    D -- "Builds Context-Rich Prompt" --> E;
    E -- "Uses" --> H;
    E -- "Generates Final Answer & Citations" --> I;
    A --> I;

    %% Assigning styles to the nodes
    class A ui;
    class B,C,D,E bqai;
    class F,G,H data;
    class I result;

    %% Assigning styles to the connections (links are 0-indexed)
    %% UI related links (blue)
    linkStyle 0,5,9 stroke:#64b5f6,stroke-width:2px;
    %% BQ AI internal process links (purple)
    linkStyle 2,4,6 stroke:#9575cd,stroke-width:2px;
    %% Data & Model interaction links (teal)
    linkStyle 1,3,7 stroke:#4db6ac,stroke-width:2px;
    %% Final result link (green)
    linkStyle 8 stroke:#81c784,stroke-width:2px;

    

```

---

## 🛠️ Implementation Details

This project was built in a series of steps, all centered around BigQuery's cutting-edge AI capabilities.

### 1. Data Preparation

The knowledge base was created from the public `stackoverflow` dataset available in BigQuery. We curated a high-quality subset of questions and answers with the following query:

```sql
CREATE OR REPLACE TABLE `your-gcp-project-id.kaggle.stackoverflow_qa` AS
WITH questions AS (
  SELECT id, title, body AS question_body, accepted_answer_id
  FROM `bigquery-public-data.stackoverflow.posts_questions`
  WHERE accepted_answer_id IS NOT NULL
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
JOIN answers a ON q.accepted_answer_id = a.id;
```

This gave us a clean table with `ticket_id`, `problem_description`, and `resolution_text`.

### 2. Model Creation in BigQuery ML

Two core models were registered within our BigQuery dataset, allowing all AI operations to be called with simple SQL.

**A. The Embedding Model**
We registered a remote model pointing to the `text-embedding-004` model, which is one of Google's latest and most powerful embedding models.

```sql
CREATE OR REPLACE MODEL `your-gcp-project-id.kaggle.text_embedding_model`
REMOTE WITH CONNECTION `your-gcp-project-id.us.vertexai`
OPTIONS (ENDPOINT = 'text-embedding-004');
```

**B. The Generation Model (Gemini 2.0 Flash)**
We registered another model that points to Google's powerful and cost-effective Gemini 2.0 Flash foundation model. This allows us to call Gemini directly from BigQuery without needing a separate API call.

```sql
CREATE OR REPLACE MODEL `your-gcp-project-id.kaggle.gemini`
REMOTE WITH CONNECTION `your-gcp-project-id.us.vertexai`
OPTIONS (ENDPOINT = 'gemini-2.0-flash-001');
```

### 3. Generating Embeddings

We then generated embeddings for our entire dataset using our registered embedding model and stored them in a new table called `stackoverflow_with_embeddings`.

```sql
CREATE OR REPLACE TABLE `your-gcp-project-id.kaggle.stackoverflow_with_embeddings` AS
SELECT
  ticket_id,
  problem_description,
  resolution_text,
  ml_generate_embedding_result AS embedding
FROM
  ML.GENERATE_EMBEDDING(
    MODEL `your-gcp-project-id.kaggle.text_embedding_model`,
    (
      SELECT
        ticket_id,
        problem_description,
        resolution_text,
        problem_description AS content
      FROM `your-gcp-project-id.kaggle.stackoverflow_qa`
    )
  );
```

### 4. Creating a Vector Index

To dramatically speed up the vector search, we created a vector index on the `embedding` column. This is a crucial step for ensuring low-latency responses in a real-world application.

```sql
CREATE OR REPLACE VECTOR INDEX `stackoverflow_index`
ON `your-gcp-project-id.kaggle.stackoverflow_with_embeddings`(embedding)
OPTIONS(index_type='IVF', distance_type='COSINE', ivf_options='{"num_lists": 4000}');
```

### 5. The Final RAG Query

The core logic is encapsulated in a single, powerful SQL query. This query performs the entire RAG pipeline in a series of steps using Common Table Expressions (CTEs):
1.  **`question_embedding`**: Takes the user's question and uses our registered `text_embedding_model` to generate a vector.
2.  **`retrieved_matches`**: Uses `VECTOR_SEARCH` to compare the question vector against the pre-calculated embeddings in our knowledge base, returning the `top_k=3` most similar documents.
3.  **`prompt_generation`**: Dynamically constructs a detailed prompt. It commands the Gemini model to act as an expert, answer *only* based on the retrieved context, structure its output in Markdown, and cite its sources.
4.  **Final `SELECT`**: Calls our registered `gemini` model with the generated prompt and returns both the final answer and the source documents that were used as context.

Here is the complete query as implemented in the Streamlit application:
```sql
-- Note: In the app, @new_question is a parameter. Here, we DECLARE it for demonstration.
DECLARE new_question STRING DEFAULT "How can I optimize reading large CSV files in Python to avoid high RAM usage?";

WITH
  question_embedding AS (
    SELECT
      p.ml_generate_embedding_result AS embedding
    FROM
      ML.GENERATE_EMBEDDING(
        MODEL `your-gcp-project-id.kaggle.text_embedding_model`,
        (SELECT new_question AS content)
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
        TABLE `your-gcp-project-id.kaggle.stackoverflow_with_embeddings`,
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
        IFNULL(STRING_AGG(CONCAT('[Source ID: ', ticket_id, '] ', answer), '\n---\n' ORDER BY distance ASC), 'No relevant context found.'),
        '---',
        'QUESTION: ',
        new_question
      ) AS prompt
    FROM
      retrieved_matches
  )

SELECT
  p.ml_generate_text_result.candidates[0].content.parts[0].text AS generated_answer,
  (SELECT ARRAY_AGG(STRUCT(ticket_id, question, answer) ORDER BY distance ASC) FROM retrieved_matches) AS top_matches
FROM
  ML.GENERATE_TEXT(
    MODEL `your-gcp-project-id.kaggle.gemini`,
    TABLE prompt_generation,
    STRUCT(
      8192 AS max_output_tokens,
      0.5 AS temperature,
      0.95 AS top_p
    )
  ) AS p;
```

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
