from __future__ import annotations
from typing import List, Dict, Any
from student import Student
from google_client import get_sheet_data, write_team_results
from ml_matching import AIMatcher, compute_team_features
from tui import interactive_loop


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
    """Parse students from Google Sheets data using original format"""
    students = []
    col = {name: idx for idx, name in enumerate(headers)}

    for row in rows:
        try:
            # Safely get cell value
            get = lambda key: row[col[key]].strip() if key in col and len(row) > col[key] else ""

            name = get("first and last name")
            email = get("email")

            # Project rankings (handle blanks)
            project_ranks = [
                safe_int(get("ranking for project 1 (1 for lowest rank - 5 for highest rank)")),
                safe_int(get("ranking for project 2")),
                safe_int(get("ranking for project 3")),
                safe_int(get("ranking for project 4")),
                safe_int(get("ranking for project 5")),
            ]

            # Teammate preferences (handle alternate field names)
            teammate_ranks = [
                get(f"{n} teammate choice") or get(f"{n} teammate choice (first and last name)(short answer)") 
                for n in [
                    "first", "second", "third", "fourth", "fifth",
                    "sixth", "seventh", "eighth", "nineth", "tenth"
                ]
            ]

            # Skills (handle blanks)
            skills = {
                "frontend": safe_int(get("skills: frontend development ( 1 for beginner - 5 for expert )")),
                "backend": safe_int(get("skills: backend development")),
                "database": safe_int(get("skills: database")),
                "testing": safe_int(get("skills: testing")),
            }

            # Availability, workstyle, meeting preference
            availability = safe_float(get("hours available (short answer)"))
            workstyle = get("workstyle")
            meeting_pref = get("meeting preference")

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
    from itertools import combinations
    import random
    
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
            sum(s.project_ranks[i] for s in t["members"]) / len(t["members"])
            for i in range(num_projects)
        ]
        project_scores.append(avg_scores)

    assigned_projects = set()
    for t in teams:
        # Pick highest-ranked project that's still unassigned
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

def print_teams(teams):
    for i, t in enumerate(teams, start=1):
        print(f"\nTeam {i} | Project {t['project']} | Compatibility: {t['compatibility']}")
        for m in t["members"]:
            print(f" - {m.name} ({m.email})")

def main():
    # Fetch and parse student data
    rows = get_sheet_data()
    if not rows:
        print("No survey data found.")
        return
    
    # Convert dict format to headers/rows format for parse_students
    if isinstance(rows, list) and len(rows) > 0 and isinstance(rows[0], dict):
        # Convert dict format to headers/rows format
        headers = list(rows[0].keys())
        rows_data = []
        for row_dict in rows:
            row_list = []
            for header in headers:
                row_list.append(row_dict.get(header, ""))
            rows_data.append(row_list)
    else:
        print("Invalid data format from get_sheet_data()")
        return
        
    students = parse_students(headers, rows_data)

    print(f"Fetched {len(students)} valid survey responses.")
    if not students:
        return

    # Use original team formation algorithm
    teams = form_teams(students)
    
    # --- Feature 9: Interactive Manual TUI adjustments ---
    
    # Convert teams format for TUI
    team_lists = [team["members"] for team in teams]
    
    # Check if interactive mode is enabled
    import sys
    interactive_mode = "--interactive" in sys.argv or "-i" in sys.argv
    
    if interactive_mode:
        # Run full interactive TUI
        print("\n🎯 INTERACTIVE WORKFLOW ACTIVATED:")
        print("\nIn interactive mode, faculty can use commands like:")
        print("  • 'l' to list teams")
        print("  • 'm' to move students")
        print("  • 's' to show scores") 
        print("  • 'w' to check warnings")
        print("  • 'd' to finalize and export")
        print("  • 'q' to quit without saving")
        print(" ")
        print("Curent Groups and AI-Computed Compatibility Scores:")
        print(" ")
        should_export = interactive_loop(teams, team_lists)

    else:
        # Demo mode - show capabilities without interactive input
        print("\n🎯 INTERACTIVE WORKFLOW NOT ACTIVATED:")
        print("To enable full interactive mode, run: python3 src/main.py --interactive")
        
        # Simulate the workflow
        print("\n📋 Current teams with AI compatibility scores:")
        from tui import list_teams, recalc_scores, warn_low_scores
        scores = recalc_scores(team_lists)
        print(list_teams(team_lists, scores))
        
        # Check for warnings
        warnings = warn_low_scores(team_lists, scores)
        if warnings:
            print("\n⚠️  Compatibility Warnings:")
            for w in warnings:
                print(f"   {w}")
        else:
            print("\n✅ No compatibility warnings - all teams look good!")
        
        # Simulate finalizing
        should_export = True  # Simulate faculty choosing to export
    
    if should_export:
        # Convert back to original format for export
        final_teams = []
        for i, team_list in enumerate(team_lists):
            final_teams.append({
                "compatibility": teams[i]["compatibility"],
                "members": team_list,
                "project": teams[i]["project"]
            })

        # After adjustments, print final and write results
        print("\n" + "="*50)
        print("📊 FINAL TEAM ASSIGNMENTS")
        print("="*50)
        print_teams(final_teams)

        # Export results to Google Sheets
        print("\n=== Exporting to Google Sheets ===")
        success = write_team_results(final_teams, "Team Matching Results")
        
        if success:
            print("✅ Successfully exported team matching results to Google Sheets!")
            print("📋 Faculty can now view the results in the 'Team Matching Results' sheet.")
        else:
            print("❌ Failed to export results to Google Sheets.")
            print("Please check your Google Sheets credentials and permissions.")
    else:
        print("\n👋 Exiting without exporting changes.")

if __name__ == "__main__":
    main()
