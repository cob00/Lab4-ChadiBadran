
from __future__ import annotations
from typing import List, Optional, Dict, Tuple
import json
import re


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _validate_email(email: str) -> str:
    if not isinstance(email, str):
        raise ValueError("Email must be a string.")
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValueError("Invalid email format.")
    return email

def _validate_age(age: int) -> int:
    if not isinstance(age, int):
        raise ValueError("Age must be an integer.")
    if age > 100 :
        raise ValueError("Age must be in normal range")
    if age < 0:
        raise ValueError("Age must be non-negative.")
    return age

def _validate_nonempty(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return value.strip()


class Person:
    def __init__(self, name: str, age: int, email: str):
        self.name = _validate_nonempty(name, "name")
        self.age = _validate_age(age)
        self._email = _validate_email(email)

    def introduce(self) -> None:
        print(f"Hi, I'm {self.name}, and I'm {self.age} years old.")

 
    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        self._email = _validate_email(value)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "age": self.age,
            "_email": self._email,
        }

    @classmethod
    def _from_base_dict(cls, data: dict) -> Tuple[str, int, str]:
        return data["name"], data["age"], data["_email"]


class Student(Person):
    def __init__(self, name: str, age: int, email: str, student_id: str):
        super().__init__(name, age, email)
        self.student_id = _validate_nonempty(student_id, "student_id")
        self.registered_courses: List[Course] = []

    def register_course(self, course: 'Course') -> None:
        if course not in self.registered_courses:
            self.registered_courses.append(course)
            if self not in course.enrolled_students:
                course.enrolled_students.append(self)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "student_id": self.student_id,
            "registered_courses": [c.course_id for c in self.registered_courses],
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> 'Student':
        name, age, email = Person._from_base_dict(data)
        s = cls(name, age, email, data["student_id"])
        return s


class Instructor(Person):
    def __init__(self, name: str, age: int, email: str, instructor_id: str):
        super().__init__(name, age, email)
        self.instructor_id = _validate_nonempty(instructor_id, "instructor_id")
        self.assigned_courses: List[Course] = []

    def assign_course(self, course: 'Course') -> None:
        if course not in self.assigned_courses:
            self.assigned_courses.append(course)
            if course.instructor is not self:
                course.instructor = self


    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "instructor_id": self.instructor_id,
            "assigned_courses": [c.course_id for c in self.assigned_courses],
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> 'Instructor':
        name, age, email = Person._from_base_dict(data)
        i = cls(name, age, email, data["instructor_id"])
        return i


class Course:
    def __init__(self, course_id: str, course_name: str, instructor: Optional[Instructor] = None):
        self.course_id = _validate_nonempty(course_id, "course_id")
        self.course_name = _validate_nonempty(course_name, "course_name")
        self.instructor: Optional[Instructor] = None
        self.enrolled_students: List[Student] = []

        if instructor:
            self.set_instructor(instructor)

    def set_instructor(self, instructor: Instructor) -> None:
        self.instructor = instructor
        instructor.assign_course(self)

    def add_student(self, student: Student) -> None:
        if student not in self.enrolled_students:
            self.enrolled_students.append(student)
            if self not in student.registered_courses:
                student.register_course(self)

    def __repr__(self) -> str:
        return f"Course({self.course_id}, {self.course_name})"

    def to_dict(self) -> dict:
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "instructor_id": self.instructor.instructor_id if self.instructor else None,
            "enrolled_students": [s.student_id for s in self.enrolled_students],
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Course':
        c = cls(course_id=data["course_id"], course_name=data["course_name"], instructor=None)
        return c


def save_to_json(
    path: str,
    students: List[Student],
    instructors: List[Instructor],
    courses: List[Course],
) -> None:
    payload = {
        "students": [s.to_dict() for s in students],
        "instructors": [i.to_dict() for i in instructors],
        "courses": [c.to_dict() for c in courses],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_from_json(path: str) -> Tuple[Dict[str, Student], Dict[str, Instructor], Dict[str, Course]]:
    """
    Returns (students_by_id, instructors_by_id, courses_by_id) with all relationships re-linked.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    students_by_id: Dict[str, Student] = {}
    instructors_by_id: Dict[str, Instructor] = {}
    courses_by_id: Dict[str, Course] = {}

    for sd in data.get("students", []):
        s = Student.from_dict(sd)
        students_by_id[s.student_id] = s

    for idd in data.get("instructors", []):
        i = Instructor.from_dict(idd)
        instructors_by_id[i.instructor_id] = i

    for cd in data.get("courses", []):
        c = Course.from_dict(cd)
        courses_by_id[c.course_id] = c

    for cd in data.get("courses", []):
        c = courses_by_id[cd["course_id"]]

  
        inst_id = cd.get("instructor_id")
        if inst_id:
            inst = instructors_by_id.get(inst_id)
            if inst:
                c.set_instructor(inst)


        for sid in cd.get("enrolled_students", []):
            s = students_by_id.get(sid)
            if s:
                c.add_student(s)


    return students_by_id, instructors_by_id, courses_by_id
