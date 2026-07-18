from collections.abc import Callable


def diff_summary_prompt(diff: str) -> str:
    return f"Summarize these changes in 3 sentences:\n\n{diff[:4000]}"


async def summarize_diff(diff: str, ai_call: Callable) -> str:
    if not diff.strip():
        return "No changes to summarize."
    try:
        return await ai_call(diff_summary_prompt(diff))
    except Exception:
        return "Could not generate summary."
