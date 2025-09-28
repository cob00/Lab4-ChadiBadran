"""
School Management System Tkinter

This app lets you create students , courses and instructors. It lets you assign an instructor for a chosen course and lets you enroll a
student to courses. You can also search for any created object in the database and extract them.
"""
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import db


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

#for the validations
def _nonempty(text:str,field:str)->str:
    """
Check that a text field is not empty.
:param text: input from user
:param field: name of the field (used in error messages).
:raises ValueError: If the field is left blank.
:return: The trimmed text.
"""

    t= (text or "").strip()
    if not t:raise ValueError(f"{field} must not be empty.")
    return t

def _age(text:str) -> int:
    """
Turn a string into an integer.
:param text: input age.
:raises ValueError: If it’s not a number, negative, or too large (>120).
:return: Age as an int.
"""

    try:
        a=int(text)
    except Exception:
        raise ValueError("Age must be an integer")
    if a<0: raise ValueError("Age must be non-negative")
    if a>120: raise ValueError("too old")
    return a

def _email(text:str)->str:
    """
check if email is valid
:param text: The input text
:raises ValueError: If the format is wrong.
:return: email as string.
"""

    t=(text or "").strip().lower()
    if not EMAIL_RE.match(t):
        raise ValueError("Invalid email")
    return t

# functions here
def add_instructor():
    """
Adds a new instructor named as the input.
Makes sure the name, email and age are correct and the ID is unique,
then stores the instructor in the database and updates the lists.
"""

    try:
        name=_nonempty(in_name.get(), "Instructor name")
        age =_age(in_age.get())
        email=_email(in_email.get())
        iid   = _nonempty(in_id.get(), "Instructor ID")

        if any(i["id"]== iid for i in db.list_instructors()):
            raise ValueError("Instructor ID already exists.")

        db.create_instructor(iid, name, age, email)
        in_name.set(""); in_age.set(""); in_email.set(""); in_id.set("")
        refresh_instructors_listbox()
        refresh_courses_listbox()
        refresh_tree()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def add_course():
    """
Add a new course.

If an instructor is selected with a course it will be linked to them.
Checks that the course ID is unique before saving.
"""

    try:
        cid   =_nonempty(c_id.get(), "Course ID")
        cname= _nonempty(c_name.get(), "Course name")

        inst_id = None
        sel =lb_instructors.curselection()
        if sel:
            iid =lb_instructors.get(sel[0]).split(" – ")[0]
            inst_id= iid


        if any(c["id"] ==cid for c in db.list_courses()):
            raise ValueError("Course ID already exists.")

        db.create_course(cid, cname, inst_id)
        c_id.set(""); c_name.set("")
        refresh_courses_listbox()
        refresh_tree()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def add_student():
    """
Add a new student from the input fields.

checks the data and makes sure different ids,
then saves to the database and updates the lists.
"""

    try:
        name =_nonempty(s_name.get(), "Student name")
        age = _age(s_age.get())
        email =_email(s_email.get())
        sid  = _nonempty(s_id.get(), "Student ID")

        if any(s["id"] == sid for s in db.list_students()):
            raise ValueError("Student ID already exists.")

        db.create_student(sid, name, age, email)
        s_name.set(""); s_age.set(""); s_email.set(""); s_id.set("")
        refresh_students_listbox()
        refresh_tree()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def enroll_student_dialog():
    """
lets you enroll selected student to course from a dropdown menu when clicked.
student is then linked to course in database
"""

    if not lb_students.curselection():
        messagebox.showwarning("Select", "Select a student first.")
        return

    sid=lb_students.get(lb_students.curselection()[0]).split(" – ")[0]
    if not db.list_courses():
        messagebox.showwarning("No courses", "Create a course first.")
        return

    win= tk.Toplevel(root); win.title(f"Enroll {sid}"); win.grab_set()
    tk.Label(win, text=f"Enroll student {sid} into:").grid(row=0, column=0, padx=10, pady=(10, 4), sticky="w")


    course_rows= db.list_courses()
    display =[f"{c['id']} – {c['name']}" for c in course_rows]
    chosen= tk.StringVar(value=display[0])
    cb =ttk.Combobox(win, textvariable=chosen, values=display, state="readonly", width=40)
    cb.grid(row=1, column=0, padx=10, pady=4, sticky="we")

    def do_enroll():
        sel_text = chosen.get()
        if not sel_text:
            messagebox.showwarning("Pick a course", "Choose a course."); return
        cid= sel_text.split(" – ")[0]
        db.enroll_student(sid, cid)
        refresh_tree()
        messagebox.showinfo("Enrolled", f"Student {sid} enrolled in {cid}")
        win.destroy()

    btns = tk.Frame(win); btns.grid(row=2, column=0, padx=10, pady=(6, 10), sticky="e")
    tk.Button(btns, text="Cancel", command=win.destroy).pack(side="right", padx=(6, 0))
    tk.Button(btns, text="Enroll", command=do_enroll).pack(side="right")

