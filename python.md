Python: Multithreading vs Multiprocessing vs asyncio vs Semaphore

The easiest way to remember them:

Concept	Best for	Runs truly in parallel?
Multithreading	I/O-bound work	Not usually for Python CPU work because of GIL
Multiprocessing / Multi-core	CPU-bound work	Yes
asyncio	Many concurrent I/O operations	No, single-threaded cooperative concurrency
Semaphore	Limiting concurrency	It's a control mechanism, not an execution model
1. Multithreading

Multiple threads execute within the same Python process.

Process
│
├── Thread 1
├── Thread 2
├── Thread 3
└── Thread 4

Threads share:

Memory
Variables
Resources
Best use case

I/O-bound operations:

API calls
Database calls
File I/O
Network requests
Waiting for services

Example:

import threading
import time


def download_file(name):
    print(f"Downloading {name}")
    time.sleep(2)
    print(f"Finished {name}")


threads = []

for i in range(5):
    thread = threading.Thread(
        target=download_file,
        args=(f"file-{i}",)
    )

    threads.append(thread)
    thread.start()


for thread in threads:
    thread.join()

print("All downloads completed")
Sequential version
for i in range(5):
    download_file(f"file-{i}")

Each operation waits for the previous one.

Threaded version
Thread 1 ── waiting ───────── done
Thread 2 ── waiting ───────── done
Thread 3 ── waiting ───────── done
Thread 4 ── waiting ───────── done
Thread 5 ── waiting ───────── done

While one thread waits for I/O, another can execute.

2. Multi-core / Multiprocessing

If the task is CPU-intensive, Python threads are usually not the right tool because of the GIL (Global Interpreter Lock) in CPython.

For CPU-heavy work, use multiple processes.

CPU
├── Core 1 → Process 1
├── Core 2 → Process 2
├── Core 3 → Process 3
└── Core 4 → Process 4

Each process has its own Python interpreter and memory space.

Example
from multiprocessing import Process


def calculate(number):
    result = 0

    for i in range(number):
        result += i * i

    print(result)


processes = []

for i in range(4):
    process = Process(
        target=calculate,
        args=(10_000_000,)
    )

    processes.append(process)
    process.start()


for process in processes:
    process.join()

print("Completed")

The processes can execute CPU-heavy calculations on different CPU cores.

Best use cases
Image processing
Video processing
Large numerical calculations
CPU-heavy data processing
Machine learning preprocessing
Compression
CPU-intensive algorithms
3. Multithreading vs Multiprocessing

The key difference:

Multithreading

One Process
     │
 ┌───┼────┬────┐
 T1  T2   T3   T4

Shared memory

versus:

Multiprocessing

Process 1 → CPU Core 1
Process 2 → CPU Core 2
Process 3 → CPU Core 3
Process 4 → CPU Core 4

Separate memory
Interview answer

Multithreading is mainly useful for I/O-bound tasks where threads spend time waiting, while multiprocessing is useful for CPU-bound tasks because separate processes can execute in parallel across CPU cores.

4. asyncio

asyncio is different from both threading and multiprocessing.

It uses cooperative concurrency.

Instead of creating many threads:

Thread 1
Thread 2
Thread 3
Thread 4

you typically have:

One Event Loop
      │
      ├── Task 1
      ├── Task 2
      ├── Task 3
      └── Task 4

When a task reaches an await and is waiting for I/O, the event loop can execute another task.

Basic example
import asyncio


async def fetch_data(name):
    print(f"Starting {name}")

    await asyncio.sleep(2)

    print(f"Finished {name}")


async def main():

    await asyncio.gather(
        fetch_data("API-1"),
        fetch_data("API-2"),
        fetch_data("API-3"),
        fetch_data("API-4")
    )


asyncio.run(main())

Instead of:

API-1 → wait 2 sec → done
API-2 → wait 2 sec → done
API-3 → wait 2 sec → done
API-4 → wait 2 sec → done

you get:

API-1 ──┐
API-2 ──┤
API-3 ──┼── waiting concurrently
API-4 ──┘
         ↓
       done

Approximately 2 seconds rather than 8 seconds for this example.

5. Why asyncio is useful for AI Engineering

This is particularly useful for LLM applications.

Imagine an agent needs to call:

LLM API
Vector DB
Database
Web API
Another service

Sequential:

result1 = await call_llm()
result2 = await search_vector_db()
result3 = await call_api()

Each waits for the previous operation.

If they're independent:

results = await asyncio.gather(
    call_llm(),
    search_vector_db(),
    call_api()
)

They can run concurrently while waiting for I/O.

6. asyncio vs Multithreading

Both can help with I/O.

Threading
threading.Thread(...)

The operating system manages threads.

Asyncio
async def ...
await ...
asyncio.gather(...)

The event loop manages tasks cooperatively.

Think:

Threading
─────────
OS manages multiple threads


Asyncio
───────
Event loop manages multiple async tasks

