from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    base_url: str
    api_key_env: str = ""
    timeout_seconds: float = 120.0
    max_retries: int = 1
    retry_backoff_seconds: float = 1.0
    reasoning_effort: str = "high"


# ============================================================
# ERRORS
# ============================================================

class ModelAdapterError(RuntimeError):
    """Base model adapter error."""


class ModelConfigurationError(ModelAdapterError):
    """Invalid model configuration."""


class ModelProviderError(ModelAdapterError):
    """Provider request failure."""


class ModelResponseError(ModelAdapterError):
    """Malformed provider response."""


# ============================================================
# RESPONSE
# ============================================================

@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str
    request_id: str | None
    response_id: str | None
    usage: dict[str, Any]
    raw: dict[str, Any]
    tool_calls: tuple[dict[str, Any], ...] = ()
    assistant_message: dict[str, Any] | None = None
    thinking: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "provider": self.provider,
            "model": self.model,
            "request_id": self.request_id,
            "response_id": self.response_id,
            "usage": self.usage,
            "tool_calls": list(self.tool_calls),
            "assistant_message": self.assistant_message,
            "thinking": self.thinking,
        }


# ============================================================
# ADAPTER
# ============================================================

class AwareOnModelAdapter:
    """
    Provider-neutral AwareOn model adapter.

    Supported:
      - ollama
      - openai

    Ollama is the primary local/free development provider.
    """

    def __init__(self, config: ModelConfig) -> None:
        self.config = config

    # ========================================================
    # FACTORY
    # ========================================================

    @classmethod
    def from_environment(cls) -> "AwareOnModelAdapter":
        provider = os.getenv(
            "AWAREON_AI_PROVIDER",
            "ollama",
        ).strip().lower()

        model = os.getenv(
            "AWAREON_AI_MODEL",
            "",
        ).strip()

        if provider == "ollama":
            base_url = os.getenv(
                "AWAREON_AI_BASE_URL",
                "http://localhost:11434/api/chat",
            ).strip()

            api_key_env = ""

        else:
            base_url = os.getenv(
                "AWAREON_AI_BASE_URL",
                "https://api.openai.com/v1/responses",
            ).strip()

            api_key_env = os.getenv(
                "AWAREON_AI_API_KEY_ENV",
                "AWAREON_AI_API_KEY",
            ).strip()

        timeout_raw = os.getenv(
            "AWAREON_AI_TIMEOUT_SECONDS",
            "120",
        )

        retries_raw = os.getenv(
            "AWAREON_AI_MAX_RETRIES",
            "1",
        )

        backoff_raw = os.getenv(
            "AWAREON_AI_RETRY_BACKOFF_SECONDS",
            "1.0",
        )

        reasoning_effort = os.getenv(
            "AWAREON_AI_REASONING_EFFORT",
            "high",
        ).strip().lower()

        try:
            timeout_seconds = float(timeout_raw)
        except ValueError:
            timeout_seconds = 120.0

        try:
            max_retries = int(retries_raw)
        except ValueError:
            max_retries = 1

        try:
            backoff = float(backoff_raw)
        except ValueError:
            backoff = 1.0

        return cls(
            ModelConfig(
                provider=provider,
                model=model,
                base_url=base_url,
                api_key_env=api_key_env,
                timeout_seconds=max(1.0, timeout_seconds),
                max_retries=max(0, max_retries),
                retry_backoff_seconds=max(0.0, backoff),
                reasoning_effort=reasoning_effort,
            )
        )

    # ========================================================
    # STATUS
    # ========================================================

    @property
    def is_configured(self) -> bool:
        if not self.config.model:
            return False

        if not self.config.base_url:
            return False

        if self.config.provider == "ollama":
            return True

        return bool(
            self.config.api_key_env
            and os.getenv(self.config.api_key_env)
        )

    def configuration_status(self) -> dict[str, Any]:
        api_key_configured = False

        if self.config.provider != "ollama":
            api_key_configured = bool(
                self.config.api_key_env
                and os.getenv(self.config.api_key_env)
            )

        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "model_configured": bool(self.config.model),
            "base_url": self.config.base_url,
            "base_url_configured": bool(self.config.base_url),
            "api_key_configured": api_key_configured,
            "reasoning_effort": self.config.reasoning_effort,
            "timeout_seconds": self.config.timeout_seconds,
            "max_retries": self.config.max_retries,
        }

    # ========================================================
    # SIMPLE GENERATION
    # ========================================================

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        think: bool | None = None,
    ) -> str:
        response = self.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            think=think,
        )

        return response.text

    # ========================================================
    # FULL GENERATION
    # ========================================================

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        think: bool | None = None,
    ) -> ModelResponse:
        self._validate_configuration()

        if self.config.provider == "ollama":
            messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ]

            return self.generate_from_messages(
                messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                think=think,
            )

        if self.config.provider == "openai":
            return self._generate_openai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
            )

        raise ModelConfigurationError(
            f"Unsupported AwareOn AI provider: "
            f"{self.config.provider}"
        )

    # ========================================================
    # CONVERSATION CONTINUATION
    # ========================================================

    def generate_from_messages(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
        think: bool | None = None,
    ) -> ModelResponse:
        self._validate_configuration()

        if self.config.provider != "ollama":
            raise ModelConfigurationError(
                "generate_from_messages currently "
                "supports Ollama only."
            )

        return self._generate_ollama_messages(
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            think=think,
        )

    # ========================================================
    # JSON
    # ========================================================

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        schema: dict[str, Any],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        think: bool | None = False,
    ) -> dict[str, Any]:
        self._validate_schema(schema)
        self._validate_configuration()

        if self.config.provider == "ollama":
            response = self.generate_from_messages(
                [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=schema.get(
                    "schema",
                    {},
                ),
                think=think,
            )

        elif self.config.provider == "openai":
            response = self._generate_openai_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=schema,
                max_tokens=max_tokens,
            )

        else:
            raise ModelConfigurationError(
                f"Unsupported AwareOn AI provider: "
                f"{self.config.provider}"
            )

        text = response.text.strip()

        if not text:
            raise ModelResponseError(
                "Structured model response returned empty content."
            )

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModelResponseError(
                "Structured model response was not valid JSON."
            ) from exc

        if not isinstance(parsed, dict):
            raise ModelResponseError(
                "Structured model response must be a JSON object."
            )

        return parsed

    # ========================================================
    # OLLAMA
    # ========================================================

    def _generate_ollama_messages(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
        think: bool | None = None,
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
        }

        if think is not None:
            payload["think"] = think

        options: dict[str, Any] = {
            "temperature": temperature,
        }

        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload["options"] = options

        if tools:
            payload["tools"] = tools

        if response_format is not None:
            payload["format"] = response_format

        raw = self._request_with_retry(payload)

        message = raw.get("message")

        if not isinstance(message, dict):
            raise ModelResponseError(
                "Ollama response is missing a valid message."
            )

        text = message.get(
            "content",
            "",
        )

        if not isinstance(text, str):
            text = ""

        thinking = message.get(
            "thinking",
            "",
        )

        if not isinstance(thinking, str):
            thinking = ""

        tool_calls = self._extract_ollama_tool_calls(
            message
        )

        assistant_message = self._build_assistant_message(
            message
        )

        return ModelResponse(
            text=text.strip(),
            provider="ollama",
            model=self.config.model,
            request_id=None,
            response_id=None,
            usage=self._extract_ollama_usage(raw),
            raw=raw,
            tool_calls=tuple(tool_calls),
            assistant_message=assistant_message,
            thinking=thinking,
        )

    # ========================================================
    # ASSISTANT MESSAGE
    # ========================================================

    @staticmethod
    def _build_assistant_message(
        message: dict[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "role": "assistant",
            "content": message.get(
                "content",
                "",
            ),
        }

        tool_calls = message.get(
            "tool_calls"
        )

        if isinstance(tool_calls, list) and tool_calls:
            result["tool_calls"] = tool_calls

        return result

    # ========================================================
    # OPENAI
    # ========================================================

    def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "input": [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": system_prompt,
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_prompt,
                        }
                    ],
                },
            ],
        }

        if self.config.reasoning_effort:
            payload["reasoning"] = {
                "effort": self.config.reasoning_effort
            }

        if max_tokens is not None:
            payload["max_output_tokens"] = max_tokens

        if tools:
            payload["tools"] = tools

        raw = self._request_with_retry(payload)

        return ModelResponse(
            text=self._extract_output_text(raw),
            provider="openai",
            model=self.config.model,
            request_id=self._extract_request_id(raw),
            response_id=self._extract_response_id(raw),
            usage=self._extract_usage(raw),
            raw=raw,
            tool_calls=tuple(
                self._extract_openai_tool_calls(raw)
            ),
            assistant_message=None,
            thinking="",
        )

    # ========================================================
    # OPENAI JSON
    # ========================================================

    def _generate_openai_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        schema: dict[str, Any],
        max_tokens: int | None = None,
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "input": [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": system_prompt,
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_prompt,
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": str(
                        schema.get(
                            "name",
                            "awareon_response",
                        )
                    ),
                    "strict": True,
                    "schema": schema.get(
                        "schema",
                        {},
                    ),
                }
            },
        }

        if self.config.reasoning_effort:
            payload["reasoning"] = {
                "effort": self.config.reasoning_effort
            }

        if max_tokens is not None:
            payload["max_output_tokens"] = max_tokens

        raw = self._request_with_retry(payload)

        return ModelResponse(
            text=self._extract_output_text(raw),
            provider="openai",
            model=self.config.model,
            request_id=self._extract_request_id(raw),
            response_id=self._extract_response_id(raw),
            usage=self._extract_usage(raw),
            raw=raw,
        )

    # ========================================================
    # REQUEST RETRY
    # ========================================================

    def _request_with_retry(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        attempts = self.config.max_retries + 1
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                return self._request(payload)

            except ModelProviderError as exc:
                last_error = exc

                if not self._should_retry(exc):
                    raise

                if attempt >= attempts - 1:
                    break

                delay = (
                    self.config.retry_backoff_seconds
                    * (2 ** attempt)
                )

                if delay > 0:
                    time.sleep(delay)

        if last_error is not None:
            raise last_error

        raise ModelAdapterError(
            "Model request failed."
        )

    # ========================================================
    # HTTP
    # ========================================================

    def _request(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AwareOn/1.0",
        }

        if self.config.provider == "openai":
            api_key = os.getenv(
                self.config.api_key_env
            )

            if not api_key:
                raise ModelConfigurationError(
                    f"{self.config.api_key_env} "
                    "is not configured."
                )

            headers["Authorization"] = (
                f"Bearer {api_key}"
            )

        request = urllib.request.Request(
            self.config.base_url,
            data=json.dumps(
                payload
            ).encode(
                "utf-8"
            ),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
                raw = response.read().decode(
                    "utf-8"
                )

                request_id = (
                    response.headers.get(
                        "x-request-id"
                    )
                    or
                    response.headers.get(
                        "request-id"
                    )
                )

        except urllib.error.HTTPError as exc:
            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            request_id = None

            if exc.headers:
                request_id = exc.headers.get(
                    "x-request-id"
                )

            raise ModelProviderError(
                self._format_http_error(
                    exc.code,
                    body,
                    request_id,
                )
            ) from exc

        except urllib.error.URLError as exc:
            raise ModelProviderError(
                "Model provider connection failed: "
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise ModelProviderError(
                "Model provider request timed out."
            ) from exc

        except OSError as exc:
            raise ModelProviderError(
                f"Model provider network error: {exc}"
            ) from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ModelResponseError(
                "Model provider returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise ModelResponseError(
                "Model provider response must be a JSON object."
            )

        if request_id:
            data["_awareon_request_id"] = request_id

        return data

    # ========================================================
    # RETRY POLICY
    # ========================================================

    @staticmethod
    def _should_retry(
        error: ModelProviderError,
    ) -> bool:
        message = str(error).lower()

        permanent = (
            "401",
            "403",
            "404",
            "insufficient_quota",
            "credit_balance_exhausted",
            "invalid_api_key",
            "quota",
        )

        return not any(
            item in message
            for item in permanent
        )

    # ========================================================
    # OLLAMA TOOL CALLS
    # ========================================================

    @staticmethod
    def _extract_ollama_tool_calls(
        message: dict[str, Any],
    ) -> list[dict[str, Any]]:
        raw_calls = message.get(
            "tool_calls",
            [],
        )

        if not isinstance(raw_calls, list):
            return []

        result = []

        for index, call in enumerate(raw_calls):
            if not isinstance(call, dict):
                continue

            function = call.get(
                "function",
                {},
            )

            if not isinstance(function, dict):
                continue

            name = function.get(
                "name"
            )

            if not name:
                continue

            arguments = function.get(
                "arguments",
                {},
            )

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(
                        arguments
                    )
                except json.JSONDecodeError:
                    arguments = {
                        "_raw_arguments": arguments
                    }

            result.append(
                {
                    "id": call.get(
                        "id",
                        f"ollama_call_{index + 1}",
                    ),
                    "name": str(name),
                    "arguments": arguments,
                    "raw": call,
                }
            )

        return result

    # ========================================================
    # OPENAI TOOL CALLS
    # ========================================================

    @staticmethod
    def _extract_openai_tool_calls(
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        output = data.get(
            "output",
            [],
        )

        if not isinstance(output, list):
            return []

        result = []

        for item in output:
            if not isinstance(item, dict):
                continue

            if item.get("type") != "function_call":
                continue

            name = item.get("name")

            if not name:
                continue

            arguments = item.get(
                "arguments",
                {},
            )

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(
                        arguments
                    )
                except json.JSONDecodeError:
                    arguments = {
                        "_raw_arguments": arguments
                    }

            result.append(
                {
                    "id": (
                        item.get("call_id")
                        or item.get("id")
                    ),
                    "name": str(name),
                    "arguments": arguments,
                }
            )

        return result

    # ========================================================
    # OPENAI TEXT
    # ========================================================

    @staticmethod
    def _extract_output_text(
        data: dict[str, Any],
    ) -> str:
        output_text = data.get(
            "output_text"
        )

        if isinstance(
            output_text,
            str,
        ):
            return output_text.strip()

        output = data.get(
            "output",
            [],
        )

        if not isinstance(
            output,
            list,
        ):
            return ""

        parts: list[str] = []

        for item in output:
            if not isinstance(
                item,
                dict,
            ):
                continue

            content = item.get(
                "content"
            )

            if not isinstance(
                content,
                list,
            ):
                continue

            for part in content:
                if not isinstance(
                    part,
                    dict,
                ):
                    continue

                text = part.get(
                    "text"
                )

                if isinstance(
                    text,
                    str,
                ):
                    parts.append(text)

        return "".join(parts).strip()

    # ========================================================
    # USAGE
    # ========================================================

    @staticmethod
    def _extract_usage(
        data: dict[str, Any],
    ) -> dict[str, Any]:
        usage = data.get(
            "usage"
        )

        return (
            usage
            if isinstance(usage, dict)
            else {}
        )

    @staticmethod
    def _extract_ollama_usage(
        data: dict[str, Any],
    ) -> dict[str, Any]:
        keys = (
            "total_duration",
            "load_duration",
            "prompt_eval_count",
            "prompt_eval_duration",
            "eval_count",
            "eval_duration",
        )

        return {
            key: data[key]
            for key in keys
            if key in data
        }

    # ========================================================
    # IDS
    # ========================================================

    @staticmethod
    def _extract_request_id(
        data: dict[str, Any],
    ) -> str | None:
        value = data.get(
            "_awareon_request_id"
        )

        if isinstance(
            value,
            str,
        ):
            return value

        value = data.get(
            "request_id"
        )

        return (
            value
            if isinstance(value, str)
            else None
        )

    @staticmethod
    def _extract_response_id(
        data: dict[str, Any],
    ) -> str | None:
        value = data.get(
            "id"
        )

        return (
            value
            if isinstance(value, str)
            else None
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def _validate_configuration(
        self,
    ) -> None:
        if not self.config.model:
            raise ModelConfigurationError(
                "AWAREON_AI_MODEL is not configured."
            )

        if not self.config.base_url:
            raise ModelConfigurationError(
                "AWAREON_AI_BASE_URL is not configured."
            )

        if self.config.provider == "ollama":
            return

        if not self.config.api_key_env:
            raise ModelConfigurationError(
                "AWAREON_AI_API_KEY_ENV is not configured."
            )

        if not os.getenv(
            self.config.api_key_env
        ):
            raise ModelConfigurationError(
                f"{self.config.api_key_env} "
                "is not configured."
            )

    @staticmethod
    def _validate_schema(
        schema: dict[str, Any],
    ) -> None:
        if not isinstance(
            schema,
            dict,
        ):
            raise ValueError(
                "schema must be a dictionary."
            )

        if not isinstance(
            schema.get("schema"),
            dict,
        ):
            raise ValueError(
                "schema['schema'] must be a dictionary."
            )

    # ========================================================
    # ERROR FORMAT
    # ========================================================

    @staticmethod
    def _format_http_error(
        status_code: int,
        body: str,
        request_id: str | None,
    ) -> str:
        suffix = ""

        if request_id:
            suffix = (
                f" | request_id={request_id}"
            )

        return (
            f"AI provider HTTP {status_code}"
            f"{suffix}: {body[:2000]}"
        )


# ============================================================
# FACTORY
# ============================================================

def get_model_adapter() -> AwareOnModelAdapter:
    return AwareOnModelAdapter.from_environment()
