# MeetMind — AI Meeting Summarizer

MeetMind is a Python-based meeting summarizer that accepts either pasted meeting text or uploaded audio/video recordings, transcribes the audio into text, and then runs the existing summarization pipeline on the resulting transcript.

## Features

- Text-based meeting transcript analysis
- Audio and video upload with transcription
- Local Whisper fallback for offline transcription
- OpenAI speech-to-text support when configured
- Meeting summary, decisions, action items, risks, and participant analysis
- Knowledge-base storage and reporting
- Calendar export of action items as iCalendar (.ics) events
- Meeting Memory Assistant for cross-meeting questions with cited sources
- Accountability Center with persistent task status and overdue-risk tracking
- Meeting Quality Coach with explainable improvement recommendations

## Requirements

- Python 3.10+
- Streamlit
- spaCy, NLTK, scikit-learn, moviepy, soundfile
- Optional: Ollama for AI-enhanced summaries
- Optional: OpenAI API key for enhanced speech-to-text

## Environment variables

Create a `.env` file in the project root with values like:

```bash
SPEECH_TO_TEXT_API_KEY=your_key_here
LLM_API_KEY=your_key_here
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
WHISPER_MODEL=openai/whisper-tiny.en
MAX_AUDIO_FILE_SIZE_MB=25
AUDIO_CHUNK_SECONDS=600
```

A template is provided in `.env.example`.

## Run the project

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown by Streamlit in your browser.

## Using text input

1. Open the app.
2. Select the text input area.
3. Paste a meeting transcript.
4. Click Analyze Meeting.
5. The existing summarization pipeline generates a summary, decisions, action items, and other insights.

## Uploading audio

1. Select the Audio input tab.
2. Upload a file in one of the supported formats.
3. The project validates the file type and size.
4. It transcribes the audio to text.
5. The generated transcript is shown and then fed into the same summary pipeline used for normal text input.

## Supported audio formats

- MP3
- WAV
- M4A
- MP4
- WEBM
- OGG
- FLAC
- MOV
- MKV
- AVI

## How speech-to-text works

The app first validates the uploaded audio file. If an OpenAI API key is configured, the app prefers the current OpenAI audio transcription API. For long recordings, the file is segmented into safe chunks, transcribed in order, and recombined before passing the transcript to the summarizer.

If OpenAI is unavailable or the key is missing, the app falls back to the local Whisper model already used by the project.

## How summarization works

The transcript is passed into the existing meeting analysis pipeline, which uses the same NLP logic already used for text input to generate:

- Meeting overview
- Key discussion points
- Decisions made
- Action items
- Risks and questions
- Next steps

## File-size and duration limits

- Maximum upload size is 25 MB by default.
- Audio longer than 10 minutes is segmented automatically for safe transcription.
- The final transcript is not silently truncated; it is processed in order and summarized as one combined document.

## Troubleshooting

- Unsupported format: choose a supported file type.
- Empty/corrupted audio: verify the file is valid and audible.
- API failure: confirm the environment variable is set and valid.
- Long session: allow chunking and reassembly to finish before summarizing.
