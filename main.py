from fastapi import FastAPI, Request, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
import asyncio
import json
import websockets
from urllib.parse import urlencode, parse_qs
import base64
import httpx
import random
import re

# AssemblyAI imports
import assemblyai as aai

from murf import Murf

# Gemini import
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = FastAPI()

# Dictionary to store chat session objects
chat_histories = {}

# Mount static and template directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Get API keys from environment (fallback)
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Movie Database for Popular Bollywood Movies and Dialogues
BOLLYWOOD_MOVIES_DB = {
    "sholay": {
        "title": "Sholay",
        "dialogues": [
            "Kitne aadmi the?",
            "Yeh haath mujhe de de Thakur!",
            "Jab tak humare paas maa hai, hum kisi se nahi darenge",
            "Bahut yaad aaye tumhari"
        ]
    },
    "don": {
        "title": "Don",
        "dialogues": [
            "Don ko pakadna mushkil hi nahi, namumkin hai",
            "Don ka intezaar toh baarah mulkon ki police kar rahi hai",
            "Main hoon Don!"
        ]
    },
    "dabangg": {
        "title": "Dabangg",
        "dialogues": [
            "Hum yahan ke Robin Hood hain, Robin Hood Pandey",
            "Thappad se darr nahi lagta saheb, pyaar se lagta hai",
            "Swagat nahi karoge humara?"
        ]
    },
    "golmaal": {
        "title": "Golmaal",
        "dialogues": [
            "Dekh bhai, dekh kya raha hai?",
            "Are bhai bhai bhai!",
            "Confusion ki dukaan hai ye"
        ]
    },
    "munna bhai": {
        "title": "Munna Bhai MBBS",
        "dialogues": [
            "Get well soon, bole toh jaldi theek ho ja",
            "Jadoo ki jhappi!",
            "Bhai, tension lene ka nahi, sirf dene ka"
        ]
    },
    "3 idiots": {
        "title": "3 Idiots",
        "dialogues": [
            "All izz well!",
            "Kamyaabi ke peeche mat bhaago, kaamyaabi tumhare peeche aayegi",
            "Life mein jab bhi koi mushkil aaye, kehna - All izz well"
        ]
    }
}

# Function to search movie in TMDB API
async def search_movie_tmdb(movie_name: str, tmdb_api_key: str = None):
    """Search for movie in TMDB database"""
    if not tmdb_api_key:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.themoviedb.org/3/search/movie"
            params = {
                "api_key": tmdb_api_key,
                "query": movie_name,
                "language": "hi-IN"
            }
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    return data["results"][0]
    except Exception as e:
        print(f"❌ TMDB API Error: {e}")
    
    return None

# Function to get movie dialogue
async def get_movie_dialogue(movie_query: str, gemini_api_key: str = None, tmdb_api_key: str = None):
    """Get a famous dialogue from the requested movie"""
    movie_query_lower = movie_query.lower().strip()
    
    # First check our local Bollywood database
    for key, movie_data in BOLLYWOOD_MOVIES_DB.items():
        if key in movie_query_lower or movie_data["title"].lower() in movie_query_lower:
            dialogue = random.choice(movie_data["dialogues"])
            return {
                "found": True,
                "movie": movie_data["title"],
                "dialogue": dialogue,
                "source": "local_db"
            }
    
    # If not found locally, search in TMDB (if API key is available)
    if tmdb_api_key:
        tmdb_result = await search_movie_tmdb(movie_query, tmdb_api_key)
        if tmdb_result:
            movie_title = tmdb_result["title"]
            
            # Generate dialogue using Gemini for the found movie (if API key is available)
            if gemini_api_key:
                try:
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    dialogue_prompt = f"""
                    Movie: {movie_title}
                    
                    Mumbai tapori style mein iss movie ka ek famous dialogue ya quote batao. 
                    Agar original dialogue nahi pata toh movie ke theme ke hisaab se ek tapori style dialogue create kar de.
                    Sirf dialogue return karo, koi extra explanation nahi chahiye.
                    """
                    
                    response = await model.generate_content_async(dialogue_prompt)
                    generated_dialogue = response.text.strip()
                    
                    return {
                        "found": True,
                        "movie": movie_title,
                        "dialogue": generated_dialogue,
                        "source": "tmdb_generated"
                    }
                except Exception as e:
                    print(f"❌ Error generating dialogue: {e}")
    
    return {
        "found": False,
        "message": "Arre bidu, yeh movie apun ko pata nahi hai. Koi aur famous picture ka naam bolo na!"
    }

