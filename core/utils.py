from .models import Subject, StudentSubject

SUBJECT_MAPPING = {
    'KG': ['English', 'Hindi', 'Mathematics', 'EVS', 'General Knowledge', 'Drawing'],
    '1': ['English', 'Hindi', 'Mathematics', 'EVS', 'General Knowledge', 'Drawing'],
    '2': ['English', 'Hindi', 'Mathematics', 'EVS', 'General Knowledge', 'Drawing'],
    '3': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Computer'],
    '4': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Assamese', 'Computer'],
    '5': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Assamese', 'Computer'],
    '6': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Assamese', 'Computer'],
    '7': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Assamese', 'Computer'],
    '8': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Assamese', 'Computer'],
    '9': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Artificial Intelligence', 'Painting'],
    '10': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Artificial Intelligence', 'Painting'],
    # 9/10 Also "Hindi or Assamese" logic - simplified to just list all potential ones? 
    # Logic says "Hindi OR Assamese", so maybe list both and teacher chooses?
    # User said: "Class 9 and 10: English, Hindi or Assamese, Mathematics, Science, Social Science, Artificial Intelligence, Painting"
    # I'll just ensure these subjects exist.
}

def get_subjects_for_class(class_name):
    """Returns list of Subject names for a given class"""
    if class_name in SUBJECT_MAPPING:
        return SUBJECT_MAPPING[class_name]
    return [] # For 11/12 it's dynamic

def seed_subjects():
    """Ensure all subjects exist in DB"""
    all_subjects = set()
    for subjects in SUBJECT_MAPPING.values():
        all_subjects.update(subjects)
    
    # Add 11/12 subjects
    seniors = ['English', 'Hindi', 'Physics', 'Accountancy', 'Political Science', 'Biology', 'Economics', 'Geography', 'Mathematics', 'Psychology', 'Informatics Practices', 'Computer Science', 'Chemistry', 'Business Studies', 'Sociology', 'Physical Education']
    all_subjects.update(seniors)

    for name in all_subjects:
        Subject.objects.get_or_create(name=name, defaults={'code': name[:3].upper()})

def calculate_grade(percentage):
    if percentage > 90: return 'A1'
    if percentage > 80: return 'A2'
    if percentage > 70: return 'B1'
    if percentage > 60: return 'B2'
    if percentage > 50: return 'C1'
    if percentage > 40: return 'C2'
    if percentage > 32: return 'D'
    return 'E'

def get_remark(grade):
    remarks = {
        'A1': 'EXCELLENT, KEEP IT UP',
        'A2': 'VERY GOOD', # Fixed typo from user req
        'B1': 'GOOD',
        'B2': 'GOOD',
        'C1': 'GOOD EFFORT',
        'C2': 'CAN DO BETTER',
        'D': 'NEEDS IMPROVEMENT',
        'E': 'NEEDS IMPROVEMENT'
    }
    return remarks.get(grade, '')
