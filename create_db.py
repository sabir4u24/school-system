import MySQLdb

try:
    db = MySQLdb.connect(host="localhost", user="root", passwd="MyPassword@321")
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS school_db CHARACTER SET utf8mb4;")
    print("Database 'school_db' created successfully.")
except Exception as e:
    print(f"Error creating database: {e}")
