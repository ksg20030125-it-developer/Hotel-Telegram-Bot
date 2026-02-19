# 🏨 Hotel Management Telegram Bot

A comprehensive hotel management system built on Telegram platform with AI-powered features, multi-language support, and integrated communication channels.

## 📞 Support
Name: Jovan Ilic
WhatsApp:+381621407098
Telegram:@jovan91


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-21.0+-blue.svg)](https://core.telegram.org/bots/api)

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Database Schema](#-database-schema)
- [API Integrations](#-api-integrations)
- [Security](#-security)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 👥 Employee Management
- Multi-department employee tracking (Reception, Housekeeping, Laundry, Kitchen, Maintenance)
- Work role assignments (shift, part-time, on-call)
- Employee profiles with contact information
- Multi-language support (English, Serbian)

### 📋 Task Management
- Create, assign, and track tasks across departments
- Priority levels (Low, Normal, High, Urgent)
- Task completion tracking with timestamps
- Overdue task notifications
- Calendar-based date selection

### 🔄 Shift Operations
- Reception shift management (Morning, Evening, Night)
- Shift handover reports with AI summaries
- On-duty employee tracking
- Automatic shift reminders
- Shift history and analytics

### 🧹 Housekeeping Operations
- Room cleaning tracking
- Tool borrowing system
- Key management
- Room status updates
- Cleaning history logs

### 📧 Communication Systems
- **Email Integration**
  - AI-powered email generation (OpenAI GPT-4)
  - Bulk email sending
  - SMTP tracking with detailed logs
  - Success/failure monitoring
  
- **WhatsApp Integration**
  - Twilio API integration
  - Message logging
  - Bulk messaging support

### 📅 Event Management
- Hotel event scheduling
- Event-specific tasks
- Multi-time alarms (30 min, 1 hour, 2 hours before)
- Department-specific notifications

### 🤖 AI Features
- Email content generation using GPT-4
- Intelligent email analysis and suggestions
- Context-aware message formatting

### 🔐 Security
- Encrypted credential storage (Fernet encryption)
- Secure database for sensitive data
- Role-based access control
- Admin-only operations protection

## 🏗️ System Architecture

```
┌─────────────────┐
│  Telegram Bot   │  ← User Interface
│   (Frontend)    │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────┐
│     Backend Application             │
│     (Python 3.12 + AsyncIO)        │
│                                     │
│  ├─ bot.py           (Handlers)    │
│  ├─ database.py      (DB Ops)      │
│  ├─ email_service.py (SMTP)        │
│  ├─ whatsapp_service.py (Twilio)   │
│  ├─ ai_analyzer.py   (OpenAI)      │
│  └─ security_manager.py (Crypto)   │
└─────────────┬───────────────────────┘
              │
              ↓
     ┌────────────────┐
     │   PostgreSQL   │  ← Database
     │  hotel_manage  │
     └────────┬───────┘
              │
    ┌─────────┴──────────┐
    ↓                    ↓
┌─────────┐      ┌──────────────┐
│ OpenAI  │      │    Twilio    │  ← External APIs
│  GPT-4  │      │   WhatsApp   │
└─────────┘      └──────────────┘
```

## 📦 Prerequisites

### Required Software
- **Python**: 3.12 or higher
- **PostgreSQL**: 14 or higher
- **Operating System**: Windows 10/11, Linux, or macOS

### Required Accounts
- [Telegram Bot Token](https://core.telegram.org/bots#6-botfather) (via @BotFather)
- [OpenAI API Key](https://platform.openai.com/api-keys) (for AI features)
- [Twilio Account](https://www.twilio.com/) (for WhatsApp integration)
- Gmail account with App Password (for email sending)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ksg20030125-it-developer/Hotel-Telegram-Bot.git
cd Hotel-Telegram-Bot
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database
```sql
-- Create database
CREATE DATABASE hotel_manage;

-- Create user (if needed)
CREATE USER postgres WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE hotel_manage TO postgres;
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hotel_manage
DB_USER=postgres
DB_PASSWORD=your_database_password

# Timezone
TIMEZONE=Europe/Belgrade
```

**Note**: Sensitive credentials (Telegram token, API keys) are stored encrypted in the database for security.

## ⚙️ Configuration

### Initial Setup

Run the setup wizard to configure encrypted credentials:

```bash
python setup_wizard.py
```

The wizard will guide you through:
1. Database connection setup
2. Telegram Bot token configuration
3. OpenAI API key setup
4. Email SMTP credentials
5. Twilio WhatsApp credentials

### Manual Credential Storage

If you prefer manual setup:

```bash
# Store Telegram token
python -c "from security_manager import SecurityManager; SecurityManager({'host':'localhost','port':'5432','name':'hotel_manage','user':'postgres','password':'YOUR_DB_PASSWORD'}).set_secret('telegram_bot_token', 'YOUR_BOT_TOKEN')"

# Store OpenAI API key
python -c "from security_manager import SecurityManager; SecurityManager({'host':'localhost','port':'5432','name':'hotel_manage','user':'postgres','password':'YOUR_DB_PASSWORD'}).set_secret('openai_api_key', 'YOUR_OPENAI_KEY')"
```

## 🎯 Usage

### Starting the Bot

```bash
python main.py
```

### Bot Commands

#### User Commands
- `/start` - Initialize bot and show main menu
- `/language` - Change language (English/Serbian)
- `/help` - Show help information

#### Menu Features
- **👥 Employees** - View and manage employees
- **📋 Tasks** - Create, view, and complete tasks
- **🔄 Shifts** - Manage reception shifts
- **🧹 Housekeeping** - Room cleaning and key management
- **📧 Email** - Send emails with AI assistance
- **💬 WhatsApp** - Send WhatsApp messages
- **📅 Events** - Schedule hotel events
- **📊 Reports** - View analytics and history

### Creating a Task

1. Tap **📋 Tasks** → **➕ Create Task**
2. Enter task description
3. Select department
4. Choose assignee
5. Set due date using calendar
6. Select priority level
7. Confirm creation

### Shift Handover

1. Tap **🔄 Shifts** → **📝 Report Current Shift**
2. Describe shift activities
3. Report any issues or notes
4. System generates AI summary
5. Notification sent to next shift

## 💾 Database Schema

### Core Tables

#### `tbl_employeer`
Employee information and department assignments
```sql
- id (SERIAL PRIMARY KEY)
- first_name (VARCHAR)
- last_name (VARCHAR)
- telegram_id (BIGINT)
- department (VARCHAR)
- work_role (VARCHAR)
- phone (VARCHAR)
- email (VARCHAR)
- language (VARCHAR)
```

#### `tbl_tasks`
Task management and tracking
```sql
- id (SERIAL PRIMARY KEY)
- description (TEXT)
- assigned_to (INTEGER)
- department (VARCHAR)
- priority (VARCHAR)
- due_date (DATE)
- completed (BOOLEAN)
- completed_at (TIMESTAMP)
- created_by (INTEGER)
- created_at (TIMESTAMP)
```

#### `tbl_email_logs`
Comprehensive email tracking
```sql
- id (SERIAL PRIMARY KEY)
- recipient_email (VARCHAR)
- subject (TEXT)
- body (TEXT)
- sent_at (TIMESTAMP)
- status (VARCHAR)
- error_message (TEXT)
- smtp_response (TEXT)
- email_size_bytes (INTEGER)
- sender_name (VARCHAR)
- recipient_name (VARCHAR)
- sent_by_user_id (INTEGER)
- attempt_count (INTEGER)
```

#### `tbl_shift_reports`
Reception shift handover reports
```sql
- id (SERIAL PRIMARY KEY)
- shift_number (INTEGER)
- report_date (DATE)
- employee_id (INTEGER)
- report_text (TEXT)
- ai_summary (TEXT)
- created_at (TIMESTAMP)
```

#### `tbl_secrets`
Encrypted credential storage (Fernet encryption)
```sql
- key (VARCHAR PRIMARY KEY)
- value (BYTEA)
- updated_at (TIMESTAMP)
```

## 🔌 API Integrations

### Telegram Bot API
- **Library**: python-telegram-bot v21+
- **Features**: Inline keyboards, callbacks, media handling
- **Async**: Full async/await support

### OpenAI GPT-4
- **Model**: gpt-4
- **Use Cases**: 
  - Email content generation
  - Shift report summarization
  - Professional message formatting

### Twilio WhatsApp
- **Service**: Twilio WhatsApp Business API
- **Features**:
  - Message sending
  - Sandbox testing
  - Production deployment

### Gmail SMTP
- **Server**: smtp.gmail.com:587
- **Protocol**: TLS encryption
- **Authentication**: App-specific passwords

## 🔐 Security

### Encryption
- **Algorithm**: Fernet (symmetric encryption)
- **Key Storage**: Secure database table
- **Encrypted Data**: 
  - Telegram Bot token
  - OpenAI API keys
  - SMTP credentials
  - Twilio credentials

### Best Practices
- Never commit `.env` files
- Use environment variables for non-sensitive config
- Database encryption for all API keys
- Role-based access control
- Admin verification for sensitive operations

### Security Utilities
```bash
# Verify encrypted secrets
python verify_secrets.py

# Migrate credentials to secure storage
python migrate_to_secure_db.py
```

## 📦 Deployment

### Development
```bash
python main.py
```

### Production (Linux with systemd)

Create `/etc/systemd/system/hotel-bot.service`:
```ini
[Unit]
Description=Hotel Management Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/Hotel-Telegram-Bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hotel-bot
sudo systemctl start hotel-bot
sudo systemctl status hotel-bot
```

### Windows Service
Use `build_exe.py` to create a standalone executable:
```bash
python build_exe.py
```

Or install as Windows service using NSSM:
```powershell
nssm install HotelBot "C:\path\to\venv\Scripts\python.exe" "C:\path\to\main.py"
nssm start HotelBot
```

## 🛠️ Development

### Project Structure
```
Hotel-Telegram-Bot/
├── main.py                    # Entry point
├── bot.py                     # Main bot logic (26k+ lines)
├── database.py                # Database operations
├── email_service.py           # SMTP email handling
├── email_ai_analyzer.py       # AI email generation
├── whatsapp_service.py        # Twilio integration
├── notification_manager.py    # Bulk notifications
├── security_manager.py        # Encryption utilities
├── shift_operations.py        # Shift management
├── languages.py               # Multi-language support
├── templates.py               # Message templates
├── setup_wizard.py            # Initial configuration
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not committed)
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

### Testing
```bash
# Test email sending
python check_email_logs.py

# Test WhatsApp status
python check_whatsapp_status.py

# Test shift operations
python test_shift_handover.py

# Test task creation
python test_create_task.py
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add docstrings to all functions
- Write unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**ksg20030125-it-developer**
- GitHub: [@ksg20030125-it-developer](https://github.com/ksg20030125-it-developer)
- Repository: [Hotel-Telegram-Bot](https://github.com/ksg20030125-it-developer/Hotel-Telegram-Bot)

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot framework
- [OpenAI](https://openai.com/) - GPT-4 API
- [Twilio](https://www.twilio.com/) - WhatsApp Business API
- [PostgreSQL](https://www.postgresql.org/) - Database system

## 📞 Support
Name: Jovan Ilic
WhatsApp:+381621407098
Telegram:@jovan91


---

**Made with ❤️ for efficient hotel management**
