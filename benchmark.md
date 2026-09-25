1. Time to First Token — TTFT
What it means

Time to First Token (TTFT) is:

The time between sending the request and receiving the first generated token.

Request
   │
   │
   ├──── preprocessing
   ├──── tokenization
   ├──── model queueing
   ├──── prefill
   └──── first token
                 ↑
                TTFT

For example:

Request sent:       10:00:00.000
First token:        10:00:00.800

TTFT = 800 ms
What affects TTFT?

For an LLM:

TTFT =
network latency
+ request queueing
+ tokenization
+ model loading/cache
+ prompt processing
+ first-token generation

For a self-hosted model, you may additionally have:

GPU scheduling
container overhead
model loading
KV-cache allocation
batching delay

For Bedrock, much of the infrastructure is managed for you.

Why TTFT matters

Imagine two models:

Model	TTFT
A	400 ms
B	2.5 sec

Even if both generate the response in the same total time, Model A feels much more responsive.

This matters heavily for:

chatbots
coding assistants
interactive agents
customer support
autocomplete
Selection implication

Lower TTFT is generally preferable when responsiveness is important, but don't select a model solely on TTFT.

A model with:

TTFT = 300 ms
Quality = poor

may be less useful than:

TTFT = 700 ms
Quality = excellent
2. Tokens Per Second — TPS

This measures how quickly the model generates tokens after generation begins.

For example:

First token
    ↓
Token 1
Token 2
Token 3
Token 4
...
Token 100

If 100 tokens take 5 seconds:

TPS = 100 / 5
    = 20 tokens/sec

Usually you'll measure output tokens/sec.

Why TPS matters

TPS determines how quickly the response streams.

Suppose:

Model A
TTFT = 500 ms
TPS = 20
Model B
TTFT = 500 ms
TPS = 80

For a 400-token answer:

Model A:

500ms + 400/20
≈ 20.5 sec

Model B:

500ms + 400/80
≈ 5.5 sec

Huge difference.

3. TTFT vs TPS

This is one of the most important distinctions in LLM benchmarking.

                 TTFT
Request ──────────────────► First Token
                               │
                               │
                               │ TPS
                               ▼
                         Token Token Token

TTFT answers:

How long before the model starts responding?

TPS answers:

How quickly does it continue responding?

You need both.

4. P50 Latency

P50 means:

50% of requests completed faster than this value, and 50% took longer.

Suppose your latency measurements are:

100 ms
110 ms
120 ms
130 ms
...
2000 ms

If:

P50 = 300 ms

then half of requests completed within roughly 300 ms.

P50 represents typical user experience better than average.

5. P95 Latency

P95 means:

95% of requests are at or below this latency.

Example:

P50 = 400 ms
P95 = 1.2 sec
P99 = 4.8 sec

Most users see:

~400 ms

But 5% experience:

>1.2 sec
6. P99 Latency

P99 represents the slow tail:

99% of requests are faster than this value.

For example:

P50 = 400 ms
P95 = 1.2 sec
P99 = 5 sec

That tells you that some requests occasionally become extremely slow.

This is particularly important for production systems because tail latency can determine whether your application feels reliable under load.

7. Why P50/P95/P99 are better than average

Suppose two models have:

Metric	Model A	Model B
Average	500 ms	600 ms
P50	400 ms	450 ms
P95	700 ms	800 ms
P99	800 ms	4 sec

Average makes them look similar.

But Model B has a major tail-latency problem.

Therefore:

Average latency
       ↓
not enough
       ↓
P50 + P95 + P99
       ↓
much better production picture
8. Throughput Under Concurrency

This asks:

How much work can the model process when multiple users request responses simultaneously?

For example:

1 concurrent request
5 concurrent requests
10 concurrent requests
25 concurrent requests
50 concurrent requests
100 concurrent requests

Measure:

requests/sec
tokens/sec
Example

Suppose:

1 concurrent request
TPS = 100
10 concurrent requests
Aggregate TPS = 750
50 concurrent requests
Aggregate TPS = 1,500

This tells you how the system scales.

9. Why concurrency changes everything

A model might look fantastic at concurrency = 1:

TTFT = 300 ms
TPS = 100

But at concurrency = 50:

TTFT = 4 sec
TPS = 25

That model may be unsuitable for your production workload.

The opposite can also happen.

A serving stack may use:

continuous batching
dynamic batching
request scheduling
KV-cache optimization

