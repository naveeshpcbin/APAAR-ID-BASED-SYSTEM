import json
import sys

with open(r'D:\AICTE\finaldemoppt\ref_inspections\deck_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open(r'D:\AICTE\finaldemoppt\ref_inspections\deck_summary.txt', 'w', encoding='utf-8') as out:
    for deck_key, deck in data.items():
        out.write(f"==================================================\n")
        out.write(f"DECK: {deck_key} - {deck['filename']}\n")
        out.write(f"==================================================\n")
        for s in deck['slides']:
            s_num = s['slide_num']
            lines = s['text_lines']
            out.write(f"--- Slide {s_num} ---\n")
            for line in lines:
                out.write(f"  > {line.replace(chr(10), ' | ')}\n")
            out.write(f"  Fonts: {s['fonts_sample']}\n\n")

print("Wrote deck_summary.txt successfully.")