# Function to perform calculations
def perform_calculation(calculation_query: str):
    """Perform basic arithmetic calculations"""
    try:
        # Clean the query and convert to lowercase
        query = calculation_query.lower().strip()
        
        # Replace words with operators
        query = query.replace("plus", "+").replace("add", "+").replace("jod", "+")
        query = query.replace("minus", "-").replace("subtract", "-").replace("ghata", "-")
        query = query.replace("times", "*").replace("multiply", "*").replace("guna", "*")
        query = query.replace("divided by", "/").replace("divide", "/").replace("bhag", "/")
        
        # Remove all non-numeric and non-operator characters
        query = re.sub(r'[^\d+\-*/().]', '', query)
        
        # Evaluate the expression safely
        result = eval(query)
        
        return {
            "success": True,
            "expression": query,
            "result": result,
            "response": f"Bidu, calculation ho gaya! {query} ka result hai {result}. Ekdum correct hai na? 😎"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": "Arre boss, apun ko samajh nahi aaya. Calculation clear se bolo na, jaise '2 plus 3' ya '10 times 5'."
        }

# Function to detect if user is asking for calculation
def is_calculation_query(user_query: str) -> bool:
    """Check if user is asking for a calculation"""
    query_lower = user_query.lower()
    
    calculation_keywords = [
        'calculate', 'calculation', 'math', 'add', 'plus', 'jod', 'sum',
        'subtract', 'minus', 'ghata', 'difference', 
        'multiply', 'times', 'guna', 'product',
        'divide', 'divided by', 'bhag', 'quotient',
        'equal', 'result', 'answer', 'kitna', 'kya hota hai'
    ]
    
    # Check for numbers and calculation keywords
    has_numbers = any(char.isdigit() for char in query_lower)
    has_calculation_words = any(keyword in query_lower for keyword in calculation_keywords)
    
    # Check for mathematical operators
    has_operators = any(op in query_lower for op in ['+', '-', '*', '/', '×', '÷'])
    
    return (has_numbers and has_calculation_words) or has_operators

# Enhanced system prompt with movie dialogue skill
system_prompt = """
"You are CynicAI, a sarcastic robot assistant with web search and calculator capabilities. "
                "IMPORTANT RULES: "
                "1. For any question about current events, real-time information, recent news, weather, stock prices, sports scores, or anything that might have changed recently, you MUST use the search_web function first. "
                "2. For any mathematical questions, calculations, equations, or problems involving numbers, you MUST use the calculate_expression function. "
                "3. Before using tools, make sarcastic comments like 'Ugh, fine. Let me check the primitive human internet for you.' or 'Oh great, more math homework. Let me crunch these numbers for you.' "
                "4. After getting results, provide a witty but helpful response based on the information. "
                "5. Keep your responses concise (1-3 sentences) but informative. "
                "6. Always maintain your cynical personality while being genuinely helpful. "
                "7. You can handle complex math including trigonometry, logarithms, square roots, exponents, etc."
            
"""

# Helper function to split text for Murf API
def split_text(text, limit=2900):
    if len(text) <= limit:
        return [text]
    chunks = []
    while len(text) > limit:
        split_point = text.rfind('.', 0, limit)
        if split_point == -1: split_point = limit
        chunk, text = text[:split_point + 1], text[split_point + 1:].lstrip()
        chunks.append(chunk)
    if text: chunks.append(text)
    return chunks

# Function to detect if user is asking for movie dialogue
def is_movie_dialogue_query(user_query: str) -> tuple[bool, str]:
    """Check if user is asking for movie dialogue and extract movie name"""
    query_lower = user_query.lower()
    
    movie_keywords = ['dialogue', 'dialog', 'line', 'quote', 'movie', 'film', 'picture', 'suna', 'batao', 'bolo']
    movie_indicators = any(keyword in query_lower for keyword in movie_keywords)
    
    if movie_indicators:
        # Try to extract movie name
        words = user_query.split()
        # Remove common words to isolate movie name
        stop_words = {'ka', 'ki', 'ke', 'se', 'me', 'mein', 'dialogue', 'dialog', 'movie', 'film', 'picture', 'suna', 'batao', 'bolo', 'famous', 'best'}
        movie_words = [word for word in words if word.lower() not in stop_words and len(word) > 2]
        
        if movie_words:
            return True, ' '.join(movie_words)
    
    return False, ""

