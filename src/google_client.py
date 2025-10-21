
"""
google_client.py
----------------
If Google credentials are configured (see config.py), this module will read survey data and write
results to a Google Sheet. If not configured, it falls back to reading/writing local CSV files:

- Input fallback:  src/data/survey.csv
- Output fallback: src/data/team_results.csv
"""
from __future__ import annotations
import csv, os, datetime
from typing import List, Dict, Any
from src.config import SURVEY_SPREADSHEET_ID, RESULTS_SPREADSHEET_ID, GOOGLE_APPLICATION_CREDENTIALS


# Try to import google API, but allow fallback
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_OK = True
except Exception:
    GOOGLE_OK = False

SRC_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(SRC_DIR, "data")

def _creds_and_service():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_APPLICATION_CREDENTIALS, scopes=scopes
    )
    service = build("sheets", "v4", credentials=creds)
    return creds, service

def get_sheet_data(sheet_name: str = "Form Responses 1") -> List[Dict[str, Any]]:
    """
    Returns a list of dict rows representing the survey.
    Columns expected (example): name,email,project_ranks,teammate_ranks,skills,availability,workstyle,meeting_pref
    Fallback to src/data/survey.csv if Google is not configured.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    if GOOGLE_OK and os.path.isfile(GOOGLE_APPLICATION_CREDENTIALS) and SURVEY_SPREADSHEET_ID != "YOUR_SURVEY_SPREADSHEET_ID_HERE":
        try:
            _, service = _creds_and_service()
            sheet = service.spreadsheets()
            rng = f"'{sheet_name}'!A1:Z1000"
            result = sheet.values().get(spreadsheetId=SURVEY_SPREADSHEET_ID, range=rng).execute()
            values = result.get("values", [])
            if not values:
                return []
            headers = [h.strip().lower() for h in values[0]]
            rows = []
            for row in values[1:]:
                item = {headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))}
                rows.append(item)
            return rows
        except Exception:
            pass

    # Fallback to local CSV
    csv_path = os.path.join(DATA_DIR, "survey.csv")
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_team_results(teams: List[list], sheet_name: str = "Team Matching Results") -> bool:
    """
    Writes organized team results to Google Sheets if configured, otherwise to CSV at src/data/team_results.csv
    """
    rows = []
    now = datetime.datetime.now().isoformat(timespec="seconds")
    for i, team in enumerate(teams, start=1):
        rows.append([f"Team {i}", "", "", f"Generated at {now}"])
        rows.append(["Name", "Email", "Skills (avg)", "Availability", "Workstyle", "Meeting Pref"])
        for s in team:
            skills = getattr(s, "skills", {}) or {}
            avg_skill = round(sum(skills.values())/len(skills), 2) if skills else 0
            rows.append([getattr(s,"name",""), getattr(s,"email",""), avg_skill, getattr(s,"availability",""),
                         getattr(s,"workstyle",""), getattr(s,"meeting_pref","")])
        rows.append(["", "", "", ""])

    if GOOGLE_OK and os.path.isfile(GOOGLE_APPLICATION_CREDENTIALS) and RESULTS_SPREADSHEET_ID != "YOUR_RESULTS_SPREADSHEET_ID_HERE":
        try:
            _, service = _creds_and_service()
            sheet = service.spreadsheets()
            body = {"values": rows}
            sheet.values().update(
                spreadsheetId=RESULTS_SPREADSHEET_ID,
                range=f"'{sheet_name}'!A1",
                valueInputOption="RAW",
                body=body
            ).execute()
            return True
        except Exception:
            pass

    # Fallback CSV
    os.makedirs(DATA_DIR, exist_ok=True)
    out_csv = os.path.join(DATA_DIR, "team_results.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return True
