import pymupdf

doc = pymupdf.open(r'D:\AICTE\finaldemoppt\sih-winning-ppt-1.pdf')

def fmt_col(c):
    if c is None:
        return "None"
    if isinstance(c, (list, tuple)):
        return f"RGB({int(c[0]*255)},{int(c[1]*255)},{int(c[2]*255)})" if len(c) >= 3 else str(c)
    if isinstance(c, int):
        return hex(c)
    return str(c)

for pno, page in enumerate(doc):
    print(f"==================================================")
    print(f"SLIDE {pno+1}: width={page.rect.width}, height={page.rect.height}")
    print(f"==================================================")
    
    drawings = page.get_drawings()
    print(f"Total vector drawings: {len(drawings)}")
    rect_drawings = []
    for d in drawings:
        r = d['rect']
        if r.width > 50 and r.height > 15:
            rect_drawings.append((round(r.x0, 1), round(r.y0, 1), round(r.width, 1), round(r.height, 1), fmt_col(d.get('fill')), fmt_col(d.get('color'))))
    print(f"Significant drawings ({len(rect_drawings)}):")
    for rd in rect_drawings[:12]:
        print(f"   box: (x={rd[0]}, y={rd[1]}, w={rd[2]}, h={rd[3]}), fill={rd[4]}, line={rd[5]}")
    
    blocks = page.get_text("dict")["blocks"]
    text_blocks = [b for b in blocks if "lines" in b]
    print(f"Total text blocks: {len(text_blocks)}")
    for b in text_blocks[:10]:
        r = b['bbox']
        first_line = b['lines'][0]['spans'][0]
        text_preview = "".join(s['text'] for line in b['lines'] for s in line['spans'])[:60].strip()
        print(f"   text @ ({r[0]:.1f}, {r[1]:.1f}, w={r[2]-r[0]:.1f}, h={r[3]-r[1]:.1f}): font={first_line['font']}, size={first_line['size']:.1f}, color={fmt_col(first_line['color'])} -> \"{text_preview}\"")
    print()
