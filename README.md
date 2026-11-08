# Videolesson Transcriber

## Run the web application

From the repository root, install the dependencies in the active Python environment:

```powershell
python -m pip install -r requirements.txt
```

Start the application with:

```powershell
python run.py
```

Note: the first time the faster-whisper model will be downloaded and cached, which may take a few minutes.
The application run by default using the NVIDIA GPU, to use the CPU instead, run the application with:

```powershell
python run.py --cpu
```

Open <http://127.0.0.1:8000/>. The video tree is read from `input/`; completed
transcriptions are written to the matching folder under `output/`.

The queue processes one video at a time and loads the configured faster-whisper
model lazily when the first queued job starts.