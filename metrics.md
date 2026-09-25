Recall@K
What does it measure?

Recall@K answers:

"Out of all the relevant documents/chunks that exist, how many did my retriever successfully retrieve in the top K?"
High recall means:

"I'm good at finding the information that could potentially answer the question."

Precision asks a different question:

"Of the K chunks I retrieved, how many are actually relevant?"
Recall tells you whether you found the answer. Precision tells you whether you avoided unnecessary noise.

MRR — Mean Reciprocal Rank

Now we introduce ranking quality.

Recall and precision don't tell you enough about where the relevant result appears.

MRR asks:

"How high was the first relevant result ranked?"

11. NDCG

NDCG is more sophisticated.

NDCG = Normalized Discounted Cumulative Gain

It answers:

"Are the most relevant chunks ranked near the top, while also considering different degrees of relevance?"

Recall@K measures whether relevant chunks were retrieved, Precision@K measures how much of the retrieved set is relevant, MRR measures how high the first relevant chunk appears, and NDCG measures the quality of the entire ranking while giving more weight to highly relevant chunks appearing near the top.