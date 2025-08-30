# 🎙️ SARC AI Voice Assistant  

An intelligent, real-time **AI-powered voice assistant** built with **FastAPI, WebSockets, AssemblyAI, Murf TTS, and Gemini AI**.  
It can listen 🎧, transcribe ✍️, understand 🤖, and respond back 🔊 in natural voice.  

---

## 🚀 Live Demo  
👉 [Live Demo Link](#) *(https://sarc-ai-voice-assisstant.onrender.com/)*  

---

## 📸 Proof of Work  
- ![Homepage Screenshot](https://i.postimg.cc/t40qwh32/Screenshot-2025-08-31-023341-1.png)  
- ![Voice Interaction Screenshot](https://i.postimg.cc/fbPD7mRc/Screenshot-2025-08-31-024410.png)  
  

---

## ✨ Features  
- 🎙️ **Real-time voice recording & streaming** (mic → backend)  
- 📝 **Speech-to-Text (STT)** using AssemblyAI  
- 🤖 **AI responses** powered by Gemini  
- 🔊 **Text-to-Speech (TTS)** responses via Murf API  
- 💬 **Chat-like UI** with timestamps & auto-scroll  
- 📊 **Stats tracking**: words, characters, messages  
- ⚙️ **API Key Manager** (save/clear keys locally)  
- 🔔 Notifications & status updates  
- 🧹 Double-click to clear chat history  
- ❌ Error handling (mic, API, WebSocket issues)  

---

## 🛠️ Tech Stack  
**Frontend:** HTML, CSS, JavaScript  
**Backend:** Python (FastAPI, WebSockets)  
**APIs/Services:**  
- AssemblyAI (Speech-to-Text)  
- Gemini (Conversational AI)  
- Murf (Text-to-Speech)  
- TMDB (optional for movie-related queries)  

---

## ⚙️ Installation & Setup  

```bash
# 1. Clone the repo
git clone https://github.com/Ekta87/SARC_AI_Voice_Assisstant.git
cd SARC_AI_Voice_Assisstant

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate    # (Linux/Mac)
venv\Scripts\activate       # (Windows)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn main:app --reload

# 5. Open in browser
http://127.0.0.1:8000
```

---

## 🔄 Usage Flow  

1. Open the app in browser  
2. Add your API keys (AssemblyAI, Murf, Gemini)  
3. Click 🎤 Record → Speak → Audio sent to backend  
4. Backend → STT → Gemini → TTS → Response generated  
5. Response text + audio displayed in UI  
6. Chat history + stats update automatically  

---

## 🔀 Architecture Flow  

```mermaid
flowchart LR
    A[🎤 User Speaks] --> B[🌐 Browser (main.js)]
    B -->|WebSocket Audio Stream| C[⚡ FastAPI Backend]
    C --> D[📝 AssemblyAI STT]
    D --> E[🤖 Gemini AI Processing]
    E --> F[🔊 Murf TTS]
    F -->|Audio Response| C
    C -->|Text + Audio| B
    B --> G[💬 Chat UI + 🔊 Audio Player]
```

---

## 📂 Project Structure  

```bash
SARC_AI_Voice_Assistant/
├── main.py              # Backend (FastAPI + WebSocket server)
├── requirements.txt     # Dependencies
├── .gitignore           # Ignored files
├── static/
│   ├── main.js          # Frontend logic (UI + API key + WS streaming)
└── templates/
    └── index.html       # Main HTML UI
```

---

## 📂 Project Structure Explained  

- **main.py** → Backend server with FastAPI + WebSocket handling.  
- **static/main.js** → Frontend JS for mic streaming, chat UI, API keys, notifications.  
- **templates/index.html** → Basic UI (chat container, buttons, modals).  
- **requirements.txt** → Python dependencies for backend.  

---

## 🌱 Future Enhancements  
- 🌍 Multilingual support  
- 📱 Responsive mobile-first UI  
- 💾 Persistent chat history (DB integration)  
- 🧠 Customizable AI personalities  
- 🔐 Encrypted storage for API keys  

---

## 👤 Author & Acknowledgments 
- **Ekta Verma** 
- **LinkedIn:** https://www.linkedin.com/in/ekta-verma-4b9436251/ 
- **GitHub:** https://github.com/Ekta87 

This project was built as part of the **#30DaysOfAIVoiceAgents** challenge. A big thank you to the organizers and the community for their support and inspiration.  

---
