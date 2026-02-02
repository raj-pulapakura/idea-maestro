import re
from typing import Optional

def get_sub_agent_marker(sub_agent_name: str) -> str:
    return f"==* by: {sub_agent_name} *=="


def find_sub_agent_marker(text: str) -> Optional[str]:
    match = re.search(r"==\* by: (\w+) \*\==", text)
    return match.group(1) if match else None


def remove_sub_agent_marker(text: str) -> str:
    return re.sub(r"==\* by: (\w+) \*\==", "", text)