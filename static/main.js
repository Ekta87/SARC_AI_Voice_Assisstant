document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const recordBtn = document.getElementById("recordBtn");
    const btnIcon = document.getElementById("btnIcon");
    const audioPlayer = document.getElementById("llmBotAudio");
    const statusDisplay = document.getElementById("llmBotStatus");
    const transcriptionDisplay = document.getElementById("streamTranscription");
    const wordsCountEl = document.getElementById("wordsCount");
    const charactersCountEl = document.getElementById("charactersCount");
    const messagesCountEl = document.getElementById("messagesCount");
    const settingsBtn = document.getElementById("settingsBtn");
    const settingsModal = document.getElementById("settingsModal");
    const closeModal = document.querySelector(".close");
    const apiKeyForm = document.getElementById("apiKeyForm");
    const clearKeysBtn = document.getElementById("clearKeys");

    // Stats
    let wordsCount = 0;
    let charactersCount = 0;
    let messagesCount = 0;

    // Session and state management
    let socket;
    let stream;
    let audioContext;
    let scriptProcessor;
    let mediaStreamSource;

    let userTranscript = "";
    let llmResponse = "";
    let audioPlaying = false;
    let receivedAudioChunks = [];
    let combinedAudioBlob = null;
    let chatHistory = [];
    let isRecording = false;

    // API Keys
    let apiKeys = {
        assemblyai: null,
        murf: null,
        gemini: null,
        tmdb: null
    };

    // Load API keys from localStorage
    const loadApiKeys = () => {
        const savedKeys = localStorage.getItem('voiceai_api_keys');
        if (savedKeys) {
            apiKeys = JSON.parse(savedKeys);
            document.getElementById("assemblyaiKey").value = apiKeys.assemblyai || '';
            document.getElementById("murfKey").value = apiKeys.murf || '';
            document.getElementById("geminiKey").value = apiKeys.gemini || '';
            document.getElementById("tmdbKey").value = apiKeys.tmdb || '';
            
            // Enable record button if we have the required keys
            if (apiKeys.assemblyai && apiKeys.murf && apiKeys.gemini) {
                recordBtn.disabled = false;
                statusDisplay.innerHTML = `<i class="fas fa-check-circle"></i> Ready to listen! Click the orb to begin.`;
                statusDisplay.className = "status-success";
                
                // Update welcome message
                if (chatHistory.length === 0) {
                    transcriptionDisplay.innerHTML = `
                        <div style="text-align: center; color: var(--text-muted); font-style: italic; padding: 2rem;">
                            <p>Your conversation will appear here</p>
                            <small>Start speaking to begin...</small>
                        </div>
                    `;
                }
            }
        }
    };

    // Save API keys to localStorage
    const saveApiKeys = () => {
        apiKeys.assemblyai = document.getElementById("assemblyaiKey").value.trim() || null;
        apiKeys.murf = document.getElementById("murfKey").value.trim() || null;
        apiKeys.gemini = document.getElementById("geminiKey").value.trim() || null;
        apiKeys.tmdb = document.getElementById("tmdbKey").value.trim() || null;
        
        localStorage.setItem('voiceai_api_keys', JSON.stringify(apiKeys));
        
        // Show success message
        showNotification('API keys saved successfully!', 'success');
        
        // Enable record button if we have the required keys
        if (apiKeys.assemblyai && apiKeys.murf && apiKeys.gemini) {
            recordBtn.disabled = false;
            statusDisplay.innerHTML = `<i class="fas fa-check-circle"></i> Ready to listen! Click the orb to begin.`;
            statusDisplay.className = "status-success";
            
            // Update welcome message
            if (chatHistory.length === 0) {
                transcriptionDisplay.innerHTML = `
                    <div style="text-align: center; color: var(--text-muted); font-style: italic; padding: 2rem;">
                        <p>Your conversation will appear here</p>
                        <small>Start speaking to begin...</small>
                    </div>
                `;
            }
        }
        
        // Close modal
        settingsModal.style.display = "none";
    };

    // Clear all API keys
    const clearApiKeys = () => {
        document.getElementById("assemblyaiKey").value = '';
        document.getElementById("murfKey").value = '';
        document.getElementById("geminiKey").value = '';
        document.getElementById("tmdbKey").value = '';
        
        apiKeys = {
            assemblyai: null,
            murf: null,
            gemini: null,
            tmdb: null
        };
        
        localStorage.removeItem('voiceai_api_keys');
        
        // Disable record button
        recordBtn.disabled = true;
        statusDisplay.innerHTML = `Configure API keys to begin`;
        statusDisplay.className = "";
        
        // Show notification
        showNotification('API keys cleared', 'info');
        
        // Reset welcome message
        if (chatHistory.length === 0) {
            transcriptionDisplay.innerHTML = `
                <div class="welcome-message">
                    <h3>Welcome to VoiceAI Pro!</h3>
                    <p>Please configure your API keys using the settings button to start the conversation.</p>
                    <div class="feature-list">
                        <div class="feature-item">
                            <i class="fas fa-microphone"></i>
                            <span>Voice conversations</span>
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-film"></i>
                            <span>Movie dialogues</span>
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-calculator"></i>
                            <span>Calculations</span>
                        </div>
                    </div>
                </div>
            `;
        }
    };

    // Show notification
    const showNotification = (message, type = 'info') => {
        // Remove any existing notification
        const existingNotification = document.getElementById('apiNotification');
        if (existingNotification) {
            existingNotification.remove();
        }
        
        // Create notification element
        const notification = document.createElement('div');
        notification.id = 'apiNotification';
        notification.textContent = message;
        
        // Set style based on type
        if (type === 'success') {
            notification.style.background = 'var(--success-color)';
            notification.style.color = 'white';
        } else if (type === 'error') {
            notification.style.background = 'var(--error-color)';
            notification.style.color = 'white';
        } else {
            notification.style.background = 'var(--glass-bg)';
            notification.style.color = 'var(--text-primary)';
            notification.style.border = '1px solid var(--border-color)';
        }
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 3000);
    };

    // Update statistics
    const updateStats = () => {
        wordsCountEl.textContent = wordsCount;
        charactersCountEl.textContent = charactersCount;
        messagesCountEl.textContent = messagesCount;
    };

    // Get current timestamp
    const getCurrentTimestamp = () => {
        return new Date().toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Update chat display with history
    const updateChatDisplay = () => {
        if (chatHistory.length === 0) {
            if (apiKeys.assemblyai && apiKeys.murf && apiKeys.gemini) {
                transcriptionDisplay.innerHTML = `
                    <div style="text-align: center; color: var(--text-muted); font-style: italic; padding: 2rem;">
                        <p>Your conversation will appear here</p>
                        <small>Start speaking to begin...</small>
                    </div>
                `;
            } else {
                transcriptionDisplay.innerHTML = `
                    <div class="welcome-message">
                        <h3>Welcome to VoiceAI Pro!</h3>
                        <p>Please configure your API keys using the settings button to start the conversation.</p>
                        <div class="feature-list">
                            <div class="feature-item">
                                <i class="fas fa-microphone"></i>
                                <span>Voice conversations</span>
                            </div>
                            <div class="feature-item">
                                <i class="fas fa-film"></i>
                                <span>Movie dialogues</span>
                            </div>
                            <div class="feature-item">
                                <i class="fas fa-calculator"></i>
                                <span>Calculations</span>
                            </div>
                        </div>
                    </div>
                `;
            }
            return;
        }

        let chatHTML = '';
        // Reset and recalculate stats
        wordsCount = 0;
        charactersCount = 0;
        messagesCount = 0;
        
        chatHistory.forEach((message) => {
            if (message.type === 'user') {
                chatHTML += `
                    <div class="chat-message user-message">
                        <div class="message-header">
                            <span>You</span>
                            <span class="message-time">${message.timestamp}</span>
                        </div>
                        <div>${message.text}</div>
                    </div>
                `;
                wordsCount += message.text.split(/\s+/).filter(Boolean).length;
                charactersCount += message.text.length;
                messagesCount++;
            } else if (message.type === 'bot') {
                chatHTML += `
                    <div class="chat-message bot-message">
                        <div class="message-header">
                            <span><i class="fas fa-robot" style="margin-right: 5px;"></i> AI Assistant</span>
                            <span class="message-time">${message.timestamp}</span>
                        </div>
                        <div>${message.text}</div>
                    </div>
                `;
                wordsCount += message.text.split(/\s+/).filter(Boolean).length;
                charactersCount += message.text.length;
                messagesCount++;
            }
        });

        transcriptionDisplay.innerHTML = chatHTML;
        updateStats();

        setTimeout(() => {
            transcriptionDisplay.scrollTop = transcriptionDisplay.scrollHeight;
        }, 100);
    };

    // Play final audio
    const playFinalAudio = () => {
        if (receivedAudioChunks.length > 0 && !audioPlaying) {
            audioPlaying = true;
            combinedAudioBlob = new Blob(receivedAudioChunks, { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(combinedAudioBlob);
            
            audioPlayer.src = audioUrl;
            const playPromise = audioPlayer.play();

            if (playPromise !== undefined) {
                playPromise.catch(error => {
                    console.error("Audio playback was prevented:", error);
                    statusDisplay.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Audio blocked. Click page to play.`;
                    statusDisplay.className = "status-error";
                    // Fallback to allow user to play with a single click anywhere on the page
                    document.body.addEventListener('click', () => audioPlayer.play(), { once: true });
                });
            }
        } else {
             // If there's no audio, just reset the UI.
            recordBtn.disabled = false;
            recordBtn.classList.remove('processing');
            btnIcon.innerHTML = '<i class="fas fa-microphone"></i>';
            statusDisplay.innerHTML = `<i class="fas fa-check-circle"></i> Ready for next input.`;
            statusDisplay.className = "status-success";
        }
    };

    // Audio player event listener
    audioPlayer.onended = () => {
        audioPlaying = false;
        if (audioPlayer.src.startsWith('blob:')) {
            URL.revokeObjectURL(audioPlayer.src);
        }
        combinedAudioBlob = null;
        receivedAudioChunks = [];
        console.log("✅ Final audio playback complete!");
        statusDisplay.innerHTML = `<i class="fas fa-check-circle"></i> Audio response complete. Ready for next question.`;
        statusDisplay.className = "status-success";

        recordBtn.disabled = false;
        recordBtn.classList.remove('processing');
        btnIcon.innerHTML = '<i class="fas fa-microphone"></i>';
    };

    // Start streaming
    const startStreaming = async () => {
        // Check if we have the required API keys
        if (!apiKeys.assemblyai || !apiKeys.murf || !apiKeys.gemini) {
            statusDisplay.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Missing API keys. Please configure in settings.`;
            statusDisplay.className = "status-error";
            isRecording = false;
            return;
        }

        try {
            userTranscript = "";
            llmResponse = "";
            if (chatHistory.length === 0) {
                updateChatDisplay();
            }
            receivedAudioChunks = [];
            combinedAudioBlob = null;
            audioPlaying = false;

            // Send API keys as query parameters
            const wsUrl = `ws://${window.location.host}/ws?assemblyai_key=${encodeURIComponent(apiKeys.assemblyai)}&murf_key=${encodeURIComponent(apiKeys.murf)}&gemini_key=${encodeURIComponent(apiKeys.gemini)}&tmdb_key=${encodeURIComponent(apiKeys.tmdb || '')}`;
            socket = new WebSocket(wsUrl);

            socket.onopen = async () => {
                console.log("WebSocket connection established for streaming.");
                statusDisplay.innerHTML = `<i class="fas fa-plug"></i> Connected! Listening...`;
                statusDisplay.className = "status-success";

                try {
                    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    if (audioContext.state === 'suspended') {
                        await audioContext.resume();
                    }

                    const inputSampleRate = audioContext.sampleRate;
                    const outputSampleRate = 16000;
                    mediaStreamSource = audioContext.createMediaStreamSource(stream);
                    const bufferSize = 4096;
                    scriptProcessor = audioContext.createScriptProcessor(bufferSize, 1, 1);

                    scriptProcessor.onaudioprocess = (e) => {
                        const inputData = e.inputBuffer.getChannelData(0);
                        const downsampledData = downsampleBuffer(inputData, inputSampleRate, outputSampleRate);
                        const pcmData = to16BitPCM(downsampledData);
                        if (socket.readyState === WebSocket.OPEN) {
                            socket.send(pcmData.buffer);
                        }
                    };
                    mediaStreamSource.connect(scriptProcessor);
                    scriptProcessor.connect(audioContext.destination);

                    recordBtn.disabled = true; // Button is disabled while setting up
                    recordBtn.classList.add('recording');
                    btnIcon.innerHTML = '<i class="fas fa-stop"></i>';
                    statusDisplay.innerHTML = `<i class="fas fa-microphone"></i> Streaming audio... Speak now!`;
                    statusDisplay.className = "status-success";
                    transcriptionDisplay.classList.add('active');
                } catch (micError) {
                    console.error("Microphone access error:", micError);
                    statusDisplay.innerHTML = `<i class="fas fa-exclamation-circle"></i> Microphone error: ${micError.message}`;
                    statusDisplay.className = "status-error";
                    if (socket.readyState === WebSocket.OPEN) socket.close();
                }
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                switch (data.type) {
                    case "EndOfTurnTranscript":
                        userTranscript = data.text;
                        if (userTranscript.trim()) {
                            chatHistory.push({
                                type: 'user',
                                text: userTranscript,
                                timestamp: getCurrentTimestamp()
                            });
                            updateChatDisplay();
                            console.log("👤 User said:", userTranscript);
                        }
                        llmResponse = "";
                        receivedAudioChunks = [];
                        combinedAudioBlob = null;
                        recordBtn.classList.remove('recording');
                        recordBtn.classList.add('processing');
                        btnIcon.innerHTML = '<i class="fas fa-sync-alt"></i>';
                        statusDisplay.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Processing request...`;
                        statusDisplay.className = "";
                        break;
                    
                    case "LLMStreamChunk":
                        let lastMessage = chatHistory[chatHistory.length - 1];
                        if (chatHistory.length > 0 && lastMessage.type === 'bot') {
                            lastMessage.text += data.text;
                        } else {
                            chatHistory.push({
                                type: 'bot',
                                text: data.text,
                                timestamp: getCurrentTimestamp()
                            });
                        }
                        updateChatDisplay();
                        break;

                    case "LLMStreamComplete":
                        console.log(`✅ LLM streaming complete!`);
                        if (chatHistory.length > 0 && chatHistory[chatHistory.length - 1].type === 'bot') {
                            chatHistory[chatHistory.length - 1].text = data.complete_response;
                            updateChatDisplay();
                        }
                        break;

                    case "MurfAudioChunk":
                        if (data.audio) {
                            const audioData = atob(data.audio);
                            const audioBytes = new Uint8Array(audioData.length);
                            for (let i = 0; i < audioData.length; i++) {
                                audioBytes[i] = audioData.charCodeAt(i);
                            }
                            receivedAudioChunks.push(audioBytes.buffer);
                        }
                        break;
                    
                    case "MurfStreamComplete":
                        console.log(`🎉 Murf audio streaming complete!`);
                        playFinalAudio();
                        break;

                    case "APIKeyError":
                        console.error("API Key Error:", data.error);
                        statusDisplay.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${data.error}`;
                        statusDisplay.className = "status-error";
                        cleanUp();
                        break;

                    default:
                        console.log("🔍 Unhandled message type:", data.type, data);
                        break;
                }
            };

            socket.onclose = () => {
                console.log("🔌 WebSocket connection closed.");
                statusDisplay.innerHTML = `<i class="fas fa-pause-circle"></i> Streaming stopped.`;
                statusDisplay.className = "";
                transcriptionDisplay.classList.remove('active');
                cleanUp();
            };

            socket.onerror = (error) => {
                console.error("❌ WebSocket Error:", error);
                statusDisplay.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Connection error.`;
                statusDisplay.className = "status-error";
                cleanUp();
            };
        } catch (err) {
            console.error("💥 Error starting stream:", err);
            statusDisplay.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Error: ${err.message}`;
            statusDisplay.className = "status-error";
        }
    };

    // Stop streaming
    const stopStreaming = () => {
        console.log("⏹️ Stopping audio stream from microphone.");
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
        cleanUp();
    };
    
    // Clean up resources
    const cleanUp = () => {
        if (scriptProcessor) scriptProcessor.disconnect();
        if (mediaStreamSource) mediaStreamSource.disconnect();
        if (audioContext) audioContext.close();
        if (stream) stream.getTracks().forEach(track => track.stop());
        scriptProcessor = mediaStreamSource = audioContext = stream = null;
        recordBtn.disabled = false;
        recordBtn.classList.remove('recording', 'processing');
        btnIcon.innerHTML = '<i class="fas fa-microphone"></i>';
        transcriptionDisplay.classList.remove('active');
    };

    // Audio processing functions
    const downsampleBuffer = (buffer, inputRate, outputRate) => {
        if (inputRate === outputRate) return buffer;
        const rate = inputRate / outputRate;
        const newLength = Math.round(buffer.length / rate);
        const result = new Float32Array(newLength);
        let offsetResult = 0, offsetBuffer = 0;
        while (offsetResult < result.length) {
            const nextOffset = Math.round((offsetResult + 1) * rate);
            let accum = 0, count = 0;
            for (let i = offsetBuffer; i < nextOffset && i < buffer.length; i++) {
                accum += buffer[i];
                count++;
            }
            result[offsetResult] = accum / count;
            offsetResult++;
            offsetBuffer = nextOffset;
        }
        return result;
    };

    const to16BitPCM = (input) => {
        const pcm = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            let s = Math.max(-1, Math.min(1, input[i]));
            pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return pcm;
    };

    // Toggle recording
    const toggleRecording = () => {
        if (isRecording) {
            stopStreaming();
        } else {
            startStreaming();
        }
        isRecording = !isRecording;
    };

    // Initialize
    const init = async () => {
        // Load API keys from localStorage
        loadApiKeys();
        
        // Modal event listeners
        settingsBtn.addEventListener('click', () => {
            settingsModal.style.display = "block";
        });

        closeModal.addEventListener('click', () => {
            settingsModal.style.display = "none";
        });

        window.addEventListener('click', (event) => {
            if (event.target === settingsModal) {
                settingsModal.style.display = "none";
            }
        });

        apiKeyForm.addEventListener('submit', (e) => {
            e.preventDefault();
            saveApiKeys();
        });

        clearKeysBtn.addEventListener('click', clearApiKeys);

        // Check microphone access
        try {
            await navigator.mediaDevices.getUserMedia({ audio: true });
            if (apiKeys.assemblyai && apiKeys.murf && apiKeys.gemini) {
                recordBtn.disabled = false;
                statusDisplay.innerHTML = `<i class="fas fa-check-circle"></i> Ready to listen! Click the orb to begin.`;
                statusDisplay.className = "status-success";
            }
        } catch (err) {
            console.error("Microphone access denied:", err);
            statusDisplay.innerHTML = `<i class="fas fa-microphone-slash"></i> Microphone access is required.`;
            statusDisplay.className = "status-error";
            recordBtn.disabled = true;
        }
        
        recordBtn.onclick = toggleRecording;
    };

    // Add double-click to clear chat
    transcriptionDisplay.addEventListener('dblclick', () => {
        if (confirm('Clear chat history?')) {
            chatHistory = [];
            wordsCount = 0;
            charactersCount = 0;
            messagesCount = 0;
            updateStats();
            updateChatDisplay();
            console.log("🧹 Chat history cleared!");
        }
    });

    // Initialize the app
    init();
});