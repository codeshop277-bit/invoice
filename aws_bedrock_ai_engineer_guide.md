# Amazon Bedrock — AI Engineer Guide

## What is Amazon Bedrock?

Amazon Bedrock is a fully managed AWS service for building generative-AI applications using foundation models without managing the underlying model infrastructure.

```text
Your Application
      |
      v
 Python / FastAPI
      |
      v
 Amazon Bedrock
      |
  +---+---+----------------+
  |       |                |
Models  Guardrails     Knowledge/RAG
  |
  v
Response
```

Typical use cases:
- Chatbots
- RAG applications
- Document Q&A
- Summarization and classification
- Content generation
- Agents and tool calling
- Embeddings
- Knowledge Bases
- Model evaluation
- Responsible-AI controls

---

## 1. Prerequisites

Install Boto3:

```bash
pip install boto3
```

Configure AWS credentials for development:

```bash
aws configure
```

For production, prefer IAM roles rather than hard-coded access keys.

You also need an AWS account, appropriate IAM permissions, a supported AWS Region, and access to the model you want to use.

---

## 2. Configure Bedrock in Python

```python
import boto3

bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1"
)
```

The region must support the model and Bedrock features you use.

---

## 3. Basic Bedrock Python Example

The `Converse` API provides a common interface for supported Bedrock models.

```python
import boto3

bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1"
)

model_id = "YOUR_MODEL_ID"

response = bedrock.converse(
    modelId=model_id,
    messages=[
        {
            "role": "user",
            "content": [
                {"text": "Explain Retrieval Augmented Generation in simple terms."}
            ]
        }
    ],
    inferenceConfig={
        "maxTokens": 500,
        "temperature": 0.2
    }
)

answer = response["output"]["message"]["content"][0]["text"]
print(answer)
```

### Important parameters

- `modelId`: identifies the model.
- `messages`: contains the conversation.
- `temperature`: controls output randomness.
- `maxTokens`: controls maximum generated output length.

---

## 4. System Prompt

```python
response = bedrock.converse(
    modelId=model_id,
    system=[
        {
            "text": """You are an enterprise AI assistant.
Answer concisely.
Do not invent information."""
        }
    ],
    messages=[
        {
            "role": "user",
            "content": [{"text": "What is RAG?"}]
        }
    ],
    inferenceConfig={
        "maxTokens": 500,
        "temperature": 0.2
    }
)
```

---

# 5. Bedrock Guardrails

Amazon Bedrock Guardrails provides configurable safety controls for generative-AI applications.

Controls can include:
- Content filters
- Denied topics
- Word filters
- Sensitive-information/PII detection
- Prompt attack detection
- Grounding/relevance controls where supported

```text
Input
  |
  v
Guardrail
  |
  +---- BLOCK
  |
  v
LLM
  |
  v
Output
  |
  v
Guardrail
  |
  +---- BLOCK
  |
  v
User
```

---

## 6. Input vs Output Guardrails

### Input Guardrail

The user's request is checked before model processing:

```text
User Input
    |
    v
Input Guardrail
    |
 +--+--+
 |     |
BLOCK ALLOW
 |     |
Stop   LLM
```

Example:

```text
User:
"Tell me how to bypass our company's security system."

Input Guardrail
        |
        v
      BLOCK
```

### Output Guardrail

The generated answer is checked before being returned:

```text
LLM Response
     |
     v
Output Guardrail
     |
  +--+--+
  |     |
BLOCK ALLOW
  |     |
Safe    User
message
```

---

## 7. Creating a Guardrail

Create/configure the guardrail in the Amazon Bedrock console.

Example policies:

### Content filters

```text
Hate
Insults
Sexual
Violence
Misconduct
```

### Denied topic

```text
Topic:
Internal security bypass

Definition:
Requests for instructions to bypass or circumvent
company security controls.
```

### Sensitive information

Configure appropriate PII/sensitive-information detection.

### Word filters

```text
internal-secret-term
```

### Prompt attack detection

Useful for detecting certain prompt-injection/jailbreak attempts.

After creating a guardrail, you receive an identifier and version:

```text
Guardrail ID:
abc123xyz

Version:
1
```

---

## 8. Attach a Guardrail Directly to Converse

```python
import boto3

bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1"
)

model_id = "YOUR_MODEL_ID"

guardrail_config = {
    "guardrailIdentifier": "YOUR_GUARDRAIL_ID",
    "guardrailVersion": "1",
    "trace": "enabled"
}

response = bedrock.converse(
    modelId=model_id,
    messages=[
        {
            "role": "user",
            "content": [{"text": "Explain our refund policy."}]
        }
    ],
    guardrailConfig=guardrail_config,
    inferenceConfig={
        "maxTokens": 500,
        "temperature": 0.2
    }
)

answer = response["output"]["message"]["content"][0]["text"]
print(answer)
```

