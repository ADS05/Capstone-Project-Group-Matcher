import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_service():
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    credentials = service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=credentials)

def get_sheet_data():
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
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