For a large number of network operations, asyncio can be more efficient because you don't need one OS thread per operation.

7. Semaphore

This is an important interview concept.

A Semaphore limits how many tasks can access a resource concurrently.

Suppose you have:

100 API requests

But the API allows only:

10 concurrent requests

Without a semaphore:

100 requests
     ↓
100 concurrent calls
     ↓
Rate limiting / overload

With a semaphore:

100 requests
     ↓
Semaphore(10)
     ↓
10 at a time
8. asyncio.Semaphore

Example:

import asyncio


semaphore = asyncio.Semaphore(3)


async def call_api(i):

    async with semaphore:

        print(f"Starting request {i}")

        await asyncio.sleep(2)

        print(f"Finished request {i}")


async def main():

    tasks = [
        call_api(i)
        for i in range(10)
    ]

    await asyncio.gather(*tasks)


asyncio.run(main())

Only 3 tasks can enter the protected section at the same time.

Semaphore(3)

Request 1 ────────┐
Request 2 ────────┤
Request 3 ────────┤
                  │
                  ↓
             3 running
                  │
                  ↓
Request 4 ────────┐
Request 5 ────────┤
Request 6 ────────┘
9. Real AI/LLM Example

Suppose you need to process 1000 documents using an LLM.

Bad approach:

await asyncio.gather(
    *[
        call_llm(document)
        for document in documents
    ]
)

You could create a huge number of concurrent requests.

Instead:

semaphore = asyncio.Semaphore(10)

Then:

async def process_document(document):

    async with semaphore:

        response = await call_llm(document)

        return response

And:

results = await asyncio.gather(
    *[
        process_document(doc)
        for doc in documents
    ]
)

Now:

1000 documents
       ↓
asyncio tasks
       ↓
Semaphore(10)
       ↓
10 LLM calls at a time
       ↓
Results

This is a very common pattern in AI engineering.

10. Semaphore + Retry

In production, you often combine:

asyncio
+
Semaphore
+
Retry
+
Exponential Backoff

Example:

import asyncio


semaphore = asyncio.Semaphore(10)


async def call_llm_with_limit(prompt):

    async with semaphore:

        for attempt in range(3):

            try:
                return await call_llm(prompt)

            except Exception:

                if attempt == 2:
                    raise

                await asyncio.sleep(
                    2 ** attempt
                )

The flow is:

Request
   ↓
Semaphore
   ↓
LLM API
   ↓
Success

or:

Request
   ↓
Semaphore
   ↓
LLM API
   ↓
429 / temporary failure
   ↓
Wait
   ↓
Retry
11. Important Distinction

Don't say:

"Semaphore makes Python multithreaded."

That's incorrect.

A semaphore is a concurrency-control primitive.

You can use semaphores with:

asyncio
threading
multiprocessing

For example:

asyncio.Semaphore

is specifically designed for async code.

12. Quick Comparison
                 Multithreading    Multiprocessing    asyncio
----------------------------------------------------------------
Execution        Threads           Processes          Tasks
Memory           Shared            Separate           Same process
CPU parallelism  Limited in CPython Yes               No
Best for         I/O               CPU                I/O
Management       OS                OS                 Event loop
Overhead         Medium            Higher              Low
Typical use      APIs/files        CPU calculations    APIs/LLMs

And:

Semaphore
    ↓
Controls concurrency

It does NOT determine
whether execution uses:

Threads
Processes
or asyncio
13. Interview 30-Second Answer

Multithreading uses multiple threads within a process and is useful mainly for I/O-bound operations. Multiprocessing uses separate processes, allowing CPU-bound workloads to run in parallel across CPU cores and avoiding the CPython GIL limitation. Asyncio uses an event loop and lightweight async tasks, making it efficient for high-concurrency I/O such as API, database, and LLM calls. An asyncio Semaphore controls how many async tasks can execute a particular section concurrently, which is especially useful for limiting LLM/API calls and avoiding throttling.

One-line memory trick
I/O + few workers       → Threading
CPU + multiple cores    → Multiprocessing
Many I/O operations     → asyncio
Limit concurrent tasks  → Semaphore

| Stage                                   | Preferred approach                                       | Why                                     |
| --------------------------------------- | -------------------------------------------------------- | --------------------------------------- |
| Reading documents from S3/local storage | `asyncio` / async I/O                                    | I/O-bound                               |
| Parsing PDFs/DOCX                       | Depends                                                  | Can be CPU-heavy for large documents    |
| Chunking                                | Normal Python / multiprocessing for very large workloads | Usually inexpensive                     |
| Calling embedding API                   | **`asyncio + Semaphore`**                                | Network I/O + API rate limits           |
| Upserting to vector DB                  | **`asyncio + Semaphore`**                                | Network I/O                             |
| Heavy preprocessing                     | `multiprocessing`                                        | CPU-bound                               |
| Controlling API/DB concurrency          | **Semaphore**                                            | Prevents throttling/connection overload |
