# Hotel Management Bot - Technical Handover Guide

## 📋 Document Information
- **Project**: Hotel Management Bot (Telegram-based)
- **Version**: 2.2 (Enhanced Email & WhatsApp Logging)
- **Date**: February 18, 2026
- **Bot**: @MySVEN0125_Hotel_ManagerBot

---

## 🏗️ System Architecture

```
┌─────────────────┐
│  Telegram Bot   │  ← User Interface (Telegram App)
│  @MySVEN999999  │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────────┐
│          Backend Application                │
│  (main.py - Python 3.12)                   │
│                                             │
│  ├─ bot.py             (Telegram handlers)  │
│  ├─ database.py        (PostgreSQL ops)     │
│  ├─ email_service.py   (SMTP/Gmail)        │
│  ├─ whatsapp_service.py (Twilio API)       │
│  ├─ notification_manager.py (Bulk sender)   │
│  ├─ email_ai_analyzer.py (OpenAI GPT-4)    │
│  └─ security_manager.py (Encryption)        │
└─────────────┬───────────────────────────────┘
              │
              ↓
     ┌────────────────┐
     │   PostgreSQL   │  ← Database (localhost:5432)
     │  hotel_manage  │
     └────────┬───────┘
              │
    ┌─────────┴──────────┐
    ↓                    ↓
┌─────────┐      ┌──────────────┐
│ OpenAI  │      │    Twilio    │  ← External APIs
│ API     │      │   WhatsApp   │
└─────────┘      └──────────────┘
```

---

## 💾 Database Schema

**Database**: PostgreSQL 14+  
**Name**: `hotel_manage`  
**User**: `postgres`  
**Port**: `5432`

### Key Tables:
- `tbl_employeer` - Employee information
- `tbl_tasks` - Task management
- `tbl_email_logs` - Email sending logs (13 columns with SMTP tracking)
- `tbl_whatsapp_logs` - WhatsApp message logs
- `tbl_secrets` - Encrypted credentials (Telegram token, API keys)
- `tbl_shift_reports` - Reception shift handover reports
- `tbl_hotel_event_tasks` - Event management tasks
- `tbl_clean_history` - Room cleaning records
- `tbl_key_history` - Key borrowing tracking
- `tbl_tool_history` - Tool borrowing tracking

---

## 🔧 System Components

### 1. Core Backend (`main.py`)
- **Language**: Python 3.12
- **Framework**: python-telegram-bot (v21+)
- **Entry Point**: `main.py`
- **Async/Await**: All handlers use async functions

### 2. Database Layer (`database.py`)
- **Driver**: psycopg2
- **Connection**: Persistent connection with reconnection logic
- **Features**: Automatic table creation, schema upgrades

### 3. Email System (`email_service.py` + `notification_manager.py`)
- **SMTP**: Gmail SMTP (smtp.gmail.com:587)
- **Enhanced Logging**: 13-column tracking system
  - Success/failure status
  - SMTP response codes
  - Error messages
  - Email size, sender/recipient names
  - Sent by user ID
- **AI Generation**: OpenAI GPT-4 for email content

### 4. WhatsApp Integration (`whatsapp_service.py`)
- **Provider**: Twilio API
- **Sandbox**: Twilio Sandbox for testing
- **Production**: Real WhatsApp Business API
- **Logging**: Complete message tracking in `tbl_whatsapp_logs`

### 5. Security (`security_manager.py`)
- **Encryption**: Fernet (symmetric encryption)
- **Encrypted Data**:
  - Telegram Bot Token
  - OpenAI API Key
  - Email credentials (sender email + app password)
  - WhatsApp credentials (Twilio SID + Auth Token)
- **Storage**: `tbl_secrets` table in PostgreSQL

---

## 📝 Configuration & Environment Variables

### Environment File: `.env`
Located in project root directory:

