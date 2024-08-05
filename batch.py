import json
import random
import os
import psycopg2
import random

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from groq import AsyncGroq
from werkzeug.security import generate_password_hash, check_password_hash
import asyncio
import base64
from httpx import URL, Proxy, Timeout, Response, ASGITransport
from httpx import URL, Proxy, Timeout, Response, ASGITransport
import groq
import re
import subprocess
import sys
import logging
import httpx
from threading import Thread
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
bcrypt = Bcrypt(app)

# Use PostgreSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://avnadmin:AVNS_h90GoFmmAWu3da7SkAz@pg-2cd7f170-hamogh-15b6.e.aivencloud.com:13630/defaultdb?sslmode=require'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    conversation = db.Column(db.Text, nullable=False)
    user = db.relationship('User', backref=db.backref('chat_history', lazy=True))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_keys = []
if "GROQ_API_KEY" in os.environ:
    print("GROQ_API_KEY found in .env file, using it and skipping GROQ_API_KEY1-4!")
    api_keys.append(os.getenv("GROQ_API_KEY"))
else:
    if "GROQ_API_KEY1" in os.environ:
        api_keys.append(os.getenv("GROQ_API_KEY1"))
    else:
        print("GROQ_API_KEY1 not found in environment variables. Please set it and try again.")
    if "GROQ_API_KEY2" in os.environ:
        api_keys.append(os.getenv("GROQ_API_KEY2"))
    else:
        print("GROQ_API_KEY2 not found in environment variables. Please set it and try again.")
    if "GROQ_API_KEY3" in os.environ:
        api_keys.append(os.getenv("GROQ_API_KEY3"))
    else:
        print("GROQ_API_KEY3 not found in environment variables. Please set it and try again.")
    if "GROQ_API_KEY4" in os.environ:
        api_keys.append(os.getenv("GROQ_API_KEY4"))
    else:
        print("GROQ_API_KEY4 not found in environment variables. Please set it and try again.")

current_api_key_index = 0

with open(os.path.join(os.path.dirname(__file__), 'templates/default.txt'), 'r') as file:
    default_system_prompt = file.read().strip()

def get_user_system_prompt(user_id):
    chat_history = ChatHistory.query.filter_by(user_id=user_id).first()
    if chat_history:
        conversation_history = json.loads(chat_history.conversation)
        if len(conversation_history) > 0:
            return conversation_history[0]['content']
    return default_system_prompt

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/try_nadia')
def try_nadia():
    if 'username' in session:
        return redirect(url_for('chat'))
    else:
        return redirect(url_for('login_register'))

@app.route('/chat')
def chat():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user:
            chat_history = ChatHistory.query.filter_by(user_id=user.id).first()
            if chat_history:
                conversation_history = [{"role": "system", "content": default_system_prompt}]
                chat_history.conversation = json.dumps(conversation_history)
                db.session.commit()
        return render_template('chat.html', username=session['username'])
    return redirect(url_for('login_register'))


