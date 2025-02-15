from flask import Blueprint, request, jsonify
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# Blueprint instance
bp = Blueprint('submit', __name__)

# Email configuration
SENDER_EMAIL = "spurzeetechnologies@gmail.com"
SENDER_PASSWORD = "zdbb ilin tpia mbvo"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Define the CSV file path
CSV_FILE = 'form_submissions.csv'

# Function to write data to CSV
def write_to_csv(name, email, subject, message):
    try:
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                # Write headers only if the file is empty
                writer.writerow(['Name', 'Email', 'Subject', 'Message'])
            writer.writerow([name, email, subject, message])
    except Exception as e:
        print(f"Error writing to CSV: {e}")
        raise

# Function to send a thank you email
def send_thank_you_email(user_email, user_name):
    try:
        subject = "Thank You for Your Submission"
        body = f"Hello {user_name},\n\nThank you for contacting us. We will reach out to you soon!\n\nBest regards,\nSpurzee Technologies"

        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = user_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, user_email, message.as_string())
            print(f"Thank you email sent to {user_email}")
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
        raise
    except Exception as e:
        print(f"Error sending email: {e}")
        raise

# Function to validate email
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email)

# Route to handle form submission
@bp.route('/submit', methods=['POST'])
def submit_form():
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', 'No Subject').strip()
        message = request.form.get('message', '').strip()

        # Validate input fields
        if not name or not email or not message:
            return jsonify({"status": "error", "message": "All fields (Name, Email, and Message) are required!"}), 400
        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email address!"}), 400

        # Save data to CSV and send email
        write_to_csv(name, email, subject, message)
        send_thank_you_email(user_email=email, user_name=name)

        return jsonify({"status": "success", "message": "Form submitted successfully! A thank-you email has been sent."}), 200
    except Exception as e:
        print(f"Error processing form: {e}")
        return jsonify({"status": "error", "message": "Internal server error occurred!"}), 500
