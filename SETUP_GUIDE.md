# School Management System - Setup Guide

Follow these steps to run this application on a new computer.

### 1. Prerequisites
- **Python**: Install Python 3.10 or higher from [python.org](https://www.python.org/).
- **MySQL Server**: Install MySQL Community Server.

### 2. Database Setup
1. Open your MySQL Command Line Client or Workbench.
2. Create the database:
   ```sql
   CREATE DATABASE school_db;
   ```
3. (Optional) If you want to transfer your existing data:
   - On the OLD PC: Run `mysqldump -u root -p school_db > backup.sql`
   - On the NEW PC: Run `mysql -u root -p school_db < backup.sql`

### 3. Project Configuration
1. Copy the entire `AdmResApp` folder to the new computer.
2. Open the folder in a terminal (Command Prompt or PowerShell).
3. **Database Credentials**: Open `school_system/settings.py` and check the `DATABASES` section. 
   - Update the `'PASSWORD'` if your new MySQL password is different.

### 4. Install Dependencies
Run the following command in the terminal to install all required libraries:
```bash
pip install -r requirements.txt
```

### 5. Initialize the App
If you imported a backup SQL file (Step 2.3), skip this.
If you are starting fresh (no data), run these commands:
```bash
python manage.py migrate
python seed_users.py
```
*(This creates the database tables and default admin/teacher/staff users)*

### 6. Run the Server
Start the application:
```bash
python manage.py runserver
```
Access the app at `http://127.0.0.1:8000/`.
