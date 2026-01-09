import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import pyodbc
from datetime import datetime
from cryptography.fernet import Fernet
from tkcalendar import DateEntry
import base64

# =====================================================
# LICENSE CONFIG
# =====================================================
SECRET_KEY = b"xBf-2rhcZgcKbpqfSpmtzwrv78TCt9DRsvoa1-szG8I="
LICENSE_FILE = "license.json"
fernet = Fernet(SECRET_KEY)

def check_license():
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, "r") as f:
                data = json.load(f)
            expire_date = datetime.strptime(data["expire_date"], "%Y-%m-%d")
            if datetime.now() <= expire_date:
                return True
            else:
                os.remove(LICENSE_FILE)
        except:
            os.remove(LICENSE_FILE)

    code = simpledialog.askstring("License", "Enter License Code")
    if not code:
        return False

    try:
        decrypted = fernet.decrypt(base64.urlsafe_b64decode(code))
        data = json.loads(decrypted.decode())
        expire_date = datetime.strptime(data["expire_date"], "%Y-%m-%d")
        if datetime.now() > expire_date:
            return False

        with open(LICENSE_FILE, "w") as f:
            json.dump(data, f)
        return True
    except:
        messagebox.showerror("Error", "Invalid License")
        return False


# =====================================================
# CONFIG
# =====================================================
CONFIG_FILE = "config.json"

def load_server():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f).get("server", "").strip()
    return ""

def save_server(server):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"server": server}, f)


# =====================================================
# DATABASE FUNCTIONS
# =====================================================
def create_database_if_not_exists():
    server = load_server()
    conn = pyodbc.connect(
        f"DRIVER={{SQL Server}};SERVER={server};DATABASE=master;Trusted_Connection=yes;",
        autocommit=True
    )
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT name FROM sys.databases WHERE name='fingerprint_db')
        CREATE DATABASE fingerprint_db
    """)
    conn.close()

def get_connection():
    server = load_server()
    return pyodbc.connect(
        f"DRIVER={{SQL Server}};SERVER={server};DATABASE=fingerprint_db;Trusted_Connection=yes;"
    )

def initialize_database():
    create_database_if_not_exists()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='departments2')
        CREATE TABLE departments2 (
            department_id VARCHAR(50) PRIMARY KEY,
            department_name VARCHAR(200) UNIQUE NOT NULL,
            created_at DATETIME2 DEFAULT SYSDATETIME()
        )
    """)
    conn.commit()
    conn.close()


# =====================================================
# SERVER CONFIG WINDOW
# =====================================================
class ServerConfigWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Server Configuration")
        self.geometry("350x200")

        tk.Label(self, text="SQL Server Name").pack(pady=10)
        self.entry = tk.Entry(self, width=40)
        self.entry.pack()

        tk.Button(self, text="Save", command=self.save).pack(pady=20)

    def save(self):
        if not self.entry.get():
            messagebox.showwarning("Error", "Enter server name")
            return
        save_server(self.entry.get().strip())
        initialize_database()
        self.destroy()
        LoginWindow().mainloop()


# =====================================================
# LOGIN WINDOW
# =====================================================
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.geometry("300x200")

        tk.Label(self, text="Username").pack()
        self.user = tk.Entry(self)
        self.user.pack()

        tk.Label(self, text="Password").pack()
        self.pwd = tk.Entry(self, show="*")
        self.pwd.pack()

        tk.Button(self, text="Login", command=self.login).pack(pady=15)

    def login(self):
        if self.user.get() == "admin" and self.pwd.get() == "admin":
            self.destroy()
            AttendanceApp().mainloop()
        else:
            messagebox.showerror("Error", "Invalid login")


