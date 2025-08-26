from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
from typing import List, Dict


def parse_transcript(content: str) -> List[Dict]:
    pattern = r'\[(\d{2}:\d{2}:\d{2})\]\s*(.*?)(?=\[\d{2}:\d{2}:\d{2}\]|$)'
    matches = re.findall(pattern, content, re.DOTALL)

    # Create segments with timestamps
    segments = []
    for i, (timestamp, text) in enumerate(matches):
        if i < len(matches) - 1:
            end_time = matches[i + 1][0]
        else:
            end_time = timestamp

        segments.append({
            "start_time": timestamp,
            "end_time": end_time,
            "text": text.strip()
        })

    return segments


def chunk_transcript_with_timestamps(segments: List[Dict], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[
    Dict]:
    """Chunk transcript with token-aware splitting while preserving timestamps"""

    # Use LangChain text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    # Create a single text with timestamp markers
    full_text = ""
    timestamp_map = []  # Maps character positions to timestamps

    for segment in segments:
        start_pos = len(full_text)
        full_text += segment["text"] + " "
        end_pos = len(full_text)

        # Map this text range to the segment's timestamps
        timestamp_map.append({
            "start_pos": start_pos,
            "end_pos": end_pos,
            "start_time": segment["start_time"],
            "end_time": segment["end_time"]
        })

    # Split the text
    chunks = text_splitter.split_text(full_text)

    # Map chunks back to timestamps
    chunked_segments = []
    current_pos = 0

    for chunk in chunks:
        chunk_end = current_pos + len(chunk)

        # Find which timestamp segments this chunk overlaps with
        overlapping_segments = []
        for ts_map in timestamp_map:
            if (current_pos < ts_map["end_pos"] and chunk_end > ts_map["start_pos"]):
                overlapping_segments.append(ts_map)

        if overlapping_segments:
            start_time = overlapping_segments[0]["start_time"]
            end_time = overlapping_segments[-1]["end_time"]
        else:
            # Fallback if no timestamps found
            start_time = "00:00:00"
            end_time = "00:00:00"

        chunked_segments.append({
            "start_time": start_time,
            "end_time": end_time,
            "text": chunk.strip()
        })

        current_pos = chunk_end

    return chunked_segments