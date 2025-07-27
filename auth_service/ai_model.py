import os
from flask import Blueprint, request, jsonify, render_template, session
import google.generativeai as genai
from dotenv import load_dotenv
from auth_service.models import User, Facility, DoctorProfile, db

load_dotenv()

# --- Initialize Gemini ---
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Define Blueprint ---
#clinical_bp = Blueprint('clinical_bp', __name__, template_folder='templates')
clinical_routes = Blueprint('clinical_routes', __name__)

# --- Helper Functions ---

def clasify_condition(prompt_text):
    try:
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        print(f"Error getting Gemini response: {e}")
        return "An error occurred while processing your request. Please try again."

def analyze_symptoms_with_gemini(patient_input, conversation_history, user_info):
    system_instruction = """
    You are an AI Clinical Officer designed to assist patients with their first-line consultations.
    Your goal is to gather information about symptoms, assess their potential severity, and recommend appropriate next steps.
    You should ask clarifying questions to get a better understanding of the patient's condition.
    Based on the information, categorize the case as 'Mild', 'Moderate', or 'Severe'.
    For 'Mild' cases, suggest self-care.
    For 'Moderate' cases, suggest booking a virtual consult with a General Practitioner.
    For 'Severe' cases, recommend visiting the nearest hospital and suggest a potential specialist if clear.
    Always prioritize patient safety. If unsure, err on the side of caution and recommend a higher level of care.
    Do not give definitive diagnoses or prescribe medication.
    """
    full_conversation = "\n".join([
        f"Patient: {msg['text']}" if msg['sender'] == 'patient' else f"AI: {msg['text']}"
        for msg in conversation_history
    ])

    user_details_prompt = ""
    if user_info:
        user_details_prompt += "\n\nPatient Details:\n"
        if user_info.get('name'):
            user_details_prompt += f"Name: {user_info['name']}\n"
        if user_info.get('age'):
            user_details_prompt += f"Age: {user_info['age']}\n"
        if user_info.get('location'):
            user_details_prompt += f"Location: {user_info['location']}\n"

    prompt = f"""
    {system_instruction}
    {user_details_prompt}

    Current conversation:
    {full_conversation}
    Patient: {patient_input}

    Please analyze the patient's current symptoms and provide:
    1. An assessment of the symptoms and any follow-up questions needed.
    2. A preliminary categorization: 'Mild', 'Moderate', or 'Severe'.
    3. The recommended next step for the patient based on the categorization (self-care, virtual consult, hospital).
    4. If hospital is recommended, suggest a potential specialist (e.g., Neurologist, Cardiologist) based on the symptoms.

    Format your response clearly, for example:
    **Assessment:** [Your assessment and follow-up questions]
    **Category:** [Mild/Moderate/Severe]
    **Recommendation:** [Self-care/Virtual Consult/Visit Hospital]
    **Specialist (if applicable):** [e.g., Neurologist]
    """
    return clasify_condition(prompt)

def parse_gemini_output(gemini_response):
    parsed = {
        "assessment": "Could not parse assessment.",
        "category": "Unknown",
        "recommendation": "Please consult a healthcare professional.",
        "specialist": "N/A"
    }
    lines = gemini_response.split('\n')
    for line in lines:
        if line.startswith('**Assessment:**'):
            parsed["assessment"] = line.replace('**Assessment:**', '').strip()
        elif line.startswith('**Category:**'):
            parsed["category"] = line.replace('**Category:**', '').strip()
        elif line.startswith('**Recommendation:**'):
            parsed["recommendation"] = line.replace('**Recommendation:**', '').strip()
        elif line.startswith('**Specialist (if applicable):**'):
            parsed["specialist"] = line.replace('**Specialist (if applicable):**', '').strip()
    return parsed

# --- Routes  should also include suggested approved doctors or facilities near the user location based on the response from gemini---

@clinical_routes.route('/clinical')
def clinical_index():
    session.clear()
    session['conversation_stage'] = 'ask_name'
    session['user_info'] = {}
    session['conversation_history'] = []
    return render_template('index.html')

