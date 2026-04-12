from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from dotenv import load_dotenv


load_dotenv()


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str:
        """Return a text completion for a system and user prompt."""


@dataclass
class OpenAIResponsesLLM:
    model: str = "gpt-5.1"

    def complete(self, system: str, user: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The openai package is not installed. Run `pip install -r requirements.txt`."
            ) from exc

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set.")

        client = OpenAI()
        response = client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.output_text.strip()


def build_llm(provider: str, model: str | None = None) -> LLMClient | None:
    if provider == "local":
        return None
    if provider == "openai":
        return OpenAIResponsesLLM(model=model or os.getenv("OPENAI_MODEL", "gpt-5.1"))
    raise ValueError(f"Unsupported LLM provider: {provider}")


@dataclass(frozen=True)
class AgentModelConfig:
    default: str | None = None
    single: str | None = None
    summarizer: str | None = None
    orchestrator: str | None = None
    fact_checker: str | None = None

    def model_for(self, role: str) -> str | None:
        explicit = getattr(self, role)
        return explicit or self.default


@dataclass(frozen=True)
class AgentLLMs:
    single: LLMClient | None = None
    summarizer: LLMClient | None = None
    orchestrator: LLMClient | None = None
    fact_checker: LLMClient | None = None


def build_agent_llms(provider: str, config: AgentModelConfig | None = None) -> AgentLLMs:
    config = config or AgentModelConfig()
    if provider == "local":
        return AgentLLMs()

    return AgentLLMs(
        single=build_llm(provider, config.model_for("single")),
        summarizer=build_llm(provider, config.model_for("summarizer")),
        orchestrator=build_llm(provider, config.model_for("orchestrator")),
        fact_checker=build_llm(provider, config.model_for("fact_checker")),
    )
