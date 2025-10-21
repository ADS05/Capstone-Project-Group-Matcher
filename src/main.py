from __future__ import annotations
from typing import List, Dict, Any
from src.student import Student
from src.google_client import get_sheet_data, write_team_results
from src.ml_matching import AIMatcher, compute_team_features
from src.tui import interactive_loop


def parse_students(rows: List[Dict[str, Any]]) -> List[Student]:
    students = []
    for r in rows:
        name = r.get("name") or r.get("student name") or r.get("full name") or ""
        email = r.get("email") or ""
        # project ranks as comma-separated integers "1,3,2"
        pr = r.get("project_ranks") or r.get("project preferences") or ""
        project_ranks = []
        for tok in str(pr).replace(";", ",").split(","):
            tok = tok.strip()
            if tok.isdigit():
                project_ranks.append(int(tok))
        # teammate ranks as comma-separated names
        tr = r.get("teammate_ranks") or r.get("preferred teammates") or ""
        teammate_ranks = [t.strip() for t in str(tr).replace(";", ",").split(",") if t.strip()]
        # skills as key:level;key:level
        skills_text = r.get("skills") or ""
        skills = {}
        for part in str(skills_text).split(","):
            if ":" in part:
                k, v = part.split(":", 1)
                try:
                    skills[k.strip()] = int(v.strip())
                except Exception:
                    continue
        try:
            availability = float(r.get("availability", 0))
        except Exception:
            availability = 0.5
        workstyle = r.get("workstyle", "")
        meeting_pref = r.get("meeting_pref", "")
        students.append(Student(name, email, project_ranks, teammate_ranks, skills, availability, workstyle, meeting_pref))
    return students

def greedy_group(students: List[Student], team_size: int = 4) -> List[List[Student]]:
    # Simple baseline grouping: chunk into equal-sized teams
    teams = []
    cur = []
    for s in students:
        cur.append(s)
        if len(cur) == team_size:
            teams.append(cur)
            cur = []
    if cur:
        teams.append(cur)
    return teams

def score_teams(teams: List[List[Student]]) -> List[float]:
    matcher = AIMatcher()
    scores = []
    for team in teams:
        feats = compute_team_features(team)
        scores.append(matcher.score_team(feats))
    return scores

def print_teams(teams: List[List[Student]]) -> None:
    scores = score_teams(teams)
    for i, (team, sc) in enumerate(zip(teams, scores), start=1):
        print(f"\nTeam {i} (score={sc:.3f}):")
        for s in team:
            print(f"  - {s.name} <{s.email}> skills={s.skills} avail={s.availability} workstyle={s.workstyle} meeting={s.meeting_pref}")

def main():
    print("Loading survey data...")
    rows = get_sheet_data()
    if not rows:
        print("No survey rows found. Put a CSV at src/data/survey.csv or configure Google Sheets (see README).")
        return
    students = parse_students(rows)
    if not students:
        print("Parsed zero students. Check your column headers in the survey sheet/CSV.")
        return

    # Baseline grouping (you can replace with a more advanced optimizer later)
    teams = greedy_group(students, team_size=4)
    print_teams(teams)

    # --- Feature 9: Manual TUI adjustments ---
    print("\nEnter the manual adjustment interface (Feature 9).")
    interactive_loop(teams)

    # After adjustments, print final and write results
    print("\nFinal teams:")
    print_teams(teams)

    print("\nExporting results...")
    ok = write_team_results(teams, sheet_name="Team Matching Results")
    print("Export:", "Success" if ok else "Failed")

if __name__ == "__main__":
    main()
