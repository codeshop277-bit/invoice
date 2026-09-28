# Vector Database Retrieval — ANN, HNSW & Cosine Similarity

## 1. Overview

A vector database stores numerical representations of data called **embeddings**.

In a RAG system:

```text
Document
   ↓
Chunking
   ↓
Embedding Model
   ↓
Vector
   ↓
Vector Database
   ↓
ANN Index (e.g. HNSW)
```

When a user sends a query:

```text
User Query
   ↓
Query Embedding
   ↓
Vector Database
   ↓
ANN / HNSW Search
   ↓
Top-K Similar Vectors
   ↓
Original Chunks
   ↓
LLM
   ↓
Answer
```

---

# 2. How Text Becomes a Vector

Suppose a document contains:

```text
AWS Bedrock provides foundation models for building
generative AI applications.
```

The document is first split into chunks.

An embedding model converts each chunk into a numerical vector.

For example, a simplified 5-dimensional embedding could be:

```text
[
    0.21,
    0.87,
    0.12,
    0.44,
    0.65
]
```

Real embedding models usually have hundreds or thousands of dimensions.

Examples:

```text
MiniLM       → 384 dimensions
Other models → 768 / 1024 / 1536 / etc.
```

The important point is:

> The vector is a numerical representation of the semantic meaning of the text.

---

# 3. What Is Stored in a Vector Database?

A vector database can conceptually store:

```json
{
    "id": "chunk_12345",

    "vector": [
        0.21,
        0.87,
        0.12,
        0.44,
        0.65
    ],

    "metadata": {
        "document_id": "aws-guide.pdf",
        "page": 10,
        "section": "Bedrock"
    }
}
```

The database therefore contains:

```text
Vector
   +
Vector ID
   +
Metadata / Payload
```

The metadata may contain:

```text
document_id
page_number
section
chunk_id
source
user_id
created_at
text
```

The original text may be stored directly in the vector database or in another storage system.

---

# 4. Example: 1 Million Vectors

Suppose:

```text
Number of vectors = 1,000,000
Dimension         = 384
```

Conceptually:

```text
Vector ID       Vector
--------------------------------------
chunk_001       [0.12, 0.34, ..., 0.55]
chunk_002       [0.82, 0.11, ..., 0.31]
chunk_003       [0.21, 0.44, ..., 0.92]
...
chunk_999999    [0.31, 0.77, ..., 0.12]
chunk_1000000   [0.44, 0.22, ..., 0.71]
```

The vector database also maintains an index to efficiently search these vectors.

---

# 5. What Happens When a Query Arrives?

Suppose the user asks:

```text
What is AWS Bedrock?
```

The query is converted into an embedding:

```text
"What is AWS Bedrock?"
          ↓
    Embedding Model
          ↓
[0.19, 0.83, 0.15, 0.47, ...]
```

This is called the **query vector**.

The vector database now needs to find vectors that are closest to this query vector.

---

# 6. Brute-Force Search

The simplest approach is to compare the query against every stored vector.

```text
Query
  │
  ├── Vector 1
  ├── Vector 2
  ├── Vector 3
  ├── Vector 4
  ├── ...
  └── Vector 1,000,000
```

For every vector:

```text
similarity(Query, Vector)
```

Example:

```text
Vector 1 → 0.21
Vector 2 → 0.87
Vector 3 → 0.32
Vector 4 → 0.91
...
```

Then sort the results:

```text
Vector 4 → 0.91
Vector 2 → 0.87
Vector 7 → 0.83
Vector 91 → 0.81
```

If:

```text
top_k = 3
```

return:

```text
Vector 4
Vector 2
Vector 7
```

### Problem

With 1 million vectors, a query potentially requires:

```text
1,000,000 similarity calculations
```

This becomes expensive at large scale.

---

# 7. ANN — Approximate Nearest Neighbor

ANN stands for:

> Approximate Nearest Neighbor

Instead of checking every vector, ANN algorithms try to quickly find vectors that are **very likely to be the nearest neighbors**.

Conceptually:

