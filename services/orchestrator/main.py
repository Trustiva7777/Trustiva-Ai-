import os
import json
from typing import Dict, Any, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field
from loguru import logger
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START


# Load env (from root .env when running in container)
load_dotenv(os.getenv("ENV_FILE", ".env"))

app = FastAPI(title="Trustiva Swarm Orchestrator")


# ----------------------- Minimal tool shims -----------------------
async def hf_generate(prompt: str) -> str:
    """
    Generate text using either Hugging Face Inference API (if HUGGING is set)
    or OpenAI Chat Completions (if OPENAI_API_KEY is set).
    """
    import httpx

    # Prefer read-only token if present (HUGGINGREAD), else HUGGING, then HUGGINGWRITE
    hf = os.getenv("HUGGINGREAD") or os.getenv("HUGGING") or os.getenv("HUGGINGWRITE")
    if hf:
        model = os.getenv("HF_MODEL", "meta-llama/Meta-Llama-3.1-70B-Instruct")
        base = os.getenv("HF_API_BASE", "https://api-inference.huggingface.co/models")
        headers = {"Authorization": f"Bearer {hf}"}
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{base}/{model}",
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {"max_new_tokens": 256},
                },
            )
            r.raise_for_status()
            data = r.json()
            # Normalize response shape
            if isinstance(data, list) and data and isinstance(data[0], dict):
                return data[0].get("generated_text") or json.dumps(data)[:1000]
            if isinstance(data, dict):
                return data.get("generated_text") or json.dumps(data)[:1000]
            return json.dumps(data)[:1000]

    oai = os.getenv("OPENAI_API_KEY")
    if oai:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=oai)
        rsp = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return rsp.choices[0].message.content or ""

    return "No LLM configured."


async def publish_ipfs(path: str) -> Dict[str, Any]:
    """Publish using the helper script, which supports CLI or HTTP API fallback."""
    import asyncio, sys

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "scripts/publish_to_ipfs.py",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await proc.communicate()
        if proc.returncode == 0:
            data = json.loads(out.decode("utf-8").strip() or "{}")
            return {"cid": data.get("cid"), "gateway": data.get("gateway"), "path": data.get("path")}
        return {"error": (err or out).decode("utf-8")}
    except Exception as e:
        return {"error": str(e)}


# ----------------------- Graph state & nodes -----------------------
class SwarmRequest(BaseModel):
    task: str
    params: Dict[str, Any] = Field(default_factory=dict)


async def node_marketing(state: Dict[str, Any]) -> Dict[str, Any]:
    params = state.get("params", {}) or {}
    prompt = params.get(
        "prompt",
        "Generate a 120-word RWA landing hero blurb with a clear call-to-action.",
    )
    txt = await hf_generate(prompt)
    provider = (
        "huggingface" if (os.getenv("HUGGINGREAD") or os.getenv("HUGGING") or os.getenv("HUGGINGWRITE")) else (
            "openai" if os.getenv("OPENAI_API_KEY") else "none"
        )
    )
    return {"output": {"content": txt, "provider": provider, "model": os.getenv("HF_MODEL") or os.getenv("OPENAI_MODEL")}}


async def node_webmaster(state: Dict[str, Any]) -> Dict[str, Any]:
    params = state.get("params", {}) or {}
    path = params.get("path", "dist")
    res = await publish_ipfs(path)
    return {"output": res}


async def node_support(state: Dict[str, Any]) -> Dict[str, Any]:
    reply = await hf_generate(
        "Draft a concise, friendly support response acknowledging receipt and promising follow-up."
    )
    return {"output": {"email_draft": reply}}


def route_from_state(state: Dict[str, Any]) -> Literal["marketing", "webmaster", "support"]:
    t = (state.get("task") or "").lower()
    if "seo" in t or "content" in t:
        return "marketing"
    if "publish" in t or "ipfs" in t:
        return "webmaster"
    if "email" in t or "inbox" in t or "support" in t:
        return "support"
    return "marketing"


# Build graph with conditional edges from START
graph = StateGraph(dict)
graph.add_node("marketing", node_marketing)
graph.add_node("webmaster", node_webmaster)
graph.add_node("support", node_support)
graph.add_conditional_edges(
    START,
    route_from_state,
    {
        "marketing": "marketing",
        "webmaster": "webmaster",
        "support": "support",
    },
)
graph.add_edge("marketing", END)
graph.add_edge("webmaster", END)
graph.add_edge("support", END)
app_state = graph.compile()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/swarm/run")
async def run_swarm(payload: SwarmRequest):
    state_dict = {"task": payload.task, "params": payload.params, "output": {}}
    result = await app_state.ainvoke(state_dict)
    return result.get("output", {})
