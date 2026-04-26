import sys
import json
import os
from datetime import date

# --- PATH FIX ---
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    current_dir = os.path.dirname(os.path.abspath(sys.executable))
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = current_dir
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    return os.path.join(BASE_DIR, relative_path)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QListWidget, QStackedWidget, QLabel, QFrame, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QDialog, QFormLayout, 
    QLineEdit, QComboBox, QDateEdit, QMessageBox, QFileDialog, QSizePolicy,
    QGraphicsDropShadowEffect, QStyle
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, QDate, QPoint, QPropertyAnimation, QEasingCurve, QTimer, QEvent
from PyQt6.QtGui import QColor, QIcon

from src.domain.types import Transaction, TransactionType, TransactionFilter
from src.infrastructure.database import SqliteTransactionRepo
from src.services.finance_service import FinanceService

# --- UI COMPONENTS ---

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("TitleBar")
        self.setFixedHeight(40)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 0, 0, 0)
        
        # Icon + Title
        title = QLabel("💳 Personal Budget Dashboard")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Buttons Style
        btn_css = "QPushButton { background: transparent; border: none; font-size: 16px; color: #a0a0b0; } QPushButton:hover { background: #303040; color: white; }"
        close_css = "QPushButton { background: transparent; border: none; font-size: 16px; color: #a0a0b0; } QPushButton:hover { background: #ed4245; color: white; }"
        
        self.btn_min = QPushButton("—")
        self.btn_min.setFixedSize(50, 40)
        self.btn_min.setStyleSheet(btn_css)
        self.btn_min.clicked.connect(self.parent.showMinimized)
        
        self.btn_max = QPushButton("☐")
        self.btn_max.setFixedSize(50, 40)
        self.btn_max.setStyleSheet(btn_css)
        self.btn_max.clicked.connect(self._toggle_max)
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(50, 40)
        self.btn_close.setStyleSheet(close_css)
        self.btn_close.clicked.connect(self.parent.close)
        
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        self.start = QPoint(0, 0)
        self.pressing = False

    def _toggle_max(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    # Move window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start = event.globalPosition().toPoint()
            self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing and not self.parent.isMaximized():
            end = event.globalPosition().toPoint()
            movement = end - self.start
            self.parent.setGeometry(self.parent.x() + movement.x(),
                                  self.parent.y() + movement.y(),
                                  self.parent.width(),
                                  self.parent.height())
            self.start = end

    def mouseReleaseEvent(self, event):
        self.pressing = False

class InfoCard(QFrame):
    def __init__(self, obj_name, title, value, icon_char):
        super().__init__()
        self.setObjectName(obj_name) 
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header Row (Title + Icon)
        h_row = QHBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setObjectName("CardTitle")
        
        lbl_icon = QLabel(icon_char)
        lbl_icon.setStyleSheet("font-size: 24px; background: transparent; color: rgba(255,255,255,0.5);")
        
        h_row.addWidget(lbl_title)
        h_row.addStretch()
        h_row.addWidget(lbl_icon)
        
        lbl_value = QLabel(value)
        lbl_value.setObjectName("CardValue")
        
        layout.addLayout(h_row)
        layout.addWidget(lbl_value)
        self.setLayout(layout)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

class TransactionDialog(QDialog):
    def __init__(self, service: FinanceService, transaction=None, parent=None):
        super().__init__(parent)
        self.transaction = transaction
        self.service = service
        
        # Settings
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setWindowOpacity(0.0)
        
        # Layouts
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10) # Padding for shadow
        
        self.container = QFrame()
        self.container.setObjectName("DialogContainer")
        
        # Shadow Effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        self.form_layout = QFormLayout(self.container)
        self.form_layout.setContentsMargins(30, 30, 30, 30)
        self.form_layout.setSpacing(15)
        
        # Header
        header_row = QHBoxLayout()
        title_lbl = QLabel("📝 Операция")
        title_lbl.setObjectName("DialogTitle")
        
        close_btn = QPushButton("X")
        close_btn.setObjectName("DialogClose")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        
        header_row.addWidget(title_lbl)
        header_row.addStretch()
        header_row.addWidget(close_btn)
        self.form_layout.addRow(header_row)
        
        # Inputs
        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in TransactionType])
        self.type_combo.currentTextChanged.connect(self._refresh_categories)
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        
        self.cat_combo = QComboBox()
        self.cat_combo.setEditable(False)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setButtonSymbols(QDateEdit.ButtonSymbols.UpDownArrows)
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Описание...")
        
        self._refresh_categories()
        if transaction:
            self.type_combo.setCurrentText(transaction.type.value)
            self._refresh_categories()
            self.amount_edit.setText(str(transaction.amount))
            self.cat_combo.setCurrentText(transaction.category)
            self.date_edit.setDate(transaction.date_added)
            self.desc_edit.setText(transaction.description)

        # Labels
        lbl_css = "color: #b9bbbe; font-size: 14px; font-weight: bold; background: transparent;"
        def mk_lbl(text):
            l = QLabel(text)
            l.setStyleSheet(lbl_css)
            return l

        self.form_layout.addRow(mk_lbl("Тип:"), self.type_combo)
        self.form_layout.addRow(mk_lbl("Сумма:"), self.amount_edit)
        self.form_layout.addRow(mk_lbl("Категория:"), self.cat_combo)
        self.form_layout.addRow(mk_lbl("Дата:"), self.date_edit)
        self.form_layout.addRow(mk_lbl("Инфо:"), self.desc_edit)
        
        # Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(15)
        
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("BtnAdd")
        save_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("BtnDelete")
        cancel_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)
        
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        self.form_layout.addRow(btn_box)
        
        self.main_layout.addWidget(self.container)
        self.setLayout(self.main_layout)
        
        self.drag_pos = None
        self._appear_anim = QPropertyAnimation(self, b"windowOpacity")
        self._appear_anim.setDuration(260)
        self._appear_anim.setStartValue(0.0)
        self._appear_anim.setEndValue(1.0)
        self._appear_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        QTimer.singleShot(0, self._start_appear_animation)

    # --- DRAG FIX: Drag only works on Top Area ---
    def mousePressEvent(self, event):
        # Allow dragging only if clicked in top 60px (Header area)
        if event.button() == Qt.MouseButton.LeftButton:
            click_pos = event.position().toPoint()
            if click_pos.y() < 60:
                self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def _start_appear_animation(self):
        self._appear_anim.stop()
        self._appear_anim.start()

    def _refresh_categories(self):
        tx_type = TransactionType(self.type_combo.currentText())
        current_text = self.cat_combo.currentText()
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        self.cat_combo.addItems(self.service.get_categories_for_type(tx_type))
        if current_text:
            self.cat_combo.setCurrentText(current_text)
        self.cat_combo.blockSignals(False)

    def eventFilter(self, source, event):
        return super().eventFilter(source, event)

    def get_data(self):
        try:
            amount = float(self.amount_edit.text())
            if amount <= 0: raise ValueError
        except: return None
            
        return Transaction(
            id=self.transaction.id if self.transaction else None,
            amount=amount,
            category=self.cat_combo.currentText(),
            date_added=self.date_edit.date().toPyDate(),
            type=TransactionType(self.type_combo.currentText()),
            description=self.desc_edit.text()
        )

