"""
Anthropic Provider

LLM provider implementation for Anthropic Claude API.
"""

import logging
import re
from collections.abc import AsyncIterator, Iterator
from typing import Any

from cdr.core.exceptions import LLMError, LLMProviderError, LLMRateLimitError
from cdr.llm.base import BaseLLMProvider, LLMResponse, Message, StreamChunk

try:
    import anthropic
    from anthropic import Anthropic, AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


logger = logging.getLogger(__name__)
_MODEL_VERSION = re.compile(r"^claude-(?:[a-z]+-)?(?P<major>\d+)(?:-(?P<minor>\d{1,2}))?(?:-|$)")
_SAMPLING_PARAMETERS = ("temperature", "top_p", "top_k")
_MIN_THINKING_OUTPUT_TOKENS = 4096


def _is_default_sampling_value(parameter: str, value: Any) -> bool:
    """Return whether a sampling value is accepted as default by current Claude models."""
    if parameter == "temperature":
        return bool(value == 1.0)
    if parameter == "top_p":
        return bool(value == 1.0)
    return False


def _effective_max_tokens(model: str, max_tokens: int | None) -> int:
    """Keep enough output budget for Claude 5+ models that think by default."""
    requested = max_tokens or 4096
    match = _MODEL_VERSION.match(model)
    if match is None:
        return requested

    version = (int(match.group("major")), int(match.group("minor") or 0))
    if model.startswith("claude-") and version >= (5, 0):
        return max(requested, _MIN_THINKING_OUTPUT_TOKENS)
    return requested


