Nadia: AI-Powered Chat Interface 🌐


Nadia is an AI-powered chatbot designed for seamless interactions, image generation, code support, LaTeX rendering, and more. With a sleek modern interface and the capability to switch between various system prompts, Nadia is built to provide a flexible, dynamic user experience.

Features ✨
Real-Time Chat: Engage with an AI that supports natural language conversations.


Image Generation: Generate images using specific prompts with a dedicated image system.


LaTeX Rendering: Automatically renders LaTeX syntax in messages.


Theming Options: Choose between different themes like Modern and CLI for the chat interface.

Customizable System Prompts: Use preset system prompts or define your own custom ones.

Streaming Tokens: Experience dynamic token-based responses as they arrive from the backend.

Getting Started 🚀
Prerequisites
Python 3.8+
Node.js
Pygame (if using the sample game)
Installation
Clone the repository:

bash
Copy code
git clone https://github.com/yourusername/nadia-chat.git
cd nadia-chat
Backend Setup: Install the required Python dependencies:

bash
Copy code
pip install -r requirements.txt
Frontend Setup: Install the necessary Node.js packages for the frontend:

bash
Copy code
npm install
Run the Application: Start the backend server:

bash
Copy code
python app.py
Then, in a new terminal, start the frontend:

bash
Copy code
npm start
Access the Website: Open your browser and navigate to:

arduino
Copy code
http://localhost:5000
Usage 🛠️
Chat Interface: Type your message into the chat box, hit "Enter", and let Nadia respond.
Image Generation: Send prompts starting with image <description> to request AI-generated images.
Code Embeds: View beautifully formatted code blocks with language-specific highlighting and a "Copy Code" button.
LaTeX Support: Use LaTeX syntax within your chat to get beautifully rendered equations.
Changing Themes
Switch between the Modern and CLI themes in the settings panel located in the upper right corner of the chat interface.

Custom Prompts
Go to the settings panel.
Select from preset prompts (e.g., mathsys.txt, codesys.txt) or create your own custom system prompt.
Screenshots 📸
Modern chat interface with syntax highlighting and LaTeX support.

Technologies Used 🛠️
Frontend: HTML5, CSS3, JavaScript (Prism.js, MathJax)
Backend: Python (Flask), Node.js
AI Model: Groq, Stable Diffusion for image generation
Socket.IO: Real-time communication between frontend and backend
Contributing 🤝
We welcome contributions! Feel free to submit a pull request or file an issue.

Fork the repository
Create a new branch (git checkout -b feature-branch)
Make your changes
Push to the branch (git push origin feature-branch)
Open a pull request
License 📝
This project is licensed under the MIT License. See the LICENSE file for details.