from flask import Flask, request, jsonify, render_template
import os
import boto3
import requests
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# AWS Rekognition Setup
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION")

rekognition_client = boto3.client(
    "rekognition",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Azure OpenAI API Credentials
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

@app.route("/")
def index():
    return render_template("index.html")

# Function to clean and format AI response
def clean_response(text):
    text = re.sub(r'[#*_~`]', '', text)  
    text = re.sub(r'\n\s*\n', '<br><br>', text)  
    text = re.sub(r'\s*-\s*', '• ', text)  
    text = text.replace("\n", "<br>")  
    return text

@app.route("/face", methods=["POST"])
def face():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files["image"]
    image_bytes = image_file.read()

    try:
        response = rekognition_client.detect_faces(
            Image={"Bytes": image_bytes},
            Attributes=["ALL"]
        )

        if not response["FaceDetails"]:
            return jsonify({"error": "No face detected. Try another image."})

        face_attributes = response["FaceDetails"][0]

        # Extract key landmarks for FOQUS-style analysis
        face_data = {
            "Age Range": f"{face_attributes['AgeRange']['Low']} - {face_attributes['AgeRange']['High']}",
            "Gender": face_attributes["Gender"]["Value"],
            "Face Width": face_attributes["BoundingBox"]["Width"],
            "Face Height": face_attributes["BoundingBox"]["Height"],
            "Nose Width": face_attributes["Landmarks"][4]["X"] - face_attributes["Landmarks"][3]["X"],
            "Jawline Definition": face_attributes["Landmarks"][8]["X"] - face_attributes["Landmarks"][7]["X"],
            "Eye Distance": face_attributes["Landmarks"][1]["X"] - face_attributes["Landmarks"][0]["X"],
            "Mouth Width": face_attributes["Landmarks"][5]["X"] - face_attributes["Landmarks"][6]["X"],
            "Emotions": sorted(face_attributes["Emotions"], key=lambda x: x["Confidence"], reverse=True)[0]["Type"]
        }

        # Create a structured prompt for GPT-4o based on detected landmarks
        prompt = f"""
        Given the following facial landmarks detected:
        - Age: {face_data['Age Range']}
        - Gender: {face_data['Gender']}
        - Face Height-to-Width Ratio: {face_data['Face Height'] / face_data['Face Width']:.2f}
        - Nose Width: {face_data['Nose Width']:.2f}
        - Jawline Definition: {face_data['Jawline Definition']:.2f}
        - Eye Distance: {face_data['Eye Distance']:.2f}
        - Mouth Width: {face_data['Mouth Width']:.2f}
        - Dominant Emotion: {face_data['Emotions']}

        Use FOQUS personality profiling framework to generate an insightful personality analysis.
        """

        ai_response = requests.post(
            f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}",
            headers={"Content-Type": "application/json", "api-key": AZURE_OPENAI_API_KEY},
            json={"messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 900, "temperature": 0.6}
        )

        personality_analysis = ai_response.json()["choices"][0]["message"]["content"]

        return jsonify({
            "face_analysis": face_data,
            "personality_insights": clean_response(personality_analysis)
        })

    except Exception as e:
        return jsonify({"error": f"AWS Rekognition Error: {str(e)}"}), 500
    
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip().lower()

    if not user_message:
        return jsonify({"response": "Please enter a message."})

    # Define prompt variations based on user input length
    if len(user_message) <= 3:
        ai_prompt = f"Respond casually and briefly to: {user_message}. Keep it short and natural."
    elif "meaning" in user_message or "explain" in user_message:
        ai_prompt = f"Provide a structured explanation for: {user_message}. Keep it clear and concise."
    else:
        ai_prompt = f"Answer this query as an AI Facial Profiling Coach: {user_message}. Keep it professional and structured but avoid unnecessary details."

    try:
        # Send Optimized Chat Message to GPT-4o
        ai_response = requests.post(
            f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}",
            headers={"Content-Type": "application/json", "api-key": AZURE_OPENAI_API_KEY},
            json={"messages": [{"role": "user", "content": ai_prompt}],
                  "max_tokens": 150, "temperature": 0.6}  # Reduced max tokens & temp for better control
        )

        bot_reply = ai_response.json()["choices"][0]["message"]["content"]

        # Remove unwanted symbols from response
        bot_reply = re.sub(r'[#*_~•`]', '', bot_reply)  

        return jsonify({"response": bot_reply})

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})


if __name__ == "__main__":
    app.run(debug=True)
