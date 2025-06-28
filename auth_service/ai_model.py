def classify_condition(symptoms, age, gender):
    """
    Replace this with your actual model inference logic.
    For now, it's a mockup.
    """
    symptoms = symptoms.lower()
    if 'cough' in symptoms or 'fever' in symptoms:
        return 'hospital'
    elif 'rash' in symptoms or 'itching' in symptoms:
        return 'pharmacy'
    elif 'blood' in symptoms:
        return 'laboratory'
    elif 'x-ray' in symptoms or 'scan' in symptoms:
        return 'imaging'
    else:
        return 'doctor'
