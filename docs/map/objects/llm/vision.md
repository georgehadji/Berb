---
type: object
cluster: llm
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/llm/vision.py
---

# Vision (image input)

Provider-neutral image parts: `image_message(text, [paths])` builds a multimodal message (`vision.py:128`); each client encodes it for its wire format. Only inline base64 images are supported.

## Why this shape

One neutral part list (`ImagePart`, `vision.py:75`) so callers never know the wire format. Encoders: `to_openai_content` (chat completions `image_url`), `to_responses_content` (Responses API `input_image`), `to_anthropic_content` (base64 `source`) (`vision.py:246-285`). A text-only message passes through unchanged, so encoding is safe to apply unconditionally (`client.py:899-903`).

## Shape

- `model_supports_vision(model)` reads `supports_vision` from `OPENROUTER_MODELS` in `openrouter_models_data.py`; returns True/False or `None` when uncatalogued (`vision.py:189-216`). It is the first and only reader of that flag.
- `ensure_vision_capable` raises `VisionUnsupportedError` only for catalogued text-only models; uncatalogued models fail open (`vision.py:219-238`).
- Gate placed in `LLMClient.chat` before the call (`client.py:672`, `681-682`).
- Live consumer: `experiment/plot_verdict.py:491-502` (`VLMPlotCritic`), used from `pipeline/stage_impls/_execution.py:490` when a vision model is configured.
- Remote image URLs are out of scope by design.

## Connected to

- **owns:** neutral part format and capability gate.
- **joins:** [[llm-client]], `llm/openrouter_models_data.py` (4430 lines, generated; refresh with `scripts/refresh_openrouter_models.py --diff`, do not hand-edit), `llm/anthropic_adapter.py`.
- **looks-like-but-is-not:** `agents/figure_agent` and `literature/multimodal_search.py` (parked), which do not use this path.

## If you change this

- **Hits:** `plot_verdict.py`; `tests/test_llm_vision.py`, `tests/test_llm_vision_wiring.py`; the four re-exported names in `llm/__init__.py:17-21`.
- **Hits:** adding a wire format needs a new encoder AND a client branch; `responses` uses its own path (`_messages_to_responses_input`).
- **Does not hit:** text-only calls.

## Surfaces

| Surface | Role |
|---|---|
| `plot_verdict.VLMPlotCritic` | only in-repo caller |
| public `berb.llm` API | `ImagePart`, `VisionUnsupportedError`, `encode_image`, `image_message`, `model_supports_vision` |

## See

- Source: `berb/llm/vision.py`