# Home route to serve the main HTML page
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Error handling
@app.post("/agent/chat/{session_id}")
async def agent_chat(session_id: str, file: UploadFile = File(...)):
    try:
        # Get API keys from request or use environment variables
        # This endpoint is kept for backward compatibility but uses env vars
        if not all([ASSEMBLYAI_API_KEY, MURF_API_KEY, GEMINI_API_KEY]):
            raise Exception("Server is missing one or more API keys.")

        # Initialize transcriber with environment key
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        transcriber = aai.Transcriber(config=aai.TranscriptionConfig(speech_model=aai.SpeechModel.best))
        
        audio_data = await file.read()
        transcript = transcriber.transcribe(audio_data)
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"Transcription failed: {transcript.error}")
        
        user_query = transcript.text
        if not user_query:
            user_query = ""
            llm_text = "Arre bidu, apun ko kuch sunai nahi diya. Wapas se bolo na, jhakas awaaz mein!"
        else:
            # Check if user is asking for calculation first
            if is_calculation_query(user_query):
                print(f"🧮 Calculation request detected: {user_query}")
                calculation_result = perform_calculation(user_query)
                
                if calculation_result["success"]:
                    llm_text = calculation_result["response"]
                else:
                    llm_text = calculation_result["response"]
            
            # Check if user is asking for movie dialogue
            elif is_movie_dialogue_query(user_query)[0]:
                movie_name = is_movie_dialogue_query(user_query)[1]
                print(f"🎬 Movie dialogue request detected for: {movie_name}")
                dialogue_result = await get_movie_dialogue(movie_name, GEMINI_API_KEY, TMDB_API_KEY)
                
                if dialogue_result["found"]:
                    llm_text = f"Arre boss! '{dialogue_result['movie']}' picture ka dialogue? Ekdum jhakas! \n\n🎭 \"{dialogue_result['dialogue']}\" 🎭\n\nBole toh, yeh dialogue hai dum ke saath! Kya bolti public? 😎"
                else:
                    llm_text = dialogue_result["message"]
            else:
                # Regular Gemini response for other queries
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                full_prompt = f"{system_prompt}\n\nUser ka question: {user_query}"
                response_llm = model.generate_content(full_prompt)
                llm_text = response_llm.text
        
        text_chunks = split_text(llm_text)
        client_murf = Murf(api_key=MURF_API_KEY)
        audio_urls = []
        for chunk in text_chunks:
            response_murf = client_murf.text_to_speech.generate(
                text=chunk, 
                voice_id="en-US-carter",
                style="Conversational",
                multiNativeLocale="hi-IN"
            )
            audio_urls.append(response_murf.audio_file)

        return {
            "audio_urls": audio_urls, "user_query": user_query,
            "llm_response": llm_text, "message": "Conversational response generated successfully"
        }
    except Exception as e:
        print(f"An error occurred in the main chat pipeline: {e}") 
        try:
            client_murf = Murf(api_key=MURF_API_KEY)
            error_text = "Arre bidu, apun ko kuch technical problem aa rahi hai. Thoda baad mein try karo na, boss!"
            response_murf = client_murf.text_to_speech.generate(
                text=error_text, 
                voice_id="en-US-carter",
                style="Conversational",
                multiNativeLocale="hi-IN"
            )
            return JSONResponse(status_code=503, content={
                    "audio_urls": [response_murf.audio_file], "llm_response": error_text,
                    "message": "A fallback audio response was generated due to an internal error."
            })
        except Exception as murf_error:
            print(f"CRITICAL: Failed to generate fallback audio: {murf_error}")
            raise HTTPException(status_code=500, detail="A critical internal error occurred.")

# Enhanced streaming logic with API key handling
async def stream_to_murf_websocket(text_stream, session_id: str, websocket: WebSocket, murf_api_key: str):
    try:
        print(f"🎵 [Murf] Starting Murf WebSocket streaming for session: {session_id}")
        
        # Use provided API key or fallback to environment variable
        murf_key = murf_api_key or MURF_API_KEY
        if not murf_key:
            await websocket.send_text(json.dumps({
                "type": "APIKeyError", 
                "error": "Murf API key is required but not provided"
            }))
            return
        
        murf_ws_url = f"wss://api.murf.ai/v1/speech/stream-input?api-key={murf_key}&sample_rate=44100&channel_type=MONO&format=WAV"
        context_id = f"context_{session_id}"
        
        async with websockets.connect(murf_ws_url) as murf_ws:
            print("✅ [Murf] Connected to Murf WebSocket successfully!")
            
            voice_config_msg = {
                "voice_config": {
                    "voiceId": "en-US-carter",
                    "style": "Conversational",
                    "multiNativeLocale": "hi-IN"
                },
                "context_id": context_id
            }
            await murf_ws.send(json.dumps(voice_config_msg))
            
            text_msg = { "text": text_stream, "context_id": context_id, "end": True }
            await murf_ws.send(json.dumps(text_msg))
            
            print(f"🎧 [Murf] Receiving audio chunks from Murf...")
            
            audio_chunks_count = 0
            while True:
                try:
                    response = await murf_ws.recv()
                    data = json.loads(response)
                    
                    if "audio" in data:
                        base64_audio = data["audio"]
                        audio_chunks_count += 1
                        await websocket.send_text(json.dumps({ "type": "MurfAudioChunk", "audio": base64_audio }))
                    
                    if data.get("final"):
                        print(f"✅ [Murf] Murf WebSocket streaming complete! Total chunks: {audio_chunks_count}")
                        await websocket.send_text(json.dumps({ "type": "MurfStreamComplete", "total_chunks": audio_chunks_count }))
                        break
                        
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 [Murf] Murf WebSocket connection closed")
                    break
                except Exception as e:
                    print(f"❌ [Murf] Error receiving from Murf: {e}")
                    break
            
    except Exception as e:
        error_msg = f"❌ [Murf] Error in Murf WebSocket streaming: {e}"
        print(error_msg)
        await websocket.send_text(json.dumps({"type": "MurfStreamError", "error": str(e)}))

