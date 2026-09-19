import cv2
import face_recognition
import os
import numpy as np
import mysql.connector
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

# Database connection
def get_connection():
    try:
        # TODO: Use environment variables for security (e.g., os.getenv('DB_PASSWORD'))
        return mysql.connector.connect(
           host=os.getenv("DB_HOST"),
           user=os.getenv("DB_USER"),
           password=os.getenv("DB_PASSWORD"),
           database=os.getenv("DB_NAME")
        )
    except mysql.connector.Error as e:
        print(f"Database connection failed: {e}")
        return None

# Mark attendance
def mark_attendance(conn, cursor, name, roll_no, marked_students):
    if roll_no in marked_students:
        return
    
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    print("CURRENT TIME:", now)
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    
    # Check for existing record on the same date to prevent duplicates
    cursor.execute(
        "SELECT id FROM attendance_records WHERE roll_no = %s AND date = %s",
        (roll_no, date)
    )
    if cursor.fetchone():
        print(f"Attendance already marked for {name} ({roll_no}) on {date}")
        return
    
    try:
        cursor.execute(
            "INSERT INTO attendance_records (name, roll_no, date, time) VALUES (%s, %s, %s, %s)",
            (name, roll_no, date, time)
        )
        conn.commit()  # Commit immediately after insert
        marked_students.add(roll_no)
        print(f"Attendance marked for {name} ({roll_no}) at {time}")
    except mysql.connector.Error as e:
        print(f"Failed to mark attendance for {name} ({roll_no}): {e}")

# Load known faces
def load_known_faces():
    known_faces = []
    known_names = []
    known_rolls = []
    
    path = "captured_faces"
    if not os.path.exists(path):
        print(f"Directory '{path}' does not exist. Please create it and add face images.")
        return known_faces, known_names, known_rolls
    
    for filename in os.listdir(path):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            if "_" not in filename:
                print(f"Skipping {filename}: Invalid format (expected 'roll_no_name.jpg')")
                continue
            
            try:
                roll_no, name_with_ext = filename.split("_", 1)
                name = os.path.splitext(name_with_ext)[0]
                
                img_path = os.path.join(path, filename)
                img = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(img)
                
                if len(encodings) == 0:
                    print(f"No face found in {filename}")
                elif len(encodings) > 1:
                    print(f"Multiple faces in {filename}, using the first one")
                    known_faces.append(encodings[0])
                    known_names.append(name)
                    known_rolls.append(roll_no)
                    print(f"Loaded: {name} ({roll_no})")
                else:
                    known_faces.append(encodings[0])
                    known_names.append(name)
                    known_rolls.append(roll_no)
                    print(f"Loaded: {name} ({roll_no})")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return known_faces, known_names, known_rolls

# Start recognition
def start_recognition():
    known_faces, known_names, known_rolls = load_known_faces()
    
    if not known_faces:
        print("No known faces loaded. Exiting.")
        return
    
    conn = get_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                roll_no VARCHAR(20),
                date DATE,
                time TIME
            )
        """)
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Failed to create table: {e}")
        conn.close()
        return
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open camera.")
        conn.close()
        return
    
    marked_students = set()
    print("Starting face recognition. Press 'q' to exit...")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from camera.")
                break
            
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.45)  # Tune tolerance if needed
                face_distances = face_recognition.face_distance(known_faces, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    name = known_names[best_match_index]
                    roll_no = known_rolls[best_match_index]
                    mark_attendance(conn, cursor, name, roll_no, marked_students)
                    color = (0, 255, 0)
                    text = f"{name} ({roll_no})"
                else:
                    color = (0, 0, 255)
                    text = "Unknown"
                
                y1, x2, y2, x1 = [v * 4 for v in face_location]
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            cv2.imshow("Face Attendance (Accurate)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e:
        print(f"Error during recognition: {e}")
    finally:
        conn.close()
        cap.release()
        cv2.destroyAllWindows()
        print("Session ended.")

if __name__ == "__main__":
    start_recognition()
