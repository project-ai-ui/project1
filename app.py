from flask import Flask, request, jsonify, render_template, redirect, session
import requests
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")  # safer for deployment

# Clever Cloud MySQL connection
conn = mysql.connector.connect(
    host="bt50vekxtlpwanbpzo6n-mysql.services.clever-cloud.com",
    user="uybdk7ycpidf4axw",
    password="ke39xPKLUbqr6PBdH351",
    database="bt50vekxtlpwanbpzo6n"
)

# Together API
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY", "9d968436e2919496ccd0e248f3e20847160c09da3befd56ad3baef31db9ab649")

headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

# Full intro prompts list
intro_prompts = [
    "tell me about yourself", "tell me something about yourself", "tell me about you",
    "about yourself", "about you", "give me your details", "what are you",
    "what is your name", "whats your name", "what’s your name", "who are you",
    "who you are", "who r u", "who u are", "who are u",
    "could you tell me about yourself", "please tell me about yourself",
    "i would like to know about you", "i’d like to know about you",
    "may i know about you", "can you tell me about you", "can you introduce yourself",
    "please introduce yourself", "would you mind introducing yourself",
    "can you share something about yourself",
    "sup who are you", "hey what are you", "hi who are u", "yo tell me about urself",
    "tell me about u bro", "yo who are you", "dude who are you", "tell me about you man",
    "so who are you", "ay who are you", "hru who are you",
    "describe yourself", "give me your intro", "what do you do",
    "whats your purpose", "what’s your purpose", "what’s your role",
    "what can you do", "what do you know", "what are you capable of", "how do you work",
    "what are you here for", "what do you exist for", "what can u do",
    "who made you", "who created you", "who built you", "who developed you",
    "where were you made", "how were you created", "what are you made for",
    "what technology are you based on", "how did you come into existence",
    "so who are you really", "who are you in real life", "are you human",
    "are you a robot", "are you an ai", "are you alive", "what species are you",
    "are you real", "are you sentient", "are you conscious"
]

def is_intro_prompt(user_input: str) -> bool:
    """Check if user message matches any intro prompt exactly (case-insensitive)."""
    return user_input.lower().strip() in intro_prompts

def get_bot_response(user_input):
    # If exact intro prompt match
    if is_intro_prompt(user_input):
        return (
            "Hi! I’m VINCI – Virtual Interactive Natural Chatbot Interface 🤖. "
            "I’m your AI assistant, here to help answer questions, share knowledge, "
            "and make conversations more engaging!"
        )

    # Otherwise use Together API
    data = {
        "model": "meta-llama/Llama-3-8b-chat-hf",
        "messages": [
            {"role": "system", "content": "You are a helpful AI chatbot assistant."},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.7,
        "max_tokens": 256,
        "top_p": 0.9
    }
    try:
        response = requests.post(TOGETHER_API_URL, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content'].strip()
    except:
        return "Sorry, something went wrong."

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
    session["user"] = name
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()

    if user:
        session["user"] = user[1]  # name
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

# Render-compatible run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
