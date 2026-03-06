import os
import re

class DependencyScanner:
    @staticmethod
    def scan_project(entry_file):
        project_dir = os.path.dirname(entry_file)
        detected_plugins = set()
        rules = {
            'numpy': 'numpy', 'pandas': 'numpy', 'PySide6': 'pyside6',
            'PyQt6': 'pyside6', 'PyQt5': 'pyqt5', 'tkinter': 'tk-inter',
            'torch': 'torch', 'tensorflow': 'tensorflow', 'cv2': 'opencv'
        }
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.py'):
                    try:
                        path = os.path.join(root, file)
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for keyword, plugin_name in rules.items():
                                if re.search(fr'\b(import|from)\s+{keyword}\b', content):
                                    detected_plugins.add(plugin_name)
                    except Exception:
                        pass
        return list(detected_plugins)