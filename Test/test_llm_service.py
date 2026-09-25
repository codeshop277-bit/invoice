import pytest
from llm_service import BedrockLLMService


class FakeBedrockClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def test_build_prompt_contains_context_and_query():
    service = BedrockLLMService("test-model", client=FakeBedrockClient({}))

    prompt = service.build_prompt(
        "What is RAG?",
        "RAG retrieves relevant documents before generation.",
    )

    assert "What is RAG?" in prompt
    assert "RAG retrieves relevant documents before generation." in prompt
    assert "Answer:" in prompt


def test_generate_calls_bedrock_with_expected_parameters():
    client = FakeBedrockClient({
        "output": {
            "message": {
                "content": [{"text": "RAG combines retrieval and generation."}]
            }
        }
    })
    service = BedrockLLMService("amazon.nova-lite-v1:0", client=client)

    result = service.generate(
        "What is RAG?",
        "RAG combines retrieval and generation.",
        max_tokens=100,
        temperature=0.2,
    )

    assert result == "RAG combines retrieval and generation."
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["modelId"] == "amazon.nova-lite-v1:0"
    assert call["inferenceConfig"] == {"maxTokens": 100, "temperature": 0.2}
    assert "What is RAG?" in call["messages"][0]["content"][0]["text"]


def test_generate_raises_for_invalid_response():
    service = BedrockLLMService(
        "test-model",
        client=FakeBedrockClient({"unexpected": "response"}),
    )

    with pytest.raises(ValueError, match="Invalid Bedrock response format"):
        service.generate("What is RAG?", "Some context")


def test_extract_text_combines_multiple_text_blocks():
    response = {
        "output": {
            "message": {
                "content": [{"text": "Hello "}, {"text": "world"}]
            }
        }
    }
    assert BedrockLLMService._extract_text(response) == "Hello world"
