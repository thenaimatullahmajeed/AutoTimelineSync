"""Grounded UI smoke-test helper for the task's Android emulator."""
from pathlib import Path
import json, re, subprocess, sys
from xml.etree import ElementTree as ET

ADB = Path.home() / 'AppData/Local/Android/Sdk/platform-tools/adb.exe'
SERIAL = 'emulator-5554'
def adb(*args):
    return subprocess.check_output([str(ADB), '-s', SERIAL, *args]).decode('utf8', 'replace')

if __name__ == '__main__':
    response = adb('shell', 'uiautomator', 'dump', '/sdcard/ats-ui.xml')
    if 'dumped to:' not in response:
        raise RuntimeError('No fresh UI snapshot; wait for the screen to settle')
    tree = ET.fromstring(adb('shell', 'cat', '/sdcard/ats-ui.xml'))
    nodes = list(tree.iter('node'))
    if len(sys.argv) > 1:
        label = sys.argv[1]
        match = [n for n in nodes if n.get('text') == label or n.get('content-desc') == label]
        if not match:
            raise RuntimeError('Label not present: ' + label)
        node = match[int(sys.argv[2]) if len(sys.argv) > 2 else 0]
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', node.get('bounds')))
        if x2 <= x1 or y2 <= y1:
            raise RuntimeError('Target has no visible bounds')
        adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
        print(json.dumps(dict(tapped=label, bounds=node.get('bounds'))))
    else:
        print(json.dumps([dict(label=n.get('text') or n.get('content-desc'), bounds=n.get('bounds'),
            resource=n.get('resource-id'), enabled=n.get('enabled')) for n in nodes
            if n.get('text') or n.get('content-desc')], indent=2))
