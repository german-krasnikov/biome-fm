import pytest
from unittest.mock import AsyncMock
from biome_fm.presenters.ai_diff_summary import summarize_diff, diff_summary_prompt


@pytest.mark.asyncio
async def test_summarize_calls_ai():
    ai = AsyncMock(return_value="Summary text")
    await summarize_diff("some diff", ai)
    ai.assert_called_once()


@pytest.mark.asyncio
async def test_prompt_includes_diff():
    diff = "- old line\n+ new line"
    ai = AsyncMock(return_value="ok")
    await summarize_diff(diff, ai)
    prompt = ai.call_args[0][0]
    assert diff in prompt


@pytest.mark.asyncio
async def test_empty_diff_returns_message():
    ai = AsyncMock()
    result = await summarize_diff("   ", ai)
    assert result == "No changes to summarize."
    ai.assert_not_called()


@pytest.mark.asyncio
async def test_ai_error_returns_fallback():
    ai = AsyncMock(side_effect=RuntimeError("boom"))
    result = await summarize_diff("some diff", ai)
    assert result == "Could not generate summary."