This is the simplest integrated approach.

---

# 9. ApplyGuardrail API

`ApplyGuardrail` allows you to evaluate text independently without invoking a foundation model.

Use `source="INPUT"` for user input and `source="OUTPUT"` for generated output.

```python
import boto3

bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1"
)

GUARDRAIL_ID = "YOUR_GUARDRAIL_ID"
GUARDRAIL_VERSION = "1"


def check_input(user_input):
    response = bedrock.apply_guardrail(
        guardrailIdentifier=GUARDRAIL_ID,
        guardrailVersion=GUARDRAIL_VERSION,
        source="INPUT",
        content=[
            {
                "text": {
                    "text": user_input
                }
            }
        ]
    )
    return response
```

---

## 10. Checking Whether Input Was Blocked

```python
def check_input(user_input):
    response = bedrock.apply_guardrail(
        guardrailIdentifier=GUARDRAIL_ID,
        guardrailVersion=GUARDRAIL_VERSION,
        source="INPUT",
        content=[
            {
                "text": {
                    "text": user_input
                }
            }
        ]
    )

    if response["action"] == "GUARDRAIL_INTERVENED":
        return False

    return True
```

Then:

```python
if not check_input(user_input):
    print("Request blocked by safety policy.")
else:
    print("Input allowed.")
```

---

# 11. Complete Input → Bedrock → Output Guardrail Example

```python
import boto3

REGION = "us-east-1"
MODEL_ID = "YOUR_MODEL_ID"
GUARDRAIL_ID = "YOUR_GUARDRAIL_ID"
GUARDRAIL_VERSION = "1"

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)


def apply_guardrail(text, source):
    return bedrock.apply_guardrail(
        guardrailIdentifier=GUARDRAIL_ID,
        guardrailVersion=GUARDRAIL_VERSION,
        source=source,
        content=[
            {"text": {"text": text}}
        ]
    )


def check_input(user_input):
    result = apply_guardrail(user_input, "INPUT")

    if result["action"] == "GUARDRAIL_INTERVENED":
        return {
            "allowed": False,
            "message": "Your request cannot be processed."
        }

    return {"allowed": True}


def call_bedrock(user_input):
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": user_input}]
            }
        ],
        inferenceConfig={
            "maxTokens": 500,
            "temperature": 0.2
        }
    )

    return response["output"]["message"]["content"][0]["text"]


def check_output(model_output):
    result = apply_guardrail(model_output, "OUTPUT")

    if result["action"] == "GUARDRAIL_INTERVENED":
        return {
            "allowed": False,
            "message": "The generated response was blocked."
        }

    return {
        "allowed": True,
        "response": model_output
    }


def chat(user_input):
    input_check = check_input(user_input)

    if not input_check["allowed"]:
        return input_check["message"]

    model_output = call_bedrock(user_input)

    output_check = check_output(model_output)

    if not output_check["allowed"]:
        return output_check["message"]

    return output_check["response"]


if __name__ == "__main__":
    user_input = "Explain Retrieval Augmented Generation."
    answer = chat(user_input)
    print(answer)
```

This provides explicit input and output validation as separate stages.

---

# 12. Why Use ApplyGuardrail Separately?

This is especially useful in RAG.

Without an explicit input guardrail:

```text
User
 ↓
Retrieve documents
 ↓
LLM
 ↓
Guardrail
```

With `ApplyGuardrail`:

```text
User
 ↓
Input Guardrail
 ↓
BLOCK → stop
 ↓
ALLOW
 ↓
Vector DB
 ↓
Retrieved Context
 ↓
LLM
```

This can prevent unnecessary retrieval and model processing.

A useful production pattern is:

```text
Input Guardrail
       ↓
Authorization / Validation
       ↓
RAG Retrieval
       ↓
Prompt Construction
       ↓
Bedrock
       ↓
Output Guardrail
       ↓
User
```

---

# 13. RAG + Bedrock + Guardrails

```text
                       User
                         |
                         v
                     FastAPI
                         |
                         v
                +----------------+
                | Input          |
                | Guardrail      |
                +-------+--------+
                        |
                      ALLOW
                        |
                        v
                  Query Rewrite
                        |
                        v
                   Embeddings
                        |
                        v
                    Vector DB
                        |
                        v
                 Relevant Chunks
                        |
                        v
                Prompt Construction
                        |
                        v
                 Amazon Bedrock
                        |
                        v
                  LLM Response
                        |
                        v
                +----------------+
                | Output         |
                | Guardrail      |
                +-------+--------+
                        |
                      ALLOW
                        |
                        v
                       User
```

