# ai_clinical_officer_service.py (or a similar name)

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables once when the module is loaded
load_dotenv()

# Configure Gemini once
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Helper Functions (remain largely the same) ---

def _get_gemini_response(prompt_text):
    """Sends prompt to Gemini model and returns the response text."""
    try:
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        # Log the error properly in a real application
        print(f"Error getting Gemini response: {e}")
        return "An error occurred while processing your request. Please try again."

def _parse_gemini_output(response_text):
    """Extracts structured fields from Gemini output."""
    parsed = {
        "assessment": "Could not parse assessment.",
        "category": "Unknown",
        "severity": "Unknown",
        "recommendation": "Please consult a healthcare professional.",
        "specialist": "N/A",
        "who_advisory": "N/A"
    }

    lines = response_text.split('\n')
    for line in lines:
        if line.startswith('**Assessment:**'):
            parsed['assessment'] = line.replace('**Assessment:**', '').strip()
        elif line.startswith('**Category:**'):
            parsed['category'] = line.replace('**Category:**', '').strip()
        elif line.startswith('**Severity:**'):
            parsed['severity'] = line.replace('**Severity:**', '').strip()
        elif line.startswith('**Recommendation:**'):
            parsed['recommendation'] = line.replace('**Recommendation:**', '').strip()
        elif line.startswith('**Specialist (if applicable):**'):
            parsed['specialist'] = line.replace('**Specialist (if applicable):**', '').strip()
        elif line.startswith('**WHO Advisory (if applicable):**'):
            parsed['who_advisory'] = line.replace('**WHO Advisory (if applicable):**', '').strip()
    
    return parsed

# --- Core Service Logic for App Integration ---

