import pymupdf
import json
import os

files = {
    'ref1': r'D:\AICTE\finaldemoppt\sih-winning-ppt-1.pdf',
    'ref2': r'D:\AICTE\finaldemoppt\sih-winning-ppt-2.pdf',
    'ref3': r'D:\AICTE\finaldemoppt\sih-winning-ppt-3.pdf',
    'current': r'D:\AICTE\finaldemoppt\PRAMAAN-AICTE_SIH2026_Idea_Presentation.pdf'
}

report = {}

for key, fpath in files.items():
    doc = pymupdf.open(fpath)
    deck_info = {
        'filename': os.path.basename(fpath),
        'page_count': len(doc),
        'slides': []
    }
    for pno, page in enumerate(doc):
        rect = page.rect
        blocks = page.get_text('blocks')
        # Sort blocks by vertical position top-to-bottom
        blocks_sorted = sorted(blocks, key=lambda b: (b[1], b[0]))
        text_content = [b[4].strip() for b in blocks_sorted if b[4].strip()]
        
        # Extract fonts
        fonts = set()
        for b in page.get_text('dict')['blocks']:
            if 'lines' in b:
                for line in b['lines']:
                    for span in line['spans']:
                        fonts.add((span['font'], round(span['size'], 1), hex(span['color'])))
        
        slide_info = {
            'slide_num': pno + 1,
            'rect': [rect.x0, rect.y0, rect.x1, rect.y1],
            'fonts_sample': list(fonts)[:10],
            'text_lines': text_content
        }
        deck_info['slides'].append(slide_info)
    report[key] = deck_info

with open(r'D:\AICTE\finaldemoppt\ref_inspections\deck_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("Saved deck_analysis.json successfully.")

