from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dass21-screening-tool-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dass21.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class ScreeningResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    responses = db.Column(db.Text)  # JSON string of responses
    depression_score = db.Column(db.Integer)
    anxiety_score = db.Column(db.Integer)
    stress_score = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('screening_responses', lazy=True))

# DASS-21 Questions
DASS21_QUESTIONS = [
    {"id": 1, "text": "I found it hard to wind down", "scale": "stress"},
    {"id": 2, "text": "I was aware of dryness of my mouth", "scale": "anxiety"},
    {"id": 3, "text": "I couldn't seem to experience any positive feeling at all", "scale": "depression"},
    {"id": 4, "text": "I experienced breathing difficulty (eg, excessively rapid breathing, breathlessness in the absence of physical exertion)", "scale": "anxiety"},
    {"id": 5, "text": "I found it difficult to work up the initiative to do things", "scale": "depression"},
    {"id": 6, "text": "I tended to over-react to situations", "scale": "stress"},
    {"id": 7, "text": "I experienced trembling (eg, in the hands)", "scale": "anxiety"},
    {"id": 8, "text": "I felt that I was using a lot of nervous energy", "scale": "stress"},
    {"id": 9, "text": "I was worried about situations in which I might panic and make a fool of myself", "scale": "anxiety"},
    {"id": 10, "text": "I felt that I had nothing to look forward to", "scale": "depression"},
    {"id": 11, "text": "I found myself getting agitated", "scale": "stress"},
    {"id": 12, "text": "I found it difficult to relax", "scale": "stress"},
    {"id": 13, "text": "I felt down-hearted and blue", "scale": "depression"},
    {"id": 14, "text": "I was intolerant of anything that kept me from getting on with what I was doing", "scale": "stress"},
    {"id": 15, "text": "I felt I was close to panic", "scale": "anxiety"},
    {"id": 16, "text": "I was unable to become enthusiastic about anything", "scale": "depression"},
    {"id": 17, "text": "I felt I wasn't worth much as a person", "scale": "depression"},
    {"id": 18, "text": "I felt that I was rather touchy", "scale": "stress"},
    {"id": 19, "text": "I was aware of the action of my heart in the absence of physical exertion (eg, sense of heart rate increase, heart missing a beat)", "scale": "anxiety"},
    {"id": 20, "text": "I felt scared without any good reason", "scale": "anxiety"},
    {"id": 21, "text": "I felt that life was meaningless", "scale": "depression"}
]

def calculate_scores(responses):
    depression_items = [3, 5, 10, 13, 16, 17, 21]
    anxiety_items = [2, 4, 7, 9, 15, 19, 20]
    stress_items = [1, 6, 8, 11, 12, 14, 18]
    
    depression_score = sum(responses.get(str(i), 0) for i in depression_items) * 2
    anxiety_score = sum(responses.get(str(i), 0) for i in anxiety_items) * 2
    stress_score = sum(responses.get(str(i), 0) for i in stress_items) * 2
    
    return depression_score, anxiety_score, stress_score

def get_severity_level(score, scale_type):
    if scale_type == "depression":
        if score <= 9: return "Normal"
        elif score <= 13: return "Mild"
        elif score <= 20: return "Moderate"
        elif score <= 27: return "Severe"
        else: return "Extremely Severe"
    elif scale_type == "anxiety":
        if score <= 7: return "Normal"
        elif score <= 9: return "Mild"
        elif score <= 14: return "Moderate"
        elif score <= 19: return "Severe"
        else: return "Extremely Severe"
    elif scale_type == "stress":
        if score <= 14: return "Normal"
        elif score <= 18: return "Mild"
        elif score <= 25: return "Moderate"
        elif score <= 33: return "Severe"
        else: return "Extremely Severe"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return render_template('register.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        flash('Registration successful')
        return redirect(url_for('screening'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('screening'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/screening', methods=['GET', 'POST'])
def screening():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        responses = {}
        for i in range(1, 22):
            responses[str(i)] = int(request.form.get(f'q{i}', 0))
        
        depression_score, anxiety_score, stress_score = calculate_scores(responses)
        
        screening_response = ScreeningResponse(
            user_id=session['user_id'],
            responses=json.dumps(responses),
            depression_score=depression_score,
            anxiety_score=anxiety_score,
            stress_score=stress_score
        )
        db.session.add(screening_response)
        db.session.commit()
        
        return redirect(url_for('results', response_id=screening_response.id))
    
    return render_template('screening.html', questions=DASS21_QUESTIONS)

@app.route('/results/<int:response_id>')
def results(response_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    response = ScreeningResponse.query.get_or_404(response_id)
    if response.user_id != session['user_id'] and not User.query.get(session['user_id']).is_admin:
        flash('Access denied')
        return redirect(url_for('screening'))
    
    depression_severity = get_severity_level(response.depression_score, "depression")
    anxiety_severity = get_severity_level(response.anxiety_score, "anxiety")
    stress_severity = get_severity_level(response.stress_score, "stress")
    
    return render_template('results.html', 
                         response=response,
                         depression_severity=depression_severity,
                         anxiety_severity=anxiety_severity,
                         stress_severity=stress_severity)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    
    users = User.query.filter_by(is_admin=False).all()
    responses = ScreeningResponse.query.join(User).all()
    
    return render_template('admin.html', users=users, responses=responses)

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return dict(current_user_is_admin=user.is_admin if user else False)
    return dict(current_user_is_admin=False)

@app.route('/generate_pdf/<int:response_id>')
def generate_pdf(response_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    response = ScreeningResponse.query.get_or_404(response_id)
    
    if not user.is_admin and response.user_id != session['user_id']:
        flash('Access denied')
        return redirect(url_for('index'))
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=1
    )
    story.append(Paragraph("DASS-21 Screening Results", title_style))
    story.append(Spacer(1, 20))
    
    # Patient info
    story.append(Paragraph(f"Patient: {response.user.username}", styles['Normal']))
    story.append(Paragraph(f"Email: {response.user.email}", styles['Normal']))
    story.append(Paragraph(f"Test Date: {response.completed_at.strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Scores table
    data = [
        ['Scale', 'Score', 'Severity Level'],
        ['Depression', str(response.depression_score), get_severity_level(response.depression_score, "depression")],
        ['Anxiety', str(response.anxiety_score), get_severity_level(response.anxiety_score, "anxiety")],
        ['Stress', str(response.stress_score), get_severity_level(response.stress_score, "stress")]
    ]
    
    table = Table(data, colWidths=[2*inch, 1*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 40))
    
    # Signature section
    story.append(Paragraph("Psychologist Signature:", styles['Normal']))
    story.append(Spacer(1, 30))
    story.append(Paragraph("_" * 50, styles['Normal']))
    story.append(Paragraph("Dr. ________________", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Date: _________________", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    response_obj = make_response(buffer.read())
    response_obj.headers['Content-Type'] = 'application/pdf'
    response_obj.headers['Content-Disposition'] = f'attachment; filename=dass21_results_{response.user.username}_{response.id}.pdf'
    
    return response_obj

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=5000)