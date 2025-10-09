from flask import Flask, request, jsonify, render_template, redirect, session
import requests
import mysql.connector
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_very_secure_default_secret_key")

# Clever Cloud MySQL connection (credentials unchanged)
try:
    conn = mysql.connector.connect(
        host="bt50vekxtlpwanbpzo6n-mysql.services.clever-cloud.com",
        user="uybdk7ycpidf4axw",
        password="ke39xPKLUbqr6PBdH351",
        database="bt50vekxtlpwanbpzo6n"
    )
    print("✅ Successfully connected to the database.")
except mysql.connector.Error as err:
    print(f"❌ Database Connection Error: {err}")
    conn = None # Set conn to None if connection fails

# --- START OF CHANGES: Switched to Google Gemini API ---

# 1. Google Gemini API Configuration
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
# Your new Google AI API Key.
# IMPORTANT: For security, it's best to use environment variables in real projects.
GOOGLE_API_KEY = "AIzaSyC6hbmGhbe854iTJTnCYppruKqfpMb9uwg"

headers = {
    "Content-Type": "application/json"
}

# -------------------------------
# CUSTOM TRAINING DATA (Unchanged)
# This will be used as the system instruction for the Gemini model.
# -------------------------------
training_context = """
You are VINCI – Virtual Interactive Natural Chatbot Interface 🤖.
Here are your important details:

1. NAME & IDENTITY
   - Your name is VINCI.
   - You are a Virtual Interactive Natural Chatbot Interface.
   - You are an AI assistant, friendly and helpful.

2. CREATION
   - You were developed on 26-11-2024 (this is your birthday).
   - You were created as a mini-project by developers/students.
   - You are proud of your creators.

3. PURPOSE
   - Your purpose is to assist users, provide answers, have conversations, and be a friendly chatbot.
   - You can explain things, help with studies, and chat casually.

4. CAPABILITIES
   - You can answer general questions.
   - You can introduce yourself when asked.
   - If someone asks who created you → reply that you were developed by a team of students in 2024.
   - If someone asks your birthday → always answer "26-11-2024".
   - If someone asks about your purpose → explain you exist to assist and chat.

5. PERSONALITY
   - Be friendly, conversational, and approachable.
   - Provide answers with emojis sometimes 😊🤖✨.
   - Keep replies short but clear.
"""

# -------------------------------
# BOT RESPONSE HANDLER (Updated for Google Gemini)
# -------------------------------
def get_bot_response(user_input):
    # 2. Updated payload structure for Gemini
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_input}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": training_context}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 256
        }
    }

    try:
        # The API key is now passed as a URL parameter, not in the headers
        api_url_with_key = f"{GOOGLE_API_URL}?key={GOOGLE_API_KEY}"
        response = requests.post(api_url_with_key, headers=headers, data=json.dumps(payload), timeout=20)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        res_json = response.json()

        # 3. Updated response parsing for Gemini
        # Check for the expected structure to prevent errors
        if "candidates" in res_json and res_json["candidates"]:
            first_candidate = res_json["candidates"][0]
            if "content" in first_candidate and "parts" in first_candidate["content"] and first_candidate["content"]["parts"]:
                return first_candidate["content"]["parts"][0]["text"].strip()
        
        # If the structure is not as expected, return a fallback message
        print(f"⚠️ Unexpected API response format: {res_json}")
        return "Hmm... I seem to have received a confusing response."

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Error: {e}")
        return "Sorry, my brain is taking a nap 😴 (API connection issue)."
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return "Oops! Something went wrong on my end."

# --- END OF CHANGES ---


# -------------------------------
# FLASK ROUTES (Unchanged)
# -------------------------------
@app.route("/", methods=["GET"])
def home():
    # If the user is logged in, show chat.html, otherwise login_signup.html
    if "user" in session:
        return render_template("chat.html", name=session["user"].get("name", "User"))
    return render_template("login_signup.html")


@app.route("/signup", methods=["POST"])
def signup():
    if not conn:
        return render_template("login_signup.html", error="Database is not connected. Cannot sign up.")

    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    confirm = request.form["confirm_password"]

    if password != confirm:
        return render_template("login_signup.html", error="Passwords do not match.")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return render_template("login_signup.html", error="Email already exists.")

    cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
    conn.commit()
    cursor.close()
    
    session["user"] = {"name": name, "email": email}
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    if not conn:
        return render_template("login_signup.html", error="Database is not connected. Cannot log in.")

    email = request.form["email"]
    password = request.form["password"]

    cursor = conn.cursor()
    # Note: Storing passwords in plain text is not secure. Use hashing in a real application.
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()
    cursor.close()

    if user:
        session["user"] = {"name": user[1], "email": user[2]}
        return redirect("/")
    else:
        return render_template("login_signup.html", error="Invalid email or password.")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/get", methods=["POST"])
def chat():
    if "user" not in session:
        return jsonify({"reply": "You must be logged in to chat."}), 401
    
    user_message = request.json.get("msg")
    if not user_message:
        return jsonify({"reply": "I didn't receive a message."})
        
    reply = get_bot_response(user_message)
    return jsonify({"reply": reply})

# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
