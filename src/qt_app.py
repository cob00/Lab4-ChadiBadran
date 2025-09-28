
import sys, re, csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QHBoxLayout, QVBoxLayout, QFormLayout, QGroupBox, QDialog
)
from PyQt5.QtCore import Qt


import db

EMAIL_RE= re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate_nonempty(text: str, field: str) -> str:
    text=(text or "").strip()
    if not text:
        raise ValueError(f"{field} must not be empty.")
    return text

def validate_age(age_str:str) -> int:
    try:
        age = int(age_str)
    except Exception:
        raise ValueError("Age must be an integer")
    if age < 0:
        raise ValueError("Age must be a positive nb")
    if age > 120:
        raise ValueError("client is not possible")
    return age

def validate_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise ValueError("Invalid email")
    return email


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("School Management System")
        self.resize(1100, 680)

        try:
            db.init_db()
        except Exception as e:
            QMessageBox.critical(self,"DB Error",f"Failed databasw:\n{e}")
            raise

        central=QWidget(self)
        self.setCentralWidget(central)
        main=QVBoxLayout(central)

        top_row=QHBoxLayout()
        main.addLayout(top_row)

        top_row.addWidget(self._build_instructor_box(), stretch=1)
        top_row.addWidget(self._build_course_box(), stretch=1)
        top_row.addWidget(self._build_student_box(), stretch=1)

        mid_row= QHBoxLayout()
        main.addLayout(mid_row)

        self.register_btn=QPushButton("Register selected Student → Course")
        self.register_btn.clicked.connect(self.register_student_to_course)
        mid_row.addWidget(self.register_btn)

        self.assign_btn=QPushButton("Assign selected Instructor → Course")
        self.assign_btn.clicked.connect(self.assign_instructor_to_course)
        mid_row.addWidget(self.assign_btn)

        mid_row.addStretch(1)
        mid_row.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("name, ID, email, course…")
        self.search_edit.textChanged.connect(self.refresh_table_filtered)
        mid_row.addWidget(self.search_edit, stretch=1)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Type",   "ID","Name","Extra"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        main.addWidget(self.table, stretch=1)

        bottom_row=QHBoxLayout()
        main.addLayout(bottom_row)

        self.edit_btn=QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_selected)
        bottom_row.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected)
        bottom_row.addWidget(self.delete_btn)

        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_csv)
        bottom_row.addWidget(self.export_btn)

        bottom_row.addStretch(1)


        self._build_menu()


        self.refresh_combos()
        self.refresh_table()

    #UI builders
    def _build_menu(self):
        bar = self.menuBar()
        file_menu = bar.addMenu("&File")

        act_backup = file_menu.addAction("Backup DB")
        act_backup.triggered.connect(self.backup_db)

        file_menu.addSeparator()
        act_quit = file_menu.addAction("Exit")
        act_quit.triggered.connect(self.close)

    def _build_instructor_box(self):
        box = QGroupBox("Instructor")
        form = QFormLayout(box)
        self.in_name = QLineEdit()
        self.in_age = QLineEdit()
        self.in_email = QLineEdit()
        self.in_id = QLineEdit()
        form.addRow("Name:",self.in_name)
        form.addRow("Age:",self.in_age)
        form.addRow("Email:",self.in_email)
        form.addRow("ID:",self.in_id)
        btn = QPushButton("Add Instructor")
        btn.clicked.connect(self.add_instructor)
        form.addRow(btn)

        self.in_selector = QComboBox()
        self.in_selector.setEditable(False)
        form.addRow("Select to assign:", self.in_selector)
        return box

    def _build_course_box(self):
        box = QGroupBox("Course")
        form = QFormLayout(box)
        self.c_id = QLineEdit()
        self.c_name = QLineEdit()
        form.addRow("Course ID:", self.c_id)
        form.addRow("Name:", self.c_name)

        btn = QPushButton("Add Course")
        btn.clicked.connect(self.add_course)
        form.addRow(btn)

        self.c_selector = QComboBox()
        self.c_selector.setEditable(False)
        form.addRow("Select Course:", self.c_selector)
        return box

    def _build_student_box(self):
        box = QGroupBox("Student")
        form = QFormLayout(box)
        self.s_name = QLineEdit()
        self.s_age = QLineEdit()
        self.s_email = QLineEdit()
        self.s_id = QLineEdit()
        form.addRow("Name:", self.s_name)
        form.addRow("Age:", self.s_age)
        form.addRow("Email:", self.s_email)
        form.addRow("ID:", self.s_id)
        btn = QPushButton("Add Student")
        btn.clicked.connect(self.add_student)
        form.addRow(btn)

        self.s_selector = QComboBox()
        self.s_selector.setEditable(False)
        form.addRow("Select Student:", self.s_selector)
        return box