```text
1,000,000 vectors
       ↓
    ANN Index
       ↓
Search relevant region
       ↓
Candidate vectors
       ↓
Similarity calculation
       ↓
Top-K
```

ANN trades a small amount of exactness for significantly better search performance.

For example, the exact nearest neighbors might be:

```text
A
B
C
D
E
```

An ANN search might return:

```text
A
B
C
D
F
```

The result may not always be mathematically exact, but the search is much faster.

---

# 8. ANN Is a Category

ANN is not one specific algorithm.

There are multiple ANN approaches:

```text
ANN
├── HNSW
├── IVF
├── IVF-PQ
├── Annoy
└── Other algorithms
```

One of the most commonly used approaches is:

```text
HNSW
```

---

# 9. HNSW

HNSW stands for:

> Hierarchical Navigable Small World

HNSW creates a graph over the vectors.

Each vector becomes a node.

For example:

```text
V1 ───── V2 ───── V3
│        │         │
│        │         │
V4 ───── V5 ───── V6
          │
          │
         V7
```

Connections represent vectors that are relatively close to each other.

Instead of comparing the query against every vector, HNSW navigates this graph toward the region containing the nearest vectors.

---

# 10. Why HNSW Is Hierarchical

HNSW contains multiple layers.

### Higher layer

Contains fewer nodes:

```text
A ───────── D ───────── H
```

This allows large jumps across the vector space.

### Lower layer

Contains more nodes:

```text
A ─ B ─ C ─ D ─ E ─ F ─ G ─ H ─ I ─ J
```

This allows fine-grained searching.

You can think of it like a road network:

```text
Highway
   ↓
Major Roads
   ↓
Local Roads
```

The upper HNSW layers allow fast navigation, while lower layers allow precise navigation.

---

# 11. HNSW Query Process

Suppose the query vector is:

```text
Q
```

The search starts from an entry point.

Conceptually:

```text
Query Q
   ↓
Entry Point A
   ↓
Check neighbors
   ↓
Move to closer node
   ↓
Check its neighbors
   ↓
Move closer
   ↓
Candidate neighborhood
   ↓
Top-K
```

For example:

```text
Q
│
▼
A
│
▼
D
│
▼
F
│
├── G
└── H
```

The algorithm doesn't need to inspect all 1 million vectors.

It navigates toward the region where the closest vectors are located.

---

# 12. Cosine Similarity

Cosine similarity measures how similar two vectors are based on their direction.

The formula is:

```text
              A · B
cosine = --------------
          |A| × |B|
```

Conceptually:

```text
Similarity
    ↑
  1.0  → very similar direction
    │
  0.8  → highly similar
    │
  0.5  → moderately similar
    │
  0.0  → unrelated direction
    │
 -1.0  → opposite direction
```

The exact interpretation depends on the embedding model.

---

# 13. When Is Cosine Similarity Applied?

This is an important concept.

It is incorrect to think:

```text
HNSW
  ↓
Find vectors
  ↓
Cosine similarity
```

Instead:

```text
                 HNSW
                  │
                  │ uses configured
                  │ distance metric
                  ▼
          Cosine / Euclidean / etc.
                  │
                  ▼
           Graph traversal
                  │
                  ▼
         Candidate vectors
                  │
                  ▼
          Rank candidates
                  │
                  ▼
                Top-K
```

### During HNSW traversal

Suppose HNSW is currently at vector `A`.

It examines neighboring vectors:

```text
A
├── B
├── C
└── D
```

It calculates the configured distance/similarity between the query and those candidates.

For example:

```text
Query → B = 0.71
Query → C = 0.84
Query → D = 0.62
```

It will prefer the more promising neighbor:

```text
C → 0.84
```

and continue navigating from there.

Therefore:

> **Cosine similarity is part of the search process when cosine is the configured metric.**

---

# 14. Final Candidate Ranking

After HNSW explores enough of the graph, it has a candidate set.

For example:

```text
Candidate 1 → 0.91
Candidate 2 → 0.87
Candidate 3 → 0.94
Candidate 4 → 0.82
Candidate 5 → 0.89
```

The candidates are ranked:

