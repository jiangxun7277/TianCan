import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
                               QMessageBox, QProgressBar, QListWidget, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt, QTimer
from builder import CompilerThread


class CompilerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("天蚕 TianCan V1.0")
        self.resize(900, 750)
        self.current_progress = 0
        self.target_progress = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_progress)
        self.resource_data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("🛡️ 天蚕 TianCan V1.0")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2C3E50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.drop_area = QLabel("\n📥\n\n请拖入项目")
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setMinimumHeight(80)
        self.drop_area.setStyleSheet("""
            QLabel { background-color: #F4F6F6; border: 2px dashed #BDC3C7; border-radius: 10px; color: #7F8C8D; font-weight: bold; font-size: 14px; }
            QLabel:hover { border-color: #3498DB; background-color: #ECF0F1; }
        """)
        layout.addWidget(self.drop_area)

        file_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("项目入口 (Main Entry)")
        self.path_input.setMinimumHeight(40)
        browse_btn = QPushButton("📂 浏览")
        browse_btn.setMinimumHeight(40)
        browse_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.path_input)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        res_group = QGroupBox("🛠️ 资源管理器")
        res_group.setStyleSheet(
            "QGroupBox { font-weight: bold; border: 1px solid #D5D8DC; margin-top: 10px; border-radius: 5px; }")
        res_layout = QVBoxLayout()
        icon_layout = QHBoxLayout()
        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText("程序图标 (.ico) - 留空则使用默认")
        icon_btn = QPushButton("选图标")
        icon_btn.clicked.connect(self.select_icon)
        icon_layout.addWidget(self.icon_input)
        icon_layout.addWidget(icon_btn)
        res_layout.addLayout(icon_layout)
        self.res_list_widget = QListWidget()
        self.res_list_widget.setMaximumHeight(80)
        self.res_list_widget.setStyleSheet("border: 1px solid #EAECEE; background-color: #FBFCFC;")
        res_layout.addWidget(self.res_list_widget)
        btn_layout = QHBoxLayout()
        add_file_btn = QPushButton("➕ 添加文件")
        add_dir_btn = QPushButton("➕ 添加文件夹")
        clear_btn = QPushButton("清空")
        btn_style = "QPushButton { background-color: #EBEDEF; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #D6DBDF; }"
        add_file_btn.setStyleSheet(btn_style)
        add_dir_btn.setStyleSheet(btn_style)
        clear_btn.setStyleSheet(btn_style)
        add_file_btn.clicked.connect(self.add_resource_file)
        add_dir_btn.clicked.connect(self.add_resource_dir)
        clear_btn.clicked.connect(self.clear_resources)
        btn_layout.addWidget(add_file_btn)
        btn_layout.addWidget(add_dir_btn)
        btn_layout.addWidget(clear_btn)
        res_layout.addLayout(btn_layout)
        res_group.setLayout(res_layout)
        layout.addWidget(res_group)

        info_layout = QHBoxLayout()
        self.chk_anti_bloat = QCheckBox("启用极限压缩")
        self.chk_anti_bloat.setChecked(True)
        self.chk_anti_bloat.setStyleSheet("color: #27AE60; font-weight: bold;")

        self.chk_no_console = QCheckBox("隐藏控制台shell")
        self.chk_no_console.setStyleSheet("color: #8E44AD; font-weight: bold;")

        smart_label = QLabel("中文VM + C-API黑盒 双重加固")
        smart_label.setStyleSheet("color: #E67E22; font-style: italic; font-weight: bold;")
        smart_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        info_layout.addWidget(self.chk_anti_bloat)
        info_layout.addWidget(self.chk_no_console)
        info_layout.addStretch()
        info_layout.addWidget(smart_label)
        layout.addLayout(info_layout)

        self.build_btn = QPushButton("开始")
        self.build_btn.setMinimumHeight(60)
        self.build_btn.setCursor(Qt.PointingHandCursor)
        self.build_btn.setStyleSheet("""
            QPushButton { background-color: #2C3E50; color: white; font-size: 18px; font-weight: bold; border-radius: 8px; }
            QPushButton:hover { background-color: #34495E; }
            QPushButton:disabled { background-color: #95A5A6; }
        """)
        self.build_btn.clicked.connect(self.start_compilation)
        layout.addWidget(self.build_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #BDC3C7; border-radius: 5px; text-align: center; } QProgressBar::chunk { background-color: #2ECC71; }")
        layout.addWidget(self.progress_bar)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(
            "background-color: #17202A; color: #2ECC71; font-family: Consolas; font-size: 12px; border-radius: 5px;")
        layout.addWidget(self.log_area)

        self.setLayout(layout)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        if files and files[0].endswith('.py'):
            self.path_input.setText(files[0])
            self.drop_area.setText(f"\n✅ 已就绪: {os.path.basename(files[0])}")

    def select_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择入口", "", "Python Files (*.py)")
        if f: self.path_input.setText(f)

    def select_icon(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择图标", "", "Icon Files (*.ico)")
        if f: self.icon_input.setText(f)

    def add_resource_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择资源文件")
        if f:
            self.resource_data.append(('file', f))
            self.res_list_widget.addItem(f"📄 {os.path.basename(f)}")

    def add_resource_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择资源文件夹")
        if d:
            self.resource_data.append(('dir', d))
            self.res_list_widget.addItem(f"📂 {os.path.basename(d)}")

    def clear_resources(self):
        self.resource_data = []
        self.res_list_widget.clear()

    def start_compilation(self):
        path = self.path_input.text()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "错误", "请先选择有效的入口文件！")
            return
        self.build_btn.setEnabled(False)
        self.log_area.clear()
        self.progress_bar.show()
        self.current_progress = 0
        self.target_progress = 0
        self.timer.start(30)
        self.thread = CompilerThread(path, self.icon_input.text(), self.resource_data, self.chk_anti_bloat.isChecked(),
                                     self.chk_no_console.isChecked())
        self.thread.log_signal.connect(self.update_log)
        self.thread.target_progress_signal.connect(self.set_target_progress)
        self.thread.finished_signal.connect(self.compilation_finished)
        self.thread.start()

    def set_target_progress(self, val):
        self.target_progress = val

    def animate_progress(self):
        if self.current_progress < self.target_progress:
            self.current_progress += 1
            self.progress_bar.setValue(self.current_progress)

    def update_log(self, text):
        self.log_area.append(text)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def compilation_finished(self, success):
        self.timer.stop()
        self.build_btn.setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "成功", "编译成功！")
        else:
            QMessageBox.critical(self, "失败", "编译失败！请查看日志")