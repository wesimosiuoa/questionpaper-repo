from .dbcon import get_connection
class User:
    def __init__(self, fullname, email, pwd, role_id):
        self.fullname = fullname
        self.email = email
        self.pwd = pwd
        self.role_id = role_id
class Course : 
    def __init__(self, title, description, teacher):
        self.title = title
        self.description = description
        self.teacher = teacher
class question_papers: 
# title = title, category = category, instruction = instruction, grade = grade, uploaded_by = uploaded_by, course_id =  course_id, file = file
    def __init__(self, title, category, instruction, grade, uploaded_by, course_id, file, date):
        self.title = title
        self.category = category
        self.instruction = instruction
        self.grade = grade
        self.uploaded_by = uploaded_by
        self.course_id = course_id
        self.file = file  
        self.date = date

class Submission : 
    def __init__ (self, student_id, paper_id, file):
        self.student_id = student_id
        self.paper_id = paper_id
        self.file = file