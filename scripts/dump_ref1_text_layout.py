import pymupdf

doc = pymupdf.open(r'D:\AICTE\finaldemoppt\sih-winning-ppt-1.pdf')

with open(r'D:\AICTE\finaldemoppt\ref_inspections\ref1_text_layout.txt', 'w', encoding='utf-8') as out:
    for pno, page in enumerate(doc):
        out.write(f"\n=======================================================\n")
        out.write(f"SLIDE {pno+1}: {page.rect}\n")
        out.write(f"=======================================================\n")
        blocks = page.get_text("dict")["blocks"]
        text_blocks = [b for b in blocks if "lines" in b]
        text_blocks.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))
        
        for b in text_blocks:
            bbox = [round(x, 1) for x in b['bbox']]
            first_span = b['lines'][0]['spans'][0]
            full_text = " ".join(s['text'].strip() for line in b['lines'] for s in line['spans'] if s['text'].strip())
            if not full_text:
                continue
            out.write(f"[{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}] ({first_span['font']}, {first_span['size']:.1f}pt, col={first_span['color']}): {full_text[:110]}\n")

print("Dumped ref1_text_layout.txt successfully.")
