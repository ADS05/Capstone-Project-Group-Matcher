from student import Student
from google_client import get_sheet_data

# --- Utility converters ---
def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def parse_students(headers, rows):
    students = []
    col = {name: idx for idx, name in enumerate(headers)}

    for row in rows:
        try:
            # Safely get cell value
            get = lambda key: row[col[key]].strip() if key in col and len(row) > col[key] else ""

            name = get("First and Last Name")
            email = get("Email")

            # Project rankings (handle blanks)
            project_ranks = [
                safe_int(get("Ranking for Project 1")),
                safe_int(get("Ranking for Project 2")),
                safe_int(get("Ranking for Project 3")),
                safe_int(get("Ranking for Project 4")),
                safe_int(get("Ranking for Project 5")),
            ]

            # Teammate preferences (handle alternate field names)
            teammate_ranks = [
                get(f"{n} Teammate Choice") or get(f"{n} Teammate Choice (First and Last Name)(short answer)") 
                for n in [
                    "First", "Second", "Third", "Fourth", "Fifth",
                    "Sixth", "Seventh", "Eighth", "Nineth", "Tenth"
                ]
            ]

            # Skills (handle blanks)
            skills = {
                "frontend": safe_int(get("Skills: Frontend Development ( 1 for Beginner - 5 for Expert )")),
                "backend": safe_int(get("Skills: Backend Development")),
                "database": safe_int(get("Skills: Database")),
                "testing": safe_int(get("Skills: Testing")),
            }

            # Availability, workstyle, meeting preference
            availability = safe_float(get("Hours Available (short answer)"))
            workstyle = get("Workstyle")
            meeting_pref = get("Meeting Preference")

            students.append(Student(
                name, email, project_ranks, teammate_ranks, skills,
                availability, workstyle, meeting_pref
            ))

        except Exception as e:
            print(f"Error parsing row: {e}")

    return students


def main():
    headers, rows = get_sheet_data()
    students = parse_students(headers, rows)

    print(f"Fetched {len(students)} valid survey responses.")
    print("\n=== Parsed Students ===")
    for s in students:
        print(s)


if __name__ == "__main__":
    main()