---

# 14. Guardrails vs Prompt Engineering

Do not confuse these.

### Prompt instruction

```text
System:
Do not provide confidential information.
```

This is an instruction to the model.

### Guardrail

```text
PII detection
Denied topics
Content filters
Word filters
```

This is an application-level safety control.

```text
Prompt
  |
  v
Model behavior

Guardrail
  |
  v
Application-level safety enforcement
```

For production GenAI systems, don't rely solely on a system prompt for safety.

---

# 15. Guardrails + RAG Grounding

Bedrock Guardrails can support grounding/relevance-related checks for generated content when configured appropriately.

Example:

```text
Retrieved Context:
"Company refunds are allowed within 30 days."

Model:
"Company refunds are allowed within 90 days."

                |
                v
         Grounding check
                |
                v
             DETECTED
```

Tune grounding configuration and thresholds against your application's data.

---

# 16. Important Tool-Calling Limitation

If you're building an agentic AI application, don't assume that attaching a guardrail means every tool argument is automatically safe.

Example:

```text
User
 ↓
LLM
 ↓
Tool call
{
   "tool": "transfer_money",
   "amount": 50000
}
```

For high-risk tool calls, implement application-level validation and authorization.

```python
def validate_transfer(amount, account):
    if amount > 10000:
        raise ValueError(
            "Transfer requires additional authorization"
        )
    return True
```

Then:

```text
LLM
 ↓
Tool call
 ↓
Application validation
 ↓
Authorization
 ↓
Tool execution
```

---

# 17. IAM Permissions

Your application role needs appropriate Bedrock permissions.

For model inference, a relevant permission is:

```text
bedrock:InvokeModel
```

For guardrails, grant the permissions required by the guardrail operations your application uses.

Follow **least privilege** rather than giving broad:

```text
bedrock:*
```

access.

Enterprise environments can also use IAM conditions to enforce use of a specific guardrail for inference requests.

---

# 18. Production Architecture

```text
                           Client
                             |
                             v
                         API Gateway
                             |
                             v
                          FastAPI
                             |
                 +-----------+-----------+
                 |                       |
          Authentication            Rate Limiting
                 |                       |
                 +-----------+-----------+
                             |
                             v
                       Input Guardrail
                             |
                         +---+---+
                         |       |
                       BLOCK   ALLOW
                                 |
                                 v
                         Business Validation
                                 |
                                 v
                           Query Processing
                                 |
                                 v
                           Vector Database
                                 |
                                 v
                           Context Retrieval
                                 |
                                 v
                       Prompt Construction
                                 |
                                 v
                       Amazon Bedrock
                                 |
                                 v
                         Foundation Model
                                 |
                                 v
                         Output Guardrail
                                 |
                         +-------+-------+
                         |               |
                       BLOCK           ALLOW
                         |               |
                         v               v
                    Safe Response       User
```

Additional production components:

```text
CloudWatch
    ↓
Logging / Metrics / Tracing

IAM
    ↓
Least-privilege access

IAM Roles / Secrets Manager
    ↓
Credential management

Application metrics
    ↓
Latency / tokens / errors / cost
```

---

# 19. Interview Answers

## What is Bedrock?

> Amazon Bedrock is a fully managed AWS service that provides API access to foundation models from Amazon and supported model providers. It allows us to build GenAI applications such as chatbots, RAG systems and agents without managing the underlying model infrastructure. We can use the Converse API for a consistent model interaction interface, and integrate features such as Guardrails, Knowledge Bases and tool calling.

## What are Bedrock Guardrails?

> Bedrock Guardrails is a safety layer for GenAI applications. We can configure content filters, denied topics, word filters, sensitive-information detection and other controls. Guardrails can evaluate model inputs and outputs. We can either attach a guardrail directly to the Converse API or use ApplyGuardrail independently before or after other application stages, which is particularly useful in RAG pipelines.

## Input vs Output Guardrails?

> An input guardrail validates the user's request before we proceed with retrieval or model invocation, so blocked requests can be stopped early. An output guardrail evaluates the model-generated response before returning it to the user. For a RAG system, I can use ApplyGuardrail on the input before vector retrieval and again on the generated response before returning it.

## Why Use ApplyGuardrail?

> ApplyGuardrail lets me evaluate text independently without invoking a foundation model. This gives me control over where safety checks happen in my application. For example, in a RAG pipeline I can validate the user's query before performing vector search, and then validate the generated answer before returning it.

