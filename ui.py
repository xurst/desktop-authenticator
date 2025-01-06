# ui.py
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget,
                             QTreeWidgetItem, QProgressBar, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
import pyperclip
import sys
from typing import Optional, Dict


class AuthenticatorUI(QMainWindow):
    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.setWindowTitle("Desktop Authenticator")
        self.setMinimumSize(400, 700)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)
        self.last_codes: Dict[str, str] = {}
        self.selected_account: Optional[str] = None
        self.progress_animation = None
        self.last_progress_value = 100
        self.setup_ui()
        self.setup_styles()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_codes)
        self.timer.start(50)

    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                background-color: #333333;
                border: 1px solid #55z;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 10px;
            }
            QGroupBox::title {
                color: #ffffff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton.danger {
                background-color: #c62828;
            }
            QPushButton.danger:hover {
                background-color: #d32f2f;
            }
            QPushButton.test {
                background-color: #2e7d32;
            }
            QPushButton.test:hover {
                background-color: #388e3c;
            }
            QLineEdit {
                background-color: #424242;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QTreeWidget {
                background-color: #424242;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QTreeWidget::item:selected {
                background-color: #1976d2;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #424242;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #1976d2;
            }
            QLabel {
                color: white;
            }
        """)

    def setup_ui(self):
        add_group = QGroupBox("add new account")
        add_layout = QVBoxLayout()
        form_layout = QHBoxLayout()
        name_layout = QVBoxLayout()
        name_label = QLabel("account name:")
        self.name_entry = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_entry)
        secret_layout = QVBoxLayout()
        secret_label = QLabel("secret key:")
        self.secret_entry = QLineEdit()
        secret_layout.addWidget(secret_label)
        secret_layout.addWidget(self.secret_entry)
        form_layout.addLayout(name_layout)
        form_layout.addLayout(secret_layout)
        button_layout = QHBoxLayout()
        add_btn = QPushButton("add account")
        add_btn.clicked.connect(self._add_account)
        test_btn = QPushButton("add test account")
        test_btn.setProperty("class", "test")
        test_btn.clicked.connect(self._add_test_account)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(test_btn)
        button_layout.addStretch()
        add_layout.addLayout(form_layout)
        add_layout.addLayout(button_layout)
        add_group.setLayout(add_layout)
        self.layout.addWidget(add_group)
        codes_group = QGroupBox("2FA codes")
        codes_layout = QVBoxLayout()
        reorder_layout = QHBoxLayout()
        up_btn = QPushButton("↑")
        up_btn.clicked.connect(lambda: self._move_account("up"))
        down_btn = QPushButton("↓")
        down_btn.clicked.connect(lambda: self._move_account("down"))
        reorder_layout.addWidget(up_btn)
        reorder_layout.addWidget(down_btn)
        reorder_layout.addStretch()
        codes_layout.addLayout(reorder_layout)
        self.codes_tree = QTreeWidget()
        self.codes_tree.setHeaderLabels(["account", "current code"])
        self.codes_tree.setColumnWidth(0, 150)
        self.codes_tree.itemSelectionChanged.connect(self._on_selection_changed)
        codes_layout.addWidget(self.codes_tree)
        actions_layout = QHBoxLayout()
        copy_btn = QPushButton("copy code")
        copy_btn.clicked.connect(self._copy_code)
        remove_btn = QPushButton("remove account")
        remove_btn.setProperty("class", "danger")
        remove_btn.clicked.connect(self._remove_account)
        actions_layout.addWidget(copy_btn)
        actions_layout.addWidget(remove_btn)
        actions_layout.addStretch()
        codes_layout.addLayout(actions_layout)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setProperty("value", 100)
        codes_layout.addWidget(self.progress)
        codes_group.setLayout(codes_layout)
        self.layout.addWidget(codes_group)

    def _start_progress_animation(self, start_value: int, end_value: int, duration: int):
        if self.progress_animation is not None:
            self.progress_animation.stop()

        self.progress_animation = QPropertyAnimation(self.progress, b"value")
        self.progress_animation.setStartValue(start_value)
        self.progress_animation.setEndValue(end_value)
        self.progress_animation.setDuration(duration)
        self.progress_animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.progress_animation.start()

    def _on_selection_changed(self):
        item = self.codes_tree.currentItem()
        if item:
            self.selected_account = item.text(0)
        else:
            self.selected_account = None

    def _add_test_account(self):
        success, message = self.logic.add_test_account()
        if success:
            QMessageBox.information(self, "success", f"added {message}")
        else:
            QMessageBox.critical(self, "error", message)

    def _add_account(self):
        name = self.name_entry.text().strip()
        secret = self.secret_entry.text().strip().replace(" ", "")

        if name and secret:
            success, message = self.logic.add_account(name, secret)
            if success:
                self.name_entry.clear()
                self.secret_entry.clear()
                QMessageBox.information(self, "success", f"added {name} successfully!")
            else:
                QMessageBox.critical(self, "error", message)

    def _copy_code(self):
        item = self.codes_tree.currentItem()
        if item:
            code = item.text(1)
            try:
                pyperclip.copy(code)
                QMessageBox.information(self, "copied", "code copied to clipboard!")
            except Exception as e:
                QMessageBox.critical(self, "error", f"failed to copy code: {str(e)}")

    def _remove_account(self):
        item = self.codes_tree.currentItem()
        if item:
            account = item.text(0)
            reply = QMessageBox.question(self, "confirm", f"remove {account}?",
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self.logic.remove_account(account):
                    pass

    def _move_account(self, direction: str) -> None:
        item = self.codes_tree.currentItem()
        if not item:
            return

        current_account = item.text(0)
        current_code = item.text(1)
        current_index = self.codes_tree.indexOfTopLevelItem(item)

        if direction == "up" and current_index > 0:
            target_index = current_index - 1
        elif direction == "down" and current_index < self.codes_tree.topLevelItemCount() - 1:
            target_index = current_index + 1
        else:
            return

        accounts = list(self.logic.secrets.keys())
        accounts[current_index], accounts[target_index] = accounts[target_index], accounts[current_index]
        if not self.logic.reorder_accounts(accounts):
            return

        self.codes_tree.takeTopLevelItem(current_index)
        new_item = QTreeWidgetItem([current_account, current_code])
        self.codes_tree.insertTopLevelItem(target_index, new_item)
        self.codes_tree.setCurrentItem(new_item)

        self.accounts_order = accounts

    def update_codes(self) -> None:
        scrollbar = self.codes_tree.verticalScrollBar()
        current_scroll = scrollbar.value()
        current_selection = self.selected_account
        new_codes = self.logic.get_all_codes()
        current_dict = {name: code for name, code in new_codes}
        time_remaining = self.logic.get_time_remaining()
        current_progress = int((time_remaining / 30) * 100)

        if current_progress > self.last_progress_value:  # New period started
            self._start_progress_animation(0, 100, 100)  # Quick reset animation
        else:
            self._start_progress_animation(self.last_progress_value, current_progress, 50)

        self.last_progress_value = current_progress

        if set(current_dict.keys()) == set(self.last_codes.keys()):
            for i in range(self.codes_tree.topLevelItemCount()):
                item = self.codes_tree.topLevelItem(i)
                account = item.text(0)
                if account in current_dict and current_dict[account] != self.last_codes.get(account):
                    item.setText(1, current_dict[account])

            self.last_codes = current_dict
            return

        self.codes_tree.setUpdatesEnabled(False)
        self.codes_tree.clear()

        for name, code in new_codes:
            item = QTreeWidgetItem([name, code])
            self.codes_tree.addTopLevelItem(item)
            if name == current_selection:
                self.codes_tree.setCurrentItem(item)

        scrollbar.setValue(current_scroll)
        self.codes_tree.setUpdatesEnabled(True)

        self.last_codes = current_dict

def run_app(logic):
    app = QApplication(sys.argv)
    window = AuthenticatorUI(logic)
    window.show()
    sys.exit(app.exec())