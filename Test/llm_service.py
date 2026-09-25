import boto3

class BedrockLLMService:
    """Build prompts and call Amazon Bedrock Converse API."""

    def __init__(self, model_id, region_name="us-east-1", client=None):
        self.model_id = model_id
        self.client = client or boto3.client("bedrock-runtime", region_name=region_name)

    def build_prompt(self, query, context):
        return (
            "Answer the user's question using only the supplied context.\n"
            "If the answer is not present in the context, say that you do not "
            "have enough information.\n\n"
            f"Context:\n{context}\n\n"
            f"Question:\n{query}\n\n"
            "Answer:"
        )

    def generate(self, query, context, max_tokens=512, temperature=0.0):
        prompt = self.build_prompt(query, context)

        response = self.client.converse(
            modelId=self.model_id,
            messages=[{
                "role": "user",
                "content": [{"text": prompt}],
            }],
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        )
        return self._extract_text(response)

    @staticmethod
    def _extract_text(response):
        try:
            content = response["output"]["message"]["content"]
            return "".join(
                item["text"] for item in content if "text" in item
            ).strip()
        except (KeyError, TypeError) as exc:
            raise ValueError("Invalid Bedrock response format") from exc
