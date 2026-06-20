"""药品说明书文本切片。

将完整的药品说明书按语义段落切分成小块，
每块保留足够上下文（200-500 字），相邻块重叠以保证检索连贯性。
"""
import re


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) <= chunk_size:
            chunks.append(para)
            continue

        sentences = re.split(r"(?<=[。！？；\.\!\?\;])", para)
        current = ""
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if len(current) + len(sent) <= chunk_size:
                current += sent
            else:
                if current:
                    chunks.append(current)
                if len(current) > overlap:
                    current = current[-overlap:] + sent
                else:
                    current = sent
        if current:
            chunks.append(current)

    return chunks


def chunk_document(
    filepath: str,
    drug_name_cn: str,
    drug_name_en: str = "",
    aliases: list[str] | None = None,
) -> list[dict]:
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text)
    meta = {
        "name_cn": drug_name_cn,
        "name_en": drug_name_en,
        "aliases": aliases or [],
        "source": filepath,
    }
    return [{"text": c, "meta": meta, "chunk_index": i} for i, c in enumerate(chunks)]