class AIConsultationService:
    def __init__(self):
        # Initialize state for a new consultation session
        self.conversation_history = []
        self.user_info = {} # This could be pre-populated from your app's user data

    def set_user_details(self, name=None, age=None, gender=None, location=None):
        """
        Sets or updates user details for the current consultation.
        Call this when user profile information is available or collected.
        """
        if name: self.user_info['name'] = name
        if age: self.user_info['age'] = age
        if gender: self.user_info['gender'] = gender
        if location: self.user_info['location'] = location

    def process_user_message(self, user_message: str) -> dict:
        """
        Processes a single user message, adds it to history, and generates a response
        from Gemini based on the accumulated conversation.

        Args:
            user_message: The text input from the user.

        Returns:
            A dictionary containing the parsed AI response and possibly internal AI message.
            Format: {
                "ai_response_text": "AI's conversational reply (e.g., 'Okay, tell me more.')",
                "structured_assessment": { ... }, # Only present if 'done' or similar trigger
                "ready_for_assessment": bool # Indicates if enough info might be gathered
            }
        """
        # Add user's message to the conversation history
        self.conversation_history.append({"sender": "patient", "text": user_message})

        # --- IMPORTANT DECISION POINT FOR YOUR APP ---
        # 1. Option A: Respond conversationally after *each* input (more interactive)
        # 2. Option B: Collect multiple inputs, then send for full analysis (simpler to implement)

        # For this example, let's implement Option B primarily, but show how Option A could start.

        # If the user signals they are done, trigger the full assessment
        if user_message.lower() == 'done' or user_message.lower().strip() in ["i'm done", "that's all"]:
            print(f"DEBUG: Triggering full assessment with history: {self.conversation_history}")
            return self._perform_full_assessment()
        else:
            # If not 'done', the AI can give a generic conversational prompt
            # Or, you could have a simpler Gemini call here to get clarifying questions.
            ai_response_text = "Okay, I'm listening. Please continue to describe any other symptoms or details you have."
            # In a more advanced conversational flow, Gemini could guide the conversation:
            # simple_prompt = f"Patient: {user_message}\nAI: "
            # ai_response_text = _get_gemini_response(simple_prompt) # This would be a lightweight call
            
            return {
                "ai_response_text": ai_response_text,
                "structured_assessment": None,
                "ready_for_assessment": False
            }


    def _perform_full_assessment(self):
        """
        Performs the full symptom analysis with Gemini based on the accumulated history.
        This is typically called when the user signals they are done providing symptoms.
        """
        full_conversation_text = "\n".join(
            [f"Patient: {msg['text']}" if msg['sender'] == 'patient' else f"AI: {msg['text']}"
             for msg in self.conversation_history]
        )

        user_details_prompt = f"\n\nPatient Details (from app's context):\n"
        if self.user_info.get('name'):
            user_details_prompt += f"Name: {self.user_info['name']}\n"
        if self.user_info.get('age'):
            user_details_prompt += f"Age: {self.user_info['age']}\n"
        if self.user_info.get('location'):
            user_details_prompt += f"Location: {self.user_info['location']}\n"
        if self.user_info.get('gender'):
            user_details_prompt += f"Gender: {self.user_info['gender']}\n"

        # The system instruction is crucial and should be included in every full analysis prompt
        system_instruction = """
        You are a highly trained Clinical Officer designed to support first-line patient consultations in accordance with best global healthcare practices, including WHO clinical guidelines.

Your responsibilities include:
1. Gathering and clarifying patient-reported symptoms through structured conversation.
2. Assessing the likely severity of the case: 'Mild', 'Moderate', or 'Severe'.
3. Categorizing the condition into a medical domain such as:
   - Cardiovascular
   - Respiratory
   - Neurological
   - Gastrointestinal
   - Musculoskeletal
   - Dermatological
   - Psychiatric/Mental Health
   - Infectious Disease
   - Endocrine/Metabolic
   - Urinary/Reproductive
   - General or Undifferentiated

4. Based on the category and severity, provide a triage recommendation:
   - Self-care or over-the-counter guidance (with WHO-standard advice where applicable)
   - Book a virtual or in-person consultation with a general practitioner
   - Refer to a specific medical specialist (e.g., Cardiologist, Neurologist, Dermatologist)
   - Recommend immediate emergency services if symptoms suggest critical or life-threatening conditions (e.g., stroke, severe chest pain, difficulty breathing)

5. Ensure patient safety at all times. If symptom patterns are unclear or suggest escalation risk, default to a higher level of care.

6. Do **not** provide definitive diagnoses or prescribe medication.

Please return your response in the following structured format:
**Assessment:** [Your clinical assessment and any clarifying questions]
**Category:** [Disease category, e.g., Cardiovascular]
**Severity:** [Mild / Moderate / Severe]
**Recommendation:** [Self-care / GP Consult / Specialist Referral / Emergency Services]
**Specialist (if applicable):** [E.g., Cardiologist]
**WHO Advisory (if applicable):** [Guidelines or self-care advice based on WHO standards for mild or common conditions]
        """

        prompt = f"""
{system_instruction}
{user_details_prompt}

The patient has provided the following conversation history and final input. Please analyze all reported symptoms comprehensively.

Conversation summary:
{full_conversation_text}

Please analyze the patient's symptoms based on the entire conversation and provide the following:

1. A clinical assessment based on the reported symptoms, and any clarifying questions you would ask the patient (though this is the final assessment, so focus on the assessment).
2. A medical category that best fits the symptoms.
3. The severity of the condition.
4. A recommended course of action.
5. Suggest the most appropriate medical specialist, if applicable.
6. If the case is mild and manageable, provide WHO-standard advisory or home-care guidance if relevant.

Format your response clearly as follows:
**Assessment:** ...
**Category:** ...
**Severity:** ...
**Recommendation:** ...
**Specialist (if applicable):** ...
**WHO Advisory (if applicable):** ...
        """

        gemini_raw_response = _get_gemini_response(prompt)
        parsed_response = _parse_gemini_output(gemini_raw_response)

        # Add AI's final assessment to history for completeness (optional)
        self.conversation_history.append({"sender": "ai", "text": "Here is my assessment:"}) # Placeholder
        self.conversation_history.append({"sender": "ai", "text": parsed_response['assessment']})


        return {
            "ai_response_text": "Here is my full assessment based on your symptoms:",
            "structured_assessment": parsed_response,
            "ready_for_assessment": True
        }

    def get_conversation_history(self):
        """Returns the full conversation history."""
        return self.conversation_history

    def reset_consultation(self):
        """Resets the consultation state for a new session."""
        self.conversation_history = []
        self.user_info = {}