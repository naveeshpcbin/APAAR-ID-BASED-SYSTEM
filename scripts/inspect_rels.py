import zipfile
import xml.etree.ElementTree as ET

namespaces = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

with zipfile.ZipFile('demoppt/SIH2026-IDEA-Presentation-Format (1).pptx', 'r') as z:
    for name in z.namelist():
        if name.endswith('.rels') and 'image' in z.read(name).decode('utf-8', errors='ignore'):
            print(name)
            root = ET.fromstring(z.read(name))
            for rel in root:
                if 'image' in rel.attrib.get('Type', ''):
                    print('  Rel ID:', rel.attrib.get('Id'), '-> Target:', rel.attrib.get('Target'))
