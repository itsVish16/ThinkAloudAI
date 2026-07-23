# AI Interviewer Service

## 📌 Overview
The AI Interviewer handles real-time voice interaction with the user. It streams live audio via WebRTC, orchestrates the LLM thinking process, and synthesizes a human-like voice response.

## ⚙️ How It Works (Excalidraw Diagram Guide)

**Draw these boxes on your whiteboard:**
1. **Frontend / Client (Browser)**: Captures user microphone.
2. **LiveKit Server (WebRTC)**: The real-time media router handling UDP traffic.
3. **AI Worker (Python / LiveKit Agent)**: The "brain" processing the audio stream.
4. **Speechmatics / OpenAI STT API**: Converts Speech to Text.
5. **Fireworks / Groq LLM API**: Generates the interviewer's responses.
6. **Cartesia TTS API**: Converts Text back to Speech.

**Draw the flow (arrows):**
1. **Frontend <-> LiveKit Server**: Streams live audio packets (WebRTC/UDP).
2. **LiveKit Server <-> AI Worker**: Forwards the audio frames to the Python worker.
3. **AI Worker -> STT API**: Sends audio chunks to get a text transcript.
4. **AI Worker -> LLM API**: Feeds the transcript + candidate's live code to the LLM.
5. **LLM API -> AI Worker**: Streams back the text response.
6. **AI Worker -> TTS API**: Sends text response to generate audio.
7. **AI Worker -> LiveKit Server**: Streams the final synthesized audio back to the user.

## 🛠️ Key Details
- **Why WebRTC (LiveKit)?** Standard HTTP REST APIs are too slow for real-time voice conversations. WebRTC operates over UDP, offering <500ms latency to prevent awkward conversational pauses.
- **State Management**: The worker maintains conversational state in memory (the chat history) during the call and periodically flushes it to PostgreSQL so progress isn't lost if the call drops.
