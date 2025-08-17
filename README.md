# DASS-21 Screening Tool

A simple web-based DASS-21 (Depression, Anxiety, and Stress Scale) screening tool built with Flask. Features monotone design, user authentication, admin management, and PDF report generation.

## Features

- **User Registration & Authentication**: Simple signup and login system
- **DASS-21 Questionnaire**: All 21 standardized questions with 4-point scale responses
- **Scoring System**: Automatic calculation of Depression, Anxiety, and Stress scores
- **Results Display**: Clear presentation of scores with severity levels
- **Admin Panel**: User management and response viewing for administrators
- **PDF Generation**: Downloadable reports with psychologist signature space
- **Monotone Design**: Simple, clean interface without fancy designs

## DASS-21 Information

The DASS-21 is a validated psychological screening tool that measures:
- **Depression**: Dysphoria, hopelessness, devaluation of life, self-deprecation, lack of interest/involvement, anhedonia, and inertia
- **Anxiety**: Autonomic arousal, skeletal muscle effects, situational anxiety, and subjective experience of anxious affect
- **Stress**: Difficulty relaxing, nervous arousal, being easily upset/agitated, irritable/over-reactive, and impatient

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and go to `http://localhost:5000`

## Default Admin Account

- **Username**: admin
- **Password**: admin123

## Usage

### For Users:
1. Register a new account or login
2. Complete the DASS-21 questionnaire
3. View your results with severity levels
4. Download PDF report

### For Administrators:
1. Login with admin credentials
2. View all registered users
3. Monitor screening responses
4. Generate PDFs for any user
5. View summary statistics

## Database

The application uses SQLite database with two main tables:
- `User`: Stores user account information
- `ScreeningResponse`: Stores completed questionnaire responses and scores

## Security Notes

- Passwords are hashed using Werkzeug's security utilities
- Session management for user authentication
- Admin-only access controls for management features

## Scoring

DASS-21 scores are calculated by:
1. Summing responses for each scale (Depression: items 3,5,10,13,16,17,21; Anxiety: items 2,4,7,9,15,19,20; Stress: items 1,6,8,11,12,14,18)
2. Multiplying by 2 to match DASS-42 scores

### Severity Levels:
- **Depression**: Normal (0-9), Mild (10-13), Moderate (14-20), Severe (21-27), Extremely Severe (28+)
- **Anxiety**: Normal (0-7), Mild (8-9), Moderate (10-14), Severe (15-19), Extremely Severe (20+)
- **Stress**: Normal (0-14), Mild (15-18), Moderate (19-25), Severe (26-33), Extremely Severe (34+)

## Important Disclaimer

This screening tool is for educational and research purposes only and should not be used as a substitute for professional medical advice, diagnosis, or treatment. If you are experiencing thoughts of self-harm or suicide, please seek immediate professional help.
