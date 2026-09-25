Amazon Bedrock Knowledge Bases, the important distinction is that you generally do not write the chunking, embedding, and vector-DB code yourself. Bedrock handles those stages after you connect a data source and start ingestion. AWS describes the ingestion flow as parsing → chunking → embedding → writing vectors to the configured vector store.

For a typical PDF RAG application:

PDF
 │
 ↓
Amazon S3
 │
 ↓
Bedrock Knowledge Base
 │
 ├── Parse
 ├── Chunk
 ├── Embed
 └── Store vectors
       │
       ↓
   Vector Store
       │
       ↓
Retrieve(query)
       │
       ↓
Relevant chunks
       │
       ↓
Bedrock LLM
       │
       ↓
Answer
1. Prerequisites

Assume you have:

S3 bucket:
s3://my-company-documents/

PDF:
s3://my-company-documents/policies/leave-policy.pdf

Knowledge Base ID:
YOUR_KB_ID

Data Source ID:
YOUR_DATA_SOURCE_ID

S3 is a common Knowledge Base data source, and supported document formats include PDF, DOC/DOCX, TXT, Markdown, HTML, CSV and Excel, subject to AWS's current quotas.

Install:

pip install boto3
2. Upload the document to S3

You can upload a document using Boto3:

import boto3

s3 = boto3.client("s3")

bucket = "my-company-documents"
file_path = "./leave-policy.pdf"
s3_key = "policies/leave-policy.pdf"

s3.upload_file(
    file_path,
    bucket,
    s3_key
)

print("Document uploaded")

Now:

Local PDF
   ↓
S3
   ↓
s3://my-company-documents/policies/leave-policy.pdf
3. Configure the Bedrock Knowledge Base

This part is normally done once through the AWS console or APIs.

Conceptually:

Knowledge Base
      │
      ├── Embedding Model
      │
      ├── Vector Store
      │
      └── Data Source
             │
             └── S3 Bucket

For example:

Knowledge Base ID:
KB12345678

Data Source ID:
DS12345678

S3:
s3://my-company-documents/

The Knowledge Base configuration determines the embedding model and vector storage configuration.

4. Ingestion Pipeline

Once the document is in S3, start an ingestion job.

Use the Bedrock Agent client in Boto3:

import boto3

bedrock_agent = boto3.client(
    "bedrock-agent",
    region_name="us-east-1"
)

KNOWLEDGE_BASE_ID = "YOUR_KB_ID"
DATA_SOURCE_ID = "YOUR_DATA_SOURCE_ID"

response = bedrock_agent.start_ingestion_job(
    knowledgeBaseId=KNOWLEDGE_BASE_ID,
    dataSourceId=DATA_SOURCE_ID,
    description="Ingest company documents"
)

print(response)

AWS exposes StartIngestionJob specifically for ingesting a data source into a Knowledge Base.

5. What Happens After start_ingestion_job()?

This is the important part for an AI Engineer interview.

Suppose:

leave-policy.pdf

contains:

Employees are entitled to 20 days of annual leave...

Leave requests must be submitted through the HR portal...

Bedrock handles approximately:

             PDF
              │
              ↓
           Parsing
              │
              ↓
       Extract document text
              │
              ↓
          Chunking
              │
       ┌──────┼──────┐
       ↓      ↓      ↓
    Chunk1  Chunk2  Chunk3
       │      │      │
       └──────┼──────┘
              ↓
        Embedding Model
              │
              ↓
       Vector Embeddings
              │
              ↓
        Vector Database

AWS documents this ingestion sequence as parsing, chunking, embedding, and storing embeddings in the configured vector store.

So you don't normally write this yourself:

pdf_to_text()
chunk_document()
embedding_model()
vector_db.insert()

Bedrock Knowledge Bases manages those stages.

6. Check Ingestion Status

After starting the job, you can monitor it.

import boto3

bedrock_agent = boto3.client(
    "bedrock-agent",
    region_name="us-east-1"
)

response = bedrock_agent.start_ingestion_job(
    knowledgeBaseId=KNOWLEDGE_BASE_ID,
    dataSourceId=DATA_SOURCE_ID
)