def assign_instructor_dialog():
    """
lets you assign selected instuctor to course from a dropdown menu when clicked.
the instructor becomes responsible for that course.
"""

    if not lb_instructors.curselection():
        messagebox.showwarning("Select", "Select an instructor first.")
        return

    iid =lb_instructors.get(lb_instructors.curselection()[0]).split(" – ")[0]
    if not db.list_courses():
        messagebox.showwarning("No courses", "Create a course first.")
        return

    win= tk.Toplevel(root); win.title(f"Assign {iid}"); win.grab_set()
    tk.Label(win, text=f"Assign instructor {iid} to:").grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

    course_rows = db.list_courses()
    display= [f"{c['id']} – {c['name']}" for c in course_rows]
    chosen =tk.StringVar(value=display[0])
    cb =ttk.Combobox(win, textvariable=chosen, values=display, state="readonly", width=40)
    cb.grid(row=1, column=0, padx=10, pady=5, sticky="we")

    def do_assign():
        sel_text = chosen.get()
        if not sel_text:
            messagebox.showwarning("Pick a course", "Choose a course."); return
        cid = sel_text.split(" – ")[0]
        db.assign_instructor(cid, iid)
        refresh_courses_listbox()
        refresh_tree()
        messagebox.showinfo("Assigned", f"Instructor {iid} assigned to {cid}")
        win.destroy()

    btns = tk.Frame(win); btns.grid(row=2, column=0, padx=10, pady=(6, 10), sticky="e")
    tk.Button(btns, text="Cancel", command=win.destroy).pack(side="right", padx=(6, 0))
    tk.Button(btns, text="Assign", command=do_assign).pack(side="right")

def view_enrolled_dialog():
    """
Shows all students enrolled in the selected course.
Opens a small window with a listbox. If no students are enrolled,
it shows same message.
"""

    if not lb_courses.curselection():
        messagebox.showwarning("Select", "Select a course first.")
        return
    cid = lb_courses.get(lb_courses.curselection()[0]).split(" – ")[0]
    enrolled = db.list_enrolled(cid)

    win= tk.Toplevel(root); win.title(f"Enrolled in {cid}"); win.grab_set()
    lst= tk.Listbox(win, width=42, height=10); lst.pack(padx=10, pady=10)
    if enrolled:
        for s in enrolled:
            lst.insert(tk.END, f"{s['id']} – {s['name']}")
    else:
        lst.insert(tk.END, "(No students)")
    tk.Button(win, text="Close", command=win.destroy).pack(pady=(0, 10))

def refresh_courses_listbox():
    """
refresh the course listbox and shows data of courses.
"""

    lb_courses.delete(0, tk.END)
    for c in db.list_courses():
        inst_name = c["instructor_name"] or "None"
        lb_courses.insert(tk.END, f"{c['id']} – {c['name']} (Instructor: {inst_name})")

def refresh_students_listbox():
        """
refresh the students listbox and shows data of students."""  
        lb_students.delete(0, tk.END)
        for s in db.list_students():
            lb_students.insert(tk.END, f"{s['id']} – {s['name']}")