# --- PAGES ---

class DashboardPage(QWidget):
    def __init__(self, service: FinanceService):
        super().__init__()
        self.service = service
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        cards = QHBoxLayout()
        cards.setSpacing(20)
        self.card_inc = InfoCard("CardIncome", "Доходы", "0 ₽", "💰")
        self.card_exp = InfoCard("CardExpense", "Расходы", "0 ₽", "💸")
        self.card_bal = InfoCard("CardBalance", "Баланс", "0 ₽", "🏦")
        cards.addWidget(self.card_inc)
        cards.addWidget(self.card_exp)
        cards.addWidget(self.card_bal)
        layout.addLayout(cards)
        
        # Charts
        row1 = QHBoxLayout()
        self.chart_pie = QWebEngineView()
        self.chart_pie.setFixedHeight(300)
        self.chart_pie.setStyleSheet("background: transparent;")
        
        self.chart_bar = QWebEngineView()
        self.chart_bar.setFixedHeight(300)
        self.chart_bar.setStyleSheet("background: transparent;")
        
        row1.addWidget(self.chart_pie)
        row1.addWidget(self.chart_bar)
        
        self.chart_line = QWebEngineView()
        self.chart_line.setFixedHeight(250)
        self.chart_line.setStyleSheet("background: transparent;")
        
        layout.addLayout(row1)
        layout.addWidget(self.chart_line)
        self.setLayout(layout)
        
        html = self._load_html()
        for c in [self.chart_pie, self.chart_bar, self.chart_line]:
            c.setHtml(html)
            c.loadFinished.connect(self.refresh_data)

    def _load_html(self):
        path = resource_path(os.path.join('ui', 'assets', 'chart_view.html'))
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: return f.read()
        return ""

    def refresh_data(self):
        data = self.service.get_summary()
        self.card_inc.findChild(QLabel, "CardValue").setText(f"{data.total_income:,.0f} ₽")
        self.card_exp.findChild(QLabel, "CardValue").setText(f"{data.total_expense:,.0f} ₽")
        self.card_bal.findChild(QLabel, "CardValue").setText(f"{data.balance:,.0f} ₽")
        
        self._inject_js(self.chart_pie, self._opt_pie(data.expense_by_category))
        self._inject_js(self.chart_bar, self._opt_bar(data.total_income, data.total_expense))
        self._inject_js(self.chart_line, self._opt_line(data.balance_history))

    def _inject_js(self, view, opt):
        view.page().runJavaScript(f"updateChart('{json.dumps(opt)}');")

    def _opt_pie(self, data):
        return {
            "title": {"text": "Расходы", "left": "center", "textStyle": {"color": "#fff", "fontSize": 16}},
            "tooltip": {"trigger": "item"},
            "series": [{"type": "pie", "radius": ["40%", "70%"], 
                        "data": [{"value": v, "name": k} for k, v in data.items()],
                        "label": {"color": "#fff"},
                        "itemStyle": {"borderRadius": 5, "borderColor": "#1e1e2d", "borderWidth": 2}}]
        }

    def _opt_bar(self, inc, exp):
        return {
            "title": {"text": "Доход/Расход", "textStyle": {"color": "#fff", "fontSize": 16}},
            "tooltip": {},
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"data": ["Доход", "Расход"], "axisLabel": {"color": "#fff"}},
            "yAxis": {"splitLine": {"show": False}, "axisLabel": {"color": "#fff"}},
            "series": [{"type": "bar", "data": [
                {"value": inc, "itemStyle": {"color": "#23a559"}},
                {"value": exp, "itemStyle": {"color": "#ed4245"}}
            ]}]
        }

    def _opt_line(self, history):
        return {
            "title": {"text": "Динамика Баланса", "textStyle": {"color": "#fff", "fontSize": 16}},
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "data": list(history.keys()), "axisLabel": {"color": "#fff"}},
            "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#333"}}, "axisLabel": {"color": "#fff"}},
            "series": [{"data": list(history.values()), "type": "line", "smooth": True, "areaStyle": {"opacity": 0.2}, "itemStyle": {"color": "#5865f2"}}]
        }

