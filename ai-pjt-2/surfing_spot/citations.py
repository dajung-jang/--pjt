"""답변 후처리와 인용 정리. (F2008)

LLM 이 "확인할 수 없다"는 문장에까지 [근거 N]을 붙이는 경우가 있다. 그런 번호는 근거 목록을 부풀리므로
문장 단위로 지운다. 실제 내용을 말하는 문장의 번호는 그대로 둔다.
"""
import re

CITE = re.compile(r"\s*\[근거\s*[\d,\s]+\]")
# 한 문장 = 끝 부호(. ! ?)까지 + 그 뒤에 붙은 [근거 N] 들. 마지막에 끝 부호가 없는 나머지도 한 문장으로 본다.
SENTENCE = re.compile(r".*?[.!?。](?:\s*\[근거[^\]]*\])*\s*|.+$")

# 이 표현이 들어간 문장은 '자료에 없다'는 말이다. 근거가 될 내용이 없으므로 번호를 지운다.
NOT_FOUND_MARKERS = (
    "확인할 수 없", "확인되지", "확인 불가", "확인이 어렵", "확인 할 수 없",
    "알 수 없", "알기 어렵", "포함되어 있지", "포함돼 있지", "나와 있지", "담겨 있지", "없습니다", "없어서",
)


def strip_empty_citations(answer: str) -> str:
    """'자료에 없다'고 말하는 문장에서 [근거 N] 표기를 지운다."""
    lines = []
    for line in answer.split("\n"):
        sentences = SENTENCE.findall(line)
        cleaned = [
            CITE.sub("", s) if any(marker in s for marker in NOT_FOUND_MARKERS) else s
            for s in sentences
        ]
        lines.append("".join(cleaned).rstrip())
    return "\n".join(lines)