job_id = response["ingestionJob"]["ingestionJobId"]

print("Job ID:", job_id)

Then:

status_response = bedrock_agent.get_ingestion_job(
    knowledgeBaseId=KNOWLEDGE_BASE_ID,
    dataSourceId=DATA_SOURCE_ID,
    ingestionJobId=job_id
)

status = status_response["ingestionJob"]["status"]

print("Status:", status)

Typical statuses include:

STARTING
IN_PROGRESS
COMPLETE
FAILED
STOPPING
STOPPED

AWS provides GetIngestionJob for checking the ingestion job status.

7. Complete Ingestion Script

You can combine the above into one script:

import boto3
import time


REGION = "us-east-1"

KNOWLEDGE_BASE_ID = "YOUR_KB_ID"
DATA_SOURCE_ID = "YOUR_DATA_SOURCE_ID"


bedrock_agent = boto3.client(
    "bedrock-agent",
    region_name=REGION
)


def start_ingestion():

    response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        dataSourceId=DATA_SOURCE_ID,
        description="Ingest company documents"
    )

    job_id = response["ingestionJob"]["ingestionJobId"]

    print("Ingestion started")
    print("Job ID:", job_id)

    return job_id


def wait_for_ingestion(job_id):

    while True:

        response = bedrock_agent.get_ingestion_job(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            dataSourceId=DATA_SOURCE_ID,
            ingestionJobId=job_id
        )

        status = response["ingestionJob"]["status"]

        print("Status:", status)

        if status == "COMPLETE":
            print("Ingestion completed successfully")
            break

        if status in ["FAILED", "STOPPED", "STOPPING"]:
            print("Ingestion failed/stopped")
            print(response)
            break

        time.sleep(5)


if __name__ == "__main__":

    job_id = start_ingestion()

    wait_for_ingestion(job_id)
8. Retrieval Code

Now comes the interesting part.

Once ingestion is complete, you can query the Knowledge Base using:

Retrieve

AWS provides two major retrieval patterns:

Retrieve

and

RetrieveAndGenerate

Retrieve returns relevant source chunks, while RetrieveAndGenerate performs retrieval and then generates a natural-language answer using a model.

For an AI Engineer, I recommend understanding Retrieve first because it gives you explicit control over the RAG pipeline.

9. Basic Retrieve Example
import boto3


REGION = "us-east-1"

KNOWLEDGE_BASE_ID = "YOUR_KB_ID"


bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=REGION
)


query = "How many annual leave days are employees entitled to?"


response = bedrock_agent_runtime.retrieve(
    knowledgeBaseId=KNOWLEDGE_BASE_ID,

    retrievalQuery={
        "text": query
    }
)


for result in response["retrievalResults"]:

    print("Score:", result.get("score"))

    print(
        "Text:",
        result["content"].get("text")
    )

    print(
        "Location:",
        result.get("location")
    )

    print("-" * 50)

The important object is:

response["retrievalResults"]

Each result represents a relevant piece of source data retrieved from the Knowledge Base.

10. What Retrieval Does

Suppose the user asks:

How many annual leave days do employees get?

The Knowledge Base performs semantic retrieval:

User Query
    │
    ↓
Embedding / Retrieval
    │
    ↓
Vector Search
    │
    ├── Chunk 1 → Score 0.91
    ├── Chunk 2 → Score 0.84
    ├── Chunk 3 → Score 0.77
    └── Chunk 4 → Score 0.52

The returned chunks might be:

Chunk 1:

Employees are entitled to 20 days
of annual leave every calendar year.
Chunk 2:

Annual leave requests should be
submitted through the HR portal.

Your application can then pass those chunks to an LLM.

11. Limit the Number of Results

You can configure the number of retrieved results.

response = bedrock_agent_runtime.retrieve(
    knowledgeBaseId=KNOWLEDGE_BASE_ID,

    retrievalQuery={
        "text": query
    },

    retrievalConfiguration={
        "vectorSearchConfiguration": {
            "numberOfResults": 5
        }
    }
)

Now you request:

