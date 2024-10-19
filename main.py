import os
import time
import pyaudio
import wave
import tkinter as tk
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize the Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
WAVE_OUTPUT_FILENAME = "output.wav"

class AudioRecorderApp:
    def __init__(self, master):
        self.master = master
        master.title("Audio Recorder and Transcriber")

        self.is_recording = False
        self.frames = []

        self.start_button = tk.Button(master, text="Start", command=self.start_recording)
        self.start_button.pack()

        self.stop_button = tk.Button(master, text="Stop", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack()

        self.text_display = tk.Text(master, height=10, width=50)
        self.text_display.pack()

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, "Recording...\n")
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)

        print("* Recording audio...")
        self.master.after(100, self.record_audio)

    def record_audio(self):
        if self.is_recording:
            data = self.stream.read(CHUNK)
            self.frames.append(data)
            self.master.after(10, self.record_audio)

    def stop_recording(self):
        self.is_recording = False
        print("* Finished recording")

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        self.save_audio()
        self.transcribe_audio()

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def save_audio(self):
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()

    def transcribe_audio(self):
        start_time = time.time()

        with open(WAVE_OUTPUT_FILENAME, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(WAVE_OUTPUT_FILENAME, file.read()),
                model="whisper-large-v3-turbo",
                response_format="json",
                language="en",
                temperature=0.0
            )

        end_time = time.time()
        latency = end_time - start_time

        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, f"Transcription:\n{transcription.text}\n\n")
        self.text_display.insert(tk.END, f"Latency: {latency:.2f} seconds")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorderApp(root)
    root.mainloop()
