from student import Student
from google_client import get_sheet_data
import itertools
from itertools import combinations
import math
from statistics import mean
import statistics
import random

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

# --- Parsing students from Google Sheet ---
def parse_students(headers, rows):
    students = []
    col = {name: idx for idx, name in enumerate(headers)}

    for row in rows:
        try:
            get = lambda key: row[col[key]].strip() if key in col and len(row) > col[key] else ""

            name = get("First and Last Name")
            email = get("Email")

            project_ranks = [
                safe_int(get("Ranking for Project 1")),
                safe_int(get("Ranking for Project 2")),
                safe_int(get("Ranking for Project 3")),
                safe_int(get("Ranking for Project 4")),
                safe_int(get("Ranking for Project 5")),
            ]

            teammate_ranks = [
                get(f"{n} Teammate Choice") or get(f"{n} Teammate Choice (First and Last Name)(short answer)") 
                for n in [
                    "First", "Second", "Third", "Fourth", "Fifth",
                    "Sixth", "Seventh", "Eighth", "Nineth", "Tenth"
                ]
            ]

            skills = {
                "frontend": safe_int(get("Skills: Frontend Development ( 1 for Beginner - 5 for Expert )")),
                "backend": safe_int(get("Skills: Backend Development")),
                "database": safe_int(get("Skills: Database")),
                "testing": safe_int(get("Skills: Testing")),
            }

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


# --- Compatibility Scoring ---
def compute_compatibility(s1, s2):
    """Compute compatibility score (0–100) between two students."""
    # Weighted components
    w_project = 0.4
    w_teammate = 0.3
    w_skills = 0.2
    w_avail = 0.1

    # Project rank similarity (lower diff = better)
    proj_diff = sum(abs(a - b) for a, b in zip(s1.project_ranks, s2.project_ranks))
    project_score = 100 - (proj_diff / (5 * 5) * 100)  # normalize

    # Mutual teammate preferences
    mutual_pref = (s2.name in s1.teammate_ranks and s1.name in s2.teammate_ranks)
    teammate_score = 100 if mutual_pref else 50 if (s2.name in s1.teammate_ranks or s1.name in s2.teammate_ranks) else 0

    # Skills similarity
    skill_diff = sum(abs(s1.skills[k] - s2.skills[k]) for k in s1.skills)
    skill_score = 100 - (skill_diff / (4 * 5) * 100)

    # Availability similarity
    avail_diff = abs(s1.availability - s2.availability)
    avail_score = max(0, 100 - (avail_diff / 40 * 100))  # assuming 0–40 hrs range

    total = (
        w_project * project_score +
        w_teammate * teammate_score +
        w_skills * skill_score +
        w_avail * avail_score
    )

    return round(total, 2)


def form_teams(students, num_projects=5):
    """Form exactly num_projects teams (2–3 members) maximizing compatibility with unique projects."""
    n = len(students)
    if n < num_projects * 2:
        raise ValueError(f"Not enough students ({n}) for {num_projects} projects.")

    # Compute all pairwise compatibility scores
    compat = {}
    for s1, s2 in combinations(students, 2):
        compat[(s1.name, s2.name)] = compute_compatibility(s1, s2)

    # Determine target team sizes (mix of 2s and 3s)
    base_size = n // num_projects
    extras = n % num_projects
    team_sizes = [base_size + 1 if i < extras else base_size for i in range(num_projects)]

    remaining = students[:]
    teams = []

    # Greedy assignment: pick highest-compatibility groups first
    for size in team_sizes:
        best_combo = None
        best_score = -1

        for combo in combinations(remaining, size):
            pair_scores = [
                compat.get((a.name, b.name)) or compat.get((b.name, a.name)) or 0
                for a, b in combinations(combo, 2)
            ]
            avg_score = sum(pair_scores) / len(pair_scores)
            if avg_score > best_score:
                best_score = avg_score
                best_combo = combo

        # Remove chosen students
        for s in best_combo:
            remaining.remove(s)

        teams.append({
            "compatibility": round(best_score, 2),
            "members": list(best_combo),
        })

    # --- Unique Project Assignment ---
    # Compute average project preference per team
    project_scores = []
    for t in teams:
        avg_scores = [
            sum(5 - s.project_ranks[i] for s in t["members"]) / len(t["members"])
            for i in range(num_projects)
        ]
        project_scores.append(avg_scores)

    assigned_projects = set()
    for t in teams:
        # Pick highest-ranked project that’s still unassigned
        scores = project_scores.pop(0)
        best_project = None
        best_value = -1
        for i, val in enumerate(scores):
            if (i + 1) not in assigned_projects and val > best_value:
                best_value = val
                best_project = i + 1
        assigned_projects.add(best_project)
        t["project"] = f"{best_project}"

    return teams





# --- Display ---
def print_teams(teams):
    print("\n=== Final Teams ===")
    for i, t in enumerate(teams, start=1):
        print(f"\nTeam {i} | Project {t['project']} | Compatibility: {t['compatibility']}")
        for m in t["members"]:
            print(f" - {m.name} ({m.email})")


# --- Main ---
def main():
    headers, rows = get_sheet_data()
    students = parse_students(headers, rows)

    print(f"Fetched {len(students)} valid survey responses.")
    if not students:
        return

    teams = form_teams(students)
    print_teams(teams)


if __name__ == "__main__":
    main()