Top 5 relevant chunks

instead of relying on the default.

12. Add Metadata Filtering

This is very useful in enterprise RAG.

Suppose your documents have metadata:

department = HR
country = India
document_type = policy

You can filter retrieval.

Conceptually:

User Query
    │
    ↓
Metadata Filter
    │
    ├── department = HR
    └── country = India
    │
    ↓
Vector Search

Example:

response = bedrock_agent_runtime.retrieve(

    knowledgeBaseId=KNOWLEDGE_BASE_ID,

    retrievalQuery={
        "text": "What is the leave policy?"
    },

    retrievalConfiguration={
        "vectorSearchConfiguration": {

            "numberOfResults": 5,

            "filter": {
                "equals": {
                    "key": "department",
                    "value": "HR"
                }
            }
        }
    }
)

This is particularly useful when you have thousands of documents.

13. Retrieve + Bedrock LLM

This is where you build your own RAG pipeline.

User
 │
 ↓
Retrieve
 │
 ↓
Relevant chunks
 │
 ↓
Build prompt
 │
 ↓
Bedrock Converse
 │
 ↓
Answer

Example:

import boto3


REGION = "us-east-1"

KNOWLEDGE_BASE_ID = "YOUR_KB_ID"

MODEL_ID = "YOUR_MODEL_ID"


bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=REGION
)

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)


def retrieve_documents(query):

    response = bedrock_agent_runtime.retrieve(

        knowledgeBaseId=KNOWLEDGE_BASE_ID,

        retrievalQuery={
            "text": query
        },

        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": 5
            }
        }
    )

    return response["retrievalResults"]

Then create context:

def build_context(results):

    context = []

    for result in results:

        text = result["content"].get("text")

        if text:
            context.append(text)

    return "\n\n".join(context)
14. Send Retrieved Context to Bedrock
def generate_answer(query, context):

    prompt = f"""
You are an enterprise AI assistant.

Answer the question using ONLY the provided context.

If the answer is not available in the context,
say that you don't have enough information.

Context:
{context}

Question:
{query}
"""

    response = bedrock.converse(

        modelId=MODEL_ID,

        messages=[
            {
                "role": "user",

                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],

        inferenceConfig={
            "maxTokens": 500,
            "temperature": 0.1
        }
    )

    return response[
        "output"
    ][
        "message"
    ][
        "content"
    ][0]["text"]
15. Complete Custom RAG Code

Putting everything together:

import boto3


REGION = "us-east-1"

KNOWLEDGE_BASE_ID = "YOUR_KB_ID"

MODEL_ID = "YOUR_MODEL_ID"


bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=REGION
)

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)


def retrieve_documents(query):

    response = bedrock_agent_runtime.retrieve(

        knowledgeBaseId=KNOWLEDGE_BASE_ID,

        retrievalQuery={
            "text": query
        },

        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": 5
            }
        }
    )

    return response["retrievalResults"]


def build_context(results):

    chunks = []

    for result in results:

        text = result["content"].get("text")

        if text:
            chunks.append(text)

    return "\n\n".join(chunks)


