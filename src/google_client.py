import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import GOOGLE_APPLICATION_CREDENTIALS

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_service():
    creds_path = GOOGLE_APPLICATION_CREDENTIALS
    credentials = service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=credentials)

def get_sheet_data():
    from config import SURVEY_SPREADSHEET_ID
    spreadsheet_id = SURVEY_SPREADSHEET_ID
    service = get_service()
    sheet = service.spreadsheets()
    
    # Adjust the range name if your sheet tab differs
    range_name = "Form Responses 1!A:Z"
    
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id, range=range_name
    ).execute()
    
    values = result.get("values", [])
    if not values:
        print("No data found.")
        return []

    headers = values[0]
    rows = values[1:]
    print(f"Fetched {len(rows)} survey responses.")
    return headers, rows

def write_team_results(team_results, sheet_name="Team Matching Results"):
    """Write team matching results in organized team sections"""
    from datetime import datetime
    from config import RESULTS_SPREADSHEET_ID
    
    spreadsheet_id = RESULTS_SPREADSHEET_ID
    service = get_service()
    sheet = service.spreadsheets()
    
    # Create the new sheet
    try:
        # Check if sheet already exists
        spreadsheet = sheet.get(spreadsheetId=spreadsheet_id).execute()
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
                spreadsheetId=spreadsheet_id,
                body={'requests': [add_sheet_request]}
            ).execute()
            print(f"Created new sheet: {sheet_name}")
    except Exception as e:
        print(f"Error creating/accessing sheet: {e}")
        return False
    
    # Prepare organized data
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_data = []
    
    # Add header with timestamp
    all_data.append([f"Capstone Team Matching Results - Generated: {timestamp}"])
    all_data.append([])  # Empty row
    
    for team_num, team in enumerate(team_results, 1):
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
    
    # Write data to sheet
    try:
        range_name = f"{sheet_name}!A1"
        body = {'values': all_data}
        
        result = sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"Successfully wrote organized team results to {sheet_name}")
        return True
        
    except Exception as e:
        print(f"Error writing to sheet: {e}")
        return False