@app.route('/login_register')
def login_register():
    return render_template('login_register.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"success": False, "error": "Email address already registered"})

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, email=email, password=hashed_password)

    try:
        db.session.add(new_user)
        db.session.commit()
        session['username'] = new_user.username
        return jsonify({"success": True, "redirect_url": url_for('chat')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter((User.username == username) | (User.email == username)).first()

    if user and check_password_hash(user.password, password):
        session['username'] = user.username
        chat_history = ChatHistory.query.filter_by(user_id=user.id).first()
        if not chat_history:
            conversation_history = [{"role": "system", "content": default_system_prompt}]
            chat_history = ChatHistory(user_id=user.id, conversation=json.dumps(conversation_history))
            db.session.add(chat_history)
            db.session.commit()
        return jsonify({"success": True, "redirect_url": url_for('chat')})
    else:
        return jsonify({"success": False, "error": "Invalid credentials"})
    
@app.route('/regenerate_response', methods=['POST'])
def regenerate_response():
    if 'username' not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    data = request.get_json()
    user_message = data.get('message')

    chat_history = ChatHistory.query.filter_by(user_id=user.id).first()
    if chat_history:
        conversation_history = json.loads(chat_history.conversation)
    else:
        return jsonify({"success": False, "error": "Conversation history not found"}), 404

    # Remove the last user message and assistant response from the conversation history
    if len(conversation_history) >= 2:
        conversation_history = conversation_history[:-2]

    # Append the user message to the conversation history
    conversation_history.append({"role": "user", "content": user_message})

    response = asyncio.run(get_completion(conversation_history))

    conversation_history.append({"role": "assistant", "content": response['response']})

    chat_history.conversation = json.dumps(conversation_history)
    db.session.commit()

    return jsonify({"success": True, "response": response['response']})



@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_register'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/chat1', methods=['POST'])
def chat1():
    if 'username' not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    chat_history = ChatHistory.query.filter_by(user_id=user.id).first()

    if chat_history:
        conversation_history = json.loads(chat_history.conversation)
    else:
        conversation_history = [{"role": "system", "content": default_system_prompt}]
        chat_history = ChatHistory(user_id=user.id, conversation=json.dumps(conversation_history))
        db.session.add(chat_history)

    user_message = request.json.get('message')

    # Check if the user's message starts with "image"
    if user_message.lower().startswith("image"):
        # Switch to the image preset
        image_preset = "Your image preset text here"
        conversation_history.append({"role": "system", "content": image_preset})

    conversation_history.append({"role": "user", "content": user_message})

    while len(conversation_history) > 1 + 8:
        conversation_history.pop(1)

    response = asyncio.run(get_completion(conversation_history))

    conversation_history.append({"role": "assistant", "content": response['response']})

    chat_history.conversation = json.dumps(conversation_history)
    db.session.commit()

    return jsonify(response)


async def get_completion(conversation_history):
    retries = 15
    delay = 0.1

    # Check if the last message in the conversation history is asking for an image
    if conversation_history and "image" in conversation_history[-1]["content"].lower():
        conversation_history.append({"role": "assistant", "content": "Your image is being generated."})

    for attempt in range(retries):
        api_key, api_index = get_next_api_key()
        logger.info(f"Using API Key: {api_key} (API {api_index + 1})")
        client = AsyncGroq(api_key=api_key)

        try:
            completion = await client.chat.completions.create(
                model="llama3-70b-8192",
                messages=conversation_history,
                temperature=0,
                max_tokens=2000,
                top_p=1,
                stop=None
            )
            if completion is not None:
                break
        except groq.RateLimitError as e:
            retry_after = float(e.response.json()['error'].get('retry_after', delay))
            logger.warning(f"Rate limited, retrying in {retry_after} seconds with the next API key...")
            await asyncio.sleep(retry_after)
            return {'response': "Rate limited, try again in 15 seconds.", 'image_url': None}
        except groq.InternalServerError as e:
            if attempt < retries - 1:
                logger.warning(f"Service unavailable, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay += 0.3
            else:
                logger.error(f"Service unavailable after {retries} attempts: {e}")
                return {'response': "Service is currently unavailable. Please try again later.", 'image_url': None}

    if completion is None:
        return {'response': "Unable to fetch response. Please try again later.", 'image_url': None}

    if hasattr(completion, 'choices') and completion.choices:
        response_text = completion.choices[0].message.content
    else:
        response_text = completion.message['content']

    conversation_history.append({"role": "assistant", "content": response_text})

    image_url = None
    image_url_match = re.search(r'(https?://[^\s]+)', response_text)
    if image_url_match:
        image_url = image_url_match.group(0)
        response_text = response_text.replace(image_url, "")

        # Fetch the image preview with a timeout of 10 seconds
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(image_url)
                    if response.status_code == 200:
                        # Encode the image data as base64
                        image_data = base64.b64encode(response.content).decode('utf-8')
                        image_url = f"data:image/png;base64,{image_data}"
                        break
            except httpx.ReadTimeout:
                if attempt < retries - 1:
                    logger.warning(f"Image URL not loaded, retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Image URL not loaded after {retries} attempts.")
                    image_url = None

    return {'response': response_text.strip(), 'image_url': image_url}





@app.route('/restart', methods=['POST'])
def restart_server():
    logger.info("Restarting server...")
    subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), 'restart_server.py')])
    return '', 204

@app.route('/change_prompt', methods=['POST'])
def change_prompt():
    if 'username' not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    data = request.get_json()
    prompt_file = data.get('prompt_file')

    if prompt_file == 'custom':
        prompt_text = data.get('prompt_text')
    else:
        with open(os.path.join('templates', prompt_file), 'r') as file:
            prompt_text = file.read().strip()

    chat_history = ChatHistory.query.filter_by(user_id=user.id).first()
    if chat_history:
        conversation_history = [{"role": "system", "content": prompt_text}]
        chat_history.conversation = json.dumps(conversation_history)
        db.session.commit()

    return jsonify({"success": True, "message": "System prompt updated successfully"})

@app.route('/reset_prompt', methods=['POST'])
def reset_prompt():
    if 'username' not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    chat_history = ChatHistory.query.filter_by(user_id=user.id).first()
    if chat_history:
        conversation_history = [{"role": "system", "content": default_system_prompt}]
        chat_history.conversation = json.dumps(conversation_history)
        db.session.commit()

    return jsonify({"success": True, "message": "Conversation history and custom prompt reset successfully"})

def get_next_api_key():
    global current_api_key_index
    if len(api_keys) == 1:
        api_key = api_keys[0]
        return api_key, 0
    else:
        api_key = api_keys[current_api_key_index]
        current_api_key_index = (current_api_key_index + 1) % len(api_keys)
        return api_key, current_api_key_index

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', debug=True)