# =====================================================
# MAIN APP
# =====================================================
class AttendanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fingerprint Attendance System")
        self.geometry("1200x650")

        self.server_name = load_server()

        self.navbar = tk.Frame(self, bg="#2c3e50", width=220)
        self.navbar.pack(side="left", fill="y")

        self.content = tk.Frame(self, bg="#ecf0f1")
        self.content.pack(side="right", fill="both", expand=True)

        self.create_navbar()
        self.show_dashboard()

    def create_navbar(self):
        tk.Label(self.navbar, text="ATTENDANCE", fg="white", bg="#2c3e50",
                 font=("Arial", 16, "bold")).pack(pady=20)

        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Employees", self.show_employees),
            ("Shifts & Schedules", self.show_shifts),
            ("report impport", self.input_download_data),
            ("Reports", self.show_reports),
            ("Leave Management", self.show_leave),
            ("Payroll", self.show_payroll),
            ("Devices & Import", self.show_devices),
            ("Settings", self.show_settings),
            ("Logging", self.show_logging),
            ("Logout", self.quit)
        ]

        for text, cmd in buttons:
            tk.Button(
                self.navbar, text=text, command=cmd, anchor="w", padx=20,
                relief="flat", bg="#34495e", fg="white",
                activebackground="#1abc9c", activeforeground="white"
            ).pack(fill="x", pady=2)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        tk.Label(self.content, text="Dashboard", font=("Arial", 22), bg="#ecf0f1").pack(pady=20)

    # =====================================================
    # DEPARTMENT FUNCTIONS (FIXED)
    # =====================================================
    def save_department(self):
        if not self.dep_id.get() or not self.dep_name.get():
            messagebox.showwarning("Error", "All fields required")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO departments2 (department_id, department_name) VALUES (?, ?)",
                self.dep_id.get(), self.dep_name.get()
            )
            conn.commit()
            conn.close()

            self.dep_id.delete(0, tk.END)
            self.dep_name.delete(0, tk.END)
            self.load_departments()

        except pyodbc.IntegrityError:
            messagebox.showerror("Error", "Duplicate Department ID or Name")

    def load_departments(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT department_id, department_name FROM departments2")
        for row in cursor.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

    # =====================================================
    def show_employees(self):
        self.clear_content()

        tk.Label(self.content, text="Add Department", font=("Arial", 22),
                 bg="#ecf0f1").pack(pady=20)

        form = tk.Frame(self.content, bg="#ecf0f1")
        form.pack(pady=10)

        tk.Label(form, text="Department ID", bg="#ecf0f1").grid(row=0, column=0)
        tk.Label(form, text="Department Name", bg="#ecf0f1").grid(row=1, column=0)

        self.dep_id = tk.Entry(form, width=30)
        self.dep_name = tk.Entry(form, width=30)

        self.dep_id.grid(row=0, column=1)
        self.dep_name.grid(row=1, column=1)

        tk.Button(form, text="Save Department",
                  command=self.save_department).grid(row=2, columnspan=2, pady=10)

        table_frame = tk.Frame(self.content)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(table_frame, columns=("ID", "Name"), show="headings")
        self.tree.heading("ID", text="Department ID")
        self.tree.heading("Name", text="Department Name")
        self.tree.pack(side="left", fill="both", expand=True)

        ttk.Scrollbar(table_frame, orient="vertical",
                      command=self.tree.yview).pack(side="right", fill="y")

        self.tree.configure(yscrollcommand=self.tree.yview)
        self.load_departments()

    def show_shifts(self):
        self.clear_content()

        # ---------------- TOP FRAME ----------------
        frame = ttk.Frame(self.content)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        # ---------------- LEFT FRAME (frame3) ----------------
        frame3 = ttk.Frame(frame, relief=tk.GROOVE)
        frame3.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(frame3, text="Set Employee").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(frame3, text="Employee ID").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame3, text="Department Name").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame3, text="Employee Code").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame3, text="First Name").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame3, text="Last Name").grid(row=5, column=0, padx=5, pady=2, sticky="w")

        employee_id = ttk.Entry(frame3)
        employee_id.grid(row=1, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        # Department Combobox (real-time DB load)
        self.department_name_var = tk.StringVar()
        self.department_combo = ttk.Combobox(frame3, textvariable=self.department_name_var, state="readonly", width=30)
        self.department_combo.grid(row=2, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        def load_departments():
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT department_name FROM departments2 ORDER BY department_name")
                rows = cursor.fetchall()
                conn.close()
                return [row[0] for row in rows]
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load departments:\n{str(e)}")
                return []

        # Load initial departments
        self.department_combo["values"] = load_departments()

        def refresh_department_combobox():
            self.department_combo["values"] = load_departments()

        employee_code = ttk.Entry(frame3)
        employee_code.grid(row=3, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        first_name = ttk.Entry(frame3)
        first_name.grid(row=4, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        last_name = ttk.Entry(frame3)
        last_name.grid(row=5, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        # ---------------- Ensure employees2 table exists ----------------
        def ensure_employees_table1():
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'employees2')
                    BEGIN
                        CREATE TABLE employees2 (
                            employee_id VARCHAR(100) PRIMARY KEY,
                            department_name VARCHAR(100),
                            employee_code VARCHAR(50) NOT NULL UNIQUE,
                            first_name VARCHAR(50) NOT NULL,
                            last_name VARCHAR(50),
                            created_at DATETIME DEFAULT GETDATE()
                        )
                    END
                """)
                conn.commit()
                conn.close()
            except Exception as e:
                messagebox.showerror("Database Error", f"Error ensuring employees2 table:\n{str(e)}")

        # ---------------- Save Employee ----------------
        def save_em():
            ensure_employees_table1()

            emp_id = employee_id.get().strip()
            dep_name_val = self.department_name_var.get().strip()
            emp_code = employee_code.get().strip()
            fname = first_name.get().strip()
            lname = last_name.get().strip()

            if not emp_id or not dep_name_val or not emp_code or not fname or not lname:
                messagebox.showwarning("Input Error", "Please enter all employee details")
                return

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO employees2 (employee_id, department_name, employee_code, first_name, last_name) VALUES (?,?,?,?,?)",
                    (emp_id, dep_name_val, emp_code, fname, lname)
                )
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Employee saved successfully")

                # Clear fields
                employee_id.delete(0, tk.END)
                self.department_name_var.set("")
                employee_code.delete(0, tk.END)
                first_name.delete(0, tk.END)
                last_name.delete(0, tk.END)

                load_table1()
            except pyodbc.IntegrityError:
                messagebox.showerror("Error", "Employee ID or Code must be unique")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(frame3, text="Save Employee", width=20, command=save_em).grid(row=6, column=0, columnspan=2, pady=10)
        frame3.grid_columnconfigure(1, weight=1)

        # ---------------- RIGHT FRAME (frame4) ----------------
        frame4 = ttk.Frame(frame, relief=tk.GROOVE)
        frame4.grid(row=1, column=1, sticky="nsew")
        frame4.grid_rowconfigure(0, weight=1)
        frame4.grid_columnconfigure(0, weight=1)

        table_frame = tk.Frame(frame4, bg="#ecf0f1")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Employee ID", "Department Name", "Employee Code", "First Name", "Last Name")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # ---------------- Load employee table ----------------
        def load_table1():
            for row in self.tree.get_children():
                self.tree.delete(row)
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT employee_id, department_name, employee_code, first_name, last_name FROM employees2")
                rows = cursor.fetchall()
                conn.close()
                for r in rows:
                    self.tree.insert("", tk.END, values=r)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        load_table1()




    def input_download_data(self):
        self.clear_content()

        tk.Label(
            self.content,
            text="Shifts & Schedules",
            font=("Arial", 22),
            bg="#ecf0f1"
        ).grid(row=0, column=0, pady=20)

        # Main container
        frame = tk.Frame(self.content, bg="#ecf0f1")
        frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        # Allow resizing
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(0, minsize=300)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, minsize=200)

        # ---------------- LEFT FRAME ----------------
        frame1 = ttk.Frame(frame, relief=tk.GROOVE)
        frame1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        frame1.grid_propagate(False)

        ttk.Label(frame1, text="Set Shifts").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(frame1, text="Shift Name").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame1, text="Start Time").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame1, text="End Time").grid(row=3, column=0, padx=5, pady=2, sticky="w")

        shift_name = ttk.Entry(frame1)
        shift_name.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        start_hour = ttk.Spinbox(frame1, from_=0, to=23, width=3, format="%02.0f")
        start_min  = ttk.Spinbox(frame1, from_=0, to=59, width=3, format="%02.0f")
        start_sec  = ttk.Spinbox(frame1, from_=0, to=59, width=3, format="%02.0f")
        start_hour.grid(row=2, column=1, padx=2)
        start_min.grid(row=2, column=2, padx=2)
        start_sec.grid(row=2, column=3, padx=2)
        start_hour.set("08")
        start_min.set("00")
        start_sec.set("00")

        end_hour = ttk.Spinbox(frame1, from_=0, to=23, width=3, format="%02.0f")
        end_min  = ttk.Spinbox(frame1, from_=0, to=59, width=3, format="%02.0f")
        end_sec  = ttk.Spinbox(frame1, from_=0, to=59, width=3, format="%02.0f")
        end_hour.grid(row=3, column=1, padx=2)
        end_min.grid(row=3, column=2, padx=2)
        end_sec.grid(row=3, column=3, padx=2)
        end_hour.set("17")
        end_min.set("00")
        end_sec.set("00")

        # ---------------- Ensure shifts table exists ----------------
        def ensure_shifts_table():
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='shifts' AND xtype='U')
                    CREATE TABLE shifts (
                        shift_id INT IDENTITY(1,1) PRIMARY KEY,
                        shift_name VARCHAR(50) NOT NULL,
                        start_time TIME NOT NULL,
                        end_time TIME NOT NULL,
                        created_at DATETIME DEFAULT GETDATE()
                    )
                """)
                conn.commit()
                conn.close()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

        # ---------------- Save shift ----------------
        def save_shift():
            ensure_shifts_table()
            sname = shift_name.get().strip()
            st = f"{start_hour.get()}:{start_min.get()}:{start_sec.get()}"
            et = f"{end_hour.get()}:{end_min.get()}:{end_sec.get()}"

            if not sname:
                messagebox.showwarning("Input Error", "Please enter shift name")
                return

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO shifts (shift_name, start_time, end_time) VALUES (?, ?, ?)",
                    (sname, st, et)
                )
                conn.commit()
                conn.close()

                messagebox.showinfo("Success", "Shift saved successfully")

                # Clear fields
                shift_name.delete(0, tk.END)
                start_hour.set("08")
                start_min.set("00")
                start_sec.set("00")
                end_hour.set("17")
                end_min.set("00")
                end_sec.set("00")

                load_table()

            except Exception as e:
                messagebox.showerror("Database Error", str(e))

        tk.Button(frame1, text="Save Shift", width=20, command=save_shift)\
            .grid(row=4, column=0, columnspan=4, pady=10)
        frame1.columnconfigure(1, weight=1)

        # ---------------- RIGHT FRAME ----------------
        frame2 = ttk.Frame(frame, relief=tk.GROOVE)
        frame2.grid(row=0, column=1, sticky="nsew")
        frame2.grid_rowconfigure(0, weight=1)
        frame2.grid_columnconfigure(0, weight=1)

        table_frame = tk.Frame(frame2, bg="#ecf0f1")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Shift ID", "Shift Name", "Start Time", "End Time")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # ---------------- Load data into table ----------------
        def load_table():
            for row in self.tree.get_children():
                self.tree.delete(row)
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT shift_id, shift_name, start_time, end_time FROM shifts")
                rows = cursor.fetchall()
                conn.close()
                for r in rows:
                    self.tree.insert("", tk.END, values=r)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        load_table()




    def show_reports(self):
        self.clear_content()

        # Main container
        frame = ttk.Frame(self.content)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        # ---------------- LEFT FRAME ----------------
        frame3 = ttk.Frame(frame, relief=tk.GROOVE)
        frame3.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        frame3.grid_rowconfigure(0, weight=0)
        frame3.grid_columnconfigure(1, weight=1)

        ttk.Label(frame3, text="Assign Employee Shifts").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(frame3, text="Employee ID").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(frame3, text="Shift ID").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame3, text="Shift Date").grid(row=3, column=0, padx=5, pady=2, sticky="w")

        employee_idd = ttk.Entry(frame3)
        employee_idd.grid(row=1, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        shift_idd = ttk.Entry(frame3)
        shift_idd.grid(row=2, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        shift_date_var = tk.StringVar()
        shift_datee = ttk.Combobox(
            frame3,
            textvariable=shift_date_var,
            values=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            state="readonly",
            width=30
        )
        
        shift_datee.grid(row=3, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        # ---------------- Ensure employee_shifts2 table exists ----------------
        def ensure_employee_shifts_table():
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_NAME = 'employee_shifts2'
                    )
                    BEGIN
                        CREATE TABLE employee_shifts2 (
                            employee_shift_id INT IDENTITY(1,1) PRIMARY KEY,
                            employee_id VARCHAR(100) NOT NULL,
                            shift_id INT NOT NULL,
                            shift_date VARCHAR(100) NOT NULL,
                            CONSTRAINT fk_emp FOREIGN KEY (employee_id)
                                REFERENCES employees2(employee_id),
                            CONSTRAINT fk_shift FOREIGN KEY (shift_id)
                                REFERENCES shifts(shift_id),
                            CONSTRAINT uq_employee_shift UNIQUE (employee_id, shift_id, shift_date)
                        )
                    END
                """)
                conn.commit()
                conn.close()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

        # ---------------- Save employee shift ----------------
        def save_emm():
            ensure_employee_shifts_table()

            emp_id = employee_idd.get().strip()
            shift_id = shift_idd.get().strip()
            shift_date = shift_date_var.get().strip()

            if not emp_id or not shift_id or not shift_date:
                messagebox.showwarning("Input Error", "Please enter all shift details")
                return

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO employee_shifts2 (employee_id, shift_id, shift_date) VALUES (?, ?, ?)",
                    (emp_id, shift_id, shift_date)
                )
                conn.commit()
                conn.close()

                messagebox.showinfo("Success", "Shift assigned successfully")

                employee_idd.delete(0, tk.END)
                shift_idd.delete(0, tk.END)
                shift_date_var.set("")

                load_table2()

            except Exception as e:
                if "uq_employee_shift" in str(e):
                    messagebox.showerror("Duplicate Assignment", "This employee is already assigned to this shift on this date")
                else:
                    messagebox.showerror("Error", str(e))

        tk.Button(frame3, text="Assign Shift", width=20, command=save_emm)\
            .grid(row=4, column=0, columnspan=2, pady=10)

        # ---------------- RIGHT FRAME ----------------
        frame4 = ttk.Frame(frame, relief=tk.GROOVE)
        frame4.grid(row=0, column=1, sticky="nsew")
        frame4.grid_rowconfigure(0, weight=1)
        frame4.grid_columnconfigure(0, weight=1)

        table_frame = tk.Frame(frame4, bg="#ecf0f1")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Employee Shift ID", "Employee ID", "Shift ID", "Shift Date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # ---------------- Load table data ----------------
        def load_table2():
            for row in self.tree.get_children():
                self.tree.delete(row)
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT employee_shift_id, employee_id, shift_id, shift_date FROM employee_shifts2")
                rows = cursor.fetchall()
                conn.close()
                for r in rows:
                    self.tree.insert("", tk.END, values=r)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        load_table2()




    def show_leave(self):
        self.clear_content()

        # Main container
        frame = tk.Frame(self.content, bg="#ecf0f1")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        tk.Label(
            frame,
            text="Download Data",
            font=("Arial", 22, "bold"),
            bg="#ecf0f1"
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Instructions
        tk.Label(
            frame,
            text="Select fingerprint download file (CSV/TXT) from your device.",
            bg="#ecf0f1",
            font=("Arial", 12)
        ).grid(row=1, column=0, sticky="w", pady=(0, 10))

        # ---------------- Import Function ----------------
        def import_fingerprint_file():
            from tkinter import filedialog, messagebox
            from datetime import datetime
            import os, shutil, csv

            # Select file
            file_path = filedialog.askopenfilename(
                title="Select Fingerprint Download File",
                filetypes=[("Text & CSV Files", "*.txt *.csv"), ("All Files", "*.*")]
            )

            if not file_path:
                return  # User canceled

            try:
                # Ensure 'files' folder exists
                project_folder = os.path.dirname(os.path.abspath(__file__))
                files_folder = os.path.join(project_folder, "files")
                os.makedirs(files_folder, exist_ok=True)

                filename = os.path.basename(file_path)
                dest_path = os.path.join(files_folder, filename)
                shutil.copy(file_path, dest_path)

                # Database connection
                conn = get_connection()
                cursor = conn.cursor()

                # Create fingerprint_logs table if not exists
                cursor.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_NAME = 'fingerprint_logs'
                    )
                    BEGIN
                        CREATE TABLE fingerprint_logs (
                            log_id INT IDENTITY(1,1) PRIMARY KEY,
                            employee_code VARCHAR(50) NOT NULL,
                            log_time DATETIME NOT NULL,
                            device_type VARCHAR(50) NOT NULL,
                            log_type VARCHAR(10) NOT NULL,
                            created_at DATETIME DEFAULT GETDATE()
                        )
                    END
                """)
                conn.commit()

                inserted = 0
                skipped = 0

                # Detect file type by extension
                ext = os.path.splitext(dest_path)[1].lower()

                if ext == ".csv":
                    # ---------------- CSV Parsing ----------------
                    with open(dest_path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            employee_code = row.get("employee_code") or row.get("EmployeeCode")
                            date_str = row.get("date") or row.get("Date")
                            time_str = row.get("time") or row.get("Time")
                            inout_mode = row.get("inout_mode") or row.get("InOutMode")

                            if not employee_code or not date_str or not time_str or inout_mode is None:
                                skipped += 1
                                continue

                            try:
                                log_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                            except:
                                skipped += 1
                                continue

                            log_type = "IN" if str(inout_mode) == "0" else "OUT"

                            # Insert only if not exists
                            cursor.execute("""
                                IF NOT EXISTS (
                                    SELECT 1 FROM fingerprint_logs
                                    WHERE employee_code = ? AND log_time = ? AND log_type = ?
                                )
                                INSERT INTO fingerprint_logs (employee_code, log_time, device_type, log_type)
                                VALUES (?, ?, ?, ?)
                            """, (employee_code, log_datetime, log_type, employee_code, log_datetime, "CSV", log_type))

                            inserted += 1

                else:
                    # ---------------- TXT Parsing (ZKTeco) ----------------
                    with open(dest_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue

                            parts = line.split()
                            if len(parts) < 7:
                                skipped += 1
                                continue

                            employee_code = parts[0]
                            date_str = parts[1]
                            time_str = parts[2]
                            inout_mode = parts[5]  # 0=IN, 1=OUT

                            try:
                                log_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                            except:
                                skipped += 1
                                continue

                            log_type = "IN" if inout_mode == "0" else "OUT"

                            # Insert only if not exists
                            cursor.execute("""
                                IF NOT EXISTS (
                                    SELECT 1 FROM fingerprint_logs
                                    WHERE employee_code = ? AND log_time = ? AND log_type = ?
                                )
                                INSERT INTO fingerprint_logs (employee_code, log_time, device_type, log_type)
                                VALUES (?, ?, ?, ?)
                            """, (employee_code, log_datetime, log_type, employee_code, log_datetime, "ZKTeco", log_type))

                            inserted += 1

                conn.commit()
                conn.close()

                messagebox.showinfo(
                    "Import Complete",
                    f"File: {filename}\nInserted: {inserted}\nSkipped: {skipped}"
                )

            except Exception as e:
                messagebox.showerror("Import Error", str(e))

        # Button to browse and import
        tk.Button(
            frame,
            text="Browse and Import File",
            width=30,
            height=2,
            bg="#3498db",
            fg="white",
            font=("Arial", 12, "bold"),
            command=import_fingerprint_file
        ).grid(row=3, column=0, sticky="w", pady=(5, 0))




    def show_payroll(self): self.clear_content()
    


    def show_devices(self): self.clear_content()
    def show_settings(self): self.clear_content()
    def show_logging(self):
        self.clear_content()
        tk.Label(self.content, text=f"Connected Server: {self.server_name}",
                 font=("Arial", 14), bg="#ecf0f1").pack(pady=10)


# =====================================================
# APP START
# =====================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    if not check_license():
        exit()

    root.destroy()

    if load_server():
        initialize_database()
        LoginWindow().mainloop()
    else:
        ServerConfigWindow().mainloop()
