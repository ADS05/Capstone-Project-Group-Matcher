
"""
tui.py
Feature 9: Manual Team Adjustments via keyboard
-----------------------------------------------
A lightweight terminal TUI to:
- View teams and scores
- Move a student between teams (manual override)
- Recalculate compatibility scores after moves
- Warn if a manual move creates a low-compatibility team

Controls (fallback non-curses):
- l : list teams
- m : move student (you will be prompted: student name, from team, to team)
- s : show scores
- w : run warnings (low-compatibility)
- q : quit

If curses is available you can later upgrade to a full-screen UI; this module isolates the logic.
"""
from __future__ import annotations
from typing import List, Dict, Tuple
import statistics
from src.ml_matching import AIMatcher, compute_team_features


LOW_SCORE_THRESHOLD = 0.45  # warn on teams scoring below this after manual changes

def recalc_scores(teams: List[List[object]]) -> List[float]:
    matcher = AIMatcher()
    scores = []
    for team in teams:
        feats = compute_team_features(team)
        scores.append(matcher.score_team(feats))
    return scores

def list_teams(teams: List[List[object]], scores: List[float] | None = None) -> str:
    out = []
    for i, t in enumerate(teams):
        score_str = f" (score={scores[i]:.3f})" if scores else ""
        out.append(f"Team {i+1}{score_str}: " + ", ".join(getattr(s, 'name', '?') for s in t))
    return "\n".join(out)

def warn_low_scores(teams: List[List[object]], scores: List[float]) -> List[str]:
    warnings = []
    for i, sc in enumerate(scores):
        if sc < LOW_SCORE_THRESHOLD:
            warnings.append(f"Warning: Team {i+1} compatibility score {sc:.3f} is below {LOW_SCORE_THRESHOLD:.2f}.")
    return warnings

def move_student(teams: List[List[object]], student_name: str, from_idx: int, to_idx: int) -> bool:
    if from_idx < 0 or from_idx >= len(teams) or to_idx < 0 or to_idx >= len(teams):
        return False
    team_from = teams[from_idx]
    team_to = teams[to_idx]
    pos = next((i for i, s in enumerate(team_from) if getattr(s, "name", "").lower() == student_name.lower()), None)
    if pos is None:
        return False
    team_to.append(team_from.pop(pos))
    return True

def interactive_loop(teams: List[List[object]]) -> None:
    print("\n--- Manual Team Adjustment TUI ---")
    print("Controls: l=list, m=move, s=scores, w=warnings, q=quit")
    scores = recalc_scores(teams)
    print(list_teams(teams, scores))

    while True:
        cmd = input("\nCommand (l/m/s/w/q): ").strip().lower()
        if cmd == "q":
            break
        elif cmd == "l":
            print(list_teams(teams, scores))
        elif cmd == "s":
            scores = recalc_scores(teams)
            print(list_teams(teams, scores))
        elif cmd == "w":
            scores = recalc_scores(teams)
            for w in warn_low_scores(teams, scores):
                print(w)
            if not warn_low_scores(teams, scores):
                print("No warnings.")
        elif cmd == "m":
            try:
                name = input("Student name to move: ").strip()
                from_team = int(input("From team number: ")) - 1
                to_team = int(input("To team number: ")) - 1
                ok = move_student(teams, name, from_team, to_team)
                if not ok:
                    print("Move failed (check names/team numbers).")
                else:
                    scores = recalc_scores(teams)
                    print("Moved.\n" + list_teams(teams, scores))
                    for w in warn_low_scores(teams, scores):
                        print(w)
            except Exception as e:
                print("Invalid input.", e)
        else:
            print("Unknown command.")
