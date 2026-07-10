"""
Experiment-local LLM client.

The paper evaluated Claude Sonnet 3.5 (`claude-3-5-sonnet-20240620`), which was
retired on 2025-10-28 and is no longer served by Anthropic or the Lava gateway.
The extended experiments evaluate its direct same-tier successor,
`claude-sonnet-4-6`, through the same Lava token.

To keep the original evaluation pipeline reproducible, we do NOT edit
services/lava_service.py (which still pins the retired model). Instead we
subclass it and override only the model id, inheriting every prompt builder and
response parser verbatim so the LLM decisions are produced exactly as the
production Response/Canary agents would produce them.
"""
from __future__ import annotations

import json

from services.lava_service import LavaAIService

# Chosen for the extended paper (see AskUserQuestion decision):
# closest same-tier successor to the retired Sonnet 3.5, same $3/$15 pricing,
# and accepts the existing request format (temperature=0.1) unchanged.
DEFAULT_MODEL = "claude-sonnet-4-6"

# The paper's original model, retained for provenance / methods section.
PAPER_MODEL = "claude-3-5-sonnet-20240620"  # retired 2025-10-28


def make_llm_service(model: str = DEFAULT_MODEL) -> LavaAIService:
    """A LavaAIService that reuses all production prompts/parsers but targets
    the chosen (non-retired) model."""
    svc = LavaAIService()      # reads LAVA_FORWARD_TOKEN from env
    svc.model = model          # override the retired default
    return svc


async def raw_json_call(service: LavaAIService, prompt: str,
                        max_tokens: int = 1024, temperature: float = 0.1):
    """
    Send an arbitrary prompt through the same Lava endpoint the production
    service uses, and return parsed JSON plus measured latency and token usage.

    Used by Experiment 5 (custom CoT vs control prompts, needs token counts for
    the cost/latency delta). Mirrors LavaAIService.analyze_incident's transport
    but does not mutate the original service. Returns:
      {parsed: dict|None, raw_text: str, latency_s, input_tokens, output_tokens,
       lava_request_id, ok: bool}
    """
    import time
    import aiohttp

    headers = {
        "Authorization": f"Bearer {service.lava_token}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": service.model, "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    t0 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        async with session.post(service.lava_url, headers=headers, json=payload,
                                timeout=aiohttp.ClientTimeout(total=45)) as resp:
            text = await resp.text()
            latency = time.perf_counter() - t0
            lava_request_id = resp.headers.get("x-lava-request-id", "")
            if resp.status != 200:
                return {"parsed": None, "raw_text": text[:300], "latency_s": latency,
                        "input_tokens": 0, "output_tokens": 0,
                        "lava_request_id": lava_request_id, "ok": False}

    body = json.loads(text)
    usage = body.get("usage", {}) or {}
    content = ""
    if isinstance(body.get("content"), list) and body["content"]:
        content = body["content"][0].get("text", "")
    parsed = None
    c = content.strip()
    if c.startswith("```"):
        c = c.split("```")[1]
        if c.startswith("json"):
            c = c[4:]
    try:
        parsed = json.loads(c.strip())
    except Exception:
        parsed = None
    return {
        "parsed": parsed, "raw_text": content, "latency_s": latency,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "lava_request_id": lava_request_id, "ok": True,
    }
