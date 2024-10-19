import os
import time
import json
import pyaudio
import wave
import tkinter as tk
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, parse_raw_as
import xml.etree.ElementTree as ET
import re  # Add this import at the top of the file

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

# Prompt parts
PREPROMPT = "Generate SVG code for a "
# POSTPROMPT = ". Expected JSON Output: { \"type\": \"svg\", \"width\": \"200\", \"height\": \"300\", \"raw_svg\": \"<svg width='200' height='300'><polygon points='100,10 40,180 160,180' fill='green'/><rect x='90' y='180' width='20' height='50' fill='brown'/><polygon points='100,30 120,80 80,80' fill='yellow'/></svg>\" }"
POSTPROMPT = "Only output the SVG, nothing else. 300x300"

class SVGResponse(BaseModel):
    type: str
    width: str
    height: str
    raw_svg: str

class AudioRecorderApp:
    def __init__(self, master):
        self.master = master
        master.title("Audio Recorder, Transcriber, and SVG Generator")

        self.is_recording = False
        self.frames = []

        self.start_button = tk.Button(master, text="Start", command=self.start_recording)
        self.start_button.pack()

        self.stop_button = tk.Button(master, text="Stop", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack()

        self.text_display = tk.Text(master, height=20, width=80)
        self.text_display.pack()

        self.canvas = tk.Canvas(master, width=200, height=300)
        self.canvas.pack()

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
        stt_latency = end_time - start_time

        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, f"Transcription:\n{transcription.text}\n\n")
        self.text_display.insert(tk.END, f"STT Latency: {stt_latency:.2f} seconds\n\n")

        self.generate_svg(transcription.text)

    def generate_svg(self, transcription):
        full_prompt = f"{PREPROMPT} {transcription}. {POSTPROMPT}"
        
        system_prompt = "You are a designer that creates SVGs for game assets for retro games."
        
        # Print the system prompt
        print("System Prompt:")
        print(system_prompt)
        print("-" * 50)  # Separator for clarity
        
        # Print the complete prompt for debugging
        print("Complete Prompt:")
        print(full_prompt)
        print("-" * 50)  # Separator for clarity
        
        start_time = time.time()
        
        chat_completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": full_prompt,
                },
            ],
            temperature=0.33,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        end_time = time.time()
        llm_latency = end_time - start_time
        
        response_content = chat_completion.choices[0].message.content
        
        # Use regex to extract SVG content
        svg_match = re.search(r'<svg.*?</svg>', response_content, re.DOTALL)
        if svg_match:
            raw_svg = svg_match.group(0)
        else:
            print("No SVG content found in the response")
            self.text_display.insert(tk.END, "Error: No SVG content found in the response\n\n")
            self.text_display.insert(tk.END, f"Raw response:\n{response_content}\n\n")
            return
        
        self.text_display.insert(tk.END, "LLM Response:\n")
        self.text_display.insert(tk.END, raw_svg)
        self.text_display.insert(tk.END, f"\n\nLLM Latency: {llm_latency:.2f} seconds\n\n")

        # Display the SVG
        self.display_svg(raw_svg)

    def display_svg(self, svg_string):
        # Clear previous content
        self.canvas.delete("all")

        # Parse the SVG string
        root = ET.fromstring(svg_string)

        # Extract width and height
        width = int(root.get('width', '200'))
        height = int(root.get('height', '300'))

        # Update canvas size
        self.canvas.config(width=width, height=height)

        # Iterate through SVG elements and draw them on the canvas
        for element in root:
            if element.tag.split('}')[-1] == 'polygon':
                points = element.get('points').split()
                fill = element.get('fill', 'black')
                coords = [float(coord) for point in points for coord in point.split(',')]
                self.canvas.create_polygon(coords, fill=fill, outline='')
            elif element.tag.split('}')[-1] == 'rect':
                x = float(element.get('x', 0))
                y = float(element.get('y', 0))
                w = float(element.get('width', 0))
                h = float(element.get('height', 0))
                fill = element.get('fill', 'black')
                self.canvas.create_rectangle(x, y, x+w, y+h, fill=fill, outline='')

        self.text_display.insert(tk.END, "SVG displayed below.\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorderApp(root)
    root.mainloop()
