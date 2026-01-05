import csv
import pandas as pd
from collections import defaultdict
import json

def fetch_departments_and_classes():
    """
    Fetch departments and their classes from CSV files.
    Returns a structured dictionary with departments and their associated classes.
    """
    
    csv_file = r'..\file\program_info (4).csv'
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file)
        
        # Dictionary to store departments and their classes
        departments = defaultdict(list)
        
        # Extract unique departments and their programs/classes
        for idx, row in df.iterrows():
            program_id = row['pid']
            program_code = row['pcode']
            program_name = row['pname']
            program_title = row['ptitle']
            program_short = row['pshort']
            batch = row['pbatch']
            status = row['pstatus']
            
            # Extract department from program title
            # Programs are grouped by degree type (B.A., B.Com., B.B.A., B.C.A., B.Sc.)
            degree = program_title.split('-')[0].strip() if pd.notna(program_title) else 'Unknown'
            
            # Create a class object
            class_info = {
                'id': int(program_id),
                'code': program_code,
                'name': program_name,
                'title': program_title,
                'shortName': program_short,
                'batch': batch,
                'status': status
            }
            
            # Add to department
            departments[degree].append(class_info)
        
        # Convert defaultdict to regular dict for JSON serialization
        result = {
            'departments': dict(departments),
            'total_departments': len(departments),
            'total_classes': len(df)
        }
        
        return result
    
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file}")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return None


def fetch_faculty_by_department():
    """
    Fetch faculty information grouped by department from user_info CSV.
    """
    
    csv_file = r'..\file\user_info (2).csv'
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file)
        
        # Dictionary to store departments and their faculty
        faculty_by_dept = defaultdict(list)
        
        # Extract faculty by department
        for idx, row in df.iterrows():
            if pd.isna(row['dept']):
                continue
                
            dept_code = str(row['dept']).strip()
            faculty_info = {
                'userId': int(row['userid']) if pd.notna(row['userid']) else None,
                'empId': str(row['uname']).strip() if pd.notna(row['uname']) else '',
                'name': str(row['fname']).strip() if pd.notna(row['fname']) else '',
                'designation': str(row['desig']).strip() if pd.notna(row['desig']) else '',
                'mobile': str(row['mobile']).strip() if pd.notna(row['mobile']) else '',
                'email': str(row['email']).strip() if pd.notna(row['email']) else '',
                'type': str(row['ugpg']).strip() if pd.notna(row['ugpg']) else ''
            }
            
            faculty_by_dept[dept_code].append(faculty_info)
        
        result = {
            'faculty_by_department': dict(faculty_by_dept),
            'total_departments': len(faculty_by_dept),
            'total_faculty': len(df)
        }
        
        return result
    
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file}")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return None


def print_departments_and_classes():
    """
    Print departments and classes in a readable format.
    """
    
    data = fetch_departments_and_classes()
    
    if data:
        print("\n" + "="*80)
        print("DEPARTMENTS AND CLASSES")
        print("="*80)
        print(f"Total Departments: {data['total_departments']}")
        print(f"Total Classes: {data['total_classes']}\n")
        
        for degree, classes in data['departments'].items():
            print(f"\n{degree}")
            print("-" * 80)
            for cls in classes:
                print(f"  [{cls['code']}] {cls['name']}")
                print(f"      Title: {cls['title']}")
                print(f"      Short: {cls['shortName']}")
                print(f"      Status: {cls['status']} (Batch: {cls['batch']})")
                print()


def print_faculty_by_department():
    """
    Print faculty grouped by department in a readable format.
    """
    
    data = fetch_faculty_by_department()
    
    if data:
        print("\n" + "="*80)
        print("FACULTY BY DEPARTMENT")
        print("="*80)
        print(f"Total Departments: {data['total_departments']}")
        print(f"Total Faculty: {data['total_faculty']}\n")
        
        for dept, faculty_list in data['faculty_by_department'].items():
            print(f"\nDepartment: {dept}")
            print("-" * 80)
            for faculty in faculty_list:
                print(f"  {faculty['name']} (ID: {faculty['empId']})")
                print(f"      Designation: {faculty['designation']}")
                print(f"      Mobile: {faculty['mobile']}")
                print(f"      Email: {faculty['email']}")
                print(f"      Type: {faculty['type']}")
                print()


def export_to_json(filename='departments_and_classes.json'):
    """
    Export departments and classes to JSON file.
    """
    
    data = fetch_departments_and_classes()
    faculty_data = fetch_faculty_by_department()
    
    combined_data = {
        'departments_and_classes': data,
        'faculty_by_department': faculty_data,
        'exported_at': pd.Timestamp.now().isoformat()
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        print(f"\nData exported to {filename}")
        return True
    except Exception as e:
        print(f"Error exporting to JSON: {str(e)}")
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("DEPARTMENT AND CLASS INFORMATION FETCHER")
    print("="*80)
    
    # Print departments and classes
    print_departments_and_classes()
    
    # Print faculty by department
    print_faculty_by_department()
    
    # Export to JSON
    print("\nExporting to JSON...")
    export_to_json()
    
    print("\nDone!")
