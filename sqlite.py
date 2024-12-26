import sqlite3
import pandas as pd
import numpy as np
from typing import List, Dict
import logging
from pathlib import Path
from datetime import datetime, timedelta
import random

class StudentDatabase:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def create_connection(self):
        try:
            return sqlite3.connect(self.db_name)
        except sqlite3.Error as e:
            self.logger.error(f"Error connecting to database: {e}")
            raise

    def create_tables(self):
        tables_info = """
        CREATE TABLE IF NOT EXISTS DEPARTMENTS (
            dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name VARCHAR(50) NOT NULL UNIQUE,
            hod_name VARCHAR(50),
            budget DECIMAL(10, 2)
        );

        CREATE TABLE IF NOT EXISTS COURSES (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name VARCHAR(50) NOT NULL,
            dept_id INTEGER,
            credits INTEGER,
            semester VARCHAR(20),
            FOREIGN KEY (dept_id) REFERENCES DEPARTMENTS(dept_id)
        );

        CREATE TABLE IF NOT EXISTS STUDENT (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE,
            dept_id INTEGER,
            enrollment_date DATE,
            cgpa DECIMAL(3, 2),
            FOREIGN KEY (dept_id) REFERENCES DEPARTMENTS(dept_id)
        );

        CREATE TABLE IF NOT EXISTS GRADES (
            grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            grade CHAR(2),
            semester VARCHAR(20),
            academic_year VARCHAR(9),
            FOREIGN KEY (student_id) REFERENCES STUDENT(student_id),
            FOREIGN KEY (course_id) REFERENCES COURSES(course_id)
        );

        CREATE TABLE IF NOT EXISTS ATTENDANCE (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            date DATE,
            status VARCHAR(10),
            FOREIGN KEY (student_id) REFERENCES STUDENT(student_id),
            FOREIGN KEY (course_id) REFERENCES COURSES(course_id)
        );
        """
        
        with self.create_connection() as conn:
            try:
                conn.executescript(tables_info)
                self.logger.info("Tables created successfully")
            except sqlite3.Error as e:
                self.logger.error(f"Error creating tables: {e}")
                raise

    def generate_sample_data(self):
        departments = [
            ("Computer Science", "Dr. Alan Turing", 500000),
            ("Data Science", "Dr. Geoffrey Hinton", 450000),
            ("Artificial Intelligence", "Dr. Yann LeCun", 600000),
            ("Machine Learning", "Dr. Andrew Ng", 550000)
        ]

        courses = [
            ("Python Programming", 1, 4, "Fall"),
            ("Database Systems", 1, 3, "Spring"),
            ("Deep Learning", 2, 4, "Fall"),
            ("Big Data Analytics", 2, 3, "Spring"),
            ("Neural Networks", 3, 4, "Fall"),
            ("Computer Vision", 3, 3, "Spring"),
            ("Statistical Learning", 4, 4, "Fall"),
            ("Natural Language Processing", 4, 3, "Spring")
        ]

        # Generate 100 sample students
        students = []
        for i in range(1, 101):
            name = f"Student_{i}"
            email = f"student_{i}@university.edu"
            dept_id = random.randint(1, 4)
            date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
            cgpa = round(random.uniform(2.0, 4.0), 2)
            students.append((name, email, dept_id, date, cgpa))

        with self.create_connection() as conn:
            cursor = conn.cursor()
            try:
                # Insert departments
                cursor.executemany(
                    "INSERT OR IGNORE INTO DEPARTMENTS (dept_name, hod_name, budget) VALUES (?, ?, ?)",
                    departments
                )

                # Insert courses
                cursor.executemany(
                    "INSERT OR IGNORE INTO COURSES (course_name, dept_id, credits, semester) VALUES (?, ?, ?, ?)",
                    courses
                )

                # Insert students
                cursor.executemany(
                    "INSERT OR IGNORE INTO STUDENT (name, email, dept_id, enrollment_date, cgpa) VALUES (?, ?, ?, ?, ?)",
                    students
                )

                # Generate grades for each student in various courses
                for student_id in range(1, 101):
                    for course_id in range(1, 9):
                        if random.random() < 0.7:  # 70% chance of having taken the course
                            grade = random.choice(['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F'])
                            semester = random.choice(['Fall', 'Spring'])
                            academic_year = f"2023-2024"
                            cursor.execute(
                                "INSERT INTO GRADES (student_id, course_id, grade, semester, academic_year) VALUES (?, ?, ?, ?, ?)",
                                (student_id, course_id, grade, semester, academic_year)
                            )

                conn.commit()
                self.logger.info("Sample data generated successfully")
            except sqlite3.Error as e:
                self.logger.error(f"Error generating sample data: {e}")
                raise

def main():
    db_path = Path(__file__).parent / "student.db"
    if db_path.exists():
        db_path.unlink()  # Remove existing database
    
    db = StudentDatabase(str(db_path))
    db.create_tables()
    db.generate_sample_data()

if __name__ == "__main__":
    main()
