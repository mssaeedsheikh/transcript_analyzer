import re
from typing import List


def parse_transcript(content: str) -> List[dict]:
    pattern = r'\[(\d{2}:\d{2}:\d{2})\]\s*(.*?)(?=\[\d{2}:\d{2}:\d{2}\]|$)'
    matches = re.findall(pattern, content, re.DOTALL)

    chunks = []
    for i, (timestamp, text) in enumerate(matches):
        if i < len(matches) - 1:
            end_time = matches[i + 1][0]
        else:
            end_time = timestamp  # Fallback if no next timestamp

        chunks.append({
            "start_time": timestamp,
            "end_time": end_time,
            "text": text.strip()
        })

    return chunks