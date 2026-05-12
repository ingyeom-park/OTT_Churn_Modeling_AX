from __future__ import annotations

import os
import re
import zlib
from pathlib import Path


PDF_DIR = Path(r"C:\Users\user\Downloads")
OUTPUT_TXT = Path(r"C:\myCode\ott-churn-prediction\.tmp\pdf_extracted_text.txt")


def load_pdf_bytes() -> bytes:
    pdf_name = next(
        name
        for name in os.listdir(PDF_DIR)
        if name.lower().endswith(".pdf") and "v3" in name.lower()
    )
    return (PDF_DIR / pdf_name).read_bytes()


def get_object_bytes(pdf_bytes: bytes, obj_no: int) -> bytes:
    pattern = rb"(?m)^%d\s+0\s+obj\s*(.*?)\s*endobj" % obj_no
    match = re.search(pattern, pdf_bytes, re.S)
    if not match:
        raise KeyError(f"object not found: {obj_no}")
    return match.group(1)


def get_stream_bytes(obj_bytes: bytes) -> bytes:
    match = re.search(rb"(.*?)stream\r?\n(.*?)\r?\nendstream", obj_bytes, re.S)
    if not match:
        raise ValueError("stream not found")
    return zlib.decompress(match.group(2))


def parse_pages_root(pdf_bytes: bytes) -> list[int]:
    obj1 = get_object_bytes(pdf_bytes, 1).decode("latin1", errors="ignore")
    kids_match = re.search(r"/Kids\s*\[(.*?)\]\s*/Count", obj1, re.S)
    if not kids_match:
        raise ValueError("page kids not found")
    kids = re.findall(r"(\d+)\s+0\s+R", kids_match.group(1))
    return [int(kid) for kid in kids]


def parse_page_refs(pdf_bytes: bytes, page_obj_no: int) -> tuple[int, int]:
    page_text = get_object_bytes(pdf_bytes, page_obj_no).decode(
        "latin1",
        errors="ignore",
    )
    content_match = re.search(r"/Contents\s+(\d+)\s+0\s+R", page_text)
    resource_match = re.search(r"/Resources\s+(\d+)\s+0\s+R", page_text)
    if not content_match or not resource_match:
        raise ValueError(f"page refs missing: {page_obj_no}")
    return int(content_match.group(1)), int(resource_match.group(1))


def parse_resource_fonts(pdf_bytes: bytes, resource_obj_no: int) -> dict[str, int]:
    resource_text = get_object_bytes(pdf_bytes, resource_obj_no).decode(
        "latin1",
        errors="ignore",
    )
    font_block = re.search(r"/Font\s*<<(.+?)>>", resource_text, re.S)
    if not font_block:
        return {}
    font_refs = re.findall(r"/(Font\d+)\s+(\d+)\s+0\s+R", font_block.group(1))
    return {font_name: int(obj_no) for font_name, obj_no in font_refs}


def parse_cmap(pdf_bytes: bytes, font_obj_no: int) -> dict[int, str]:
    font_text = get_object_bytes(pdf_bytes, font_obj_no).decode(
        "latin1",
        errors="ignore",
    )
    to_unicode_match = re.search(r"/ToUnicode\s+(\d+)\s+0\s+R", font_text)
    if not to_unicode_match:
        return {}
    cmap_obj_no = int(to_unicode_match.group(1))
    cmap_text = get_stream_bytes(get_object_bytes(pdf_bytes, cmap_obj_no)).decode(
        "latin1",
        errors="ignore",
    )

    mapping: dict[int, str] = {}
    for match in re.finditer(
        r"(\d+)\s+beginbfchar(.*?)endbfchar",
        cmap_text,
        re.S,
    ):
        for src_hex, dst_hex in re.findall(r"<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>", match.group(2)):
            src = int(src_hex, 16)
            mapping[src] = bytes.fromhex(dst_hex).decode("utf-16-be", errors="ignore")

    for match in re.finditer(
        r"(\d+)\s+beginbfrange(.*?)endbfrange",
        cmap_text,
        re.S,
    ):
        for src_start, src_end, dst_start in re.findall(
            r"<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>",
            match.group(2),
        ):
            start = int(src_start, 16)
            end = int(src_end, 16)
            base = int(dst_start, 16)
            for offset, src in enumerate(range(start, end + 1)):
                dst = base + offset
                mapping[src] = dst.to_bytes(2, "big").decode("utf-16-be", errors="ignore")
    return mapping


def parse_literal_string(data: bytes, start_idx: int) -> tuple[bytes, int]:
    result = bytearray()
    depth = 1
    idx = start_idx + 1

    while idx < len(data) and depth > 0:
        byte = data[idx]
        if byte == 0x5C:
            idx += 1
            if idx >= len(data):
                break
            esc = data[idx]
            if esc in b"nrtbf":
                mapping = {
                    ord("n"): b"\n",
                    ord("r"): b"\r",
                    ord("t"): b"\t",
                    ord("b"): b"\b",
                    ord("f"): b"\f",
                }
                result.extend(mapping.get(esc, bytes([esc])))
            elif esc in b"()\\":
                result.append(esc)
            elif 48 <= esc <= 55:
                oct_digits = bytes([esc])
                for _ in range(2):
                    if idx + 1 < len(data) and 48 <= data[idx + 1] <= 55:
                        idx += 1
                        oct_digits += bytes([data[idx]])
                    else:
                        break
                result.append(int(oct_digits, 8))
            else:
                result.append(esc)
        elif byte == 0x28:
            depth += 1
            result.append(byte)
        elif byte == 0x29:
            depth -= 1
            if depth > 0:
                result.append(byte)
        else:
            result.append(byte)
        idx += 1

    return bytes(result), idx


