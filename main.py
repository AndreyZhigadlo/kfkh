import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

DB_PATH = "krs_accounting.db"

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Полная таблица животных
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS animals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag TEXT, chip TEXT, name TEXT, gender TEXT, dob TEXT,
        breed TEXT, mother TEXT, father TEXT, group_name TEXT,
        status TEXT, status_date TEXT, notes TEXT
    );
    """)
    # Таблица здоровья
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS health_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, animal_id TEXT, event_type TEXT, 
        drug TEXT, duration TEXT, repeat_event TEXT, notes TEXT
    );
    """)
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_PATH)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def calc_age(dob_str):
    if not dob_str or dob_str.strip() == "": return ""
    formats = ["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            dob = datetime.strptime(dob_str.strip(), fmt)
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return f"{age} л."
        except ValueError: continue
    return ""

class SortableTableItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            # Пытаемся сравнить как числа (для веса или ID)
            return float(self.text().split()[0]) < float(other.text().split()[0])
        except:
            return self.text().lower() < other.text().lower()

# --- ОСНОВНОЕ ОКНО ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система учета КРС v1.5")
        self.resize(1400, 850)
        
        self.data_animals = []
        self.filters_animals = {}
        self.data_health = []
        self.filters_health = {}

        self.init_ui()

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.tabs.addTab(self.create_tab_animals(), "🐮 Картотека")
        self.tabs.addTab(self.create_tab_health(), "💊 Здоровье")
        
        # Заглушки для будущих разделов
        for name in ["🧬 Воспроизводство", "⚖️ Взвешивание"]:
            self.tabs.addTab(self.create_placeholder(f"Раздел {name} в разработке"), name)

    def create_placeholder(self, text):
        w = QWidget(); l = QVBoxLayout(); lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter); l.addWidget(lbl); w.setLayout(l)
        return w

    # --- ВКЛАДКА: КАРТОТЕКА ---
    def create_tab_animals(self):
        tab = QWidget(); layout = QVBoxLayout()
        
        # Верхняя панель поиска
        search_layout = QHBoxLayout()
        self.search_animals = QLineEdit()
        self.search_animals.setPlaceholderText("🔍 Быстрый поиск по всей базе...")
        self.search_animals.textChanged.connect(self.apply_filter_animals)
        search_layout.addWidget(self.search_animals)
        
        btn_clear = QPushButton("❌ Сбросить фильтры")
        btn_clear.clicked.connect(self.clear_animals_filters)
        search_layout.addWidget(btn_clear)
        layout.addLayout(search_layout)
        
        # Таблица
        self.table_animals = QTableWidget()
        # Все столбцы как в вашей исходной версии
        self.headers_animals = ["ID (Бирка/Чип)", "Кличка", "Пол", "Дата рожд.", "Возраст", 
                                "Порода", "Мать", "Отец", "Группа", "Статус", "Дата статуса"]
        self.table_animals.setColumnCount(len(self.headers_animals))
        self.table_animals.setHorizontalHeaderLabels(self.headers_animals)
        self.table_animals.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_animals.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        header = self.table_animals.horizontalHeader()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(lambda col: self.open_filter_dialog(col, "animals"))
        header.setStyleSheet("QHeaderView::section { background-color: #0078D7; color: white; height: 35px; }")
        
        layout.addWidget(self.table_animals)
        
        # Кнопки управления
        btn_lay = QHBoxLayout()
        btns = [("➕ Добавить", self.add_animal), ("✏️ Изменить", self.edit_animal), 
                ("🗑 Удалить", self.delete_animal), ("🔄 Обновить", self.load_animals)]
        for txt, func in btns:
            b = QPushButton(txt); b.clicked.connect(func); btn_lay.addWidget(b)
        layout.addLayout(btn_lay)
        
        tab.setLayout(layout)
        self.load_animals()
        return tab

    # --- ВКЛАДКА: ЗДОРОВЬЕ ---
    def create_tab_health(self):
        tab = QWidget(); layout = QVBoxLayout()
        
        self.search_health = QLineEdit()
        self.search_health.setPlaceholderText("🔍 Поиск по препаратам или животным...")
        self.search_health.textChanged.connect(self.apply_filter_health)
        layout.addWidget(self.search_health)
        
        self.table_health = QTableWidget()
        self.headers_health = ["Дата", "Животное (ID)", "Событие", "Препарат", "Срок действ.", "Повтор", "Примечание"]
        self.table_health.setColumnCount(len(self.headers_health))
        self.table_health.setHorizontalHeaderLabels(self.headers_health)
        
        header = self.table_health.horizontalHeader()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(lambda col: self.open_filter_dialog(col, "health"))
        header.setStyleSheet("QHeaderView::section { background-color: #2E7D32; color: white; height: 35px; }")
        
        self.table_health.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_health.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.table_health)
        
        btn_lay = QHBoxLayout()
        btns = [("➕ Добавить запись", self.add_health), ("✏️ Изменить", self.edit_health), 
                ("🗑 Удалить", self.delete_health), ("🔄 Обновить", self.load_health)]
        for txt, func in btns:
            b = QPushButton(txt); b.clicked.connect(func); btn_lay.addWidget(b)
        layout.addLayout(btn_lay)
        
        tab.setLayout(layout)
        self.load_health()
        return tab

    # --- СИСТЕМА ФИЛЬТРАЦИИ (EXCEL STYLE) ---
    def open_filter_dialog(self, col, mode):
        table = self.table_animals if mode == "animals" else self.table_health
        data = self.data_animals if mode == "animals" else self.data_health
        filter_dict = self.filters_animals if mode == "animals" else self.filters_health
        headers = self.headers_animals if mode == "animals" else self.headers_health

        unique_values = set()
        for r in data:
            disp = self.get_display_row_animals(r) if mode == "animals" else self.get_display_row_health(r)
            val = str(disp[col]).strip() if disp[col] else "(Пустые)"
            unique_values.add(val)
        
        unique_values = sorted(list(unique_values))

        dlg = QDialog(self); dlg.setWindowTitle(f"Фильтр: {headers[col]}"); l = QVBoxLayout(dlg)
        
        b_asc = QPushButton("🔼 Сортировать А-Я"); b_asc.clicked.connect(lambda: self.do_sort(table, col, Qt.AscendingOrder, dlg))
        b_desc = QPushButton("🔽 Сортировать Я-А"); b_desc.clicked.connect(lambda: self.do_sort(table, col, Qt.DescendingOrder, dlg))
        l.addWidget(b_asc); l.addWidget(b_desc)

        lw = QListWidget()
        all_it = QListWidgetItem("(Выбрать все)"); all_it.setFlags(all_it.flags() | Qt.ItemIsUserCheckable)
        all_it.setCheckState(Qt.Checked); lw.addItem(all_it)
        
        items = []
        for v in unique_values:
            it = QListWidgetItem(v); it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked if (col in filter_dict and v not in filter_dict[col]) else Qt.Checked)
            lw.addItem(it); items.append(it)
        l.addWidget(lw)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject); l.addWidget(bb)

        if dlg.exec_() == QDialog.Accepted:
            if all_it.checkState() == Qt.Checked: filter_dict.pop(col, None)
            else: filter_dict[col] = {i.text() for i in items if i.checkState() == Qt.Checked}
            self.apply_filter_animals() if mode == "animals" else self.apply_filter_health()

    def do_sort(self, table, col, order, dlg):
        table.setSortingEnabled(True); table.sortItems(col, order); table.setSortingEnabled(False); dlg.accept()

    # --- ЛОГИКА ДАННЫХ КАРТОТЕКИ ---
    def load_animals(self):
        conn = get_conn(); self.data_animals = conn.execute("SELECT * FROM animals").fetchall(); conn.close()
        self.apply_filter_animals()

    def get_display_row_animals(self, r):
        # r: (id, tag, chip, name, gender, dob, breed, mother, father, group, status, status_date, notes)
        tag, chip = r[1] or "", r[2] or ""
        ident = f"{tag} / {chip}" if (tag and chip) else (tag if tag else chip)
        return [ident, r[3], r[4], r[5], calc_age(r[5]), r[6], r[7], r[8], r[9], r[10], r[11]]

    def apply_filter_animals(self):
        self.table_animals.setRowCount(0)
        search = self.search_animals.text().lower()
        for r in self.data_animals:
            disp = self.get_display_row_animals(r)
            if search and search not in " ".join(map(str, disp)).lower(): continue
            skip = False
            for col, allowed in self.filters_animals.items():
                val = str(disp[col]).strip() if disp[col] else "(Пустые)"
                if val not in allowed: skip = True; break
            if skip: continue

            pos = self.table_animals.rowCount()
            self.table_animals.insertRow(pos)
            for i, v in enumerate(disp): self.table_animals.setItem(pos, i, SortableTableItem(str(v or "")))

    def clear_animals_filters(self):
        self.filters_animals.clear(); self.search_animals.clear(); self.apply_filter_animals()

    # --- ЛОГИКА ДАННЫХ ЗДОРОВЬЯ ---
    def load_health(self):
        conn = get_conn(); self.data_health = conn.execute("SELECT * FROM health_records").fetchall(); conn.close()
        self.apply_filter_health()

    def get_display_row_health(self, r):
        return [r[1], r[2], r[3], r[4], r[5], r[6], r[7]]

    def apply_filter_health(self):
        self.table_health.setRowCount(0)
        search = self.search_health.text().lower()
        for r in self.data_health:
            disp = self.get_display_row_health(r)
            if search and search not in " ".join(map(str, disp)).lower(): continue
            skip = False
            for col, allowed in self.filters_health.items():
                val = str(disp[col]).strip() if disp[col] else "(Пустые)"
                if val not in allowed: skip = True; break
            if skip: continue

            pos = self.table_health.rowCount()
            self.table_health.insertRow(pos)
            for i, v in enumerate(disp): self.table_health.setItem(pos, i, SortableTableItem(str(v or "")))

    # --- ДИАЛОГИ КАРТОТЕКИ (ПОЛНЫЕ) ---
    def add_animal(self): self.open_animal_dialog()
    def edit_animal(self):
        row = self.table_animals.currentRow()
        if row >= 0:
            target_ident = self.table_animals.item(row, 0).text()
            for r in self.data_animals:
                if self.get_display_row_animals(r)[0] == target_ident:
                    self.open_animal_dialog(r[0]); break

    def open_animal_dialog(self, anim_id=None):
        dlg = QDialog(self); dlg.setWindowTitle("Карточка животного"); f = QFormLayout(dlg)
        labs = ["Бирка", "Чип", "Кличка", "Пол", "Дата рождения", "Порода", "Мать (ID)", "Отец (ID)", "Группа", "Статус", "Дата статуса", "Заметки"]
        edits = {l: QLineEdit() for l in labs}
        for l in labs: f.addRow(l, edits[l])
        
        if anim_id:
            conn = get_conn(); d = conn.execute("SELECT * FROM animals WHERE id=?", (anim_id,)).fetchone(); conn.close()
            for i, l in enumerate(labs): edits[l].setText(str(d[i+1] or ""))

        def save():
            v = [edits[l].text() for l in labs]
            conn = get_conn()
            if anim_id: conn.execute("UPDATE animals SET tag=?, chip=?, name=?, gender=?, dob=?, breed=?, mother=?, father=?, group_name=?, status=?, status_date=?, notes=? WHERE id=?", v + [anim_id])
            else: conn.execute("INSERT INTO animals (tag, chip, name, gender, dob, breed, mother, father, group_name, status, status_date, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", v)
            conn.commit(); conn.close(); self.load_animals(); dlg.accept()

        btn = QPushButton("💾 Сохранить"); btn.clicked.connect(save); f.addRow(btn); dlg.exec_()

    def delete_animal(self):
        row = self.table_animals.currentRow()
        if row >= 0 and QMessageBox.question(self, "Удаление", "Удалить животное?") == QMessageBox.Yes:
            target_ident = self.table_animals.item(row, 0).text()
            conn = get_conn()
            for r in self.data_animals:
                if self.get_display_row_animals(r)[0] == target_ident:
                    conn.execute("DELETE FROM animals WHERE id=?", (r[0],)); break
            conn.commit(); conn.close(); self.load_animals()

    # --- ДИАЛОГИ ЗДОРОВЬЯ (С УМНЫМ ВЫБОРОМ ID И КНОПКОЙ ИЗМЕНИТЬ) ---
    def add_health(self): self.open_health_dialog()
    def edit_health(self):
        row = self.table_health.currentRow()
        if row >= 0:
            # Поиск записи по дате и ID животного (уникальная связка для примера)
            d_val, a_val = self.table_health.item(row, 0).text(), self.table_health.item(row, 1).text()
            for r in self.data_health:
                if r[1] == d_val and r[2] == a_val:
                    self.open_health_dialog(r[0]); break

    def open_health_dialog(self, record_id=None):
        dlg = QDialog(self); dlg.setWindowTitle("Запись о здоровье"); f = QFormLayout(dlg)
        e_date = QLineEdit(datetime.now().strftime("%d.%m.%Y"))
        
        # УМНЫЙ ВЫБОР ЖИВОТНОГО
        e_animal = QComboBox(); e_animal.setEditable(True); e_animal.setInsertPolicy(QComboBox.NoInsert)
        animal_list = sorted([self.get_display_row_animals(r)[0] for r in self.data_animals])
        e_animal.addItems(animal_list)
        
        e_type = QComboBox(); e_type.addItems(["Вакцинация", "Лечение", "Осмотр", "Витамины"])
        e_drug = QLineEdit(); e_dur = QLineEdit(); e_rep = QLineEdit(); e_note = QLineEdit()
        
        f.addRow("Дата:", e_date); f.addRow("Животное (ID):", e_animal); f.addRow("Событие:", e_type)
        f.addRow("Препарат:", e_drug); f.addRow("Срок (дней):", e_dur); f.addRow("Повтор:", e_rep); f.addRow("Примечание:", e_note)

        if record_id:
            conn = get_conn(); d = conn.execute("SELECT * FROM health_records WHERE id=?", (record_id,)).fetchone(); conn.close()
            e_date.setText(d[1]); e_animal.setCurrentText(d[2]); e_type.setCurrentText(d[3])
            e_drug.setText(d[4]); e_dur.setText(d[5]); e_rep.setText(d[6]); e_note.setText(d[7])

        def save():
            v = [e_date.text(), e_animal.currentText(), e_type.currentText(), e_drug.text(), e_dur.text(), e_rep.text(), e_note.text()]
            conn = get_conn()
            if record_id: conn.execute("UPDATE health_records SET date=?, animal_id=?, event_type=?, drug=?, duration=?, repeat_event=?, notes=? WHERE id=?", v + [record_id])
            else: conn.execute("INSERT INTO health_records (date, animal_id, event_type, drug, duration, repeat_event, notes) VALUES (?,?,?,?,?,?,?)", v)
            conn.commit(); conn.close(); self.load_health(); dlg.accept()

        btn = QPushButton("💾 Сохранить"); btn.clicked.connect(save); f.addRow(btn); dlg.exec_()

    def delete_health(self):
        row = self.table_health.currentRow()
        if row >= 0 and QMessageBox.question(self, "Удаление", "Удалить запись?") == QMessageBox.Yes:
            d_val, a_val = self.table_health.item(row, 0).text(), self.table_health.item(row, 1).text()
            conn = get_conn()
            conn.execute("DELETE FROM health_records WHERE date=? AND animal_id=?", (d_val, a_val))
            conn.commit(); conn.close(); self.load_health()

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    win = MainWindow(); win.show(); sys.exit(app.exec_())