"""Exercise Anthropic SDK requests against a local HTTP API."""

import asyncio
import json
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any

import pytest

from cdr.config import LLMSettings
from cdr.llm.anthropic_provider import AnthropicProvider
from cdr.llm.base import Message

CURRENT_CLAUDE_MODEL = "claude-sonnet-5"


class _RecordingHTTPServer(ThreadingHTTPServer):
    requests: list[dict[str, Any]]

    def __init__(self, server_address: tuple[str, int], handler: type[BaseHTTPRequestHandler]):
        self.requests = []
        super().__init__(server_address, handler)


@pytest.fixture
def fake_anthropic_api() -> Iterator[tuple[str, list[dict[str, Any]]]]:
    """Run a loopback-only HTTP server that returns Anthropic Messages responses."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.server.requests.append(body)  # type: ignore[attr-defined]

            if body.get("stream"):
                self._write_stream()
            else:
                response = _message_response(body["model"])
                encoded = json.dumps(response).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        def _write_stream(self) -> None:
            response = _message_response(CURRENT_CLAUDE_MODEL)
            response["content"] = []
            response["usage"]["output_tokens"] = 0
            events = [
                ("message_start", {"type": "message_start", "message": response}),
                (
                    "content_block_start",
                    {
                        "type": "content_block_start",
                        "index": 0,
                        "content_block": {"type": "text", "text": ""},
                    },
                ),
                (
                    "content_block_delta",
                    {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "text_delta", "text": "fake streamed response"},
                    },
                ),
                ("content_block_stop", {"type": "content_block_stop", "index": 0}),
                (
                    "message_delta",
                    {
                        "type": "message_delta",
                        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                        "usage": {"output_tokens": 3},
                    },
                ),
                ("message_stop", {"type": "message_stop"}),
            ]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            for event, data in events:
                chunk = f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()
                self.wfile.write(chunk)
                self.wfile.flush()

        def log_message(self, format: str, *args: Any) -> None:
            del format, args

    server = _RecordingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", server.requests
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def _message_response(model: str) -> dict[str, Any]:
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": "fake response"}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 3, "output_tokens": 2},
    }


def _provider(base_url: str, model: str | None = None) -> AnthropicProvider:
    if model is None:
        return AnthropicProvider(api_key="test-key", base_url=base_url, max_retries=0)
    return AnthropicProvider(model=model, api_key="test-key", base_url=base_url, max_retries=0)


def _messages() -> list[Message]:
    return [Message(role="user", content="hello")]


def test_current_anthropic_model_is_configured_as_default():
    assert LLMSettings.model_fields["anthropic_model"].default == CURRENT_CLAUDE_MODEL


def test_complete_uses_sdk_1_against_fake_http_server(fake_anthropic_api):
    base_url, requests = fake_anthropic_api

    response = _provider(base_url).complete(_messages())

    assert response.content == "fake response"
    assert requests[0]["model"] == CURRENT_CLAUDE_MODEL
    assert "temperature" not in requests[0]


def test_acomplete_uses_sdk_1_against_fake_http_server(fake_anthropic_api):
    base_url, requests = fake_anthropic_api

    response = asyncio.run(_provider(base_url).acomplete(_messages()))

    assert response.content == "fake response"
    assert requests[0]["model"] == CURRENT_CLAUDE_MODEL
    assert "temperature" not in requests[0]


def test_stream_uses_sdk_1_against_fake_http_server(fake_anthropic_api):
    base_url, requests = fake_anthropic_api

    chunks = list(_provider(base_url).stream(_messages()))

    assert "".join(chunk.content for chunk in chunks) == "fake streamed response"
    assert chunks[-1].is_final
    assert requests[0]["model"] == CURRENT_CLAUDE_MODEL
    assert requests[0]["stream"] is True
    assert "temperature" not in requests[0]


def test_astream_uses_sdk_1_against_fake_http_server(fake_anthropic_api):
    base_url, requests = fake_anthropic_api

    async def collect_chunks():
        return [chunk async for chunk in _provider(base_url).astream(_messages())]

    chunks = asyncio.run(collect_chunks())

    assert "".join(chunk.content for chunk in chunks) == "fake streamed response"
    assert chunks[-1].is_final
    assert requests[0]["model"] == CURRENT_CLAUDE_MODEL
    assert requests[0]["stream"] is True
    assert "temperature" not in requests[0]


def test_legacy_model_sampling_options_use_extra_body(fake_anthropic_api):
    base_url, requests = fake_anthropic_api

    _provider(base_url, model="claude-sonnet-4-6").complete(
        _messages(), temperature=0.2, top_p=0.8, top_k=20
    )

    assert requests[0]["temperature"] == 0.2
    assert requests[0]["top_p"] == 0.8
    assert requests[0]["top_k"] == 20


def test_new_model_omits_accepted_compatibility_sampling_values_without_warning(
    fake_anthropic_api, caplog
):
    base_url, requests = fake_anthropic_api
    provider = _provider(base_url)

    provider.complete(_messages(), temperature=1.0, top_p=1.0)
    provider.complete(_messages(), temperature=1.0, top_p=1.0)

    assert len(requests) == 2
    assert all(not {"temperature", "top_p", "top_k"}.intersection(body) for body in requests)
    assert not [record for record in caplog.records if "ignores non-default" in record.message]


def test_new_model_warns_once_and_omits_unsupported_sampling_options(fake_anthropic_api, caplog):
    base_url, requests = fake_anthropic_api
    provider = _provider(base_url)

    provider.complete(_messages(), top_p=0.6, top_k=20)
    provider.complete(_messages(), top_p=0.6, top_k=20)

    assert len(requests) == 2
    assert all(not {"temperature", "top_p", "top_k"}.intersection(body) for body in requests)
    warnings = [record for record in caplog.records if "ignores non-default" in record.message]
    assert len(warnings) == 1
    assert all(parameter in warnings[0].message for parameter in ("temperature", "top_p", "top_k"))


def test_new_model_warns_for_top_p_slightly_below_default(fake_anthropic_api, caplog):
    base_url, requests = fake_anthropic_api

    _provider(base_url).complete(_messages(), temperature=1.0, top_p=0.995)

    assert len(requests) == 1
    assert "top_p" not in requests[0]
    warnings = [
        record.message for record in caplog.records if "ignores non-default" in record.message
    ]
    assert len(warnings) == 1
    assert "top_p=0.995" in warnings[0]
