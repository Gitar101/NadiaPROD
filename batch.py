import json
import random
import os
import time

import psycopg2
import random

import requests
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://avnadmin:AVNS_h90GoFmmAWu3da7SkAz@pg-2cd7f170-hamogh-15b6.e.aivencloud.com:13630/defaultdb?sslmode=require'
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
        image_preset = "Image"
        conversation_history.append({"role": "system", "content": image_preset})

    conversation_history.append({"role": "user", "content": user_message})

    while len(conversation_history) > 1 + 8:
        conversation_history.pop(1)

    response = asyncio.run(get_completion(conversation_history))

    conversation_history.append({"role": "assistant", "content": response['response']})

    chat_history.conversation = json.dumps(conversation_history)
    db.session.commit()

    return jsonify(response)




async def get_completion(conversation_history, websocket=None):
    retries = 20
    delay = 0.5

    for attempt in range(retries):
        api_key, api_index = get_next_api_key()
        logger.info(f"Using API Key:  (API {api_index + 1})")
        client = AsyncGroq(api_key=api_key)

        try:
            # Use streaming option if available
            completion = await client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=conversation_history,
                temperature=0.5,
                max_tokens=2500,
                top_p=1,
                stop=None,
                stream=True  # Enabling streaming
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

    response_text = ""
    image_url = None

    # Stream each token as it is received
    try:
        total_tokens = 0
        start_time = time.time()

        async for chunk in completion:
            if hasattr(chunk, 'choices') and chunk.choices:
                # Extract the content from the 'delta' attribute
                delta_content = chunk.choices[0].delta.content if chunk.choices[0].delta.content else ''

                response_text += delta_content

                # If connected to a WebSocket, send streamed response incrementally
                if websocket is not None:
                    await websocket.send_json({'response': response_text.strip()})

                logger.info("Streaming token: %s", delta_content)

                # Update total tokens
                total_tokens += len(delta_content.split())

        # Calculate average tokens per second for the entire response
        elapsed_time = time.time() - start_time
        print(elapsed_time)
        if elapsed_time > 0:  # Avoid division by zero
            average_tokens_per_second = total_tokens / elapsed_time
            logger.info("Average tokens per second: %s", average_tokens_per_second)
    except Exception as e:
        logger.error(f"Error during streaming: {e}")
        return {'response': "Error occurred during streaming. Please try again later.", 'image_url': None}

    # Process image prompt if the response contains "IMAGEN:"
    # Process image prompt if the response contains "IMAGEN:"
    lines = response_text.split('\n', 1)
    first_line = lines[0].strip()

    if first_line.startswith("IMAGEN:"):
        logger.info("Processing Flux prompt...")

        # Updated regex to include width and height
        match = re.search(r"IMAGEN:(.*?)(?:NEGATIVE:(.*?))? W:\s*(\d+)\s*H:\s*(\d+)", first_line, re.DOTALL)
        if match:
            image_prompt = match.group(1).strip().replace(' ', '%20')
            negative_prompt = match.group(2).strip().replace(' ', '%20') if match.group(2) else ""
            width = match.group(3)  # Extract width
            height = match.group(4)  # Extract height

            # Construct the image generation URL with width and height
            image_generation_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width={width}&height={height}&model=flux&negative={negative_prompt}&nologo=True"
            logger.info("Generated image URL: %s", image_generation_url)

            # Send request to generate the image
            requests.post(image_generation_url)

            # Fetch the image preview with a timeout of 60 seconds
            for attempt in range(retries):
                try:
                    async with httpx.AsyncClient(timeout=60) as client:
                        response = await client.get(image_generation_url)
                        if response.status_code == 200:
                            # Encode the image data as base64
                            image_data = base64.b64encode(response.content).decode('utf-8')
                            image_url = f"data:image/png;base64,{image_data}"
                            logger.info("Image fetched and encoded successfully.")
                            break
                        else:
                            logger.error(f"Failed to fetch image. Status code: {response.status_code}")
                except httpx.ReadTimeout:
                    if attempt < retries - 1:
                        logger.warning(f"Image URL not loaded, retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        logger.error(f"Image URL not loaded after {retries} attempts.")
                        image_url = None

        # Clean up the response text
        remaining_text = lines[1].strip() if len(lines) > 1 else ""
        response_text = re.sub(r"IMAGEN:.*(?:NEGATIVE:.*)?", "", remaining_text, flags=re.DOTALL).strip()
        logger.info("Cleaned response text: %s", response_text)


    # Append the final response text to conversation history
    conversation_history.append({"role": "assistant", "content": response_text.strip()})

    # Final logging and return
    logger.info("Final response text: %s", response_text)
    return {'response': response_text.strip(), 'image_url': image_url}






@app.route('/regenerate_response', methods=['POST'])
def regenerate_response():
    if 'username' not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    chat_history = ChatHistory.query.filter_by(user_id=user.id).first()
    if not chat_history:
        return jsonify({"success": False, "error": "No conversation history found."}), 404

    conversation_history = json.loads(chat_history.conversation)

    # Find the last user question and clear conversation history
    user_conversation = [msg for msg in conversation_history if msg['role'] == 'user']
    assistant_conversation = [msg for msg in conversation_history if msg['role'] == 'assistant']

    if not user_conversation or not assistant_conversation:
        return jsonify({"success": False, "error": "No previous conversation to regenerate."}), 400

    # Keep conversation history up to the last user message
    last_user_message = user_conversation[-1]['content']
    conversation_history = [{"role": "system", "content": default_system_prompt}]  # Reset history
    conversation_history.append({"role": "user", "content": last_user_message})

    # Generate new response
    response = asyncio.run(get_completion(conversation_history))

    # Update conversation history with new response
    conversation_history.append({"role": "assistant", "content": response['response']})
    chat_history.conversation = json.dumps(conversation_history)
    db.session.commit()

    return jsonify(response)

#asdads




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
    try:
        with app.app_context():
            db.create_all()
        app.run(host='0.0.0.0', port ='7000', debug=True)
    finally:
        asyncio.get_event_loop().close()
