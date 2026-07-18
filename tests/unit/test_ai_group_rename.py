import pytest
from biome_fm.presenters.ai_group_rename import group_rename, group_rename_prompt, parse_group_response


@pytest.mark.asyncio
async def test_group_rename_single_request():
    calls = []

    async def ai_call(prompt):
        calls.append(prompt)
        return "a.txt\nb.txt\nc.txt"

    await group_rename(["x.txt", "y.txt", "z.txt"], ai_call)
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_response_count_matches_files():
    async def ai_call(prompt):
        return "a.txt\nb.txt"  # only 2 lines for 3 files

    with pytest.raises(ValueError):
        await group_rename(["x.txt", "y.txt", "z.txt"], ai_call)


def test_prompt_contains_all_names():
    names = ["foo.mp4", "bar.mp4", "baz.mp4"]
    prompt = group_rename_prompt(names)
    for name in names:
        assert name in prompt


@pytest.mark.asyncio
async def test_empty_list_returns_empty():
    async def ai_call(prompt):
        raise AssertionError("should not be called")

    result = await group_rename([], ai_call)
    assert result == []
