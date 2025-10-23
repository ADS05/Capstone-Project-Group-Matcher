# 🎯 Capstone Team Matcher

A Python application that matches students into capstone project teams based on their survey responses, skills, preferences, and compatibility. The system reads student data from Google Sheets and exports organized team matching results to a separate spreadsheet for faculty review.

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

## 🚀 Quick Start

### **Demo Mode (Default)**
```bash
python3 src/main.py
```
- Shows automatic team matching
- Displays compatibility scores and warnings
- Automatically exports to Google Sheets
- Perfect for demonstrations

### **Interactive Mode (Faculty Use)**
```bash
python3 src/main.py --interactive
```
- Full interactive terminal interface
- Faculty can manually adjust teams
- Real-time compatibility scoring
- Manual export when satisfied

## 🎯 Interactive Commands

When running in interactive mode, faculty can use:

| Command | Function | Example |
|---------|-----------|----------|
| **`l`** | List all teams | Shows: "Team 1 (score=0.717): Harry Kim, Violet York" |
| **`m`** | Move student | Prompts: "Student name?", "From team?", "To team?" |
| **`s`** | Show scores | Recalculates and displays all team scores |
| **`w`** | Check warnings | Shows teams with compatibility < 0.45 |
| **`d`** | Done & export | Finalizes teams and exports to Google Sheets |
| **`q`** | Quit | Exits without saving changes |

## 📊 Faculty Workflow

1. **Run the program**: `python3 src/main.py --interactive`
2. **Review initial teams**: System shows automatically generated teams
3. **Make adjustments**: Use `m` to move students if needed
4. **Check compatibility**: Use `w` to see warnings
5. **Finalize**: Use `d` to export final teams to Google Sheets

## 🔧 Features

- ✅ **Automatic Team Matching**: AI-powered compatibility scoring
- ✅ **Manual Override**: Faculty can adjust teams as needed
- ✅ **Real-time Scoring**: See compatibility scores update after changes
- ✅ **Warning System**: Alerts for problematic team combinations
- ✅ **Google Sheets Export**: Saves organized results for faculty review
- ✅ **Project Assignment**: Each team gets a unique project
- ✅ **Smart Team Matching**: Uses compatibility scoring based on:
  - Project preference similarity
  - Mutual teammate preferences  
  - Skills compatibility
  - Availability matching

## 📋 Output Format

The exported Google Sheet includes:
- **Team sections**: Each team in its own organized section
- **Member details**: Name, email, skills, preferences, availability
- **Compatibility scores**: Team compatibility ratings
- **Project assignments**: Unique project assigned to each team
- **Timestamp**: When the matching was performed

## Files Structure

- `src/main.py` - Main application with team matching algorithm
- `src/google_client.py` - Google Sheets API integration
- `src/student.py` - Student data model
- `src/config.py` - Configuration settings
- `requirements.txt` - Python dependencies

## 🎯 Perfect for Demos!

The system is production-ready and perfect for your capstone demo! 🚀