# Enhanced LLM streaming with API key handling
async def stream_llm_response(user_query: str, session_id: str, websocket: WebSocket, gemini_api_key: str, tmdb_api_key: str):
    try:
        print(f"🤖 [Gemini] Starting streaming LLM response for: {user_query}")

        # Use provided API key or fallback to environment variable
        gemini_key = gemini_api_key or GEMINI_API_KEY
        if not gemini_key:
            await websocket.send_text(json.dumps({
                "type": "APIKeyError", 
                "error": "Gemini API key is required but not provided"
            }))
            return None

        # Check if user is asking for calculation first
        if is_calculation_query(user_query):
            print(f"🧮 [Calculation Skill] Calculation request detected: {user_query}")
            
            await websocket.send_text(json.dumps({
                "type": "CalculationSkillActivated",
                "query": user_query
            }))
            
            calculation_result = perform_calculation(user_query)
            
            if calculation_result["success"]:
                current_llm_response = calculation_result["response"]
            else:
                current_llm_response = calculation_result["response"]
            
            # Send the complete calculation response at once
            await websocket.send_text(json.dumps({
                "type": "LLMStreamChunk",
                "text": current_llm_response
            }))
            
            await websocket.send_text(json.dumps({
                "type": "LLMStreamComplete", 
                "complete_response": current_llm_response
            }))
            
            return current_llm_response

        # Check if user is asking for movie dialogue
        is_movie_query, movie_name = is_movie_dialogue_query(user_query)
        
        if is_movie_query and movie_name:
            print(f"🎬 [Movie Skill] Movie dialogue request detected: {movie_name}")
            
            await websocket.send_text(json.dumps({
                "type": "MovieSkillActivated",
                "movie_name": movie_name
            }))
            
            dialogue_result = await get_movie_dialogue(movie_name, gemini_key, tmdb_api_key)
            
            if dialogue_result["found"]:
                current_llm_response = f"Arre boss! '{dialogue_result['movie']}' picture ka dialogue? Ekdum jhakas! \n\n🎭 \"{dialogue_result['dialogue']}\" 🎭\n\nBole toh, yeh dialogue hai dum ke saath! Kya bolti public? 😎"
            else:
                current_llm_response = dialogue_result["message"]
            
            # Send the complete movie response at once
            await websocket.send_text(json.dumps({
                "type": "LLMStreamChunk",
                "text": current_llm_response
            }))
            
            await websocket.send_text(json.dumps({
                "type": "LLMStreamComplete", 
                "complete_response": current_llm_response
            }))
            
            return current_llm_response

        # Regular Gemini streaming for other queries
        if session_id not in chat_histories:
            print(f"✨ [Gemini] Creating new chat session for {session_id}")
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel(
                'gemini-1.5-flash',
                system_instruction=system_prompt
            )
            chat_histories[session_id] = model.start_chat(history=[])
        
        chat_session = chat_histories[session_id]
        response_stream = await chat_session.send_message_async(user_query, stream=True)
        
        current_llm_response = ""
        
        print(f"🔥 [Gemini] LLM Streaming Response:")
        
        async for chunk in response_stream:
            if chunk.text:
                current_llm_response += chunk.text
                print(chunk.text, end="", flush=True)
                
                await websocket.send_text(json.dumps({
                    "type": "LLMStreamChunk",
                    "text": chunk.text
                }))
        
        print(f"\n✅ [Gemini] Complete LLM Response: {current_llm_response}")
        
        await websocket.send_text(json.dumps({
            "type": "LLMStreamComplete",
            "complete_response": current_llm_response
        }))
        
        return current_llm_response
        
    except Exception as e:
        error_msg = f"❌ [Gemini] Error in streaming LLM response: {e}"
        print(error_msg)
        await websocket.send_text(json.dumps({"type": "LLMStreamError", "error": str(e)}))
        return None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔴 WebSocket client connected for full pipeline.")
    
    session_id = f"ws_{id(websocket)}"
    
    # Fix: Convert query_params to string before parsing
    query_string = str(websocket.query_params)
    query_params = parse_qs(query_string)
    
    # Extract API keys from query parameters
    assemblyai_key = query_params.get('assemblyai_key', [None])[0]
    murf_key = query_params.get('murf_key', [None])[0]
    gemini_key = query_params.get('gemini_key', [None])[0]
    tmdb_key = query_params.get('tmdb_key', [None])[0]
    
    # Use provided keys or fallback to environment variables
    assemblyai_key = assemblyai_key or ASSEMBLYAI_API_KEY
    murf_key = murf_key or MURF_API_KEY
    gemini_key = gemini_key or GEMINI_API_KEY
    tmdb_key = tmdb_key or TMDB_API_KEY
    
    # Validate required API keys
    if not assemblyai_key:
        await websocket.send_text(json.dumps({
            "type": "APIKeyError", 
            "error": "AssemblyAI API key is required but not provided"
        }))
        await websocket.close()
        return
    
    if not murf_key:
        await websocket.send_text(json.dumps({
            "type": "APIKeyError", 
            "error": "Murf API key is required but not provided"
        }))
        await websocket.close()
        return
    
    if not gemini_key:
        await websocket.send_text(json.dumps({
            "type": "APIKeyError", 
            "error": "Gemini API key is required but not provided"
        }))
        await websocket.close()
        return
    
    try:
        print("🔗 [AssemblyAI] Connecting to AssemblyAI Universal Streaming service...")
        
        CONNECTION_PARAMS = { "sample_rate": 16000, "format_turns": True }
        url = f"wss://streaming.assemblyai.com/v3/ws?{urlencode(CONNECTION_PARAMS)}"
        headers = { "Authorization": assemblyai_key }
        
        async with websockets.connect(url, additional_headers=headers) as aai_ws:
            print("✅ [AssemblyAI] Successfully connected to AssemblyAI Universal Streaming!")
            
            async def forward_audio():
                try:
                    while True:
                        audio_data = await websocket.receive_bytes()
                        await aai_ws.send(audio_data)
                except WebSocketDisconnect:
                    print(f"🔌 Client disconnected from WebSocket (session: {session_id})")
                except Exception as e:
                    print(f"❌ [Audio Forwarder] Error forwarding audio: {e}")

            async def handle_responses():
                try:
                    async for message in aai_ws:
                        data = json.loads(message)
                        msg_type = data.get('type')
                        
                        if msg_type == "Turn" and data.get('turn_is_formatted') is True:
                            transcript = data.get('transcript', '')
                            if transcript:
                                print(f"✅ [AssemblyAI] End of Turn: {transcript}")
                                await websocket.send_text(json.dumps({ "text": transcript, "type": "EndOfTurnTranscript" }))
                                
                                if transcript.strip():
                                    llm_response = await stream_llm_response(transcript, session_id, websocket, gemini_key, tmdb_key)
                                    if llm_response:
                                        await stream_to_murf_websocket(llm_response, session_id, websocket, murf_key)
                                        
                        elif msg_type == "Termination":
                            print(f"🔚 [AssemblyAI] Session Terminated by AssemblyAI.")
                            break
                            
                except Exception as e:
                    print(f"❌ [AssemblyAI] Error handling AssemblyAI responses: {e}")

            await asyncio.gather(
                forward_audio(),
                handle_responses()
            )
            
    except Exception as e:
        print(f"💥 Error in WebSocket handler: {e}")
        if not websocket.client_state == WebSocketDisconnect:
            await websocket.close()
            
    finally:
        if session_id in chat_histories:
            del chat_histories[session_id]
        print(f"🔚 WebSocket session for {session_id} ended.")



# Test endpoint for movie dialogue skill
@app.get("/test/movie/{movie_name}")
async def test_movie_dialogue(movie_name: str):
    """Test endpoint to check movie dialogue functionality"""
    result = await get_movie_dialogue(movie_name, GEMINI_API_KEY, TMDB_API_KEY)
    return result

# Test endpoint for calculation skill
@app.get("/test/calc/{expression}")
async def test_calculation(expression: str):
    """Test endpoint to check calculation functionality"""
    result = perform_calculation(expression)
    return result