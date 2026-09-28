# RAG Retrieval Evaluation — Recall, Precision, MRR & NDCG

## 1. Purpose

After hybrid retrieval and reranking:

```text
User Query
    │
    ├── BM25
    │     └── Top-K
    │
    └── Vector Search
          └── Top-K
                │
                ▼
              RRF
                │
                ▼
          Candidate Chunks
                │
                ▼
            Reranker
                │
                ▼
        reranked_results
                │
                ▼
       Retrieval Evaluation
                │
       ┌────────┼─────────┬─────────┐
       ▼        ▼         ▼         ▼
    Recall   Precision   MRR      NDCG
```

The four metrics answer different questions:

| Metric          | Question                                           |
| --------------- | -------------------------------------------------- |
| **Recall@K**    | Did we retrieve the relevant chunks?               |
| **Precision@K** | How many of the retrieved chunks are relevant?     |
| **MRR**         | How high was the first relevant chunk ranked?      |
| **NDCG@K**      | Did we rank the most relevant chunks near the top? |

---

# 2. Required Input

Assume the reranker has already produced:

```python
reranked_results = [
    {
        "chunk_id": "chunk_42",
        "score": 0.94,
        "text": "AWS Bedrock can be used to build RAG applications."
    },
    {
        "chunk_id": "chunk_91",
        "score": 0.82,
        "text": "Amazon S3 is an object storage service."
    },
    {
        "chunk_id": "chunk_17",
        "score": 0.79,
        "text": "Bedrock provides access to foundation models."
    },
    {
        "chunk_id": "chunk_63",
        "score": 0.51,
        "text": "AWS Lambda runs serverless functions."
    },
    {
        "chunk_id": "chunk_75",
        "score": 0.43,
        "text": "Bedrock supports knowledge bases."
    }
]
```

The evaluation dataset must also tell us which chunks are actually relevant.

Example:

```python
ground_truth = {
    "chunk_42",
    "chunk_17",
    "chunk_75"
}
```

So:

```text
Relevant chunks:

chunk_42  ✓
chunk_17  ✓
chunk_75  ✓
```

Retrieved:

```text
Rank 1 → chunk_42 ✓
Rank 2 → chunk_91 ✗
Rank 3 → chunk_17 ✓
Rank 4 → chunk_63 ✗
Rank 5 → chunk_75 ✓
```

---

# 3. Extract Retrieved IDs

First convert the reranker output into an ordered list.

```python
retrieved_ids = [
    result["chunk_id"]
    for result in reranked_results
]

print(retrieved_ids)
```

Output:

```text
[
    "chunk_42",
    "chunk_91",
    "chunk_17",
    "chunk_63",
    "chunk_75"
]
```

The order is important because MRR and NDCG depend on ranking.

---

# 4. Recall@K

## Definition

Recall@K answers:

> Did the Top-K retrieval results contain the relevant chunks?

Formula:

```text
Recall@K =
Number of relevant chunks retrieved in Top-K
--------------------------------------------
Total number of relevant chunks
```

---

## Example

Ground truth:

```python
ground_truth = {
    "chunk_42",
    "chunk_17",
    "chunk_75"
}
```

Top 5:

```text
chunk_42 ✓
chunk_91 ✗
chunk_17 ✓
chunk_63 ✗
chunk_75 ✓
```

All 3 relevant chunks were found.

Therefore:

```text
Recall@5 = 3 / 3 = 1.0
```

---

## Python

```python
def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:

    if not relevant_ids:
        return 0.0

    top_k = retrieved_ids[:k]

    relevant_retrieved = sum(
        1
        for chunk_id in top_k
        if chunk_id in relevant_ids
    )

    return relevant_retrieved / len(relevant_ids)
```

Usage:

```python
recall = recall_at_k(
    retrieved_ids,
    ground_truth,
    k=5,
)

print(f"Recall@5: {recall:.4f}")
```

Output:

```text
Recall@5: 1.0000
```

---

# 5. Precision@K

## Definition

Precision@K answers:

> Of the Top-K chunks we retrieved, how many are relevant?

Formula:

```text
Precision@K =
Relevant chunks retrieved in Top-K
----------------------------------
K
```

For the example:

```text
Top 5:

chunk_42 ✓
chunk_91 ✗
chunk_17 ✓
chunk_63 ✗
chunk_75 ✓
```

3 out of 5 are relevant.

Therefore:

```text
Precision@5 = 3 / 5
            = 0.60
```

---

## Python

```python
def precision_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:

    if k <= 0:
        return 0.0

    top_k = retrieved_ids[:k]

    relevant_retrieved = sum(
        1
        for chunk_id in top_k
        if chunk_id in relevant_ids
    )

    return relevant_retrieved / len(top_k)
```

Usage:

```python
precision = precision_at_k(
    retrieved_ids,
    ground_truth,
    k=5,
)

print(f"Precision@5: {precision:.4f}")
```

Output:

```text
Precision@5: 0.6000
```

---

# 6. MRR — Mean Reciprocal Rank

## Definition

MRR answers:

> How high was the FIRST relevant chunk?

It only cares about the first relevant result.

Formula:

```text
Reciprocal Rank = 1 / rank_of_first_relevant_result
```

Example:

```text
Rank 1 → chunk_42 ✓
```

Therefore:

```text
RR = 1 / 1
   = 1.0
```

Another example:

```text
Rank 1 → irrelevant
Rank 2 → irrelevant
Rank 3 → relevant
```

Then:

```text
RR = 1 / 3
   = 0.3333
```

For multiple queries:

```text
MRR = average(Reciprocal Rank)
```

---

## Python

```python
def reciprocal_rank(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:

    for rank, chunk_id in enumerate(
        retrieved_ids,
        start=1,
    ):

        if chunk_id in relevant_ids:
            return 1.0 / rank

    return 0.0
```

Usage:

```python
rr = reciprocal_rank(
    retrieved_ids,
    ground_truth,
)

print(f"Reciprocal Rank: {rr:.4f}")
```

Output:

```text
Reciprocal Rank: 1.0000
```

Because `chunk_42` is ranked first.

---

# 7. MRR Across Multiple Queries

MRR becomes more useful when evaluating a complete test dataset.

Example:

```python
evaluation_data = [
    {
        "query": "How does Bedrock support RAG?",
        "relevant_chunks": {
            "chunk_42",
            "chunk_17",
        },
    },
    {
        "query": "How does HNSW work?",
        "relevant_chunks": {
            "chunk_91",
        },
    },
]
```

Python:

```python
def mean_reciprocal_rank(
    all_retrieved_ids: list[list[str]],
    all_relevant_ids: list[set[str]],
) -> float:

    if not all_retrieved_ids:
        return 0.0

    reciprocal_ranks = []

    for retrieved, relevant in zip(
        all_retrieved_ids,
        all_relevant_ids,
    ):

        rr = reciprocal_rank(
            retrieved,
            relevant,
        )

        reciprocal_ranks.append(rr)

    return sum(reciprocal_ranks) / len(
        reciprocal_ranks
    )
```

---

# 8. NDCG@K

## Definition

NDCG stands for:

> Normalized Discounted Cumulative Gain

NDCG evaluates **ranking quality**.

Unlike Recall and Precision, it can handle **graded relevance**.

For example:

```text
3 → Highly relevant
2 → Relevant
1 → Somewhat relevant
0 → Irrelevant
```

Example:

```text
Rank 1 → relevance 3
Rank 2 → relevance 2
Rank 3 → relevance 0
Rank 4 → relevance 1
Rank 5 → relevance 0
```

NDCG rewards highly relevant chunks appearing near the top.

---

# 9. Why NDCG is useful for RAG

Consider:

### Ranking A

```text
Rank 1 → Highly relevant
Rank 2 → Relevant
Rank 3 → Irrelevant
```

versus:

### Ranking B

```text
Rank 1 → Irrelevant
Rank 2 → Relevant
Rank 3 → Highly relevant
```

Both might contain the same relevant chunks.

But Ranking A is better for RAG because the strongest context is immediately available at the top.

NDCG captures this difference.

---

# 10. NDCG Python Implementation

```python
import math


def dcg_at_k(
    relevance_scores: list[int],
    k: int,
) -> float:

    scores = relevance_scores[:k]

    dcg = 0.0

    for rank, relevance in enumerate(
        scores,
        start=1,
    ):

        dcg += (
            (2 ** relevance - 1)
            / math.log2(rank + 1)
        )

    return dcg
```