```ini
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hotel_manage
DB_USER=postgres
DB_PASSWORD=postgres

# SMTP Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# API Keys stored encrypted in database (via Setup Wizard)
# TELEGRAM_BOT_TOKEN=
# OPENAI_API_KEY=
# SENDER_EMAIL=
# APP_PASSWORD=
# TWILIO_ACCOUNT_SID=
# TWILIO_AUTH_TOKEN=
# TWILIO_WHATSAPP_FROM=
```

### First-Time Setup:
1. Run `main.py`
2. Setup Wizard automatically launches
3. Enter credentials (saved encrypted in database)
4. Credentials persist across restarts

---

## 🚀 Deployment

### Current Deployment:
- **Location**: `d:\Work\Telegram-Bot217`
- **Execution**: `python main.py` (or use virtual environment)
- **Virtual Environment**: `.venv` folder
- **Release Build**: `release\HotelManagementBot.exe` (standalone)

### Dependencies:
```bash
python-telegram-bot>=21.0
psycopg2-binary
openai>=1.0
cryptography
twilio
python-dotenv
```

### Install Dependencies:
```bash
pip install -r requirements.txt
```

### PostgreSQL Setup:
```sql
CREATE DATABASE hotel_manage;
-- Tables auto-created on first run
```

---

## 📦 Standalone Executable Deployment

### Build Process:
```bash
python build_simple.py
```

### Output:
- `release\HotelManagementBot.exe` (44 MB)
- `release\.env` (configuration file)

### Deploy to Another Computer:
1. Copy both files to target computer
2. Ensure PostgreSQL is accessible
3. Update `.env` if database is remote:
   ```ini
   DB_HOST=192.168.1.100  # Server IP
   ```
4. Run `HotelManagementBot.exe`

### Server Configuration (for remote access):
```bash
# postgresql.conf
listen_addresses = '*'

# pg_hba.conf
host    all    all    0.0.0.0/0    md5

# Firewall
Allow port 5432
```

---

## 👥 User Roles & Onboarding

### Role System:
1. **Admin** (Management Department)
   - Full system access
   - Task creation for all departments
   - Email/WhatsApp bulk sending
   - Report viewing and confirmation
   
2. **Reception** (Receptie Department)
   - Shift report submission
   - Task management
   - Guest room management
   
3. **Department Employees**
   - Task viewing and completion
   - Department-specific features (cleaning, laundry, repair, etc.)

### Adding New User:
1. User sends `/start` to bot
2. Admin receives notification
3. Admin registers user via bot menu:
   - Admin → Manage Employees → Add Employee
   - Enter: Name, Department, Work Role, Email, WhatsApp
4. User automatically assigned to department role

### Departments:
- Management (Admin)
- Receptie (Reception)
- Schoonmaak (Housekeeping)
- Waskamer (Laundry)
- Restaurant
- Chauffeur (Driver)
- Technisch (Technical/Repair)
- Boekhouding (Accounting)

---

## 🔐 Security & Credentials

### Encrypted Credentials Storage:
- **Location**: `tbl_secrets` table
- **Encryption**: Fernet symmetric encryption
- **Master Key**: Auto-generated on first run

### Access Credentials:
1. **Telegram Bot Token**: From @BotFather
2. **OpenAI API Key**: For AI email/WhatsApp generation
3. **Gmail App Password**: 
   - Enable 2-factor authentication
   - Generate app-specific password
4. **Twilio Credentials**:
   - Account SID
   - Auth Token
   - WhatsApp From Number (sandbox: +14155238886)

### Retrieving Stored Credentials:
```python
# Via security_manager
from security_manager import SecurityManager
sm = SecurityManager()
secrets = sm.get_secrets()
# Returns: telegram_token, openai_key, sender_email, app_password
```

---

## 🔍 Monitoring & Logs

### Application Logs:
- **Console Output**: Real-time logging
- **Database Logs**:
  - `tbl_email_logs` - All email attempts (success/failure)
  - `tbl_whatsapp_logs` - All WhatsApp messages
  - `tbl_action_history` - User actions audit log

