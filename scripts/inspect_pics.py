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
        print(f'*** SLIDE {i} PICTURES ***')
        for pic in root.findall('.//p:pic', namespaces):
            cNvPr = pic.find('.//p:nvPicPr/p:cNvPr', namespaces)
            blip = pic.find('.//p:blipFill/a:blip', namespaces)
            embed = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') if blip is not None else ''
            xfrm = pic.find('.//p:spPr/a:xfrm', namespaces)
            pos = ''
            if xfrm is not None:
                off = xfrm.find('a:off', namespaces)
                ext = xfrm.find('a:ext', namespaces)
                if off is not None and ext is not None:
                    pos = f"x={off.attrib.get('x')}, y={off.attrib.get('y')}, w={ext.attrib.get('cx')}, h={ext.attrib.get('cy')}"
            print(f"  Pic '{cNvPr.attrib.get('name') if cNvPr is not None else ''}' embed={embed} pos=({pos})")
