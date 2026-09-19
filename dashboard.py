import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import plotly.express as px  
from dotenv import load_dotenv
import os 

load_dotenv()

# Database connection with error handling
def get_connection():
    try:
        return mysql.connector.connect(
           host=os.getenv("DB_HOST"),
           user=os.getenv("DB_USER"),
           password=os.getenv("DB_PASSWORD"),
           database=os.getenv("DB_NAME")
        )
    except mysql.connector.Error as e:
        st.error(f"Database connection failed: {e}")
        return None

# Ensure tables exist
def ensure_tables():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        # Create students table if not exists (adjust columns as needed)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                roll_no VARCHAR(20) UNIQUE
            )
        """)
        # attendance_records is already created in the face recognition code
        conn.commit()
        conn.close()

st.set_page_config(page_title="Smart Attendance Dashboard", layout="wide")

st.title(" Smart Face Attendance Dashboard")

# Ensure tables exist on app start
ensure_tables()

menu = ["View Attendance", "View Students", "Analytics"]
choice = st.sidebar.selectbox("Select Option", menu)

if choice == "View Students":
    st.subheader(" Student Records")
    conn = get_connection()
    if conn:
        try:
            df = pd.read_sql("SELECT * FROM students", conn)
            st.dataframe(df)
        except Exception as e:
            st.error(f" Failed to load students: {e}")
        finally:
            conn.close()

elif choice == "View Attendance":
    st.subheader(" Attendance Records")
    # Add date filter
    selected_date = st.date_input("Select Date", datetime.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    conn = get_connection()
    if conn:
        try:
            query = f"SELECT * FROM attendance_records WHERE date = '{date_str}'"
            df = pd.read_sql(query, conn)
            st.dataframe(df)
            if df.empty:
                st.info("No records for the selected date.")
        except Exception as e:
            st.error(f" Failed to load attendance: {e}")
        finally:
            conn.close()

elif choice == "Analytics":
    st.subheader(" Attendance Analytics")
    # Refresh button
    if st.button("Refresh Data"):
        st.rerun()
    
    today = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
    conn = get_connection()
    if conn:
        try:
            # Get today's attendance
            df_attendance = pd.read_sql(f"SELECT * FROM attendance_records WHERE date = '{today}'", conn)
            # Get total students
            df_students = pd.read_sql("SELECT COUNT(*) as total FROM students", conn)
            total_students = df_students.iloc[0, 0] if not df_students.empty else 0
            
            if total_students > 0:
                present_count = df_attendance['roll_no'].nunique() if not df_attendance.empty else 0
                absent_count = total_students - present_count
                attendance_percentage = (present_count / total_students) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Students", total_students)
                col2.metric("Present Today", present_count)
                col3.metric("Absent Today", absent_count)
                col4.metric("Attendance %", f"{attendance_percentage:.1f}%")
                
                # Pie chart
                fig = px.pie(
                    names=["Present", "Absent"],
                    values=[present_count, absent_count],
                    title="Today's Attendance"
                )
                st.plotly_chart(fig)
            else:
                st.warning("No students found in the database.")
        except Exception as e:
            st.error(f"Failed to load analytics: {e}")
        finally:
            conn.close()
    else:
        st.warning("No attendance data available.")
