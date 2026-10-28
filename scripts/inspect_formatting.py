import zipfile
import xml.etree.ElementTree as ET

namespaces = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

with zipfile.ZipFile('demoppt/SIH2026-IDEA-Presentation-Format (1).pptx', 'r') as z:
    for i in range(1, 8):
        root = ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
        print(f"\n==================== SLIDE {i} ====================")
        for sp in root.findall('.//p:sp', namespaces):
            cNvPr = sp.find('.//p:nvSpPr/p:cNvPr', namespaces)
            name = cNvPr.attrib.get('name', '') if cNvPr is not None else ''
            
            txBody = sp.find('p:txBody', namespaces)
            if txBody is None:
                continue
            
            print(f"\n--- Shape: {name} ---")
            for p in txBody.findall('a:p', namespaces):
                pPr = p.find('a:pPr', namespaces)
                lvl = pPr.attrib.get('lvl', '0') if pPr is not None else '0'
                buNone = pPr.find('a:buNone', namespaces) if pPr is not None else None
                buChar = pPr.find('a:buChar', namespaces) if pPr is not None else None
                buType = "None" if buNone is not None else ("Char:" + buChar.attrib.get('char', '') if buChar is not None else "Bullet")
                
                runs = []
                for r in p.findall('a:r', namespaces):
                    rPr = r.find('a:rPr', namespaces)
                    sz = rPr.attrib.get('sz', '') if rPr is not None else ''
                    b = rPr.attrib.get('b', '0') if rPr is not None else '0'
                    t = r.find('a:t', namespaces)
                    if t is not None and t.text:
                        runs.append(f"[{t.text}] (sz={sz}, b={b})")
                if runs:
                    print(f"  P (lvl={lvl}, bu={buType}): {' '.join(runs)}")