def generate_answer(query, context):

    prompt = f"""
You are an enterprise AI assistant.

Use only the following context to answer.

If the answer cannot be found in the context,
say that you don't have enough information.

Context:
{context}

Question:
{query}
"""

    response = bedrock.converse(

        modelId=MODEL_ID,

        messages=[
            {
                "role": "user",

                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],

        inferenceConfig={
            "maxTokens": 500,
            "temperature": 0.1
        }
    )

    return response[
        "output"
    ][
        "message"
    ][
        "content"
    ][0]["text"]


def ask_question(query):

    # 1. Retrieve relevant chunks

    results = retrieve_documents(query)


    # 2. Build context

    context = build_context(results)


    # 3. Generate answer

    answer = generate_answer(
        query,
        context
    )


    return answer


if __name__ == "__main__":

    query = (
        "How many annual leave days "
        "are employees entitled to?"
    )

    answer = ask_question(query)

    print(answer)
16. Add Sources/Citations to the Answer

One major advantage of using Retrieve yourself is that you can preserve the source information.

For example:

def print_sources(results):

    for result in results:

        print(
            "Score:",
            result.get("score")
        )

        print(
            "Source:",
            result.get("location")
        )

        print(
            "Content:",
            result["content"].get("text")
        )

        print("-" * 60)

Then:

results = retrieve_documents(query)

print_sources(results)

You can build a response like:

Answer:
Employees receive 20 annual leave days.

Sources:
- leave-policy.pdf
- HR-policy.pdf

This is preferable to returning only the generated answer in an enterprise RAG application.

17. Easier Option: RetrieveAndGenerate

If you don't need to manually construct the prompt, Bedrock provides:

RetrieveAndGenerate

This combines retrieval and model generation. AWS describes it as combining Retrieve with model invocation to retrieve relevant source chunks and generate a natural-language response.

Example:

import boto3


client = boto3.client(
    "bedrock-agent-runtime",
    region_name="us-east-1"
)


response = client.retrieve_and_generate(

    input={
        "text": "How many annual leave days do employees get?"
    },

    retrieveAndGenerateConfiguration={

        "type": "KNOWLEDGE_BASE",

        "knowledgeBaseConfiguration": {

            "knowledgeBaseId": "YOUR_KB_ID",

            "modelArn": "YOUR_MODEL_ARN"
        }
    }
)


print(
    response["output"]["text"]
)

The architecture becomes:

User Query
    │
    ↓
RetrieveAndGenerate
    │
    ├── Retrieve chunks
    │
    ├── Build prompt
    │
    ├── Invoke model
    │
    └── Generate answer
            │
            ↓
          User
18. Retrieve vs RetrieveAndGenerate
Feature	Retrieve	RetrieveAndGenerate
Retrieves chunks	✅	✅
Generates answer	❌	✅
You control prompt	✅	Less control
You control LLM call	✅	Managed as part of operation
Easy to implement	Medium	Easy
Custom RAG logic	Excellent	More limited
Custom validation	Excellent	Less explicit
Debug retrieval	Excellent	Possible through response/source data
Good for learning RAG	Yes	Yes

For your AI Engineer interview preparation, understand this distinction clearly.

19. Where Bedrock Knowledge Bases Fit

You can think of the complete application as:

                 INGESTION
                     │
                     ↓
                 Documents
                     │
                     ↓
                    S3
                     │
                     ↓
          Bedrock Knowledge Base
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Parse      Chunk      Embed
          │          │          │
          └──────────┼──────────┘
                     ↓
                Vector Store
                     │
                     │
=====================│=====================
                     │
                  RETRIEVAL
                     │
                     ↓
                 User Query
                     │
                     ↓
                  Retrieve
                     │
                     ↓
               Top K Chunks
                     │
                     ↓
              Prompt + Context
                     │
                     ↓
                Bedrock LLM
                     │
                     ↓
                  Answer
20. The Important Interview Explanation

If an interviewer asks:

"How would you implement a document ingestion pipeline using Bedrock Knowledge Bases?"

A strong answer is:

"I would store the documents in an S3 data source connected to an Amazon Bedrock Knowledge Base. When documents are added or modified, I would start an ingestion job using the Bedrock Agent API. Bedrock handles parsing, chunking, embedding and indexing the chunks into the configured vector store. I would monitor the ingestion job until it completes and handle failures. At query time, I can use the Retrieve API to retrieve the top relevant chunks and pass them to a Bedrock model through the Converse API, giving me full control over the RAG pipeline. Alternatively, I can use RetrieveAndGenerate when I want Bedrock to combine retrieval and generation."

The key APIs to remember
S3
 │
 ↓
StartIngestionJob()
 │
 ↓
GetIngestionJob()
 │
 ↓
Knowledge Base
 │
 ↓
Retrieve()
 │
 ↓
Bedrock Converse()

And the simpler managed query:

User
 │
 ↓
RetrieveAndGenerate()
 │
 ↓
Answer + Sources

AWS currently recommends managed Knowledge Bases for an optimized retrieval/managed experience, while S3 data sources support incremental syncing of added, modified, and deleted content.