and therefore become more efficient as concurrency increases.

10. Accelerator Utilization

For self-hosted models, this usually means:

GPU utilization %

Example:

GPU utilization = 85%

means the accelerator is being heavily utilized.

But 100% GPU utilization isn't automatically better.

Suppose:

GPU utilization = 95%
TPS = 100

versus:

GPU utilization = 70%
TPS = 120

The second system is actually producing more work with less accelerator utilization.

Therefore, don't optimize utilization in isolation.

Measure:

GPU utilization
        +
tokens/sec
        +
latency
11. What high GPU utilization tells you

High utilization can indicate:

GPU is being efficiently used
model computation is the bottleneck
batching is working
hardware isn't sitting idle

But extremely high utilization can also mean:

no headroom
latency spikes under additional load
requests queue up
scaling becomes difficult

For production you often want good utilization with latency headroom, not simply 100%.

12. Memory Usage

For self-hosted LLMs, memory is critical.

Measure:

GPU VRAM
CPU RAM
KV cache
model weights
activation memory
runtime overhead

For example:

Model weights       30 GB
KV cache             8 GB
Runtime              2 GB
-------------------------
Total               40 GB

If your GPU has:

48 GB VRAM

you have:

8 GB headroom
13. Why memory affects model selection

Suppose:

Model A
70B parameters
VRAM requirement = 80 GB
Model B
32B parameters
VRAM requirement = 40 GB

If your infrastructure has:

1 × 48 GB GPU

Model A may require:

multi-GPU

while Model B can run on one GPU.

So the "better" model on paper might have a much higher infrastructure requirement.

14. Memory also affects concurrency

This is especially important for LLM serving.

The model weights aren't the only thing consuming VRAM.

During inference you also need:

Model weights
+
activations
+
KV cache
+
batching
+
runtime

As concurrent requests and context lengths increase:

KV cache
    ↑
    ↑
VRAM consumption

Eventually:

VRAM full
    ↓
batch size limited
    ↓
throughput decreases
    ↓
requests queue
    ↓
P95/P99 latency increases

So memory indirectly impacts latency and throughput.

15. Model Quality

This answers:

Does the model actually produce the correct/useful answer?

For your RAG system, don't just evaluate generic LLM benchmarks.

Evaluate your actual workload.

For RAG you might measure:

Retrieval
Recall@K
Precision@K
MRR
NDCG
Generation
Answer correctness
Faithfulness
Groundedness
Citation correctness
Completeness
Overall application
Task success rate
16. Example quality comparison

Suppose:

Metric	Model A	Model B
TTFT	500 ms	1 sec
TPS	100	60
P95	1.2 sec	2 sec
Quality	78%	94%
Cost	$0.002	$0.006

Model A is:

faster
cheaper

Model B is:

higher quality

You can't determine the right selection from performance metrics alone.

You need to understand the business requirement.

17. Cost per Request

This is particularly important when comparing:

Bedrock
       vs
Self-hosted

For Bedrock, you might calculate:

input token cost
+
output token cost
+
other applicable service costs

For self-hosting:

GPU cost
+
CPU/RAM
+
storage
+
network
+
load balancer
+
orchestration
+
idle capacity
+
operations

Then:

Cost per request =
Total infrastructure cost
-------------------------
Number of successful requests
18. Self-hosted Cost Example

Suppose:

GPU infrastructure = $4/hour

and you process:

1,000 requests/hour

Then the GPU component is:

$4 / 1000
= $0.004/request

But if utilization drops and you process only:

200 requests/hour

then:

$4 / 200
= $0.020/request

Same GPU.

Five times higher cost per request.

This is why throughput and utilization directly affect self-hosted economics.

19. Bedrock vs Self-Hosted

The comparison is particularly interesting here.

Bedrock

You generally care about:

TTFT
TPS
P95/P99
quality
cost/request

You don't directly manage:

GPU allocation
GPU utilization
VRAM
model serving infrastructure
Self-hosted

You additionally care about:

GPU utilization
VRAM
batch size
KV cache
GPU count
scaling
model loading
serving framework
infrastructure cost
20. How These Metrics Interact

This is the most important part.

They aren't independent.

                 Model size
                     │
             ┌───────┴────────┐
             ▼                ▼
          Memory           Compute
             │                │
             ▼                ▼
       Concurrency          TPS
             │                │
             └───────┬────────┘
                     ▼
                 Throughput
                     │
                     ▼
                 Queueing
                     │
                     ▼
                P95 / P99

