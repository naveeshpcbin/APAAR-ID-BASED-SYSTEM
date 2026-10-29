import pymupdf

for fname in ['sih-winning-ppt-2.pdf', 'sih-winning-ppt-3.pdf']:
    doc = pymupdf.open(f'D:\\AICTE\\finaldemoppt\\{fname}')
    out_name = f'D:\\AICTE\\dump_{fname}.txt'
    with open(out_name, 'w', encoding='utf-8') as f:
        f.write(f"============================== {fname} ==============================\n")
        for i, page in enumerate(doc):
            f.write(f"\n--- SLIDE {i+1} ---\n")
            blocks = page.get_text('blocks')
            blocks.sort(key=lambda b: (b[1], b[0]))
            for b in blocks:
                t = b[4].strip().replace('\n', ' // ')
                if t:
                    f.write(f"  [{b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, {b[3]:.1f}] -> {t}\n")
    print(f"Dumped {out_name}")