def skip_ws(data: bytes, idx: int) -> int:
    while idx < len(data) and data[idx] in b" \t\r\n\x0c\x00":
        idx += 1
    return idx


def parse_simple_token(data: bytes, idx: int) -> tuple[str, int]:
    end = idx
    while end < len(data) and data[end] not in b" \t\r\n\x0c\x00[]()<>/":
        end += 1
    return data[idx:end].decode("latin1", errors="ignore"), end


def parse_name_token(data: bytes, idx: int) -> tuple[str, int]:
    end = idx + 1
    while end < len(data) and data[end] not in b" \t\r\n\x0c\x00[]()<>/":
        end += 1
    return data[idx + 1:end].decode("latin1", errors="ignore"), end


def parse_array(data: bytes, idx: int) -> tuple[list[object], int]:
    items: list[object] = []
    idx += 1
    while idx < len(data):
        idx = skip_ws(data, idx)
        if idx >= len(data):
            break
        if data[idx] == 0x5D:
            return items, idx + 1
        token, idx = parse_token(data, idx)
        items.append(token)
    return items, idx


def parse_token(data: bytes, idx: int) -> tuple[object, int]:
    idx = skip_ws(data, idx)
    if idx >= len(data):
        return "", idx
    byte = data[idx]

    if byte == 0x28:
        return parse_literal_string(data, idx)
    if byte == 0x5B:
        return parse_array(data, idx)
    if byte == 0x2F:
        return parse_name_token(data, idx)
    return parse_simple_token(data, idx)


def decode_pdf_text(raw_bytes: bytes, cmap: dict[int, str]) -> str:
    if not raw_bytes:
        return ""
    if not cmap:
        return raw_bytes.decode("latin1", errors="ignore")

    chars: list[str] = []
    for idx in range(0, len(raw_bytes), 2):
        pair = raw_bytes[idx:idx + 2]
        if len(pair) < 2:
            continue
        code = int.from_bytes(pair, "big")
        chars.append(cmap.get(code, ""))
    return "".join(chars)


def extract_page_text_items(
    pdf_bytes: bytes,
    page_obj_no: int,
) -> list[tuple[float, float, str]]:
    content_obj_no, resource_obj_no = parse_page_refs(pdf_bytes, page_obj_no)
    content_bytes = get_stream_bytes(get_object_bytes(pdf_bytes, content_obj_no))
    font_refs = parse_resource_fonts(pdf_bytes, resource_obj_no)
    cmap_by_font = {
        font_name: parse_cmap(pdf_bytes, font_obj_no)
        for font_name, font_obj_no in font_refs.items()
    }

    items: list[tuple[float, float, str]] = []
    operands: list[object] = []
    current_font = ""
    current_x = 0.0
    current_y = 0.0

    idx = 0
    while idx < len(content_bytes):
        token, idx = parse_token(content_bytes, idx)
        if token == "":
            break

        if isinstance(token, str) and token in {"BT", "ET"}:
            operands = []
            continue

        if isinstance(token, str) and token == "Tf":
            if len(operands) >= 2:
                font_name = operands[-2]
                current_font = str(font_name)
            operands = []
            continue

        if isinstance(token, str) and token == "Tm":
            if len(operands) >= 6:
                current_x = float(operands[-2])
                current_y = float(operands[-1])
            operands = []
            continue

        if isinstance(token, str) and token == "Td":
            if len(operands) >= 2:
                current_x += float(operands[-2])
                current_y += float(operands[-1])
            operands = []
            continue

        if isinstance(token, str) and token == "Tj":
            if operands:
                raw = operands[-1]
                if isinstance(raw, bytes):
                    text = decode_pdf_text(raw, cmap_by_font.get(current_font, {}))
                    if text.strip():
                        items.append((current_x, current_y, text))
            operands = []
            continue

        if isinstance(token, str) and token == "TJ":
            if operands:
                arr = operands[-1]
                if isinstance(arr, list):
                    text_parts = []
                    for arr_item in arr:
                        if isinstance(arr_item, bytes):
                            text_parts.append(
                                decode_pdf_text(
                                    arr_item,
                                    cmap_by_font.get(current_font, {}),
                                )
                            )
                    text = "".join(text_parts)
                    if text.strip():
                        items.append((current_x, current_y, text))
            operands = []
            continue

        if isinstance(token, str) and token in {
            "Tr",
            "rg",
            "RG",
            "w",
            "J",
            "j",
            "M",
            "d",
            "gs",
            "cm",
            "m",
            "l",
            "h",
            "W",
            "n",
            "f",
            "S",
            "Q",
            "q",
        }:
            operands = []
            continue

        operands.append(token)

    return items


def main() -> None:
    pdf_bytes = load_pdf_bytes()
    page_objs = parse_pages_root(pdf_bytes)

    lines: list[str] = []
    for page_index, page_obj_no in enumerate(page_objs, start=1):
        items = extract_page_text_items(pdf_bytes, page_obj_no)
        grouped: dict[int, list[tuple[float, str]]] = {}
        for x, y, text in items:
            key = int(round(y))
            grouped.setdefault(key, []).append((x, text))

        lines.append(f"=== PAGE {page_index} / OBJ {page_obj_no} ===")
        for y_key in sorted(grouped.keys(), reverse=True):
            row_items = sorted(grouped[y_key], key=lambda item: item[0])
            row_text = " ".join(text for _, text in row_items)
            lines.append(f"{y_key:>4} | {row_text}")
        lines.append("")

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8-sig")
    print(OUTPUT_TXT)


if __name__ == "__main__":
    main()
