
from flask import Flask, request, jsonify, render_template
import os
import difflib

app = Flask(__name__)

DISEASE_FOLDER = "./datasets"  # Update this to your folder path


def load_disease_data(folder_path):
    disease_data = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".txt"):
            path = os.path.join(folder_path, file_name)
            disease_name = file_name[:-4].lower()
            with open(path, "r", encoding="utf-8") as file:
                content = file.read().lower()
                if "symptoms:" in content and "natural remedies:" in content:
                    parts = content.split("natural remedies:")
                    symptoms = parts[0].replace("symptoms:", "").strip()
                    remedies = parts[1].strip()
                    disease_data[disease_name] = {
                        "symptoms": [s.strip() for s in symptoms.split(",")],
                        "remedies": remedies
                    }
    return disease_data


disease_data = load_disease_data(DISEASE_FOLDER)


def correct_input_phrase(symptom_phrase, valid_phrases):
    matches = difflib.get_close_matches(symptom_phrase.strip(), valid_phrases, n=1, cutoff=0.7)
    return matches[0] if matches else symptom_phrase.strip()


def query_diseases(user_symptoms, disease_data):
    user_set = set(user_symptoms)
    results = []
    for disease, data in disease_data.items():
        db_set = set(data["symptoms"])
        if user_set.issubset(db_set):
            results.append({
                "disease": disease.title(),
                "symptoms": ", ".join(data["symptoms"]),
                "remedies": data["remedies"]
            })
    return results


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/check-symptoms', methods=['POST'])
def check_symptoms():
    data = request.get_json()
    user_input = data.get("symptoms", "").lower().strip()

    if not user_input:
        return jsonify({"prediction": "❗ Please enter your symptoms."})

    input_symptoms = [s.strip() for s in user_input.split(',') if s.strip()]
    if not input_symptoms:
        return jsonify({"prediction": "❗ Please enter valid symptoms separated by commas."})

    # Collect all valid symptom phrases from dataset
    valid_symptom_phrases = set()
    for entry in disease_data.values():
        valid_symptom_phrases.update(entry["symptoms"])

    # Correct input phrases
    corrected_symptoms = [correct_input_phrase(s, valid_symptom_phrases) for s in input_symptoms]

    matches = query_diseases(corrected_symptoms, disease_data)

    if not matches:
        return jsonify({"prediction": [], "input": ", ".join(corrected_symptoms)})

    return jsonify({"prediction": matches, "input": ", ".join(corrected_symptoms)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