@clinical_routes.route('/reset')
def reset_conversation():
    session.clear()
    session['conversation_stage'] = 'ask_name'
    session['user_info'] = {}
    session['conversation_history'] = []
    return jsonify({"message": "Conversation reset. Please refresh the page.", "reset": True})

@clinical_routes.route('/consult', methods=['POST'])
def consult():
    data = request.get_json()
    user_input = data.get('input', '').strip()

    if not user_input:
        return jsonify({"response": "Please provide a response."})

    current_stage = session.get('conversation_stage', 'ask_name')
    user_info = session.get('user_info', {})
    conversation_history = session.get('conversation_history', [])

    ai_response = ""
    next_stage = current_stage
    gemini_raw_response = None
    triage_outcome = None

    conversation_history.append({'sender': 'patient', 'text': user_input})

    if current_stage == 'ask_name':
        user_info['name'] = user_input
        ai_response = f"Nice to meet you, {user_info['name']}! How old are you?"
        next_stage = 'ask_age'
    elif current_stage == 'ask_age':
        try:
            age = int(user_input)
            if age <= 0 or age > 120:
                ai_response = "Please enter a valid age. How old are you?"
            else:
                user_info['age'] = age
                ai_response = "Great. In which city or town are you located? (e.g., Nairobi, Mombasa)"
                next_stage = 'ask_location'
        except ValueError:
            ai_response = "Please enter a number for your age. How old are you?"
    elif current_stage == 'ask_location':
        user_info['location'] = user_input
        ai_response = f"Thank you, {user_info.get('name', 'there')} in {user_info['location']}. Now, please tell me about the symptoms you're experiencing."
        next_stage = 'ask_symptoms'
    elif current_stage == 'ask_symptoms':
        gemini_raw_response = analyze_symptoms_with_gemini(user_input, conversation_history, user_info)
        triage_outcome = parse_gemini_output(gemini_raw_response)

        response_text = f"**AI Clinical Officer Assessment:**\n{triage_outcome['assessment']}\n\n" \
                        f"**Case Category:** {triage_outcome['category']}\n" \
                        f"**Recommendation:** {triage_outcome['recommendation']}\n"
        if triage_outcome['specialist'] and triage_outcome['specialist'] != 'N/A':
            response_text += f"**Potential Specialist:** {triage_outcome['specialist']}\n"

        ai_response = response_text
        next_stage = 'ask_symptoms'

    session['conversation_stage'] = next_stage
    session['user_info'] = user_info
    conversation_history.append({'sender': 'ai', 'text': ai_response})
    session['conversation_history'] = conversation_history

    return jsonify({
        "response": ai_response,
        "current_stage": next_stage,
        "user_info": user_info,
        "raw_gemini_output": gemini_raw_response,
        "parsed_outcome": triage_outcome
    })
    
    #triage outcome parsing and fetching nearby doctors or facilities from database then display for user to choose from
@clinical_routes.route('/doctors', methods=['GET'])
def get_doctors():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    specialty = request.args.get('specialty', '').strip().lower()
    location = request.args.get('location', '').strip().lower()
    query = User.query.filter_by(role='doctor', approved=True).join(DoctorProfile)
    if specialty:
        query = query.filter(db.func.lower(DoctorProfile.specialty).like(f"%{specialty}%"))
    if location:
        query = query.filter(db.func.lower(User.location).like(f"%{location}%"))
    pagination = query.paginate(page=page, per_page=per_page)
    doctors = pagination.items
    return render_template(
        'doctors/list.html',
        doctors=doctors,
        pagination=pagination,
        specialty=specialty,
        location=location
    )
@clinical_routes.route('/doctors/<int:doctor_id>', methods=['GET'])
def get_doctor_detail(doctor_id):
    doctor = User.query.filter_by(id=doctor_id, role='doctor', approved=True).first_or_404()
    return render_template('doctors/detail.html', doctor=doctor)
    return render_template('model/copilot_results.html', response=gemini_raw_response, parsed_outcome=triage_outcome)
    return render_template('model/copilot_results.html', response=None, parsed_outcome=None)





