# NEET PG Timetable Generator

A Flask-based web application to generate personalized study timetables for NEET PG aspirants.

## Features
- **Main Timetable**: Generates a study schedule based on available days and subject weightage.
- **Revision Timetable**: Creates a revision plan with dedicated slots for Weekly Revision (Saturdays) and Grand Tests (Sundays).
- **PDF Export**: Generates a clean, printable PDF of the schedule.
- **Responsive Design**: Mobile-friendly interface optimized for all devices.

## Local Setup

1. **Clone the repository** (if applicable) or navigate to the project directory.

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```
   The app will run at `http://127.0.0.1:5000`.

## Deployment on Render

1. Create a new **Web Service** on [Render](https://render.com/).
2. Connect your GitHub repository.
3. Render will automatically detect the `Dockerfile`.
4. Click **Create Web Service**.

> **Note on Database**: This application uses SQLite. On Render's free tier, the filesystem is ephemeral, meaning the database will reset if the service restarts. For persistent data in production, consider switching to Render's PostgreSQL service.
