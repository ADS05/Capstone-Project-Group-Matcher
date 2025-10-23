
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
from config import SURVEY_SPREADSHEET_ID, RESULTS_SPREADSHEET_ID, GOOGLE_APPLICATION_CREDENTIALS


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
    from datetime import datetime
    
    # Prepare organized data
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_data = []
    
    # Add header with timestamp
    all_data.append([f"Capstone Team Matching Results - Generated: {timestamp}"])
    all_data.append([])  # Empty row
    
    for team_num, team in enumerate(teams, 1):
        # Team header
        all_data.append([f"TEAM {team_num} - PROJECT {team.get('project', 'N/A')} - Compatibility: {team.get('compatibility', 'N/A')}"])
        all_data.append([])  # Empty row
        
        # Team member details
        for member in team['members']:
            # Member name and email
            all_data.append([f"👤 {member.name} ({member.email})"])
            
            # Skills breakdown
            skills_str = f"Frontend: {member.skills['frontend']}/5, Backend: {member.skills['backend']}/5, Database: {member.skills['database']}/5, Testing: {member.skills['testing']}/5"
            all_data.append([f"   Skills: {skills_str}"])
            
            # Project preferences
            project_prefs = []
            for i, rank in enumerate(member.project_ranks):
                if rank > 0:
                    project_prefs.append(f"Project {i+1} (Rank {rank})")
            all_data.append([f"   Project Preferences: {', '.join(project_prefs) if project_prefs else 'None specified'}"])
            
            # Availability and preferences
            all_data.append([f"   Availability: {member.availability} hours/week"])
            all_data.append([f"   Workstyle: {member.workstyle}"])
            all_data.append([f"   Meeting Preference: {member.meeting_pref}"])
            
            # Teammate preferences
            teammate_prefs = [pref for pref in member.teammate_ranks if pref.strip()]
            if teammate_prefs:
                all_data.append([f"   Preferred Teammates: {', '.join(teammate_prefs[:3])}{'...' if len(teammate_prefs) > 3 else ''}"])
            
            all_data.append([])  # Empty row after each member
        
        all_data.append(["─" * 50])  # Separator line
        all_data.append([])  # Empty row after each team

    if GOOGLE_OK and os.path.isfile(GOOGLE_APPLICATION_CREDENTIALS) and RESULTS_SPREADSHEET_ID != "YOUR_RESULTS_SPREADSHEET_ID_HERE":
        try:
            _, service = _creds_and_service()
            sheet = service.spreadsheets()
            
            # Create the new sheet
            try:
                # Check if sheet already exists
                spreadsheet = sheet.get(spreadsheetId=RESULTS_SPREADSHEET_ID).execute()
                existing_sheets = [s['properties']['title'] for s in spreadsheet['sheets']]
                
                if sheet_name in existing_sheets:
                    print(f"Sheet '{sheet_name}' already exists. Updating...")
                else:
                    # Create new sheet
                    add_sheet_request = {
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    }
                    sheet.batchUpdate(
                        spreadsheetId=RESULTS_SPREADSHEET_ID,
                        body={'requests': [add_sheet_request]}
                    ).execute()
                    print(f"Created new sheet: {sheet_name}")
            except Exception as e:
                print(f"Error creating/accessing sheet: {e}")
                return False
            
            # Write data to sheet
            try:
                range_name = f"{sheet_name}!A1"
                body = {'values': all_data}
                
                result = sheet.values().update(
                    spreadsheetId=RESULTS_SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                print(f"Successfully wrote organized team results to {sheet_name}")
                return True
                
            except Exception as e:
                print(f"Error writing to sheet: {e}")
                return False
                
        except Exception as e:
            print(f"Google Sheets error: {e}")
            return False

    # Fallback CSV
    os.makedirs(DATA_DIR, exist_ok=True)
    out_csv = os.path.join(DATA_DIR, "team_results.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(all_data)
    print(f"Fallback: Saved results to {out_csv}")
    return True
