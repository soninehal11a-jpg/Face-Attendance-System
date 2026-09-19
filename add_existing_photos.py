import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def add_existing_photos():
    folder = "captured_faces"  # Change to absolute path if needed, e.g., "/home/user/captured_faces"
    
    if not os.path.exists(folder):
        print(f" Error: Folder '{folder}' does not exist.")
        return
    
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
        
        files_processed = 0
        for filename in os.listdir(folder):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    # Validate filename format: expect "roll_no_name.ext"
                    parts = filename.split("_", 1)
                    if len(parts) != 2:
                        print(f"Debug: Skipping invalid filename '{filename}' (expected 'roll_no_name.ext').")
                        continue
                    
                    roll_no = parts[0]
                    name_ext = parts[1]
                    name = os.path.splitext(name_ext)[0]
                    image_path = os.path.join(folder, filename)
                    
                    print(f"Debug: Inserting {name} (roll: {roll_no})...")
                    cursor.execute("""
                        INSERT IGNORE INTO students (name, roll_no, image_path)
                        VALUES (%s, %s, %s)
                    """, (name, roll_no, image_path))
                    files_processed += 1
                    
                except ValueError as ve:
                    print(f"Debug: Filename parsing error for '{filename}': {ve}")
                except Exception as e:
                    print(f"Debug: Error processing '{filename}': {e}")
        
        conn.commit()
        print(f" Processed {files_processed} photos successfully!")
        
    except mysql.connector.Error as err:
        print(f" MySQL Error: {err}")
        print("Debug: Check connection, permissions, or table existence.")
    except Exception as e:
        print(f" Unexpected Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print("Debug: Connection closed.")

add_existing_photos()
