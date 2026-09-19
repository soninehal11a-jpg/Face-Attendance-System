import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    conn = None
    cursor = None
    try:
        print("Debug: Connecting to database...")
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
            
        )
        cursor = conn.cursor()
        
        print("Debug: Creating students table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                roll_no VARCHAR(50) UNIQUE,
                image_path VARCHAR(255)
            )
        """)
        
        print("Debug: Creating attendance table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT,
                date DATE,
                time TIME,
                status VARCHAR(10),
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)
        
        conn.commit()
        print(" Tables created successfully!")
        
    except mysql.connector.Error as err:
        print(f" MySQL Error: {err}")
        print("Debug: Check connection, permissions, or database existence.")
    except Exception as e:
        print(f" Unexpected Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print("Debug: Connection closed.")

create_tables()