### Email Logs (Enhanced in v2.2):
```sql
SELECT * FROM tbl_email_logs 
ORDER BY sent_at DESC 
LIMIT 20;
```

Fields:
- `status`: 'sent' | 'failed' | 'queued'
- `smtp_response_code`: SMTP status code (250 = success)
- `smtp_response_message`: SMTP response
- `error_message`: Error details if failed
- `email_size_bytes`: Email size
- `sender_email`, `recipient_name`: Tracking info

### Check System Status:
```bash
# Database connection
python -c "from database import DatabaseManager; db = DatabaseManager(); print(db.connect())"

# Check email logs
python quick_check_logs.py
```

---

## 🛠️ Maintenance Tasks

### Daily:
- Monitor bot responsiveness
- Check email/WhatsApp logs for failures

### Weekly:
- Review overdue tasks escalation
- Check shift report submissions

### Monthly:
- Database backup
- Review performance metrics

### Database Backup:
```bash
pg_dump -U postgres hotel_manage > backup_$(date +%Y%m%d).sql
```

### Database Restore:
```bash
psql -U postgres hotel_manage < backup_20260218.sql
```

---

## 🐛 Troubleshooting

### Bot Not Responding:
1. Check if `main.py` is running
2. Verify Telegram token in database
3. Check internet connection

### Database Connection Failed:
1. Verify PostgreSQL is running
2. Check `.env` DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
3. Test connection: `psql -U postgres -h localhost hotel_manage`

### Email Not Sending:
1. Check `tbl_email_logs` for error messages
2. Verify Gmail app password (not regular password)
3. Test SMTP: `telnet smtp.gmail.com 587`
4. Check firewall/antivirus blocking port 587

### WhatsApp Not Working:
1. Check `tbl_whatsapp_logs` for errors
2. Verify Twilio credentials
3. For Sandbox: User must send "join <code>" first
4. Check Twilio account balance

---

## 📞 Key Contacts & Resources

### External Services:
- **Telegram Bot**: @MySVEN0125_Hotel_ManagerBot
- **Bot Admin**: @SVEN999999
- **OpenAI**: https://platform.openai.com/api-keys
- **Twilio Console**: https://www.twilio.com/console

### Code Repository:
- **Location**: `d:\Work\Telegram-Bot217`
- **Main Files**:
  - `main.py` - Entry point
  - `bot.py` - Bot logic (26,000+ lines)
  - `database.py` - Database operations (11,000+ lines)
  - `notification_manager.py` - Email/WhatsApp sender

---

## 📈 Recent Updates (v2.2)

### Enhanced Email Logging System:
- **Date**: February 18, 2026
- **Changes**:
  1. Expanded `tbl_email_logs` from 6 to 13 columns
  2. Added SMTP response code tracking (250 = success)
  3. Added email size measurement
  4. Added sender/recipient name tracking
  5. Added sent_by_user_id for audit trail
  6. **Fixed**: SMTP connection errors now log all recipients
  7. **Fixed**: All email attempts (success/fail) recorded

### Email Logs UI:
- Simplified display: status, recipient, subject, time, error
- SMTP details stored in DB but hidden from user interface
- Access via: Admin → Email Logs

---

## ✅ System Health Checklist

- [ ] Bot responding to `/start` command
- [ ] Database connection successful
- [ ] Email logs recording (check `tbl_email_logs`)
- [ ] WhatsApp logs recording (check `tbl_whatsapp_logs`)
- [ ] OpenAI API responding (test email generation)
- [ ] Shift reports being submitted
- [ ] Tasks being created and completed
- [ ] Admin notifications working

---

## 📄 End of Technical Handover

**For Questions or Support:**
- Review code comments in main files
- Check error logs in database tables
- Test individual components with test scripts

**System Status**: ✅ Production Ready
**Last Update**: February 18, 2026