---

# 20. Bedrock vs Self-Hosted LLM

| Bedrock | Self-hosted LLM |
|---|---|
| AWS-managed infrastructure | You manage infrastructure |
| Fast integration | More infrastructure work |
| Access to supported FMs | Full control over model/runtime |
| AWS-native IAM/security | You design infrastructure security |
| Pay for usage/inference | Pay for infrastructure |
| Less operational overhead | More operational control |
| Guardrails available | You implement/configure safety stack |
| No accelerator management required | You manage GPU/accelerator infrastructure |

Use Bedrock when managed model access and reduced infrastructure responsibility are valuable.

Self-host when you need greater control over model weights, runtime, serving stack, or hardware and are prepared to operate that infrastructure.

---

# 21. Bedrock vs SageMaker

| Bedrock | SageMaker |
|---|---|
| GenAI/foundation-model focused | Broader ML platform |
| Managed access to FMs | Build/train/deploy ML models |
| Less infrastructure management | More infrastructure control |
| RAG/Agents/Guardrails integrations | Training/tuning/deployment workflows |
| API-first FM consumption | Full ML lifecycle |

Simplified:

```text
Need to consume a foundation model?
        |
        v
     Bedrock

Need to train/develop/manage
your own ML models?
        |
        v
     SageMaker
```

The services can also be used together.

---

# 22. Bedrock + RAG

```text
Documents
    ↓
Chunking
    ↓
Embedding Model
    ↓
Vector Database
    ↓
Retrieved Context
    ↓
Prompt
    ↓
Amazon Bedrock
    ↓
Foundation Model
    ↓
Answer
```

With guardrails:

```text
User
 ↓
Input Guardrail
 ↓
Query
 ↓
Vector Search
 ↓
Context
 ↓
Bedrock
 ↓
Output Guardrail
 ↓
Answer
```

---

# 23. Bedrock + Agentic AI

```text
User
 ↓
Bedrock
 ↓
Reasoning / tool selection
 ↓
Tool
 ├── Database
 ├── REST API
 ├── Search
 └── Internal service
 ↓
Tool result
 ↓
Bedrock
 ↓
Final response
```

With safety controls:

```text
User
 ↓
Input Guardrail
 ↓
Bedrock
 ↓
Tool selection
 ↓
Application validation
 ↓
Authorization
 ↓
Tool execution
 ↓
Output Guardrail
 ↓
User
```

For sensitive actions, don't let the LLM alone decide whether an operation is authorized.

---

# 24. Complete Mental Model

```text
                    USER
                      |
                      v
                  FastAPI
                      |
                      v
              INPUT GUARDRAIL
                      |
                +-----+-----+
                |           |
              BLOCK        ALLOW
                |           |
                v           v
             Reject       RAG
                            |
                            v
                       Vector DB
                            |
                            v
                         Context
                            |
                            v
                       BEDROCK
                            |
                            v
                       FOUNDATION
                         MODEL
                            |
                            v
                     OUTPUT GUARDRAIL
                            |
                      +-----+-----+
                      |           |
                    BLOCK        ALLOW
                      |           |
                      v           v
                  Safe error    USER
```

---

# 25. Quick Revision Cheat Sheet

```text
Amazon Bedrock
|
├── Foundation Models
│   ├── Amazon models
│   └── Supported model providers
|
├── APIs
│   ├── Converse
│   ├── ConverseStream
│   └── ApplyGuardrail
|
├── GenAI Capabilities
│   ├── Chat
│   ├── RAG
│   ├── Agents
│   ├── Tool Calling
│   └── Embeddings
|
├── Guardrails
│   ├── Input protection
│   ├── Output protection
│   ├── Content filters
│   ├── Denied topics
│   ├── Word filters
│   ├── Sensitive information
│   └── Grounding/relevance controls
|
└── Security
    ├── IAM
    ├── Least privilege
    ├── Guardrail enforcement
    └── CloudWatch/observability
```

## One-line interview memory trick

> **Bedrock = managed foundation-model platform; Converse = model interaction API; Guardrails = safety layer; ApplyGuardrail = independent safety check; RAG/Agents = application patterns built around the model.**

---

## Official AWS References

- Amazon Bedrock documentation: https://docs.aws.amazon.com/bedrock/
- Bedrock Runtime API: https://docs.aws.amazon.com/bedrock/latest/APIReference/welcome.html
- Converse API: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html
- ApplyGuardrail API: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ApplyGuardrail.html
- Bedrock Guardrails: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html
