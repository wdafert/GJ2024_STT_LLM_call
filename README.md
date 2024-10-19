# Audio Recorder and Transcriber

This application allows you to record audio from your microphone and transcribe it using the Groq API.

## Installation

1. Clone this repository:   ```
   git clone https://github.com/wdafert/GJ2024_STT_LLM_call.git
   cd GJ2024_STT_LLM_call   ```

2. Create a virtual environment (optional but recommended):   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`   ```

3. Install the required packages:   ```
   pip install groq python-dotenv pyaudio   ```

4. Create a `.env` file in the project root and add your Groq API key:   ```
   GROQ_API_KEY=your_api_key_here   ```

## Usage

1. Run the application:   ```
   python main.py   ```

2. Click the "Start" button to begin recording audio.
3. Click the "Stop" button to stop recording and start transcription.
4. The transcribed text and latency will be displayed in the application window.

## Note

Make sure your microphone is properly connected and configured before running the application.
