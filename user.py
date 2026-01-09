import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import pyodbc
import shutil
from tkinter import filedialog, messagebox
from datetime import datetime
from cryptography.fernet import Fernet
import base64

# =====================================================
# LICENSE CONFIG (HARD-CODED)
# =====================================================
SECRET_KEY = b"xBf-2rhcZgcKbpqfSpmtzwrv78TCt9DRsvoa1-szG8I="
LICENSE_FILE = "license.json"

fernet = Fernet(SECRET_KEY)

# =====================================================
# LICENSE CHECK (ASK ONLY ONCE UNTIL EXPIRE)
# =====================================================
def check_license():
    # If license exists, validate it
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, "r") as f:
                data = json.load(f)

            expire_date = datetime.strptime(data["expire_date"], "%Y-%m-%d")
            if datetime.now() <= expire_date:
                return True
            else:
                messagebox.showerror("License Expired", "Your license has expired.")
                os.remove(LICENSE_FILE)
        except Exception:
            os.remove(LICENSE_FILE)

    # Ask license ONLY ONCE
    license_code = simpledialog.askstring(
        "License Required",
        "Enter License Code:",
        parent=None
    )

    if not license_code:
        return False

    try:
        token = base64.urlsafe_b64decode(license_code.encode())
        decrypted = fernet.decrypt(token)
        data = json.loads(decrypted.decode())

        expire_date = datetime.strptime(data["expire_date"], "%Y-%m-%d")
        if datetime.now() > expire_date:
            messagebox.showerror("Invalid License", "License already expired.")
            return False

        with open(LICENSE_FILE, "w") as f:
            json.dump(data, f)

        return True

    except Exception:
        messagebox.showerror("Invalid License", "License code is invalid.")
        return False


# =====================================================
# APP CONFIG
# =====================================================
CONFIG_FILE = "config.json"

def load_server():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("server", "").strip()
        except:
            return ""
    return ""

def get_connection():
    server_name = load_server()
    if not server_name:
        raise Exception("Server name not configured.")
    conn_str = f"DRIVER={{SQL Server}};SERVER={server_name};DATABASE=fingerprint_db;Trusted_Connection=yes;"
    return pyodbc.connect(conn_str)

# =====================================================
# SERVER CONFIG WINDOW
# =====================================================
class ServerConfigWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Server Configuration")
        self.geometry("400x220")
        self.resizable(False, False)

        tk.Label(self, text="SQL Server Name").pack(pady=10)
        self.server_entry = tk.Entry(self, width=45)
        self.server_entry.pack(pady=5)

        tk.Button(self, text="Save & Continue", command=self.save).pack(pady=20)

    def save(self):
        server = self.server_entry.get().strip()
        if not server:
            messagebox.showwarning("Error", "Server name required")
            return
        with open(CONFIG_FILE, "w") as f:
            json.dump({"server": server}, f, indent=4)
        self.destroy()
        LoginWindow().mainloop()

# =====================================================
# LOGIN WINDOW
# =====================================================
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.geometry("400x250")

        tk.Label(self, text="Username").pack(pady=10)
        self.user = tk.Entry(self)
        self.user.pack()

        tk.Label(self, text="Password").pack(pady=10)
        self.pwd = tk.Entry(self, show="*")
        self.pwd.pack()

        tk.Button(self, text="Login", command=self.login).pack(pady=20)

    def login(self):
        if self.user.get() == "admin" and self.pwd.get() == "admin":
            self.destroy()
            AttendanceApp().mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")

