from flask import Flask, request, jsonify, render_template, redirect, session
import requests
import mysql.connector
import os

from flask import Flask, request, jsonify, render_template, redirect, session
import requests
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

# Clever Cloud MySQL connection
conn = mysql.connector.connect(
    host="bt50vekxtlpwanbpzo6n-mysql.services.clever-cloud.com",
    user="uybdk7ycpidf4axw",
    password="ke39xPKLUbqr6PBdH351",
    database="bt50vekxtlpwanbpzo6n"
)

# Together API
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
TOGETHER_API_KEY = os.environ.get(
    "TOGETHER_API_KEY",
    "9d968436e2919496ccd0e248f3e20847160c09da3befd56ad3baef31db9ab649"
)

headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

# -------------------------------
# CUSTOM TRAINING DATA
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
# BOT RESPONSE HANDLER
# -------------------------------
def get_bot_response(user_input):
    data = {
        "model": "meta-llama/Llama-3-8b-chat-hf",
        "messages": [
            {"role": "system", "content": training_context},   # inject training on every chat
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.7,
        "max_tokens": 256,
        "top_p": 0.9
    }
    try:
        response = requests.post(TOGETHER_API_URL, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        res_json = response.json()

        if "choices" in res_json and len(res_json["choices"]) > 0:
            return res_json["choices"][0]["message"]["content"].strip()
        else:
            return "Hmm... I didn’t understand that."
    except Exception as e:
        print(f"❌ API Error: {e}")
        return "Sorry, my brain is taking a nap 😴 (API issue)."

# -------------------------------
# FLASK ROUTES
# -------------------------------
@app.route("/", methods=["GET"])
def home():
    return render_template("login_signup.html", show_chat="user" in session)

@app.route("/signup", methods=["POST"])
def signup():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    confirm = request.form["confirm_password"]

    if password != confirm:
        return render_template("login_signup.html", show_chat=False, error="Passwords do not match.")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return render_template("login_signup.html", show_chat=False, error="Email already exists.")

    cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
    conn.commit()
    session["user"] = {"name": name, "email": email}
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()

    if user:
        session["user"] = {"name": user[1], "email": user[2]}
        return redirect("/")
    else:
        return render_template("login_signup.html", show_chat=False, error="Check your email and password")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/get", methods=["POST"])
def chat():
    user_message = request.json["msg"]
    reply = get_bot_response(user_message)
    return jsonify({"reply": reply})

# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
