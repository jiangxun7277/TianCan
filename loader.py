def generate_v1_final_loader_code(encrypted_script_b64, script_key_salt, dummy_imports):
    import random
    from vm import assemble_chinese

    build_seed = random.randint(1000, 9999)
    chinese_probe = """
    矩阵 青龙, 0
    矩阵 白虎, 1
    映射 青龙, 白虎
    铣削
    拟合 白虎, 5
    寻路
    渲染 青龙, 白虎
    归一 青龙
    """
    dynamic_bytecode = assemble_chinese(chinese_probe, build_seed)
    code = f'''
import sys
import os
import base64
import __main__

class LoaderProxy:
    def __init__(self, real_loader):
        self._real_loader = real_loader
        self.__name__ = type(real_loader).__name__
        self.__spec__ = None 

    def __getattr__(self, name):
        return getattr(self._real_loader, name)

class MetaPathProxy:
    def __init__(self, real_finder):
        self._real_finder = real_finder

    def find_spec(self, fullname, path=None, target=None):
        if hasattr(self._real_finder, 'find_spec'):
            spec = self._real_finder.find_spec(fullname, path, target)
            if spec and spec.loader and type(spec.loader).__name__ in ('nuitka_module_loader', 'FrozenImporter'):
                spec.loader = LoaderProxy(spec.loader)
            return spec
        return None

    def find_module(self, fullname, path=None):
        if hasattr(self._real_finder, 'find_module'):
            loader = self._real_finder.find_module(fullname, path)
            if loader and type(loader).__name__ in ('nuitka_module_loader', 'FrozenImporter'):
                return LoaderProxy(loader)
        return None

new_meta = []
for finder in sys.meta_path:
    if type(finder).__name__ in ('FrozenImporter', 'nuitka_module_finder'):
        new_meta.append(MetaPathProxy(finder))
    else:
        new_meta.append(finder)
sys.meta_path = new_meta

for mod in list(sys.modules.values()):
    if mod is None: continue
    loader = getattr(mod, '__loader__', None)
    if loader and type(loader).__name__ in ('nuitka_module_loader', 'FrozenImporter'):
        mod.__loader__ = LoaderProxy(loader)

{dummy_imports}

__main__.__file__ = __file__
__main__.__cached__ = None

try:
    import security
except Exception:
    sys.exit(1)

seed = {build_seed}
bytecode = {dynamic_bytecode}
encrypted_payload = base64.b64decode("{encrypted_script_b64}")
salt = "{script_key_salt}"

try:
    security.run_secure(seed, bytecode, encrypted_payload, salt)
except Exception:
    sys.exit(1)
'''
    return code