Calculate NDCG:

```python
def ndcg_at_k(
    relevance_scores: list[int],
    k: int,
) -> float:

    actual_dcg = dcg_at_k(
        relevance_scores,
        k,
    )

    ideal_scores = sorted(
        relevance_scores,
        reverse=True,
    )

    ideal_dcg = dcg_at_k(
        ideal_scores,
        k,
    )

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg
```

---

# 11. Example NDCG

Suppose your reranked results have relevance labels:

```python
relevance_scores = [
    3,  # rank 1
    2,  # rank 2
    0,  # rank 3
    1,  # rank 4
    0,  # rank 5
]
```

Calculate:

```python
score = ndcg_at_k(
    relevance_scores,
    k=5,
)

print(f"NDCG@5: {score:.4f}")
```

The score ranges from approximately:

```text
0 → poor ranking
1 → ideal ranking
```

---

# 12. Complete Evaluation Code

You can put all four metrics into:

```text
evaluation/
└── retrieval_metrics.py
```

```python
import math


def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:

    if not relevant_ids:
        return 0.0

    top_k = retrieved_ids[:k]

    relevant_retrieved = sum(
        1
        for chunk_id in top_k
        if chunk_id in relevant_ids
    )

    return relevant_retrieved / len(relevant_ids)


def precision_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:

    top_k = retrieved_ids[:k]

    if not top_k:
        return 0.0

    relevant_retrieved = sum(
        1
        for chunk_id in top_k
        if chunk_id in relevant_ids
    )

    return relevant_retrieved / len(top_k)


def reciprocal_rank(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:

    for rank, chunk_id in enumerate(
        retrieved_ids,
        start=1,
    ):

        if chunk_id in relevant_ids:
            return 1.0 / rank

    return 0.0


def mean_reciprocal_rank(
    all_retrieved_ids: list[list[str]],
    all_relevant_ids: list[set[str]],
) -> float:

    if not all_retrieved_ids:
        return 0.0

    scores = []

    for retrieved, relevant in zip(
        all_retrieved_ids,
        all_relevant_ids,
    ):

        scores.append(
            reciprocal_rank(
                retrieved,
                relevant,
            )
        )

    return sum(scores) / len(scores)


def dcg_at_k(
    relevance_scores: list[int],
    k: int,
) -> float:

    scores = relevance_scores[:k]

    dcg = 0.0

    for rank, relevance in enumerate(
        scores,
        start=1,
    ):

        dcg += (
            (2 ** relevance - 1)
            / math.log2(rank + 1)
        )

    return dcg


def ndcg_at_k(
    relevance_scores: list[int],
    k: int,
) -> float:

    actual_dcg = dcg_at_k(
        relevance_scores,
        k,
    )

    ideal_scores = sorted(
        relevance_scores,
        reverse=True,
    )

    ideal_dcg = dcg_at_k(
        ideal_scores,
        k,
    )

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg
```

---

# 13. Using It With `reranked_results`

Assume:

```python
reranked_results = [
    {
        "chunk_id": "chunk_42",
        "score": 0.94,
    },
    {
        "chunk_id": "chunk_91",
        "score": 0.82,
    },
    {
        "chunk_id": "chunk_17",
        "score": 0.79,
    },
    {
        "chunk_id": "chunk_63",
        "score": 0.51,
    },
    {
        "chunk_id": "chunk_75",
        "score": 0.43,
    },
]
```

Ground truth:

```python
ground_truth = {
    "chunk_42",
    "chunk_17",
    "chunk_75",
}
```

Extract IDs:

```python
retrieved_ids = [
    result["chunk_id"]
    for result in reranked_results
]
```

Calculate Recall:

```python
recall = recall_at_k(
    retrieved_ids,
    ground_truth,
    k=5,
)
```

Calculate Precision:

```python
precision = precision_at_k(
    retrieved_ids,
    ground_truth,
    k=5,
)
```

Calculate MRR:

```python
mrr = reciprocal_rank(
    retrieved_ids,
    ground_truth,
)
```

For NDCG, we need relevance labels.

Example:

```python
relevance_scores = [
    3,  # chunk_42
    0,  # chunk_91
    3,  # chunk_17
    0,  # chunk_63
    2,  # chunk_75
]
```

Then:

```python
ndcg = ndcg_at_k(
    relevance_scores,
    k=5,
)
```

Finally:

```python
print(f"Recall@5     : {recall:.4f}")
print(f"Precision@5  : {precision:.4f}")
print(f"MRR          : {mrr:.4f}")
print(f"NDCG@5       : {ndcg:.4f}")
```

---

# 14. How These Metrics Differ

The easiest way to remember them:

```text
Recall
│
└── Did I FIND the relevant chunks?


Precision
│
└── How much of what I retrieved is relevant?


MRR
│
└── How EARLY did I find the first relevant chunk?


NDCG
│
└── Did I RANK the most relevant chunks HIGH?
```

---

# 15. Recommended Metrics for Hybrid RAG

For your pipeline:

```text
BM25
  +
Vector Search
  ↓
RRF
  ↓
Reranker
  ↓
reranked_results
```

Evaluate each stage.

### BM25

```text
Recall@20
Precision@20
MRR
NDCG@20
```

### Vector Search

```text
Recall@20
Precision@20
MRR
NDCG@20
```

### Hybrid + RRF

```text
Recall@20
Precision@20
MRR
NDCG@20
```

### After Reranking

```text
Recall@5
Precision@5
MRR
NDCG@5
```

This allows you to determine whether each component is actually improving retrieval.

---

# 16. Example Evaluation Table

For illustration only:

| Pipeline            | Recall@20 | Precision@20 |  MRR | NDCG@20 |
| ------------------- | --------: | -----------: | ---: | ------: |
| BM25                |      0.72 |         0.48 | 0.61 |    0.64 |
| Vector              |      0.81 |         0.52 | 0.69 |    0.72 |
| BM25 + Vector + RRF |      0.88 |         0.59 | 0.76 |    0.80 |
| RRF + Reranker      |      0.87 |         0.78 | 0.85 |    0.91 |

These numbers are **examples only**. Your evaluation dataset should produce the actual values.

---

# 17. Important: RRF Is Not One of These Metrics

Your pipeline contains:

```text
BM25
 +
Vector
 ↓
RRF
 ↓
Reranker
```

RRF means:

> **Reciprocal Rank Fusion**

RRF is a **fusion algorithm**, not a retrieval evaluation metric.

It combines multiple ranked lists.

```text
BM25 Results
     │
     ├─────────┐
               ▼
Vector Results → RRF → Combined Ranking
```

MRR means:

> **Mean Reciprocal Rank**

MRR evaluates the ranking produced by your retriever.

```text
Retrieved Ranking
       │
       ▼
      MRR
       │
       ▼
How high was the
first relevant result?
```

So:

```text
RRF → combines results

MRR → evaluates results
```

---

# 18. Recommended RAG Evaluation Flow

Your complete evaluation architecture should look like:

```text
                         QUERY
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
           BM25                        Vector
             │                           │
          Top-20                      Top-20
             │                           │
             └─────────────┬─────────────┘
                           ▼
                          RRF
                           │
                       Top-20
                           │
                           ▼
                        Reranker
                           │
                           ▼
                       Top-5
                           │
                           ▼
                  reranked_results
                           │
                           ▼
                  ┌────────────────┐
                  │ Evaluation     │
                  │                │
                  │ Recall@K       │
                  │ Precision@K    │
                  │ MRR            │
                  │ NDCG@K         │
                  └────────────────┘
```

## Key takeaway

For your **retrieval stage**, start with:

```text
Recall@K
Precision@K
MRR
NDCG@K
```

The most important distinction is:

```text
Recall@K   → Did we retrieve the answer?

Precision@K → Did we retrieve mostly useful chunks?

MRR         → How early did we find the first useful chunk?

NDCG@K      → Are the most useful chunks ranked highest?
```

Then, **after retrieval evaluation**, evaluate the generated answer separately using metrics such as **faithfulness/groundedness, answer correctness, answer relevance, and citation correctness**. Retrieval metrics should not be used as a substitute for evaluating the final LLM response.

Packages that exposes these functions
ragas, deepeval, ranx