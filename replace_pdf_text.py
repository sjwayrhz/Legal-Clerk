#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
import glob
import tempfile

try:
    import fitz  # PyMuPDF
except ImportError:
    print("未找到 PyMuPDF，请先安装：pip install pymupdf --break-system-packages")
    sys.exit(1)


# 需要替换的字符串：(旧, 新)
REPLACEMENTS = [
    ("顾小翔", "周晓林"),
    ("372328197010050096", "370784198402038219"),
    ("17638192436", "18913125617"),
]


def normalize(s: str) -> str:
    """去掉空格、连字符并转小写，便于模糊匹配字体名称"""
    return s.lower().replace(" ", "").replace("-", "")


_ink_cache = {}


def font_covers_text(fontfile: str, text: str) -> bool:
    """
    检查用该字体文件绘制 text 中的每一个字符时，是否都能真正画出墨迹。

    仅用 has_glyph() 是不够的：不少 PDF 里的中文字体是"子集字体"，
    部分子集在生成时会保留 cmap 映射表项，但把对应字形的轮廓数据清空，
    导致 has_glyph() 仍返回"存在"，实际画出来却是完全空白。
    这里改为直接实际绘制每个字符并检查像素，从根本上避免这个问题。
    """
    for ch in set(text):
        if ch.isspace():
            continue
        key = (fontfile, ch)
        if key in _ink_cache:
            if not _ink_cache[key]:
                return False
            continue
        has_ink = False
        try:
            tmp_doc = fitz.open()
            tmp_page = tmp_doc.new_page(width=100, height=100)
            tmp_page.insert_text((10, 60), ch, fontname="ck", fontfile=fontfile, fontsize=40)
            pix = tmp_page.get_pixmap(dpi=150)
            has_ink = any(b < 250 for b in pix.samples)
            tmp_doc.close()
        except Exception:
            has_ink = False
        _ink_cache[key] = has_ink
        if not has_ink:
            return False
    return True


def extract_page_fonts(doc: "fitz.Document", page: "fitz.Page") -> dict:
    """
    提取当前页用到的所有嵌入字体，写入临时文件。
    返回 {xref: 临时字体文件路径 或 None}
    """
    font_files = {}
    for f in page.get_fonts(full=True):
        xref = f[0]
        try:
            _basename, ext, _ftype, buf = doc.extract_font(xref)
        except Exception:
            buf, ext = b"", ""
        if buf and ext not in ("n/a", ""):
            tmp = tempfile.NamedTemporaryFile(suffix="." + ext, delete=False)
            tmp.write(buf)
            tmp.close()
            font_files[xref] = tmp.name
        else:
            font_files[xref] = None
    return font_files


def find_span_for_rect(spans: list, rect: "fitz.Rect"):
    """在页面所有文字片段中，找到与给定矩形重叠面积最大的那个 span"""
    best_span, best_area = None, 0.0
    for span in spans:
        span_rect = fitz.Rect(span["bbox"])
        inter = span_rect & rect
        area = 0.0 if inter.is_empty else inter.get_area()
        if area > best_area:
            best_area, best_span = area, span
    return best_span


def process_pdf(path: str) -> int:
    """处理单个 PDF 文件，返回本文件中实际替换的次数"""
    doc = fitz.open(path)
    total_replacements = 0
    temp_font_files = []  # 记录本文件用到的临时字体文件，处理完后清理

    for page in doc:
        # 收集本页所有需要替换的位置及其原始样式信息
        text_dict = page.get_text("dict")
        spans = [
            span
            for block in text_dict["blocks"]
            for line in block.get("lines", [])
            for span in line["spans"]
        ]
        if not spans:
            continue  # 该页没有可提取的文字（可能是扫描图片页）

        fonts_full = page.get_fonts(full=True)
        font_files = extract_page_fonts(doc, page)
        temp_font_files.extend(p for p in font_files.values() if p)

        matches = []  # (rect, 新文本, 字号, 颜色, 字体文件, 基线起点)
        for old, new in REPLACEMENTS:
            for rect in page.search_for(old):
                span = find_span_for_rect(spans, rect)
                if span:
                    fontsize = span["size"]
                    ci = span["color"]
                    color = ((ci >> 16 & 255) / 255, (ci >> 8 & 255) / 255, (ci & 255) / 255)
                    origin = (rect.x0, span["origin"][1])
                    fontfile = None
                    norm_span_font = normalize(span["font"])
                    for xref, _ext, _ftype, basefont, _refname, _enc in [f[:6] for f in fonts_full]:
                        norm_base = normalize(basefont)
                        if norm_base and (norm_base in norm_span_font or norm_span_font in norm_base):
                            candidate = font_files.get(xref)
                            if candidate and font_covers_text(candidate, new):
                                fontfile = candidate
                            break
                else:
                    # 极少数情况下取不到 span 信息，使用矩形做粗略估算
                    fontsize = max(6.0, round(rect.height * 0.8, 1))
                    color = (0, 0, 0)
                    origin = (rect.x0, rect.y1 - fontsize * 0.15)
                    fontfile = None
                matches.append((rect, new, fontsize, color, fontfile, origin))

        if not matches:
            continue

        # 第一步：统一打码清除原文字
        for rect, *_ in matches:
            page.add_redact_annot(rect, fill=(1, 1, 1))
        page.apply_redactions()

        # 第二步：在原位置插入新文字，尽量复用原字体/字号/颜色
        for _rect, new_text, fontsize, color, fontfile, origin in matches:
            kwargs = dict(fontsize=fontsize, color=color)
            if fontfile:
                kwargs["fontfile"] = fontfile
                kwargs["fontname"] = "F-custom"
            else:
                # 找不到可复用的嵌入字体时，按中英文选用内置字体兜底
                kwargs["fontname"] = "helv" if new_text.isascii() else "china-s"
            page.insert_text(origin, new_text, **kwargs)
            total_replacements += 1

    if total_replacements > 0:
        # 直接原地覆盖保存（不生成备份）
        tmp_path = path + ".tmp"
        doc.save(tmp_path, garbage=4, deflate=True)
        doc.close()
        os.replace(tmp_path, path)
    else:
        doc.close()

    # 清理临时字体文件
    for fp in temp_font_files:
        try:
            os.remove(fp)
        except OSError:
            pass

    return total_replacements


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_files = sorted(
        set(
            glob.glob(os.path.join(script_dir, "**", "*.pdf"), recursive=True)
            + glob.glob(os.path.join(script_dir, "**", "*.PDF"), recursive=True)
        )
    )

    if not pdf_files:
        print(f"在目录 {script_dir} 及其子目录下未找到任何 PDF 文件。")
        return

    print(f"共找到 {len(pdf_files)} 个 PDF 文件（含子目录），开始处理...\n")

    grand_total = 0
    for path in pdf_files:
        rel_path = os.path.relpath(path, script_dir)
        try:
            count = process_pdf(path)
        except Exception as e:
            print(f"[失败] {rel_path}：处理出错 -> {e}")
            continue

        if count > 0:
            print(f"[完成] {rel_path}：共替换 {count} 处")
        else:
            print(f"[跳过] {rel_path}：未找到需要替换的字符串")
        grand_total += count

    print(f"\n全部处理完毕，共替换 {grand_total} 处。")


if __name__ == "__main__":
    main()