from collections.abc import Callable


def group_rename_prompt(names: list[str]) -> str:
    return f"Rename these files coherently. Return exactly {len(names)} names, one per line:\n" + "\n".join(names)


def parse_group_response(response: str, expected_count: int) -> list[str]:
    lines = [l.strip() for l in response.strip().splitlines() if l.strip()]
    if len(lines) != expected_count:
        raise ValueError(f"Expected {expected_count} names, got {len(lines)}")
    return lines


async def group_rename(names: list[str], ai_call: Callable) -> list[str]:
    if not names:
        return []
    response = await ai_call(group_rename_prompt(names))
    return parse_group_response(response, len(names))