# UI
    def refresh_combos(self):
        # Students selector
        self.s_selector.blockSignals(True)
        self.s_selector.clear()
        for s in db.list_students():
            self.s_selector.addItem(f"{s['id']} – {s['name']}", s['id'])
        self.s_selector.blockSignals(False)

        # Instructors selector
        self.in_selector.blockSignals(True)
        self.in_selector.clear()
        for i in db.list_instructors():
            self.in_selector.addItem(f"{i['id']} – {i['name']}", i['id'])
        self.in_selector.blockSignals(False)

        # Courses selector
        self.c_selector.blockSignals(True)
        self.c_selector.clear()
        for c in db.list_courses():
            inst_name = c['instructor_name'] if c['instructor_name'] else "None"
            self.c_selector.addItem(f"{c['id']} – {c['name']} (Instructor: {inst_name})", c['id'])
        self.c_selector.blockSignals(False)

    def refresh_table(self, filtered=None):
        self.table.setRowCount(0)

        if filtered is None:
            students= db.list_students()
            instructors= db.list_instructors()
            courses =db.list_courses()
        else:
            students =filtered.get("students", [])
            instructors = filtered.get("instructors", [])
            courses = filtered.get("courses", [])

        def add_row(type_, id_, name_, extra_, iid):
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r,0,QTableWidgetItem(type_))
            self.table.setItem(r, 1,QTableWidgetItem(id_))
            self.table.setItem(r, 2,QTableWidgetItem(name_))
            self.table.setItem(r,3, QTableWidgetItem(extra_))
            for c in range(4):
                self.table.item(r, c).setData(Qt.UserRole, iid)

        for s in students:
            add_row("Student", s["id"], s["name"], f"Age: {s['age']}, Email: {s['email']}", f"Student:{s['id']}")

        for i in instructors:
            add_row("Instructor", i["id"], i["name"], f"Age: {i['age']}, Email: {i['email']}", f"Instructor:{i['id']}")

        for c in courses:
            inst_name = c["instructor_name"] if c["instructor_name"] else "None"
            extra = f"Instructor: {inst_name}, Students: {c['enrolled_count']}"
            add_row("Course", c["id"], c["name"], extra, f"Course:{c['id']}")

    def refresh_table_filtered(self):
        q = (self.search_edit.text() or "").lower().strip()
        if not q:
            self.refresh_table()
            return
        try:
            filtered = db.search_all(q)
            self.refresh_table(filtered)
        except Exception as e:
            QMessageBox.critical(self, "Search Error", str(e))

    def add_instructor(self):
        try:
            name = validate_nonempty(self.in_name.text(), "Instructor name")
            age = validate_age(self.in_age.text())
            email = validate_email(self.in_email.text())
            iid = validate_nonempty(self.in_id.text(), "Instructor ID")
            db.create_instructor(iid, name, age, email)
            self.in_name.clear(); self.in_age.clear(); self.in_email.clear(); self.in_id.clear()
            self.refresh_combos(); self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def add_course(self):
        try:
            cid = validate_nonempty(self.c_id.text(), "Course ID")
            cname = validate_nonempty(self.c_name.text(), "Course name")
            inst_id = None
            if self.in_selector.count():
                sel_idx = self.in_selector.currentIndex()
                if sel_idx >= 0:
                    inst_id = self.in_selector.itemData(sel_idx)
            db.create_course(cid, cname, inst_id)
            self.c_id.clear(); self.c_name.clear()
            self.refresh_combos(); self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def add_student(self):
        try:
            name = validate_nonempty(self.s_name.text(), "Student name")
            age = validate_age(self.s_age.text())
            email = validate_email(self.s_email.text())
            sid = validate_nonempty(self.s_id.text(), "Student ID")
            db.create_student(sid, name, age, email)
            self.s_name.clear(); self.s_age.clear(); self.s_email.clear(); self.s_id.clear()
            self.refresh_combos(); self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def register_student_to_course(self):
        if self.s_selector.count() == 0 or self.c_selector.count() == 0:
            QMessageBox.warning(self, "Select", "You need at least one student and one course.")
            return
        sid = self.s_selector.currentData()
        cid = self.c_selector.currentData()
        try:
            db.enroll_student(sid, cid)
            self.refresh_table()
            QMessageBox.information(self, "Enrolled",
                f"{self.s_selector.currentText()} enrolled in {self.c_selector.currentText()}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def assign_instructor_to_course(self):
        if self.in_selector.count() == 0 or self.c_selector.count() == 0:
            QMessageBox.warning(self, "Select", "You need at least one instructor and one course.")
            return
        iid = self.in_selector.currentData()
        cid = self.c_selector.currentData()
        try:
            db.assign_instructor(cid, iid)
            self.refresh_combos()
            self.refresh_table()
            QMessageBox.information(self, "Assigned",
                f"{self.in_selector.currentText()} assigned to {self.c_selector.currentText()}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _selected_row_key(self):
        row = self.table.currentRow()
        if row < 0:
            return None, None
        item = self.table.item(row, 0)
        if not item:
            return None, None
        iid = item.data(Qt.UserRole)
        if not iid:
            for c in range(1, 4):
                cell = self.table.item(row, c)
                if cell:
                    iid = cell.data(Qt.UserRole)
                    if iid:
                        break
        if not iid:
            return None, None
        t, id_ = iid.split(":", 1)
        return t, id_

    def edit_selected(self):
        t, id_ = self._selected_row_key()
        if not t:
            QMessageBox.warning(self, "Select", "Select a row to edit.")
            return
        try:
            if t == "Student":
                s = next((x for x in db.list_students() if x["id"] == id_), None)
                if not s: raise ValueError("Student not found.")
                self._edit_student_dialog(s)
            elif t == "Instructor":
                i = next((x for x in db.list_instructors() if x["id"] == id_), None)
                if not i: raise ValueError("Instructor not found.")
                self._edit_instructor_dialog(i)
            elif t == "Course":
                c = next((x for x in db.list_courses() if x["id"] == id_), None)
                if not c: raise ValueError("Course not found.")
                self._edit_course_dialog(c)
            else:
                QMessageBox.critical(self, "Error", "Unknown record type.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def delete_selected(self):
        t, id_ = self._selected_row_key()
        if not t:
            QMessageBox.warning(self, "Select", "Select a row to delete.")
            return

        if QMessageBox.question(self, "Confirm", f"Delete {t} '{id_}'?") != QMessageBox.Yes:
            return

        try:
            if t == "Student":
                db.delete_student(id_)
            elif t == "Instructor":
                db.delete_instructor(id_)
            elif t == "Course":
                db.delete_course(id_)
            self.refresh_combos()
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _edit_student_dialog(self, s: dict):
        dlg = QDialog(self); dlg.setWindowTitle(f"Edit Student {s['id']}")
        layout = QFormLayout(dlg)
        name = QLineEdit(s["name"])
        age = QLineEdit(str(s["age"]))
        email = QLineEdit(s["email"])
        layout.addRow("Name:", name)
        layout.addRow("Age:", age)
        layout.addRow("Email:", email)
        row = QHBoxLayout()
        ok = QPushButton("Save"); cancel = QPushButton("Cancel")
        row.addWidget(ok); row.addWidget(cancel)
        layout.addRow(row)

        def save():
            try:
                new_name = validate_nonempty(name.text(), "Name")
                new_age = validate_age(age.text())
                new_email = validate_email(email.text())
                db.update_student(s["id"], new_name, new_age, new_email)
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(self, "Invalid data", str(e))

        ok.clicked.connect(save)
        cancel.clicked.connect(dlg.reject)

        if dlg.exec_():
            self.refresh_combos()
            self.refresh_table()

    def _edit_instructor_dialog(self, i: dict):
        dlg = QDialog(self); dlg.setWindowTitle(f"Edit Instructor {i['id']}")
        layout = QFormLayout(dlg)
        name = QLineEdit(i["name"])
        age = QLineEdit(str(i["age"]))
        email = QLineEdit(i["email"])
        layout.addRow("Name:", name)
        layout.addRow("Age:", age)
        layout.addRow("Email:", email)
        row = QHBoxLayout()
        ok = QPushButton("Save"); cancel = QPushButton("Cancel")
        row.addWidget(ok); row.addWidget(cancel)
        layout.addRow(row)

        def save():
            try:
                new_name = validate_nonempty(name.text(), "Name")
                new_age = validate_age(age.text())
                new_email = validate_email(email.text())
                db.update_instructor(i["id"], new_name, new_age, new_email)
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(self, "Invalid data", str(e))

        ok.clicked.connect(save)
        cancel.clicked.connect(dlg.reject)

        if dlg.exec_():
            self.refresh_combos()
            self.refresh_table()

    def _edit_course_dialog(self, c: dict):
        dlg = QDialog(self); dlg.setWindowTitle(f"Edit Course {c['id']}")
        layout = QFormLayout(dlg)
        name = QLineEdit(c["name"])
        layout.addRow("Name:", name)

        inst_combo = QComboBox()
        inst_combo.addItem("(None)", None)
        sel_index = 0
        idx = 1
        all_instructors = db.list_instructors()
        for ins in all_instructors:
            label = f"{ins['id']} – {ins['name']}"
            inst_combo.addItem(label, ins["id"])
            if c["instructor_id"] == ins["id"]:
                sel_index = idx
            idx += 1
        inst_combo.setCurrentIndex(sel_index)
        layout.addRow("Instructor:", inst_combo)

        row = QHBoxLayout()
        ok = QPushButton("Save"); cancel = QPushButton("Cancel")
        row.addWidget(ok); row.addWidget(cancel)
        layout.addRow(row)

        def save():
            try:
                cname = validate_nonempty(name.text(), "Course name")
                iid = inst_combo.currentData()
                db.update_course(c["id"], cname, iid)
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(self, "Invalid data", str(e))

        ok.clicked.connect(save)
        cancel.clicked.connect(dlg.reject)

        if dlg.exec_():
            self.refresh_combos()
            self.refresh_table()

    def export_csv(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Nothing to export", "No rows to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", filter="CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Type", "ID", "Name", "Extra"])
                for r in range(self.table.rowCount()):
                    row = []
                    for c in range(4):
                        item = self.table.item(r, c)
                        row.append(item.text() if item else "")
                    writer.writerow(row)
            QMessageBox.information(self, "Exported", f"Exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def backup_db(self):
        path, _ = QFileDialog.getSaveFileName(self, "Backup DB", filter="SQLite DB (*.db)")
        if not path:
            return
        try:
            db.backup_to(path)
            QMessageBox.information(self, "Backup", f"Database backed up to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", str(e))


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
