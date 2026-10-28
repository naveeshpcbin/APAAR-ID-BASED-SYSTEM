import pymupdf

doc = pymupdf.open(r'D:\AICTE\deck\final\PRAMAAN-AICTE_SIH2026_Final.pdf')

with open(r'D:\AICTE\deck\final\pdf_text_dump.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total pages in final PDF: {len(doc)}\n")
    for i, page in enumerate(doc):
        rect = page.rect
        out.write(f"\n=======================================================\n")
        out.write(f"SLIDE {i+1}: width={rect.width}, height={rect.height}\n")
        out.write(f"=======================================================\n")
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0]))
        for b in blocks:
            text = b[4].strip().replace('\n', ' ')
            if text:
                out.write(f"  [{b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, {b[3]:.1f}] -> {text}\n")

print("Saved pdf_text_dump.txt successfully.")
