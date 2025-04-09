import re


def remove_think_block(text: str) -> str:
    # 1) <think>~</think> 구간 통째로 제거 (DOTALL 플래그로 개행 포함)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # 2) 연속된 빈 줄(\n + 공백 + \n)을 한 줄로 정리
    text = re.sub(r"\n\s*\n", "\n", text)

    # 3) 맨 앞뒤 불필요한 공백 및 개행 제거
    text = text.strip()

    return text