```text
Candidate 3 → 0.94
Candidate 1 → 0.91
Candidate 5 → 0.89
Candidate 2 → 0.87
Candidate 4 → 0.82
```

For:

```text
top_k = 3
```

the result is:

```text
Candidate 3
Candidate 1
Candidate 5
```

The vector database then returns the corresponding IDs and metadata.

---

# 15. HNSW Does Not Replace Similarity Calculation

A common misconception is:

> "HNSW finds the vectors, and then cosine similarity is calculated."

More accurately:

> **HNSW is the search/indexing strategy, while cosine similarity is the distance metric used to navigate and rank vectors.**

HNSW reduces the number of vectors that need to be considered.

It does not eliminate distance calculations.

---

# 16. HNSW Parameters

Three important HNSW parameters are:

## M

Controls the approximate number of graph connections per node.

Higher `M`:

```text
M ↑
 ↓
More graph connections
 ↓
Potentially better recall
 ↓
More memory
 ↓
Higher index construction cost
```

---

## efConstruction

Controls how much effort is used when constructing the HNSW graph.

Higher `efConstruction`:

```text
efConstruction ↑
       ↓
More effort building graph
       ↓
Potentially better graph quality
       ↓
Better search quality
       ↓
Longer indexing time
```

---

## efSearch

Controls the amount of search effort during a query.

Higher `efSearch`:

```text
efSearch ↑
    ↓
Explore more candidates
    ↓
Potentially better recall
    ↓
Higher query latency
```

So:

```text
efSearch ↑
    ├── Recall ↑
    └── Latency ↑
```

---

# 17. HNSW vs Brute Force

| Feature        | Brute Force                  | HNSW           |
| -------------- | ---------------------------- | -------------- |
| Search method  | Compare against every vector | Navigate graph |
| Exactness      | Exact                        | Approximate    |
| Search speed   | Slower at scale              | Much faster    |
| Index required | No                           | Yes            |
| Memory         | Lower index overhead         | Higher         |
| Scalability    | Poorer for huge datasets     | Good           |
| Search quality | Exact                        | Tunable        |

---

# 18. HNSW vs IVF

Another ANN approach is IVF:

> Inverted File Index

IVF groups vectors into clusters.

```text
1 Million Vectors
       │
       ▼
   Clustering
       │
 ┌─────┼─────┐
 ▼     ▼     ▼
C1     C2    C3
│      │     │
...    ...   ...
```

When a query arrives:

```text
Query
  ↓
Find closest clusters
  ↓
Search those clusters
  ↓
Top-K
```

### HNSW

```text
Graph navigation
```

### IVF

```text
Cluster selection
+
Search selected clusters
```

Both are approaches to ANN search.

---

# 19. Complete RAG Retrieval Flow

A production RAG system can look like this:

```text
                    DOCUMENT
                       │
                       ▼
                    CHUNKING
                       │
                       ▼
                 EMBEDDING MODEL
                       │
                       ▼
                 VECTOR [384/768/...]
                       │
                       ▼
                VECTOR DATABASE
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
        HNSW Index            Metadata
             │
             ▼
         Vector Graph


                  USER QUERY
                       │
                       ▼
                QUERY EMBEDDING
                       │
                       ▼
                 QUERY VECTOR
                       │
                       ▼
                 HNSW SEARCH
                       │
                       │
              Cosine similarity
              during traversal
                       │
                       ▼
               Candidate vectors
                       │
                       ▼
              Candidate ranking
                       │
                       ▼
                    Top-K
                       │
                       ▼
               Original chunks
                       │
                       ▼
                      LLM
                       │
                       ▼
                    Answer
```

---

# 20. Example End-to-End

Suppose we have:

```text
1,000,000 document chunks
384-dimensional embeddings
HNSW index
Cosine similarity
```

User asks:

```text
How does AWS Bedrock support RAG?
```

### Step 1 — Embed query

```text
Query
  ↓
Embedding model
  ↓
Q = [0.19, 0.83, 0.15, ...]
```

### Step 2 — Start HNSW search

```text
Q
 ↓
Entry point
```

### Step 3 — Compare neighboring vectors

