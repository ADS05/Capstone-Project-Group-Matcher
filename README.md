# Sprint MVP - Capstone Team Matcher

A Python application that matches students into capstone project teams based on their survey responses, skills, preferences, and compatibility. The system reads student data from Google Sheets and exports organized team matching results to a separate spreadsheet for faculty review.

## Features

- **Google Sheets Integration**: Reads student survey data from Google Sheets
- **Smart Team Matching**: Uses compatibility scoring based on:
  - Project preference similarity
  - Mutual teammate preferences  
  - Skills compatibility
  - Availability matching
- **Organized Results Export**: Writes formatted team assignments to a separate Google Sheet
- **Faculty-Friendly Output**: Each team is displayed in its own section with detailed member information

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Google Sheets API Setup
1. Create a Google Cloud Project
2. Enable the Google Sheets API
3. Create a Service Account and download the JSON key file
4. Share your Google Sheets with the service account email

### 3. Configuration
1. Update `src/config.py` with your spreadsheet IDs:
   - `SURVEY_SPREADSHEET_ID`: Your survey data spreadsheet (read-only)
   - `RESULTS_SPREADSHEET_ID`: Your results spreadsheet (write access)
2. Ensure the service account has **Editor** access to the results spreadsheet

### 4. Run the Application
```bash
python src/main.py
```

## Output

The application will:
1. Read student survey data from the survey spreadsheet
2. Create optimized teams based on compatibility scoring
3. Export organized results to the "Team Matching Results" tab in your results spreadsheet
4. Display team summaries in the terminal

## Results Format

The exported Google Sheet includes:
- **Team sections**: Each team displayed in its own organized section
- **Member details**: Name, email, skills, project preferences, availability
- **Compatibility scores**: Team compatibility ratings
- **Project assignments**: Unique project assigned to each team
- **Timestamp**: When the matching was performed

## Files Structure

- `src/main.py` - Main application with team matching algorithm
- `src/google_client.py` - Google Sheets API integration
- `src/student.py` - Student data model
- `src/config.py` - Configuration settings
- `requirements.txt` - Python dependencies
