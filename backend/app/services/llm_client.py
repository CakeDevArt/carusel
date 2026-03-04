import json
import re
import logging

import httpx

from app.core.config import settings
from app.schemas.llm import LLMOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a carousel content generator. Given the source text and parameters, create engaging carousel slides.

Output ONLY valid JSON (no markdown, no extra text) matching this schema:
{
  "slides": [
    {"order": 1, "title": "Short title (max 40 chars)", "body": "Main text (max 320 chars)", "footer": "Optional footer (max 60 chars)"}
  ]
}

Rules:
- title: max 40 characters, catchy and concise
- body: max 320 characters, informative and engaging
- footer: max 60 characters, optional call-to-action or note
- First slide should be a hook/intro
- Last slide should be a call-to-action or summary
- Each slide should flow logically to the next
- Write in the specified language
- Match the style hint if provided"""


def _build_user_prompt(
    source_text: str,
    language: str,
    slides_count: int,
    style_hint: str | None,
) -> str:
    parts = [
        f"Create exactly {slides_count} carousel slides.",
        f"Language: {language}",
    ]
    if style_hint:
        parts.append(f"Style reference (match this tone/style): {style_hint}")
    parts.append(f"Source content:\n{source_text[:4000]}")
    return "\n\n".join(parts)


def _extract_json(raw: str) -> str:
    """Try to extract JSON from LLM response that may contain extra text."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        return match.group(0)
    return raw


async def generate_slides(
    source_text: str,
    language: str,
    slides_count: int,
    style_hint: str | None,
) -> tuple[LLMOutput, int]:
    """Call LLM and return parsed slides + tokens_used. Retries up to 2 times on invalid JSON."""
    is_mock = not settings.LLM_BASE_URL or settings.LLM_API_KEY in ("", "mock")

    if is_mock:
        return _mock_generate(language, slides_count), 0

    user_prompt = _build_user_prompt(source_text, language, slides_count, style_hint)
    last_error = None

    for attempt in range(3):
        try:
            result, tokens = await _call_llm(user_prompt)
            json_str = _extract_json(result)
            parsed = json.loads(json_str)
            output = LLMOutput.model_validate(parsed)

            if len(output.slides) != slides_count:
                logger.warning("LLM returned %d slides, expected %d", len(output.slides), slides_count)

            return output, tokens

        except (json.JSONDecodeError, Exception) as e:
            last_error = e
            logger.warning("LLM attempt %d failed: %s", attempt + 1, e)

    logger.error("All LLM attempts failed, using mock: %s", last_error)
    return _mock_generate(language, slides_count), 0


async def _call_llm(user_prompt: str) -> tuple[str, int]:
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_completion_tokens": 2000,
    }

    headers = {"Content-Type": "application/json"}
    if settings.LLM_API_KEY and settings.LLM_API_KEY not in ("not-needed", "mock", ""):
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens", 0)
    return content, tokens


def _mock_generate(language: str, slides_count: int) -> LLMOutput:
    if language == "ru":
        slides = []
        titles = [
            "Введение", "Проблема", "Решение", "Преимущества",
            "Как начать", "Примеры", "Результаты", "Советы",
            "Итоги", "Действуй!",
        ]
        bodies = [
            "Это первый слайд вашей карусели. Он привлечет внимание аудитории ярким заголовком.",
            "Здесь мы описываем главную проблему, которую решает ваш контент.",
            "Предлагаем конкретное решение для вашей аудитории.",
            "Перечисляем ключевые преимущества и выгоды.",
            "Пошаговая инструкция для начала работы.",
            "Реальные примеры успешного применения.",
            "Конкретные результаты и цифры.",
            "Полезные советы для вашей аудитории.",
            "Подводим итоги всего сказанного выше.",
            "Призыв к действию: подпишись, сохрани, поделись!",
        ]
        for i in range(slides_count):
            idx = i % len(titles)
            slides.append({
                "order": i + 1,
                "title": titles[idx],
                "body": bodies[idx],
                "footer": f"Слайд {i + 1} из {slides_count}",
            })
    else:
        slides = []
        titles = [
            "Introduction", "The Problem", "Our Solution", "Key Benefits",
            "Getting Started", "Examples", "Results", "Pro Tips",
            "Summary", "Take Action!",
        ]
        bodies = [
            "Welcome to this carousel! This first slide hooks your audience with a powerful opening.",
            "Here we describe the main problem your audience faces today.",
            "We offer a clear, actionable solution to the problem.",
            "Key benefits that make this solution stand out.",
            "Step-by-step guide to get started right away.",
            "Real-world examples of successful implementation.",
            "Concrete results and metrics that prove it works.",
            "Expert tips to help you maximize your results.",
            "A concise summary of everything covered above.",
            "Call to action: save this, share it, and start today!",
        ]
        for i in range(slides_count):
            idx = i % len(titles)
            slides.append({
                "order": i + 1,
                "title": titles[idx],
                "body": bodies[idx],
                "footer": f"Slide {i + 1} of {slides_count}",
            })

    return LLMOutput.model_validate({"slides": slides})
