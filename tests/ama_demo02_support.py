from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from nma.llm import LLMAdapter, LLMResult
from nma.llm.base import canonical_json
from nma.research_runtime import AMAResearchRuntime


ROOT = Path(__file__).resolve().parents[1]
SCHOOL_REQUEST = "Change elementary school 9920103 color to blue."
HYDRANT_REQUEST = "What is the reviewed portrayal rule for fire hydrant 9350906?"
AUTHORIZATION = (
    ROOT / "artifacts/runtime/school-hero/authorizations/"
    "authorization-school-demo-b4ecdbfc35ecaf73293ed497.json"
)


class ScriptedAdapter(LLMAdapter):
    def __init__(self, outputs: list[dict[str, Any]]) -> None:
        self.outputs = [deepcopy(item) for item in outputs]
        self.calls: list[dict[str, Any]] = []

    def generate_structured(
        self,
        *,
        task: str,
        instructions: str,
        context: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> LLMResult:
        self.calls.append(
            {
                "task": task,
                "instructions": instructions,
                "context": deepcopy(context),
                "output_schema": deepcopy(output_schema),
            }
        )
        output = self.outputs.pop(0)
        return LLMResult(
            model_id="qwen-test-recording",
            provider="recorded-local-test",
            output=output,
            latency_ms=1,
            usage={"input_tokens": 1, "output_tokens": 1},
            raw_response_hash=hashlib.sha256(canonical_json(output)).hexdigest(),
        )


def plan_candidate() -> dict[str, Any]:
    catalog = json.loads(
        (ROOT / "data/research/ama-demo-02-school-plan-catalog-v1.0.json").read_text(
            encoding="utf-8"
        )
    )
    return catalog["candidates"][0]


def school_adapter(*, candidate: dict[str, Any] | None = None) -> ScriptedAdapter:
    return ScriptedAdapter(
        [
            {"selected_node_ids": ["portrayal-rule:doc01:9920103"]},
            candidate or plan_candidate(),
        ]
    )


def runtime(adapter: LLMAdapter) -> AMAResearchRuntime:
    return AMAResearchRuntime(
        repository_root=ROOT,
        adapter=adapter,
        graph_settings={
            "NMA_GRAPH_BACKEND": "canonical-json",
            "NMA_GRAPH_FALLBACK": "canonical-json",
        },
    )
