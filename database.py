import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
def get_connection():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
        
    )
    return conn

# Test connection
conn = None
try:
    print("Debug: Attempting connection...")
    conn = get_connection()
    print("Connection successful:", conn.is_connected())
except mysql.connector.Error as err:
    print(" MySQL Error:", err)
    print("Debug: Check MySQL server, credentials, and database existence.")
except Exception as e:
    print("Unexpected Error:", e)
    print("Debug: Check network, firewall, or module installation.")
finally:
    if conn:
        conn.close()
        print("Debug: Connection closed.")

get_connection()
