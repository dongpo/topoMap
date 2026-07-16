from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .baselines import tokenize
from .specification import Specification

PROTOCOL_VERSION = "nma-bench-adapter/1.0"


class ExternalBaseline:
    def __init__(
        self,
        configuration: dict[str, Any],
        specification: Specification,
        root: Path,
    ):
        self.configuration = configuration
        self.specification = specification
        self.root = root
        self.name = str(configuration["name"])
        command = configuration.get("command")
        if (
            not isinstance(command, list)
            or not command
            or not all(isinstance(item, str) and item for item in command)
        ):
            raise ValueError(f"External system {self.name!r} requires a non-empty command array")
        self.command = command
        self.timeout_seconds = int(configuration.get("timeout_seconds", 120))
        self.repetitions = int(configuration.get("repetitions", 3))
        self.context_mode = str(configuration.get("context_mode", "none"))
        self.top_k = int(configuration.get("top_k", 3))
        self.metadata = configuration.get("metadata", {})
        if not isinstance(self.metadata, dict):
            raise ValueError(f"External system {self.name!r} metadata must be an object")
        required_metadata = {"model", "model_version", "server", "server_version", "prompt_version"}
        missing_metadata = required_metadata - self.metadata.keys()
        if missing_metadata:
            raise ValueError(
                f"External system {self.name!r} is missing audit metadata: "
                f"{', '.join(sorted(missing_metadata))}"
            )
        if any("REPLACE_WITH" in str(value) for value in self.metadata.values()):
            raise ValueError(f"External system {self.name!r} contains placeholder audit metadata")
        if not 1 <= self.repetitions <= 20:
            raise ValueError(f"External system {self.name!r} repetitions must be between 1 and 20")
        if self.context_mode not in {"none", "document", "document_rag", "structured"}:
            raise ValueError(f"Unsupported context_mode for {self.name!r}: {self.context_mode}")

    def _document_chunks(self) -> list[dict[str, Any]]:
        return [
            {
                "rule_id": rule.rule_id,
                "text": f"{rule.message} {rule.evidence.excerpt}",
                "evidence": rule.evidence.as_dict(),
            }
            for rule in self.specification.rules
        ]

    def _context(self, task: dict[str, Any]) -> Any:
        if self.context_mode == "none":
            return None
        if self.context_mode == "structured":
            return self.specification.raw
        chunks = self._document_chunks()
        if self.context_mode == "document":
            return chunks
        query = tokenize(task["input"])
        return sorted(
            chunks,
            key=lambda chunk: len(query & tokenize(chunk["text"])),
            reverse=True,
        )[: self.top_k]

    def run(self, task: dict[str, Any], run_index: int) -> dict[str, Any]:
        public_task = {key: value for key, value in task.items() if key != "expected"}
        request = {
            "protocol": PROTOCOL_VERSION,
            "system": self.name,
            "run_index": run_index,
            "task": public_task,
            "context_mode": self.context_mode,
            "context": self._context(task),
        }
        try:
            process = subprocess.run(
                self.command,
                cwd=self.root,
                input=json.dumps(request, ensure_ascii=False),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"adapter timed out after {self.timeout_seconds} seconds") from exc
        except OSError as exc:
            raise RuntimeError(f"adapter could not start: {exc}") from exc
        if process.returncode != 0:
            detail = process.stderr.strip()[-1000:] or f"exit code {process.returncode}"
            raise RuntimeError(f"adapter failed: {detail}")
        try:
            response = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("adapter did not return one JSON object on stdout") from exc
        if not isinstance(response, dict) or "value" not in response:
            raise RuntimeError("adapter response must be an object containing 'value'")
        evidence = response.get("evidence", [])
        if not isinstance(evidence, list) or not all(isinstance(item, dict) for item in evidence):
            raise RuntimeError("adapter response 'evidence' must be an array of objects")
        response["evidence"] = evidence
        return response

    def audit_configuration(self) -> dict[str, Any]:
        return {
            "protocol": PROTOCOL_VERSION,
            "command": self.command,
            "context_mode": self.context_mode,
            "top_k": self.top_k if self.context_mode == "document_rag" else None,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
        }


def load_external_config(path: str | Path) -> list[dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    systems = raw.get("systems") if isinstance(raw, dict) else None
    if not isinstance(systems, list):
        raise ValueError("External baseline config must contain a 'systems' array")
    if not all(
        isinstance(item, dict) and isinstance(item.get("name"), str) and bool(item["name"].strip())
        for item in systems
    ):
        raise ValueError("External systems must be objects with non-empty names")
    names = [item["name"] for item in systems]
    if len(names) != len(set(names)):
        raise ValueError("External system names must be unique")
    return systems