```text
Neighbor A → cosine 0.62
Neighbor B → cosine 0.78
Neighbor C → cosine 0.71
```

Move toward B.

### Step 4 — Continue graph traversal

```text
B
├── D → 0.81
├── E → 0.76
└── F → 0.84
```

Move toward F.

### Step 5 — Build candidate set

Eventually HNSW identifies promising candidates:

```text
Chunk A → 0.94
Chunk B → 0.91
Chunk C → 0.89
Chunk D → 0.87
Chunk E → 0.85
```

### Step 6 — Return Top-K

If:

```text
top_k = 3
```

return:

```text
Chunk A
Chunk B
Chunk C
```

### Step 7 — Retrieve original content

The IDs map back to:

```text
aws-bedrock.pdf
page 12
chunk 45

aws-rag.pdf
page 8
chunk 21

bedrock-guide.pdf
page 15
chunk 62
```

### Step 8 — Send context to LLM

```text
Query
+
Retrieved chunks
+
System prompt
       ↓
      LLM
       ↓
    Answer
```

---

# 21. Key Interview Points

Remember these distinctions:

### Embedding

Converts semantic content into a numerical vector.

```text
Text → Vector
```

### Vector Database

Stores vectors and associated metadata.

```text
Vector + Metadata
```

### ANN

A family of techniques for efficiently finding approximate nearest neighbors.

```text
ANN = category
```

### HNSW

One ANN indexing/search algorithm.

```text
HNSW = graph-based ANN
```

### Cosine Similarity

A metric used to measure similarity between vectors.

```text
Cosine = similarity metric
```

### HNSW + Cosine

If cosine is configured:

```text
HNSW
  +
Cosine similarity
```

HNSW uses cosine-based distance/similarity while navigating the graph and ranking candidates.

---

# 22. One-Sentence Interview Answer

> **When a query arrives, we convert it into an embedding vector and search the ANN index. If the index is HNSW with cosine distance, HNSW navigates its graph using cosine-based distance calculations, explores a limited candidate set rather than all 1 million vectors, ranks the candidates, and returns the Top-K nearest chunks along with their metadata.**

---

# 23. Mental Model

The easiest way to remember everything:

```text
Embedding
    ↓
"What does this text mean?"
    ↓
Vector
    ↓
"Where is this meaning located?"
    ↓
HNSW / ANN
    ↓
"Which nearby vectors should I explore?"
    ↓
Cosine Similarity
    ↓
"How similar is this candidate to my query?"
    ↓
Top-K
    ↓
Retrieved Context
    ↓
LLM
    ↓
Answer
```

The most important distinction is:

```text
ANN  → Search strategy/category
HNSW → Graph-based ANN algorithm
Cosine → Similarity/distance metric
Vector → Numerical semantic representation
Top-K → Number of results returned
```

# Embedding Dimension
The purpose of the dimensions is to provide enough numerical space for the embedding model to represent semantic relationships.
A 384-dimensional embedding:
[0.21, -0.45, 0.72, 0.13, ... 380 more values]
Text
 │
 ▼
Embedding Model
 │
 ▼
384-dimensional representation
 │
 ├── semantic information
 ├── contextual relationships
 ├── linguistic relationships
 └── other learned features

 1,000,000 × 384 × 4 bytes
≈ 1.536 GB  
The dimensions represent the learned numerical embedding space in which the model encodes semantic relationships. A higher-dimensional embedding can provide greater representational capacity, but it also increases storage, memory, bandwidth, and computation costs. Higher dimension doesn't automatically mean better retrieval because embedding quality depends on the model and its training. For a vector database, the query and document embeddings must have the same dimension and belong to the same embedding space. In large-scale retrieval, dimensionality also affects ANN index size and search performance, so we balance retrieval quality against infrastructure cost and latency."

# Metrics
RRF
→ "How do I COMBINE retrieval systems?"

Recall
→ "Did I FIND the relevant chunk?"

Precision
→ "How much of what I found is RELEVANT?"

MRR
→ "How EARLY did I find the first relevant chunk?"

NDCG
→ "Did I RANK the most relevant chunks HIGH?"