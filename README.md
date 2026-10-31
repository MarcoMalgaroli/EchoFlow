# Videolesson Transcriber

## Run the web application

From the repository root, install the dependencies in the active Python environment:

```powershell
python -m pip install -r requirements.txt
```

Start FastAPI with:

```powershell
python -m uvicorn transcriber.backend.app:app --reload
```

Open <http://127.0.0.1:8000/>. The video tree is read from `input/`; completed
transcriptions are written to the matching folder under `output/`.

The queue processes one video at a time and loads the configured faster-whisper
model lazily when the first queued job starts. `WHISPER_DEVICE` and
`WHISPER_COMPUTE_TYPE` can be used to override the default model settings.