class TransactionsPage(QWidget):
    def __init__(self, service: FinanceService):
        super().__init__()
        self.service = service
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Toolbar
        btns = QHBoxLayout()
        btns.setSpacing(15)
        
        b_add = QPushButton(" Добавить")
        b_add.setObjectName("BtnAdd")
        b_add.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        b_add.setCursor(Qt.CursorShape.PointingHandCursor)
        b_add.clicked.connect(self.add_tx)
        
        b_edit = QPushButton(" Изменить")
        b_edit.setObjectName("BtnEdit")
        b_edit.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        b_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        b_edit.clicked.connect(self.edit_tx)
        
        b_del = QPushButton(" Удалить")
        b_del.setObjectName("BtnDelete")
        b_del.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        b_del.setCursor(Qt.CursorShape.PointingHandCursor)
        b_del.clicked.connect(self.del_tx)
        
        b_exp = QPushButton(" Экспорт")
        b_exp.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        b_exp.setCursor(Qt.CursorShape.PointingHandCursor)
        b_exp.clicked.connect(self.export_csv)
        
        btns.addWidget(b_add)
        btns.addWidget(b_edit)
        btns.addWidget(b_del)
        btns.addStretch()
        btns.addWidget(b_exp)
        layout.addLayout(btns)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Дата", "Тип", "Категория", "Сумма", "Описание"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        self.refresh()
        self.setLayout(layout)

    def refresh(self):
        txs = self.service.repo.get_filtered(TransactionFilter())
        self.table.setRowCount(len(txs))
        for i, t in enumerate(txs):
            self.table.setItem(i, 0, QTableWidgetItem(str(t.id)))
            self.table.setItem(i, 1, QTableWidgetItem(str(t.date_added)))
            self.table.setItem(i, 2, QTableWidgetItem(t.type.value))
            self.table.setItem(i, 3, QTableWidgetItem(t.category))
            
            amt = QTableWidgetItem(f"{t.amount:,.2f}")
            amt.setForeground(Qt.GlobalColor.green if t.type == TransactionType.INCOME else Qt.GlobalColor.red)
            self.table.setItem(i, 4, amt)
            self.table.setItem(i, 5, QTableWidgetItem(t.description))
            
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, t)

    def add_tx(self):
        dlg = TransactionDialog(self.service)
        if dlg.exec():
            t = dlg.get_data()
            if t:
                self.service.repo.add(t)
                self.service.add_category(t.category)
                self.refresh()

    def edit_tx(self):
        row = self.table.currentRow()
        if row < 0: return
        t_old = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dlg = TransactionDialog(self.service, t_old)
        if dlg.exec():
            t_new = dlg.get_data()
            if t_new:
                self.service.repo.update(t_new)
                self.refresh()

    def del_tx(self):
        row = self.table.currentRow()
        if row < 0: return
        t = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        msg = QMessageBox(self)
        msg.setWindowTitle("Удаление")
        msg.setText("Удалить запись?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        yes_btn = msg.button(QMessageBox.StandardButton.Yes)
        no_btn = msg.button(QMessageBox.StandardButton.No)
        if yes_btn:
            yes_btn.setText("Да")
        if no_btn:
            no_btn.setText("Нет")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.service.repo.delete(t.id)
            self.refresh()
    
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить", "report.csv", "CSV (*.csv)")
        if path:
            self.service.export_csv(path, TransactionFilter())
            QMessageBox.information(self, "Успех", "Файл сохранен")

# --- MAIN WINDOW ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1200, 800)
        
        self.repo = SqliteTransactionRepo()
        self.service = FinanceService(self.repo)
        
        self.setup_ui()
        
    def setup_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar(self)
        v_layout.addWidget(self.title_bar)
        
        content = QWidget()
        h_layout = QHBoxLayout(content)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(240)
        # Using Emoji Icons for Menu
        self.sidebar.addItems(["  📊 Дашборд", "  💸 Операции", "  📥 Отчет CSV"])
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self.switch_page)
        
        self.stack = QStackedWidget()
        self.p_dash = DashboardPage(self.service)
        self.p_trans = TransactionsPage(self.service)
        self.stack.addWidget(self.p_dash)
        self.stack.addWidget(self.p_trans)
        
        h_layout.addWidget(self.sidebar)
        h_layout.addWidget(self.stack)
        
        v_layout.addWidget(content)

    def switch_page(self, idx):
        if idx == 0:
            self.p_dash.refresh_data()
            self.stack.setCurrentIndex(0)
        elif idx == 1:
            self.p_trans.refresh()
            self.stack.setCurrentIndex(1)
        elif idx == 2:
            self.p_trans.export_csv()
            self.sidebar.setCurrentRow(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    style_path = resource_path(os.path.join('ui', 'styles.qss'))
    if os.path.exists(style_path):
        with open(style_path, 'r') as f:
            app.setStyleSheet(f.read())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())