# =====================================================
# MAIN APP
# =====================================================
class AttendanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fingerprint Attendance System")
        self.geometry("1200x650")

        self.server_name = load_server()

        # Layout frames
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
            btn = tk.Button(self.navbar, text=text, command=cmd, anchor="w", padx=20,
                            relief="flat", bg="#34495e", fg="white",
                            activebackground="#1abc9c", activeforeground="white")
            btn.pack(fill="x", pady=2)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        tk.Label(self.content, text="Dashboard", font=("Arial", 22), bg="#ecf0f1").pack(pady=20)

    # ---------------- Employees Page ----------------
    def show_employees(self):
        self.clear_content()

        # Title
        tk.Label(
            self.content,
            text="Employees",
            font=("Arial", 22),
            bg="#ecf0f1"
        ).grid(row=0, column=0, columnspan=2, pady=20)

        # Main container frame
        frame = tk.Frame(self.content, bg="#ecf0f1")
        frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        # Allow resizing
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Configure columns for left & right sections
        frame.grid_columnconfigure(0, minsize=300)  # LEFT WIDTH
        frame.grid_columnconfigure(1, weight=1)     # RIGHT EXPANDS
        frame.grid_rowconfigure(0, minsize=200)     # HEIGHT

        # ---------------- LEFT SIDE (FORM) ----------------
        frame1 = ttk.Frame(frame, relief=tk.GROOVE)
        frame1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Prevent auto-resize
        frame1.grid_propagate(False)

        #333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333
        ttk.Label(frame1, text="Set Departments").grid(
            row=0, column=0, padx=(5,5), pady=(5,2), sticky="w"
        )
        #-------------------------------------------------------------------------------------------------------------------

        ttk.Label(frame1, text="Department ID").grid(row=1, column=0, padx=(5,5), pady=(2,2), sticky="w")
        ttk.Label(frame1, text="Department Name").grid(row=2, column=0, padx=(5,5), pady=(2,2), sticky="w")

        dep_id = ttk.Entry(frame1)
        dep_id.grid(row=1, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        dep_name = ttk.Entry(frame1)
        dep_name.grid(row=2, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        #///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        def ensure_departments_table():
            """
            Ensure that the 'departments2' table exists in the database.
            If it doesn't exist, create it automatically.
            """
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # Check if table exists
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'departments2')
                    BEGIN
                        CREATE TABLE departments2 (
                            department_id VARCHAR(100) PRIMARY KEY,
                            department_name VARCHAR(200) NOT NULL UNIQUE,
                            created_at DATETIME2 DEFAULT SYSDATETIME()
                        )
                    END
                """)
                conn.commit()
                conn.close()
            except Exception as e:
                messagebox.showerror("Database Error", f"Error ensuring departments2 table:\n{str(e)}")


        def save_employee():
            ensure_departments_table()  # make sure table exists

            depid = dep_id.get().strip()
            depname = dep_name.get().strip()

            if not depid or not depname:
                messagebox.showwarning("Input Error", "Please enter all department details")
                return

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO [departments2] (department_id, department_name) VALUES (?, ?)",
                    (depid, depname)
                )
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Department saved successfully")

                # Clear Entry fields
                dep_id.delete(0, tk.END)
                dep_name.delete(0, tk.END)

                # Reload table to show new data
                load_table()

            except ValueError:
                messagebox.showerror("Error", "Department ID must be unique")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(frame1, text="Save Department", width=20, command=save_employee).grid(
            row=3, column=0, columnspan=2, pady=10
        )
            
        
        #-----------------------------------------------------------------------------------------------------------------

        # Make the Entry expand horizontally
        frame1.grid_columnconfigure(1, weight=0)

        # ---------------- RIGHT SIDE (EMPTY FOR NOW) ----------------
        #frame2 = ttk.Frame(frame, relief=tk.GROOVE)
        #frame2.grid(row=0, column=1, sticky="nsew")
        frame2 = ttk.Frame(frame, relief=tk.GROOVE)
        frame2.grid(row=0, column=1, sticky="nsew")
        frame2.grid_rowconfigure(0, weight=1)
        frame2.grid_columnconfigure(0, weight=1)

        # Table with scrollbar
        table_frame = tk.Frame(frame2, bg="#ecf0f1")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Department ID", "Department Name")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscroll=scrollbar.set)

        # ---------------- Load data into table ----------------
        def load_table():
            # Clear existing rows
            for row in self.tree.get_children():
                self.tree.delete(row)

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT department_id, department_name FROM departments2")
                rows = cursor.fetchall()
                conn.close()

                for r in rows:
                    self.tree.insert("", tk.END, values=r)

            except Exception as e:
                messagebox.showerror("Error", str(e))

        load_table()
    # Key points*******************************************************************************************************************************
        
        # ---------------- BOTTOM LEFT (frame3) ----------------
        frame3 = ttk.Frame(frame, relief=tk.GROOVE)
        frame3.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        # Example content for frame3
        ttk.Label(frame3, text="Set Employee").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(frame3, text="Employee ID").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame3, text="Department Name").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame3, text="Employee Code").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame3, text="First Name").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame3, text="Last Name").grid(row=5, column=0, padx=5, pady=2, sticky="w")

        employee_id = ttk.Entry(frame3)
        employee_id.grid(row=1, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        department_name = tk.StringVar()

# Fetch department names from the database
       # ---------- Department Combobox (Real-time DB load) ----------

# StringVar (DO NOT rename)
        self.department_name_var = tk.StringVar()

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

        # Create Combobox
        self.department_combo = ttk.Combobox(
            frame3,
            textvariable=self.department_name_var,
            values=load_departments(),
            state="readonly",
            width=30
        )

        self.department_combo.grid(
            row=2,
            column=1,
            padx=(2, 5),
            pady=(2, 2),
            sticky="ew"
        )

        # Call this function AFTER insert/update/delete department
        def refresh_department_combobox():
            self.department_combo["values"] = load_departments()


        employee_code = ttk.Entry(frame3)
        employee_code.grid(row=3, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        first_name = ttk.Entry(frame3)
        first_name.grid(row=4, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        last_name = ttk.Entry(frame3)
        last_name.grid(row=5, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        def ensure_employees_table1():
            """
            Ensure that the 'employees2' table exists.
            If it does not exist, create it automatically.
            """
            try:
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_NAME = 'employees2'
                    )
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
                messagebox.showerror(
                    "Database Error",
                    f"Error ensuring employees2 table:\n{str(e)}"
                )




        def save_em():
            ensure_employees_table1()
            

            employeeid = employee_id.get().strip()
            departmentname=department_name.get().strip()
            employeecode=employee_code.get().strip()
            firstname=first_name.get().strip()
            lastname=last_name.get().strip()


            if not employeeid or not departmentname or not employeecode or not firstname or not lastname:
                messagebox.showwarning("Input Error", "Please enter all employee details")
                return

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO [employees2] (employee_id,department_name,employee_code,first_name,last_name) VALUES (?,?,?,?,?)",
                    (employeeid,departmentname,employeecode,firstname,lastname)
                )
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "employee saved successfully")

                # Clear Entry fields
                employeeid.delete(0, tk.END)
                departmentname.delete(0, tk.END)
                employeecode.delete(0, tk.END)
                firstname.delete(0, tk.END)
                lastname.delete(0, tk.END)

                # Reload table to show new data
                load_table1()

            except ValueError:
                messagebox.showerror("Error", "Department ID must be unique")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(frame3, text="Save Employee", width=20, command=save_em).grid(
            row=6, column=0, columnspan=2, pady=10
        )

       
        # Make columns expand
        frame3.grid_columnconfigure(1, weight=1)


        # ---------------- BOTTOM RIGHT (frame4) ----------------
        frame4 = ttk.Frame(frame, relief=tk.GROOVE)
        frame4.grid(row=1, column=1, sticky="nsew")
        frame4.grid_rowconfigure(0, weight=1)
        frame4.grid_columnconfigure(0, weight=1)

        # Example content for frame4
        #////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        table_frame = tk.Frame(frame4, bg="#ecf0f1")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("employee id", "Department Name", "Employee Code", "First Name", "Last Name")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscroll=scrollbar.set)

        # ---------------- Load data into table ----------------
        def load_table1():
            # Clear existing rows
            for row in self.tree.get_children():
                self.tree.delete(row)

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT employee_id,department_name,employee_code,first_name,last_name FROM [employees2]")
                rows = cursor.fetchall()
                conn.close()

                for r in rows:
                    self.tree.insert("", tk.END, values=r)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        load_table1()



        #//////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    # ---------------- Other Pages ----------------
    def show_shifts(self):
        self.clear_content()

        # Title (use grid, not pack)
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

        # Configure grid for frame
        frame.grid_columnconfigure(0, minsize=300)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, minsize=200)

        # ---------------- LEFT FRAME ----------------
        frame1 = ttk.Frame(frame, relief=tk.GROOVE)
        frame1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        frame1.grid_propagate(False)

        ttk.Label(frame1, text="Set shifts").grid(row=0, column=0, padx=(5,5), pady=(5,2), sticky="w")
        ttk.Label(frame1, text="Shift Name").grid(row=1, column=0, padx=(5,5), pady=(2,2), sticky="w")
        ttk.Label(frame1, text="Start time").grid(row=2, column=0, padx=(5,5), pady=(2,2), sticky="w")
        ttk.Label(frame1, text="end time").grid(row=3, column=0, padx=(5,5), pady=(2,2), sticky="w")

        shift_name = ttk.Entry(frame1)
        shift_name.grid(row=1, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        start_hour = ttk.Spinbox(frame1, from_=0, to=23, width=3, format="%02.0f")
        start_min  = ttk.Spinbox(frame1, from_=0, to=59, width=3, format="%02.0f")
        start_sec  = ttk.Spinbox(frame1, from_=0, to=59, width=3, format="%02.0f")

        start_hour.grid(row=2, column=1, padx=2)
        start_min.grid(row=2, column=2, padx=2)
        start_sec.grid(row=2, column=3, padx=2)

        # Default values
        start_hour.set("08")
        start_min.set("00")
        start_sec.set("00")

        # ---------------- End Time Spinboxes ----------------
        end_hour = ttk.Spinbox(frame1, from_=0, to=23, width=3, format="%02.0f")
        end_min  = ttk.Spinbox(frame1, from_=0, to=59, width=3, format="%02.0f")
        end_sec  = ttk.Spinbox(frame1, from_=0, to=59, width=3, format="%02.0f")

        end_hour.grid(row=3, column=1, padx=2)
        end_min.grid(row=3, column=2, padx=2)
        end_sec.grid(row=3, column=3, padx=2)

        # Default values
        end_hour.set("17")
        end_min.set("00")
        end_sec.set("00")

        def ensure_shifts_table():
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

           # ---------------- Save shift function ----------------
        def save_shift():
            ensure_shifts_table()  # make sure table exists

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

            except Exception as e:
                messagebox.showerror("Database Error", str(e))
                

        # ---------------- Create button ----------------
        # Place this **outside** the try/except and outside any other function
        tk.Button(frame1,text="Save Shift",width=20,command=save_shift).grid(row=4,column=0,columnspan=4,pady=10)


        frame1.columnconfigure(1, weight=1)

        


        # ---------------- RIGHT FRAME ----------------
        #frame2 = ttk.Frame(frame, relief=tk.GROOVE)
        #frame2.grid(row=0, column=1, sticky="nsew")
        frame2 = ttk.Frame(frame, relief=tk.GROOVE)
        frame2.grid(row=0, column=1, sticky="nsew")
        frame2.grid_rowconfigure(0, weight=1)
        frame2.grid_columnconfigure(0, weight=1)

        # Table container
        table_frame = tk.Frame(frame2, bg="#ecf0f1")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Correct column names
        columns = ("Shift ID", "Shift Name", "Start Time", "End Time")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # ---------------- Load data into table ----------------
        def load_table():
            # Clear existing rows
            for row in self.tree.get_children():
                self.tree.delete(row)

            try:
                conn = get_connection()
                cursor = conn.cursor()

                # ✅ FIXED SQL QUERY
                cursor.execute("""
                    SELECT shift_id, shift_name, start_time, end_time
                    FROM shifts
                """)

                rows = cursor.fetchall()
                conn.close()

                for r in rows:
                    self.tree.insert("", tk.END, values=r)

            except Exception as e:
                messagebox.showerror("Error", str(e))

        load_table()

        #*****************************************************************************************************************************
        frame3 = ttk.Frame(frame, relief=tk.GROOVE)
        frame3.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        # Example content for frame3
        ttk.Label(frame3, text="set employee shits").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(frame3, text="employee ID").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(frame3, text="Shift ID").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(frame3, text="shift date").grid(row=3, column=0, padx=5, pady=2, sticky="w")
       

        employee_idd = ttk.Entry(frame3)
        employee_idd.grid(row=1, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        shift_idd = ttk.Entry(frame3)
        shift_idd.grid(row=2, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        shift_datee = tk.StringVar()

# Fetch department names from the database
        

        
        # Create the Combobox with the department names
        shift_datee = ttk.Combobox(
            frame3,
            textvariable=shift_datee,
            values=["Monday","tuesday","wendsday","thursday","friday","saturday","sunday"],  # Use values from the database
            state="readonly",
            width=30
        )
        shift_datee.grid(row=3, column=1, padx=(2,5), pady=(2,2), sticky="ew")

        #**************************************************************************************************************************
        def ensure_employee_shifts_table():
            """
            Create employee_shifts2 table if it does not exist.
            If it exists, do nothing.
            """
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

#***************************************************************************************************************************

        def save_emm():
            ensure_employee_shifts_table()

            employeeidd = employee_idd.get().strip()
            shiftidd = shift_idd.get().strip()
            shiftdatee = shift_datee.get().strip()

            if not employeeidd or not shiftidd or not shiftdatee:
                messagebox.showwarning(
                    "Input Error",
                    "Please enter all shift details"
                )
                return

            try:
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO employee_shifts2
                    (employee_id, shift_id, shift_date)
                    VALUES (?, ?, ?)
                """, (employeeidd, shiftidd, shiftdatee))

                conn.commit()
                conn.close()

                messagebox.showinfo("Success", "Shift assigned successfully")

                # Clear fields
                employee_idd.delete(0, tk.END)
                shift_idd.delete(0, tk.END)
                shift_datee.delete(0, tk.END)

                # Optional refresh
                load_table2()

            except Exception as e:
                if "uq_employee_shift" in str(e):
                    messagebox.showerror(
                        "Duplicate Assignment",
                        "This employee is already assigned to this shift on this date"
                    )
                else:
                    messagebox.showerror("Error", str(e))

        tk.Button(frame3, text="assign user", width=20, command=save_emm).grid(
            row=4, column=0, columnspan=2, pady=10
        )

       
        # Make columns expand
        frame3.grid_columnconfigure(1, weight=1)


        #*************************************************************************************************************************************

        frame4 = ttk.Frame(frame, relief=tk.GROOVE)
        frame4.grid(row=1, column=1, sticky="nsew")
        frame4.grid_rowconfigure(0, weight=1)
        frame4.grid_columnconfigure(0, weight=1)

        # Example content for frame4
        #////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        table_frame = tk.Frame(frame4, bg="#ecf0f1")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("employee shift id", "employee id", "shift id", "shift date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscroll=scrollbar.set)

        # ---------------- Load data into table ----------------
        def load_table2():
            # Clear existing rows
            for row in self.tree.get_children():
                self.tree.delete(row)

            try:
                conn = get_connection()
                cursor = conn.cursor()

                # ✅ FIXED SQL QUERY
                cursor.execute("""
                    SELECT employee_shift_id, employee_id, shift_id, shift_date
                    FROM employee_shifts2
                """)

                rows = cursor.fetchall()
                conn.close()

                for r in rows:
                    self.tree.insert("", tk.END, values=r)

            except Exception as e:
                messagebox.showerror("Error", str(e))

        load_table2()


        
      #*****************************************************************************************************************************************  
    def input_download_data(self):
        self.clear_content()
       



        frame = tk.Frame(self.content, bg="#ecf0f1")
        frame.grid(row=0, column=0, sticky="nw", padx=20, pady=20)  # align top-left

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

        #///////////////////////////////////////////////////////////////////////////////////////////////////////////
        def import_fingerprint_file():
            from tkinter import filedialog, messagebox
            from datetime import datetime
            import os, shutil

            # ---------------- Select file ----------------
            file_path = filedialog.askopenfilename(
                title="Select Fingerprint Download File",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )

            if not file_path:
                return  # User canceled

            try:
                # ---------------- Ensure 'files' folder ----------------
                project_folder = os.path.dirname(os.path.abspath(__file__))
                files_folder = os.path.join(project_folder, "files")
                os.makedirs(files_folder, exist_ok=True)

                filename = os.path.basename(file_path)
                dest_path = os.path.join(files_folder, filename)
                shutil.copy(file_path, dest_path)

                # ---------------- DB connection ----------------
                conn = get_connection()
                cursor = conn.cursor()

                # ---------------- Create table ONLY if not exists ----------------
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

                # ---------------- Read REAL ZKTeco file ----------------
                with open(dest_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        # REAL FORMAT (space-separated)
                        # 12 2025-12-20 17:10:07 1 5 1 0
                        parts = line.split()

                        if len(parts) < 7:
                            skipped += 1
                            continue

                        employee_code = parts[0]
                        date_str = parts[1]
                        time_str = parts[2]
                        inout_mode = parts[5]  # 0=IN, 1=OUT

                        try:
                            log_datetime = datetime.strptime(
                                f"{date_str} {time_str}",
                                "%Y-%m-%d %H:%M:%S"
                            )
                        except:
                            skipped += 1
                            continue

                        log_type = "IN" if inout_mode == "0" else "OUT"

                        # Optional: prevent duplicates
                        cursor.execute("""
                            IF NOT EXISTS (
                                SELECT 1 FROM fingerprint_logs
                                WHERE employee_code = ?
                                AND log_time = ?
                                AND log_type = ?
                            )
                            BEGIN
                                INSERT INTO fingerprint_logs
                                (employee_code, log_time, device_type, log_type)
                                VALUES (?, ?, ?, ?)
                            END
                        """, (
                            employee_code, log_datetime, log_type,
                            employee_code, log_datetime, "ZKTeco", log_type
                        ))

                        inserted += 1

                conn.commit()
                conn.close()

                messagebox.showinfo(
                    "Import Complete",
                    f"File: {filename}\nInserted: {inserted}\nSkipped: {skipped}"
                )

            except Exception as e:
                messagebox.showerror("Import Error", str(e))

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


#**********************************************************************************************************************************************

    def show_reports(self):
        self.clear_content()
        tk.Label(self.content, text="Reports", font=("Arial", 22), bg="#ecf0f1").pack(pady=20)

    def show_leave(self):
        self.clear_content()
        tk.Label(self.content, text="Leave Management", font=("Arial", 22), bg="#ecf0f1").pack(pady=20)

    def show_payroll(self):
        self.clear_content()
        tk.Label(self.content, text="Payroll Attendance", font=("Arial", 22), bg="#ecf0f1").pack(pady=20)

    def show_devices(self):
        self.clear_content()
        tk.Label(self.content, text="Devices & Import", font=("Arial", 22), bg="#ecf0f1").pack(pady=20)

    def show_settings(self):
        self.clear_content()
        tk.Label(self.content, text="Settings", font=("Arial", 22), bg="#ecf0f1").pack(pady=20)

    def show_logging(self):
        self.clear_content()
        tk.Label(self.content, text="Logging", font=("Arial", 22), bg="#ecf0f1").pack(pady=20)
        tk.Label(self.content, text=f"Connected Server: {self.server_name}", font=("Arial", 14), bg="#ecf0f1").pack(pady=10)

# =====================================================
# APP START
# =====================================================
if __name__ == "__main__":
    temp = tk.Tk()
    temp.withdraw()

    if not check_license():
        exit()

    temp.destroy()

    if load_server():
        LoginWindow().mainloop()
    else:
        ServerConfigWindow().mainloop()
