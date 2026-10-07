"""Model adapters for the Text2Cypher evaluation harness.

Every adapter exposes generate(system, user) -> str. Imports of cloud SDKs
are lazy so the harness (and the gold smoke test) runs without AWS
credentials installed.
"""


class GoldAdapter:
    """Returns the item's own gold Cypher. Smoke-tests the harness: execution
    accuracy must be 100 percent, anything less is a harness bug."""

    name = "gold"

    def __init__(self):
        self.current_item = None

    def generate(self, system, user):
        import json
        return json.dumps({"cypher": self.current_item["cypher"],
                           "params": self.current_item["params"]})


class AnthropicBedrockAdapter:
    """Claude models on Amazon Bedrock via the Anthropic Mantle client.
    model example: 'anthropic.claude-sonnet-5' (Bedrock ids carry the
    'anthropic.' prefix)."""

    def __init__(self, model, region="us-east-1", max_tokens=1500):
        from anthropic import AnthropicBedrockMantle
        self.client = AnthropicBedrockMantle(aws_region=region)
        self.model = model
        self.name = model
        self.max_tokens = max_tokens

    def generate(self, system, user):
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if b.type == "text")


class BedrockConverseAdapter:
    """Non-Claude Bedrock models (Llama, Mistral, Nova) via boto3 converse.
    model example: 'meta.llama3-3-70b-instruct-v1:0'."""

    def __init__(self, model, region="us-east-1", max_tokens=1500):
        import boto3
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model = model
        self.name = model
        self.max_tokens = max_tokens

    def generate(self, system, user):
        cfg = {"maxTokens": self.max_tokens}
        if "anthropic" not in self.model:
            # Claude 5 models reject sampling params; others get temp 0
            cfg["temperature"] = 0
        resp = self.client.converse(
            modelId=self.model,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig=cfg,
        )
        parts = resp["output"]["message"]["content"]
        return "".join(p.get("text", "") for p in parts)


class OllamaAdapter:
    """Open-weight models served locally by Ollama, via its native chat API.
    model example: 'llama3.1:8b-instruct-q8_0'.

    Sampling matches the Bedrock runs: temperature 0 and a 1,500-token cap,
    plus a fixed seed. The context window is set explicitly because Ollama
    otherwise truncates a long prompt silently to its default; a prompt that
    comes near the window raises instead of being cut."""

    def __init__(self, model, host="http://localhost:11434", max_tokens=1500,
                 num_ctx=8192):
        self.model = model
        self.name = model
        self.url = host.rstrip("/") + "/api/chat"
        self.options = {"temperature": 0, "seed": 0,
                        "num_predict": max_tokens, "num_ctx": num_ctx}

    def generate(self, system, user):
        import json
        import urllib.request
        body = json.dumps({
            "model": self.model, "stream": False, "keep_alive": "30m",
            "options": self.options,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }).encode("utf-8")
        req = urllib.request.Request(self.url, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as resp:
            out = json.loads(resp.read().decode("utf-8"))
        used = out.get("prompt_eval_count", 0)
        if used >= self.options["num_ctx"] - self.options["num_predict"]:
            raise RuntimeError(f"prompt of {used} tokens is near the "
                               f"{self.options['num_ctx']}-token window")
        return out["message"]["content"]


def make_adapter(spec, region="us-east-1"):
    """spec: 'gold', 'bedrock:<model-id>' (everything through the classic
    converse API: the Anthropic Mantle client needs the newer
    bedrock-mantle:CreateInference IAM action, which restricted roles often
    lack, while converse works for Claude models too),
    'mantle:<model-id>' to use the Anthropic client explicitly, or
    'ollama:<model>' for a model served locally by Ollama."""
    if spec == "gold":
        return GoldAdapter()
    if spec.startswith("bedrock:"):
        return BedrockConverseAdapter(spec.split(":", 1)[1], region=region)
    if spec.startswith("mantle:"):
        return AnthropicBedrockAdapter(spec.split(":", 1)[1], region=region)
    if spec.startswith("ollama:"):
        return OllamaAdapter(spec.split(":", 1)[1])
    raise ValueError(f"unknown adapter spec {spec}")