def refresh_instructors_listbox():
        """
refresh the instructors listbox and shows data of instructors.
""" 
        lb_instructors.delete(0, tk.END)
        for i in db.list_instructors():
            lb_instructors.insert(tk.END, f"{i['id']} – {i['name']}")

def refresh_tree(records=None):
    """
Rebuild the tree view with students, instructors, and courses.

If no records are passed, it loads everything from the database.
If a filtered dict is given, it displays only those.
"""

    tree.delete(*tree.get_children())

    if records is None:
        students_= {s["id"]: s for s in db.list_students()}
        instructors_= {i["id"]: i for i in db.list_instructors()}
        courses_ = {c["id"]: c for c in db.list_courses()}
    else:
        students_   = records.get("students", {})
        instructors_ = records.get("instructors", {})
        courses_     = records.get("courses", {})

  
    for sid, s in students_.items():
        tree.insert("", "end", iid=f"Student:{sid}",
                    values=("Student", s["id"], s["name"], f"Email: {s['email']}"))

   
    for iid, i in instructors_.items():
        tree.insert("", "end", iid=f"Instructor:{iid}",
                    values=("Instructor", i["id"], i["name"], f"Email: {i['email']}"))

    
    for cid, c in courses_.items():
        extra = f"Instructor: {c.get('instructor_name') or 'None'}, Students: {c.get('enrolled_count', 0)}"
        tree.insert("", "end", iid=f"Course:{cid}",
                    values=("Course", c["id"], c["name"], extra))

def search_records():
    """
Search across all the data and find input.

If empty, resets the tree to show everything.
"""

    q = search_var.get().lower().strip()
    if not q:
        refresh_tree(); return
    res = db.search_all(q)
    filtered = {
        "students":   {s["id"]: s for s in res["students"]},
        "instructors": {i["id"]: i for i in res["instructors"]},
        "courses":     {c["id"]: c for c in res["courses"]},
    }
    refresh_tree(filtered)

def delete_selected():
    """
Delete the selected student, instructor, or course.

Asks for confirmation before removing from the database.
Afterwards, updates all lists and the tree.
"""

    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a record to delete."); return

    row_iid = sel[0]
    rec_type, rec_id = row_iid.split(":", 1)

    if not messagebox.askyesno("Confirm delete", f"Delete {rec_type} '{rec_id}'?"):
        return

    if rec_type== "Student":
        db.delete_student(rec_id)
    elif rec_type== "Instructor":
        db.delete_instructor(rec_id)
    elif rec_type== "Course":
        pass
        db.delete_course(rec_id)

    refresh_students_listbox()
    refresh_instructors_listbox()
    refresh_courses_listbox()
    refresh_tree()

