import psycopg2
import psycopg2.extras
import os
import sys
from typing import Optional
import os

class DatabaseManager:
    """Hotel Management Database Manager Class"""
    
    def __init__(self):
        """
        Initialize Database Manager
        
        Reads PostgreSQL connection parameters from environment variables:
        - DB_HOST
        - DB_PORT
        - DB_NAME
        - DB_USER
        - DB_PASSWORD
        """
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'hotel_manage')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', 'postgres')
        self.connection: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extensions.cursor] = None
    
    def connect(self) -> bool:
        """
        Connect to PostgreSQL database
        
        Returns:
            Connection success status
        """
        try:
            self.connection = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            print(f"Database connection successful: {self.db_name}@{self.db_host}:{self.db_port}")
            return True
        except psycopg2.Error as e:
            print(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")
    
    def execute_query(self, query: str, params: tuple = ()):
        """
        Execute SQL query
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query result
        """
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            if self.connection:
                self.connection.rollback()
            print(f"Query execution error: {e}")
            return None
    
    def create_tables(self):
        """Create basic tables"""
        try:
            # Check and update existing table structure
            try:
                self.cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'tbl_employeer'
                """)
                columns = [col[0] if isinstance(col, tuple) else col['column_name'] for col in self.cursor.fetchall()]
                
                if columns and 'telegram_user_id' not in columns:
                    # Drop and recreate existing table
                    self.cursor.execute("DROP TABLE IF EXISTS tbl_employeer CASCADE")
                    self.connection.commit()
            except Exception as e:
                print(f"ℹ️ Column check skipped: {e}")
                if self.connection:
                    self.connection.rollback()
            
            # Employee table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_employeer (
                    employee_id TEXT PRIMARY KEY,
                    telegram_user_id BIGINT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Room table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    room_id SERIAL PRIMARY KEY,
                    room_number TEXT UNIQUE NOT NULL,
                    room_type TEXT NOT NULL,
                    price REAL NOT NULL,
                    status TEXT DEFAULT 'available'
                )
            """)
            
            # Reservation table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id SERIAL PRIMARY KEY,
                    room_id INTEGER,
                    guest_name TEXT NOT NULL,
                    check_in DATE NOT NULL,
                    check_out DATE NOT NULL,
                    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
                )
            """)
            
            # Work history table (attendance management)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_work_history (
                    id SERIAL PRIMARY KEY,
                    telegram_user_id BIGINT NOT NULL,
                    department TEXT NOT NULL,
                    name TEXT NOT NULL,
                    work_date DATE NOT NULL,
                    check_in_time TIME,
                    check_out_time TIME,
                    status INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(telegram_user_id, work_date)
                )
            """)
            
            # Add check_out_time column if not exists
            try:
                self.cursor.execute("ALTER TABLE tbl_work_history ADD COLUMN IF NOT EXISTS check_out_time TIME")
                self.connection.commit()
                print("✅ check_out_time column added to tbl_work_history")
            except Exception as e:
                if self.connection:
                    self.connection.rollback()
                # Column already exists or other error
            
            # Complaints table (employee complaints/reports)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_complaints (
                    id SERIAL PRIMARY KEY,
                    telegram_user_id BIGINT NOT NULL,
                    department TEXT NOT NULL,
                    name TEXT NOT NULL,
                    complaint_date DATE NOT NULL,
                    complaint_text TEXT NOT NULL,
                    media_type TEXT,
                    media_file_id TEXT,
                    confirmed INTEGER DEFAULT 0,
                    confirmed_by BIGINT,
                    confirmed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Daily duty check table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_duty_check (
                    id SERIAL PRIMARY KEY,
                    check_date DATE NOT NULL,
                    admin_id BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'pending'
                )
            """)
            
            # Daily duty responses table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_duty_response (
                    id SERIAL PRIMARY KEY,
                    duty_check_id INTEGER NOT NULL,
                    telegram_user_id BIGINT NOT NULL,
                    name TEXT NOT NULL,
                    response INTEGER DEFAULT 0,
                    responded_at TIMESTAMP,
                    FOREIGN KEY (duty_check_id) REFERENCES tbl_duty_check(id)
                )
            """)
            
            # Work roles table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_work_roles (
                    id SERIAL PRIMARY KEY,
                    role_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Hotel settings table for room management configuration
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_hotel_settings (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    total_rooms INTEGER DEFAULT 0,
                    hotel_name TEXT DEFAULT 'Hotel',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (id = 1)
                )
            """)
            
            # Hotel rooms table (non-guest rooms: meeting rooms, offices, storage, etc.)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_hotel_rooms (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    state INTEGER NOT NULL DEFAULT 1,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Key history table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_key_history (
                    id SERIAL PRIMARY KEY,
                    room_id INTEGER NOT NULL,
                    room_name TEXT NOT NULL,
                    person_name TEXT NOT NULL,
                    person_telegram_id BIGINT,
                    purpose TEXT NOT NULL,
                    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    taken_photo TEXT,
                    taken_video TEXT,
                    returned_at TIMESTAMP,
                    returned_photo TEXT,
                    returned_video TEXT,
                    status TEXT NOT NULL DEFAULT 'Opened',
                    created_by BIGINT,
                    FOREIGN KEY (room_id) REFERENCES tbl_hotel_rooms(id),
                    CHECK (status IN ('Opened', 'Returned', 'Delayed'))
                )
            """)
            
            # Hotel tools table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_hotel_tools (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    total_quantity INTEGER NOT NULL DEFAULT 1,
                    available_quantity INTEGER NOT NULL DEFAULT 1,
                    state INTEGER NOT NULL DEFAULT 1,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tool history table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_tool_history (
                    id SERIAL PRIMARY KEY,
                    tool_id INTEGER NOT NULL,
                    tool_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    person_name TEXT NOT NULL,
                    person_telegram_id BIGINT,
                    purpose TEXT NOT NULL,
                    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    taken_photo TEXT,
                    taken_video TEXT,
                    returned_at TIMESTAMP,
                    returned_photo TEXT,
                    returned_video TEXT,
                    status TEXT NOT NULL DEFAULT 'Opened',
                    created_by BIGINT,
                    FOREIGN KEY (tool_id) REFERENCES tbl_hotel_tools(id),
                    CHECK (status IN ('Opened', 'Returned', 'Delayed'))
                )
            """)
            
            # Transportation table (vehicles management)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_hotel_transportations (
                    id SERIAL PRIMARY KEY,
                    plate_number TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    description TEXT,
                    state INTEGER DEFAULT 1,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (vehicle_type IN ('Car', 'Van', 'Truck', 'Bus', 'Motorcycle', 'Other'))
                )
            """)
            
            # Storage table (food, chemicals, tool room, shop management)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_hotel_storages (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    storage_type TEXT NOT NULL,
                    description TEXT,
                    state INTEGER DEFAULT 1,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (storage_type IN ('Food', 'Chemicals', 'ToolRoom', 'Shop', 'Other'))
                )
            """)
            
            # External Service Contacts table (electrician, heating, internet, etc.)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_out_contacts (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    contact_type TEXT NOT NULL,
                    email TEXT NOT NULL,
                    whatsapp TEXT NOT NULL,
                    description TEXT,
                    state INTEGER DEFAULT 1,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (contact_type IN ('Electrician', 'Heating', 'Internet', 'PPService', 'PestControl', 'Taxi', 'Other'))
                )
            """)
            
            # Vehicle Usage table (transportation usage records like key management)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_vehicle_usage (
                    id SERIAL PRIMARY KEY,
                    vehicle_id INTEGER NOT NULL,
                    driver_id INTEGER NOT NULL,
                    driver_name TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    start_mileage INTEGER,
                    end_mileage INTEGER,
                    borrowed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    returned_at TIMESTAMP,
                    inspection_status TEXT,
                    inspection_notes TEXT,
                    inspection_photo TEXT,
                    status TEXT DEFAULT 'Borrowed',
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vehicle_id) REFERENCES tbl_hotel_transportations(id),
                    CHECK (status IN ('Borrowed', 'Returned', 'Overdue'))
                )
            """)
            
            # Clean history table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_clean_history (
                    id SERIAL PRIMARY KEY,
                    room_id INTEGER,
                    room_number TEXT NOT NULL,
                    floor INTEGER,
                    clean_type TEXT NOT NULL,
                    clean_status TEXT NOT NULL DEFAULT 'Completed',
                    condition TEXT,
                    notes TEXT,
                    photo TEXT,
                    video TEXT,
                    cleaned_by BIGINT NOT NULL,
                    cleaned_by_name TEXT NOT NULL,
                    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    clean_date DATE DEFAULT (CURRENT_DATE),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES tbl_hotel_rooms(id),
                    CHECK (clean_type IN ('guest_room', 'staff_room', 'common_area')),
                    CHECK (clean_status IN ('Completed', 'Partial', 'Skipped', 'Issue'))
                )
            """)
            
            # Reception Shift Settings table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_reception_shift (
                    id SERIAL PRIMARY KEY,
                    shift_count INTEGER NOT NULL DEFAULT 2,
                    shift_1_start TEXT DEFAULT '00:00',
                    shift_1_end TEXT DEFAULT '12:00',
                    shift_2_start TEXT DEFAULT '12:00',
                    shift_2_end TEXT DEFAULT '24:00',
                    shift_3_start TEXT,
                    shift_3_end TEXT,
                    shift_4_start TEXT,
                    shift_4_end TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Shift Reports table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_shift_reports (
                    id SERIAL PRIMARY KEY,
                    shift_number INTEGER NOT NULL,
                    shift_date DATE DEFAULT (CURRENT_DATE),
                    employee_id TEXT NOT NULL,
                    employee_name TEXT NOT NULL,
                    reservations_count INTEGER DEFAULT 0,
                    arrivals_count INTEGER DEFAULT 0,
                    departures_count INTEGER DEFAULT 0,
                    issues_notes TEXT,
                    cash_amount REAL DEFAULT 0,
                    cash_photo TEXT,
                    pos_report_photo TEXT,
                    store_stock_notes TEXT,
                    restaurant_cash_confirmed INTEGER DEFAULT 0,
                    key_log_notes TEXT,
                    tool_log_notes TEXT,
                    additional_notes TEXT,
                    status TEXT DEFAULT 'pending',
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_by BIGINT,
                    confirmed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES tbl_employeer(employee_id),
                    CHECK (status IN ('pending', 'submitted', 'confirmed', 'rejected'))
                )
            """)
            
            # Employee Shifts Assignment table (for A/B/C shift rotation)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_employee_shifts (
                    id SERIAL PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    telegram_user_id BIGINT NOT NULL,
                    employee_name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    shift_type TEXT NOT NULL,
                    effective_date DATE DEFAULT (CURRENT_DATE),
                    is_active INTEGER DEFAULT 1,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES tbl_employeer(employee_id),
                    CHECK (shift_type IN ('A', 'B', 'C', 'FIXED', 'NONE')),
                    CHECK (department IN ('Reception', 'Restaurant'))
                )
            """)
            
            # Initialize hotel settings if empty
            self.cursor.execute("SELECT COUNT(*) FROM tbl_hotel_settings")
            result = self.cursor.fetchone()

            check_settings = result[0] if result else False
            if check_settings == 0:
                self.cursor.execute("INSERT INTO tbl_hotel_settings (id, total_rooms, hotel_name) VALUES (1, 0, 'Hotel')")
                self.connection.commit()
                print("✅ Hotel settings initialized")
            
            # Add work_role column to tbl_employeer if not exists
            try:
                self.cursor.execute("ALTER TABLE tbl_employeer ADD COLUMN IF NOT EXISTS work_role TEXT")
                print("✅ work_role column added to tbl_employeer")
            except:
                pass  # Column already exists
            
            # Add AI analysis settings columns to tbl_hotel_settings
            try:
                self.cursor.execute("ALTER TABLE tbl_hotel_settings ADD COLUMN IF NOT EXISTS ai_analysis_enabled INTEGER DEFAULT 0")
                print("✅ ai_analysis_enabled column added to tbl_hotel_settings")
            except:
                pass  # Column already exists
            
            try:
                self.cursor.execute("ALTER TABLE tbl_hotel_settings ADD COLUMN IF NOT EXISTS email_notifications_enabled INTEGER DEFAULT 0")
                print("✅ email_notifications_enabled column added to tbl_hotel_settings")
            except:
                pass  # Column already exists
            
            try:
                self.cursor.execute("ALTER TABLE tbl_hotel_settings ADD COLUMN IF NOT EXISTS whatsapp_notifications_enabled INTEGER DEFAULT 0")
                print("✅ whatsapp_notifications_enabled column added to tbl_hotel_settings")
            except:
                pass  # Column already exists
            
            # Hotel Events table (for banquet/event booking management)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_hotel_events (
                    id SERIAL PRIMARY KEY,
                    event_name TEXT NOT NULL,
                    hall TEXT NOT NULL,
                    event_date DATE NOT NULL,
                    event_time TIME NOT NULL,
                    end_time TIME,
                    seats INTEGER NOT NULL,
                    price REAL NOT NULL DEFAULT 0,
                    menu TEXT,
                    meals_count INTEGER NOT NULL DEFAULT 0,
                    notes TEXT,
                    status TEXT NOT NULL DEFAULT 'scheduled',
                    created_by BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'on_hold'))
                )
            """)
            
            # Hotel Event History table (tracking confirmations and alarms)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_hotel_event_history (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    department TEXT NOT NULL,
                    alarm_type TEXT NOT NULL,
                    alarm_sent_at TIMESTAMP,
                    acknowledged INTEGER DEFAULT 0,
                    acknowledged_by BIGINT,
                    acknowledged_at TIMESTAMP,
                    confirmed INTEGER DEFAULT 0,
                    confirmed_by BIGINT,
                    confirmed_at TIMESTAMP,
                    ready_confirmed INTEGER DEFAULT 0,
                    ready_confirmed_by BIGINT,
                    ready_confirmed_at TIMESTAMP,
                    ready_proof TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES tbl_hotel_events(id),
                    CHECK (alarm_type IN ('T-2', 'T-1', 'event_day'))
                )
            """)
            
            # Hotel Event User Notifications table (tracking individual user notifications)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_hotel_event_user_notifications (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    telegram_user_id BIGINT NOT NULL,
                    alarm_type TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES tbl_hotel_events(id),
                    CHECK (alarm_type IN ('T-2', 'T-1', 'event_day')),
                    UNIQUE (event_id, telegram_user_id, alarm_type)
                )
            """)
            
            # Tasks table (must be created before tbl_hotel_event_tasks due to FK constraint)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_tasks (
                    id SERIAL PRIMARY KEY,
                    Date DATE NOT NULL,
                    department TEXT,
                    assignee_id BIGINT NOT NULL,
                    assignee_name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'Normal',
                    due_date TEXT NOT NULL,
                    is_materials INTEGER NOT NULL DEFAULT 0,
                    is_check INTEGER NOT NULL DEFAULT 0,
                    is_perform INTEGER NOT NULL,
                    proof_path TEXT NOT NULL,
                    check_admin INTEGER NOT NULL DEFAULT 0,
                    created_by BIGINT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    attachment TEXT,
                    report_attachment TEXT,
                    report_notes TEXT
                )
            """)
            
            # Add overdue_notified_date column if not exists
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS overdue_notified_date DATE")
            
            # Add enhanced workflow columns to tbl_tasks
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending'")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS started_at TIMESTAMP")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS proof_required INTEGER DEFAULT 0")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS proof_type TEXT")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS proof_submitted INTEGER DEFAULT 0")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS rejected_by BIGINT")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS rejection_reason TEXT")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS escalated INTEGER DEFAULT 0")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMP")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS escalated_to BIGINT")
            self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS task_type TEXT DEFAULT 'general'")
            
            # Task status history table for audit trail
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_task_status_history (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL,
                    task_table TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    changed_by BIGINT NOT NULL,
                    changed_by_name TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            """)
            
            # Action history table (for logging user actions)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_action_history (
                    id SERIAL PRIMARY KEY,
                    telegram_user_id BIGINT NOT NULL,
                    employee_id TEXT,
                    employee_name TEXT NOT NULL,
                    department TEXT,
                    action_type TEXT NOT NULL,
                    action_detail TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Hotel Event Tasks table (auto-generated tasks for each department)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_hotel_event_tasks (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    task_id INTEGER,
                    department TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    due_date DATE NOT NULL,
                    assigned_to BIGINT,
                    assigned_name TEXT,
                    status TEXT DEFAULT 'pending',
                    accepted_at TIMESTAMP,
                    accepted_by BIGINT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    completed_by BIGINT,
                    proof_photo TEXT,
                    report_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES tbl_hotel_events(id),
                    FOREIGN KEY (task_id) REFERENCES tbl_tasks(id),
                    CHECK (status IN ('pending', 'accepted', 'in_progress', 'completed', 'confirmed', 'cancelled'))
                )
            """)
            
            # Migrate tbl_hotel_event_tasks - add new columns if they don't exist
            event_task_columns = {
                'assigned_to': 'INTEGER',
                'assigned_name': 'TEXT',
                'accepted_at': 'TIMESTAMP',
                'accepted_by': 'INTEGER',
                'started_at': 'TIMESTAMP',
                'completed_at': 'TIMESTAMP',
                'completed_by': 'INTEGER',
                'proof_photo': 'TEXT',
                'report_notes': 'TEXT',
                'confirmed_at': 'TIMESTAMP',
                'confirmed_by': 'TEXT'
            }
            
            for col_name, col_type in event_task_columns.items():
                try:
                    self.cursor.execute(f"ALTER TABLE tbl_hotel_event_tasks ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
                    print(f"✅ Added {col_name} column to tbl_hotel_event_tasks")
                except psycopg2.OperationalError:
                    pass  # Column already exists
            
            # Email logs table (track all sent emails with enhanced logging)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_email_logs (
                    id SERIAL PRIMARY KEY,
                    recipient TEXT NOT NULL,
                    recipient_name TEXT,
                    subject TEXT NOT NULL,
                    status TEXT NOT NULL,
                    smtp_response_code INTEGER,
                    smtp_response_message TEXT,
                    error_message TEXT,
                    sender_email TEXT,
                    sender_name TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_by_user_id BIGINT,
                    email_size_bytes INTEGER,
                    CHECK (status IN ('sent', 'failed', 'queued'))
                )
            """)
            
            # Add new columns to existing tbl_email_logs if they don't exist
            email_log_columns = {
                'recipient_name': 'TEXT',
                'smtp_response_code': 'INTEGER',
                'smtp_response_message': 'TEXT',
                'sender_email': 'TEXT',
                'sender_name': 'TEXT',
                'sent_by_user_id': 'BIGINT',
                'email_size_bytes': 'INTEGER'
            }
            
            for col_name, col_type in email_log_columns.items():
                try:
                    self.cursor.execute(f"ALTER TABLE tbl_email_logs ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
                except psycopg2.OperationalError:
                    pass  # Column already exists
            
            # Update CHECK constraint to include 'queued' status
            try:
                self.cursor.execute("""
                    ALTER TABLE tbl_email_logs DROP CONSTRAINT IF EXISTS tbl_email_logs_status_check
                """)
                self.cursor.execute("""
                    ALTER TABLE tbl_email_logs ADD CONSTRAINT tbl_email_logs_status_check 
                    CHECK (status IN ('sent', 'failed', 'queued'))
                """)
            except psycopg2.Error:
                pass  # Constraint already exists or can't be modified
            
            # WhatsApp logs table (track all sent WhatsApp messages)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_whatsapp_logs (
                    id SERIAL PRIMARY KEY,
                    recipient TEXT NOT NULL,
                    recipient_name TEXT,
                    message_body TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message_sid TEXT,
                    error_message TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (status IN ('sent', 'failed'))
                )
            """)
            
            # WhatsApp credentials table (encrypted storage)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_whatsapp_credentials (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    account_sid_encrypted BYTEA,
                    auth_token_encrypted BYTEA,
                    whatsapp_from_encrypted BYTEA,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (id = 1)
                )
            """)
            
            self.connection.commit()
        except psycopg2.Error as e:
            print(f"Table creation error: {e}")
            if self.connection:
                self.connection.rollback()
    
    def check_admin(self, telegram_user_id: int) -> bool:
        """
        Check admin permission by Telegram user ID
        
        Args:
            telegram_user_id: Telegram user ID (update.effective_user.id)
            
        Returns:
            Admin status (True: Management department, False: others)
        """
        try:
            self.cursor.execute(
                "SELECT department FROM tbl_employeer WHERE telegram_user_id = %s",
                (telegram_user_id,)
            )

            result = self.cursor.fetchone()
            
            if result and result[0] == "Management":
                print(f"✅ Admin authentication successful: Telegram User ID {telegram_user_id}")
                return True
            
            print(f"❌ No admin permission: Telegram User ID {telegram_user_id}")
            return False
        except psycopg2.Error as e:
            print(f"Admin check error: {e}")
            return False
    
    def get_employee_info(self, telegram_user_id: int):
        """
        Get employee info by Telegram user ID
        
        Args:
            telegram_user_id: Telegram user ID (update.effective_user.id)
            
        Returns:
            Employee info dict {'employee_id', 'name', 'department', 'work_role', 'gmail', 'whatsapp'} or None
        """
        try:
            self.cursor.execute(
                "SELECT employee_id, name, department, work_role, gmail, whatsapp FROM tbl_employeer WHERE telegram_user_id = %s",
                (telegram_user_id,)
            )

            result = self.cursor.fetchone()
            
            if result:
                print(f"✅ Employee info retrieved: {result}")
                return {
                    'employee_id': result[0],
                    'name': result[1],
                    'department': result[2],
                    'work_role': result[3],
                    'gmail': result[4],
                    'whatsapp': result[5]
                }
            else:
                print(f"❌ Unregistered user: Telegram User ID {telegram_user_id}")
                return None
        except psycopg2.Error as e:
            print(f"Employee info retrieval error: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def get_employee_info_by_telegram_id(self, telegram_user_id: int):
        """
        Alias for get_employee_info - Get employee info by Telegram user ID
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            Employee info dict {'employee_id', 'name', 'department', 'work_role'} or None
        """
        return self.get_employee_info(telegram_user_id)
    
    def get_all_admins(self):
        """
        Get all admin users (Management department)
        
        Returns:
            List of admin telegram_user_id tuples
        """
        try:
            results = self.cursor.execute(
                "SELECT telegram_user_id FROM tbl_employeer WHERE department = 'Management' AND telegram_user_id IS NOT NULL"
            )
            results = self.cursor.fetchall()
            print(f"✅ Admins retrieved: {len(results)} admin(s)")
            return results
        except psycopg2.Error as e:
            print(f"Get all admins error: {e}")
            return []
    
    def get_departments(self, exclude_management: bool = True):
        """
        Get department list
        
        Args:
            exclude_management: Whether to exclude Management department
            
        Returns:
            Department list [(id, name, content), ...]
        """
        try:
            if exclude_management:
                self.cursor.execute(
                    "SELECT id, name, content FROM tbl_department WHERE name != 'Management' ORDER BY id"
                )
                result = self.cursor.fetchall()
            else:
                self.cursor.execute(
                    "SELECT id, name, content FROM tbl_department ORDER BY id"
                )
                result = self.cursor.fetchall()
            
            print(f"✅ Department list retrieved: {len(result)} items")
            return result
        except psycopg2.Error as e:
            if self.connection:
                self.connection.rollback()
            print(f"Department list retrieval error: {e}")
            return []
    
    def get_email_logs(self, limit: int = 50):
        """
        Get email logs
        
        Args:
            limit: Number of logs to retrieve (default: 50)
            
        Returns:
            List of email logs [(id, recipient, subject, status, error_message, sent_at), ...]
        """
        try:
            result = self.cursor.execute(
                """SELECT id, recipient, subject, status, error_message, sent_at 
                   FROM tbl_email_logs 
                   ORDER BY sent_at DESC 
                   LIMIT %s""",
                (limit,)
            )
            result = self.cursor.fetchall()
            
            print(f"✅ Email logs retrieved: {len(result)} log(s)")
            return result
        except psycopg2.Error as e:
            print(f"Email logs retrieval error: {e}")
            return []
    
    def get_email_logs_by_recipient(self, recipient: str, limit: int = 20):
        """
        Get email logs by recipient
        
        Args:
            recipient: Email address
            limit: Number of logs to retrieve (default: 20)
            
        Returns:
            List of email logs for the recipient
        """
        try:
            result = self.cursor.execute(
                """SELECT id, recipient, subject, status, error_message, sent_at 
                   FROM tbl_email_logs 
                   WHERE recipient = %s
                   ORDER BY sent_at DESC 
                   LIMIT %s""",
                (recipient, limit)
            )
            result = self.cursor.fetchall()
            
            print(f"✅ Email logs for {recipient}: {len(result)} log(s)")
            return result
        except psycopg2.Error as e:
            print(f"Email logs retrieval error: {e}")
            return []
    
    def get_admin_actions(self):
        """
        Get admin action list
        
        Returns:
            Action list [(id, type, content), ...]
        """
        try:
            result = self.cursor.execute(
                "SELECT id, type, content FROM tbl_admin_actions ORDER BY id"
            )
            result = self.cursor.fetchall()
            
            print(f"✅ Admin action list retrieved: {len(result)} items")
            return result
        except psycopg2.Error as e:
            print(f"Admin action list retrieval error: {e}")
            return []
    
    def get_employees_by_department(self, department: str):
        """
        Get employee list by department
        
        Args:
            department: Department name
            
        Returns:
            Employee list [(employee_id, telegram_user_id, name, work_role), ...]
        """
        try:
            result = self.cursor.execute(
                "SELECT employee_id, telegram_user_id, name, work_role FROM tbl_employeer WHERE department = %s ORDER BY name",
                (department,)
            )
            result = self.cursor.fetchall()
            
            print(f"✅ {department} department employees retrieved: {len(result)} items")
            return result
        except psycopg2.Error as e:
            print(f"Department employee retrieval error: {e}")
            return []
    
    def get_all_employees(self):
        """
        Get all employee list
        
        Returns:
            Employee list [(employee_id, telegram_user_id, name, department, work_role), ...]
        """
        try:
            result = self.cursor.execute(
                "SELECT employee_id, telegram_user_id, name, department, work_role FROM tbl_employeer ORDER BY department, name"
            )
            result = self.cursor.fetchall()
            
            print(f"✅ All employees retrieved: {len(result)} items")
            return result
        except psycopg2.Error as e:
            print(f"All employee retrieval error: {e}")
            return []
    
    def check_employee_exists(self, telegram_user_id: int):
        """
        Check if employee exists (by telegram_user_id)
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            Employee info tuple or None
        """
        try:
            # Auto-recover from aborted transaction state
            if self.connection:
                import psycopg2.extensions
                if self.connection.get_transaction_status() == psycopg2.extensions.TRANSACTION_STATUS_INERROR:
                    self.connection.rollback()
            self.cursor.execute(
                "SELECT employee_id, name, department, work_role, gmail, whatsapp FROM tbl_employeer WHERE telegram_user_id = %s",
                (telegram_user_id,)
            )
            result = self.cursor.fetchone()
            
            if result:
                print(f"✅ Employee found: {result[1]} ({result[2]})")
            else:
                print(f"ℹ️ Unregistered user: Telegram ID {telegram_user_id}")
            return result
        except psycopg2.Error as e:
            print(f"Employee check error: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def register_employee(self, telegram_user_id: int, name: str, department: str, work_role: str = None):
        """
        Register new employee
        
        Args:
            telegram_user_id: Telegram user ID
            name: Employee name
            department: Department name
            work_role: Work role name (optional)
            
        Returns:
            Generated employee_id or None
        """
        try:
            # Generate next employee_id
            self.cursor.execute(
                "SELECT employee_id FROM tbl_employeer WHERE employee_id LIKE 'EMP%' ORDER BY employee_id DESC LIMIT 1"
            )

            result = self.cursor.fetchone()
            
            if result:
                # Extract number from EMP00001 format and add 1
                num_part = result[0].replace('EMP', '')
                last_num = int(num_part) if num_part.isdigit() else 0
                new_id = f"EMP{str(last_num + 1).zfill(5)}"
            else:
                # Check max numeric suffix from all EMP-prefixed IDs
                new_id = "EMP00001"
            
            self.cursor.execute("""
                INSERT INTO tbl_employeer (employee_id, telegram_user_id, name, department, work_role, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (new_id, telegram_user_id, name, department, work_role))
            
            self.connection.commit()
            print(f"✅ Employee registration successful: {new_id} - {name} ({department}) - Role: {work_role}")
            return new_id
        except psycopg2.Error as e:
            print(f"Employee registration error: {e}")
            return None
    
    def update_employee(self, employee_id: str, name: str = None, department: str = None, work_role: str = None):
        """
        Update employee information
        
        Args:
            employee_id: Employee ID (EMP00001 format)
            name: New name (optional)
            department: New department (optional)
            work_role: New work role (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            updates = []
            params = []
            
            if name:
                updates.append("name = %s")
                params.append(name)
            if department:
                updates.append("department = %s")
                params.append(department)
            if work_role is not None:
                updates.append("work_role = %s")
                params.append(work_role)
            
            if not updates:
                return False
            
            params.append(employee_id)
            query = f"UPDATE tbl_employeer SET {', '.join(updates)} WHERE employee_id = %s"
            self.cursor.execute(query, tuple(params))
            
            self.connection.commit()
            print(f"✅ Employee updated: {employee_id}")
            return True
        except psycopg2.Error as e:
            print(f"Employee update error: {e}")
            return False
    
    def delete_employee(self, employee_id: str):
        """
        Delete employee
        
        Args:
            employee_id: Employee ID (EMP00001 format)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute("DELETE FROM tbl_employeer WHERE employee_id = %s", (employee_id,))
            self.connection.commit()
            print(f"✅ Employee deleted: {employee_id}")
            return True
        except psycopg2.Error as e:
            print(f"Employee delete error: {e}")
            return False
    
    def get_employee_by_id(self, employee_id: str):
        """
        Get employee by employee_id
        
        Args:
            employee_id: Employee ID (EMP00001 format)
            
        Returns:
            Employee info dict or None
        """
        try:
            self.cursor.execute(
                "SELECT employee_id, telegram_user_id, name, department, work_role, created_at FROM tbl_employeer WHERE employee_id = %s",
                (employee_id,)
            )

            result = self.cursor.fetchone()
            
            if result:
                return {
                    "employee_id": result[0],
                    "telegram_user_id": result[1],
                    "name": result[2],
                    "department": result[3],
                    "work_role": result[4],
                    "created_at": result[5]
                }
            return None
        except psycopg2.Error as e:
            print(f"Get employee by ID error: {e}")
            return None
    
    # ==================== ATTENDANCE MANAGEMENT ====================
    
    def create_daily_attendance_for_all(self, work_date: str):
        """
        Create daily attendance records for all employees
        
        Args:
            work_date: Date in YYYY-MM-DD format
            
        Returns:
            Number of records created
        """
        try:
            employees = self.get_all_employees()
            created_count = 0
            
            for emp_id, telegram_id, name, dept, work_role in employees:
                # Check if record already exists
                self.cursor.execute(
                    "SELECT id FROM tbl_work_history WHERE telegram_user_id = %s AND work_date = %s",
                    (telegram_id, work_date)
                )

                existing = self.cursor.fetchone()
                
                if not existing:
                    self.cursor.execute("""
                        INSERT INTO tbl_work_history (telegram_user_id, department, name, work_date, status)
                        VALUES (%s, %s, %s, %s, 0)
                    """, (telegram_id, dept, name, work_date))
                    created_count += 1
            
            self.connection.commit()
            print(f"✅ Daily attendance records created: {created_count}")
            return created_count
        except psycopg2.Error as e:
            print(f"Create daily attendance error: {e}")
            return 0
    
    def get_attendance_by_user_and_date(self, telegram_user_id: int, work_date: str):
        """
        Get attendance record for specific user and date
        
        Args:
            telegram_user_id: Telegram user ID
            work_date: Date in YYYY-MM-DD format
            
        Returns:
            Attendance record dict or None
        """
        try:
            self.cursor.execute("""
                SELECT id, telegram_user_id, department, name, work_date, check_in_time, status
                FROM tbl_work_history 
                WHERE telegram_user_id = %s AND work_date = %s
            """, (telegram_user_id, work_date))

            result = self.cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "telegram_user_id": result[1],
                    "department": result[2],
                    "name": result[3],
                    "work_date": result[4],
                    "check_in_time": result[5],
                    "status": result[6]
                }
            return None
        except psycopg2.Error as e:
            print(f"Get attendance error: {e}")
            return None
    
    def update_attendance_status(self, telegram_user_id: int, work_date: str, status: int, check_in_time: str = None):
        """
        Update attendance status
        
        Args:
            telegram_user_id: Telegram user ID
            work_date: Date in YYYY-MM-DD format
            status: 0-absent, 1-present, 2-late, 3-vacation
            check_in_time: Check-in time in HH:MM format (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First check if record exists
            existing = self.get_attendance_by_user_and_date(telegram_user_id, work_date)
            
            if existing:
                if check_in_time:
                    self.cursor.execute("""
                        UPDATE tbl_work_history SET status = %s, check_in_time = %s 
                        WHERE telegram_user_id = %s AND work_date = %s
                    """, (status, check_in_time, telegram_user_id, work_date))
                else:
                    self.cursor.execute("""
                        UPDATE tbl_work_history SET status = %s 
                        WHERE telegram_user_id = %s AND work_date = %s
                    """, (status, telegram_user_id, work_date))
            else:
                # Get employee info to create new record
                emp_info = self.get_employee_info(telegram_user_id)
                if emp_info:
                    emp_id = emp_info['employee_id']
                    name = emp_info['name']
                    dept = emp_info['department']
                    self.cursor.execute("""
                        INSERT INTO tbl_work_history (telegram_user_id, department, name, work_date, check_in_time, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (telegram_user_id, dept, name, work_date, check_in_time, status))
            
            self.connection.commit()
            print(f"✅ Attendance updated: User {telegram_user_id}, Date {work_date}, Status {status}")
            return True
        except psycopg2.Error as e:
            print(f"Update attendance error: {e}")
            return False
    
    def update_checkout_time(self, telegram_user_id: int, work_date: str, check_out_time: str):
        """
        Update checkout time for an employee
        
        Args:
            telegram_user_id: Employee's Telegram user ID
            work_date: Date in YYYY-MM-DD format
            check_out_time: Checkout time in HH:MM format
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute("""
                UPDATE tbl_work_history SET check_out_time = %s 
                WHERE telegram_user_id = %s AND work_date = %s
            """, (check_out_time, telegram_user_id, work_date))
            
            self.connection.commit()
            print(f"✅ Checkout updated: User {telegram_user_id}, Date {work_date}, Time {check_out_time}")
            return True
        except psycopg2.Error as e:
            print(f"Update checkout error: {e}")
            return False
    
    def get_attendance_by_date(self, work_date: str):
        """
        Get all attendance records for a specific date
        
        Args:
            work_date: Date in YYYY-MM-DD format
            
        Returns:
            List of attendance records
        """
        try:
            result = self.cursor.execute("""
                SELECT id, telegram_user_id, department, name, work_date, check_in_time, check_out_time, status
                FROM tbl_work_history 
                WHERE work_date = %s
                ORDER BY department, name
            """, (work_date,))
            result = self.cursor.fetchall()
            
            records = []
            for row in result:
                records.append({
                    "id": row[0],
                    "telegram_user_id": row[1],
                    "department": row[2],
                    "name": row[3],
                    "work_date": row[4],
                    "check_in_time": row[5],
                    "check_out_time": row[6],
                    "status": row[7]
                })
            
            print(f"✅ Attendance records for {work_date}: {len(records)}")
            return records
        except psycopg2.Error as e:
            print(f"Get attendance by date error: {e}")
            return []
    
    def get_user_attendance_history(self, telegram_user_id: int, limit: int = 30):
        """
        Get user's attendance history
        
        Args:
            telegram_user_id: Telegram user ID
            limit: Number of records to retrieve
            
        Returns:
            List of attendance records
        """
        try:
            result = self.cursor.execute("""
                SELECT id, telegram_user_id, department, name, work_date, check_in_time, check_out_time, status
                FROM tbl_work_history 
                WHERE telegram_user_id = %s
                ORDER BY work_date DESC
                LIMIT %s
            """, (telegram_user_id, limit))
            result = self.cursor.fetchall()
            
            records = []
            for row in result:
                records.append({
                    "id": row[0],
                    "telegram_user_id": row[1],
                    "department": row[2],
                    "name": row[3],
                    "work_date": row[4],
                    "check_in_time": row[5],
                    "check_out_time": row[6],
                    "status": row[7]
                })
            
            return records
        except psycopg2.Error as e:
            print(f"Get user attendance history error: {e}")
            return []

    # ==================== END ATTENDANCE MANAGEMENT ====================
    
    # ==================== DUTY CHECK MANAGEMENT ====================
    
    def create_duty_check(self, admin_id: int, expires_minutes: int = 5):
        """
        Create a new duty check request
        
        Args:
            admin_id: Admin's Telegram user ID
            expires_minutes: Minutes until expiration (default 5)
            
        Returns:
            Created duty check ID or None
        """
        try:
            from datetime import datetime, timedelta
            check_date = datetime.now().strftime("%Y-%m-%d")
            expires_at = (datetime.now() + timedelta(minutes=expires_minutes)).strftime("%Y-%m-%d %H:%M:%S")
            
            self.cursor.execute("""
                INSERT INTO tbl_duty_check (check_date, admin_id, expires_at, status)
                VALUES (%s, %s, %s, 'pending')
                RETURNING id
            """, (check_date, admin_id, expires_at))
            
            duty_check_id = self.cursor.fetchone()[0]
            self.connection.commit()
            print(f"✅ Duty check created: ID {duty_check_id}")
            return duty_check_id
        except psycopg2.Error as e:
            print(f"Create duty check error: {e}")
            return None
    
    def add_duty_response(self, duty_check_id: int, telegram_user_id: int, name: str):
        """
        Add an employee to duty response list
        
        Args:
            duty_check_id: Duty check ID
            telegram_user_id: Employee's Telegram user ID
            name: Employee's name
        """
        try:
            self.cursor.execute("""
                INSERT INTO tbl_duty_response (duty_check_id, telegram_user_id, name, response)
                VALUES (%s, %s, %s, 0)
            """, (duty_check_id, telegram_user_id, name))
            self.connection.commit()
        except psycopg2.Error as e:
            print(f"Add duty response error: {e}")
    
    def update_duty_response(self, duty_check_id: int, telegram_user_id: int, response: int):
        """
        Update duty response (1=Yes I'm on duty, 2=No)
        
        Args:
            duty_check_id: Duty check ID
            telegram_user_id: Employee's Telegram user ID
            response: 1=On duty, 2=Not on duty
            
        Returns:
            True if successful
        """
        try:
            from datetime import datetime
            self.cursor.execute("""
                UPDATE tbl_duty_response 
                SET response = %s, responded_at = %s
                WHERE duty_check_id = %s AND telegram_user_id = %s
            """, (response, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), duty_check_id, telegram_user_id))
            self.connection.commit()
            print(f"✅ Duty response updated: Check {duty_check_id}, User {telegram_user_id}, Response {response}")
            return True
        except psycopg2.Error as e:
            print(f"Update duty response error: {e}")
            return False
    
    def get_duty_check_by_id(self, duty_check_id: int):
        """
        Get duty check by ID
        
        Returns:
            Duty check record or None
        """
        try:
            self.cursor.execute("""
                SELECT id, check_date, admin_id, created_at, expires_at, status
                FROM tbl_duty_check WHERE id = %s
            """, (duty_check_id,))

            result = self.cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "check_date": result[1],
                    "admin_id": result[2],
                    "created_at": result[3],
                    "expires_at": result[4],
                    "status": result[5]
                }
            return None
        except psycopg2.Error as e:
            print(f"Get duty check error: {e}")
            return None
    
    def get_duty_responses(self, duty_check_id: int):
        """
        Get all responses for a duty check
        
        Returns:
            List of responses
        """
        try:
            results = self.cursor.execute("""
                SELECT id, duty_check_id, telegram_user_id, name, response, responded_at
                FROM tbl_duty_response WHERE duty_check_id = %s
            """, (duty_check_id,))
            results = self.cursor.fetchall()
            
            responses = []
            for row in results:
                responses.append({
                    "id": row[0],
                    "duty_check_id": row[1],
                    "telegram_user_id": row[2],
                    "name": row[3],
                    "response": row[4],
                    "responded_at": row[5]
                })
            return responses
        except psycopg2.Error as e:
            print(f"Get duty responses error: {e}")
            return []
    
    def get_latest_duty_check(self, check_date: str = None):
        """
        Get the latest duty check for a date
        
        Args:
            check_date: Date in YYYY-MM-DD format (default: today)
            
        Returns:
            Duty check record or None
        """
        try:
            from datetime import datetime
            if not check_date:
                check_date = datetime.now().strftime("%Y-%m-%d")
            
            self.cursor.execute("""
                SELECT id, check_date, admin_id, created_at, expires_at, status
                FROM tbl_duty_check 
                WHERE check_date = %s
                ORDER BY created_at DESC LIMIT 1
            """, (check_date,))

            
            result = self.cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "check_date": result[1],
                    "admin_id": result[2],
                    "created_at": result[3],
                    "expires_at": result[4],
                    "status": result[5]
                }
            return None
        except psycopg2.Error as e:
            print(f"Get latest duty check error: {e}")
            return None
    
    def update_duty_check_status(self, duty_check_id: int, status: str):
        """
        Update duty check status
        
        Args:
            duty_check_id: Duty check ID
            status: 'pending', 'completed', 'expired'
        """
        try:
            self.cursor.execute("""
                UPDATE tbl_duty_check SET status = %s WHERE id = %s
            """, (status, duty_check_id))
            self.connection.commit()
        except psycopg2.Error as e:
            print(f"Update duty check status error: {e}")
    
    def get_reception_employees(self):
        """
        Get all Reception department employees
        
        Returns:
            List of (telegram_user_id, name) tuples
        """
        try:
            results = self.cursor.execute("""
                SELECT telegram_user_id, name FROM tbl_employeer 
                WHERE department = 'Reception' AND telegram_user_id IS NOT NULL
            """)
            results = self.cursor.fetchall()
            return results
        except psycopg2.Error as e:
            print(f"Get reception employees error: {e}")
            return []
    
    def mark_expired_duty_responses(self, duty_check_id: int):
        """
        Mark non-responded entries as not on duty (response=3 means expired/no response)
        """
        try:
            self.cursor.execute("""
                UPDATE tbl_duty_response 
                SET response = 3
                WHERE duty_check_id = %s AND response = 0
            """, (duty_check_id,))
            self.connection.commit()
        except psycopg2.Error as e:
            print(f"Mark expired responses error: {e}")
    
    # ==================== END DUTY CHECK MANAGEMENT ====================
    
    # ==================== COMPLAINTS MANAGEMENT ====================
    
    def create_complaint(self, telegram_user_id: int, department: str, name: str, 
                         complaint_text: str, media_type: str = None, media_file_id: str = None):
        """
        Create a new complaint record
        
        Args:
            telegram_user_id: Employee's Telegram user ID
            department: Employee's department
            name: Employee's name
            complaint_text: Complaint description
            media_type: Type of attached media (photo, video, document, etc.)
            media_file_id: Telegram file ID of the attached media
            
        Returns:
            Created complaint ID or None
        """
        try:
            from datetime import datetime
            complaint_date = datetime.now().strftime("%Y-%m-%d")
            
            self.cursor.execute("""
                INSERT INTO tbl_complaints 
                (telegram_user_id, department, name, complaint_date, complaint_text, media_type, media_file_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (telegram_user_id, department, name, complaint_date, complaint_text, media_type, media_file_id))
            
            complaint_id = self.cursor.fetchone()[0]
            self.connection.commit()
            print(f"✅ Complaint created: ID {complaint_id}")
            return complaint_id
        except psycopg2.Error as e:
            print(f"Create complaint error: {e}")
            return None
    
    def get_all_complaints(self, limit: int = 50):
        """
        Get all complaints (for admin)
        
        Args:
            limit: Number of records to retrieve
            
        Returns:
            List of complaint records
        """
        try:
            result = self.cursor.execute("""
                SELECT id, telegram_user_id, department, name, complaint_date, 
                       complaint_text, media_type, media_file_id, confirmed, confirmed_by, confirmed_at, created_at
                FROM tbl_complaints 
                ORDER BY confirmed ASC, created_at DESC
                LIMIT %s
            """, (limit,))
            result = self.cursor.fetchall()
            
            complaints = []
            for row in result:
                complaints.append({
                    "id": row[0],
                    "telegram_user_id": row[1],
                    "department": row[2],
                    "name": row[3],
                    "complaint_date": row[4],
                    "complaint_text": row[5],
                    "media_type": row[6],
                    "media_file_id": row[7],
                    "confirmed": row[8],
                    "confirmed_by": row[9],
                    "confirmed_at": row[10],
                    "created_at": row[11]
                })
            
            return complaints
        except psycopg2.Error as e:
            print(f"Get all complaints error: {e}")
            return []
    
    def get_unconfirmed_complaints(self):
        """
        Get unconfirmed complaints count
        
        Returns:
            Number of unconfirmed complaints
        """
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM tbl_complaints WHERE confirmed = 0
            """)

            result = self.cursor.fetchone()
            return result[0] if result else 0
        except psycopg2.Error as e:
            print(f"Get unconfirmed complaints error: {e}")
            return 0
    
    def get_complaint_by_id(self, complaint_id: int):
        """
        Get complaint by ID
        
        Args:
            complaint_id: Complaint ID
            
        Returns:
            Complaint record or None
        """
        try:
            self.cursor.execute("""
                SELECT id, telegram_user_id, department, name, complaint_date, 
                       complaint_text, media_type, media_file_id, confirmed, confirmed_by, confirmed_at, created_at
                FROM tbl_complaints 
                WHERE id = %s
            """, (complaint_id,))

            result = self.cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "telegram_user_id": result[1],
                    "department": result[2],
                    "name": result[3],
                    "complaint_date": result[4],
                    "complaint_text": result[5],
                    "media_type": result[6],
                    "media_file_id": result[7],
                    "confirmed": result[8],
                    "confirmed_by": result[9],
                    "confirmed_at": result[10],
                    "created_at": result[11]
                }
            return None
        except psycopg2.Error as e:
            print(f"Get complaint by ID error: {e}")
            return None
    
    def mark_complaint_confirmed(self, complaint_id: int, confirmed_by: int):
        """
        Mark complaint as confirmed by admin
        
        Args:
            complaint_id: Complaint ID
            confirmed_by: Admin's Telegram user ID
            
        Returns:
            Success status
        """
        try:
            from datetime import datetime
            confirmed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.cursor.execute("""
                UPDATE tbl_complaints 
                SET confirmed = 1, confirmed_by = %s, confirmed_at = %s
                WHERE id = %s
            """, (confirmed_by, confirmed_at, complaint_id))
            self.connection.commit()
            
            print(f"✅ Complaint {complaint_id} confirmed by {confirmed_by}")
            return True
        except psycopg2.Error as e:
            print(f"Mark complaint confirmed error: {e}")
            return False
    
    def get_user_complaints(self, telegram_user_id: int, limit: int = 20):
        """
        Get complaints by user
        
        Args:
            telegram_user_id: User's Telegram ID
            limit: Number of records
            
        Returns:
            List of complaints
        """
        try:
            result = self.cursor.execute("""
                SELECT id, telegram_user_id, department, name, complaint_date, 
                       complaint_text, media_type, media_file_id, confirmed, confirmed_by, confirmed_at, created_at
                FROM tbl_complaints 
                WHERE telegram_user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (telegram_user_id, limit))
            result = self.cursor.fetchall()
            
            complaints = []
            for row in result:
                complaints.append({
                    "id": row[0],
                    "telegram_user_id": row[1],
                    "department": row[2],
                    "name": row[3],
                    "complaint_date": row[4],
                    "complaint_text": row[5],
                    "media_type": row[6],
                    "media_file_id": row[7],
                    "confirmed": row[8],
                    "confirmed_by": row[9],
                    "confirmed_at": row[10],
                    "created_at": row[11]
                })
            
            return complaints
        except psycopg2.Error as e:
            print(f"Get user complaints error: {e}")
            return []
    
    # ==================== END COMPLAINTS MANAGEMENT ====================

    def get_employee_tasks(self, telegram_user_id: int):
        """
        Get task list assigned to employee
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            Task list
        """
        try:
            result = self.cursor.execute("""
                SELECT id, Date, department, description, priority, due_date, is_materials, is_check, is_perform
                FROM tbl_tasks 
                WHERE assignee_id = %s
                ORDER BY 
                    CASE priority WHEN 'Urgent' THEN 1 WHEN 'Normal' THEN 2 WHEN 'Low' THEN 3 END,
                    due_date ASC
            """, (telegram_user_id,))
            result = self.cursor.fetchall()
            
            print(f"✅ Employee tasks retrieved: {len(result)} items")
            return result
        except psycopg2.Error as e:
            print(f"Employee task retrieval error: {e}")
            return []
    
    def get_tasks_for_employee(self, telegram_user_id: int, department: str):
        """
        Get task list for employee (department or directly assigned)
        
        Args:
            telegram_user_id: Telegram user ID
            department: Employee's department name
            
        Returns:
            Task list
        """
        try:
            result = self.cursor.execute("""
                SELECT id, Date, department, description, priority, due_date, is_materials, is_check, is_perform, assignee_name
                FROM tbl_tasks 
                WHERE department = %s OR assignee_id = %s
                ORDER BY 
                    Date DESC,
                    is_check ASC,
                    CASE priority WHEN 'Urgent' THEN 1 WHEN 'Normal' THEN 2 WHEN 'Low' THEN 3 END,
                    id DESC
            """, (department, telegram_user_id))
            result = self.cursor.fetchall()
            
            print(f"✅ Employee tasks retrieved (department: {department}): {len(result)} items")
            return result
        except psycopg2.Error as e:
            print(f"Employee task retrieval error: {e}")
            return []
    
    def get_unread_task_count(self, telegram_user_id: int, department: str):
        """
        Get unread task count (is_check = 0)
        
        Args:
            telegram_user_id: Telegram user ID
            department: Employee's department name
            
        Returns:
            Unread task count
        """
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM tbl_tasks 
                WHERE (department = %s OR assignee_id = %s) AND is_check = 0
            """, (department, telegram_user_id))
            result = self.cursor.fetchone()
            
            count = result[0] if result else 0
            print(f"✅ Unread task count: {count} items")
            return count
        except psycopg2.Error as e:
            print(f"Unread task count retrieval error: {e}")
            return 0
    
    def get_task_by_id(self, task_id: int):
        """
        Get task detail info
        
        Args:
            task_id: Task ID
            
        Returns:
            Task info tuple or None
        """
        try:
            self.cursor.execute("""
                SELECT id, Date, department, assignee_id, assignee_name, description, priority, due_date, is_materials, is_check, is_perform, proof_path, check_admin, created_by, created_at, proof_required, report_notes, report_attachment
                FROM tbl_tasks 
                WHERE id = %s
            """, (task_id,))

            result = self.cursor.fetchone()
            
            if result:
                print(f"✅ Task detail retrieved: ID {task_id}")
            return result
        except psycopg2.Error as e:
            print(f"Task detail retrieval error: {e}")
            return None
    
    def mark_task_as_read(self, task_id: int):
        """
        Mark task as read (is_check = 1)
        
        Args:
            task_id: Task ID
            
        Returns:
            Success status
        """
        try:
            self.cursor.execute("""
                UPDATE tbl_tasks SET is_check = 1 WHERE id = %s
            """, (task_id,))
            self.connection.commit()
            print(f"✅ Task marked as read: ID {task_id}")
            return True
        except psycopg2.Error as e:
            print(f"Task read marking error: {e}")
            return False
    
    def create_task(self, task_data: dict):
        """
        Create new task
        
        Args:
            task_data: Task data dict
            
        Returns:
            Created task ID or None
        """
        try:
            # Create tbl_tasks table if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_tasks (
                    id SERIAL PRIMARY KEY,
                    Date DATE NOT NULL,
                    department TEXT,
                    assignee_id BIGINT NOT NULL,
                    assignee_name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'Normal',
                    due_date TEXT NOT NULL,
                    is_materials INTEGER NOT NULL DEFAULT 0,
                    is_check INTEGER NOT NULL DEFAULT 0,
                    is_perform INTEGER NOT NULL,
                    proof_path TEXT NOT NULL,
                    check_admin INTEGER NOT NULL DEFAULT 0,
                    created_by BIGINT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    attachment TEXT,
                    report_attachment TEXT
                )
            """)
            
            # Add columns if they don't exist
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS attachment TEXT")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS report_attachment TEXT")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            from datetime import date
            today = date.today().isoformat()
            
            # Add new tracking columns if they don't exist
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS notification_sent_at TIMESTAMP")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS notification_read_at TIMESTAMP")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS task_started_at TIMESTAMP")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS task_completed_at TIMESTAMP")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS task_status TEXT DEFAULT 'pending'")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS proof_required INTEGER DEFAULT 0")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS overdue_notified_date DATE")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            self.cursor.execute("""
                INSERT INTO tbl_tasks (Date, department, assignee_id, assignee_name, description, priority, due_date, is_materials, is_check, is_perform, proof_path, created_by, attachment, proof_required)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                today,
                task_data.get('department_name'),
                task_data.get('employee_id') or 0,
                task_data.get('employee_name') or 'Unassigned',
                task_data.get('description'),
                task_data.get('priority', 'Normal'),
                task_data.get('due_date'),
                1 if task_data.get('requires_materials') else 0,
                0,  # is_check: 0 = Pending
                0,  # is_perform: 0 = Not performed
                '',  # proof_path: empty initially
                task_data.get('created_by') or 0,
                task_data.get('attachment'),  # attachment file_id
                1 if task_data.get('proof_required') else 0  # proof_required
            ))
            
            task_id = self.cursor.fetchone()[0]
            self.connection.commit()
            print(f"✅ Task created successfully: ID {task_id}")
            return task_id
        except psycopg2.Error as e:
            print(f"Task creation error: {e}")
            self.connection.rollback()
            return None
    
    def mark_task_notification_sent(self, task_id: int) -> bool:
        """
        Mark task notification as sent and record the time
        
        Args:
            task_id: Task ID
            
        Returns:
            Success status
        """
        try:
            from datetime import datetime
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute("""
                UPDATE tbl_tasks SET notification_sent_at = %s, task_status = 'notified' WHERE id = %s
            """, (now, task_id))
            self.connection.commit()
            print(f"✅ Task {task_id} notification sent at {now}")
            return True
        except psycopg2.Error as e:
            print(f"Error marking notification sent: {e}")
            return False
    
    def mark_task_notification_read(self, task_id: int) -> bool:
        """
        Mark task notification as read and record the time
        
        Args:
            task_id: Task ID
            
        Returns:
            Success status
        """
        try:
            from datetime import datetime
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute("""
                UPDATE tbl_tasks SET notification_read_at = %s, task_status = 'read' 
                WHERE id = %s AND notification_read_at IS NULL
            """, (now, task_id))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                print(f"✅ Task {task_id} notification read at {now}")
            return True
        except psycopg2.Error as e:
            print(f"Error marking notification read: {e}")
            return False
    
    def get_overdue_tasks_for_notification(self):
        """
        Get overdue tasks (due_date passed, is_perform=0) that haven't been notified today.
        Groups by assignee_id (telegram_user_id) for batch notification.
        
        Returns:
            List of dicts: [{telegram_user_id, name, task_id, description, due_date, department, priority}, ...]
        """
        try:
            from datetime import date
            today = date.today().isoformat()
            
            self.cursor.execute("""
                SELECT t.id, t.assignee_id, t.assignee_name, t.description, t.due_date, 
                       t.department, t.priority, e.telegram_user_id, e.name as emp_name
                FROM tbl_tasks t
                LEFT JOIN tbl_employeer e ON t.assignee_id = e.telegram_user_id
                WHERE t.is_perform = 0 
                  AND t.due_date < %s
                  AND t.assignee_id != 0
                  AND (t.overdue_notified_date IS NULL OR t.overdue_notified_date < %s)
                ORDER BY t.assignee_id, t.due_date ASC
            """, (today, today))
            
            results = self.cursor.fetchall()
            tasks = []
            for r in results:
                tasks.append({
                    'task_id': r[0],
                    'assignee_id': r[1],
                    'assignee_name': r[2],
                    'description': r[3],
                    'due_date': r[4],
                    'department': r[5],
                    'priority': r[6],
                    'telegram_user_id': r[7] or r[1],
                    'emp_name': r[8] or r[2]
                })
            
            print(f"✅ Overdue tasks for notification: {len(tasks)} items")
            return tasks
        except psycopg2.Error as e:
            print(f"❌ Error getting overdue tasks: {e}")
            self.connection.rollback()
            return []
    
    def mark_overdue_notified(self, task_ids: list):
        """
        Mark overdue tasks as notified today so they won't be notified again until tomorrow.
        
        Args:
            task_ids: List of task IDs
        """
        try:
            from datetime import date
            today = date.today().isoformat()
            
            for tid in task_ids:
                self.cursor.execute(
                    "UPDATE tbl_tasks SET overdue_notified_date = %s WHERE id = %s",
                    (today, tid)
                )
            self.connection.commit()
            print(f"✅ Marked {len(task_ids)} overdue tasks as notified for {today}")
        except psycopg2.Error as e:
            print(f"❌ Error marking overdue notified: {e}")
            self.connection.rollback()
    
    def mark_task_started(self, task_id: int) -> bool:
        """
        Mark task as started and record the time
        
        Args:
            task_id: Task ID
            
        Returns:
            Success status
        """
        try:
            from datetime import datetime
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute("""
                UPDATE tbl_tasks SET task_started_at = %s, task_status = 'in_progress' 
                WHERE id = %s AND task_started_at IS NULL
            """, (now, task_id))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                print(f"✅ Task {task_id} started at {now}")
            return True
        except psycopg2.Error as e:
            print(f"Error marking task started: {e}")
            return False
    
    def mark_task_completed(self, task_id: int) -> bool:
        """
        Mark task as completed and record the time
        
        Args:
            task_id: Task ID
            
        Returns:
            Success status
        """
        try:
            from datetime import datetime
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute("""
                UPDATE tbl_tasks SET task_completed_at = %s, task_status = 'completed', is_perform = 1 
                WHERE id = %s
            """, (now, task_id))
            self.connection.commit()
            print(f"✅ Task {task_id} completed at {now}")
            return True
        except psycopg2.Error as e:
            print(f"Error marking task completed: {e}")
            return False
    
    def get_task_tracking_info(self, task_id: int):
        """
        Get task tracking information (notification sent/read times, task start/complete times)
        
        Args:
            task_id: Task ID
            
        Returns:
            Tracking info dict or None
        """
        try:
            self.cursor.execute("""
                SELECT notification_sent_at, notification_read_at, task_started_at, task_completed_at, task_status
                FROM tbl_tasks WHERE id = %s
            """, (task_id,))

            result = self.cursor.fetchone()
            
            if result:
                return {
                    'notification_sent_at': result[0],
                    'notification_read_at': result[1],
                    'task_started_at': result[2],
                    'task_completed_at': result[3],
                    'task_status': result[4]
                }
            return None
        except psycopg2.Error as e:
            print(f"Error getting task tracking info: {e}")
            return None

    def get_customer_rooms(self):
        """
        Get customer room list
        
        Returns:
            Room list [(id, id_room, is_check, AC, TV, Toilet, Remote_Control, is_active, total_capacity, current_guests), ...]
        """
        try:
            self.cursor.execute(
                """SELECT id, id_room, 
                   COALESCE(is_check, 0) as is_check,
                   COALESCE(ac, 0) as AC, 
                   COALESCE(tv, 0) as TV, 
                   COALESCE(toilet, 0) as Toilet, 
                   COALESCE(remote_control, 0) as Remote_Control, 
                   COALESCE(is_active, 1) as is_active, 
                   COALESCE(total_capacity, 2) as total_capacity, 
                   COALESCE(current_guests, 0) as current_guests 
                   FROM tbl_customer_rooms ORDER BY id"""
            )
            result = self.cursor.fetchall()
            
            print(f"✅ Customer room list retrieved: {len(result)} items")
            return result
        except psycopg2.Error as e:
            if self.connection:
                self.connection.rollback()
            print(f"Customer room list retrieval error: {e}")
            return []
    
    def get_customer_rooms_summary(self):
        """
        Get customer room summary info
        
        Returns:
            Summary info dict
        """
        try:
            # Total room count
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms")
            result = self.cursor.fetchone()
            total = result[0] if result else 0
            
            # Active room count (is_active = 1)
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms WHERE is_active = 1")
            result = self.cursor.fetchone()
            active = result[0] if result else 0
            
            # Inactive room count (is_active = 0)
            inactive = total - active
            
            # Checked-in room count (is_check = 1)
            self.cursor.execute("""
                SELECT COUNT(*) FROM tbl_customer_rooms 
                WHERE is_check = 1 
                AND is_active = 1
            """)
            result = self.cursor.fetchone()
            checked_in = result[0] if result else 0
            
            # Available room count (is_active = 1 and not checked in)
            available = active - checked_in
            
            # AC working room count
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms WHERE (ac = 1 OR ac = '1') AND is_active = 1")
            result = self.cursor.fetchone()
            ac_working = result[0] if result else 0
            
            # TV working room count
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms WHERE (tv = 1 OR tv = '1') AND is_active = 1")
            result = self.cursor.fetchone()
            tv_working = result[0] if result else 0
            
            # Toilet working room count
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms WHERE (toilet = 1 OR toilet = '1') AND is_active = 1")
            result = self.cursor.fetchone()
            toilet_working = result[0] if result else 0
            
            # Remote Control working room count
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms WHERE (remote_control = 1 OR remote_control = '1') AND is_active = 1")
            result = self.cursor.fetchone()
            remote_working = result[0] if result else 0
            
            return {
                'total': total,
                'active': active,
                'inactive': inactive,
                'checked_in': checked_in,
                'available': available,
                'ac_working': ac_working,
                'tv_working': tv_working,
                'toilet_working': toilet_working,
                'remote_working': remote_working
            }
        except psycopg2.Error as e:
            if self.connection:
                self.connection.rollback()
            print(f"Customer room summary retrieval error: {e}")
            return None
    
    def get_hotel_settings(self):
        """
        Get hotel settings
        
        Returns:
            Settings dict with total_rooms, hotel_name, ai_analysis_enabled, etc.
        """
        try:
            self.cursor.execute(
                """SELECT id, total_rooms, hotel_name, updated_at, 
                   COALESCE(ai_analysis_enabled, 0) as ai_analysis_enabled,
                   COALESCE(email_notifications_enabled, 0) as email_notifications_enabled,
                   COALESCE(whatsapp_notifications_enabled, 0) as whatsapp_notifications_enabled
                   FROM tbl_hotel_settings WHERE id = 1"""
            )
            result = self.cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "total_rooms": result[1],
                    "hotel_name": result[2],
                    "updated_at": result[3],
                    "ai_analysis_enabled": bool(result[4]),
                    "email_notifications_enabled": bool(result[5]),
                    "whatsapp_notifications_enabled": bool(result[6])
                }
            return {
                "id": 1, "total_rooms": 0, "hotel_name": "Hotel", "updated_at": None,
                "ai_analysis_enabled": False, "email_notifications_enabled": False, 
                "whatsapp_notifications_enabled": False
            }
        except psycopg2.Error as e:
            print(f"Error getting hotel settings: {e}")
            if self.connection:
                self.connection.rollback()
            return {
                "id": 1, "total_rooms": 0, "hotel_name": "Hotel", "updated_at": None,
                "ai_analysis_enabled": False, "email_notifications_enabled": False,
                "whatsapp_notifications_enabled": False
            }
    
    def update_hotel_settings(self, total_rooms: int = None, hotel_name: str = None,
                               ai_analysis_enabled: bool = None, email_notifications_enabled: bool = None,
                               whatsapp_notifications_enabled: bool = None):
        """
        Update hotel settings
        
        Args:
            total_rooms: Total number of rooms (optional)
            hotel_name: Hotel name (optional)
            ai_analysis_enabled: Enable AI analysis (optional)
            email_notifications_enabled: Enable email notifications (optional)
            whatsapp_notifications_enabled: Enable WhatsApp notifications (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            updates = []
            params = []
            
            if total_rooms is not None:
                updates.append("total_rooms = %s")
                params.append(total_rooms)
            
            if hotel_name is not None:
                updates.append("hotel_name = %s")
                params.append(hotel_name)
            
            if ai_analysis_enabled is not None:
                updates.append("ai_analysis_enabled = %s")
                params.append(1 if ai_analysis_enabled else 0)
            
            if email_notifications_enabled is not None:
                updates.append("email_notifications_enabled = %s")
                params.append(1 if email_notifications_enabled else 0)
            
            if whatsapp_notifications_enabled is not None:
                updates.append("whatsapp_notifications_enabled = %s")
                params.append(1 if whatsapp_notifications_enabled else 0)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(1)
            
            query = f"UPDATE tbl_hotel_settings SET {', '.join(updates)} WHERE id = %s"
            self.cursor.execute(query, tuple(params))
            self.connection.commit()
            print(f"✅ Hotel settings updated")
            return True
        except psycopg2.Error as e:
            print(f"Error updating hotel settings: {e}")
            return False
    
    def get_whatsapp_credentials(self):
        """
        Get WhatsApp/Twilio credentials from database (decrypted)
        
        Returns:
            Dictionary with 'account_sid', 'auth_token', 'whatsapp_from' or None
        """
        try:
            self.cursor.execute("""
                SELECT account_sid_encrypted, auth_token_encrypted, whatsapp_from_encrypted
                FROM tbl_whatsapp_credentials
                WHERE id = 1
            """)
            
            result = self.cursor.fetchone()
            
            if not result:
                print("⚠️ No WhatsApp credentials found in database")
                return None
            
            from security_manager import SecurityManager
            import os
            
            # Initialize security manager with db_config
            db_config = {
                'host': os.getenv('DB_HOST', self.db_host),
                'port': os.getenv('DB_PORT', self.db_port),
                'name': os.getenv('DB_NAME', self.db_name),
                'user': os.getenv('DB_USER', self.db_user),
                'password': os.getenv('DB_PASSWORD', self.db_password)
            }
            sec_mgr = SecurityManager(db_config)
            
            # Decrypt credentials
            account_sid = sec_mgr.decrypt(bytes(result[0]))
            auth_token = sec_mgr.decrypt(bytes(result[1]))
            whatsapp_from = sec_mgr.decrypt(bytes(result[2]))
            
            # Close security manager connection
            sec_mgr.close()
            
            return {
                'account_sid': account_sid,
                'auth_token': auth_token,
                'whatsapp_from': whatsapp_from
            }
            
        except Exception as e:
            print(f"❌ Error getting WhatsApp credentials: {e}")
            return None
    
    def get_room_detail(self, room_id: int):
        """
        Get room detail info
        
        Args:
            room_id: Room ID
            
        Returns:
            Room info (id, id_room, is_check, AC, TV, Toilet, Remote_Control, total_capacity, current_guests)
        """
        try:
            self.cursor.execute(
                """SELECT id, id_room, is_check, AC, TV, Toilet, Remote_Control, 
                   COALESCE(total_capacity, 2) as total_capacity, 
                   COALESCE(current_guests, 0) as current_guests 
                   FROM tbl_customer_rooms WHERE id = %s""",
                (room_id,)
            )
            result = self.cursor.fetchone()
            
            if result:
                print(f"✅ Room detail retrieved: {result}")
            return result
        except psycopg2.Error as e:
            if self.connection:
                self.connection.rollback()
            print(f"Room detail retrieval error: {e}")
            return None
    
    def update_room_guests(self, room_id: int, current_guests: int):
        """
        Update current guests count for a room
        
        Args:
            room_id: Room ID
            current_guests: Number of current guests
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                "UPDATE tbl_customer_rooms SET current_guests = %s WHERE id = %s",
                (current_guests, room_id)
            )
            self.connection.commit()
            print(f"✅ Room {room_id} guests updated to {current_guests}")
            return True
        except psycopg2.Error as e:
            print(f"Room guests update error: {e}")
            return False
    
    def update_room_capacity(self, room_id: int, total_capacity: int):
        """
        Update total capacity for a room
        
        Args:
            room_id: Room ID
            total_capacity: Total capacity
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                "UPDATE tbl_customer_rooms SET total_capacity = %s WHERE id = %s",
                (total_capacity, room_id)
            )
            self.connection.commit()
            print(f"✅ Room {room_id} capacity updated to {total_capacity}")
            return True
        except psycopg2.Error as e:
            print(f"Room capacity update error: {e}")
            return False
    
    def get_housekeeping_summary(self):
        """
        Get housekeeping amenity status summary
        
        Returns:
            Amenity status summary dict
        """
        try:
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms")

            result = self.cursor.fetchone()


            total = result[0] if result else 0
            
            # Count of each amenity in OK(1) status
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms WHERE AC = '1' OR AC = 1")

            result = self.cursor.fetchone()


            ac_ok = result[0] if result else None
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms WHERE TV = '1' OR TV = 1")

            result = self.cursor.fetchone()


            tv_ok = result[0] if result else None
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms WHERE Toilet = '1' OR Toilet = 1")

            result = self.cursor.fetchone()


            toilet_ok = result[0] if result else None
            self.cursor.execute("SELECT COUNT(*) FROM tbl_customer_rooms WHERE Remote_Control = '1' OR Remote_Control = 1")

            result = self.cursor.fetchone()


            remote_ok = result[0] if result else None
            
            return {
                'total': total,
                'ac_ok': ac_ok,
                'tv_ok': tv_ok,
                'toilet_ok': toilet_ok,
                'remote_ok': remote_ok
            }
        except psycopg2.Error as e:
            print(f"Housekeeping summary retrieval error: {e}")
            return None
    
    def get_rooms_by_amenity(self, amenity: str):
        """
        Get room list by specific amenity
        
        Args:
            amenity: Amenity name (AC, TV, Toilet, Remote_Control)
            
        Returns:
            Room amenity status list [(id, id_room, status), ...]
        """
        try:
            result = self.cursor.execute(
                f"SELECT id, id_room, {amenity} FROM tbl_customer_rooms ORDER BY id"
            )
            result = self.cursor.fetchall()
            
            print(f"✅ {amenity} amenity status retrieved: {len(result)} items")
            return result
        except psycopg2.Error as e:
            print(f"{amenity} amenity status retrieval error: {e}")
            return []
    
    def get_accounting_summary(self):
        """
        Get accounting summary info (overall average)
        
        Returns:
            Average values by category dict
        """
        try:
            result = self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_days,
                    ROUND(AVG(Room_Revenue), 0) as avg_room,
                    ROUND(AVG(Food_Beverage_Revenue), 0) as avg_food,
                    ROUND(AVG(Purchasing_Product_Revenue), 0) as avg_purchase,
                    ROUND(AVG(Utilities_Expenses), 0) as avg_utilities,
                    ROUND(AVG(Total_amount), 0) as avg_total,
                    SUM(Total_amount) as sum_total
                FROM tbl_hotel_accounts
            """).fetchone()
            
            return {
                'total_days': result[0] or 0,
                'avg_room': int(result[1] or 0),
                'avg_food': int(result[2] or 0),
                'avg_purchase': int(result[3] or 0),
                'avg_utilities': int(result[4] or 0),
                'avg_total': int(result[5] or 0),
                'sum_total': int(result[6] or 0)
            }
        except psycopg2.Error as e:
            print(f"Accounting summary retrieval error: {e}")
            return None
    
    def get_accounting_by_period(self, period: str):
        """
        Get accounting data by period
        
        Args:
            period: 'weekly', 'monthly', 'all'
            
        Returns:
            Period data list
        """
        try:
            if period == 'weekly':
                # Last 7 days
                result = self.cursor.execute("""
                    SELECT id, Date, Room_Revenue, Food_Beverage_Revenue, 
                           Purchasing_Product_Revenue, Utilities_Expenses, Total_amount
                    FROM tbl_hotel_accounts 
                    ORDER BY Date DESC LIMIT 7
                """)
                result = self.cursor.fetchall()
            elif period == 'monthly':
                # Last 30 days
                result = self.cursor.execute("""
                    SELECT id, Date, Room_Revenue, Food_Beverage_Revenue, 
                           Purchasing_Product_Revenue, Utilities_Expenses, Total_amount
                    FROM tbl_hotel_accounts 
                    ORDER BY Date DESC LIMIT 30
                """)
                result = self.cursor.fetchall()
            else:
                # All data
                result = self.cursor.execute("""
                    SELECT id, Date, Room_Revenue, Food_Beverage_Revenue, 
                           Purchasing_Product_Revenue, Utilities_Expenses, Total_amount
                    FROM tbl_hotel_accounts 
                    ORDER BY Date DESC
                """)
                result = self.cursor.fetchall()
            
            print(f"✅ {period} accounting data retrieved: {len(result)} items")
            return result
        except psycopg2.Error as e:
            print(f"Accounting data retrieval error: {e}")
            return []
    
    def get_accounting_detail(self, account_id: int):
        """
        Get accounting detail info
        
        Args:
            account_id: Account ID
            
        Returns:
            Accounting detail info
        """
        try:
            self.cursor.execute("""
                SELECT id, Date, Room_Revenue, Food_Beverage_Revenue, 
                       Purchasing_Product_Revenue, Utilities_Expenses, Total_amount
                FROM tbl_hotel_accounts WHERE id = %s
            """, (account_id,))

            result = self.cursor.fetchone()
            
            if result:
                print(f"✅ Accounting detail retrieved: {result}")
            return result
        except psycopg2.Error as e:
            print(f"Accounting detail retrieval error: {e}")
            return None
    
    def get_reportable_tasks(self, telegram_user_id: int, department: str = None, limit: int = 20, offset: int = 0):
        """
        Get tasks that employee can report (assigned to self or department, is_perform=0)
        
        Args:
            telegram_user_id: Telegram user ID
            department: Employee's department name
            limit: Maximum number of tasks to return (default 20)
            offset: Number of tasks to skip (for pagination)
            
        Returns:
            Reportable task list (newest first)
        """
        try:
            # Tasks directly assigned or unassigned department tasks (assignee_id=0)
            # ORDER BY: Latest tasks first (id DESC), then by priority and due_date
            result = self.cursor.execute("""
                SELECT id, Date, department, description, priority, due_date, is_materials, is_check
                FROM tbl_tasks 
                WHERE is_perform = 0 AND (assignee_id = %s OR (assignee_id = 0 AND department = %s))
                ORDER BY id DESC, 
                    CASE priority WHEN 'Urgent' THEN 1 WHEN 'Normal' THEN 2 WHEN 'Low' THEN 3 END,
                    due_date ASC
                LIMIT %s OFFSET %s
            """, (telegram_user_id, department, limit, offset))
            result = self.cursor.fetchall()
            
            print(f"✅ Reportable tasks retrieved: {len(result)} items (limit={limit}, offset={offset})")
            return result
        except psycopg2.Error as e:
            print(f"Reportable task retrieval error: {e}")
            return []
    
    def get_reportable_tasks_count(self, telegram_user_id: int, department: str = None):
        """
        Get total count of reportable tasks for pagination
        
        Args:
            telegram_user_id: Telegram user ID
            department: Employee's department name
            
        Returns:
            Total count of reportable tasks
        """
        try:
            result = self.cursor.execute("""
                SELECT COUNT(*) 
                FROM tbl_tasks 
                WHERE is_perform = 0 AND (assignee_id = %s OR (assignee_id = 0 AND department = %s))
            """, (telegram_user_id, department))
            count = self.cursor.fetchone()[0]
            return count
        except psycopg2.Error as e:
            print(f"Reportable task count error: {e}")
            return 0
    
    def complete_task_with_proof(self, task_id: int, proof_file_id: str):
        """
        Complete task (is_perform=1, save proof_path)
        
        Args:
            task_id: Task ID
            proof_file_id: Telegram file_id (proof file)
            
        Returns:
            Success status
        """
        try:
            self.cursor.execute("""
                UPDATE tbl_tasks SET is_perform = 1, proof_path = %s WHERE id = %s
            """, (proof_file_id, task_id))
            self.connection.commit()
            print(f"✅ Task completion successful: ID {task_id}, proof: {proof_file_id}")
            return True
        except psycopg2.Error as e:
            print(f"Task completion error: {e}")
            return False
    
    def complete_task_with_report(self, task_id: int, report_notes: str, report_attachment: str = None):
        """
        Complete task with report notes and optional attachment
        
        Args:
            task_id: Task ID
            report_notes: Report notes from employee
            report_attachment: Telegram file_id for report attachment (optional)
            
        Returns:
            Success status
        """
        try:
            # Add report_attachment column if not exists
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS report_attachment TEXT")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            try:
                self.cursor.execute("ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS report_notes TEXT")
            except psycopg2.OperationalError:
                pass  # Column already exists
            
            from datetime import datetime
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Check if task is not accepted yet (is_check = 0)
            self.cursor.execute("SELECT is_check FROM tbl_tasks WHERE id = %s", (task_id,))
            result = self.cursor.fetchone()
            
            if result and result[0] == 0:
                # Task not accepted yet, automatically accept it
                print(f"📋 Task #{task_id} not accepted yet, automatically accepting on report submission")
                self.cursor.execute("""
                    UPDATE tbl_tasks SET is_check = 1, is_perform = 1, report_notes = %s, report_attachment = %s, 
                    task_completed_at = %s, task_status = 'completed' WHERE id = %s
                """, (report_notes, report_attachment, now, task_id))
            else:
                # Task already accepted, just complete it
                self.cursor.execute("""
                    UPDATE tbl_tasks SET is_perform = 1, report_notes = %s, report_attachment = %s, 
                    task_completed_at = %s, task_status = 'completed' WHERE id = %s
                """, (report_notes, report_attachment, now, task_id))
            
            self.connection.commit()
            print(f"✅ Task completion with report successful: ID {task_id} at {now}")
            return True
        except psycopg2.Error as e:
            print(f"❌ Task completion with report error: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def confirm_task_by_admin(self, task_id: int):
        """
        Admin confirms task (check_admin=1)
        
        Args:
            task_id: Task ID
            
        Returns:
            Success status
        """
        try:
            self.cursor.execute("""
                UPDATE tbl_tasks SET check_admin = 1 WHERE id = %s
            """, (task_id,))
            self.connection.commit()
            print(f"✅ Admin confirmation successful: ID {task_id}")
            return True
        except psycopg2.Error as e:
            print(f"Admin confirmation error: {e}")
            return False
    
    def get_pending_admin_reports(self):
        """
        Get completed tasks not confirmed by admin (is_perform=1, check_admin=0)
        
        Returns:
            Unconfirmed completed task list (sorted by task_completed_at date)
        """
        try:
            self.cursor.execute("""
                SELECT id, COALESCE(task_completed_at::date, Date) as report_date, department, assignee_id, assignee_name, description, priority, due_date, is_materials, proof_path
                FROM tbl_tasks 
                WHERE is_perform = 1 AND check_admin = 0
                ORDER BY COALESCE(task_completed_at, Date) DESC
            """)
            result = self.cursor.fetchall()
            
            # Debug: Show dates found
            if result:
                dates_found = set()
                for r in result:
                    dates_found.add(str(r['report_date']) if r['report_date'] else 'N/A')
                print(f"✅ Unconfirmed completed tasks retrieved: {len(result)} items, dates: {sorted(dates_found, reverse=True)}")
            else:
                print(f"✅ Unconfirmed completed tasks retrieved: 0 items")
            return result
        except psycopg2.Error as e:
            print(f"Unconfirmed completed task retrieval error: {e}")
            return []
    
    def get_admin_telegram_ids(self):
        """
        Get admin (Management department) Telegram ID list
        
        Returns:
            Admin Telegram ID list
        """
        try:
            result = self.cursor.execute(
                "SELECT telegram_user_id FROM tbl_employeer WHERE department = 'Management'"
            )
            result = self.cursor.fetchall()
            
            admin_ids = [row[0] for row in result]
            print(f"✅ Admin IDs retrieved: {admin_ids}")
            return admin_ids
        except psycopg2.Error as e:
            print(f"Admin ID retrieval error: {e}")
            return []
    
    def add_check_admin_column(self):
        """
        Add check_admin column to existing tbl_tasks table
        """
        try:
            # Check if column exists
            self.cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tbl_tasks'
            """)
            columns = [col['column_name'] for col in self.cursor.fetchall()]
            
            if 'check_admin' not in columns:
                self.cursor.execute("""
                    ALTER TABLE tbl_tasks ADD COLUMN IF NOT EXISTS check_admin INTEGER NOT NULL DEFAULT 0
                """)
                self.connection.commit()
                print("✅ check_admin column added successfully")
            else:
                print("ℹ️ check_admin column already exists")
        except psycopg2.Error as e:
            print(f"check_admin column addition error: {e}")
            if self.connection:
                self.connection.rollback()
    
    def add_customer_rooms_guest_columns(self):
        """
        Add total_capacity and current_guests columns to tbl_customer_rooms table
        """
        try:
            # Check if columns exist
            self.cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tbl_customer_rooms'
            """)
            columns = [col['column_name'] for col in self.cursor.fetchall()]
            
            if 'total_capacity' not in columns:
                self.cursor.execute("""
                    ALTER TABLE tbl_customer_rooms ADD COLUMN IF NOT EXISTS total_capacity INTEGER NOT NULL DEFAULT 2
                """)
                print("✅ total_capacity column added to tbl_customer_rooms")
            else:
                print("ℹ️ total_capacity column already exists")
            
            if 'current_guests' not in columns:
                self.cursor.execute("""
                    ALTER TABLE tbl_customer_rooms ADD COLUMN IF NOT EXISTS current_guests INTEGER NOT NULL DEFAULT 0
                """)
                print("✅ current_guests column added to tbl_customer_rooms")
            else:
                print("ℹ️ current_guests column already exists")
            
            self.connection.commit()
        except psycopg2.Error as e:
            print(f"customer_rooms guest columns addition error: {e}")
            if self.connection:
                self.connection.rollback()
    
    def add_employee_contact_columns(self):
        """
        Add gmail, whatsapp, and work_role columns to tbl_employeer table
        """
        try:
            # Check if columns exist
            self.cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tbl_employeer'
            """)
            columns = [col['column_name'] for col in self.cursor.fetchall()]
            
            if 'gmail' not in columns:
                self.cursor.execute("""
                    ALTER TABLE tbl_employeer ADD COLUMN IF NOT EXISTS gmail TEXT
                """)
                print("✅ gmail column added to tbl_employeer")
            else:
                print("ℹ️ gmail column already exists")
            
            if 'whatsapp' not in columns:
                self.cursor.execute("""
                    ALTER TABLE tbl_employeer ADD COLUMN IF NOT EXISTS whatsapp TEXT
                """)
                print("✅ whatsapp column added to tbl_employeer")
            else:
                print("ℹ️ whatsapp column already exists")
            
            if 'work_role' not in columns:
                self.cursor.execute("""
                    ALTER TABLE tbl_employeer ADD COLUMN IF NOT EXISTS work_role TEXT
                """)
                print("✅ work_role column added to tbl_employeer")
            else:
                print("ℹ️ work_role column already exists")
            
            if 'language' not in columns:
                self.cursor.execute("""
                    ALTER TABLE tbl_employeer ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'sr'
                """)
                print("✅ language column added to tbl_employeer")
            else:
                print("ℹ️ language column already exists")
            
            self.connection.commit()
        except psycopg2.Error as e:
            print(f"employee contact columns addition error: {e}")
            if self.connection:
                self.connection.rollback()
    
    def update_employee_gmail(self, telegram_user_id: int, gmail: str) -> bool:
        """
        Update employee Gmail address
        
        Args:
            telegram_user_id: Telegram user ID
            gmail: Gmail address
            
        Returns:
            Success status
        """
        try:
            self.cursor.execute(
                "UPDATE tbl_employeer SET gmail = %s WHERE telegram_user_id = %s",
                (gmail, telegram_user_id)
            )
            self.connection.commit()
            print(f"✅ Gmail updated for user {telegram_user_id}: {gmail}")
            return True
        except psycopg2.Error as e:
            print(f"❌ Gmail update error: {e}")
            return False
    
    def update_employee_whatsapp(self, telegram_user_id: int, whatsapp: str) -> bool:
        """
        Update employee WhatsApp number
        
        Args:
            telegram_user_id: Telegram user ID
            whatsapp: WhatsApp number
            
        Returns:
            Success status
        """
        try:
            self.cursor.execute(
                "UPDATE tbl_employeer SET whatsapp = %s WHERE telegram_user_id = %s",
                (whatsapp, telegram_user_id)
            )
            self.connection.commit()
            print(f"✅ WhatsApp updated for user {telegram_user_id}: {whatsapp}")
            return True
        except psycopg2.Error as e:
            print(f"❌ WhatsApp update error: {e}")
            return False
    
    def get_employee_contact_info(self, telegram_user_id: int) -> dict:
        """
        Get employee contact information
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            Dictionary with gmail and whatsapp
        """
        try:
            self.cursor.execute(
                "SELECT gmail, whatsapp FROM tbl_employeer WHERE telegram_user_id = %s",
                (telegram_user_id,)
            )
            result = self.cursor.fetchone()
            if result:
                return {
                    'gmail': result[0] or '',
                    'whatsapp': result[1] or ''
                }
            return {'gmail': '', 'whatsapp': ''}
        except psycopg2.Error as e:
            print(f"Contact info retrieval error: {e}")
            return {'gmail': '', 'whatsapp': ''}
    
    def update_employee_language(self, telegram_user_id: int, language: str) -> bool:
        """
        Update employee language preference
        
        Args:
            telegram_user_id: Telegram user ID
            language: Language code (sr, en, ru, etc.)
            
        Returns:
            Success status
        """
        try:
            self.cursor.execute(
                "UPDATE tbl_employeer SET language = %s WHERE telegram_user_id = %s",
                (language, telegram_user_id)
            )
            self.connection.commit()
            print(f"✅ Language updated for user {telegram_user_id}: {language}")
            return True
        except psycopg2.Error as e:
            print(f"❌ Language update error: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_employee_language(self, telegram_user_id: int) -> str:
        """
        Get employee language preference
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            Language code (default: 'sr')
        """
        try:
            self.cursor.execute(
                "SELECT language FROM tbl_employeer WHERE telegram_user_id = %s",
                (telegram_user_id,)
            )
            result = self.cursor.fetchone()
            if result and result[0]:
                return result[0]
            return 'sr'  # Default to Serbian
        except psycopg2.Error as e:
            print(f"Language retrieval error: {e}")
            return 'sr'
    
    def check_gmail_exists(self, gmail: str, exclude_telegram_id: int = None) -> bool:
        """
        Check if Gmail already exists in database
        
        Args:
            gmail: Gmail address to check
            exclude_telegram_id: Telegram user ID to exclude from check (for updates)
            
        Returns:
            True if Gmail exists, False otherwise
        """
        try:
            if exclude_telegram_id:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM tbl_employeer WHERE gmail = %s AND telegram_user_id != %s",
                    (gmail, exclude_telegram_id)
                )
            else:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM tbl_employeer WHERE gmail = %s",
                    (gmail,)
                )
            result = self.cursor.fetchone()
            return result[0] > 0 if result else False
        except psycopg2.Error as e:
            print(f"Gmail check error: {e}")
            return False
    
    def check_whatsapp_exists(self, whatsapp: str, exclude_telegram_id: int = None) -> bool:
        """
        Check if WhatsApp number already exists in database
        
        Args:
            whatsapp: WhatsApp number to check
            exclude_telegram_id: Telegram user ID to exclude from check (for updates)
            
        Returns:
            True if WhatsApp exists, False otherwise
        """
        try:
            if exclude_telegram_id:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM tbl_employeer WHERE whatsapp = %s AND telegram_user_id != %s",
                    (whatsapp, exclude_telegram_id)
                )
            else:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM tbl_employeer WHERE whatsapp = %s",
                    (whatsapp,)
                )
            result = self.cursor.fetchone()
            return result[0] > 0 if result else False
        except psycopg2.Error as e:
            print(f"WhatsApp check error: {e}")
            return False
    
    def update_employee_name(self, telegram_user_id: int, name: str) -> bool:
        """
        Update employee name
        
        Args:
            telegram_user_id: Telegram user ID
            name: New name
            
        Returns:
            Success status
        """
        try:
            self.cursor.execute(
                "UPDATE tbl_employeer SET name = %s WHERE telegram_user_id = %s",
                (name, telegram_user_id)
            )
            self.connection.commit()
            return True
        except psycopg2.Error as e:
            print(f"Name update error: {e}")
            return False
    
    def update_employee_department(self, telegram_user_id: int, department: str) -> bool:
        """
        Update employee department
        
        Args:
            telegram_user_id: Telegram user ID
            department: New department
            
        Returns:
            Success status
        """
        try:
            self.cursor.execute(
                "UPDATE tbl_employeer SET department = %s WHERE telegram_user_id = %s",
                (department, telegram_user_id)
            )
            self.connection.commit()
            return True
        except psycopg2.Error as e:
            print(f"Department update error: {e}")
            return False
    
    def update_employee_work_role(self, telegram_user_id: int, work_role: str) -> bool:
        """
        Update employee work role
        
        Args:
            telegram_user_id: Telegram user ID
            work_role: New work role
            
        Returns:
            Success status
        """
        try:
            self.cursor.execute(
                "UPDATE tbl_employeer SET work_role = %s WHERE telegram_user_id = %s",
                (work_role, telegram_user_id)
            )
            self.connection.commit()
            return True
        except psycopg2.Error as e:
            print(f"Work role update error: {e}")
            return False
    
    # ==================== Shift Report Methods (Class) ====================
    
    def create_shift_report(self, shift_date: str = None, shift_number: int = 1, employee_id: int = None,
                           reservations_count: int = 0, arrivals_count: int = 0, cash_amount: float = 0,
                           cash_photo: str = None, pos_report_photo: str = None, store_stock_notes: str = None,
                           restaurant_cash_confirmed: bool = False, key_log_notes: str = None,
                           tool_log_notes: str = None) -> int:
        """Create a new shift report (class method)"""
        try:
            from datetime import date as dt
            if shift_date is None:
                shift_date = dt.today().isoformat()
            
            # Get employee name by employee_id
            try:
                name_result = self.execute_query(
                    "SELECT name FROM tbl_employeer WHERE employee_id = %s OR CAST(telegram_user_id AS TEXT) = %s",
                    (str(employee_id), str(employee_id))
                )
                employee_name = name_result[0][0] if name_result else 'Unknown'
            except:
                employee_name = 'Unknown'
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO tbl_shift_reports 
                (shift_date, shift_number, employee_id, employee_name, reservations_count, arrivals_count,
                 departures_count, issues_notes, cash_amount, cash_photo, pos_report_photo,
                 store_stock_notes, restaurant_cash_confirmed, key_log_notes, tool_log_notes,
                 additional_notes, status)
                VALUES (%s, %s, %s, %s, %s, %s, 0, '', %s, %s, %s, %s, %s, %s, %s, '', 'submitted')
                RETURNING id
            """, (shift_date, shift_number, employee_id, employee_name, reservations_count, arrivals_count,
                  cash_amount, cash_photo, pos_report_photo, store_stock_notes, 
                  1 if restaurant_cash_confirmed else 0, key_log_notes, tool_log_notes))
            result = cursor.fetchone()[0]
            self.connection.commit()
            return result
        except Exception as e:
            print(f"Error creating shift report: {e}")
            return None
        
    
    def get_shift_reports_list(self, date: str = None, limit: int = 20) -> list:
        """Get shift reports, optionally filtered by date"""
        try:
            cursor = self.connection.cursor()
            if date:
                cursor.execute("""
                    SELECT * FROM tbl_shift_reports 
                    WHERE shift_date = %s
                    ORDER BY shift_number, submitted_at DESC
                """, (date,))
            else:
                cursor.execute("""
                    SELECT * FROM tbl_shift_reports 
                    ORDER BY shift_date DESC, shift_number
                    LIMIT %s
                """, (limit,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting shift reports: {e}")
            return []
    
    def has_shift_report_submitted(self, telegram_user_id: int, shift_number: int, shift_date: str) -> bool:
        """Check if a shift report has been submitted by an employee for a specific shift and date
        
        Args:
            telegram_user_id: Telegram user ID (unique identifier)
            shift_number: Shift number (1, 2, 3)
            shift_date: Date in YYYY-MM-DD format
        
        Returns:
            True if report already submitted, False otherwise
        """
        try:
            # First get employee_id from telegram_user_id
            employee_result = self.execute_query(
                "SELECT employee_id FROM tbl_employeer WHERE telegram_user_id = %s",
                (telegram_user_id,)
            )
            
            if not employee_result:
                print(f"⚠️ No employee found for telegram_user_id: {telegram_user_id}")
                return False
            
            employee_id = employee_result[0][0]
            
            # Check if report exists for this employee_id
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM tbl_shift_reports 
                WHERE employee_id = %s AND shift_number = %s AND shift_date = %s
                AND status IN ('submitted', 'confirmed')
            """, (employee_id, shift_number, shift_date))
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            if count > 0:
                print(f"✅ Report already submitted: employee_id={employee_id}, telegram_id={telegram_user_id}, shift={shift_number}, date={shift_date}")
            
            return count > 0
        except Exception as e:
            print(f"Error checking shift report: {e}")
            return False
    
    def has_shift_report_task_created(self, employee_id: int, shift_number: int, shift_date: str) -> bool:
        """Check if a shift report task has already been created for this employee, shift, and date"""
        try:
            cursor = self.connection.cursor()
            # Check for existing task with shift report description pattern
            cursor.execute("""
                SELECT COUNT(*) FROM tbl_tasks 
                WHERE assignee_id = %s AND Date = %s
                AND (description LIKE '%%Shift Change Report%%' OR description LIKE '%%Izveštaj o promeni smene%%')
                AND description LIKE %s
            """, (employee_id, shift_date, f'%Shift {shift_number}%'))
            result = cursor.fetchone()
            count = result[0] if result else 0
            return count > 0
        except Exception as e:
            print(f"Error checking shift report task: {e}")
            return False
    
    def get_current_shift_number(self) -> int:
        """Get current shift number based on time"""
        from datetime import datetime
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM tbl_reception_shift WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return 1
            
            shift_count = row[1]  # shift_count column
            current_time = datetime.now().strftime('%H:%M')
            
            # Get shift times from row
            shifts = []
            for i in range(1, 5):
                start_idx = 2 + (i - 1) * 2
                end_idx = start_idx + 1
                if start_idx < len(row) and row[start_idx]:
                    shifts.append((row[start_idx], row[end_idx]))
            
            for i, (start, end) in enumerate(shifts[:shift_count], 1):
                if start and end:
                    # Handle overnight shifts (e.g., 21:00 - 05:00)
                    if start > end:
                        if current_time >= start or current_time < end:
                            return i
                    else:
                        if start <= current_time < end:
                            return i
            return 1
        except Exception as e:
            print(f"Error getting current shift: {e}")
            return 1

    def get_shift_report_task_id(self, telegram_user_id: int, shift_number: int, date: str) -> int:
        """Get the task ID for a shift report task
        
        Args:
            telegram_user_id: Telegram user ID
            shift_number: Shift number
            date: Date string (YYYY-MM-DD)
            
        Returns:
            Task ID if found, None otherwise
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id FROM tbl_tasks 
                WHERE assignee_id = %s 
                AND Date = %s 
                AND is_perform = 0
                AND (description LIKE '%%Shift Change Report%%' OR description LIKE '%%Izveštaj o promeni smene%%')
                AND description LIKE %s
                ORDER BY id DESC LIMIT 1
            """, (telegram_user_id, date, f'%Shift {shift_number}%'))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting shift report task ID: {e}")
            import traceback
            traceback.print_exc()
            return None


    def get_employee_work_role(self, employee_id: str) -> str:
        """
        Get employee work role
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Work role name or None
        """
        try:
            result = self.execute_query(
                "SELECT work_role FROM tbl_employeer WHERE employee_id = %s",
                (employee_id,)
            )
            if result and len(result) > 0 and result[0][0]:
                return result[0][0]
            return None
        except Exception as e:
            print(f"Work role retrieval error: {e}")
            return None
    
    def get_task_statistics(self):
        """Get overall task statistics"""
        try:
            # Total task count
            total = self.execute_query("SELECT COUNT(*) FROM tbl_tasks")[0][0]
            
            # Completed task count (is_perform=1 AND check_admin=1)
            completed = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE is_perform=1 AND check_admin=1"
            )[0][0]
            
            # In progress task count (is_perform=1 AND check_admin=0)
            in_progress = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE is_perform=1 AND check_admin=0"
            )[0][0]
            
            # Unassigned task count (assignee_name='Unassigned')
            unassigned = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE assignee_name='Unassigned'"
            )[0][0]
            
            # Assigned but not started task count (assignee_name!='Unassigned' AND is_perform=0)
            assigned_not_started = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE assignee_name!='Unassigned' AND is_perform=0"
            )[0][0]
            
            # Statistics by priority
            priority_stats = {}
            for priority in ["Low", "Normal", "Urgent"]:
                count = self.execute_query(
                    "SELECT COUNT(*) FROM tbl_tasks WHERE priority=%s", (priority,)
                )[0][0]
                priority_stats[priority] = count
            
            # Statistics by department
            dept_stats = self.execute_query("""
                SELECT department, COUNT(*) as count
                FROM tbl_tasks
                GROUP BY department
                ORDER BY count DESC
            """)
            
            return {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "unassigned": unassigned,
                "assigned_not_started": assigned_not_started,
                "priority": priority_stats,
                "departments": dept_stats
            }
        except Exception as e:
            print(f"Error getting task statistics: {e}")
            return None
    
    def get_daily_task_statistics(self):
        """Get today's task statistics"""
        try:
            from datetime import date
            today = date.today().isoformat()
            
            # Tasks created today
            created_today = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE date=%s", (today,)
            )[0][0]
            
            # Tasks due today
            due_today = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE due_date=%s", (today,)
            )[0][0]
            
            # Tasks completed today (created_at is today and check_admin=1)
            completed_today = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE DATE(created_at)=%s AND check_admin=1", (today,)
            )[0][0]
            
            # Today's task list
            tasks_today = self.execute_query("""
                SELECT id, date, department, assignee_name, description, priority, is_perform, check_admin
                FROM tbl_tasks
                WHERE date=%s OR due_date=%s
                ORDER BY priority DESC, id DESC
                LIMIT 20
            """, (today, today))
            
            return {
                "created_today": created_today,
                "due_today": due_today,
                "completed_today": completed_today,
                "tasks": tasks_today
            }
        except Exception as e:
            print(f"Error getting daily statistics: {e}")
            return None
    
    def get_weekly_task_statistics(self):
        """Get this week's task statistics"""
        try:
            from datetime import date, timedelta
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            # Tasks created this week
            created_this_week = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE date BETWEEN %s AND %s",
                (week_start.isoformat(), week_end.isoformat())
            )[0][0]
            
            # Tasks completed this week
            completed_this_week = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE DATE(created_at) BETWEEN %s AND %s AND check_admin=1",
                (week_start.isoformat(), week_end.isoformat())
            )[0][0]
            
            # Tasks due this week
            due_this_week = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE due_date BETWEEN %s AND %s",
                (week_start.isoformat(), week_end.isoformat())
            )[0][0]
            
            # Daily statistics
            daily_stats = []
            for i in range(7):
                day = week_start + timedelta(days=i)
                day_str = day.isoformat()
                created = self.execute_query(
                    "SELECT COUNT(*) FROM tbl_tasks WHERE date=%s", (day_str,)
                )[0][0]
                completed = self.execute_query(
                    "SELECT COUNT(*) FROM tbl_tasks WHERE DATE(created_at)=%s AND check_admin=1", (day_str,)
                )[0][0]
                daily_stats.append({
                    "date": day_str,
                    "day_name": day.strftime("%A"),
                    "created": created,
                    "completed": completed
                })
            
            return {
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "created_this_week": created_this_week,
                "completed_this_week": completed_this_week,
                "due_this_week": due_this_week,
                "daily_stats": daily_stats
            }
        except Exception as e:
            print(f"Error getting weekly statistics: {e}")
            return None
    
    def get_overview_report(self):
        """Get comprehensive hotel overview report"""
        try:
            from datetime import date, timedelta
            today = date.today()
            today_str = today.isoformat()
            
            # === Room Statistics ===
            total_rooms = self.execute_query("SELECT COUNT(*) FROM tbl_customer_rooms")[0][0]
            occupied = self.execute_query("SELECT COUNT(*) FROM tbl_customer_rooms WHERE is_check = 1")[0][0]
            available = total_rooms - occupied
            occupancy_rate = round((occupied / total_rooms * 100), 1) if total_rooms > 0 else 0
            
            # Room type distribution
            room_types = self.execute_query("""
                SELECT room_type, COUNT(*) as total, 
                       SUM(CASE WHEN is_check = 1 THEN 1 ELSE 0 END) as occupied
                FROM tbl_customer_rooms 
                GROUP BY room_type ORDER BY total DESC
            """) or []
            
            # === Task Statistics (Today) ===
            tasks_today = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE date = %s", (today_str,)
            )[0][0]
            tasks_pending = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE is_perform = 0 AND is_check = 0"
            )[0][0]
            tasks_completed_today = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE DATE(task_completed_at) = %s", (today_str,)
            )[0][0]
            tasks_total = self.execute_query("SELECT COUNT(*) FROM tbl_tasks")[0][0]
            tasks_done = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE check_admin = 1"
            )[0][0]
            
            # Tasks by department
            dept_tasks = self.execute_query("""
                SELECT department, COUNT(*) as total,
                       SUM(CASE WHEN check_admin = 1 THEN 1 ELSE 0 END) as done
                FROM tbl_tasks GROUP BY department ORDER BY total DESC
            """) or []
            
            # === Employee Statistics ===
            total_employees = self.execute_query("SELECT COUNT(*) FROM tbl_employeer")[0][0]
            
            # Top performers (most tasks completed)
            top_performers = self.execute_query("""
                SELECT assignee_name, COUNT(*) as completed
                FROM tbl_tasks WHERE check_admin = 1
                GROUP BY assignee_name ORDER BY completed DESC LIMIT 5
            """) or []
            
            # === Shift Reports (Today) ===
            shifts_today = self.execute_query(
                "SELECT COUNT(*) FROM tbl_shift_reports WHERE shift_date = %s", (today_str,)
            )[0][0]
            
            # === Recent Activity (last 7 days) ===
            week_ago = (today - timedelta(days=7)).isoformat()
            tasks_week = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE date BETWEEN %s AND %s",
                (week_ago, today_str)
            )[0][0]
            completed_week = self.execute_query(
                "SELECT COUNT(*) FROM tbl_tasks WHERE DATE(task_completed_at) BETWEEN %s AND %s",
                (week_ago, today_str)
            )[0][0]
            
            # === Revenue estimate ===
            revenue = self.execute_query("""
                SELECT COALESCE(SUM(price_per_night), 0) FROM tbl_customer_rooms WHERE is_check = 1
            """)[0][0]
            
            # === Complaints ===
            try:
                complaints_pending = self.execute_query(
                    "SELECT COUNT(*) FROM tbl_complaints WHERE confirmed = 0"
                )[0][0]
            except:
                complaints_pending = 0
            
            return {
                'rooms': {
                    'total': total_rooms, 'occupied': occupied, 'available': available,
                    'occupancy_rate': occupancy_rate, 'room_types': room_types
                },
                'tasks': {
                    'today': tasks_today, 'pending': tasks_pending,
                    'completed_today': tasks_completed_today,
                    'total': tasks_total, 'done': tasks_done,
                    'dept_tasks': dept_tasks
                },
                'employees': {
                    'total': total_employees, 'top_performers': top_performers
                },
                'shifts_today': shifts_today,
                'week': {
                    'tasks': tasks_week, 'completed': completed_week
                },
                'revenue_daily': float(revenue),
                'complaints_pending': complaints_pending
            }
        except Exception as e:
            print(f"Error getting overview report: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    # ==================== Shift Report Methods ====================
    
    def create_shift_report(self, shift_date: str = None, shift_number: int = 1, employee_id: int = None,
                           reservations_count: int = 0, arrivals_count: int = 0, cash_amount: float = 0,
                           cash_photo: str = None, pos_report_photo: str = None, store_stock_notes: str = None,
                           restaurant_cash_confirmed: bool = False, key_log_notes: str = None,
                           tool_log_notes: str = None) -> int:
        """Create a new shift report"""
        try:
            from datetime import date as dt
            if shift_date is None:
                shift_date = dt.today().isoformat()
            
            # Get employee name by employee_id
            try:
                name_result = self.execute_query(
                    "SELECT name FROM tbl_employeer WHERE employee_id = %s OR CAST(telegram_user_id AS TEXT) = %s",
                    (str(employee_id), str(employee_id))
                )
                employee_name = name_result[0][0] if name_result else 'Unknown'
            except:
                employee_name = 'Unknown'
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO tbl_shift_reports 
                (shift_date, shift_number, employee_id, employee_name, reservations_count, arrivals_count,
                 departures_count, issues_notes, cash_amount, cash_photo, pos_report_photo,
                 store_stock_notes, restaurant_cash_confirmed, key_log_notes, tool_log_notes,
                 additional_notes, status)
                VALUES (%s, %s, %s, %s, %s, %s, 0, '', %s, %s, %s, %s, %s, %s, %s, '', 'submitted')
                RETURNING id
            """, (shift_date, shift_number, employee_id, employee_name, reservations_count, arrivals_count,
                  cash_amount, cash_photo, pos_report_photo, store_stock_notes, 
                  1 if restaurant_cash_confirmed else 0, key_log_notes, tool_log_notes))
            result = cursor.fetchone()[0]
            self.connection.commit()
            return result
        except Exception as e:
            print(f"Error creating shift report: {e}")
            return None
    
    def get_shift_reports(self, date: str = None, limit: int = 20) -> list:
        """Get shift reports, optionally filtered by date"""
        try:
            cursor = self.connection.cursor()
            if date:
                cursor.execute("""
                    SELECT * FROM tbl_shift_reports 
                    WHERE shift_date = %s
                    ORDER BY shift_number, submitted_at DESC
                """, (date,))
            else:
                cursor.execute("""
                    SELECT * FROM tbl_shift_reports 
                    ORDER BY shift_date DESC, shift_number
                    LIMIT %s
                """, (limit,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting shift reports: {e}")
            return []
    
    def get_current_shift(self) -> int:
        """Get current shift number based on time"""
        from datetime import datetime
        try:
            settings = get_shift_settings(self)
            if not settings:
                return 1
            
            current_time = datetime.now().strftime('%H:%M')
            shift_count = settings['shift_count']
            
            for i in range(1, shift_count + 1):
                start = settings.get(f'shift_{i}_start')
                end = settings.get(f'shift_{i}_end')
                if start and end:
                    # Handle overnight shifts (e.g., 21:00 - 05:00)
                    if start > end:
                        if current_time >= start or current_time < end:
                            return i
                    else:
                        if start <= current_time < end:
                            return i
            return 1
        except Exception as e:
            print(f"Error getting current shift: {e}")
            return 1


def get_database_connection() -> DatabaseManager:
    """
    Create and return PostgreSQL database connection
    
    Returns:
        DatabaseManager instance
    """
    db_manager = DatabaseManager()
    db_manager.connect()
    return db_manager


# ==================== Room Management Functions ====================

def get_all_floors(db: DatabaseManager) -> list:
    """
    Get list of all floors from customer rooms
    
    Returns:
        List of floor numbers extracted from room IDs (e.g., '101' -> '1', '201' -> '2')
    """
    try:
        result = db.execute_query("""
            SELECT DISTINCT floor
            FROM tbl_customer_rooms 
            WHERE floor IS NOT NULL
            ORDER BY floor
        """)
        return [str(row[0]) for row in result] if result else []
    except Exception as e:
        print(f"Error getting floors: {e}")
        return []


def get_floors_with_rooms(db: DatabaseManager) -> list:
    """
    Get list of floors that have at least one room
    
    Returns:
        List of floor numbers as strings (e.g., ['1', '2', '3'])
    """
    try:
        result = db.execute_query("""
            SELECT DISTINCT floor
            FROM tbl_customer_rooms
            WHERE floor IS NOT NULL
            ORDER BY floor
        """)
        return [str(row[0]) for row in result] if result else []
    except Exception as e:
        print(f"Error getting floors with rooms: {e}")
        return []


def get_rooms_by_floor(db: DatabaseManager, floor: str) -> list:
    """
    Get all rooms on a specific floor
    
    Args:
        floor: Floor number (e.g., '1', '2')
        
    Returns:
        List of room tuples (id, id_room, is_check, AC, TV, Toilet, Remote_Control, is_active, total_capacity, current_guests)
    """
    try:
        result = db.execute_query("""
            SELECT id, id_room, is_check, AC, TV, Toilet, Remote_Control, 
                   COALESCE(is_active, 1) as is_active,
                   COALESCE(total_capacity, 2) as total_capacity,
                   COALESCE(current_guests, 0) as current_guests
            FROM tbl_customer_rooms 
            WHERE floor = %s
            ORDER BY id
        """, (int(floor),))
        return result if result else []
    except Exception as e:
        print(f"Error getting rooms by floor: {e}")
        return []


def get_room_by_id(db: DatabaseManager, room_id: int) -> dict:
    """
    Get room details by room ID
    
    Args:
        room_id: Room database ID
        
    Returns:
        Dictionary with room details
    """
    try:
        result = db.execute_query("""
            SELECT id, id_room, is_check, AC, TV, Toilet, Remote_Control, 
                   COALESCE(is_active, 1) as is_active, created_at,
                   COALESCE(total_capacity, 2) as total_capacity,
                   COALESCE(current_guests, 0) as current_guests
            FROM tbl_customer_rooms 
            WHERE id = %s
        """, (room_id,))
        if result:
            row = result[0]
            return {
                "id": row[0],
                "id_room": row[1],
                "is_check": row[2],
                "AC": row[3],
                "TV": row[4],
                "Toilet": row[5],
                "Remote_Control": row[6],
                "is_active": row[7],
                "created_at": row[8],
                "total_capacity": row[9],
                "current_guests": row[10]
            }
        return None
    except Exception as e:
        print(f"Error getting room by ID: {e}")
        return None


def toggle_room_active(db: DatabaseManager, room_id: int) -> bool:
    """
    Toggle room is_active status (0 -> 1, 1 -> 0)
    
    Args:
        room_id: Room database ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query("""
            UPDATE tbl_customer_rooms 
            SET is_active = CASE WHEN COALESCE(is_active, 1) = 1 THEN 0 ELSE 1 END
            WHERE id = %s
        """, (room_id,))
        return True
    except Exception as e:
        print(f"Error toggling room active status: {e}")
        return False


def update_room_equipment(db: DatabaseManager, room_id: int, equipment: str, value: str) -> bool:
    """
    Update room equipment status
    
    Args:
        room_id: Room database ID
        equipment: Equipment name (AC, TV, Toilet, Remote_Control)
        value: New value ('1' for working, '0' for not working)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        valid_equipment = ['AC', 'TV', 'Toilet', 'Remote_Control']
        if equipment not in valid_equipment:
            return False
        
        query = f"UPDATE tbl_customer_rooms SET {equipment} = %s WHERE id = %s"
        db.execute_query(query, (value, room_id))
        return True
    except Exception as e:
        print(f"Error updating room equipment: {e}")
        return False


def update_room_guests(db: DatabaseManager, room_id: int, current_guests: int) -> bool:
    """
    Update current guests count for a room
    
    Args:
        room_id: Room database ID
        current_guests: Number of current guests
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query(
            "UPDATE tbl_customer_rooms SET current_guests = %s WHERE id = %s",
            (current_guests, room_id)
        )
        return True
    except Exception as e:
        print(f"Error updating room guests: {e}")
        return False


def update_room_capacity(db: DatabaseManager, room_id: int, total_capacity: int) -> bool:
    """
    Update room total capacity
    
    Args:
        room_id: Room database ID
        total_capacity: Total capacity of the room
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query(
            "UPDATE tbl_customer_rooms SET total_capacity = %s WHERE id = %s",
            (total_capacity, room_id)
        )
        return True
    except Exception as e:
        print(f"Error updating room capacity: {e}")
        return False


def create_room(db: DatabaseManager, id_room: str) -> bool:
    """
    Create a new room
    
    Args:
        id_room: Room number (e.g., '301', '302')
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query("""
            INSERT INTO tbl_customer_rooms (id_room, is_check, AC, TV, Toilet, Remote_Control, is_active, created_at)
            VALUES (%s, 0, '1', '1', '1', '1', 1, NOW())
        """, (id_room,))
        return True
    except Exception as e:
        print(f"Error creating room: {e}")
        return False


def delete_room(db: DatabaseManager, room_id: int) -> bool:
    """
    Delete a room
    
    Args:
        room_id: Room database ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query("DELETE FROM tbl_customer_rooms WHERE id = %s", (room_id,))
        return True
    except Exception as e:
        print(f"Error deleting room: {e}")
        return False


def get_room_count_by_floor(db: DatabaseManager) -> list:
    """
    Get room count statistics for each floor
    
    Returns:
        List of tuples (floor, total_rooms, active_rooms, inactive_rooms)
    """
    try:
        result = db.execute_query("""
            SELECT 
                floor,
                COUNT(*) as total,
                SUM(CASE WHEN COALESCE(is_active, 1) = 1 THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN COALESCE(is_active, 1) = 0 THEN 1 ELSE 0 END) as inactive
            FROM tbl_customer_rooms 
            WHERE floor IS NOT NULL
            GROUP BY floor
            ORDER BY floor
        """)
        return result if result else []
    except Exception as e:
        print(f"Error getting room count by floor: {e}")
        return []


def create_room_inactive(db: DatabaseManager, id_room: str) -> bool:
    """
    Create a new room with is_active=0 (inactive, pending approval)
    
    Args:
        id_room: Room number (e.g., '105', '112', '301')
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query("""
            INSERT INTO tbl_customer_rooms (id_room, is_check, AC, TV, Toilet, Remote_Control, is_active, created_at)
            VALUES (%s, 0, '1', '1', '1', '1', 0, NOW())
        """, (id_room,))
        print(f"✅ Room created (inactive): {id_room}")
        return True
    except Exception as e:
        print(f"Error creating room (inactive): {e}")
        return False


# ==================== WORK ROLES MANAGEMENT ====================

def get_all_work_roles(db: DatabaseManager) -> list:
    """
    Get all work roles
    
    Returns:
        List of work roles [(id, role_name, description, created_at), ...]
    """
    try:
        result = db.execute_query(
            "SELECT id, role_name, description, created_at FROM tbl_work_roles ORDER BY role_name"
        )
        return result if result else []
    except Exception as e:
        print(f"Error getting work roles: {e}")
        return []


def get_work_role_by_id(db: DatabaseManager, role_id: int) -> dict:
    """
    Get work role by ID
    
    Args:
        role_id: Work role ID
        
    Returns:
        Work role dict or None
    """
    try:
        result = db.execute_query(
            "SELECT id, role_name, description, created_at FROM tbl_work_roles WHERE id = %s",
            (role_id,)
        )
        if result and len(result) > 0:
            return {
                "id": result[0][0],
                "role_name": result[0][1],
                "description": result[0][2],
                "created_at": result[0][3]
            }
        return None
    except Exception as e:
        print(f"Error getting work role by ID: {e}")
        return None


def add_work_role(db: DatabaseManager, role_name: str, description: str = None) -> bool:
    """
    Add new work role
    
    Args:
        role_name: Role name
        description: Role description (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query(
            "INSERT INTO tbl_work_roles (role_name, description) VALUES (%s, %s)",
            (role_name, description)
        )
        print(f"✅ Work role added: {role_name}")
        return True
    except Exception as e:
        print(f"Error adding work role: {e}")
        return False


def update_work_role(db: DatabaseManager, role_id: int, role_name: str = None, description: str = None) -> bool:
    """
    Update work role
    
    Args:
        role_id: Work role ID
        role_name: New role name (optional)
        description: New description (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if role_name and description is not None:
            db.execute_query(
                "UPDATE tbl_work_roles SET role_name = %s, description = %s WHERE id = %s",
                (role_name, description, role_id)
            )
        elif role_name:
            db.execute_query(
                "UPDATE tbl_work_roles SET role_name = %s WHERE id = %s",
                (role_name, role_id)
            )
        elif description is not None:
            db.execute_query(
                "UPDATE tbl_work_roles SET description = %s WHERE id = %s",
                (description, role_id)
            )
        print(f"✅ Work role updated: ID {role_id}")
        return True
    except Exception as e:
        print(f"Error updating work role: {e}")
        return False


def delete_work_role(db: DatabaseManager, role_id: int) -> bool:
    """
    Delete work role
    
    Args:
        role_id: Work role ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query("DELETE FROM tbl_work_roles WHERE id = %s", (role_id,))
        print(f"✅ Work role deleted: ID {role_id}")
        return True
    except Exception as e:
        print(f"Error deleting work role: {e}")
        return False


def get_work_role_by_name(db: DatabaseManager, role_name: str) -> dict:
    """
    Get work role by name
    
    Args:
        role_name: Role name
        
    Returns:
        Work role dict or None
    """
    try:
        result = db.execute_query(
            "SELECT id, role_name, description, created_at FROM tbl_work_roles WHERE role_name = %s",
            (role_name,)
        )
        if result and len(result) > 0:
            return {
                "id": result[0][0],
                "role_name": result[0][1],
                "description": result[0][2],
                "created_at": result[0][3]
            }
        return None
    except Exception as e:
        print(f"Error getting work role by name: {e}")
        return None


def get_hotel_settings(db: DatabaseManager) -> dict:
    """
    Get hotel settings
    
    Returns:
        Settings dict with total_rooms, hotel_name, etc.
    """
    try:
        result = db.execute_query(
            "SELECT id, total_rooms, hotel_name, updated_at FROM tbl_hotel_settings WHERE id = 1"
        )
        if result and len(result) > 0:
            return {
                "id": result[0][0],
                "total_rooms": result[0][1],
                "hotel_name": result[0][2],
                "updated_at": result[0][3]
            }
        return {"id": 1, "total_rooms": 0, "hotel_name": "Hotel", "updated_at": None}
    except Exception as e:
        print(f"Error getting hotel settings: {e}")
        return {"id": 1, "total_rooms": 0, "hotel_name": "Hotel", "updated_at": None}


def update_hotel_settings(db: DatabaseManager, total_rooms: int = None, hotel_name: str = None) -> bool:
    """
    Update hotel settings
    
    Args:
        total_rooms: Total number of rooms (optional)
        hotel_name: Hotel name (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        updates = []
        params = []
        
        if total_rooms is not None:
            updates.append("total_rooms = %s")
            params.append(total_rooms)
        
        if hotel_name is not None:
            updates.append("hotel_name = %s")
            params.append(hotel_name)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(1)  # WHERE id = 1
        
        query = f"UPDATE tbl_hotel_settings SET {', '.join(updates)} WHERE id = %s"
        db.execute_query(query, tuple(params))
        print(f"✅ Hotel settings updated")
        return True
    except Exception as e:
        print(f"Error updating hotel settings: {e}")
        return False


# ==================== HOTEL ROOMS MANAGEMENT ====================

def get_all_hotel_rooms(db: DatabaseManager) -> list:
    """
    Get all hotel rooms (non-guest rooms)
    
    Returns:
        List of rooms [(id, name, description, state, created_at, updated_at), ...]
    """
    try:
        result = db.execute_query("""
            SELECT id, name, description, state, created_at, updated_at
            FROM tbl_hotel_rooms
            ORDER BY state DESC, name ASC
        """)
        return result if result else []
    except Exception as e:
        print(f"Error getting hotel rooms: {e}")
        return []


def get_hotel_room_by_id(db: DatabaseManager, room_id: int) -> dict:
    """
    Get hotel room by ID
    
    Args:
        room_id: Room ID
        
    Returns:
        Room dict or None
    """
    try:
        result = db.execute_query("""
            SELECT id, name, description, state, created_by, created_at, updated_at
            FROM tbl_hotel_rooms WHERE id = %s
        """, (room_id,))
        
        if result and len(result) > 0:
            return {
                "id": result[0][0],
                "name": result[0][1],
                "description": result[0][2],
                "state": result[0][3],
                "created_by": result[0][4],
                "created_at": result[0][5],
                "updated_at": result[0][6]
            }
        return None
    except Exception as e:
        print(f"Error getting hotel room by ID: {e}")
        return None


def create_hotel_room(db: DatabaseManager, name: str, description: str, created_by: int) -> int:
    """
    Create new hotel room
    
    Args:
        name: Room name
        description: Room description
        created_by: Creator's telegram user ID
        
    Returns:
        Created room ID or None
    """
    try:
        result = db.execute_query("""
            INSERT INTO tbl_hotel_rooms (name, description, state, created_by)
            VALUES (%s, %s, 1, %s)
            RETURNING id
        """, (name, description, created_by))
        
        room_id = result[0][0] if result else None
        print(f"✅ Hotel room created: {name} (ID: {room_id})")
        return room_id
    except Exception as e:
        print(f"Error creating hotel room: {e}")
        return None


def update_hotel_room(db: DatabaseManager, room_id: int, name: str = None, description: str = None) -> bool:
    """
    Update hotel room info
    
    Args:
        room_id: Room ID
        name: New name (optional)
        description: New description (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(room_id)
        
        query = f"UPDATE tbl_hotel_rooms SET {', '.join(updates)} WHERE id = %s"
        db.execute_query(query, tuple(params))
        print(f"✅ Hotel room updated: ID {room_id}")
        return True
    except Exception as e:
        print(f"Error updating hotel room: {e}")
        return False


def toggle_hotel_room_state(db: DatabaseManager, room_id: int) -> bool:
    """
    Toggle hotel room state (0 <-> 1)
    
    Args:
        room_id: Room ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query("""
            UPDATE tbl_hotel_rooms 
            SET state = CASE WHEN state = 1 THEN 0 ELSE 1 END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (room_id,))
        print(f"✅ Hotel room state toggled: ID {room_id}")
        return True
    except Exception as e:
        print(f"Error toggling hotel room state: {e}")
        return False


def delete_hotel_room(db: DatabaseManager, room_id: int) -> bool:
    """
    Delete hotel room
    
    Args:
        room_id: Room ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query("DELETE FROM tbl_hotel_rooms WHERE id = %s", (room_id,))
        print(f"✅ Hotel room deleted: ID {room_id}")
        return True
    except Exception as e:
        print(f"Error deleting hotel room: {e}")
        return False


# ==================== Key History Management Functions ====================

def get_active_rooms_for_keys(db: DatabaseManager):
    """
    Get all active hotel rooms (state=1) for key management
    
    Returns:
        List of tuples: (id, name, description)
    """
    try:
        result = db.execute_query("""
            SELECT id, name, description 
            FROM tbl_hotel_rooms 
            WHERE state = 1 
            ORDER BY name
        """)
        return result if result else []
    except Exception as e:
        print(f"Error getting active rooms for keys: {e}")
        return []


def create_key_record(db: DatabaseManager, room_id: int, room_name: str, 
                     person_name: str, person_telegram_id: int, purpose: str,
                     taken_photo: str = None, taken_video: str = None,
                     created_by: int = None) -> int:
    """
    Create new key taking record
    
    Args:
        room_id: Hotel room ID
        room_name: Room name
        person_name: Name of person taking the key
        person_telegram_id: Telegram user ID of person
        purpose: Purpose of taking key
        taken_photo: File ID of photo evidence (optional)
        taken_video: File ID of video evidence (optional)
        created_by: Telegram user ID who created the record
        
    Returns:
        Record ID if successful, None otherwise
    """
    try:
        result = db.execute_query("""
            INSERT INTO tbl_key_history 
            (room_id, room_name, person_name, person_telegram_id, purpose, 
             taken_photo, taken_video, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Opened', %s)
            RETURNING id
        """, (room_id, room_name, person_name, person_telegram_id, purpose,
              taken_photo, taken_video, created_by))
        
        record_id = result[0][0] if result else None
        print(f"✅ Key record created: ID {record_id} for room '{room_name}'")
        return record_id
    except Exception as e:
        print(f"Error creating key record: {e}")
        return None


def return_key(db: DatabaseManager, record_id: int, 
               returned_photo: str = None, returned_video: str = None) -> bool:
    """
    Mark key as returned
    
    Args:
        record_id: Key history record ID
        returned_photo: File ID of return photo evidence (optional)
        returned_video: File ID of return video evidence (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query("""
            UPDATE tbl_key_history 
            SET returned_at = CURRENT_TIMESTAMP,
                returned_photo = %s,
                returned_video = %s,
                status = 'Returned'
            WHERE id = %s
        """, (returned_photo, returned_video, record_id))
        print(f"✅ Key returned: Record ID {record_id}")
        return True
    except Exception as e:
        print(f"Error returning key: {e}")
        return False


def get_open_key_records(db: DatabaseManager):
    """
    Get all open (not returned) key records
    
    Returns:
        List of tuples: (id, room_name, person_name, purpose, taken_at, status, room_id)
    """
    try:
        result = db.execute_query("""
            SELECT id, room_name, person_name, purpose, taken_at, status, room_id
            FROM tbl_key_history 
            WHERE status = 'Opened'
            ORDER BY taken_at DESC
        """)
        return result if result else []
    except Exception as e:
        print(f"Error getting open key records: {e}")
        return []


def get_key_record_by_id(db: DatabaseManager, record_id: int):
    """
    Get key record details by ID
    
    Returns:
        Dict with record details or None
    """
    try:
        result = db.execute_query("""
            SELECT id, room_id, room_name, person_name, person_telegram_id, 
                   purpose, taken_at, taken_photo, taken_video,
                   returned_at, returned_photo, returned_video, status
            FROM tbl_key_history 
            WHERE id = %s
        """, (record_id,))
        
        if result and len(result) > 0:
            row = result[0]
            return {
                'id': row[0],
                'room_id': row[1],
                'room_name': row[2],
                'person_name': row[3],
                'person_telegram_id': row[4],
                'purpose': row[5],
                'taken_at': row[6],
                'taken_photo': row[7],
                'taken_video': row[8],
                'returned_at': row[9],
                'returned_photo': row[10],
                'returned_video': row[11],
                'status': row[12]
            }
        return None
    except Exception as e:
        print(f"Error getting key record: {e}")
        return None


def get_all_key_records(db: DatabaseManager, limit: int = 50):
    """
    Get all key records (returns dictionaries for easy access)
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        List of dicts with keys: id, room_name, person_name, purpose, borrowed_at, returned_at, status
    """
    try:
        result = db.execute_query("""
            SELECT id, room_name, person_name, purpose, taken_at, returned_at, status
            FROM tbl_key_history 
            ORDER BY taken_at DESC
            LIMIT %s
        """, (limit,))
        
        if result:
            records = []
            for row in result:
                records.append({
                    'id': row[0],
                    'room_name': row[1],
                    'person_name': row[2],
                    'purpose': row[3],
                    'borrowed_at': row[4],  # taken_at as borrowed_at for compatibility
                    'returned_at': row[5],
                    'status': row[6]
                })
            return records
        return []
    except Exception as e:
        print(f"Error getting all key records: {e}")
        return []


def get_all_key_history(db: DatabaseManager, limit: int = 50):
    """
    Get key history records (all statuses)
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        List of tuples: (id, room_name, person_name, purpose, taken_at, returned_at, status)
    """
    try:
        result = db.execute_query("""
            SELECT id, room_name, person_name, purpose, taken_at, returned_at, status
            FROM tbl_key_history 
            ORDER BY taken_at DESC
            LIMIT %s
        """, (limit,))
        return result if result else []
    except Exception as e:
        print(f"Error getting key history: {e}")
        return []


def update_key_status_delayed(db: DatabaseManager, record_id: int) -> bool:
    """
    Update key record status to 'Delayed'
    
    Args:
        record_id: Key history record ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db.execute_query("""
            UPDATE tbl_key_history 
            SET status = 'Delayed'
            WHERE id = %s
        """, (record_id,))
        print(f"✅ Key status updated to Delayed: Record ID {record_id}")
        return True
    except Exception as e:
        print(f"Error updating key status: {e}")
        return False


def get_borrowed_room_ids(db):
    """
    Get list of room_ids that currently have borrowed keys (status='Opened')
    Returns a set of room_ids for quick lookup
    """
    try:
        result = db.execute_query("""
            SELECT DISTINCT room_id FROM tbl_key_history
            WHERE status = 'Opened'
        """)
        
        if result:
            # result is list of dicts or sqlite3.Row, access by key or index
            borrowed_set = set()
            for row in result:
                if isinstance(row, dict):
                    borrowed_set.add(row['room_id'])
                else:
                    borrowed_set.add(row[0])  # First column is room_id
            return borrowed_set
        return set()
    except Exception as e:
        print(f"Error getting borrowed room ids: {e}")
        return set()


# ==================== TOOL MANAGEMENT FUNCTIONS ====================

def get_all_tools(db: DatabaseManager):
    """
    Get all tools (active)
    
    Returns:
        List of dicts with tool info
    """
    try:
        result = db.execute_query("""
            SELECT id, name, description, total_quantity, available_quantity, state
            FROM tbl_hotel_tools 
            WHERE state = 1
            ORDER BY name
        """)
        if result:
            tools = []
            for row in result:
                tools.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'total_quantity': row[3],
                    'available_quantity': row[4],
                    'state': row[5]
                })
            return tools
        return []
    except Exception as e:
        print(f"Error getting all tools: {e}")
        return []


def get_tool_by_id(db: DatabaseManager, tool_id: int):
    """
    Get tool by ID
    
    Returns:
        Dict with tool info or None
    """
    try:
        result = db.execute_query("""
            SELECT id, name, description, total_quantity, available_quantity, state, created_by, created_at, updated_at
            FROM tbl_hotel_tools WHERE id = %s
        """, (tool_id,))
        
        if result and len(result) > 0:
            row = result[0]
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'total_quantity': row[3],
                'available_quantity': row[4],
                'state': row[5],
                'created_by': row[6],
                'created_at': row[7],
                'updated_at': row[8]
            }
        return None
    except Exception as e:
        print(f"Error getting tool by ID: {e}")
        return None


def create_tool(db: DatabaseManager, name: str, description: str, quantity: int, created_by: int) -> int:
    """
    Create new tool
    
    Returns:
        Tool ID or None
    """
    try:
        result = db.execute_query("""
            INSERT INTO tbl_hotel_tools (name, description, total_quantity, available_quantity, created_by)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (name, description, quantity, quantity, created_by))
        
        if result and len(result) > 0:
            tool_id = result[0][0]
            print(f"✅ Tool created: ID {tool_id}, Name '{name}', Qty {quantity}")
            return tool_id
        return None
    except Exception as e:
        print(f"Error creating tool: {e}")
        return None


def update_tool(db: DatabaseManager, tool_id: int, name: str = None, description: str = None, 
                total_quantity: int = None, state: int = None) -> bool:
    """
    Update tool info
    """
    try:
        tool = get_tool_by_id(db, tool_id)
        if not tool:
            return False
        
        new_name = name if name is not None else tool['name']
        new_desc = description if description is not None else tool['description']
        new_total = total_quantity if total_quantity is not None else tool['total_quantity']
        new_state = state if state is not None else tool['state']
        
        # Calculate new available quantity if total changed
        old_total = tool['total_quantity']
        old_available = tool['available_quantity']
        borrowed = old_total - old_available
        new_available = max(0, new_total - borrowed)
        
        db.execute_query("""
            UPDATE tbl_hotel_tools 
            SET name = %s, description = %s, total_quantity = %s, available_quantity = %s, state = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_name, new_desc, new_total, new_available, new_state, tool_id))
        
        print(f"✅ Tool updated: ID {tool_id}")
        return True
    except Exception as e:
        print(f"Error updating tool: {e}")
        return False


def delete_tool(db: DatabaseManager, tool_id: int) -> bool:
    """
    Delete tool (soft delete - set state to 0)
    """
    try:
        db.execute_query("""
            UPDATE tbl_hotel_tools SET state = 0, updated_at = CURRENT_TIMESTAMP WHERE id = %s
        """, (tool_id,))
        print(f"✅ Tool deleted (soft): ID {tool_id}")
        return True
    except Exception as e:
        print(f"Error deleting tool: {e}")
        return False


# ==================== TOOL HISTORY FUNCTIONS ====================

def borrow_tool(db: DatabaseManager, tool_id: int, tool_name: str, quantity: int,
                person_name: str, person_telegram_id: int, purpose: str,
                taken_photo: str = None, taken_video: str = None,
                created_by: int = None) -> int:
    """
    Borrow tool (create history record and decrease available quantity)
    
    Returns:
        History record ID or None
    """
    try:
        # Check if enough quantity available
        tool = get_tool_by_id(db, tool_id)
        if not tool or tool['available_quantity'] < quantity:
            print(f"❌ Not enough tools available: requested {quantity}, available {tool['available_quantity'] if tool else 0}")
            return None
        
        # Create history record
        result = db.execute_query("""
            INSERT INTO tbl_tool_history 
            (tool_id, tool_name, quantity, person_name, person_telegram_id, purpose, taken_photo, taken_video, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (tool_id, tool_name, quantity, person_name, person_telegram_id, purpose, taken_photo, taken_video, created_by))
        
        # Update available quantity
        new_available = tool['available_quantity'] - quantity
        db.execute_query("""
            UPDATE tbl_hotel_tools SET available_quantity = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s
        """, (new_available, tool_id))
        
        if result and len(result) > 0:
            record_id = result[0][0]
            print(f"✅ Tool borrowed: Record ID {record_id}, Tool '{tool_name}', Qty {quantity}")
            return record_id
        return None
    except Exception as e:
        print(f"Error borrowing tool: {e}")
        return None


def return_tool(db: DatabaseManager, record_id: int, returned_photo: str = None, returned_video: str = None) -> bool:
    """
    Return tool (update history record and increase available quantity)
    """
    try:
        # Get record info
        result = db.execute_query("""
            SELECT tool_id, quantity, status FROM tbl_tool_history WHERE id = %s
        """, (record_id,))
        
        if not result or len(result) == 0:
            return False
        
        tool_id = result[0][0]
        quantity = result[0][1]
        status = result[0][2]
        
        if status == 'Returned':
            print(f"⚠️ Tool already returned: Record ID {record_id}")
            return False
        
        # Update history record
        db.execute_query("""
            UPDATE tbl_tool_history 
            SET status = 'Returned', returned_at = CURRENT_TIMESTAMP, returned_photo = %s, returned_video = %s
            WHERE id = %s
        """, (returned_photo, returned_video, record_id))
        
        # Update available quantity
        tool = get_tool_by_id(db, tool_id)
        if tool:
            new_available = min(tool['total_quantity'], tool['available_quantity'] + quantity)
            db.execute_query("""
                UPDATE tbl_hotel_tools SET available_quantity = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s
            """, (new_available, tool_id))
        
        print(f"✅ Tool returned: Record ID {record_id}")
        return True
    except Exception as e:
        print(f"Error returning tool: {e}")
        return False


def get_open_tool_records(db: DatabaseManager):
    """
    Get all open (not returned) tool records
    
    Returns:
        List of dicts with record info
    """
    try:
        result = db.execute_query("""
            SELECT id, tool_id, tool_name, quantity, person_name, purpose, taken_at, status
            FROM tbl_tool_history 
            WHERE status = 'Opened'
            ORDER BY taken_at DESC
        """)
        if result:
            records = []
            for row in result:
                records.append({
                    'id': row[0],
                    'tool_id': row[1],
                    'tool_name': row[2],
                    'quantity': row[3],
                    'person_name': row[4],
                    'purpose': row[5],
                    'taken_at': row[6],
                    'status': row[7]
                })
            return records
        return []
    except Exception as e:
        print(f"Error getting open tool records: {e}")
        return []


def get_tool_record_by_id(db: DatabaseManager, record_id: int):
    """
    Get tool history record by ID
    """
    try:
        result = db.execute_query("""
            SELECT id, tool_id, tool_name, quantity, person_name, person_telegram_id,
                   purpose, taken_at, taken_photo, taken_video,
                   returned_at, returned_photo, returned_video, status
            FROM tbl_tool_history WHERE id = %s
        """, (record_id,))
        
        if result and len(result) > 0:
            row = result[0]
            return {
                'id': row[0],
                'tool_id': row[1],
                'tool_name': row[2],
                'quantity': row[3],
                'person_name': row[4],
                'person_telegram_id': row[5],
                'purpose': row[6],
                'taken_at': row[7],
                'taken_photo': row[8],
                'taken_video': row[9],
                'returned_at': row[10],
                'returned_photo': row[11],
                'returned_video': row[12],
                'status': row[13]
            }
        return None
    except Exception as e:
        print(f"Error getting tool record by ID: {e}")
        return None


# ==================== Clean History Functions ====================

def create_clean_record(db: DatabaseManager, room_id: int, room_number: str, floor: int,
                        clean_type: str, clean_status: str, condition: str, notes: str,
                        photo: str, video: str, cleaned_by: int, cleaned_by_name: str) -> int:
    """
    Create a cleaning record
    
    Args:
        clean_type: 'guest_room', 'staff_room', 'common_area'
        clean_status: 'Completed', 'Partial', 'Skipped', 'Issue'
    
    Returns:
        Record ID or None
    """
    try:
        result = db.execute_query("""
            INSERT INTO tbl_clean_history 
            (room_id, room_number, floor, clean_type, clean_status, condition, notes, photo, video, cleaned_by, cleaned_by_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (room_id, room_number, floor, clean_type, clean_status, condition, notes, photo, video, cleaned_by, cleaned_by_name))
        
        if result and len(result) > 0:
            record_id = result[0][0]
            print(f"✅ Clean record created: ID {record_id}, Room '{room_number}', Type '{clean_type}'")
            return record_id
        return None
    except Exception as e:
        print(f"Error creating clean record: {e}")
        return None


def get_today_clean_records(db: DatabaseManager, clean_type: str = None) -> list:
    """Get today's cleaning records"""
    try:
        if clean_type:
            result = db.execute_query("""
                SELECT id, room_id, room_number, floor, clean_type, clean_status, condition, notes, 
                       photo, video, cleaned_by, cleaned_by_name, cleaned_at, clean_date
                FROM tbl_clean_history 
                WHERE clean_date = CURRENT_DATE AND clean_type = %s
                ORDER BY cleaned_at DESC
            """, (clean_type,))
        else:
            result = db.execute_query("""
                SELECT id, room_id, room_number, floor, clean_type, clean_status, condition, notes, 
                       photo, video, cleaned_by, cleaned_by_name, cleaned_at, clean_date
                FROM tbl_clean_history 
                WHERE clean_date = CURRENT_DATE
                ORDER BY cleaned_at DESC
            """)
        
        if result:
            records = []
            for row in result:
                records.append({
                    'id': row[0],
                    'room_id': row[1],
                    'room_number': row[2],
                    'floor': row[3],
                    'clean_type': row[4],
                    'clean_status': row[5],
                    'condition': row[6],
                    'notes': row[7],
                    'photo': row[8],
                    'video': row[9],
                    'cleaned_by': row[10],
                    'cleaned_by_name': row[11],
                    'cleaned_at': row[12],
                    'clean_date': row[13]
                })
            return records
        return []
    except Exception as e:
        print(f"Error getting today's clean records: {e}")
        return []


def get_room_cleaned_today(db: DatabaseManager, room_id: int, clean_type: str) -> bool:
    """Check if a room has been cleaned today"""
    try:
        result = db.execute_query("""
            SELECT COUNT(*) FROM tbl_clean_history 
            WHERE room_id = %s AND clean_type = %s AND clean_date = CURRENT_DATE
        """, (room_id, clean_type))
        
        if result and len(result) > 0:
            return result[0][0] > 0
        return False
    except Exception as e:
        print(f"Error checking room cleaned today: {e}")
        return False


def get_daily_clean_stats(db: DatabaseManager, date: str = None) -> dict:
    """Get cleaning statistics for a specific date (default: today)"""
    try:
        date_filter = date if date else "CURRENT_DATE"
        
        result = db.execute_query(f"""
            SELECT clean_type, clean_status, COUNT(*) as cnt
            FROM tbl_clean_history 
            WHERE clean_date = {date_filter if date else "CURRENT_DATE"}
            GROUP BY clean_type, clean_status
        """) if not date else db.execute_query("""
            SELECT clean_type, clean_status, COUNT(*) as cnt
            FROM tbl_clean_history 
            WHERE clean_date = %s
            GROUP BY clean_type, clean_status
        """, (date,))
        
        stats = {
            'guest_room': {'Completed': 0, 'Partial': 0, 'Skipped': 0, 'Issue': 0, 'total': 0},
            'staff_room': {'Completed': 0, 'Partial': 0, 'Skipped': 0, 'Issue': 0, 'total': 0},
            'common_area': {'Completed': 0, 'Partial': 0, 'Skipped': 0, 'Issue': 0, 'total': 0}
        }
        
        if result:
            for row in result:
                clean_type, clean_status, cnt = row
                if clean_type in stats:
                    stats[clean_type][clean_status] = cnt
                    stats[clean_type]['total'] += cnt
        
        return stats
    except Exception as e:
        print(f"Error getting daily clean stats: {e}")
        return {}


def get_weekly_clean_stats(db: DatabaseManager) -> list:
    """Get cleaning statistics for the last 7 days"""
    try:
        result = db.execute_query("""
            SELECT clean_date, clean_type, clean_status, COUNT(*) as cnt
            FROM tbl_clean_history 
            WHERE clean_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY clean_date, clean_type, clean_status
            ORDER BY clean_date DESC
        """)
        
        if result:
            return [{'date': row[0], 'clean_type': row[1], 'clean_status': row[2], 'count': row[3]} for row in result]
        return []
    except Exception as e:
        print(f"Error getting weekly clean stats: {e}")
        return []


def get_monthly_clean_stats(db: DatabaseManager, year: int = None, month: int = None) -> list:
    """Get cleaning statistics for a specific month"""
    try:
        from datetime import datetime
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        result = db.execute_query("""
            SELECT clean_date, clean_type, clean_status, COUNT(*) as cnt
            FROM tbl_clean_history 
            WHERE clean_date >= %s AND clean_date < %s
            GROUP BY clean_date, clean_type, clean_status
            ORDER BY clean_date DESC
        """, (start_date, end_date))
        
        if result:
            return [{'date': row[0], 'clean_type': row[1], 'clean_status': row[2], 'count': row[3]} for row in result]
        return []
    except Exception as e:
        print(f"Error getting monthly clean stats: {e}")
        return []


def get_cleaner_stats(db: DatabaseManager, cleaned_by: int, days: int = 7) -> dict:
    """Get cleaning statistics for a specific cleaner"""
    try:
        result = db.execute_query("""
            SELECT clean_type, clean_status, COUNT(*) as cnt
            FROM tbl_clean_history 
            WHERE cleaned_by = %s AND clean_date >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY clean_type, clean_status
        """, (cleaned_by, days))
        
        stats = {
            'guest_room': {'Completed': 0, 'Partial': 0, 'Skipped': 0, 'Issue': 0, 'total': 0},
            'staff_room': {'Completed': 0, 'Partial': 0, 'Skipped': 0, 'Issue': 0, 'total': 0},
            'common_area': {'Completed': 0, 'Partial': 0, 'Skipped': 0, 'Issue': 0, 'total': 0},
            'total': 0
        }
        
        if result:
            for row in result:
                clean_type, clean_status, cnt = row
                if clean_type in stats:
                    stats[clean_type][clean_status] = cnt
                    stats[clean_type]['total'] += cnt
                    stats['total'] += cnt
        
        return stats
    except Exception as e:
        print(f"Error getting cleaner stats: {e}")
        return {}


def get_rooms_by_floor_and_type(db: DatabaseManager, floor: int, room_type: str = None) -> list:
    """Get rooms by floor from tbl_customer_rooms"""
    try:
        # Use tbl_customer_rooms table
        # floor is extracted from room number (e.g., 101 -> floor 1, 201 -> floor 2)
        floor_start = floor * 100
        floor_end = (floor + 1) * 100
        
        result = db.execute_query("""
            SELECT id, id_room, is_check, AC, TV, Toilet, Remote_Control, 
                   total_capacity, current_guests, is_active
            FROM tbl_customer_rooms 
            WHERE CAST(id_room AS INTEGER) >= %s AND CAST(id_room AS INTEGER) < %s AND is_active = 1
            ORDER BY CAST(id_room AS INTEGER)
        """, (floor_start, floor_end))
        
        if result:
            rooms = []
            for row in result:
                rooms.append({
                    'id': row[0],
                    'room_number': str(row[1]),
                    'floor': floor,
                    'room_type': 'Standard',
                    'is_check': row[2],
                    'AC': row[3],
                    'TV': row[4],
                    'Toilet': row[5],
                    'Remote_Control': row[6],
                    'total_capacity': row[7],
                    'current_guests': row[8],
                    'is_active': row[9]
                })
            return rooms
        return []
    except Exception as e:
        print(f"Error getting rooms by floor: {e}")
        return []


def get_customer_room_by_id(db: DatabaseManager, room_id: int) -> dict:
    """Get customer room by ID from tbl_customer_rooms"""
    try:
        result = db.execute_query("""
            SELECT id, id_room, is_check, AC, TV, Toilet, Remote_Control, 
                   total_capacity, current_guests, is_active
            FROM tbl_customer_rooms 
            WHERE id = %s
        """, (room_id,))
        
        if result and len(result) > 0:
            row = result[0]
            room_number = int(row[1])  # Convert to int
            floor = room_number // 100  # Extract floor from room number
            
            return {
                'id': row[0],
                'room_number': str(room_number),
                'floor': floor,
                'room_type': 'Standard',
                'is_check': row[2],
                'AC': row[3],
                'TV': row[4],
                'Toilet': row[5],
                'Remote_Control': row[6],
                'total_capacity': row[7],
                'current_guests': row[8],
                'is_active': row[9]
            }
        return None
    except Exception as e:
        print(f"Error getting customer room by ID: {e}")
        return None


def get_all_hotel_rooms(db: DatabaseManager) -> list:
    """Get all rooms from tbl_hotel_rooms (staff/office rooms)"""
    try:
        result = db.execute_query("""
            SELECT id, name, description, state, created_by, created_at
            FROM tbl_hotel_rooms 
            ORDER BY state DESC, name ASC
        """)
        
        if result:
            rooms = []
            for row in result:
                rooms.append({
                    'id': row[0],
                    'name': row[1],
                    'room_number': row[1],  # Use name as room_number
                    'description': row[2],
                    'state': row[3],
                    'created_by': row[4],
                    'created_at': row[5]
                })
            return rooms
        return []
    except Exception as e:
        print(f"Error getting all hotel rooms: {e}")
        return []


def get_hotel_room_by_id_for_clean(db: DatabaseManager, room_id: int) -> dict:
    """Get hotel room by ID from tbl_hotel_rooms for cleaning"""
    try:
        result = db.execute_query("""
            SELECT id, name, description, state
            FROM tbl_hotel_rooms 
            WHERE id = %s
        """, (room_id,))
        
        if result and len(result) > 0:
            row = result[0]
            return {
                'id': row[0],
                'name': row[1],
                'room_number': row[1],
                'description': row[2],
                'state': row[3],
                'floor': 0  # No floor info
            }
        return None
    except Exception as e:
        print(f"Error getting hotel room by ID: {e}")
        return None


def get_staff_rooms(db: DatabaseManager) -> list:
    """Get all staff rooms (rooms not for guests - employee rooms, storage, etc.)"""
    try:
        # Staff rooms are typically marked differently or have specific types
        result = db.execute_query("""
            SELECT id, room_number, floor, room_type, room_status, description
            FROM tbl_hotel_rooms 
            WHERE state = 1 AND (room_type LIKE '%staff%' OR room_type LIKE '%employee%' 
                   OR room_type LIKE '%storage%' OR room_type LIKE '%office%'
                   OR room_type = 'Radna' OR room_type = 'Magacin')
            ORDER BY floor, room_number
        """)
        
        if result:
            rooms = []
            for row in result:
                rooms.append({
                    'id': row[0],
                    'room_number': row[1],
                    'floor': row[2],
                    'room_type': row[3],
                    'room_status': row[4],
                    'description': row[5]
                })
            return rooms
        return []
    except Exception as e:
        print(f"Error getting staff rooms: {e}")
        return []


def get_guest_rooms(db: DatabaseManager) -> list:
    """Get all guest rooms"""
    try:
        result = db.execute_query("""
            SELECT id, room_number, floor, room_type, room_status, max_guests
            FROM tbl_hotel_rooms 
            WHERE state = 1 AND room_type NOT LIKE '%staff%' AND room_type NOT LIKE '%employee%' 
                   AND room_type NOT LIKE '%storage%' AND room_type NOT LIKE '%office%'
                   AND room_type != 'Radna' AND room_type != 'Magacin'
            ORDER BY floor, room_number
        """)
        
        if result:
            rooms = []
            for row in result:
                rooms.append({
                    'id': row[0],
                    'room_number': row[1],
                    'floor': row[2],
                    'room_type': row[3],
                    'room_status': row[4],
                    'max_guests': row[5]
                })
            return rooms
        return []
    except Exception as e:
        print(f"Error getting guest rooms: {e}")
        return []


def get_floors_for_cleaning(db: DatabaseManager, room_category: str = 'guest') -> list:
    """Get floors that have rooms for cleaning from tbl_customer_rooms
    
    Args:
        room_category: 'guest' or 'staff'
    """
    try:
        if room_category == 'guest':
            # Get distinct floors from tbl_customer_rooms
            result = db.execute_query("""
                SELECT DISTINCT floor 
                FROM tbl_customer_rooms 
                WHERE is_active = 1 AND floor IS NOT NULL
                ORDER BY floor
            """)
        else:
            # For staff rooms, use tbl_hotel_rooms
            result = db.execute_query("""
                SELECT DISTINCT floor FROM tbl_hotel_rooms 
                WHERE state = 1 AND (room_type LIKE '%staff%' OR room_type LIKE '%employee%' 
                       OR room_type LIKE '%storage%' OR room_type LIKE '%office%'
                       OR room_type = 'Radna' OR room_type = 'Magacin')
                ORDER BY floor
            """)
        
        if result:
            return [row[0] for row in result if row[0] is not None]
        return []
    except Exception as e:
        print(f"Error getting floors for cleaning: {e}")
        return []


# ========== Assignment Functions ==========

def create_assignments_table(db: DatabaseManager):
    """Create unified assignments table for all types of assignments (laundry, driver, kitchen, accounting, etc.)"""
    try:
        db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_assignments (
                id SERIAL PRIMARY KEY,
                assignment_type TEXT NOT NULL,
                assignee_id BIGINT NOT NULL,
                assignee_name TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT,
                due_time TEXT,
                attachment TEXT,
                attachment_type TEXT,
                status TEXT DEFAULT 'Pending',
                assigned_by BIGINT NOT NULL,
                assigned_by_name TEXT NOT NULL,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                accepted_at DATETIME,
                completed_at DATETIME,
                report_notes TEXT,
                report_attachment TEXT,
                report_attachment_type TEXT
            )
        """)
        db.connection.commit()
        print("✅ tbl_assignments table ready")
        return True
    except Exception as e:
        print(f"Error creating assignments table: {e}")
        return False


def create_assignment(db: DatabaseManager, assignment_type: str, assignee_id: int, assignee_name: str,
                     description: str, due_date: str, due_time: str, assigned_by: int, 
                     assigned_by_name: str, attachment: str = None, attachment_type: str = None) -> int:
    """Create a new assignment"""
    try:
        create_assignments_table(db)
        
        db.cursor.execute("""
            INSERT INTO tbl_assignments 
            (assignment_type, assignee_id, assignee_name, description, due_date, due_time, 
             attachment, attachment_type, assigned_by, assigned_by_name, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
            RETURNING id
        """, (assignment_type, assignee_id, assignee_name, description, due_date, due_time,
              attachment, attachment_type, assigned_by, assigned_by_name))
        
        assignment_id = db.cursor.fetchone()[0]
        db.connection.commit()
        print(f"✅ Assignment created: ID {assignment_id}, Type: {assignment_type}")
        return assignment_id
    except Exception as e:
        print(f"Error creating assignment: {e}")
        return None


def get_pending_assignments(db: DatabaseManager, assignee_id: int, assignment_type: str = None) -> list:
    """Get pending assignments for an employee"""
    try:
        create_assignments_table(db)
        
        if assignment_type:
            result = db.execute_query("""
                SELECT id, assignment_type, description, due_date, due_time, attachment, 
                       assigned_by_name, assigned_at, status
                FROM tbl_assignments 
                WHERE assignee_id = %s AND assignment_type = %s AND status IN ('Pending', 'Accepted')
                ORDER BY assigned_at DESC
            """, (assignee_id, assignment_type))
        else:
            result = db.execute_query("""
                SELECT id, assignment_type, description, due_date, due_time, attachment,
                       assigned_by_name, assigned_at, status
                FROM tbl_assignments 
                WHERE assignee_id = %s AND status IN ('Pending', 'Accepted')
                ORDER BY assigned_at DESC
            """, (assignee_id,))
        return result if result else []
    except Exception as e:
        print(f"Error getting pending assignments: {e}")
        return []


def get_assignment_by_id(db: DatabaseManager, assignment_id: int) -> dict:
    """Get assignment details by ID"""
    try:
        result = db.execute_query("""
            SELECT id, assignment_type, assignee_id, assignee_name, description, 
                   due_date, due_time, attachment, attachment_type, status,
                   assigned_by, assigned_by_name, assigned_at, accepted_at, completed_at,
                   report_notes, report_attachment, report_attachment_type
            FROM tbl_assignments WHERE id = %s
        """, (assignment_id,))
        
        if result and len(result) > 0:
            row = result[0]
            return {
                'id': row[0],
                'assignment_type': row[1],
                'assignee_id': row[2],
                'assignee_name': row[3],
                'description': row[4],
                'due_date': row[5],
                'due_time': row[6],
                'attachment': row[7],
                'attachment_type': row[8],
                'status': row[9],
                'assigned_by': row[10],
                'assigned_by_name': row[11],
                'assigned_at': row[12],
                'accepted_at': row[13],
                'completed_at': row[14],
                'report_notes': row[15],
                'report_attachment': row[16],
                'report_attachment_type': row[17]
            }
        return None
    except Exception as e:
        print(f"Error getting assignment: {e}")
        return None


def accept_assignment(db: DatabaseManager, assignment_id: int) -> bool:
    """Accept an assignment"""
    try:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        db.cursor.execute("""
            UPDATE tbl_assignments SET status = 'Accepted', accepted_at = %s WHERE id = %s
        """, (now, assignment_id))
        db.connection.commit()
        print(f"✅ Assignment accepted: ID {assignment_id}")
        return True
    except Exception as e:
        print(f"Error accepting assignment: {e}")
        return False


def complete_assignment(db: DatabaseManager, assignment_id: int, report_notes: str = None, 
                       report_attachment: str = None, report_attachment_type: str = None) -> bool:
    """Complete an assignment with optional report"""
    try:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        db.cursor.execute("""
            UPDATE tbl_assignments 
            SET status = 'Completed', completed_at = %s, report_notes = %s, 
                report_attachment = %s, report_attachment_type = %s
            WHERE id = %s
        """, (now, report_notes, report_attachment, report_attachment_type, assignment_id))
        db.connection.commit()
        print(f"✅ Assignment completed: ID {assignment_id}")
        return True
    except Exception as e:
        print(f"Error completing assignment: {e}")
        return False


def get_employees_by_department_name(db: DatabaseManager, department: str) -> list:
    """Get all employees in a specific department"""
    try:
        result = db.execute_query("""
            SELECT telegram_user_id, employee_id, name, work_role 
            FROM tbl_employeer 
            WHERE LOWER(department) = LOWER(%s)
            ORDER BY name
        """, (department,))
        return result if result else []
    except Exception as e:
        print(f"Error getting employees by department: {e}")
        return []


# ========== Legacy Laundry Functions ==========

def create_laundry_tasks_table(db: DatabaseManager):
    """Create laundry tasks table if not exists"""
    try:
        db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_laundry_tasks (
                id SERIAL PRIMARY KEY,
                room_id INTEGER,
                room_number TEXT,
                floor INTEGER,
                assignee_id BIGINT,
                assignee_name TEXT,
                description TEXT,
                due_date TEXT,
                due_time TEXT,
                proof_required INTEGER DEFAULT 0,
                proof_path TEXT,
                status TEXT DEFAULT 'pending',
                assigned_by BIGINT,
                assigned_by_name TEXT,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                accepted_at DATETIME,
                completed_at DATETIME,
                report_notes TEXT
            )
        """)
        
        # Add enhanced workflow columns to tbl_laundry_tasks
        db.cursor.execute("ALTER TABLE tbl_laundry_tasks ADD COLUMN IF NOT EXISTS started_at TIMESTAMP")
        db.cursor.execute("ALTER TABLE tbl_laundry_tasks ADD COLUMN IF NOT EXISTS proof_type TEXT")
        db.cursor.execute("ALTER TABLE tbl_laundry_tasks ADD COLUMN IF NOT EXISTS proof_submitted INTEGER DEFAULT 0")
        db.cursor.execute("ALTER TABLE tbl_laundry_tasks ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP")
        db.cursor.execute("ALTER TABLE tbl_laundry_tasks ADD COLUMN IF NOT EXISTS rejected_by BIGINT")
        db.cursor.execute("ALTER TABLE tbl_laundry_tasks ADD COLUMN IF NOT EXISTS rejection_reason TEXT")
        db.cursor.execute("ALTER TABLE tbl_laundry_tasks ADD COLUMN IF NOT EXISTS escalated INTEGER DEFAULT 0")
        db.cursor.execute("ALTER TABLE tbl_laundry_tasks ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMP")
        db.cursor.execute("ALTER TABLE tbl_laundry_tasks ADD COLUMN IF NOT EXISTS escalated_to BIGINT")
        
        db.connection.commit()
        print("✅ tbl_laundry_tasks table ready")
        return True
    except Exception as e:
        print(f"Error creating laundry tasks table: {e}")
        return False


def get_laundry_employees(db: DatabaseManager) -> list:
    """Get all employees in Waskamer (Laundry) department"""
    try:
        result = db.execute_query("""
            SELECT telegram_user_id, employee_id, name, work_role 
            FROM tbl_employeer 
            WHERE department = 'waskamer' OR department = 'Waskamer' OR department = 'Laundry'
            ORDER BY name
        """)
        return result if result else []
    except Exception as e:
        print(f"Error getting laundry employees: {e}")
        return []


def create_laundry_task(db: DatabaseManager, room_id: int, room_number: str, floor: int,
                        assignee_id: int, assignee_name: str, description: str,
                        due_date: str, due_time: str, proof_required: int,
                        assigned_by: int, assigned_by_name: str) -> int:
    """Create a new laundry task"""
    try:
        db.cursor.execute("""
            INSERT INTO tbl_laundry_tasks 
            (room_id, room_number, floor, assignee_id, assignee_name, description,
             due_date, due_time, proof_required, assigned_by, assigned_by_name, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
            RETURNING id
        """, (room_id, room_number, floor, assignee_id, assignee_name, description,
              due_date, due_time, proof_required, assigned_by, assigned_by_name))
        task_id = db.cursor.fetchone()[0]
        db.connection.commit()
        print(f"✅ Laundry task created: ID {task_id}, Room {room_number}")
        return task_id
    except Exception as e:
        print(f"Error creating laundry task: {e}")
        return None


def get_pending_laundry_tasks(db: DatabaseManager, assignee_id: int) -> list:
    """Get pending laundry tasks for an employee"""
    try:
        result = db.execute_query("""
            SELECT id, room_id, room_number, floor, description, due_date, due_time,
                   proof_required, assigned_by_name, assigned_at, status
            FROM tbl_laundry_tasks 
            WHERE assignee_id = %s AND status IN ('Pending', 'Accepted')
            ORDER BY due_date ASC, due_time ASC
        """, (assignee_id,))
        return result if result else []
    except Exception as e:
        print(f"Error getting pending laundry tasks: {e}")
        if db.connection:
            db.connection.rollback()
        return []


def accept_laundry_task(db: DatabaseManager, task_id: int) -> bool:
    """Accept a laundry task"""
    try:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.cursor.execute("""
            UPDATE tbl_laundry_tasks 
            SET status = 'Accepted', accepted_at = %s
            WHERE id = %s
        """, (now, task_id))
        db.connection.commit()
        print(f"✅ Laundry task {task_id} accepted")
        return True
    except Exception as e:
        print(f"Error accepting laundry task: {e}")
        return False


def complete_laundry_task(db: DatabaseManager, task_id: int, proof_path: str = None, report_notes: str = None) -> bool:
    """Complete a laundry task"""
    try:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.cursor.execute("""
            UPDATE tbl_laundry_tasks 
            SET status = 'Completed', completed_at = %s, proof_path = %s, report_notes = %s
            WHERE id = %s
        """, (now, proof_path, report_notes, task_id))
        db.connection.commit()
        print(f"✅ Laundry task {task_id} completed")
        return True
    except Exception as e:
        print(f"Error completing laundry task: {e}")
        return False


def get_laundry_task_by_id(db: DatabaseManager, task_id: int) -> dict:
    """Get laundry task details by ID"""
    try:
        result = db.execute_query("""
            SELECT id, room_id, room_number, floor, assignee_id, assignee_name,
                   description, due_date, due_time, proof_required, proof_path,
                   status, assigned_by, assigned_by_name, assigned_at,
                   accepted_at, completed_at, report_notes
            FROM tbl_laundry_tasks 
            WHERE id = %s
        """, (task_id,))
        if result:
            row = result[0]
            return {
                'id': row[0], 'room_id': row[1], 'room_number': row[2], 'floor': row[3],
                'assignee_id': row[4], 'assignee_name': row[5], 'description': row[6],
                'due_date': row[7], 'due_time': row[8], 'proof_required': row[9],
                'proof_path': row[10], 'status': row[11], 'assigned_by': row[12],
                'assigned_by_name': row[13], 'assigned_at': row[14], 'accepted_at': row[15],
                'completed_at': row[16], 'report_notes': row[17]
            }
        return None
    except Exception as e:
        print(f"Error getting laundry task: {e}")
        return None


def get_all_laundry_tasks(db: DatabaseManager, status: str = None, assigned_by: int = None) -> list:
    """Get all laundry tasks with optional filters - for managers and receptionists"""
    try:
        query = """
            SELECT id, room_number, floor, assignee_name, description, 
                   due_date, due_time, status, assigned_by_name, assigned_at,
                   accepted_at, completed_at, proof_path, report_notes
            FROM tbl_laundry_tasks 
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if assigned_by:
            query += " AND assigned_by = %s"
            params.append(assigned_by)
        
        query += " ORDER BY assigned_at DESC"
        
        result = db.execute_query(query, tuple(params))
        return result if result else []
    except Exception as e:
        print(f"Error getting all laundry tasks: {e}")
        return []


def get_laundry_stats(db: DatabaseManager) -> dict:
    """Get statistics for laundry tasks"""
    try:
        # Count by status
        result = db.execute_query("""
            SELECT status, COUNT(*) 
            FROM tbl_laundry_tasks 
            GROUP BY status
        """)
        
        stats = {'Pending': 0, 'Accepted': 0, 'Completed': 0, 'total': 0}
        if result:
            for row in result:
                stats[row[0]] = row[1]
                stats['total'] += row[1]
        
        return stats
    except Exception as e:
        print(f"Error getting laundry stats: {e}")
        if db.connection:
            db.connection.rollback()
        return {'Pending': 0, 'Accepted': 0, 'Completed': 0, 'total': 0}


def get_laundry_dashboard_view(db: DatabaseManager) -> str:
    """Get formatted dashboard view for laundry tasks - for receptionists and managers"""
    try:
        stats = get_laundry_stats(db)
        
        # Get pending tasks
        pending = db.execute_query("""
            SELECT id, room_number, assignee_name, description, due_date, due_time
            FROM tbl_laundry_tasks 
            WHERE status = 'Pending'
            ORDER BY due_date, due_time
            LIMIT 5
        """)
        
        # Get accepted tasks
        accepted = db.execute_query("""
            SELECT id, room_number, assignee_name, description, due_date, due_time
            FROM tbl_laundry_tasks 
            WHERE status = 'Accepted'
            ORDER BY accepted_at DESC
            LIMIT 5
        """)
        
        # Get completed tasks (today)
        completed = db.execute_query("""
            SELECT id, room_number, assignee_name, description, completed_at
            FROM tbl_laundry_tasks 
            WHERE status = 'Completed' AND date(completed_at) = CURRENT_DATE
            ORDER BY completed_at DESC
            LIMIT 5
        """)
        
        # Build dashboard text
        dashboard = f"""🧺 Laundry Dashboard

━━━━━━━━━━━━━━━━━━
📊 Statistics
━━━━━━━━━━━━━━━━━━
📋 Total: {stats['total']}
⏳ Pending: {stats['Pending']}
🔄 In Progress: {stats['Accepted']}
✅ Completed: {stats['Completed']}

"""
        
        if pending:
            dashboard += "━━━━━━━━━━━━━━━━━━\n⏳ Pending Tasks (Recent 5)\n━━━━━━━━━━━━━━━━━━\n"
            for task in pending:
                task_id, room, assignee, desc, due_date, due_time = task
                short_desc = desc[:20] + "..." if len(desc) > 20 else desc
                dashboard += f"#{task_id} 🚪{room} | {assignee}\n"
                dashboard += f"   📝 {short_desc}\n"
                dashboard += f"   ⏰ {due_date} {due_time}\n\n"
        
        if accepted:
            dashboard += "━━━━━━━━━━━━━━━━━━\n🔄 In Progress (Recent 5)\n━━━━━━━━━━━━━━━━━━\n"
            for task in accepted:
                task_id, room, assignee, desc, due_date, due_time = task
                short_desc = desc[:20] + "..." if len(desc) > 20 else desc
                dashboard += f"#{task_id} 🚪{room} | {assignee}\n"
                dashboard += f"   📝 {short_desc}\n"
                dashboard += f"   ⏰ {due_date} {due_time}\n\n"
        
        if completed:
            dashboard += "━━━━━━━━━━━━━━━━━━\n✅ Completed Today\n━━━━━━━━━━━━━━━━━━\n"
            for task in completed:
                task_id, room, assignee, desc, completed_at = task
                short_desc = desc[:20] + "..." if len(desc) > 20 else desc
                time_only = completed_at.split()[1] if ' ' in completed_at else completed_at
                dashboard += f"#{task_id} 🚪{room} | {assignee}\n"
                dashboard += f"   📝 {short_desc}\n"
                dashboard += f"   ✅ {time_only}\n\n"
        
        return dashboard
    except Exception as e:
        print(f"Error getting laundry dashboard: {e}")
        return "❌ Unable to load dashboard."


# ==================== Restaurant Task Management ====================

def create_restaurant_tasks_table(db: DatabaseManager):
    """Create restaurant tasks table if not exists"""
    try:
        # Drop existing table to ensure clean structure
        db.cursor.execute("DROP TABLE IF EXISTS tbl_restaurant_tasks")
        
        # Create new table with simplified structure
        db.cursor.execute("""
            CREATE TABLE tbl_restaurant_tasks (
                id SERIAL PRIMARY KEY,
                assignee_id BIGINT NOT NULL,
                assignee_name TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT NOT NULL,
                due_time TEXT NOT NULL,
                attachment_file_id TEXT,
                attachment_type TEXT,
                status TEXT DEFAULT 'Pending',
                assigned_by BIGINT NOT NULL,
                assigned_by_name TEXT NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMP,
                completed_at TIMESTAMP,
                report_notes TEXT,
                report_media_file_id TEXT,
                report_media_type TEXT
            )
        """)
        db.connection.commit()
        print("✅ tbl_restaurant_tasks table ready")
        return True
    except Exception as e:
        print(f"Error creating restaurant tasks table: {e}")
        return False


def get_restaurant_employees(db: DatabaseManager) -> list:
    """Get all employees in Restaurant department"""
    try:
        result = db.execute_query("""
            SELECT telegram_user_id, employee_id, name, work_role 
            FROM tbl_employeer 
            WHERE LOWER(department) = 'restaurant'
            ORDER BY name
        """)
        return result if result else []
    except Exception as e:
        print(f"Error getting restaurant employees: {e}")
        return []


def create_restaurant_task(db: DatabaseManager, assignee_id: int, assignee_name: str, 
                          description: str, due_date: str, due_time: str,
                          assigned_by: int, assigned_by_name: str,
                          attachment_file_id: str = None, attachment_type: str = None) -> int:
    """Create a new restaurant task"""
    try:
        db.cursor.execute("""
            INSERT INTO tbl_restaurant_tasks 
            (assignee_id, assignee_name, description, due_date, due_time, 
             attachment_file_id, attachment_type, assigned_by, assigned_by_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (assignee_id, assignee_name, description, due_date, due_time,
              attachment_file_id, attachment_type, assigned_by, assigned_by_name))
        task_id = db.cursor.fetchone()[0]
        db.connection.commit()
        print(f"✅ Restaurant task created: ID {task_id}")
        return task_id
    except Exception as e:
        print(f"Error creating restaurant task: {e}")
        return 0


def get_restaurant_tasks_by_assignee(db: DatabaseManager, telegram_user_id: int) -> list:
    """Get restaurant tasks assigned to a specific employee"""
    try:
        result = db.execute_query("""
            SELECT id, description, due_date, due_time, status, assigned_at, 
                   accepted_at, completed_at, assigned_by_name
            FROM tbl_restaurant_tasks
            WHERE assignee_id = %s AND status != 'Completed'
            ORDER BY due_date, due_time
        """, (telegram_user_id,))
        return result if result else []
    except Exception as e:
        print(f"Error getting restaurant tasks: {e}")
        return []


def get_restaurant_task_by_id(db: DatabaseManager, task_id: int) -> dict:
    """Get a specific restaurant task by ID"""
    try:
        result = db.execute_query("""
            SELECT id, assignee_id, assignee_name, description, due_date, due_time,
                   attachment_file_id, attachment_type, status, assigned_by, 
                   assigned_by_name, assigned_at, accepted_at, completed_at, 
                   report_notes, report_media_file_id, report_media_type
            FROM tbl_restaurant_tasks
            WHERE id = %s
        """, (task_id,))
        
        if result and len(result) > 0:
            row = result[0]
            return {
                'id': row[0],
                'assignee_id': row[1],
                'assignee_name': row[2],
                'description': row[3],
                'due_date': row[4],
                'due_time': row[5],
                'attachment_file_id': row[6],
                'attachment_type': row[7],
                'status': row[8],
                'assigned_by': row[9],
                'assigned_by_name': row[10],
                'assigned_at': row[11],
                'accepted_at': row[12],
                'completed_at': row[13],
                'report_notes': row[14],
                'report_media_file_id': row[15],
                'report_media_type': row[16]
            }
        return None
    except Exception as e:
        print(f"Error getting restaurant task: {e}")
        return None


def accept_restaurant_task(db: DatabaseManager, task_id: int) -> bool:
    """Accept a restaurant task"""
    try:
        # Check if task is already accepted or completed
        db.cursor.execute("""
            SELECT status FROM tbl_restaurant_tasks WHERE id = %s
        """, (task_id,))
        result = db.cursor.fetchone()
        
        if not result:
            print(f"❌ Restaurant task {task_id} not found")
            return False
            
        current_status = result[0]
        if current_status != 'Pending':
            print(f"⚠️ Restaurant task {task_id} already {current_status}")
            return False
        
        db.cursor.execute("""
            UPDATE tbl_restaurant_tasks 
            SET status = 'Accepted', accepted_at = CURRENT_TIMESTAMP
            WHERE id = %s AND status = 'Pending'
        """, (task_id,))
        db.connection.commit()
        
        if db.cursor.rowcount > 0:
            print(f"✅ Restaurant task {task_id} accepted")
            return True
        else:
            print(f"⚠️ Restaurant task {task_id} was not updated (already processed)")
            return False
    except Exception as e:
        print(f"Error accepting restaurant task: {e}")
        return False


def complete_restaurant_task(db: DatabaseManager, task_id: int, report_notes: str = '', 
                            report_media_file_id: str = None, report_media_type: str = None) -> bool:
    """Complete a restaurant task"""
    try:
        db.cursor.execute("""
            UPDATE tbl_restaurant_tasks 
            SET status = 'Completed', 
                completed_at = CURRENT_TIMESTAMP,
                report_notes = %s,
                report_media_file_id = %s,
                report_media_type = %s
            WHERE id = %s
        """, (report_notes, report_media_file_id, report_media_type, task_id))
        db.connection.commit()
        print(f"✅ Restaurant task {task_id} completed")
        return True
    except Exception as e:
        print(f"Error completing restaurant task: {e}")
        return False


def get_restaurant_stats(db: DatabaseManager) -> dict:
    """Get restaurant tasks statistics"""
    try:
        pending = db.execute_query("""
            SELECT COUNT(*) FROM tbl_restaurant_tasks WHERE status = 'Pending'
        """)[0][0]
        
        accepted = db.execute_query("""
            SELECT COUNT(*) FROM tbl_restaurant_tasks WHERE status = 'Accepted'
        """)[0][0]
        
        completed = db.execute_query("""
            SELECT COUNT(*) FROM tbl_restaurant_tasks WHERE status = 'Completed'
        """)[0][0]
        
        return {
            'pending': pending,
            'accepted': accepted,
            'completed': completed,
            'total': pending + accepted + completed
        }
    except Exception as e:
        print(f"Error getting restaurant stats: {e}")
        return {'pending': 0, 'accepted': 0, 'completed': 0, 'total': 0}


def get_restaurant_dashboard_view(db: DatabaseManager) -> str:
    """Get formatted restaurant dashboard view"""
    try:
        stats = get_restaurant_stats(db)
        
        dashboard = "🍽️ Restaurant Dashboard\n\n"
        dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        dashboard += f"📊 Statistics\n"
        dashboard += f"   ⏳ Pending: {stats['pending']}\n"
        dashboard += f"   🔄 In Progress: {stats['accepted']}\n"
        dashboard += f"   ✅ Completed: {stats['completed']}\n"
        dashboard += f"   📈 Total: {stats['total']}\n\n"
        
        # Pending tasks
        pending = db.execute_query("""
            SELECT id, task_type, assignee_name, description, due_date, due_time
            FROM tbl_restaurant_tasks
            WHERE status = 'Pending'
            ORDER BY due_date, due_time
            LIMIT 5
        """)
        
        if pending:
            dashboard += "⏳ Pending Tasks:\n"
            dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for task in pending:
                task_id, task_type, assignee, desc, due_date, due_time = task
                short_desc = desc[:20] + "..." if len(desc) > 20 else desc
                type_icon = "🎉" if task_type == "Event" else "🍱" if task_type == "Catering" else "👨‍🍳"
                dashboard += f"#{task_id} {type_icon} {task_type} | {assignee}\n"
                dashboard += f"   📝 {short_desc}\n"
                dashboard += f"   📅 {due_date} {due_time}\n\n"
        
        # Accepted tasks
        accepted = db.execute_query("""
            SELECT id, task_type, assignee_name, description, accepted_at
            FROM tbl_restaurant_tasks
            WHERE status = 'Accepted'
            ORDER BY accepted_at DESC
            LIMIT 5
        """)
        
        if accepted:
            dashboard += "🔄 In Progress:\n"
            dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for task in accepted:
                task_id, task_type, assignee, desc, accepted_at = task
                short_desc = desc[:20] + "..." if len(desc) > 20 else desc
                time_only = accepted_at.split()[1] if ' ' in accepted_at else accepted_at
                type_icon = "🎉" if task_type == "Event" else "🍱" if task_type == "Catering" else "👨‍🍳"
                dashboard += f"#{task_id} {type_icon} {task_type} | {assignee}\n"
                dashboard += f"   📝 {short_desc}\n"
                dashboard += f"   🔄 {time_only}\n\n"
        
        # Recently completed
        completed = db.execute_query("""
            SELECT id, task_type, assignee_name, description, completed_at
            FROM tbl_restaurant_tasks
            WHERE status = 'Completed'
            ORDER BY completed_at DESC
            LIMIT 5
        """)
        
        if completed:
            dashboard += "✅ Recently Completed:\n"
            dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for task in completed:
                task_id, task_type, assignee, desc, completed_at = task
                short_desc = desc[:20] + "..." if len(desc) > 20 else desc
                time_only = completed_at.split()[1] if ' ' in completed_at else completed_at
                type_icon = "🎉" if task_type == "Event" else "🍱" if task_type == "Catering" else "👨‍🍳"
                dashboard += f"#{task_id} {type_icon} {task_type} | {assignee}\n"
                dashboard += f"   📝 {short_desc}\n"
                dashboard += f"   ✅ {time_only}\n\n"
        
        return dashboard
    except Exception as e:
        print(f"Error getting restaurant dashboard: {e}")
        return "❌ Unable to load dashboard."


# ============================================================
# DELIVERY TASKS (Driver Assignment System)
# ============================================================

def create_delivery_tasks_table(db: DatabaseManager):
    """Create the delivery tasks table for driver assignments"""
    try:
        db.cursor.execute("DROP TABLE IF EXISTS tbl_delivery_tasks")
        db.cursor.execute("""
            CREATE TABLE tbl_delivery_tasks (
                id SERIAL PRIMARY KEY,
                assignee_id TEXT NOT NULL,
                assignee_name TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT,
                due_time TEXT,
                attachment_file_id TEXT,
                attachment_type TEXT,
                status TEXT DEFAULT 'Pending',
                assigned_by TEXT NOT NULL,
                assigned_by_name TEXT NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMP,
                completed_at TIMESTAMP,
                report_notes TEXT,
                report_media_file_id TEXT,
                report_media_type TEXT
            )
        """)
        db.connection.commit()
        print("✅ tbl_delivery_tasks table ready")
        return True
    except Exception as e:
        print(f"Error creating delivery tasks table: {e}")
        return False


def get_drivers(db: DatabaseManager) -> list:
    """Get all employees in Transportation department with Driver role"""
    try:
        results = db.execute_query("""
            SELECT employee_id, name, department, work_role
            FROM tbl_employeer
            WHERE LOWER(department) = 'transportation'
        """)
        print(f"✅ Drivers retrieved: {len(results) if results else 0}")
        return results if results else []
    except Exception as e:
        print(f"Error getting drivers: {e}")
        return []


def create_delivery_task(db: DatabaseManager, assignee_id: str, assignee_name: str, 
                        description: str, due_date: str = None, due_time: str = None,
                        assigned_by: str = None, assigned_by_name: str = None,
                        attachment_file_id: str = None, attachment_type: str = None) -> int:
    """Create a new delivery task"""
    try:
        db.cursor.execute("""
            INSERT INTO tbl_delivery_tasks 
            (assignee_id, assignee_name, description, due_date, due_time, 
             assigned_by, assigned_by_name, attachment_file_id, attachment_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (assignee_id, assignee_name, description, due_date, due_time,
              assigned_by, assigned_by_name, attachment_file_id, attachment_type))
        task_id = db.cursor.fetchone()[0]
        db.connection.commit()
        print(f"✅ Delivery task created: ID {task_id}")
        return task_id
    except Exception as e:
        print(f"Error creating delivery task: {e}")
        return None


def get_delivery_tasks_by_assignee(db: DatabaseManager, assignee_id: str) -> list:
    """Get all pending/accepted delivery tasks for a specific driver"""
    try:
        results = db.execute_query("""
            SELECT id, description, due_date, due_time, status, assigned_at, 
                   accepted_at, completed_at, assigned_by_name
            FROM tbl_delivery_tasks
            WHERE assignee_id = %s AND status IN ('Pending', 'Accepted')
            ORDER BY 
                CASE WHEN status = 'Pending' THEN 0 ELSE 1 END,
                assigned_at DESC
        """, (assignee_id,))
        print(f"✅ Driver tasks retrieved: {len(results) if results else 0}")
        return results if results else []
    except Exception as e:
        print(f"Error getting delivery tasks by assignee: {e}")
        return []


def get_delivery_task_by_id(db: DatabaseManager, task_id: int) -> dict:
    """Get a specific delivery task by ID"""
    try:
        result = db.execute_query("""
            SELECT id, assignee_id, assignee_name, description, due_date, due_time,
                   attachment_file_id, attachment_type, status, assigned_by, 
                   assigned_by_name, assigned_at, accepted_at, completed_at,
                   report_notes, report_media_file_id, report_media_type
            FROM tbl_delivery_tasks
            WHERE id = %s
        """, (task_id,))
        
        if result:
            row = result[0]
            return {
                'id': row[0], 'assignee_id': row[1], 'assignee_name': row[2],
                'description': row[3], 'due_date': row[4], 'due_time': row[5],
                'attachment_file_id': row[6], 'attachment_type': row[7],
                'status': row[8], 'assigned_by': row[9], 'assigned_by_name': row[10],
                'assigned_at': row[11], 'accepted_at': row[12], 'completed_at': row[13],
                'report_notes': row[14], 'report_media_file_id': row[15], 
                'report_media_type': row[16]
            }
        return None
    except Exception as e:
        print(f"Error getting delivery task by ID: {e}")
        return None


def accept_delivery_task(db: DatabaseManager, task_id: int) -> bool:
    """Accept a delivery task"""
    try:
        # Check if task is already accepted or completed
        db.cursor.execute("""
            SELECT status FROM tbl_delivery_tasks WHERE id = %s
        """, (task_id,))
        result = db.cursor.fetchone()
        
        if not result:
            print(f"❌ Delivery task {task_id} not found")
            return False
            
        current_status = result[0]
        if current_status != 'Pending':
            print(f"⚠️ Delivery task {task_id} already {current_status}")
            return False
        
        db.cursor.execute("""
            UPDATE tbl_delivery_tasks 
            SET status = 'Accepted', accepted_at = CURRENT_TIMESTAMP
            WHERE id = %s AND status = 'Pending'
        """, (task_id,))
        db.connection.commit()
        
        if db.cursor.rowcount > 0:
            print(f"✅ Delivery task {task_id} accepted")
            return True
        else:
            print(f"⚠️ Delivery task {task_id} was not updated")
            return False
    except Exception as e:
        print(f"Error accepting delivery task: {e}")
        return False


def complete_delivery_task(db: DatabaseManager, task_id: int, report_notes: str = '', 
                          report_media_file_id: str = None, report_media_type: str = None) -> bool:
    """Complete a delivery task with optional report"""
    try:
        db.cursor.execute("""
            UPDATE tbl_delivery_tasks 
            SET status = 'Completed', completed_at = CURRENT_TIMESTAMP,
                report_notes = %s, report_media_file_id = %s, report_media_type = %s
            WHERE id = %s
        """, (report_notes, report_media_file_id, report_media_type, task_id))
        db.connection.commit()
        print(f"✅ Delivery task {task_id} completed")
        return True
    except Exception as e:
        print(f"Error completing delivery task: {e}")
        return False


# ============================================================
# HOTEL FINANCE MANAGEMENT (tbl_hotel_accounts + tbl_financial_transactions)
# ============================================================

def upgrade_hotel_accounts_table(db: DatabaseManager):
    """Upgrade tbl_hotel_accounts with new columns for comprehensive finance tracking"""
    try:
        # Add new columns if they don't exist
        new_cols = {
            'cash_balance': "DECIMAL(15,2) DEFAULT 0",
            'bank_balance': "DECIMAL(15,2) DEFAULT 0",
            'total_revenue': "DECIMAL(15,2) DEFAULT 0",
            'total_expenses': "DECIMAL(15,2) DEFAULT 0",
            'net_profit': "DECIMAL(15,2) DEFAULT 0",
            'notes': "TEXT",
            'closed_by': "BIGINT",
            'closed_by_name': "TEXT",
            'is_closed': "BOOLEAN DEFAULT FALSE",
        }
        for col_name, col_def in new_cols.items():
            try:
                db.cursor.execute(
                    f"ALTER TABLE tbl_hotel_accounts ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                )
                db.connection.commit()
            except Exception:
                db.connection.rollback()
        print("tbl_hotel_accounts upgraded")
        return True
    except Exception as e:
        print(f"Error upgrading hotel accounts: {e}")
        return False


def create_financial_transactions_table(db: DatabaseManager):
    """Create financial transactions table for detailed tracking"""
    try:
        db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_financial_transactions (
                id SERIAL PRIMARY KEY,
                transaction_date DATE DEFAULT CURRENT_DATE,
                transaction_type TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                reference_number TEXT,
                vendor_client TEXT,
                recorded_by BIGINT NOT NULL,
                recorded_by_name TEXT NOT NULL,
                approved_by BIGINT,
                approved_by_name TEXT,
                attachment_file_id TEXT,
                attachment_type TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.connection.commit()
        print("tbl_financial_transactions table ready")
        return True
    except Exception as e:
        print(f"Error creating financial transactions table: {e}")
        return False


def get_hotel_finance_summary(db: DatabaseManager):
    """Get current hotel financial summary from latest accounts + transactions"""
    try:
        # Get today's transaction totals
        db.cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END), 0) as today_income,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END), 0) as today_expense,
                COUNT(*) as today_count
            FROM tbl_financial_transactions
            WHERE transaction_date = CURRENT_DATE
        """)
        today = db.cursor.fetchone()
        
        # Get this month totals
        db.cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END), 0) as month_income,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END), 0) as month_expense,
                COUNT(*) as month_count
            FROM tbl_financial_transactions
            WHERE DATE_TRUNC('month', transaction_date) = DATE_TRUNC('month', CURRENT_DATE)
        """)
        month = db.cursor.fetchone()
        
        # Get category breakdown for today
        db.cursor.execute("""
            SELECT category, transaction_type,
                   COUNT(*) as cnt, SUM(amount) as total
            FROM tbl_financial_transactions
            WHERE transaction_date = CURRENT_DATE
            GROUP BY category, transaction_type
            ORDER BY total DESC
        """)
        today_categories = db.cursor.fetchall()
        
        # Get latest hotel_accounts record for balances
        db.cursor.execute("""
            SELECT cash_balance, bank_balance, total_revenue, total_expenses, net_profit
            FROM tbl_hotel_accounts
            ORDER BY date DESC LIMIT 1
        """)
        balances = db.cursor.fetchone()
        
        return {
            'today_income': float(today[0]) if today else 0,
            'today_expense': float(today[1]) if today else 0,
            'today_count': today[2] if today else 0,
            'month_income': float(month[0]) if month else 0,
            'month_expense': float(month[1]) if month else 0,
            'month_count': month[2] if month else 0,
            'today_categories': today_categories or [],
            'cash_balance': float(balances[0]) if balances and balances[0] else 0,
            'bank_balance': float(balances[1]) if balances and balances[1] else 0,
            'total_revenue': float(balances[2]) if balances and balances[2] else 0,
            'total_expenses': float(balances[3]) if balances and balances[3] else 0,
            'net_profit': float(balances[4]) if balances and balances[4] else 0,
        }
    except Exception as e:
        print(f"Error getting finance summary: {e}")
        return None


def record_financial_transaction(db: DatabaseManager, data: dict):
    """Record a new financial transaction and update hotel accounts"""
    try:
        db.cursor.execute("""
            INSERT INTO tbl_financial_transactions 
            (transaction_date, transaction_type, category, description, amount,
             payment_method, reference_number, vendor_client,
             recorded_by, recorded_by_name, attachment_file_id, attachment_type, notes)
            VALUES (CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['transaction_type'],
            data['category'],
            data['description'],
            data['amount'],
            data.get('payment_method', 'cash'),
            data.get('reference_number'),
            data.get('vendor_client'),
            data['recorded_by'],
            data['recorded_by_name'],
            data.get('attachment_file_id'),
            data.get('attachment_type'),
            data.get('notes')
        ))
        tx_id = db.cursor.fetchone()[0]
        
        # Update hotel_accounts balance
        amount = float(data['amount'])
        pay_method = data.get('payment_method', 'cash')
        tx_type = data['transaction_type']
        
        # Check if today's account record exists
        db.cursor.execute("SELECT id FROM tbl_hotel_accounts WHERE date = CURRENT_DATE")
        account = db.cursor.fetchone()
        
        if not account:
            # Create today's record by copying yesterday's balances
            db.cursor.execute("""
                INSERT INTO tbl_hotel_accounts (date, Room_Revenue, Food_Beverage_Revenue, 
                    Purchasing_Product_Revenue, Utilities_Expenses, Total_amount,
                    cash_balance, bank_balance, total_revenue, total_expenses, net_profit, created_at)
                SELECT CURRENT_DATE, 0, 0, 0, 0, 0,
                    COALESCE(cash_balance, 0), COALESCE(bank_balance, 0),
                    0, 0, 0, CURRENT_DATE
                FROM tbl_hotel_accounts ORDER BY date DESC LIMIT 1
            """)
            # If no previous record exists at all
            db.cursor.execute("SELECT id FROM tbl_hotel_accounts WHERE date = CURRENT_DATE")
            account = db.cursor.fetchone()
            if not account:
                db.cursor.execute("""
                    INSERT INTO tbl_hotel_accounts (date, Room_Revenue, Food_Beverage_Revenue,
                        Purchasing_Product_Revenue, Utilities_Expenses, Total_amount,
                        cash_balance, bank_balance, total_revenue, total_expenses, net_profit, created_at)
                    VALUES (CURRENT_DATE, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, CURRENT_DATE)
                """)
        
        # Update balances
        if tx_type == 'income':
            if pay_method in ('cash', 'mixed'):
                db.cursor.execute("""
                    UPDATE tbl_hotel_accounts 
                    SET cash_balance = COALESCE(cash_balance, 0) + %s,
                        total_revenue = COALESCE(total_revenue, 0) + %s,
                        net_profit = COALESCE(net_profit, 0) + %s,
                        Total_amount = COALESCE(Total_amount, 0) + %s
                    WHERE date = CURRENT_DATE
                """, (amount, amount, amount, amount))
            else:
                db.cursor.execute("""
                    UPDATE tbl_hotel_accounts 
                    SET bank_balance = COALESCE(bank_balance, 0) + %s,
                        total_revenue = COALESCE(total_revenue, 0) + %s,
                        net_profit = COALESCE(net_profit, 0) + %s,
                        Total_amount = COALESCE(Total_amount, 0) + %s
                    WHERE date = CURRENT_DATE
                """, (amount, amount, amount, amount))
            
            # Update category-specific columns
            cat = data['category']
            if cat == 'room_revenue':
                db.cursor.execute("UPDATE tbl_hotel_accounts SET Room_Revenue = COALESCE(Room_Revenue,0) + %s WHERE date = CURRENT_DATE", (int(amount),))
            elif cat == 'food_beverage':
                db.cursor.execute("UPDATE tbl_hotel_accounts SET Food_Beverage_Revenue = COALESCE(Food_Beverage_Revenue,0) + %s WHERE date = CURRENT_DATE", (int(amount),))
        
        elif tx_type == 'expense':
            if pay_method in ('cash', 'mixed'):
                db.cursor.execute("""
                    UPDATE tbl_hotel_accounts 
                    SET cash_balance = COALESCE(cash_balance, 0) - %s,
                        total_expenses = COALESCE(total_expenses, 0) + %s,
                        net_profit = COALESCE(net_profit, 0) - %s
                    WHERE date = CURRENT_DATE
                """, (amount, amount, amount))
            else:
                db.cursor.execute("""
                    UPDATE tbl_hotel_accounts 
                    SET bank_balance = COALESCE(bank_balance, 0) - %s,
                        total_expenses = COALESCE(total_expenses, 0) + %s,
                        net_profit = COALESCE(net_profit, 0) - %s
                    WHERE date = CURRENT_DATE
                """, (amount, amount, amount))
            
            cat = data['category']
            if cat == 'purchase':
                db.cursor.execute("UPDATE tbl_hotel_accounts SET Purchasing_Product_Revenue = COALESCE(Purchasing_Product_Revenue,0) + %s WHERE date = CURRENT_DATE", (int(amount),))
            elif cat == 'utilities':
                db.cursor.execute("UPDATE tbl_hotel_accounts SET Utilities_Expenses = COALESCE(Utilities_Expenses,0) + %s WHERE date = CURRENT_DATE", (int(amount),))
        
        db.connection.commit()
        print(f"✅ Financial transaction recorded: #{tx_id} ({tx_type}: {amount})")
        return tx_id
    except Exception as e:
        db.connection.rollback()
        print(f"Error recording financial transaction: {e}")
        return None


def get_financial_transactions(db: DatabaseManager, period='today', category=None, limit=20):
    """Get financial transactions filtered by period and category"""
    try:
        where = []
        params = []
        
        if period == 'today':
            where.append("transaction_date = CURRENT_DATE")
        elif period == 'week':
            where.append("transaction_date >= CURRENT_DATE - INTERVAL '7 days'")
        elif period == 'month':
            where.append("transaction_date >= CURRENT_DATE - INTERVAL '30 days'")
        
        if category:
            where.append("category = %s")
            params.append(category)
        
        where_clause = "WHERE " + " AND ".join(where) if where else ""
        params.append(limit)
        
        db.cursor.execute(f"""
            SELECT id, transaction_date, transaction_type, category, description,
                   amount, payment_method, vendor_client, recorded_by_name, created_at
            FROM tbl_financial_transactions
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """, tuple(params))
        
        rows = db.cursor.fetchall()
        return [{
            'id': r[0], 'date': r[1], 'type': r[2], 'category': r[3],
            'description': r[4], 'amount': float(r[5]), 'payment_method': r[6],
            'vendor_client': r[7], 'recorded_by': r[8], 'created_at': r[9]
        } for r in rows]
    except Exception as e:
        print(f"Error getting transactions: {e}")
        return []


def get_admin_finance_dashboard(db: DatabaseManager):
    """Get comprehensive finance dashboard for admin - includes balances, recent transactions, and pending proofs"""
    try:
        # Get current balances from latest account record
        db.cursor.execute("""
            SELECT cash_balance, bank_balance, total_revenue, total_expenses, net_profit, date
            FROM tbl_hotel_accounts 
            ORDER BY date DESC LIMIT 1
        """)
        balance_row = db.cursor.fetchone()
        
        balances = {
            'cash_balance': float(balance_row[0]) if balance_row and balance_row[0] else 0,
            'bank_balance': float(balance_row[1]) if balance_row and balance_row[1] else 0,
            'total_balance': float(balance_row[0] or 0) + float(balance_row[1] or 0) if balance_row else 0,
            'total_revenue': float(balance_row[2]) if balance_row and balance_row[2] else 0,
            'total_expenses': float(balance_row[3]) if balance_row and balance_row[3] else 0,
            'net_profit': float(balance_row[4]) if balance_row and balance_row[4] else 0,
            'last_update': balance_row[5] if balance_row else None
        }
        
        # Get today's summary
        db.cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount END), 0) as today_income,
                COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount END), 0) as today_expense,
                COUNT(*) as today_count
            FROM tbl_financial_transactions
            WHERE transaction_date = CURRENT_DATE
        """)
        today = db.cursor.fetchone()
        today_summary = {
            'income': float(today[0]) if today else 0,
            'expense': float(today[1]) if today else 0,
            'count': today[2] if today else 0
        }
        
        # Get this week's summary
        db.cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount END), 0) as week_income,
                COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount END), 0) as week_expense,
                COUNT(*) as week_count
            FROM tbl_financial_transactions
            WHERE transaction_date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        week = db.cursor.fetchone()
        week_summary = {
            'income': float(week[0]) if week else 0,
            'expense': float(week[1]) if week else 0,
            'count': week[2] if week else 0
        }
        
        # Get this month's summary
        db.cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount END), 0) as month_income,
                COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount END), 0) as month_expense,
                COUNT(*) as month_count
            FROM tbl_financial_transactions
            WHERE transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
        """)
        month = db.cursor.fetchone()
        month_summary = {
            'income': float(month[0]) if month else 0,
            'expense': float(month[1]) if month else 0,
            'count': month[2] if month else 0
        }
        
        # Get transactions without proof (attachment)
        db.cursor.execute("""
            SELECT COUNT(*) FROM tbl_financial_transactions 
            WHERE attachment_file_id IS NULL
        """)
        no_proof_count = db.cursor.fetchone()[0]
        
        # Get recent transactions (last 10)
        db.cursor.execute("""
            SELECT id, transaction_date, transaction_type, category, description,
                   amount, payment_method, recorded_by_name, attachment_file_id, created_at
            FROM tbl_financial_transactions
            ORDER BY created_at DESC
            LIMIT 10
        """)
        recent_rows = db.cursor.fetchall()
        recent_transactions = [{
            'id': r[0], 'date': r[1], 'type': r[2], 'category': r[3],
            'description': r[4], 'amount': float(r[5]), 'payment_method': r[6],
            'recorded_by': r[7], 'has_proof': r[8] is not None, 'created_at': r[9]
        } for r in recent_rows]
        
        return {
            'balances': balances,
            'today': today_summary,
            'week': week_summary,
            'month': month_summary,
            'no_proof_count': no_proof_count,
            'recent_transactions': recent_transactions
        }
    except Exception as e:
        print(f"Error getting admin finance dashboard: {e}")
        return None


def get_transaction_detail(db: DatabaseManager, tx_id: int):
    """Get detailed transaction info including attachment"""
    try:
        db.cursor.execute("""
            SELECT id, transaction_date, transaction_type, category, description,
                   amount, payment_method, reference_number, vendor_client,
                   recorded_by, recorded_by_name, attachment_file_id, attachment_type, 
                   notes, created_at
            FROM tbl_financial_transactions
            WHERE id = %s
        """, (tx_id,))
        row = db.cursor.fetchone()
        
        if row:
            return {
                'id': row[0], 'date': row[1], 'type': row[2], 'category': row[3],
                'description': row[4], 'amount': float(row[5]), 'payment_method': row[6],
                'reference_number': row[7], 'vendor_client': row[8],
                'recorded_by': row[9], 'recorded_by_name': row[10],
                'attachment_file_id': row[11], 'attachment_type': row[12],
                'notes': row[13], 'created_at': row[14]
            }
        return None
    except Exception as e:
        print(f"Error getting transaction detail: {e}")
        return None


def get_finance_daily_report(db: DatabaseManager, date=None):
    """Get daily financial report for a specific date"""
    try:
        date_filter = "CURRENT_DATE" if not date else "%s"
        params = (date,) if date else ()
        
        db.cursor.execute(f"""
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount END), 0) as total_income,
                COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount END), 0) as total_expense,
                COUNT(CASE WHEN transaction_type='income' THEN 1 END) as income_count,
                COUNT(CASE WHEN transaction_type='expense' THEN 1 END) as expense_count
            FROM tbl_financial_transactions
            WHERE transaction_date = {date_filter}
        """, params)
        summary = db.cursor.fetchone()
        
        db.cursor.execute(f"""
            SELECT category, transaction_type, COUNT(*) as cnt, SUM(amount) as total
            FROM tbl_financial_transactions
            WHERE transaction_date = {date_filter}
            GROUP BY category, transaction_type
            ORDER BY total DESC
        """, params)
        categories = db.cursor.fetchall()
        
        return {
            'total_income': float(summary[0]),
            'total_expense': float(summary[1]),
            'income_count': summary[2],
            'expense_count': summary[3],
            'net': float(summary[0]) - float(summary[1]),
            'categories': categories
        }
    except Exception as e:
        print(f"Error getting daily report: {e}")
        return None


def insert_sample_financial_data(db: DatabaseManager):
    """Insert sample financial transactions for February 1-8, 2026"""
    try:
        db.cursor.execute("SELECT COUNT(*) FROM tbl_financial_transactions")
        count = db.cursor.fetchone()[0]
        if count > 0:
            print(f"Financial transaction data already exists ({count} records)")
            return
        
        sample_data = [
            # Feb 1 - Room revenue + expenses
            ('2026-02-01', 'income', 'room_revenue', 'Room 101-105 check-in (5 rooms)', 125000, 'card', 'RES-20260201', 'Walk-in guests', 8261255116, 'Sven'),
            ('2026-02-01', 'income', 'food_beverage', 'Restaurant lunch service', 45000, 'cash', 'REST-001', 'Hotel restaurant', 8261255116, 'Sven'),
            ('2026-02-01', 'expense', 'purchase', 'Fresh vegetables and meat delivery', 28000, 'cash', 'PO-2026-001', 'Farm Market d.o.o.', 8261255116, 'Sven'),
            ('2026-02-01', 'expense', 'utilities', 'Electricity bill - January', 42000, 'bank_transfer', 'EPS-JAN-2026', 'EPS Snabdevanje', 8261255116, 'Sven'),
            ('2026-02-01', 'expense', 'salary', 'Cleaning staff salary advance', 35000, 'cash', 'SAL-ADV-001', 'Hotel staff', 8261255116, 'Sven'),
            
            # Feb 2
            ('2026-02-02', 'income', 'room_revenue', 'Room 201-203 extended stay', 75000, 'card', 'RES-20260202', 'Corporate booking', 8261255116, 'Sven'),
            ('2026-02-02', 'income', 'food_beverage', 'Breakfast buffet + minibar', 32000, 'mixed', 'REST-002', 'Hotel guests', 8261255116, 'Sven'),
            ('2026-02-02', 'expense', 'purchase', 'Cleaning supplies restock', 15000, 'card', 'PO-2026-002', 'Clean Pro d.o.o.', 8261255116, 'Sven'),
            ('2026-02-02', 'expense', 'maintenance', 'AC unit repair - Room 301', 22000, 'cash', 'MNT-001', 'Cool Air Service', 8261255116, 'Sven'),
            
            # Feb 3
            ('2026-02-03', 'income', 'room_revenue', 'Room 301-302 VIP booking', 180000, 'bank_transfer', 'RES-20260203', 'Travel Agency Beograd', 8261255116, 'Sven'),
            ('2026-02-03', 'income', 'other_income', 'Conference room rental', 50000, 'bank_transfer', 'CONF-001', 'IT Solutions Corp', 8261255116, 'Sven'),
            ('2026-02-03', 'expense', 'purchase', 'Bed linens replacement', 45000, 'card', 'PO-2026-003', 'Textile House', 8261255116, 'Sven'),
            
            # Feb 4
            ('2026-02-04', 'income', 'room_revenue', 'Weekend package 4 rooms', 160000, 'card', 'RES-20260204', 'Online booking', 8261255116, 'Sven'),
            ('2026-02-04', 'income', 'food_beverage', 'Dinner event catering', 85000, 'bank_transfer', 'REST-003', 'Private event', 8261255116, 'Sven'),
            ('2026-02-04', 'expense', 'utilities', 'Water bill - January', 18000, 'bank_transfer', 'WATER-JAN-2026', 'JKP Vodovod', 8261255116, 'Sven'),
            ('2026-02-04', 'expense', 'purchase', 'Kitchen equipment - mixer', 35000, 'card', 'PO-2026-004', 'Gastro Equip', 8261255116, 'Sven'),
            
            # Feb 5
            ('2026-02-05', 'income', 'room_revenue', 'Group booking 8 rooms', 200000, 'bank_transfer', 'RES-20260205', 'Tour operator Srbija', 8261255116, 'Sven'),
            ('2026-02-05', 'expense', 'salary', 'February salary - Reception', 620000, 'bank_transfer', 'SAL-FEB-REC', 'Reception team', 8261255116, 'Sven'),
            ('2026-02-05', 'expense', 'tax', 'VAT payment Q4 2025', 185000, 'bank_transfer', 'TAX-VAT-Q4', 'Poreska uprava', 8261255116, 'Sven'),
            
            # Feb 6
            ('2026-02-06', 'income', 'room_revenue', 'Room 101-103 regular', 90000, 'cash', 'RES-20260206', 'Walk-in', 8261255116, 'Sven'),
            ('2026-02-06', 'income', 'food_beverage', 'Bar revenue evening', 28000, 'cash', 'REST-004', 'Bar service', 8261255116, 'Sven'),
            ('2026-02-06', 'expense', 'purchase', 'Beverages wholesale order', 55000, 'cash', 'PO-2026-005', 'Drink Supply', 8261255116, 'Sven'),
            ('2026-02-06', 'expense', 'maintenance', 'Plumbing repair lobby', 12000, 'cash', 'MNT-002', 'Vodoinstalater Mika', 8261255116, 'Sven'),
            
            # Feb 7
            ('2026-02-07', 'income', 'room_revenue', 'Rooms 201-205 corporate', 250000, 'bank_transfer', 'RES-20260207', 'Business Travel Agency', 8261255116, 'Sven'),
            ('2026-02-07', 'income', 'other_income', 'Parking fees collected', 8000, 'cash', 'PARK-007', 'Daily parking', 8261255116, 'Sven'),
            ('2026-02-07', 'expense', 'utilities', 'Internet service - February', 15000, 'bank_transfer', 'NET-FEB-2026', 'SBB Provider', 8261255116, 'Sven'),
            
            # Feb 8 (today)
            ('2026-02-08', 'income', 'room_revenue', 'Room 401-402 suite booking', 180000, 'card', 'RES-20260208', 'VIP guest', 8261255116, 'Sven'),
            ('2026-02-08', 'income', 'food_beverage', 'Sunday brunch buffet', 65000, 'mixed', 'REST-005', 'Hotel restaurant', 8261255116, 'Sven'),
            ('2026-02-08', 'expense', 'purchase', 'Fresh flowers lobby decoration', 8000, 'cash', 'PO-2026-006', 'Flower Shop Ana', 8261255116, 'Sven'),
        ]
        
        for row in sample_data:
            db.cursor.execute("""
                INSERT INTO tbl_financial_transactions 
                (transaction_date, transaction_type, category, description, amount,
                 payment_method, reference_number, vendor_client, recorded_by, recorded_by_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
        
        db.connection.commit()
        
        # Update hotel_accounts with calculated balances
        # Set initial balance for Feb 1
        db.cursor.execute("""
            INSERT INTO tbl_hotel_accounts (date, Room_Revenue, Food_Beverage_Revenue,
                Purchasing_Product_Revenue, Utilities_Expenses, Total_amount,
                cash_balance, bank_balance, total_revenue, total_expenses, net_profit, created_at)
            VALUES ('2026-02-08', 0, 0, 0, 0, 0, 350000, 1200000, 0, 0, 0, CURRENT_DATE)
            ON CONFLICT DO NOTHING
        """)
        db.connection.commit()
        
        print(f"Sample financial data inserted: {len(sample_data)} transactions")
    except Exception as e:
        db.connection.rollback()
        print(f"Error inserting sample financial data: {e}")


# ============================================================
# ACCOUNTING TASKS (Accountant Assignment System)
# ============================================================

def create_accounting_tasks_table(db: DatabaseManager):
    """Create the accounting tasks table for accountant assignments"""
    try:
        db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_accounting_tasks (
                id SERIAL PRIMARY KEY,
                assignee_id TEXT NOT NULL,
                assignee_name TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT,
                due_time TEXT,
                attachment_file_id TEXT,
                attachment_type TEXT,
                status TEXT DEFAULT 'Pending',
                assigned_by TEXT NOT NULL,
                assigned_by_name TEXT NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMP,
                completed_at TIMESTAMP,
                report_notes TEXT,
                report_media_file_id TEXT,
                report_media_type TEXT,
                category TEXT DEFAULT 'other',
                amount DECIMAL(12,2) DEFAULT 0,
                vendor_name TEXT,
                invoice_number TEXT,
                payment_method TEXT DEFAULT 'cash'
            )
        """)
        db.connection.commit()
        
        # Add new columns if table already exists
        new_cols = {
            'category': "TEXT DEFAULT 'other'",
            'amount': "DECIMAL(12,2) DEFAULT 0",
            'vendor_name': "TEXT",
            'invoice_number': "TEXT",
            'payment_method': "TEXT DEFAULT 'cash'"
        }
        for col_name, col_def in new_cols.items():
            try:
                db.cursor.execute(
                    f"ALTER TABLE tbl_accounting_tasks ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                )
                db.connection.commit()
            except Exception:
                db.connection.rollback()
        
        print("tbl_accounting_tasks table ready")
        return True
    except Exception as e:
        print(f"Error creating accounting tasks table: {e}")
        return False


def get_accountants(db: DatabaseManager) -> list:
    """Get all employees in Accounting department"""
    try:
        results = db.execute_query("""
            SELECT employee_id, name, department, work_role
            FROM tbl_employeer
            WHERE LOWER(department) = 'accounting'
        """)
        print(f"✅ Accountants retrieved: {len(results) if results else 0}")
        return results if results else []
    except Exception as e:
        print(f"Error getting accountants: {e}")
        return []


def create_accounting_task(db: DatabaseManager, assignee_id: str, assignee_name: str, 
                          description: str, due_date: str = None, due_time: str = None,
                          assigned_by: str = None, assigned_by_name: str = None,
                          attachment_file_id: str = None, attachment_type: str = None,
                          category: str = 'other', amount: float = 0,
                          vendor_name: str = None, invoice_number: str = None,
                          payment_method: str = 'cash') -> int:
    """Create a new accounting task with financial details"""
    try:
        db.cursor.execute("""
            INSERT INTO tbl_accounting_tasks 
            (assignee_id, assignee_name, description, due_date, due_time, 
             assigned_by, assigned_by_name, attachment_file_id, attachment_type,
             category, amount, vendor_name, invoice_number, payment_method)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (assignee_id, assignee_name, description, due_date, due_time,
              assigned_by, assigned_by_name, attachment_file_id, attachment_type,
              category, amount, vendor_name, invoice_number, payment_method))
        task_id = db.cursor.fetchone()[0]
        db.connection.commit()
        print(f"Accounting task created: ID {task_id}")
        return task_id
    except Exception as e:
        print(f"Error creating accounting task: {e}")
        return None


def get_accounting_tasks_by_assignee(db: DatabaseManager, assignee_id: str) -> list:
    """Get all pending/accepted accounting tasks for a specific accountant"""
    try:
        results = db.execute_query("""
            SELECT id, description, due_date, due_time, status, assigned_at, 
                   accepted_at, completed_at, assigned_by_name,
                   category, amount, vendor_name, invoice_number, payment_method
            FROM tbl_accounting_tasks
            WHERE assignee_id = %s AND status IN ('Pending', 'Accepted')
            ORDER BY 
                CASE WHEN status = 'Pending' THEN 0 ELSE 1 END,
                assigned_at DESC
        """, (assignee_id,))
        return results if results else []
    except Exception as e:
        print(f"Error getting accounting tasks by assignee: {e}")
        return []


def get_accounting_task_by_id(db: DatabaseManager, task_id: int) -> dict:
    """Get a specific accounting task by ID"""
    try:
        result = db.execute_query("""
            SELECT id, assignee_id, assignee_name, description, due_date, due_time,
                   attachment_file_id, attachment_type, status, assigned_by, 
                   assigned_by_name, assigned_at, accepted_at, completed_at,
                   report_notes, report_media_file_id, report_media_type,
                   category, amount, vendor_name, invoice_number, payment_method
            FROM tbl_accounting_tasks
            WHERE id = %s
        """, (task_id,))
        
        if result:
            row = result[0]
            return {
                'id': row[0], 'assignee_id': row[1], 'assignee_name': row[2],
                'description': row[3], 'due_date': row[4], 'due_time': row[5],
                'attachment_file_id': row[6], 'attachment_type': row[7],
                'status': row[8], 'assigned_by': row[9], 'assigned_by_name': row[10],
                'assigned_at': row[11], 'accepted_at': row[12], 'completed_at': row[13],
                'report_notes': row[14], 'report_media_file_id': row[15], 
                'report_media_type': row[16],
                'category': row[17] if len(row) > 17 else 'other',
                'amount': float(row[18]) if len(row) > 18 and row[18] else 0,
                'vendor_name': row[19] if len(row) > 19 else None,
                'invoice_number': row[20] if len(row) > 20 else None,
                'payment_method': row[21] if len(row) > 21 else 'cash'
            }
        return None
    except Exception as e:
        print(f"Error getting accounting task by ID: {e}")
        return None


def accept_accounting_task(db: DatabaseManager, task_id: int) -> bool:
    """Accept an accounting task"""
    try:
        db.cursor.execute("""
            SELECT status FROM tbl_accounting_tasks WHERE id = %s
        """, (task_id,))
        result = db.cursor.fetchone()
        
        if not result:
            print(f"❌ Accounting task {task_id} not found")
            return False
            
        current_status = result[0]
        if current_status != 'Pending':
            print(f"⚠️ Accounting task {task_id} already {current_status}")
            return False
        
        db.cursor.execute("""
            UPDATE tbl_accounting_tasks 
            SET status = 'Accepted', accepted_at = CURRENT_TIMESTAMP
            WHERE id = %s AND status = 'Pending'
        """, (task_id,))
        db.connection.commit()
        
        if db.cursor.rowcount > 0:
            print(f"✅ Accounting task {task_id} accepted")
            return True
        else:
            print(f"⚠️ Accounting task {task_id} was not updated")
            return False
    except Exception as e:
        print(f"Error accepting accounting task: {e}")
        return False


def complete_accounting_task(db: DatabaseManager, task_id: int, report_notes: str = '', 
                            report_media_file_id: str = None, report_media_type: str = None) -> bool:
    """Complete an accounting task with optional report"""
    try:
        db.cursor.execute("""
            UPDATE tbl_accounting_tasks 
            SET status = 'Completed', completed_at = CURRENT_TIMESTAMP,
                report_notes = %s, report_media_file_id = %s, report_media_type = %s
            WHERE id = %s
        """, (report_notes, report_media_file_id, report_media_type, task_id))
        db.connection.commit()
        print(f"✅ Accounting task {task_id} completed")
        return True
    except Exception as e:
        print(f"Error completing accounting task: {e}")
        return False


def get_accounting_tasks_summary(db: DatabaseManager, period: str = 'daily') -> dict:
    """
    Get accounting tasks summary with financial analysis
    
    Args:
        db: Database manager
        period: 'daily', 'weekly', 'monthly'
    
    Returns:
        Summary dict with totals by category, status counts, amounts
    """
    from datetime import datetime, timedelta
    
    try:
        today = datetime.now()
        
        if period == 'daily':
            start_date = today.strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif period == 'weekly':
            start_of_week = today - timedelta(days=today.weekday())
            start_date = start_of_week.strftime('%Y-%m-%d')
            end_date = (start_of_week + timedelta(days=7)).strftime('%Y-%m-%d')
        else:  # monthly
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            if today.month == 12:
                end_date = today.replace(year=today.year+1, month=1, day=1).strftime('%Y-%m-%d')
            else:
                end_date = today.replace(month=today.month+1, day=1).strftime('%Y-%m-%d')
        
        # Status counts
        db.cursor.execute("""
            SELECT status, COUNT(*) as cnt
            FROM tbl_accounting_tasks 
            WHERE assigned_at >= %s AND assigned_at < %s
            GROUP BY status
        """, (start_date, end_date))
        status_counts = {}
        for row in db.cursor.fetchall():
            status_counts[row[0]] = row[1]
        
        # Category totals
        db.cursor.execute("""
            SELECT COALESCE(category, 'other'), COUNT(*), COALESCE(SUM(amount), 0)
            FROM tbl_accounting_tasks
            WHERE assigned_at >= %s AND assigned_at < %s
            GROUP BY COALESCE(category, 'other')
            ORDER BY COALESCE(SUM(amount), 0) DESC
        """, (start_date, end_date))
        category_data = []
        for row in db.cursor.fetchall():
            category_data.append({
                'category': row[0],
                'count': row[1],
                'total_amount': float(row[2]) if row[2] else 0
            })
        
        # Overall totals
        db.cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0)
            FROM tbl_accounting_tasks
            WHERE assigned_at >= %s AND assigned_at < %s
        """, (start_date, end_date))
        row = db.cursor.fetchone()
        total_tasks = row[0] if row else 0
        total_amount = float(row[1]) if row and row[1] else 0
        
        # Payment method breakdown
        db.cursor.execute("""
            SELECT COALESCE(payment_method, 'cash'), COUNT(*), COALESCE(SUM(amount), 0)
            FROM tbl_accounting_tasks
            WHERE assigned_at >= %s AND assigned_at < %s AND status = 'Completed'
            GROUP BY COALESCE(payment_method, 'cash')
        """, (start_date, end_date))
        payment_data = []
        for row in db.cursor.fetchall():
            payment_data.append({
                'method': row[0],
                'count': row[1],
                'total': float(row[2]) if row[2] else 0
            })
        
        return {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'total_tasks': total_tasks,
            'total_amount': total_amount,
            'status_counts': status_counts,
            'category_data': category_data,
            'payment_data': payment_data
        }
    except Exception as e:
        print(f"Error getting accounting summary: {e}")
        return None


def get_accounting_tasks_history(db: DatabaseManager, start_date: str = None, 
                                 end_date: str = None, category: str = None,
                                 limit: int = 20) -> list:
    """Get accounting tasks history with filters"""
    try:
        query = """
            SELECT id, assignee_name, description, due_date, due_time, status,
                   assigned_at, completed_at, assigned_by_name,
                   category, amount, vendor_name, invoice_number, payment_method
            FROM tbl_accounting_tasks
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND assigned_at >= %s"
            params.append(start_date)
        if end_date:
            query += " AND assigned_at < %s"
            params.append(end_date)
        if category:
            query += " AND category = %s"
            params.append(category)
        
        query += " ORDER BY assigned_at DESC LIMIT %s"
        params.append(limit)
        
        results = db.execute_query(query, tuple(params))
        
        tasks = []
        if results:
            for row in results:
                tasks.append({
                    'id': row[0], 'assignee_name': row[1], 'description': row[2],
                    'due_date': row[3], 'due_time': row[4], 'status': row[5],
                    'assigned_at': row[6], 'completed_at': row[7],
                    'assigned_by_name': row[8], 'category': row[9],
                    'amount': float(row[10]) if row[10] else 0,
                    'vendor_name': row[11], 'invoice_number': row[12],
                    'payment_method': row[13]
                })
        return tasks
    except Exception as e:
        print(f"Error getting accounting history: {e}")
        return []


def insert_sample_accounting_data(db: DatabaseManager) -> bool:
    """Insert sample accounting data from February 1, 2026 for analysis"""
    try:
        # Check if sample data already exists
        db.cursor.execute("""
            SELECT COUNT(*) FROM tbl_accounting_tasks 
            WHERE assigned_at >= '2026-02-01' AND assigned_at < '2026-02-09'
            AND description LIKE '%[SAMPLE]%'
        """)
        count = db.cursor.fetchone()[0]
        if count > 0:
            print(f"Sample data already exists ({count} records)")
            return True
        
        sample_tasks = [
            # Feb 1 - Supplier invoice
            ("7836819730", "CPN", "[SAMPLE] Supplier invoice - ABC Food d.o.o.", 
             "2026-02-02", "17:00", "Completed", "8541474860", "Jovan",
             "2026-02-01 09:00:00", "2026-02-01 09:15:00", "2026-02-01 14:30:00",
             "Invoice verified and processed", "invoice", 125000.00, 
             "ABC Food d.o.o.", "INV-2026-0201", "bank_transfer"),
            
            # Feb 1 - Petty cash
            ("7836819730", "CPN", "[SAMPLE] Petty cash - Office supplies",
             "2026-02-01", "12:00", "Completed", "8541474860", "Jovan",
             "2026-02-01 10:00:00", "2026-02-01 10:05:00", "2026-02-01 11:30:00",
             "Receipt collected and filed", "petty_cash", 3500.00,
             "Papirnica Beograd", None, "cash"),
            
            # Feb 2 - Utility bill
            ("7836819730", "CPN", "[SAMPLE] Electricity bill - January 2026",
             "2026-02-05", "17:00", "Completed", "8541474860", "Jovan",
             "2026-02-02 08:30:00", "2026-02-02 08:45:00", "2026-02-02 10:00:00",
             "Payment processed via bank", "utility", 87500.00,
             "EPS Distribucija", "EPS-JAN-2026", "bank_transfer"),
            
            # Feb 2 - Guest deposit
            ("7836819730", "CPN", "[SAMPLE] Guest deposit - Room 205 check-in",
             "2026-02-02", "14:00", "Completed", "8541474860", "Jovan",
             "2026-02-02 13:00:00", "2026-02-02 13:05:00", "2026-02-02 13:30:00",
             "Deposit received and recorded", "deposit", 15000.00,
             None, "DEP-0205-0202", "cash"),
            
            # Feb 3 - Supplier payment
            ("7836819730", "CPN", "[SAMPLE] Cleaning supplies - Hemija Plus",
             "2026-02-04", "17:00", "Completed", "8541474860", "Jovan",
             "2026-02-03 09:00:00", "2026-02-03 09:10:00", "2026-02-03 15:00:00",
             "Invoice paid, goods received", "supplier", 45000.00,
             "Hemija Plus d.o.o.", "INV-HP-1234", "bank_transfer"),
            
            # Feb 3 - Receipt recording
            ("7836819730", "CPN", "[SAMPLE] Restaurant daily revenue recording",
             "2026-02-03", "22:00", "Completed", "8541474860", "Jovan",
             "2026-02-03 20:00:00", "2026-02-03 20:05:00", "2026-02-03 21:30:00",
             "Daily revenue reconciled", "receipt", 230000.00,
             None, "RCV-0203", "cash"),
            
            # Feb 4 - Tax payment
            ("7836819730", "CPN", "[SAMPLE] VAT payment - Q4 2025",
             "2026-02-10", "17:00", "Completed", "8541474860", "Jovan",
             "2026-02-04 09:00:00", "2026-02-04 09:30:00", "2026-02-04 11:00:00",
             "Tax payment submitted to PU", "tax", 450000.00,
             "Poreska Uprava", "PDV-Q4-2025", "bank_transfer"),
            
            # Feb 4 - Refund processing
            ("7836819730", "CPN", "[SAMPLE] Guest refund - Room 301 early checkout",
             "2026-02-04", "15:00", "Completed", "8541474860", "Jovan",
             "2026-02-04 12:00:00", "2026-02-04 12:10:00", "2026-02-04 14:00:00",
             "Refund processed to guest card", "refund", 8500.00,
             None, "REF-0301-0204", "card"),
            
            # Feb 5 - Salary payment
            ("7836819730", "CPN", "[SAMPLE] Staff salary - January 2026 Reception",
             "2026-02-05", "17:00", "Completed", "8541474860", "Jovan",
             "2026-02-05 09:00:00", "2026-02-05 09:15:00", "2026-02-05 16:00:00",
             "Salaries transferred for 5 employees", "salary", 750000.00,
             None, "SAL-JAN-REC", "bank_transfer"),
            
            # Feb 5 - Supplier invoice
            ("7836819730", "CPN", "[SAMPLE] Laundry chemicals - Clean Pro",
             "2026-02-07", "17:00", "Completed", "8541474860", "Jovan",
             "2026-02-05 14:00:00", "2026-02-05 14:10:00", "2026-02-05 16:30:00",
             "Invoice received, scheduled for payment", "invoice", 32000.00,
             "Clean Pro d.o.o.", "INV-CP-5678", "bank_transfer"),
            
            # Feb 6 - Audit task
            ("7836819730", "CPN", "[SAMPLE] Monthly cash audit - January 2026",
             "2026-02-07", "17:00", "Completed", "8541474860", "Jovan",
             "2026-02-06 09:00:00", "2026-02-06 09:20:00", "2026-02-06 17:00:00",
             "Cash count verified, report submitted", "audit", 0,
             None, "AUD-JAN-2026", None),
            
            # Feb 6 - Bank transaction
            ("7836819730", "CPN", "[SAMPLE] Bank reconciliation - weekly",
             "2026-02-06", "17:00", "Completed", "8541474860", "Jovan",
             "2026-02-06 14:00:00", "2026-02-06 14:10:00", "2026-02-06 16:00:00",
             "All transactions reconciled", "bank", 0,
             "Komercijalna Banka", "BNK-W05-2026", "bank_transfer"),
            
            # Feb 7 - Receipt 
            ("7836819730", "CPN", "[SAMPLE] Weekend room revenue recording",
             "2026-02-07", "22:00", "Completed", "8541474860", "Jovan",
             "2026-02-07 20:00:00", "2026-02-07 20:05:00", "2026-02-07 21:00:00",
             "Weekend revenue entered", "receipt", 185000.00,
             None, "RCV-0207", "mixed"),
            
            # Feb 7 - Supplier payment
            ("7836819730", "CPN", "[SAMPLE] Kitchen supplies - Maxi Gastro",
             "2026-02-08", "17:00", "Completed", "8541474860", "Jovan",
             "2026-02-07 10:00:00", "2026-02-07 10:15:00", "2026-02-07 14:00:00",
             "Payment processed", "supplier", 67000.00,
             "Maxi Gastro d.o.o.", "INV-MG-9012", "bank_transfer"),
            
            # Feb 8 - Pending tasks
            ("7836819730", "CPN", "[SAMPLE] Water bill - January 2026",
             "2026-02-10", "17:00", "Pending", "8541474860", "Jovan",
             "2026-02-08 08:00:00", None, None,
             None, "utility", 42000.00,
             "BVK Beograd", "BVK-JAN-2026", "bank_transfer"),
            
            ("7836819730", "CPN", "[SAMPLE] Staff salary - January 2026 Housekeeping",
             "2026-02-08", "17:00", "Accepted", "8541474860", "Jovan",
             "2026-02-08 08:30:00", "2026-02-08 08:45:00", None,
             None, "salary", 620000.00,
             None, "SAL-JAN-HSK", "bank_transfer"),
            
            # Feb 8 - Financial report
            ("7836819730", "CPN", "[SAMPLE] Weekly financial report - W5 2026",
             "2026-02-09", "12:00", "Pending", "8541474860", "Jovan",
             "2026-02-08 09:00:00", None, None,
             None, "report", 0,
             None, "RPT-W05-2026", None),
        ]
        
        for task in sample_tasks:
            db.cursor.execute("""
                INSERT INTO tbl_accounting_tasks 
                (assignee_id, assignee_name, description, due_date, due_time,
                 status, assigned_by, assigned_by_name, assigned_at, accepted_at, 
                 completed_at, report_notes, category, amount, vendor_name, 
                 invoice_number, payment_method)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, task)
        
        db.connection.commit()
        print(f"Sample accounting data inserted: {len(sample_tasks)} records")
        return True
    except Exception as e:
        db.connection.rollback()
        print(f"Error inserting sample data: {e}")
        return False


# ============================================================
# DEPARTMENT STATISTICS (Daily/Weekly/Monthly)
# ============================================================

def get_department_task_stats(db: DatabaseManager, department: str, period: str = 'daily') -> dict:
    """
    Get task statistics for a department by period (daily/weekly/monthly)
    
    Args:
        db: Database connection
        department: Department name (e.g., 'Laundry', 'Restaurant', 'Transportation', 'Accounting')
        period: 'daily', 'weekly', or 'monthly'
    
    Returns:
        Dictionary with task statistics
    """
    from datetime import datetime, timedelta
    
    try:
        today = datetime.now()
        
        # Determine table and date field based on department
        table_map = {
            'Laundry': ('tbl_laundry_tasks', 'assigned_at'),
            'Restaurant': ('tbl_restaurant_tasks', 'assigned_at'),
            'Transportation': ('tbl_delivery_tasks', 'assigned_at'),
            'Accounting': ('tbl_accounting_tasks', 'assigned_at'),
        }
        
        if department not in table_map:
            return None
        
        table_name, date_field = table_map[department]
        
        # Check if table exists (PostgreSQL)
        db.cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            )
        """, (table_name,))
        if not db.cursor.fetchone()[0]:
            return {'total': 0, 'pending': 0, 'accepted': 0, 'completed': 0, 'tasks': [], 'period_label': ''}
        
        # Calculate date range based on period
        if period == 'daily':
            start_date = today.strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
            period_label = f"Danas ({today.strftime('%d.%m.%Y')})"
        elif period == 'weekly':
            # Start of week (Monday)
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=7)
            start_date = start_of_week.strftime('%Y-%m-%d')
            end_date = end_of_week.strftime('%Y-%m-%d')
            period_label = f"Ova nedelja ({start_of_week.strftime('%d.%m')} - {(end_of_week - timedelta(days=1)).strftime('%d.%m.%Y')})"
        elif period == 'monthly':
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            # First day of next month
            if today.month == 12:
                end_date = today.replace(year=today.year+1, month=1, day=1).strftime('%Y-%m-%d')
            else:
                end_date = today.replace(month=today.month+1, day=1).strftime('%Y-%m-%d')
            period_label = f"Ovaj mesec ({today.strftime('%B %Y')})"
        else:
            return None
        
        # Get task counts by status
        db.cursor.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) as accepted,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM {table_name}
            WHERE DATE({date_field}) >= %s AND DATE({date_field}) < %s
        """, (start_date, end_date))
        
        row = db.cursor.fetchone()
        total, pending, accepted, completed = row if row else (0, 0, 0, 0)
        
        # Get recent tasks (up to 10)
        db.cursor.execute(f"""
            SELECT id, assignee_name, description, status, {date_field}, completed_at
            FROM {table_name}
            WHERE DATE({date_field}) >= %s AND DATE({date_field}) < %s
            ORDER BY {date_field} DESC
            LIMIT 10
        """, (start_date, end_date))
        
        tasks = []
        for task in db.cursor.fetchall():
            task_id, assignee, desc, status, assigned_at, completed_at = task
            tasks.append({
                'id': task_id,
                'assignee': assignee,
                'description': desc[:30] + '...' if len(desc) > 30 else desc,
                'status': status,
                'assigned_at': assigned_at,
                'completed_at': completed_at
            })
        
        return {
            'total': total or 0,
            'pending': pending or 0,
            'accepted': accepted or 0,
            'completed': completed or 0,
            'tasks': tasks,
            'period_label': period_label
        }
        
    except Exception as e:
        print(f"Error getting department task stats: {e}")
        return {'total': 0, 'pending': 0, 'accepted': 0, 'completed': 0, 'tasks': [], 'period_label': ''}


def get_clean_history_stats(db: DatabaseManager, period: str = 'daily') -> dict:
    """Get cleaning statistics by period"""
    from datetime import datetime, timedelta
    
    try:
        today = datetime.now()
        
        if period == 'daily':
            start_date = today.strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
            period_label = f"Danas ({today.strftime('%d.%m.%Y')})"
        elif period == 'weekly':
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=7)
            start_date = start_of_week.strftime('%Y-%m-%d')
            end_date = end_of_week.strftime('%Y-%m-%d')
            period_label = f"Ova nedelja ({start_of_week.strftime('%d.%m')} - {(end_of_week - timedelta(days=1)).strftime('%d.%m.%Y')})"
        elif period == 'monthly':
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            if today.month == 12:
                end_date = today.replace(year=today.year+1, month=1, day=1).strftime('%Y-%m-%d')
            else:
                end_date = today.replace(month=today.month+1, day=1).strftime('%Y-%m-%d')
            period_label = f"Ovaj mesec ({today.strftime('%B %Y')})"
        else:
            return None
        
        # Get cleaning counts
        db.cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT cleaned_by) as cleaners,
                COUNT(DISTINCT room_number) as rooms_cleaned
            FROM tbl_clean_history
            WHERE DATE(created_at) >= %s AND DATE(created_at) < %s
        """, (start_date, end_date))
        
        row = db.cursor.fetchone()
        total, cleaners, rooms = row if row else (0, 0, 0)
        
        # Get recent cleaning records
        db.cursor.execute("""
            SELECT id, room_number, cleaned_by_name, clean_type, created_at
            FROM tbl_clean_history
            WHERE DATE(created_at) >= %s AND DATE(created_at) < %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (start_date, end_date))
        
        records = []
        for record in db.cursor.fetchall():
            rec_id, room, cleaner, clean_type, created_at = record
            records.append({
                'id': rec_id,
                'room': room,
                'cleaner': cleaner,
                'type': clean_type,
                'created_at': created_at
            })
        
        return {
            'total': total or 0,
            'cleaners': cleaners or 0,
            'rooms_cleaned': rooms or 0,
            'records': records,
            'period_label': period_label
        }
        
    except Exception as e:
        print(f"Error getting clean history stats: {e}")
        return {'total': 0, 'cleaners': 0, 'rooms_cleaned': 0, 'records': [], 'period_label': ''}


# ============================================================
# REPAIR TASKS (Technical Department)
# ============================================================

def create_repair_tasks_table(db: DatabaseManager):
    """Create repair tasks table if not exists"""
    try:
        db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_repair_tasks (
                id SERIAL PRIMARY KEY,
                room_id INTEGER,
                room_number TEXT,
                floor INTEGER,
                assignee_id BIGINT,
                assignee_name TEXT,
                description TEXT,
                repair_type TEXT,
                priority TEXT DEFAULT 'Normal',
                due_date TEXT,
                due_time TEXT,
                proof_required INTEGER DEFAULT 0,
                proof_path TEXT,
                proof_media_type TEXT,
                proof_file_id TEXT,
                status TEXT DEFAULT 'Pending',
                assigned_by BIGINT,
                assigned_by_name TEXT,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                accepted_at DATETIME,
                completed_at DATETIME,
                report_notes TEXT
            )
        """)
        db.connection.commit()
        
        # Add proof columns if they don't exist (for existing tables)
        try:
            db.cursor.execute("ALTER TABLE tbl_repair_tasks ADD COLUMN IF NOT EXISTS proof_media_type TEXT")
            db.connection.commit()
        except:
            pass
        try:
            db.cursor.execute("ALTER TABLE tbl_repair_tasks ADD COLUMN IF NOT EXISTS proof_file_id TEXT")
            db.connection.commit()
        except:
            pass
            
        print("✅ tbl_repair_tasks table ready")
        return True
    except Exception as e:
        print(f"Error creating repair tasks table: {e}")
        return False


def get_technical_employees(db: DatabaseManager) -> list:
    """Get all employees in Technical department"""
    try:
        result = db.execute_query("""
            SELECT telegram_user_id, employee_id, name, work_role 
            FROM tbl_employeer 
            WHERE department = 'Technical' OR department = 'technical'
            ORDER BY name
        """)
        return result if result else []
    except Exception as e:
        print(f"Error getting technical employees: {e}")
        return []


def create_repair_task(db: DatabaseManager, room_id: int, room_number: str, floor: int,
                       assignee_id: int, assignee_name: str, description: str,
                       repair_type: str, priority: str, due_date: str, due_time: str,
                       proof_required: int, assigned_by: int, assigned_by_name: str) -> int:
    """Create a new repair task"""
    try:
        db.cursor.execute("""
            INSERT INTO tbl_repair_tasks 
            (room_id, room_number, floor, assignee_id, assignee_name, description,
             repair_type, priority, due_date, due_time, proof_required, 
             assigned_by, assigned_by_name, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
            RETURNING id
        """, (room_id, room_number, floor, assignee_id, assignee_name, description,
              repair_type, priority, due_date, due_time, proof_required, 
              assigned_by, assigned_by_name))
        task_id = db.cursor.fetchone()[0]
        db.connection.commit()
        print(f"✅ Repair task created: ID {task_id}, Room {room_number}")
        return task_id
    except Exception as e:
        print(f"Error creating repair task: {e}")
        return None


def get_pending_repair_tasks(db: DatabaseManager, assignee_id: int) -> list:
    """Get pending repair tasks for an employee"""
    try:
        result = db.execute_query("""
            SELECT id, room_id, room_number, floor, description, repair_type, priority,
                   due_date, due_time, proof_required, assigned_by_name, assigned_at, status
            FROM tbl_repair_tasks 
            WHERE assignee_id = %s AND status IN ('Pending', 'Accepted')
            ORDER BY 
                CASE priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2 WHEN 'Normal' THEN 3 ELSE 4 END,
                due_date ASC, due_time ASC
        """, (assignee_id,))
        return result if result else []
    except Exception as e:
        print(f"Error getting pending repair tasks: {e}")
        return []


def get_all_repair_tasks(db: DatabaseManager, status: str = None) -> list:
    """Get all repair tasks, optionally filtered by status"""
    try:
        if status:
            result = db.execute_query("""
                SELECT id, room_number, floor, assignee_name, description, repair_type, 
                       priority, due_date, due_time, status, assigned_at, completed_at
                FROM tbl_repair_tasks 
                WHERE status = %s
                ORDER BY assigned_at DESC
            """, (status,))
        else:
            result = db.execute_query("""
                SELECT id, room_number, floor, assignee_name, description, repair_type,
                       priority, due_date, due_time, status, assigned_at, completed_at
                FROM tbl_repair_tasks 
                ORDER BY assigned_at DESC
            """)
        return result if result else []
    except Exception as e:
        print(f"Error getting repair tasks: {e}")
        return []


def get_repair_task_by_id(db: DatabaseManager, task_id: int) -> tuple:
    """Get repair task by ID"""
    try:
        result = db.execute_query("""
            SELECT id, room_id, room_number, floor, assignee_id, assignee_name, 
                   description, repair_type, priority, due_date, due_time, 
                   proof_required, proof_path, status, assigned_by, assigned_by_name,
                   assigned_at, accepted_at, completed_at, report_notes
            FROM tbl_repair_tasks 
            WHERE id = %s
        """, (task_id,))
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting repair task: {e}")
        return None


def accept_repair_task(db: DatabaseManager, task_id: int) -> bool:
    """Accept a repair task"""
    try:
        db.cursor.execute("""
            UPDATE tbl_repair_tasks 
            SET status = 'Accepted', accepted_at = CURRENT_TIMESTAMP
            WHERE id = %s AND status = 'Pending'
        """, (task_id,))
        db.connection.commit()
        return db.cursor.rowcount > 0
    except Exception as e:
        print(f"Error accepting repair task: {e}")
        return False


def complete_repair_task(db: DatabaseManager, task_id: int, report_notes: str = None,
                         proof_path: str = None, proof_media_type: str = None,
                         proof_file_id: str = None) -> bool:
    """Complete a repair task with optional proof media"""
    try:
        db.cursor.execute("""
            UPDATE tbl_repair_tasks 
            SET status = 'Completed', completed_at = CURRENT_TIMESTAMP,
                report_notes = %s, proof_path = %s, proof_media_type = %s, proof_file_id = %s
            WHERE id = %s AND status = 'Accepted'
        """, (report_notes, proof_path, proof_media_type, proof_file_id, task_id))
        db.connection.commit()
        return db.cursor.rowcount > 0
    except Exception as e:
        print(f"Error completing repair task: {e}")
        return False


def get_repair_tasks_summary(db: DatabaseManager) -> dict:
    """Get summary of repair tasks"""
    try:
        pending = db.execute_query(
            "SELECT COUNT(*) FROM tbl_repair_tasks WHERE status = 'Pending'"
        )[0][0]
        accepted = db.execute_query(
            "SELECT COUNT(*) FROM tbl_repair_tasks WHERE status = 'Accepted'"
        )[0][0]
        completed = db.execute_query(
            "SELECT COUNT(*) FROM tbl_repair_tasks WHERE status = 'Completed'"
        )[0][0]
        total = db.execute_query(
            "SELECT COUNT(*) FROM tbl_repair_tasks"
        )[0][0]
        return {
            'pending': pending or 0,
            'accepted': accepted or 0,
            'completed': completed or 0,
            'total': total or 0
        }
    except Exception as e:
        print(f"Error getting repair tasks summary: {e}")
        return {'pending': 0, 'accepted': 0, 'completed': 0, 'total': 0}


def get_repair_task_stats(db: DatabaseManager, period: str = 'daily') -> dict:
    """Get repair task statistics by period"""
    try:
        from datetime import datetime, timedelta
        
        now = datetime.now()
        if period == 'daily':
            date_filter = now.strftime('%Y-%m-%d')
            period_label = f"Danas ({date_filter})"
            where_clause = "DATE(assigned_at) = %s"
        elif period == 'weekly':
            week_start = now - timedelta(days=now.weekday())
            date_filter = week_start.strftime('%Y-%m-%d')
            period_label = f"Ova nedelja (od {date_filter})"
            where_clause = "DATE(assigned_at) >= %s"
        else:  # monthly
            date_filter = now.strftime('%Y-%m-01')
            period_label = f"Ovaj mesec ({now.strftime('%B %Y')})"
            where_clause = "DATE(assigned_at) >= %s"
        
        total = db.execute_query(f"""
            SELECT COUNT(*) FROM tbl_repair_tasks WHERE {where_clause}
        """, (date_filter,))[0][0]
        
        pending = db.execute_query(f"""
            SELECT COUNT(*) FROM tbl_repair_tasks 
            WHERE {where_clause} AND status = 'Pending'
        """, (date_filter,))[0][0]
        
        accepted = db.execute_query(f"""
            SELECT COUNT(*) FROM tbl_repair_tasks 
            WHERE {where_clause} AND status = 'Accepted'
        """, (date_filter,))[0][0]
        
        completed = db.execute_query(f"""
            SELECT COUNT(*) FROM tbl_repair_tasks 
            WHERE {where_clause} AND status = 'Completed'
        """, (date_filter,))[0][0]
        
        tasks = db.execute_query(f"""
            SELECT id, assignee_name, description, status 
            FROM tbl_repair_tasks 
            WHERE {where_clause}
            ORDER BY assigned_at DESC
            LIMIT 10
        """, (date_filter,))
        
        task_list = []
        for task in (tasks or []):
            task_list.append({
                'id': task[0],
                'assignee': task[1],
                'description': task[2][:30] + '...' if len(task[2]) > 30 else task[2],
                'status': task[3]
            })
        
        return {
            'total': total or 0,
            'pending': pending or 0,
            'accepted': accepted or 0,
            'completed': completed or 0,
            'tasks': task_list,
            'period_label': period_label
        }
    except Exception as e:
        print(f"Error getting repair task stats: {e}")
        return {'total': 0, 'pending': 0, 'accepted': 0, 'completed': 0, 'tasks': [], 'period_label': ''}


# ==================== TRANSPORTATION MANAGEMENT ====================

def get_all_transportations(db: DatabaseManager) -> list:
    """Get all transportations"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT id, plate_number, name, vehicle_type, description, state, created_by, created_at, updated_at
            FROM tbl_hotel_transportations 
            WHERE state = 1
            ORDER BY name ASC
        """)
        rows = cursor.fetchall()
        return [{
            'id': row[0],
            'plate_number': row[1],
            'name': row[2],
            'vehicle_type': row[3],
            'description': row[4],
            'state': row[5],
            'created_by': row[6],
            'created_at': row[7],
            'updated_at': row[8]
        } for row in rows]
    except Exception as e:
        print(f"Error getting transportations: {e}")
        return []


def get_transportation_by_id(db: DatabaseManager, transport_id: int) -> dict:
    """Get transportation by ID"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT id, plate_number, name, vehicle_type, description, state, created_by, created_at, updated_at
            FROM tbl_hotel_transportations WHERE id = %s
        """, (transport_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'plate_number': row[1],
                'name': row[2],
                'vehicle_type': row[3],
                'description': row[4],
                'state': row[5],
                'created_by': row[6],
                'created_at': row[7],
                'updated_at': row[8]
            }
        return None
    except Exception as e:
        print(f"Error getting transportation by ID: {e}")
        return None


def create_transportation(db: DatabaseManager, plate_number: str, name: str, vehicle_type: str, description: str, created_by: int) -> int:
    """Create new transportation"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO tbl_hotel_transportations (plate_number, name, vehicle_type, description, created_by)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (plate_number, name, vehicle_type, description, created_by))
        result = cursor.fetchone()[0]
        db.connection.commit()
        return result
    except Exception as e:
        print(f"Error creating transportation: {e}")
        return None


def update_transportation(db: DatabaseManager, transport_id: int, plate_number: str = None, name: str = None, vehicle_type: str = None, description: str = None) -> bool:
    """Update transportation"""
    try:
        cursor = db.connection.cursor()
        updates = []
        params = []
        
        if plate_number:
            updates.append("plate_number = %s")
            params.append(plate_number)
        if name:
            updates.append("name = %s")
            params.append(name)
        if vehicle_type:
            updates.append("vehicle_type = %s")
            params.append(vehicle_type)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(transport_id)
            cursor.execute(f"""
                UPDATE tbl_hotel_transportations 
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            db.connection.commit()
            return True
        return False
    except Exception as e:
        print(f"Error updating transportation: {e}")
        return False


def delete_transportation(db: DatabaseManager, transport_id: int) -> bool:
    """Delete transportation (soft delete)"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            UPDATE tbl_hotel_transportations SET state = 0, updated_at = CURRENT_TIMESTAMP WHERE id = %s
        """, (transport_id,))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"Error deleting transportation: {e}")
        return False


# ==================== STORAGE MANAGEMENT ====================

def get_all_storages(db: DatabaseManager) -> list:
    """Get all storages"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT id, name, storage_type, description, state, created_by, created_at, updated_at
            FROM tbl_hotel_storages 
            WHERE state = 1
            ORDER BY name ASC
        """)
        rows = cursor.fetchall()
        return [{
            'id': row[0],
            'name': row[1],
            'storage_type': row[2],
            'description': row[3],
            'state': row[4],
            'created_by': row[5],
            'created_at': row[6],
            'updated_at': row[7]
        } for row in rows]
    except Exception as e:
        print(f"Error getting storages: {e}")
        return []


def get_storage_by_id(db: DatabaseManager, storage_id: int) -> dict:
    """Get storage by ID"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT id, name, storage_type, description, state, created_by, created_at, updated_at
            FROM tbl_hotel_storages WHERE id = %s
        """, (storage_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'storage_type': row[2],
                'description': row[3],
                'state': row[4],
                'created_by': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            }
        return None
    except Exception as e:
        print(f"Error getting storage by ID: {e}")
        return None


def create_storage(db: DatabaseManager, name: str, storage_type: str, description: str, created_by: int) -> int:
    """Create new storage"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO tbl_hotel_storages (name, storage_type, description, created_by)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (name, storage_type, description, created_by))
        result = cursor.fetchone()[0]
        db.connection.commit()
        return result
    except Exception as e:
        print(f"Error creating storage: {e}")
        return None


def update_storage(db: DatabaseManager, storage_id: int, name: str = None, storage_type: str = None, description: str = None) -> bool:
    """Update storage"""
    try:
        cursor = db.connection.cursor()
        updates = []
        params = []
        
        if name:
            updates.append("name = %s")
            params.append(name)
        if storage_type:
            updates.append("storage_type = %s")
            params.append(storage_type)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(storage_id)
            cursor.execute(f"""
                UPDATE tbl_hotel_storages 
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            db.connection.commit()
            return True
        return False
    except Exception as e:
        print(f"Error updating storage: {e}")
        return False


def delete_storage(db: DatabaseManager, storage_id: int) -> bool:
    """Delete storage (soft delete)"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            UPDATE tbl_hotel_storages SET state = 0, updated_at = CURRENT_TIMESTAMP WHERE id = %s
        """, (storage_id,))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"Error deleting storage: {e}")
        return False


# ==================== EXTERNAL SERVICE CONTACTS MANAGEMENT ====================

def get_all_contacts(db: DatabaseManager) -> list:
    """Get all external service contacts"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT id, name, contact_type, email, whatsapp, description, state, created_by, created_at, updated_at
            FROM tbl_out_contacts 
            WHERE state = 1
            ORDER BY contact_type, name ASC
        """)
        rows = cursor.fetchall()
        return [{
            'id': row[0],
            'name': row[1],
            'contact_type': row[2],
            'email': row[3],
            'whatsapp': row[4],
            'description': row[5],
            'state': row[6],
            'created_by': row[7],
            'created_at': row[8],
            'updated_at': row[9]
        } for row in rows]
    except Exception as e:
        print(f"Error getting contacts: {e}")
        return []


def get_contact_by_id(db: DatabaseManager, contact_id: int) -> dict:
    """Get contact by ID"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT id, name, contact_type, email, whatsapp, description, state, created_by, created_at, updated_at
            FROM tbl_out_contacts WHERE id = %s
        """, (contact_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'contact_type': row[2],
                'email': row[3],
                'whatsapp': row[4],
                'description': row[5],
                'state': row[6],
                'created_by': row[7],
                'created_at': row[8],
                'updated_at': row[9]
            }
        return None
    except Exception as e:
        print(f"Error getting contact by ID: {e}")
        return None


def create_contact(db: DatabaseManager, name: str, contact_type: str, email: str, whatsapp: str, description: str, created_by: int) -> int:
    """Create new external service contact"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO tbl_out_contacts (name, contact_type, email, whatsapp, description, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (name, contact_type, email, whatsapp, description, created_by))
        result = cursor.fetchone()[0]
        db.connection.commit()
        return result
    except Exception as e:
        print(f"Error creating contact: {e}")
        return None


def update_contact(db: DatabaseManager, contact_id: int, name: str = None, contact_type: str = None, email: str = None, whatsapp: str = None, description: str = None) -> bool:
    """Update contact"""
    try:
        cursor = db.connection.cursor()
        updates = []
        params = []
        
        if name:
            updates.append("name = %s")
            params.append(name)
        if contact_type:
            updates.append("contact_type = %s")
            params.append(contact_type)
        if email:
            updates.append("email = %s")
            params.append(email)
        if whatsapp:
            updates.append("whatsapp = %s")
            params.append(whatsapp)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(contact_id)
            cursor.execute(f"""
                UPDATE tbl_out_contacts 
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            db.connection.commit()
            return True
        return False
    except Exception as e:
        print(f"Error updating contact: {e}")
        return False


def delete_contact(db: DatabaseManager, contact_id: int) -> bool:
    """Delete contact (soft delete)"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            UPDATE tbl_out_contacts SET state = 0, updated_at = CURRENT_TIMESTAMP WHERE id = %s
        """, (contact_id,))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"Error deleting contact: {e}")
        return False


# ==================== VEHICLE USAGE MANAGEMENT ====================

def get_available_vehicles(db: DatabaseManager) -> list:
    """Get all available vehicles (not currently borrowed)"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT t.id, t.plate_number, t.name, t.vehicle_type, t.description
            FROM tbl_hotel_transportations t
            WHERE t.state = 1 
            AND t.id NOT IN (
                SELECT vehicle_id FROM tbl_vehicle_usage WHERE status = 'Borrowed'
            )
            ORDER BY t.name ASC
        """)
        rows = cursor.fetchall()
        return [{
            'id': row[0],
            'plate_number': row[1],
            'name': row[2],
            'vehicle_type': row[3],
            'description': row[4]
        } for row in rows]
    except Exception as e:
        print(f"Error getting available vehicles: {e}")
        return []


def get_borrowed_vehicles(db: DatabaseManager) -> list:
    """Get all currently borrowed vehicles"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT u.id, u.vehicle_id, t.plate_number, t.name, t.vehicle_type,
                   u.driver_id, u.driver_name, u.purpose, u.start_mileage,
                   u.borrowed_at, u.created_by
            FROM tbl_vehicle_usage u
            JOIN tbl_hotel_transportations t ON u.vehicle_id = t.id
            WHERE u.status = 'Borrowed'
            ORDER BY u.borrowed_at DESC
        """)
        rows = cursor.fetchall()
        return [{
            'id': row[0],
            'vehicle_id': row[1],
            'plate_number': row[2],
            'vehicle_name': row[3],
            'vehicle_type': row[4],
            'driver_id': row[5],
            'driver_name': row[6],
            'purpose': row[7],
            'start_mileage': row[8],
            'borrowed_at': row[9],
            'created_by': row[10]
        } for row in rows]
    except Exception as e:
        print(f"Error getting borrowed vehicles: {e}")
        return []


def get_vehicle_usage_by_id(db: DatabaseManager, usage_id: int) -> dict:
    """Get vehicle usage record by ID"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT u.id, u.vehicle_id, t.plate_number, t.name, t.vehicle_type,
                   u.driver_id, u.driver_name, u.purpose, u.start_mileage, u.end_mileage,
                   u.borrowed_at, u.returned_at, u.inspection_status, u.inspection_notes,
                   u.inspection_photo, u.status, u.created_by
            FROM tbl_vehicle_usage u
            JOIN tbl_hotel_transportations t ON u.vehicle_id = t.id
            WHERE u.id = %s
        """, (usage_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'vehicle_id': row[1],
                'plate_number': row[2],
                'vehicle_name': row[3],
                'vehicle_type': row[4],
                'driver_id': row[5],
                'driver_name': row[6],
                'purpose': row[7],
                'start_mileage': row[8],
                'end_mileage': row[9],
                'borrowed_at': row[10],
                'returned_at': row[11],
                'inspection_status': row[12],
                'inspection_notes': row[13],
                'inspection_photo': row[14],
                'status': row[15],
                'created_by': row[16]
            }
        return None
    except Exception as e:
        print(f"Error getting vehicle usage: {e}")
        return None


def create_vehicle_usage(db: DatabaseManager, vehicle_id: int, driver_id: int, driver_name: str, purpose: str, start_mileage: int, created_by: int) -> int:
    """Create new vehicle usage record (borrow vehicle)"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO tbl_vehicle_usage (vehicle_id, driver_id, driver_name, purpose, start_mileage, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (vehicle_id, driver_id, driver_name, purpose, start_mileage, created_by))
        result = cursor.fetchone()[0]
        db.connection.commit()
        return result
    except Exception as e:
        print(f"Error creating vehicle usage: {e}")
        return None


def return_vehicle(db: DatabaseManager, usage_id: int, end_mileage: int, inspection_status: str, inspection_notes: str, inspection_photo: str = None) -> bool:
    """Return vehicle and complete usage record"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            UPDATE tbl_vehicle_usage 
            SET status = 'Returned',
                returned_at = CURRENT_TIMESTAMP,
                end_mileage = %s,
                inspection_status = %s,
                inspection_notes = %s,
                inspection_photo = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (end_mileage, inspection_status, inspection_notes, inspection_photo, usage_id))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"Error returning vehicle: {e}")
        return False


def get_vehicle_usage_history(db: DatabaseManager, vehicle_id: int = None, limit: int = 20) -> list:
    """Get vehicle usage history"""
    try:
        cursor = db.connection.cursor()
        if vehicle_id:
            cursor.execute("""
                SELECT u.id, u.vehicle_id, t.plate_number, t.name, t.vehicle_type,
                       u.driver_name, u.purpose, u.start_mileage, u.end_mileage,
                       u.borrowed_at, u.returned_at, u.inspection_status, u.status
                FROM tbl_vehicle_usage u
                JOIN tbl_hotel_transportations t ON u.vehicle_id = t.id
                WHERE u.vehicle_id = %s
                ORDER BY u.borrowed_at DESC
                LIMIT %s
            """, (vehicle_id, limit))
        else:
            cursor.execute("""
                SELECT u.id, u.vehicle_id, t.plate_number, t.name, t.vehicle_type,
                       u.driver_name, u.purpose, u.start_mileage, u.end_mileage,
                       u.borrowed_at, u.returned_at, u.inspection_status, u.status
                FROM tbl_vehicle_usage u
                JOIN tbl_hotel_transportations t ON u.vehicle_id = t.id
                ORDER BY u.borrowed_at DESC
                LIMIT %s
            """, (limit,))
        rows = cursor.fetchall()
        return [{
            'id': row[0],
            'vehicle_id': row[1],
            'plate_number': row[2],
            'vehicle_name': row[3],
            'vehicle_type': row[4],
            'driver_name': row[5],
            'purpose': row[6],
            'start_mileage': row[7],
            'end_mileage': row[8],
            'borrowed_at': row[9],
            'returned_at': row[10],
            'inspection_status': row[11],
            'status': row[12]
        } for row in rows]
    except Exception as e:
        print(f"Error getting vehicle usage history: {e}")
        return []


def get_active_vehicle_usage_by_vehicle(db: DatabaseManager, vehicle_id: int) -> dict:
    """Get active usage record for a vehicle"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT u.id, u.vehicle_id, u.driver_id, u.driver_name, u.purpose,
                   u.start_mileage, u.borrowed_at, u.created_by
            FROM tbl_vehicle_usage u
            WHERE u.vehicle_id = %s AND u.status = 'Borrowed'
        """, (vehicle_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'vehicle_id': row[1],
                'driver_id': row[2],
                'driver_name': row[3],
                'purpose': row[4],
                'start_mileage': row[5],
                'borrowed_at': row[6],
                'created_by': row[7]
            }
        return None
    except Exception as e:
        print(f"Error getting active vehicle usage: {e}")
        return None


def get_active_vehicle_usage(db: DatabaseManager) -> list:
    """Get all active vehicle usage records"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT u.id, t.name, u.driver_name, u.purpose, u.start_mileage, u.borrowed_at
            FROM tbl_vehicle_usage u
            JOIN tbl_hotel_transportations t ON u.vehicle_id = t.id
            WHERE u.status = 'Borrowed'
            ORDER BY u.borrowed_at DESC
        """)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Error getting active vehicle usage: {e}")
        return []


def get_available_vehicles(db: DatabaseManager) -> list:
    """Get available vehicles (not currently borrowed)"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT t.id, t.name, t.vehicle_type, t.plate_number
            FROM tbl_hotel_transportations t
            WHERE t.state = 1
            AND t.id NOT IN (
                SELECT vehicle_id FROM tbl_vehicle_usage WHERE status = 'Borrowed'
            )
            ORDER BY t.name
        """)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Error getting available vehicles: {e}")
        return []


def complete_vehicle_usage(db: DatabaseManager, usage_id: int, end_mileage: int, inspection_status: str) -> bool:
    """Complete vehicle return"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            UPDATE tbl_vehicle_usage 
            SET status = 'Returned',
                returned_at = CURRENT_TIMESTAMP,
                end_mileage = %s,
                inspection_status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (end_mileage, inspection_status, usage_id))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"Error completing vehicle usage: {e}")
        return False


def get_vehicle_usage_records(db: DatabaseManager, limit: int = 20) -> list:
    """Get vehicle usage records for history display"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT u.id, t.name, u.driver_name, u.purpose, u.start_mileage, u.end_mileage,
                   u.status, u.borrowed_at, u.returned_at
            FROM tbl_vehicle_usage u
            JOIN tbl_hotel_transportations t ON u.vehicle_id = t.id
            ORDER BY u.borrowed_at DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Error getting vehicle usage records: {e}")
        return []


# ==================== Reception Shift Management ====================

def get_shift_settings(db: DatabaseManager) -> dict:
    """Get current shift settings"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM tbl_reception_shift WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'shift_count': row[1],
                'shift_1_start': row[2],
                'shift_1_end': row[3],
                'shift_2_start': row[4],
                'shift_2_end': row[5],
                'shift_3_start': row[6],
                'shift_3_end': row[7],
                'shift_4_start': row[8],
                'shift_4_end': row[9],
                'is_active': row[10]
            }
        return None
    except Exception as e:
        print(f"Error getting shift settings: {e}")
        return None


def save_shift_settings(db: DatabaseManager, shift_count: int, shifts: list) -> bool:
    """Save shift settings by updating existing active record
    shifts: list of tuples [(start1, end1), (start2, end2)]
    
    Automatically calculates 24-hour coverage:
    - Only accepts 3 shifts (A, B, C)
    - Admin provides: shift_1_start, shift_2_start, shift_3_start
    - Automatically calculates end times to ensure 24-hour coverage
    """
    try:
        cursor = db.connection.cursor()
        
        # Force 3-shift configuration
        if shift_count != 3 or len(shifts) != 3:
            print("❌ Error: Only 3-shift configuration is supported")
            return False
        
        # Check if there's an active record
        cursor.execute("SELECT id FROM tbl_reception_shift WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
        active_record = cursor.fetchone()
        
        # Auto-calculate 24-hour coverage
        # Admin provides start times, we calculate end times automatically
        shift_1_start = shifts[0][0]  # e.g., "08:00"
        shift_2_start = shifts[1][0]  # e.g., "16:00"
        shift_3_start = shifts[2][0]  # e.g., "00:00" or "24:00"
        
        # Shift 1 ends when Shift 2 starts
        shift_1_end = shift_2_start
        
        # Shift 2 ends when Shift 3 starts
        shift_2_end = shift_3_start
        
        # Shift 3 ends when Shift 1 starts (next day)
        shift_3_end = shift_1_start
        
        # Not used for 3-shift configuration
        shift_4_start = None
        shift_4_end = None
        
        if active_record:
            # Update existing active record
            record_id = active_record[0]
            cursor.execute("""
                UPDATE tbl_reception_shift 
                SET shift_count = %s,
                    shift_1_start = %s, shift_1_end = %s,
                    shift_2_start = %s, shift_2_end = %s,
                    shift_3_start = %s, shift_3_end = %s,
                    shift_4_start = %s, shift_4_end = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (shift_count, shift_1_start, shift_1_end, shift_2_start, shift_2_end,
                  shift_3_start, shift_3_end, shift_4_start, shift_4_end, record_id))
            print(f"✅ Updated existing shift settings (ID: {record_id})")
        else:
            # No active record exists, insert new one
            cursor.execute("""
                INSERT INTO tbl_reception_shift 
                (shift_count, shift_1_start, shift_1_end, shift_2_start, shift_2_end,
                 shift_3_start, shift_3_end, shift_4_start, shift_4_end, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, (shift_count, shift_1_start, shift_1_end, shift_2_start, shift_2_end,
                  shift_3_start, shift_3_end, shift_4_start, shift_4_end))
            print(f"✅ Created new shift settings record")
        
        db.connection.commit()
        return True
    except Exception as e:
        print(f"Error saving shift settings: {e}")
        db.connection.rollback()
        return False


def get_default_shifts(shift_count: int) -> list:
    """Get default shift start times for 3-shift configuration
    Returns list of (start_time, None) tuples - end times are auto-calculated
    """
    if shift_count == 3:
        # Return only start times, end times will be auto-calculated
        return [('08:00', None), ('16:00', None), ('00:00', None)]
    return [('08:00', None), ('16:00', None), ('00:00', None)]


def create_shift_report(db: DatabaseManager, shift_number: int, employee_id: str, employee_name: str,
                        reservations_count: int = 0, arrivals_count: int = 0, departures_count: int = 0,
                        issues_notes: str = None, cash_amount: float = 0, cash_photo: str = None,
                        pos_report_photo: str = None, store_stock_notes: str = None,
                        restaurant_cash_confirmed: bool = False, key_log_notes: str = None,
                        tool_log_notes: str = None, additional_notes: str = None) -> int:
    """Create a new shift report"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO tbl_shift_reports 
            (shift_number, employee_id, employee_name, reservations_count, arrivals_count,
             departures_count, issues_notes, cash_amount, cash_photo, pos_report_photo,
             store_stock_notes, restaurant_cash_confirmed, key_log_notes, tool_log_notes,
             additional_notes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'submitted')
            RETURNING id
        """, (shift_number, employee_id, employee_name, reservations_count, arrivals_count,
              departures_count, issues_notes, cash_amount, cash_photo, pos_report_photo,
              store_stock_notes, 1 if restaurant_cash_confirmed else 0, key_log_notes,
              tool_log_notes, additional_notes))
        result = cursor.fetchone()[0]
        db.connection.commit()
        return result
    except Exception as e:
        print(f"Error creating shift report: {e}")
        if db.connection:
            db.connection.rollback()
        return None


def get_shift_reports(db: DatabaseManager, date: str = None, limit: int = 20) -> list:
    """Get shift reports, optionally filtered by date"""
    try:
        cursor = db.connection.cursor()
        if date:
            cursor.execute("""
                SELECT * FROM tbl_shift_reports 
                WHERE shift_date = %s
                ORDER BY shift_number, submitted_at DESC
            """, (date,))
        else:
            cursor.execute("""
                SELECT * FROM tbl_shift_reports 
                ORDER BY shift_date DESC, shift_number
                LIMIT %s
            """, (limit,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting shift reports: {e}")
        return []


def get_shift_reports_by_date(db: DatabaseManager, date: str) -> list:
    """Get all shift reports for a specific date, with full details"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT 
                id, shift_number, shift_date, employee_id, employee_name,
                reservations_count, arrivals_count, departures_count,
                issues_notes, cash_amount, cash_photo, pos_report_photo,
                store_stock_notes, restaurant_cash_confirmed,
                key_log_notes, tool_log_notes, additional_notes,
                status, submitted_at, confirmed_by, confirmed_at
            FROM tbl_shift_reports 
            WHERE shift_date = %s
            ORDER BY submitted_at ASC
        """, (date,))
        
        rows = cursor.fetchall()
        reports = []
        
        for row in rows:
            reports.append({
                'id': row[0],
                'shift_number': row[1],
                'shift_date': row[2],
                'employee_id': row[3],
                'employee_name': row[4],
                'reservations_count': row[5],
                'arrivals_count': row[6],
                'departures_count': row[7],
                'issues_notes': row[8],
                'cash_amount': row[9],
                'cash_photo': row[10],
                'pos_report_photo': row[11],
                'store_stock_notes': row[12],
                'restaurant_cash_confirmed': row[13],
                'key_log_notes': row[14],
                'tool_log_notes': row[15],
                'additional_notes': row[16],
                'status': row[17],
                'submitted_at': row[18],
                'confirmed_by': row[19],
                'confirmed_at': row[20]
            })
        
        return reports
    except Exception as e:
        print(f"Error getting shift reports by date: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_shift_report_by_id(db: DatabaseManager, report_id: int) -> dict:
    """Get a specific shift report by ID"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM tbl_shift_reports WHERE id = %s", (report_id,))
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"Error getting shift report: {e}")
        return None


def get_pending_shift_reports(db: DatabaseManager) -> list:
    """Get shift reports that are submitted but not confirmed"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT * FROM tbl_shift_reports 
            WHERE status = 'submitted'
            ORDER BY submitted_at DESC
        """)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"Error getting pending shift reports: {e}")
        return []


def confirm_shift_report(db: DatabaseManager, report_id: int, confirmed_by: int) -> bool:
    """Confirm a shift report"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            UPDATE tbl_shift_reports 
            SET status = 'confirmed', confirmed_by = %s, confirmed_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (confirmed_by, report_id))
        db.connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error confirming shift report: {e}")
        return False


# ===== EVENT MANAGEMENT FUNCTIONS =====

def create_event(db: DatabaseManager, event_data: dict) -> int:
    """
    Create a new hotel event
    
    Args:
        db: DatabaseManager instance
        event_data: Dict with event_name, hall, event_date, event_time, end_time, seats, price, menu, meals_count, notes, created_by
    
    Returns:
        Event ID or None on failure
    """
    try:
        db.cursor.execute("""
            INSERT INTO tbl_hotel_events (
                event_name, hall, event_date, event_time, end_time, 
                seats, price, menu, meals_count, notes, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            event_data.get('event_name'),
            event_data.get('hall'),
            event_data.get('event_date'),
            event_data.get('event_time'),
            event_data.get('end_time'),
            event_data.get('seats', 0),
            event_data.get('price', 0),
            event_data.get('menu'),
            event_data.get('meals_count', 0),
            event_data.get('notes'),
            event_data.get('created_by')
        ))
        event_id = db.cursor.fetchone()[0]
        db.connection.commit()
        print(f"✅ Event created: ID {event_id}")
        return event_id
    except Exception as e:
        print(f"❌ Error creating event: {e}")
        return None


def get_all_events(db: DatabaseManager, status: str = None) -> list:
    """Get all events, optionally filtered by status"""
    try:
        if status:
            results = db.cursor.execute("""
                SELECT id, event_name, hall, event_date, event_time, end_time,
                       seats, price, menu, meals_count, notes, status, created_by, created_at
                FROM tbl_hotel_events WHERE status = %s ORDER BY event_date, event_time
            """, (status,))
            results = db.cursor.fetchall()
        else:
            results = db.cursor.execute("""
                SELECT id, event_name, hall, event_date, event_time, end_time,
                       seats, price, menu, meals_count, notes, status, created_by, created_at
                FROM tbl_hotel_events ORDER BY event_date, event_time
            """)
            results = db.cursor.fetchall()
        return results
    except Exception as e:
        print(f"❌ Error getting events: {e}")
        return []


def get_event_by_id(db: DatabaseManager, event_id: int) -> dict:
    """Get event details by ID"""
    try:
        db.cursor.execute("""
            SELECT id, event_name, hall, event_date, event_time, end_time,
                   seats, price, menu, meals_count, notes, status, created_by, created_at
            FROM tbl_hotel_events WHERE id = %s
        """, (event_id,))

        result = db.cursor.fetchone()
        
        if result:
            return {
                'id': result[0],
                'event_name': result[1],
                'hall': result[2],
                'event_date': result[3],
                'event_time': result[4],
                'end_time': result[5],
                'seats': result[6],
                'price': result[7],
                'menu': result[8],
                'meals_count': result[9],
                'notes': result[10],
                'status': result[11],
                'created_by': result[12],
                'created_at': result[13]
            }
        return None
    except Exception as e:
        print(f"❌ Error getting event: {e}")
        return None


def update_event_status(db: DatabaseManager, event_id: int, status: str) -> bool:
    """Update event status"""
    try:
        db.cursor.execute("""
            UPDATE tbl_hotel_events SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s
        """, (status, event_id))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating event status: {e}")
        return False


def get_upcoming_events(db: DatabaseManager, days: int = 7) -> list:
    """Get events within next N days (and recent past events still in progress)"""
    try:
        results = db.cursor.execute("""
            SELECT id, event_name, hall, event_date, event_time, end_time,
                   seats, price, menu, meals_count, notes, status, created_by, created_at
            FROM tbl_hotel_events 
            WHERE (event_date >= CURRENT_DATE - 7 AND event_date <= CURRENT_DATE + %s)
            AND status NOT IN ('completed', 'cancelled')
            ORDER BY event_date DESC, event_time
        """, (days,))
        results = db.cursor.fetchall()
        return results
    except Exception as e:
        print(f"❌ Error getting upcoming events: {e}")
        return []



def create_event_history(db: DatabaseManager, event_id: int, department: str, alarm_type: str) -> int:
    """Create event history record for alarm tracking"""
    try:
        db.cursor.execute("""
            INSERT INTO tbl_hotel_event_history (event_id, department, alarm_type, alarm_sent_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
        """, (event_id, department, alarm_type))
        result = db.cursor.fetchone()[0]
        db.connection.commit()
        return result
    except Exception as e:
        print(f"❌ Error creating event history: {e}")
        return None


def get_event_history(db: DatabaseManager, event_id: int) -> list:
    """Get event history (all department confirmations)"""
    try:
        results = db.cursor.execute("""
            SELECT id, event_id, department, alarm_type, alarm_sent_at,
                   acknowledged, acknowledged_by, acknowledged_at,
                   confirmed, confirmed_by, confirmed_at,
                   ready_confirmed, ready_confirmed_by, ready_confirmed_at, ready_proof, notes
            FROM tbl_hotel_event_history WHERE event_id = %s ORDER BY created_at DESC
        """, (event_id,))
        results = db.cursor.fetchall()
        return results
    except Exception as e:
        print(f"❌ Error getting event history: {e}")
        return []


def acknowledge_event_alarm(db: DatabaseManager, history_id: int, telegram_user_id: int) -> bool:
    """Acknowledge event alarm"""
    try:
        db.cursor.execute("""
            UPDATE tbl_hotel_event_history 
            SET acknowledged = 1, acknowledged_by = %s, acknowledged_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (telegram_user_id, history_id))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error acknowledging event alarm: {e}")
        return False


def confirm_event_preparation(db: DatabaseManager, history_id: int, telegram_user_id: int, notes: str = None) -> bool:
    """Confirm event preparation (T-1 day confirmation)"""
    try:
        db.cursor.execute("""
            UPDATE tbl_hotel_event_history 
            SET confirmed = 1, confirmed_by = %s, confirmed_at = CURRENT_TIMESTAMP, notes = %s
            WHERE id = %s
        """, (telegram_user_id, notes, history_id))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error confirming event preparation: {e}")
        return False


def confirm_event_ready(db: DatabaseManager, history_id: int, telegram_user_id: int, proof: str = None) -> bool:
    """Confirm READY status with proof (event day)"""
    try:
        db.cursor.execute("""
            UPDATE tbl_hotel_event_history 
            SET ready_confirmed = 1, ready_confirmed_by = %s, ready_confirmed_at = CURRENT_TIMESTAMP, ready_proof = %s
            WHERE id = %s
        """, (telegram_user_id, proof, history_id))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error confirming event ready: {e}")
        return False


def get_events_for_alarm(db: DatabaseManager, days_before: int) -> list:
    """Get events that need alarm (T-2 or T-1)"""
    try:
        db.cursor.execute("""
            SELECT id, event_name, hall, event_date, event_time, seats, menu, meals_count
            FROM tbl_hotel_events 
            WHERE event_date = CURRENT_DATE + INTERVAL '%s days'
            AND status NOT IN ('completed', 'cancelled')
        """, (days_before,))
        results = db.cursor.fetchall()
        return results
    except Exception as e:
        print(f"❌ Error getting events for alarm: {e}")
        if db.connection:
            db.connection.rollback()
        return []



def get_todays_events(db: DatabaseManager) -> list:
    """Get today's events"""
    try:
        db.cursor.execute("""
            SELECT id, event_name, hall, event_date, event_time, end_time, seats, menu, meals_count, status
            FROM tbl_hotel_events 
            WHERE event_date = CURRENT_DATE
            AND status NOT IN ('completed', 'cancelled')
            ORDER BY event_time
        """)
        results = db.cursor.fetchall()
        return results
    except Exception as e:
        print(f"❌ Error getting today's events: {e}")
        return []


def get_unconfirmed_event_history(db: DatabaseManager, event_id: int, alarm_type: str) -> list:
    """Get unconfirmed departments for an event alarm"""
    try:
        if alarm_type == 'T-2':
            results = db.cursor.execute("""
                SELECT id, department FROM tbl_hotel_event_history 
                WHERE event_id = %s AND alarm_type = %s AND acknowledged = 0
            """, (event_id, alarm_type))
            results = db.cursor.fetchall()
        elif alarm_type == 'T-1':
            results = db.cursor.execute("""
                SELECT id, department FROM tbl_hotel_event_history 
                WHERE event_id = %s AND alarm_type = %s AND confirmed = 0
            """, (event_id, alarm_type))
            results = db.cursor.fetchall()
        else:  # event_day
            results = db.cursor.execute("""
                SELECT id, department FROM tbl_hotel_event_history 
                WHERE event_id = %s AND alarm_type = %s AND ready_confirmed = 0
            """, (event_id, alarm_type))
            results = db.cursor.fetchall()
        return results
    except Exception as e:
        print(f"❌ Error getting unconfirmed event history: {e}")
        return []


def get_alarm_last_sent(db: DatabaseManager, event_id: int, alarm_type: str, department: str) -> str:
    """Get the last alarm sent time for a specific event/department/alarm_type"""
    try:
        db.cursor.execute("""
            SELECT alarm_sent_at FROM tbl_hotel_event_history 
            WHERE event_id = %s AND alarm_type = %s AND department = %s
        """, (event_id, alarm_type, department))

        result = db.cursor.fetchone()
        return result[0] if result and result[0] else None
    except Exception as e:
        print(f"❌ Error getting alarm last sent: {e}")
        return None


def update_alarm_sent_time(db: DatabaseManager, event_id: int, alarm_type: str, department: str) -> bool:
    """Update the alarm sent time to current timestamp"""
    try:
        db.cursor.execute("""
            UPDATE tbl_hotel_event_history 
            SET alarm_sent_at = CURRENT_TIMESTAMP
            WHERE event_id = %s AND alarm_type = %s AND department = %s
        """, (event_id, alarm_type, department))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating alarm sent time: {e}")
        return False


def should_send_alarm(db: DatabaseManager, event_id: int, alarm_type: str, department: str, interval_seconds: int) -> bool:
    """Check if alarm should be sent based on last sent time and interval"""
    try:
        db.cursor.execute("""
            SELECT alarm_sent_at FROM tbl_hotel_event_history 
            WHERE event_id = %s AND alarm_type = %s AND department = %s
        """, (event_id, alarm_type, department))

        result = db.cursor.fetchone()
        
        if not result or not result[0]:
            return True  # Never sent, should send
        
        # Check if interval has passed
        from datetime import datetime
        last_sent_raw = result[0]
        
        # Handle both string and datetime object
        if isinstance(last_sent_raw, datetime):
            last_sent = last_sent_raw
        else:
            last_sent = datetime.strptime(last_sent_raw, '%Y-%m-%d %H:%M:%S')
        
        now = datetime.now()
        elapsed = (now - last_sent).total_seconds()
        
        return elapsed >= interval_seconds
    except Exception as e:
        print(f"❌ Error checking should_send_alarm: {e}")
        return True  # Send on error to be safe


def create_event_task(db: DatabaseManager, event_id: int, task_id: int, department: str, 
                      task_type: str, description: str, due_date: str,
                      assigned_to: int = None, assigned_name: str = None) -> int:
    """Create an event-related task record with assignment info"""
    try:
        db.cursor.execute("""
            INSERT INTO tbl_hotel_event_tasks 
            (event_id, task_id, department, task_type, description, due_date, assigned_to, assigned_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (event_id, task_id, department, task_type, description, due_date, assigned_to, assigned_name))
        result = db.cursor.fetchone()[0]
        db.connection.commit()
        return result
    except Exception as e:
        print(f"❌ Error creating event task: {e}")
        return None


def accept_event_task(db: DatabaseManager, event_task_id: int, accepted_by: int) -> bool:
    """Mark event task as accepted"""
    try:
        db.cursor.execute("""
            UPDATE tbl_hotel_event_tasks 
            SET status = 'accepted', accepted_at = CURRENT_TIMESTAMP, accepted_by = %s
            WHERE id = %s
        """, (accepted_by, event_task_id))
        db.connection.commit()
        print(f"✅ Event task {event_task_id} accepted by {accepted_by}")
        return True
    except Exception as e:
        print(f"❌ Error accepting event task: {e}")
        return False


def start_event_task(db: DatabaseManager, event_task_id: int) -> bool:
    """Mark event task as in progress"""
    try:
        db.cursor.execute("""
            UPDATE tbl_hotel_event_tasks 
            SET status = 'in_progress', started_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (event_task_id,))
        db.connection.commit()
        print(f"✅ Event task {event_task_id} started")
        return True
    except Exception as e:
        print(f"❌ Error starting event task: {e}")
        return False


def complete_event_task(db: DatabaseManager, event_task_id: int, completed_by: int, 
                        proof_photo: str = None, report_notes: str = None) -> bool:
    """Mark event task as completed with optional proof"""
    try:
        db.cursor.execute("""
            UPDATE tbl_hotel_event_tasks 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP, completed_by = %s,
                proof_photo = %s, report_notes = %s
            WHERE id = %s
        """, (completed_by, proof_photo, report_notes, event_task_id))
        db.connection.commit()
        print(f"✅ Event task {event_task_id} completed by {completed_by}")
        return True
    except Exception as e:
        print(f"❌ Error completing event task: {e}")
        return False


def get_event_task_by_id(db: DatabaseManager, event_task_id: int) -> dict:
    """Get event task details by ID"""
    try:
        db.cursor.execute("""
            SELECT id, event_id, task_id, department, task_type, description, due_date,
                   assigned_to, assigned_name, status, accepted_at, accepted_by,
                   started_at, completed_at, completed_by, proof_photo, report_notes, 
                   created_at, confirmed_at, confirmed_by
            FROM tbl_hotel_event_tasks WHERE id = %s
        """, (event_task_id,))

        result = db.cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'event_id': result[1],
                'task_id': result[2],
                'department': result[3],
                'task_type': result[4],
                'description': result[5],
                'due_date': result[6],
                'assigned_to': result[7],
                'assigned_name': result[8],
                'status': result[9],
                'accepted_at': result[10],
                'accepted_by': result[11],
                'started_at': result[12],
                'completed_at': result[13],
                'completed_by': result[14],
                'proof_photo': result[15],
                'report_notes': result[16],
                'created_at': result[17],
                'confirmed_at': result[18],
                'confirmed_by': result[19]
            }
        return None
    except Exception as e:
        print(f"❌ Error getting event task: {e}")
        return None


def get_event_task_by_task_id(db: DatabaseManager, task_id: int) -> dict:
    """Get event task by linked task_id"""
    try:
        db.cursor.execute("""
            SELECT id, event_id, task_id, department, task_type, description, due_date,
                   assigned_to, assigned_name, status, accepted_at, accepted_by,
                   started_at, completed_at, completed_by, proof_photo, report_notes, created_at
            FROM tbl_hotel_event_tasks WHERE task_id = %s
        """, (task_id,))

        result = db.cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'event_id': result[1],
                'task_id': result[2],
                'department': result[3],
                'task_type': result[4],
                'description': result[5],
                'due_date': result[6],
                'assigned_to': result[7],
                'assigned_name': result[8],
                'status': result[9],
                'accepted_at': result[10],
                'accepted_by': result[11],
                'started_at': result[12],
                'completed_at': result[13],
                'completed_by': result[14],
                'proof_photo': result[15],
                'report_notes': result[16],
                'created_at': result[17]
            }
        return None
    except Exception as e:
        print(f"❌ Error getting event task by task_id: {e}")
        return None


def update_event_task_status_from_task(db: DatabaseManager, task_id: int, new_status: str, 
                                       by_user: int = None, proof: str = None, notes: str = None) -> bool:
    """Update event task status when linked task status changes"""
    try:
        event_task = get_event_task_by_task_id(db, task_id)
        if not event_task:
            return False
        
        event_task_id = event_task['id']
        
        if new_status == 'accepted':
            return accept_event_task(db, event_task_id, by_user)
        elif new_status == 'in_progress':
            return start_event_task(db, event_task_id)
        elif new_status == 'completed':
            return complete_event_task(db, event_task_id, by_user, proof, notes)
        return False
    except Exception as e:
        print(f"❌ Error updating event task from task: {e}")
        return False


def get_event_tasks(db: DatabaseManager, event_id: int) -> list:
    """Get all tasks for an event with full status info"""
    try:
        results = db.cursor.execute("""
            SELECT et.id, et.event_id, et.task_id, et.department, et.task_type, 
                   et.description, et.due_date, et.assigned_to, et.assigned_name,
                   et.status, et.accepted_at, et.accepted_by, et.started_at,
                   et.completed_at, et.completed_by, et.proof_photo, et.report_notes,
                   et.created_at, t.is_perform, t.task_status
            FROM tbl_hotel_event_tasks et
            LEFT JOIN tbl_tasks t ON et.task_id = t.id
            WHERE et.event_id = %s
            ORDER BY et.due_date, et.department
        """, (event_id,))
        results = db.cursor.fetchall()
        
        # Convert to list of dicts for easier use
        tasks = []
        for r in results:
            tasks.append({
                'id': r[0],
                'event_id': r[1],
                'task_id': r[2],
                'department': r[3],
                'task_type': r[4],
                'description': r[5],
                'due_date': r[6],
                'assigned_to': r[7],
                'assigned_name': r[8],
                'status': r[9],
                'accepted_at': r[10],
                'accepted_by': r[11],
                'started_at': r[12],
                'completed_at': r[13],
                'completed_by': r[14],
                'proof_photo': r[15],
                'report_notes': r[16],
                'created_at': r[17],
                'is_perform': r[18],
                'task_status': r[19]
            })
        return tasks
    except Exception as e:
        print(f"❌ Error getting event tasks: {e}")
        return []


def get_current_shift(db: DatabaseManager) -> int:
    """Get current shift number based on time"""
    from datetime import datetime
    try:
        settings = get_shift_settings(db)
        if not settings:
            return 1
        
        current_time = datetime.now().strftime('%H:%M')
        shift_count = settings['shift_count']
        
        for i in range(1, shift_count + 1):
            start = settings.get(f'shift_{i}_start')
            end = settings.get(f'shift_{i}_end')
            if start and end:
                # Handle overnight shifts (e.g., 21:00 - 05:00)
                if start > end:
                    if current_time >= start or current_time < end:
                        return i
                else:
                    if start <= current_time < end:
                        return i
        return 1
    except Exception as e:
        print(f"Error getting current shift: {e}")
        return 1


# ==================== PERFORMANCE ANALYSIS FUNCTIONS ====================

def get_employee_performance(db: DatabaseManager, employee_id: int = None, days: int = 7) -> list:
    """
    Get employee performance statistics
    
    Args:
        db: DatabaseManager instance
        employee_id: Specific employee ID (None for all employees)
        days: Number of days to analyze
        
    Returns:
        List of employee performance data
    """
    from datetime import datetime, timedelta
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        if employee_id:
            query = """
                SELECT 
                    e.id as employee_id,
                    e.name,
                    e.department,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.is_perform = 1 THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.is_perform = 1 AND t.task_completed_at <= t.due_date THEN 1 ELSE 0 END) as on_time_tasks,
                    SUM(CASE WHEN t.is_perform = 0 AND t.due_date < CURRENT_DATE THEN 1 ELSE 0 END) as overdue_tasks,
                    SUM(CASE WHEN t.proof_path != '' AND t.proof_path IS NOT NULL THEN 1 ELSE 0 END) as with_proof,
                    AVG(CASE 
                        WHEN t.task_completed_at IS NOT NULL AND t.task_started_at IS NOT NULL 
                        THEN (julianday(t.task_completed_at) - julianday(t.task_started_at)) * 24 * 60 
                        ELSE NULL 
                    END) as avg_completion_minutes,
                    AVG(CASE 
                        WHEN t.notification_read_at IS NOT NULL AND t.notification_sent_at IS NOT NULL 
                        THEN (julianday(t.notification_read_at) - julianday(t.notification_sent_at)) * 24 * 60 
                        ELSE NULL 
                    END) as avg_response_minutes
                FROM tbl_employee e
                LEFT JOIN tbl_tasks t ON e.id = t.assignee_id AND t.Date >= %s
                WHERE e.id = %s
                GROUP BY e.id
            """
            db.cursor.execute(query, (start_date, employee_id))
            result = db.cursor.fetchall()
        else:
            query = """
                SELECT 
                    e.id as employee_id,
                    e.name,
                    e.department,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.is_perform = 1 THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.is_perform = 1 AND t.task_completed_at <= t.due_date THEN 1 ELSE 0 END) as on_time_tasks,
                    SUM(CASE WHEN t.is_perform = 0 AND t.due_date < CURRENT_DATE THEN 1 ELSE 0 END) as overdue_tasks,
                    SUM(CASE WHEN t.proof_path != '' AND t.proof_path IS NOT NULL THEN 1 ELSE 0 END) as with_proof,
                    AVG(CASE 
                        WHEN t.task_completed_at IS NOT NULL AND t.task_started_at IS NOT NULL 
                        THEN (julianday(t.task_completed_at) - julianday(t.task_started_at)) * 24 * 60 
                        ELSE NULL 
                    END) as avg_completion_minutes,
                    AVG(CASE 
                        WHEN t.notification_read_at IS NOT NULL AND t.notification_sent_at IS NOT NULL 
                        THEN (julianday(t.notification_read_at) - julianday(t.notification_sent_at)) * 24 * 60 
                        ELSE NULL 
                    END) as avg_response_minutes
                FROM tbl_employee e
                LEFT JOIN tbl_tasks t ON e.id = t.assignee_id AND t.Date >= %s
                WHERE e.department != 'Management'
                GROUP BY e.id
                HAVING total_tasks > 0
                ORDER BY completed_tasks DESC
            """
            db.cursor.execute(query, (start_date,))
            result = db.cursor.fetchall()
        
        employees = []
        for r in result:
            total = r[3] or 0
            completed = r[4] or 0
            on_time = r[5] or 0
            completion_rate = (completed / total * 100) if total > 0 else 0
            on_time_rate = (on_time / completed * 100) if completed > 0 else 0
            
            employees.append({
                'employee_id': r[0],
                'name': r[1],
                'department': r[2],
                'total_tasks': total,
                'completed_tasks': completed,
                'on_time_tasks': on_time,
                'overdue_tasks': r[6] or 0,
                'with_proof': r[7] or 0,
                'completion_rate': round(completion_rate, 1),
                'on_time_rate': round(on_time_rate, 1),
                'avg_completion_minutes': round(r[8], 1) if r[8] else 0,
                'avg_response_minutes': round(r[9], 1) if r[9] else 0
            })
        
        return employees
    except Exception as e:
        print(f"❌ Error getting employee performance: {e}")
        return []


def get_department_performance(db: DatabaseManager, department: str = None, days: int = 7) -> list:
    """
    Get department performance statistics
    
    Args:
        db: DatabaseManager instance
        department: Specific department (None for all departments)
        days: Number of days to analyze
        
    Returns:
        List of department performance data
    """
    from datetime import datetime, timedelta
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        if department:
            query = """
                SELECT 
                    t.department,
                    COUNT(DISTINCT e.id) as employee_count,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.is_perform = 1 THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.is_perform = 1 AND t.task_completed_at <= t.due_date THEN 1 ELSE 0 END) as on_time_tasks,
                    SUM(CASE WHEN t.is_perform = 0 AND t.due_date < CURRENT_DATE THEN 1 ELSE 0 END) as overdue_tasks,
                    SUM(CASE WHEN t.priority = 'High' OR t.priority = 'Urgent' THEN 1 ELSE 0 END) as high_priority_tasks,
                    AVG(CASE 
                        WHEN t.task_completed_at IS NOT NULL AND t.task_started_at IS NOT NULL 
                        THEN (julianday(t.task_completed_at) - julianday(t.task_started_at)) * 24 * 60 
                        ELSE NULL 
                    END) as avg_completion_minutes
                FROM tbl_tasks t
                LEFT JOIN tbl_employee e ON t.assignee_id = e.id
                WHERE t.Date >= %s AND t.department = %s
                GROUP BY t.department
            """
            db.cursor.execute(query, (start_date, department))
            result = db.cursor.fetchall()
        else:
            query = """
                SELECT 
                    t.department,
                    COUNT(DISTINCT e.id) as employee_count,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.is_perform = 1 THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.is_perform = 1 AND t.task_completed_at <= t.due_date THEN 1 ELSE 0 END) as on_time_tasks,
                    SUM(CASE WHEN t.is_perform = 0 AND t.due_date < CURRENT_DATE THEN 1 ELSE 0 END) as overdue_tasks,
                    SUM(CASE WHEN t.priority = 'High' OR t.priority = 'Urgent' THEN 1 ELSE 0 END) as high_priority_tasks,
                    AVG(CASE 
                        WHEN t.task_completed_at IS NOT NULL AND t.task_started_at IS NOT NULL 
                        THEN (julianday(t.task_completed_at) - julianday(t.task_started_at)) * 24 * 60 
                        ELSE NULL 
                    END) as avg_completion_minutes
                FROM tbl_tasks t
                LEFT JOIN tbl_employee e ON t.assignee_id = e.id
                WHERE t.Date >= %s AND t.department IS NOT NULL AND t.department != ''
                GROUP BY t.department
                ORDER BY completed_tasks DESC
            """
            db.cursor.execute(query, (start_date,))
            result = db.cursor.fetchall()
        
        departments = []
        for r in result:
            total = r[2] or 0
            completed = r[3] or 0
            on_time = r[4] or 0
            completion_rate = (completed / total * 100) if total > 0 else 0
            on_time_rate = (on_time / completed * 100) if completed > 0 else 0
            
            departments.append({
                'department': r[0],
                'employee_count': r[1] or 0,
                'total_tasks': total,
                'completed_tasks': completed,
                'on_time_tasks': on_time,
                'overdue_tasks': r[5] or 0,
                'high_priority_tasks': r[6] or 0,
                'completion_rate': round(completion_rate, 1),
                'on_time_rate': round(on_time_rate, 1),
                'avg_completion_minutes': round(r[7], 1) if r[7] else 0
            })
        
        # Sort by completion rate for ranking
        departments.sort(key=lambda x: x['completion_rate'], reverse=True)
        for i, dept in enumerate(departments):
            dept['rank'] = i + 1
        
        return departments
    except Exception as e:
        print(f"❌ Error getting department performance: {e}")
        return []


def get_performance_ranking(db: DatabaseManager, days: int = 7, limit: int = 10) -> dict:
    """
    Get performance ranking for employees and departments
    
    Args:
        db: DatabaseManager instance
        days: Number of days to analyze
        limit: Maximum number of results per category
        
    Returns:
        Dictionary with top performers, departments ranking, and concerns
    """
    try:
        employees = get_employee_performance(db, days=days)
        departments = get_department_performance(db, days=days)
        
        # Sort employees by completion rate
        employees_sorted = sorted(employees, key=lambda x: (x['completion_rate'], x['completed_tasks']), reverse=True)
        
        # Top performers (completion rate >= 80% and at least 3 tasks)
        top_performers = [e for e in employees_sorted if e['completion_rate'] >= 80 and e['total_tasks'] >= 3][:limit]
        
        # Employees needing attention (completion rate < 60% or high overdue)
        concerns = [e for e in employees_sorted if e['completion_rate'] < 60 or e['overdue_tasks'] >= 3][:limit]
        
        # Calculate overall statistics
        total_tasks = sum(e['total_tasks'] for e in employees)
        total_completed = sum(e['completed_tasks'] for e in employees)
        total_overdue = sum(e['overdue_tasks'] for e in employees)
        overall_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'period_days': days,
            'total_employees': len(employees),
            'total_departments': len(departments),
            'overall_stats': {
                'total_tasks': total_tasks,
                'completed_tasks': total_completed,
                'overdue_tasks': total_overdue,
                'completion_rate': round(overall_rate, 1)
            },
            'top_performers': top_performers,
            'concerns': concerns,
            'department_ranking': departments
        }
    except Exception as e:
        print(f"❌ Error getting performance ranking: {e}")
        return {}


# ==================== ACTION HISTORY FUNCTIONS ====================
# Audit logs are persisted in PostgreSQL as append-only records
# Records: who did what, when, on which entity, including before/after state

import json as _json

def create_action_history_table(db):
    """Create action history table with extended audit fields"""
    try:
        cursor = db.cursor
        
        # Create table with extended fields for audit logging
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_action_history (
                id SERIAL PRIMARY KEY,
                telegram_user_id BIGINT NOT NULL,
                employee_id TEXT,
                employee_name TEXT NOT NULL,
                department TEXT,
                action_type TEXT NOT NULL,
                action_detail JSONB,
                entity_type TEXT,
                entity_id TEXT,
                before_state JSONB,
                after_state JSONB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add new columns if they don't exist (for migration)
        migration_columns = [
            ("entity_type", "TEXT"),
            ("entity_id", "TEXT"),
            ("before_state", "JSONB"),
            ("after_state", "JSONB")
        ]
        
        for col_name, col_type in migration_columns:
            try:
                cursor.execute(f"""
                    ALTER TABLE tbl_action_history 
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                """)
            except Exception:
                pass
        
        # Convert action_detail to JSONB if it's TEXT
        try:
            cursor.execute("""
                ALTER TABLE tbl_action_history 
                ALTER COLUMN action_detail TYPE JSONB USING 
                    CASE 
                        WHEN action_detail IS NULL THEN NULL
                        WHEN action_detail = '' THEN NULL
                        ELSE to_jsonb(action_detail)
                    END
            """)
        except Exception:
            pass  # Already JSONB or conversion not needed
        
        # Create index for efficient querying
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_action_history_timestamp 
            ON tbl_action_history(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_action_history_entity 
            ON tbl_action_history(entity_type, entity_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_action_history_user 
            ON tbl_action_history(telegram_user_id)
        """)
        
        db.connection.commit()
        print("✅ Action history table ready (with audit fields)")
        return True
    except Exception as e:
        print(f"❌ Error creating action history table: {e}")
        if db.connection:
            try:
                db.connection.rollback()
                print("⚠️ Transaction rolled back, continuing...")
            except:
                pass
        return False


def log_action(db, telegram_user_id, employee_name, action_type, action_detail="", employee_id="", department=""):
    """
    Log user action to history (legacy compatibility function)
    
    For new code, use log_audit() for more detailed logging with before/after states.
    """
    try:
        cursor = db.cursor
        
        # Convert action_detail to JSON if it's a string
        if isinstance(action_detail, str):
            detail_json = _json.dumps({"description": action_detail}) if action_detail else None
        elif isinstance(action_detail, dict):
            detail_json = _json.dumps(action_detail)
        else:
            detail_json = None
        
        cursor.execute("""
            INSERT INTO tbl_action_history 
            (telegram_user_id, employee_id, employee_name, department, action_type, action_detail)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (telegram_user_id, employee_id, employee_name, department, action_type, detail_json))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error logging action: {e}")
        if db.connection:
            db.connection.rollback()
        return False


def log_audit(db, telegram_user_id: int, employee_name: str, action_type: str,
              entity_type: str = None, entity_id: str = None,
              action_detail: dict = None, before_state: dict = None, after_state: dict = None,
              employee_id: str = "", department: str = ""):
    """
    Log detailed audit record to PostgreSQL (append-only)
    
    Args:
        db: Database connection
        telegram_user_id: Who performed the action
        employee_name: Name of the actor
        action_type: Type of action (create, update, delete, view, etc.)
        entity_type: Type of entity affected (task, employee, shift, menu_item, inventory, etc.)
        entity_id: ID of the affected entity
        action_detail: Additional details about the action (dict)
        before_state: State before the action (for updates/deletes)
        after_state: State after the action (for creates/updates)
        employee_id: Employee ID of the actor
        department: Department of the actor
    
    Returns:
        bool: Success status
    """
    try:
        cursor = db.cursor
        
        # Convert dicts to JSON strings
        detail_json = _json.dumps(action_detail) if action_detail else None
        before_json = _json.dumps(before_state) if before_state else None
        after_json = _json.dumps(after_state) if after_state else None
        
        cursor.execute("""
            INSERT INTO tbl_action_history 
            (telegram_user_id, employee_id, employee_name, department, action_type, 
             action_detail, entity_type, entity_id, before_state, after_state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            telegram_user_id, employee_id, employee_name, department, action_type,
            detail_json, entity_type, str(entity_id) if entity_id else None, 
            before_json, after_json
        ))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error logging audit: {e}")
        if db.connection:
            db.connection.rollback()
        return False


# Convenience audit logging functions for common operations

def audit_task_action(db, user_id: int, user_name: str, action: str, task_id: int,
                      task_data: dict = None, before_state: dict = None, after_state: dict = None,
                      employee_id: str = "", department: str = ""):
    """Log task-related audit action"""
    return log_audit(
        db, user_id, user_name, action,
        entity_type="task", entity_id=str(task_id),
        action_detail=task_data, before_state=before_state, after_state=after_state,
        employee_id=employee_id, department=department
    )


def audit_shift_action(db, user_id: int, user_name: str, action: str,
                       shift_data: dict = None, before_state: dict = None, after_state: dict = None,
                       employee_id: str = "", department: str = ""):
    """Log shift-related audit action (check-in, check-out, report)"""
    return log_audit(
        db, user_id, user_name, action,
        entity_type="shift", entity_id=shift_data.get('id') if shift_data else None,
        action_detail=shift_data, before_state=before_state, after_state=after_state,
        employee_id=employee_id, department=department
    )


def audit_menu_action(db, user_id: int, user_name: str, action: str, item_id: int,
                      item_data: dict = None, before_state: dict = None, after_state: dict = None,
                      employee_id: str = "", department: str = ""):
    """Log menu item audit action"""
    return log_audit(
        db, user_id, user_name, action,
        entity_type="menu_item", entity_id=str(item_id),
        action_detail=item_data, before_state=before_state, after_state=after_state,
        employee_id=employee_id, department=department
    )


def audit_inventory_action(db, user_id: int, user_name: str, action: str, item_id: int,
                           item_data: dict = None, before_state: dict = None, after_state: dict = None,
                           employee_id: str = "", department: str = ""):
    """Log inventory audit action"""
    return log_audit(
        db, user_id, user_name, action,
        entity_type="inventory", entity_id=str(item_id),
        action_detail=item_data, before_state=before_state, after_state=after_state,
        employee_id=employee_id, department=department
    )


def audit_employee_action(db, user_id: int, user_name: str, action: str, 
                          target_employee_id: str = None, target_data: dict = None,
                          before_state: dict = None, after_state: dict = None,
                          employee_id: str = "", department: str = ""):
    """Log employee-related audit action"""
    return log_audit(
        db, user_id, user_name, action,
        entity_type="employee", entity_id=target_employee_id,
        action_detail=target_data, before_state=before_state, after_state=after_state,
        employee_id=employee_id, department=department
    )


def get_action_history_by_date(db, date_str, department=None, limit=None, offset=0):
    """Get action history for specific date with optional department filter and pagination"""
    try:
        cursor = db.cursor
        
        # Build query based on filters - include new audit fields
        if date_str:
            query = """
                SELECT id, telegram_user_id, employee_id, employee_name, department,
                       action_type, action_detail, entity_type, entity_id, 
                       before_state, after_state, timestamp
                FROM tbl_action_history
                WHERE DATE(timestamp) = %s
            """
            params = [date_str]
        else:
            # Get all history if date is None
            query = """
                SELECT id, telegram_user_id, employee_id, employee_name, department,
                       action_type, action_detail, entity_type, entity_id,
                       before_state, after_state, timestamp
                FROM tbl_action_history
                WHERE 1=1
            """
            params = []
        
        if department:
            query += " AND department = %s"
            params.append(department)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            # Parse JSONB fields
            action_detail = row[6]
            if isinstance(action_detail, str):
                try:
                    action_detail = _json.loads(action_detail)
                except:
                    action_detail = {"description": action_detail}
            
            before_state = row[9]
            if isinstance(before_state, str):
                try:
                    before_state = _json.loads(before_state)
                except:
                    before_state = None
            
            after_state = row[10]
            if isinstance(after_state, str):
                try:
                    after_state = _json.loads(after_state)
                except:
                    after_state = None
            
            results.append({
                'id': row[0],
                'telegram_user_id': row[1],
                'employee_id': row[2],
                'employee_name': row[3],
                'department': row[4],
                'action_type': row[5],
                'action_detail': action_detail,
                'entity_type': row[7],
                'entity_id': row[8],
                'before_state': before_state,
                'after_state': after_state,
                'timestamp': row[11]
            })
        return results
    except Exception as e:
        print(f"❌ Error getting action history: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_action_history_count(db, date_str, department=None):
    """Get total count of actions for specific date with optional department filter"""
    try:
        cursor = db.cursor
        
        query = """
            SELECT COUNT(*)
            FROM tbl_action_history
            WHERE DATE(timestamp) = %s
        """
        params = [date_str]
        
        if department:
            query += " AND department = %s"
            params.append(department)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        print(f"❌ Error getting action history count: {e}")
        return 0


def get_departments_with_actions(db, date_str):
    """Get list of departments that have actions on specific date"""
    try:
        cursor = db.cursor
        cursor.execute("""
            SELECT DISTINCT department, COUNT(*) as action_count
            FROM tbl_action_history
            WHERE DATE(timestamp) = %s AND department IS NOT NULL AND department != ''
            GROUP BY department
            ORDER BY department
        """, (date_str,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'department': row[0],
                'count': row[1]
            })
        return results
    except Exception as e:
        print(f"❌ Error getting departments with actions: {e}")
        return []


def get_action_dates(db, limit=30):
    """Get list of dates with actions"""
    try:
        cursor = db.cursor
        cursor.execute("""
            SELECT DATE(timestamp) as action_date, COUNT(*) as action_count
            FROM tbl_action_history
            GROUP BY DATE(timestamp)
            ORDER BY action_date DESC
            LIMIT %s
        """, (limit,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                'date': row[0],
                'count': row[1]
            })
        return results
    except Exception as e:
        print(f"❌ Error getting action dates: {e}")
        return []


def get_action_statistics(db, date_str):
    """Get action statistics for specific date"""
    try:
        cursor = db.cursor
        
        # Total actions
        cursor.execute("""
            SELECT COUNT(*) FROM tbl_action_history
            WHERE DATE(timestamp) = %s
        """, (date_str,))
        result = cursor.fetchone()

        total = result[0] if result else 0
        
        # By action type
        cursor.execute("""
            SELECT action_type, COUNT(*) as count
            FROM tbl_action_history
            WHERE DATE(timestamp) = %s
            GROUP BY action_type
            ORDER BY count DESC
        """, (date_str,))
        by_type = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # By user
        cursor.execute("""
            SELECT employee_name, department, COUNT(*) as count
            FROM tbl_action_history
            WHERE DATE(timestamp) = %s
            GROUP BY employee_name
            ORDER BY count DESC
            LIMIT 10
        """, (date_str,))
        by_user = [{'name': row[0], 'department': row[1], 'count': row[2]} for row in cursor.fetchall()]
        
        return {
            'total': total,
            'by_type': by_type,
            'by_user': by_user
        }
    except Exception as e:
        print(f"❌ Error getting action statistics: {e}")
        return {'total': 0, 'by_type': [], 'by_user': []}


# ==================== KITCHEN & INVENTORY FUNCTIONS ====================

def create_kitchen_menu_table(db):
    """Create kitchen menu table"""
    try:
        db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_kitchen_menu (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                quantity INTEGER DEFAULT 0,
                price DECIMAL(10,2),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.connection.commit()
        
        # Check if table has data
        db.cursor.execute("SELECT COUNT(*) FROM tbl_kitchen_menu")
        count = db.cursor.fetchone()[0]
        
        # Insert sample data if empty
        if count == 0:
            sample_menu = [
                ('Breakfast Combo', 'Breakfast', 'Ready', 15, 12.99, 'Eggs, toast, coffee'),
                ('Grilled Chicken', 'Main Course', 'Cooking', 8, 18.99, 'Grilled chicken with vegetables'),
                ('Caesar Salad', 'Salad', 'Ready', 12, 9.99, 'Fresh caesar salad'),
                ('Beef Stew', 'Main Course', 'Pending', 5, 22.99, 'Slow cooked beef stew'),
                ('Fruit Platter', 'Dessert', 'Ready', 10, 8.99, 'Seasonal fresh fruits'),
                ('Pasta Carbonara', 'Main Course', 'Ready', 7, 16.99, 'Classic Italian pasta'),
                ('Fish and Chips', 'Main Course', 'Cooking', 6, 19.99, 'Fried fish with french fries'),
                ('Vegetable Soup', 'Appetizer', 'Ready', 20, 6.99, 'Fresh vegetable soup'),
            ]
            
            for item in sample_menu:
                db.cursor.execute("""
                    INSERT INTO tbl_kitchen_menu (name, category, status, quantity, price, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, item)
            
            db.connection.commit()
            print("✅ Sample kitchen menu data inserted")
        
        print("✅ tbl_kitchen_menu table ready")
        return True
    except Exception as e:
        print(f"❌ Error creating kitchen menu table: {e}")
        return False


def create_inventory_table(db):
    """Create inventory table"""
    try:
        db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_inventory (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                stock DECIMAL(10,2) DEFAULT 0,
                unit TEXT NOT NULL,
                min_stock DECIMAL(10,2) DEFAULT 0,
                max_stock DECIMAL(10,2),
                price_per_unit DECIMAL(10,2),
                supplier TEXT,
                last_ordered TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.connection.commit()
        
        # Check if table has data
        db.cursor.execute("SELECT COUNT(*) FROM tbl_inventory")
        count = db.cursor.fetchone()[0]
        
        # Insert sample data if empty
        if count == 0:
            sample_inventory = [
                ('Chicken Breast', 'Meat', 25, 'kg', 10, 50, 8.99, 'Local Farm'),
                ('Rice', 'Grains', 50, 'kg', 20, 100, 2.50, 'Rice Supplier Co'),
                ('Tomatoes', 'Vegetables', 8, 'kg', 15, 30, 3.20, 'Fresh Veggies Ltd'),
                ('Olive Oil', 'Oils', 12, 'L', 5, 20, 12.00, 'Olive Oil Co'),
                ('Eggs', 'Dairy', 3, 'dozen', 10, 30, 4.50, 'Farm Fresh Eggs'),
                ('Flour', 'Grains', 30, 'kg', 15, 60, 1.80, 'Grain Masters'),
                ('Milk', 'Dairy', 18, 'L', 10, 40, 2.30, 'Dairy Farm'),
                ('Beef', 'Meat', 7, 'kg', 12, 40, 15.50, 'Butcher Shop'),
                ('Onions', 'Vegetables', 20, 'kg', 10, 50, 1.50, 'Fresh Veggies Ltd'),
                ('Potatoes', 'Vegetables', 35, 'kg', 20, 80, 1.20, 'Fresh Veggies Ltd'),
                ('Cheese', 'Dairy', 6, 'kg', 8, 20, 12.50, 'Cheese Factory'),
                ('Salt', 'Spices', 15, 'kg', 5, 25, 0.80, 'Spice Warehouse'),
            ]
            
            for item in sample_inventory:
                db.cursor.execute("""
                    INSERT INTO tbl_inventory (name, category, stock, unit, min_stock, max_stock, price_per_unit, supplier)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, item)
            
            db.connection.commit()
            print("✅ Sample inventory data inserted")
        
        print("✅ tbl_inventory table ready")
        return True
    except Exception as e:
        print(f"❌ Error creating inventory table: {e}")
        return False


def get_kitchen_menu_items(db):
    """Get today's kitchen menu items from database"""
    try:
        db.cursor.execute("""
            SELECT id, name, category, status, quantity, price, description
            FROM tbl_kitchen_menu
            ORDER BY category, name
        """)
        
        rows = db.cursor.fetchall()
        menu_items = []
        
        for row in rows:
            menu_items.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'status': row[3],
                'quantity': row[4],
                'price': float(row[5]) if row[5] else 0,
                'description': row[6]
            })
        
        return menu_items
    except Exception as e:
        print(f"❌ Error getting kitchen menu items: {e}")
        return []


def get_inventory_items(db):
    """Get inventory items with stock levels from database"""
    try:
        db.cursor.execute("""
            SELECT id, name, category, stock, unit, min_stock, supplier, price_per_unit
            FROM tbl_inventory
            ORDER BY category, name
        """)
        
        rows = db.cursor.fetchall()
        inventory_items = []
        
        for row in rows:
            stock = float(row[3])
            min_stock = float(row[5])
            
            # Determine status
            if stock <= min_stock * 0.3:  # 30% or less of minimum
                status = 'Critical'
            elif stock < min_stock:
                status = 'Low'
            else:
                status = 'OK'
            
            inventory_items.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'stock': stock,
                'unit': row[4],
                'min_stock': min_stock,
                'supplier': row[6],
                'price': float(row[7]) if row[7] else 0,
                'status': status
            })
        
        return inventory_items
    except Exception as e:
        print(f"❌ Error getting inventory items: {e}")
        return []


def get_inventory_summary(db):
    """Get inventory summary statistics"""
    items = get_inventory_items(db)
    
    total_items = len(items)
    ok_items = len([i for i in items if i['status'] == 'OK'])
    low_items = len([i for i in items if i['status'] == 'Low'])
    critical_items = len([i for i in items if i['status'] == 'Critical'])
    
    return {
        'total': total_items,
        'ok': ok_items,
        'low': low_items,
        'critical': critical_items
    }


def get_menu_item_by_id(db, item_id):
    """Get a single menu item by ID"""
    try:
        db.cursor.execute("""
            SELECT id, name, category, status, quantity, price, description
            FROM tbl_kitchen_menu WHERE id = %s
        """, (item_id,))
        row = db.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'status': row[3],
                'quantity': row[4],
                'price': row[5],
                'description': row[6]
            }
        return None
    except Exception as e:
        print(f"❌ Error getting menu item: {e}")
        return None


def update_menu_item_status(db, menu_id, status):
    """Update kitchen menu item status"""
    try:
        db.cursor.execute("""
            UPDATE tbl_kitchen_menu 
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (status, menu_id))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating menu item: {e}")
        return False


def get_inventory_item_by_id(db, item_id):
    """Get a single inventory item by ID"""
    try:
        db.cursor.execute("""
            SELECT id, name, category, stock, unit, min_stock, department
            FROM tbl_inventory WHERE id = %s
        """, (item_id,))
        row = db.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'stock': row[3],
                'unit': row[4],
                'min_stock': row[5],
                'department': row[6]
            }
        return None
    except Exception as e:
        print(f"❌ Error getting inventory item: {e}")
        return None


def update_inventory_stock(db, item_id, new_stock):
    """Update inventory item stock level"""
    try:
        db.cursor.execute("""
            UPDATE tbl_inventory 
            SET stock = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_stock, item_id))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating inventory: {e}")
        return False


def has_user_been_notified(db: DatabaseManager, event_id: int, telegram_user_id: int, alarm_type: str) -> bool:
    """Check if a user has already been notified for this event and alarm type"""
    try:
        db.cursor.execute("""
            SELECT COUNT(*) FROM tbl_hotel_event_user_notifications
            WHERE event_id = %s AND telegram_user_id = %s AND alarm_type = %s
        """, (event_id, telegram_user_id, alarm_type))
        result = db.cursor.fetchone()
        return result[0] > 0 if result else False
    except Exception as e:
        print(f"❌ Error checking user notification: {e}")
        return False


def record_user_notification(db: DatabaseManager, event_id: int, telegram_user_id: int, alarm_type: str) -> bool:
    """Record that a user has been notified for this event and alarm type"""
    try:
        db.cursor.execute("""
            INSERT INTO tbl_hotel_event_user_notifications (event_id, telegram_user_id, alarm_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (event_id, telegram_user_id, alarm_type) DO NOTHING
        """, (event_id, telegram_user_id, alarm_type))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error recording user notification: {e}")
        if db.connection:
            db.connection.rollback()
        return False


def get_notified_users_for_event(db: DatabaseManager, event_id: int, alarm_type: str) -> set:
    """Get set of user IDs that have been notified for this event and alarm type"""
    try:
        db.cursor.execute("""
            SELECT telegram_user_id FROM tbl_hotel_event_user_notifications
            WHERE event_id = %s AND alarm_type = %s
        """, (event_id, alarm_type))
        results = db.cursor.fetchall()
        return {row[0] for row in results}
    except Exception as e:
        print(f"❌ Error getting notified users: {e}")
        return set()


def clear_event_notifications(db: DatabaseManager, event_id: int) -> bool:
    """Clear all user notifications for an event (useful when event is cancelled/rescheduled)"""
    try:
        db.cursor.execute("""
            DELETE FROM tbl_hotel_event_user_notifications
            WHERE event_id = %s
        """, (event_id,))
        db.connection.commit()
        print(f"✅ Cleared all notifications for event ID {event_id}")
        return True
    except Exception as e:
        print(f"❌ Error clearing event notifications: {e}")
        if db.connection:
            db.connection.rollback()
        return False


# ========== Task Workflow Management Functions ==========

def validate_task_status_transition(current_status: str, new_status: str) -> tuple[bool, str]:
    """
    Validate if a status transition is allowed
    
    Returns:
        (is_valid, error_message)
    """
    # Define allowed transitions
    allowed_transitions = {
        'pending': ['in_progress', 'pending_confirmation', 'rejected'],
        'in_progress': ['pending_confirmation', 'rejected'],
        'pending_confirmation': ['completed', 'rejected'],  # Admin can approve or reject
        'completed': [],  # Cannot change from completed
        'rejected': ['pending']  # Can reassign rejected tasks
    }
    
    if current_status not in allowed_transitions:
        return False, f"Invalid current status: {current_status}"
    
    if new_status not in allowed_transitions.get(current_status, []):
        return False, f"Cannot change from '{current_status}' to '{new_status}'"
    
    return True, ""


def record_task_status_change(db: DatabaseManager, task_id: int, task_table: str, 
                               old_status: str, new_status: str, 
                               changed_by: int, changed_by_name: str = None, 
                               notes: str = None) -> bool:
    """Record task status change in history table"""
    try:
        db.cursor.execute("""
            INSERT INTO tbl_task_status_history 
            (task_id, task_table, old_status, new_status, changed_by, changed_by_name, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (task_id, task_table, old_status, new_status, changed_by, changed_by_name, notes))
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error recording status change: {e}")
        return False


def start_task(db: DatabaseManager, task_id: int, task_table: str, user_id: int, user_name: str = None) -> tuple[bool, str]:
    """
    Start a task (transition from pending to in_progress)
    
    Returns:
        (success, message)
    """
    try:
        # Get current task status
        db.cursor.execute(f"SELECT status FROM {task_table} WHERE id = %s", (task_id,))
        result = db.cursor.fetchone()
        
        if not result:
            return False, "Task not found"
        
        current_status = result[0]
        
        # Validate transition
        is_valid, error_msg = validate_task_status_transition(current_status, 'in_progress')
        if not is_valid:
            return False, error_msg
        
        # Update task status
        db.cursor.execute(f"""
            UPDATE {task_table} 
            SET status = 'in_progress', started_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (task_id,))
        
        # Record status change
        record_task_status_change(db, task_id, task_table, current_status, 'in_progress', 
                                 user_id, user_name, "Task started")
        
        db.connection.commit()
        print(f"✅ Task {task_id} started by user {user_id}")
        return True, "Task started successfully"
        
    except Exception as e:
        print(f"❌ Error starting task: {e}")
        if db.connection:
            db.connection.rollback()
        return False, str(e)


def complete_task_with_proof(db: DatabaseManager, task_id: int, task_table: str, 
                              user_id: int, proof_path: str = None, 
                              report_notes: str = None, user_name: str = None) -> tuple[bool, str]:
    """
    Submit task for completion (will be pending admin confirmation)
    
    Returns:
        (success, message)
    """
    try:
        # Get current task info
        db.cursor.execute(f"""
            SELECT status, proof_required, proof_type 
            FROM {task_table} WHERE id = %s
        """, (task_id,))
        result = db.cursor.fetchone()
        
        if not result:
            return False, "Task not found"
        
        current_status, proof_required, proof_type = result[0], result[1], result[2]
        
        # Validate transition to pending_confirmation
        is_valid, error_msg = validate_task_status_transition(current_status, 'pending_confirmation')
        if not is_valid:
            return False, error_msg
        
        # ENFORCE PROOF REQUIREMENT
        if proof_required == 1:
            if not proof_path:
                return False, f"⛔ Proof is REQUIRED for this task. Please upload {proof_type or 'photo/video'}"
        
        # Update task status to pending_confirmation (awaiting admin approval)
        update_query = f"""
            UPDATE {task_table} 
            SET status = 'pending_confirmation', 
                completed_at = CURRENT_TIMESTAMP,
                proof_path = %s,
                proof_submitted = %s,
                report_notes = %s
            WHERE id = %s
        """
        proof_submitted = 1 if proof_path else 0
        db.cursor.execute(update_query, (proof_path, proof_submitted, report_notes, task_id))
        
        # Record status change
        notes = f"Task submitted for approval. Proof submitted: {'Yes' if proof_path else 'No'}"
        if report_notes:
            notes += f". Notes: {report_notes}"
        
        record_task_status_change(db, task_id, task_table, current_status, 'pending_confirmation', 
                                 user_id, user_name, notes)
        
        db.connection.commit()
        print(f"✅ Task {task_id} submitted for approval by user {user_id}")
        return True, "Task submitted for admin approval"
        
    except Exception as e:
        print(f"❌ Error submitting task: {e}")
        if db.connection:
            db.connection.rollback()
        return False, str(e)


def reject_task(db: DatabaseManager, task_id: int, task_table: str, 
                admin_id: int, reason: str, admin_name: str = None) -> tuple[bool, str]:
    """
    Reject a task (admin only)
    
    Returns:
        (success, message)
    """
    try:
        # Get current task status
        db.cursor.execute(f"SELECT status FROM {task_table} WHERE id = %s", (task_id,))
        result = db.cursor.fetchone()
        
        if not result:
            return False, "Task not found"
        
        current_status = result[0]
        
        # Validate transition
        is_valid, error_msg = validate_task_status_transition(current_status, 'rejected')
        if not is_valid:
            return False, error_msg
        
        # Update task status
        db.cursor.execute(f"""
            UPDATE {task_table} 
            SET status = 'rejected', 
                rejected_at = CURRENT_TIMESTAMP,
                rejected_by = %s,
                rejection_reason = %s
            WHERE id = %s
        """, (admin_id, reason, task_id))
        
        # Record status change
        record_task_status_change(db, task_id, task_table, current_status, 'rejected', 
                                 admin_id, admin_name, f"Rejected: {reason}")
        
        db.connection.commit()
        print(f"✅ Task {task_id} rejected by admin {admin_id}")
        return True, "Task rejected"
        
    except Exception as e:
        print(f"❌ Error rejecting task: {e}")
        if db.connection:
            db.connection.rollback()
        return False, str(e)


def escalate_overdue_task(db: DatabaseManager, task_id: int, task_table: str, 
                          escalated_to: int) -> tuple[bool, str]:
    """
    Escalate an overdue task to a manager/admin
    
    Returns:
        (success, message)
    """
    try:
        db.cursor.execute(f"""
            UPDATE {task_table} 
            SET escalated = 1, 
                escalated_at = CURRENT_TIMESTAMP,
                escalated_to = %s
            WHERE id = %s
        """, (escalated_to, task_id))
        
        db.connection.commit()
        print(f"✅ Task {task_id} escalated to user {escalated_to}")
        return True, "Task escalated"
        
    except Exception as e:
        print(f"❌ Error escalating task: {e}")
        if db.connection:
            db.connection.rollback()
        return False, str(e)


def get_overdue_tasks_for_escalation(db: DatabaseManager, hours_overdue: int = 4) -> list:
    """
    Get tasks that are overdue by specified hours and not yet escalated
    
    Returns:
        List of task dictionaries
    """
    try:
        # Query from tbl_tasks
        db.cursor.execute(f"""
            SELECT id, description, assignee_id, assignee_name, department, 
                   due_date, status, escalated, created_by
            FROM tbl_tasks
            WHERE status IN ('pending', 'in_progress')
            AND escalated = 0
            AND due_date::timestamp < NOW() - INTERVAL '{hours_overdue} hours'
        """)
        
        results = db.cursor.fetchall()
        tasks = []
        for row in results:
            tasks.append({
                'id': row[0],
                'description': row[1],
                'assignee_id': row[2],
                'assignee_name': row[3],
                'department': row[4],
                'due_date': row[5],
                'status': row[6],
                'escalated': row[7],
                'created_by': row[8],
                'table': 'tbl_tasks'
            })
        
        return tasks
        
    except Exception as e:
        print(f"❌ Error getting overdue tasks for escalation: {e}")
        return []


def get_task_status_history(db: DatabaseManager, task_id: int, task_table: str) -> list:
    """Get status change history for a task"""
    try:
        db.cursor.execute("""
            SELECT old_status, new_status, changed_by, changed_by_name, changed_at, notes
            FROM tbl_task_status_history
            WHERE task_id = %s AND task_table = %s
            ORDER BY changed_at DESC
        """, (task_id, task_table))
        
        results = db.cursor.fetchall()
        history = []
        for row in results:
            history.append({
                'old_status': row[0],
                'new_status': row[1],
                'changed_by': row[2],
                'changed_by_name': row[3],
                'changed_at': row[4],
                'notes': row[5]
            })
        
        return history
        
    except Exception as e:
        print(f"❌ Error getting task history: {e}")
        return []


# ==================== WhatsApp Management Functions ====================

def save_whatsapp_credentials(db: DatabaseManager, account_sid: str, auth_token: str, whatsapp_from: str) -> bool:
    """
    Save WhatsApp/Twilio credentials to database (encrypted)
    
    Args:
        db: Database manager instance
        account_sid: Twilio Account SID
        auth_token: Twilio Auth Token
        whatsapp_from: WhatsApp-enabled Twilio number
        
    Returns:
        True if successful
    """
    try:
        from security_manager import SecurityManager
        import os
        
        # Initialize security manager with db_config
        db_config = {
            'host': os.getenv('DB_HOST', db.db_host),
            'port': os.getenv('DB_PORT', db.db_port),
            'name': os.getenv('DB_NAME', db.db_name),
            'user': os.getenv('DB_USER', db.db_user),
            'password': os.getenv('DB_PASSWORD', db.db_password)
        }
        sec_mgr = SecurityManager(db_config)
        
        # Encrypt credentials
        sid_encrypted = sec_mgr.encrypt(account_sid)
        token_encrypted = sec_mgr.encrypt(auth_token)
        from_encrypted = sec_mgr.encrypt(whatsapp_from)
        
        # Close security manager connection
        sec_mgr.close()
        
        # Check if credentials already exist
        db.cursor.execute("SELECT id FROM tbl_whatsapp_credentials WHERE id = 1")
        exists = db.cursor.fetchone()
        
        if exists:
            # Update existing credentials
            db.cursor.execute("""
                UPDATE tbl_whatsapp_credentials
                SET account_sid_encrypted = %s,
                    auth_token_encrypted = %s,
                    whatsapp_from_encrypted = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """, (sid_encrypted, token_encrypted, from_encrypted))
        else:
            # Insert new credentials
            db.cursor.execute("""
                INSERT INTO tbl_whatsapp_credentials (id, account_sid_encrypted, auth_token_encrypted, whatsapp_from_encrypted)
                VALUES (1, %s, %s, %s)
            """, (sid_encrypted, token_encrypted, from_encrypted))
        
        db.connection.commit()
        print("✅ WhatsApp credentials saved to database")
        return True
        
    except Exception as e:
        print(f"❌ Error saving WhatsApp credentials: {e}")
        if db.connection:
            db.connection.rollback()
        return False


def get_whatsapp_credentials_from_db(db: DatabaseManager) -> dict:
    """
    Get WhatsApp/Twilio credentials from database (decrypted)
    
    Returns:
        Dictionary with 'account_sid', 'auth_token', 'whatsapp_from' or None
    """
    try:
        db.cursor.execute("""
            SELECT account_sid_encrypted, auth_token_encrypted, whatsapp_from_encrypted
            FROM tbl_whatsapp_credentials
            WHERE id = 1
        """)
        
        result = db.cursor.fetchone()
        
        if not result:
            print("⚠️ No WhatsApp credentials found in database")
            return None
        
        from security_manager import SecurityManager
        import os
        
        # Initialize security manager with db_config
        db_config = {
            'host': os.getenv('DB_HOST', db.db_host),
            'port': os.getenv('DB_PORT', db.db_port),
            'name': os.getenv('DB_NAME', db.db_name),
            'user': os.getenv('DB_USER', db.db_user),
            'password': os.getenv('DB_PASSWORD', db.db_password)
        }
        sec_mgr = SecurityManager(db_config)
        
        # Decrypt credentials
        account_sid = sec_mgr.decrypt(bytes(result[0]))
        auth_token = sec_mgr.decrypt(bytes(result[1]))
        whatsapp_from = sec_mgr.decrypt(bytes(result[2]))
        
        # Close security manager connection
        sec_mgr.close()
        
        return {
            'account_sid': account_sid,
            'auth_token': auth_token,
            'whatsapp_from': whatsapp_from
        }
        
    except Exception as e:
        print(f"❌ Error getting WhatsApp credentials: {e}")
        return None


def log_whatsapp_message(db: DatabaseManager, recipient: str, recipient_name: str, 
                        message_body: str, status: str, message_sid: str = None, 
                        error_message: str = None) -> bool:
    """
    Log WhatsApp message sending to database
    
    Args:
        db: Database manager instance
        recipient: Recipient phone number
        recipient_name: Recipient name
        message_body: Message body text
        status: 'sent' or 'failed'
        message_sid: Twilio message SID (if sent)
        error_message: Error message (if failed)
        
    Returns:
        True if logged successfully
    """
    try:
        db.cursor.execute("""
            INSERT INTO tbl_whatsapp_logs 
            (recipient, recipient_name, message_body, status, message_sid, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (recipient, recipient_name, message_body, status, message_sid, error_message))
        
        db.connection.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error logging WhatsApp message: {e}")
        if db.connection:
            db.connection.rollback()
        return False


def get_whatsapp_logs(db: DatabaseManager, limit: int = 50) -> list:
    """
    Get WhatsApp message logs
    
    Args:
        db: Database manager instance
        limit: Maximum number of logs to retrieve
        
    Returns:
        List of log dictionaries
    """
    try:
        db.cursor.execute("""
            SELECT id, recipient, recipient_name, message_body, status, 
                   message_sid, error_message, sent_at
            FROM tbl_whatsapp_logs
            ORDER BY sent_at DESC
            LIMIT %s
        """, (limit,))
        
        results = db.cursor.fetchall()
        logs = []
        
        for row in results:
            logs.append({
                'id': row[0],
                'recipient': row[1],
                'recipient_name': row[2],
                'message_body': row[3],
                'status': row[4],
                'message_sid': row[5],
                'error_message': row[6],
                'sent_at': row[7]
            })
        
        return logs
        
    except Exception as e:
        print(f"❌ Error getting WhatsApp logs: {e}")
        return []


def get_employees_with_whatsapp(db: DatabaseManager, department: str = None) -> list:
    """
    Get employees who have WhatsApp numbers registered
    
    Args:
        db: Database manager instance
        department: Filter by department (optional)
        
    Returns:
        List of employee dictionaries with WhatsApp numbers
    """
    try:
        if department:
            db.cursor.execute("""
                SELECT employee_id, name, department, whatsapp, telegram_user_id
                FROM tbl_employeer
                WHERE whatsapp IS NOT NULL AND whatsapp != ''
                AND department = %s
                ORDER BY name
            """, (department,))
        else:
            db.cursor.execute("""
                SELECT employee_id, name, department, whatsapp, telegram_user_id
                FROM tbl_employeer
                WHERE whatsapp IS NOT NULL AND whatsapp != ''
                ORDER BY department, name
            """)
        
        results = db.cursor.fetchall()
        employees = []
        
        for row in results:
            employees.append({
                'employee_id': row[0],
                'name': row[1],
                'department': row[2],
                'whatsapp': row[3],
                'telegram_user_id': row[4]
            })
        
        return employees
        
    except Exception as e:
        print(f"❌ Error getting employees with WhatsApp: {e}")
        return []