And:

Model quality
      │
      ▼
Task success
      │
      ▼
Business value

while:

Infrastructure
      │
      ▼
Cost/request
21. A Practical Benchmark Matrix

For your Bedrock vs self-hosted benchmark, I'd create a matrix like this:

Metric	Bedrock	Self-hosted
TTFT	✓	✓
Output TPS	✓	✓
P50 latency	✓	✓
P95 latency	✓	✓
P99 latency	✓	✓
Requests/sec	✓	✓
Aggregate tokens/sec	✓	✓
GPU utilization	N/A/limited visibility	✓
VRAM usage	N/A/limited visibility	✓
CPU/RAM	N/A/limited visibility	✓
Model quality	✓	✓
Cost/request	✓	✓
Cost/1M tokens	✓	✓
Error rate	✓	✓
Timeout rate	✓	✓

I'd also add:

Input tokens and output tokens per request.

Otherwise two models generating different response lengths aren't being compared fairly.

22. Benchmark at Different Concurrency Levels

Don't benchmark only at concurrency = 1.

Use something like:

Concurrency
───────────
1
2
5
10
20
50
100

At every level measure:

TTFT
P50
P95
P99
Output TPS
Aggregate TPS
Error rate
Cost/request

For self-hosted:

GPU utilization
VRAM
CPU
RAM

This gives you a performance curve, rather than one misleading number.

23. Example Benchmark

Imagine:

Concurrency	Model	TTFT	P95	TPS	GPU
1	Bedrock	500ms	800ms	80	—
1	Self-hosted	300ms	500ms	100	62%
10	Bedrock	700ms	1.5s	75	—
10	Self-hosted	450ms	1.1s	92	84%
50	Bedrock	1.2s	3s	65	—
50	Self-hosted	900ms	2.4s	80	96%

Now you can understand:

Concurrency ↑
      ↓
queueing ↑
      ↓
latency ↑

and whether self-hosting maintains its advantage under realistic load.

24. Don't Pick the "Fastest" Model

This is a common benchmarking mistake.

Imagine:

Model A

TTFT       300ms
TPS        100
Quality    70%
Cost       $0.002

versus:

Model B

TTFT       700ms
TPS        70
Quality    95%
Cost       $0.005

For a simple chatbot, the latency difference might matter.

For an enterprise RAG system answering financial/legal/technical questions, correctness may dominate.

So model selection should be based on:

                 Quality
                    │
                    │
           ┌────────┴────────┐
           │                 │
        Latency           Cost
           │                 │
           └────────┬────────┘
                    │
                Throughput
                    │
                    ▼
              Business SLA
25. How I Would Select the Best Model

Instead of:

"Which model has the best benchmark?"

define minimum acceptable requirements first.

For example:

Quality ≥ 90%

P95 latency ≤ 2 seconds

TTFT ≤ 800 ms

Throughput ≥ 500 req/min

Error rate < 1%

Cost ≤ $0.01/request

Then eliminate models that fail mandatory requirements.

Only after that compare the trade-offs among the models that meet the requirements.

This is much more defensible in an AI engineering interview and in production.

26. The Metrics You Should Remember for Interviews

A concise explanation:

TTFT measures how quickly the model starts responding. It determines perceived responsiveness.

Tokens/sec measures generation speed after the first token and determines how quickly the response streams.

P50/P95/P99 latency describe typical and tail latency. P95/P99 are especially important for understanding production reliability under load.

Concurrency throughput measures how many requests or tokens the serving system can process simultaneously and exposes scalability limitations.

Accelerator utilization measures how effectively GPU/accelerator resources are being used. It helps identify underutilization, compute bottlenecks and capacity headroom.

Memory usage measures model weights, KV cache and runtime memory requirements. It determines whether the model fits on the available hardware and how much concurrency/context length the system can support.

Model quality measures whether the model actually solves the target task correctly. For RAG, this should include retrieval quality, groundedness, answer correctness and citation accuracy.

Cost per request combines infrastructure or API pricing with workload characteristics and tells us whether the model is economically viable.

And the key conclusion:

The best model isn't necessarily the model with the lowest latency or highest TPS. It is the model that satisfies the required quality and latency SLOs while providing sufficient throughput at an acceptable cost.