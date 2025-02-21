import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import openai
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

print(f'Using api key: {openai.api_key}')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///candidates.db'
db = SQLAlchemy(app)


class Candidate(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	position = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	resume = db.Column(db.Text, nullable=True)
	invite_url = db.Column(db.String(200), unique=True, nullable=True)
	interview_completed = db.Column(db.Boolean, default=False)
	interview_started = db.Column(db.Boolean, default=False)  # New field


@app.route('/')
def candidates_table():
	candidates = Candidate.query.all()
	return render_template('candidates_table.html', candidates=candidates)


@app.route('/candidate/<int:id>')
def candidate_details(id):
	candidate = Candidate.query.get_or_404(id)
	return jsonify({
		'name': candidate.name,
		'position': candidate.position,
		'email': candidate.email,
		'resume': candidate.resume,
		'invite_url': candidate.invite_url,
		'interview_completed': candidate.interview_completed
	})


@app.route('/invite/<int:id>')
def invite_candidate(id):
	candidate = Candidate.query.get_or_404(id)
	invite_url = f"http://localhost:3000/interview/{uuid.uuid4()}?id={id}"
	candidate.invite_url = invite_url
	db.session.commit()

	# Email configuration
	sender_email = "aditya.arolkar2@gmail.com"  # Replace with your email
	sender_password = os.getenv('GMAIL_APP_PASSWORD')  # Replace with your app password
	print(f'Using app password: {sender_password}')
	smtp_server = "smtp.gmail.com"
	smtp_port = 587

	# Create message
	message = MIMEMultipart("alternative")
	message["Subject"] = "Interview Invitation"
	message["From"] = sender_email
	message["To"] = candidate.email

	# Create the plain-text and HTML version of your message
	text = f"""
    Dear {candidate.name},

    You have been invited for an interview for the position of {candidate.position}.
    Please click on the following link to start your interview:

    {invite_url}

    Best regards,
    The Hiring Team
    """

	html = f"""
    <html>
      <body>
        <p>Dear {candidate.name},</p>
        <p>You have been invited for an interview for the position of {candidate.position}.</p>
        <p>Please click on the following link to start your interview:</p>
        <p><a href="{invite_url}">{invite_url}</a></p>
        <p>Best regards,<br>The Hiring Team</p>
      </body>
    </html>
    """

	# Turn these into plain/html MIMEText objects
	part1 = MIMEText(text, "plain")
	part2 = MIMEText(html, "html")

	# Add HTML/plain-text parts to MIMEMultipart message
	# The email client will try to render the last part first
	message.attach(part1)
	message.attach(part2)

	# Send email
	try:
		with smtplib.SMTP(smtp_server, smtp_port) as server:
			server.starttls()  # Secure the connection
			server.login(sender_email, sender_password)
			server.sendmail(sender_email, candidate.email, message.as_string())
		print(f"Email sent successfully to {candidate.email}")
		return jsonify({'status': 'success', 'message': 'Invitation sent'})
	except Exception as e:
		print(f"Failed to send email. Error: {str(e)}")
		return jsonify({'status': 'error', 'message': 'Failed to send invitation'})


@app.route('/interview/<string:invite_id>')
def interview_session(invite_id):
	candidate_id = request.args.get('id')
	if not candidate_id:
		return "Invalid interview URL", 400

	candidate = Candidate.query.get_or_404(int(candidate_id))
	if candidate.invite_url != request.url:
		return "Invalid interview URL", 400

	if candidate.interview_completed:
		return "This interview has already been completed.", 400

	return render_template('interview_session.html', candidate=candidate)


@app.route('/start_interview/<int:id>', methods=['POST'])
def start_interview(id):
    candidate = Candidate.query.get_or_404(id)
    if candidate.interview_started:
        return jsonify({'status': 'error', 'message': 'Interview already started'}), 400
    candidate.interview_started = True
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Interview started'})

@app.route('/interview_status/<int:id>')
def interview_status(id):
    candidate = Candidate.query.get_or_404(id)
    return jsonify({
        'started': candidate.interview_started,
        'completed': candidate.interview_completed
    })

@app.route('/complete_interview/<int:id>', methods=['POST'])
def complete_interview(id):
    candidate = Candidate.query.get_or_404(id)
    candidate.interview_completed = True
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'Interview completed',
        'interviewCompleted': candidate.interview_completed
    })


@app.route('/ai_response', methods=['POST'])
def ai_response():
	data = request.json
	messages = data['messages']

	try:
		response = openai.chat.completions.create(
			model="gpt-3.5-turbo",
			messages=messages
		)
		ai_message = response.choices[0].message.content
		return jsonify({'message': ai_message})
	except Exception as e:
		print(f"Error in AI response: {str(e)}")
		return jsonify({'message': "I'm sorry, I'm having trouble responding right now."})

def init_db():
	db_path = 'instance/candidates.db'
	if not os.path.exists(db_path):
		with app.app_context():
			db.create_all()

			# Add sample data
			sample_candidates = [
				Candidate(name="Aditya Arolkar", position="Software Engineer", email="aditya.arolkar@berkeley.edu",
						  resume="Experienced software engineer with 5 years of Python development."),
				Candidate(name="Jane Smith", position="Data Scientist", email="jane@example.com",
						  resume="Data scientist with expertise in machine learning and statistical analysis.")
			]
			db.session.add_all(sample_candidates)
			db.session.commit()
		print("Database initialized with sample data.")
	else:
		print("Database already exists.")


if __name__ == '__main__':
	init_db()
	app.run(debug=True, port=3000)