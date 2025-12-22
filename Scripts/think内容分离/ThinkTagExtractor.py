import re
from typing import Optional, Tuple


class ThinkTagExtractor:
    """
    流式 <think>...</think> 标签提取器
    """
    def __init__(self, opening_tag: str = "<think>", closing_tag: str = "</think>"):
        self.opening_tag = opening_tag
        self.closing_tag = closing_tag
        self.buffer = ""
        self.is_inside_tag = False
        self.accumulated_thinking = ""

    def _find_potential_tag_start(self, text: str, tag: str) -> Optional[int]:
        # 先找完整匹配
        idx = text.find(tag)
        if idx != -1:
            return idx
        # 找部分匹配（标签可能被截断，如 "<thi" 和 "nk>" 分两次到达）
        for i in range(len(text) - 1, -1, -1):
            suffix = text[i:]
            if tag.startswith(suffix):
                return i
        return None

    def process(self, new_text: str) -> Tuple[str, str]:
        self.buffer += new_text
        text_to_render = ""
        thinking_content = ""

        while True:
            target_tag = self.closing_tag if self.is_inside_tag else self.opening_tag
            tag_pos = self._find_potential_tag_start(self.buffer, target_tag)

            if tag_pos is None:
                if self.is_inside_tag:
                    thinking_content += self.buffer
                else:
                    text_to_render += self.buffer
                self.buffer = ""
                break

            is_complete_tag = (tag_pos + len(target_tag) <= len(self.buffer))

            if is_complete_tag:
                before_tag = self.buffer[:tag_pos]
                if before_tag:
                    if self.is_inside_tag:
                        thinking_content += before_tag
                    else:
                        text_to_render += before_tag

                self.buffer = self.buffer[tag_pos + len(target_tag):]
                self.is_inside_tag = not self.is_inside_tag
            else:
                before_tag = self.buffer[:tag_pos]
                if before_tag:
                    if self.is_inside_tag:
                        thinking_content += before_tag
                    else:
                        text_to_render += before_tag
                self.buffer = self.buffer[tag_pos:]
                break

        if thinking_content:
            self.accumulated_thinking += thinking_content

        return text_to_render, thinking_content

    def finalize(self) -> str:
        remaining = self.accumulated_thinking
        if self.buffer and self.is_inside_tag:
            remaining += self.buffer
        return remaining

    def reset(self):
        self.buffer = ""
        self.is_inside_tag = False
        self.accumulated_thinking = ""
