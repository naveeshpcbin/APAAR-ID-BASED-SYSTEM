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
        print(f'*** SLIDE {i} ***')
        for sp in root.findall('.//p:sp', namespaces):
            cNvPr = sp.find('.//p:nvSpPr/p:cNvPr', namespaces)
            name = cNvPr.attrib.get('name', '') if cNvPr is not None else ''
            xfrm = sp.find('.//p:spPr/a:xfrm', namespaces)
            pos = ''
            if xfrm is not None:
                off = xfrm.find('a:off', namespaces)
                ext = xfrm.find('a:ext', namespaces)
                if off is not None and ext is not None:
                    pos = f"x={off.attrib.get('x')}, y={off.attrib.get('y')}, w={ext.attrib.get('cx')}, h={ext.attrib.get('cy')}"
            
            texts = []
            for p in sp.findall('.//a:p', namespaces):
                t_list = [t.text for t in p.findall('.//a:t', namespaces) if t.text]
                if t_list:
                    texts.append(''.join(t_list))
            if texts:
                print(f'  Shape "{name}" ({pos}):')
                for t in texts:
                    print(f'    -> {t}')