def edit_selected():
    """
Opens a window for the selected data where you can change data relating to it.

different fields show up depending on type
you can change fields and save them back to the database.
"""

    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a record to edit.")
        return

    row_iid =sel[0]
    rec_type,rec_id = row_iid.split(":", 1)

    win = tk.Toplevel(root)
    win.title(f"Edit {rec_type} {rec_id}")
    win.grab_set()

    ROW =0
    def row(label):
        nonlocal ROW
        tk.Label(win, text=label).grid(row=ROW, column=0, sticky="e", padx=10, pady=6)
        ROW += 1
    def add_entry(var):
        e = tk.Entry(win, textvariable=var, width=32)
        e.grid(row=ROW-1, column=1, padx=10, pady=6)
        return e

    if rec_type ==    "Student":
        s = next((x for x in db.list_students() if x["id"] == rec_id), None)
        if not s: messagebox.showerror("Error","Student not found"); win.destroy(); return
        name_var  = tk.StringVar(value=s["name"])
        age_var = tk.StringVar(value=str(s["age"]))
        email_var = tk.StringVar(value=s["email"])

        row("Name");  add_entry(name_var)
        row("Age");   add_entry(age_var)
        row("Email"); add_entry(email_var)

        def save_changes():
            try:
                db.update_student(rec_id,
                                  _nonempty(name_var.get(), "Name"),
                                  _age(age_var.get()),
                                  _email(email_var.get()))
            except Exception as e:
                messagebox.showerror("Invalid data", str(e)); return
            refresh_students_listbox(); refresh_tree(); win.destroy()

    elif rec_type=="Instructor":
        i = next((x for x in db.list_instructors() if x["id"] == rec_id), None)
        if not i: messagebox.showerror("Error","Instructor not found"); win.destroy(); return
        name_var  = tk.StringVar(value=i["name"])
        age_var = tk.StringVar(value=str(i["age"]))
        email_var= tk.StringVar(value=i["email"])

        row("Name");  add_entry(name_var)
        row("Age");   add_entry(age_var)
        row("Email"); add_entry(email_var)

        def save_changes():
            try:
                db.update_instructor(rec_id,
                                     _nonempty(name_var.get(), "Name"),
                                     _age(age_var.get()),
                                     _email(email_var.get()))
            except Exception as e:
                messagebox.showerror("Invalid data", str(e)); return
            refresh_instructors_listbox(); refresh_courses_listbox(); refresh_tree(); win.destroy()

    elif rec_type == "Course":
        c = next((x for x in db.list_courses() if x["id"] == rec_id), None)
        if not c: messagebox.showerror("Error","Course not found"); win.destroy(); return
        name_var = tk.StringVar(value=c["name"])

        row("Course name"); add_entry(name_var)

        row("Instructor")
        options = ["(None)"] + [f"{i['id']} – {i['name']}" for i in db.list_instructors()]
        current = "(None)" if not c["instructor_id"] else f"{c['instructor_id']} – {c['instructor_name']}"
        chosen = tk.StringVar(value=current)
        cb = ttk.Combobox(win, textvariable=chosen, values=options, state="readonly", width=30)
        cb.grid(row=ROW-1, column=1, padx=10, pady=6)

        def save_changes():
            new_name = _nonempty(name_var.get(), "Course name")
            sel = chosen.get()
            new_inst_id = None if sel == "(None)" else sel.split(" – ")[0]
            try:
                db.update_course(rec_id, new_name, new_inst_id)
            except Exception as e:
                messagebox.showerror("Invalid data", str(e)); return
            refresh_courses_listbox(); refresh_tree(); win.destroy()

    else:
        messagebox.showerror("Error", "Record not found."); win.destroy(); return

    tk.Button(win, text="Save", command=save_changes).grid(row=ROW, column=0, columnspan=2, pady=(4, 10))

def backup_db():
    """
Save a copy of the SQLite database to a file chosen by the user.

Shows a success message if the backup works, otherwise an error.
"""

    path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB","*.db")], title="Backup Database")
    if not path: return
    try:
        db.backup_to(path)
        messagebox.showinfo("Backup", f"Database copied to {path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# this is the GUI part
db.init_db()

root = tk.Tk()
root.title("School Management System")

root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)

# Menu
menubar= tk.Menu(root)
filemenu =tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Backup DB", command=backup_db)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)
root.config(menu=menubar)

# Display of instructor
fr_in = tk.LabelFrame(root, text="Instructor")
in_name, in_age, in_email, in_id = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
tk.Label(fr_in, text="Name").grid(row=0, column=0); tk.Entry(fr_in, textvariable=in_name).grid(row=0, column=1)
tk.Label(fr_in, text="Age").grid(row=1, column=0); tk.Entry(fr_in, textvariable=in_age).grid(row=1, column=1)
tk.Label(fr_in, text="Email").grid(row=2, column=0); tk.Entry(fr_in, textvariable=in_email).grid(row=2, column=1)
tk.Label(fr_in, text="ID").grid(row=3, column=0); tk.Entry(fr_in, textvariable=in_id).grid(row=3, column=1)
tk.Button(fr_in, text="Add Instructor", command=add_instructor).grid(row=4, column=0, columnspan=2, pady=4)
lb_instructors = tk.Listbox(fr_in, width=35, height=5); lb_instructors.grid(row=5, column=0, columnspan=2)
tk.Button(fr_in, text="Assign selected instructor", command=assign_instructor_dialog)\
    .grid(row=6, column=0, columnspan=2, pady=4)
