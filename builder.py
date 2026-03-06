import sys
import os
import subprocess
import shutil
import base64
import time
import re
from PySide6.QtCore import QThread, Signal
from crypto import TianCanCrypto
from loader import generate_v1_final_loader_code
from scanner import DependencyScanner


class CompilerThread(QThread):
    log_signal = Signal(str)
    target_progress_signal = Signal(int)
    finished_signal = Signal(bool)

    def __init__(self, file_path, icon_path, resource_list, use_anti_bloat, disable_console):
        super().__init__()
        self.file_path = file_path
        self.icon_path = icon_path
        self.resource_list = resource_list
        self.use_anti_bloat = use_anti_bloat
        self.disable_console = disable_console

    def run(self):
        file_name = os.path.basename(self.file_path)
        file_dir = os.path.dirname(self.file_path)

        self.target_progress_signal.emit(5)

        auto_plugins = DependencyScanner.scan_project(self.file_path)
        exe_name = file_name.replace('.py', '.exe')

        if "python" not in os.path.basename(sys.executable).lower():
            python_exe = "python"
        else:
            python_exe = sys.executable

        cmd = [
            python_exe, "-m", "nuitka", "--standalone", "--onefile",
            "--assume-yes-for-downloads", f"--output-dir={file_dir}",
            "-o", exe_name
        ]

        for plugin in auto_plugins: cmd.append(f"--enable-plugin={plugin}")
        if self.use_anti_bloat: cmd.append("--enable-plugin=anti-bloat")
        if self.icon_path and os.path.exists(self.icon_path):
            cmd.append(f"--windows-icon-from-ico={self.icon_path}")
        if self.disable_console:
            cmd.append("--windows-disable-console")

        for r_type, src_path in self.resource_list:
            name = os.path.basename(src_path)
            if r_type == 'file':
                cmd.append(f"--include-data-file={src_path}={name}")
            elif r_type == 'dir':
                cmd.append(f"--include-data-dir={src_path}={name}")

        compiler_root = os.path.dirname(os.path.abspath(__file__))
        pyd_source = os.path.join(compiler_root, "security.pyd")

        if not os.path.exists(pyd_source):
            self.log_signal.emit("❌ 错误：找不到 security.pyd。请先执行 C 编译器编译！")
            self.finished_signal.emit(False)
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            import_lines = re.findall(r'^(?:import\s+.*|from\s+.*)', script_content, re.MULTILINE)
            dummy_imports = "\n".join(import_lines)

            script_key_salt = TianCanCrypto.generate_random_key(8).decode()
            correct_key = "205" + script_key_salt

            enc_script = TianCanCrypto.rc4(script_content.encode('utf-8'), correct_key.encode())
            enc_script_b64 = base64.b64encode(enc_script).decode()

            loader_code = generate_v1_final_loader_code(enc_script_b64, script_key_salt, dummy_imports)

            temp_entry_name = f"tiancan_launcher_{int(time.time())}.py"
            temp_entry_path = os.path.join(file_dir, temp_entry_name)

            with open(temp_entry_path, 'w', encoding='utf-8') as f:
                f.write(loader_code)

            cmd.append(temp_entry_path)

            pyd_temp_target = os.path.join(file_dir, "security.pyd")
            shutil.copyfile(pyd_source, pyd_temp_target)

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW, cwd=file_dir
            )

            for line in process.stdout:
                self.log_signal.emit(line.strip())
                if "compiling" in line.lower(): self.target_progress_signal.emit(50)

            process.wait()

            if os.path.exists(temp_entry_path): os.remove(temp_entry_path)
            if os.path.exists(pyd_temp_target):
                try:
                    os.remove(pyd_temp_target)
                except:
                    pass

            if process.returncode == 0:
                self.target_progress_signal.emit(100)
                self.finished_signal.emit(True)
            else:
                self.finished_signal.emit(False)

        except Exception as e:
            self.log_signal.emit(f"\n❌ 异常: {str(e)}")
            self.finished_signal.emit(False)