def _handle_stop_reason(model: str, stop_reason: str | None) -> None:
    """Surface refusals and warn when Anthropic truncates output at its token limit."""
    if stop_reason == "refusal":
        raise LLMError(f"Anthropic model {model} refused the request")
    if stop_reason == "max_tokens":
        logger.warning(
            "Anthropic model %s stopped at max_tokens; the response may be truncated.", model
        )


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude API provider.

    Supports:
        - Claude Messages API models, including current Claude Sonnet
        - Streaming responses
        - Extended context (up to 200K tokens)
    """

    def __init__(
        self,
        model: str = "claude-sonnet-5-5",
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize Anthropic provider.

        Args:
            model: Model name (claude-sonnet-5-5, etc.).
            api_key: Anthropic API key.
            base_url: Custom base URL.
            timeout: Request timeout.
            max_retries: Maximum retries.
        """
        if not ANTHROPIC_AVAILABLE:
            raise LLMProviderError(
                provider="anthropic",
                message="Anthropic package not installed. Run: pip install anthropic",
            )

        super().__init__(model, api_key, base_url, timeout, max_retries)
        self._warned_unsupported_sampling_parameters: set[str] = set()

        # Initialize clients
        client_kwargs: dict[str, Any] = {
            "timeout": timeout,
            "max_retries": max_retries,
        }
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = Anthropic(**client_kwargs)
        self._async_client = AsyncAnthropic(**client_kwargs)

    @property
    def name(self) -> str:
        return "anthropic"

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict[str, str]]]:
        """
        Convert messages to Anthropic format.

        Anthropic uses separate system parameter.

        Returns:
            Tuple of (system_prompt, messages).
        """
        system_prompt: str | None = None
        converted: list[dict[str, str]] = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                converted.append({"role": msg.role, "content": msg.content})

        return system_prompt, converted

    @staticmethod
    def _model_supports_sampling_parameters(model: str) -> bool:
        """Claude 4.7+ removed non-default sampling controls; custom APIs may differ."""
        if not model.startswith("claude-"):
            return True

        match = _MODEL_VERSION.match(model)
        if match is None:
            # Preserve caller-specified sampling for custom or newly named models.
            return True

        version = (int(match.group("major")), int(match.group("minor") or 0))
        return version < (4, 7)

    def _request_options(self, temperature: float, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Route sampling parameters through SDK 1.x extra_body only when the model accepts them."""
        request_options = dict(kwargs)
        extra_body = dict(request_options.pop("extra_body", {}) or {})
        sampling_options: dict[str, Any] = {"temperature": temperature}

        for parameter in ("top_p", "top_k"):
            if parameter in request_options:
                sampling_options[parameter] = request_options.pop(parameter)

        # The SDK documents extra_body as taking precedence over normal request options.
        for parameter in _SAMPLING_PARAMETERS:
            if parameter in extra_body:
                sampling_options[parameter] = extra_body.pop(parameter)

        if self._model_supports_sampling_parameters(self._model):
            extra_body.update(sampling_options)
        else:
            unsupported_options: dict[str, Any] = {}
            for parameter, value in sampling_options.items():
                if value is None or _is_default_sampling_value(parameter, value):
                    continue
                if parameter not in self._warned_unsupported_sampling_parameters:
                    unsupported_options[parameter] = value
                    self._warned_unsupported_sampling_parameters.add(parameter)
            if unsupported_options:
                formatted_options = ", ".join(
                    f"{parameter}={value!r}" for parameter, value in unsupported_options.items()
                )
                logger.warning(
                    "Anthropic model %s ignores non-default sampling parameters (%s); "
                    "omitting them. Sampling controls have no direct mapping to "
                    "output_config.effort.",
                    self._model,
                    formatted_options,
                )

        if extra_body:
            request_options["extra_body"] = extra_body
        return request_options

    def complete(
        self,
        messages: list[Message],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Synchronous completion."""
        # Normalize messages to handle both Message objects and dicts
        normalized = self._normalize_messages(messages)
        system_prompt, converted_messages = self._convert_messages(normalized)

        try:
            call_kwargs: dict[str, Any] = {
                "model": self._model,
                "messages": converted_messages,
                "max_tokens": _effective_max_tokens(self._model, max_tokens),
            }
            if system_prompt:
                call_kwargs["system"] = system_prompt
            call_kwargs.update(self._request_options(temperature, kwargs))

            response = self._client.messages.create(**call_kwargs)
            _handle_stop_reason(self._model, response.stop_reason)

            # Extract text from content blocks
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.name,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                finish_reason=response.stop_reason,
                raw_response=response,
            )

        except anthropic.RateLimitError as e:
            raise LLMRateLimitError(
                provider=self.name,
                retry_after=60.0,  # Anthropic doesn't always provide retry-after
            ) from e

        except anthropic.APIError as e:
            raise LLMProviderError(provider=self.name, message=str(e)) from e

        except LLMError:
            raise

        except Exception as e:
            raise LLMError(f"Anthropic error: {e}") from e

    async def acomplete(
        self,
        messages: list[Message],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Async completion."""
        # Normalize messages to handle both Message objects and dicts
        normalized = self._normalize_messages(messages)
        system_prompt, converted_messages = self._convert_messages(normalized)

        try:
            call_kwargs: dict[str, Any] = {
                "model": self._model,
                "messages": converted_messages,
                "max_tokens": _effective_max_tokens(self._model, max_tokens),
            }
            if system_prompt:
                call_kwargs["system"] = system_prompt
            call_kwargs.update(self._request_options(temperature, kwargs))

            response = await self._async_client.messages.create(**call_kwargs)
            _handle_stop_reason(self._model, response.stop_reason)

            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.name,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                finish_reason=response.stop_reason,
                raw_response=response,
            )

        except anthropic.RateLimitError as e:
            raise LLMRateLimitError(provider=self.name, retry_after=60.0) from e

        except anthropic.APIError as e:
            raise LLMProviderError(provider=self.name, message=str(e)) from e

        except LLMError:
            raise

        except Exception as e:
            raise LLMError(f"Anthropic async error: {e}") from e

    def stream(
        self,
        messages: list[Message],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        """Streaming completion."""
        system_prompt, converted_messages = self._convert_messages(messages)

        try:
            call_kwargs: dict[str, Any] = {
                "model": self._model,
                "messages": converted_messages,
                "max_tokens": _effective_max_tokens(self._model, max_tokens),
            }
            if system_prompt:
                call_kwargs["system"] = system_prompt
            call_kwargs.update(self._request_options(temperature, kwargs))

            with self._client.messages.stream(**call_kwargs) as stream:
                for text in stream.text_stream:
                    yield StreamChunk(content=text, is_final=False)

                response = stream.get_final_message()
                _handle_stop_reason(self._model, response.stop_reason)

                # Final chunk
                yield StreamChunk(content="", is_final=True)

        except LLMError:
            raise

        except Exception as e:
            raise LLMError(f"Anthropic streaming error: {e}") from e

    async def astream(
        self,
        messages: list[Message],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Async streaming completion."""
        system_prompt, converted_messages = self._convert_messages(messages)

        try:
            call_kwargs: dict[str, Any] = {
                "model": self._model,
                "messages": converted_messages,
                "max_tokens": _effective_max_tokens(self._model, max_tokens),
            }
            if system_prompt:
                call_kwargs["system"] = system_prompt
            call_kwargs.update(self._request_options(temperature, kwargs))

            async with self._async_client.messages.stream(**call_kwargs) as stream:
                async for text in stream.text_stream:
                    yield StreamChunk(content=text, is_final=False)

                response = await stream.get_final_message()
                _handle_stop_reason(self._model, response.stop_reason)

                yield StreamChunk(content="", is_final=True)

        except LLMError:
            raise

        except Exception as e:
            raise LLMError(f"Anthropic async streaming error: {e}") from e