fr_in.grid(row=0, column=0, padx=10, pady=10)

# Display of courses
fr_c = tk.LabelFrame(root, text="Course")
c_id, c_name = tk.StringVar(), tk.StringVar()
tk.Label(fr_c, text="Course ID").grid(row=0, column=0); tk.Entry(fr_c, textvariable=c_id).grid(row=0, column=1)
tk.Label(fr_c, text="Name").grid(row=1, column=0); tk.Entry(fr_c, textvariable=c_name).grid(row=1, column=1)
tk.Button(fr_c, text="Add Course", command=add_course).grid(row=2, column=0, columnspan=2, pady=4)
lb_courses = tk.Listbox(fr_c, width=50, height=6); lb_courses.grid(row=3, column=0, columnspan=2)
tk.Button(fr_c, text="View enrolled students", command=view_enrolled_dialog).grid(row=4, column=0, columnspan=2, pady=(6,0))
fr_c.grid(row=0, column=1, padx=10, pady=10)

# Display of student
fr_s = tk.LabelFrame(root, text="Student")
s_name, s_age, s_email, s_id = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
tk.Label(fr_s, text="Name").grid(row=0, column=0); tk.Entry(fr_s, textvariable=s_name).grid(row=0, column=1)
tk.Label(fr_s, text="Age").grid(row=1, column=0); tk.Entry(fr_s, textvariable=s_age).grid(row=1, column=1)
tk.Label(fr_s, text="Email").grid(row=2, column=0); tk.Entry(fr_s, textvariable=s_email).grid(row=2, column=1)
tk.Label(fr_s, text="ID").grid(row=3, column=0); tk.Entry(fr_s, textvariable=s_id).grid(row=3, column=1)
tk.Button(fr_s, text="Add Student", command=add_student).grid(row=4, column=0, columnspan=2, pady=4)
lb_students = tk.Listbox(fr_s, width=35, height=6); lb_students.grid(row=5, column=0, columnspan=2)
tk.Button(fr_s, text="Enroll selected student…", command=enroll_student_dialog).grid(row=6, column=0, columnspan=2, pady=(6,0))
fr_s.grid(row=0, column=2, padx=10, pady=10)

# Display of tree
fr_records = tk.LabelFrame(root, text="All Records")
fr_records.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

search_var = tk.StringVar()
tk.Label(fr_records, text="Search:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
tk.Entry(fr_records, textvariable=search_var, width=30).grid(row=0, column=1, padx=5, pady=5, sticky="we")
tk.Button(fr_records, text="Search", command=lambda: search_records()).grid(row=0, column=2, padx=5, pady=5)

columns = ("Type", "ID", "Name", "Extra")
tree = ttk.Treeview(fr_records, columns=columns, show="headings", height=10)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=180, stretch=True)
tree.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

scroll_y = ttk.Scrollbar(fr_records, orient="vertical", command=tree.yview)
tree.configure(yscroll=scroll_y.set)
scroll_y.grid(row=1, column=3, sticky="ns")

scroll_x = ttk.Scrollbar(fr_records, orient="horizontal", command=tree.xview)
tree.configure(xscroll=scroll_x.set)
scroll_x.grid(row=2, column=0, columnspan=3, sticky="ew")

def _on_tree_double_click(_evt):
    """
you can use double click to select

When a row is double-clicked, it opens the edit box
for that student, instructor, or course.
"""

    if tree.selection():
        edit_selected()
tree.bind("<Double-1>", _on_tree_double_click)

tk.Button(fr_records, text="Edit", command=lambda: edit_selected()).grid(row=3, column=0, pady=6)
tk.Button(fr_records, text="Delete", command=lambda: delete_selected()).grid(row=3, column=1, pady=6)
tk.Button(fr_records, text="Refresh", command=lambda: refresh_tree()).grid(row=3, column=2, pady=6)

fr_records.grid_rowconfigure(1, weight=1)
fr_records.grid_columnconfigure(1, weight=1)

# Prime the UI from DB
refresh_students_listbox()
refresh_instructors_listbox()
refresh_courses_listbox()
refresh_tree()

root.mainloop()
