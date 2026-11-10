# EchoFlow

EchoFlow is a web application that turns video and audio files into text
transcriptions using [faster-whisper](https://github.com/SYSTRAN/faster-whisper/tree/master). It is designed to organize large media
libraries without forcing a particular naming or folder convention: create the
folder structure that best fits your workflow inside `input/`, and EchoFlow
will reproduce that same structure in `output/` with each transcription saved
alongside its corresponding media file.

## Run the web application

From the repository root, install the dependencies in the active Python environment:

Create and activate a virtual environment:

```powershell
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

### Install the dependencies

The default setup runs transcription on an NVIDIA GPU. `requirements.txt`
installs the application dependencies together with the NVIDIA CUDA DLLs
required by faster-whisper.

```powershell
python -m pip install -r requirements.txt
```

<details>
<summary>Run on CPU</summary>
<br>

If you do not have an NVIDIA GPU or prefer to run on the CPU, install the
CPU-only dependencies instead. `CPU_requirements.txt` does not install the
NVIDIA CUDA DLLs:

```powershell
python -m pip install -r CPU_requirements.txt
```
</details>

### Start the application with:

```powershell
python run.py
```

Note: the first time the faster-whisper model will be downloaded and cached, which may take a few minutes.
The application uses the NVIDIA GPU by default. To use the CPU instead, run the application with:

```powershell
python run.py --cpu
```

Open <http://127.0.0.1:8000/>. The Media tree is read from `input/`; completed
transcriptions are written to the matching folder under `output/`.

The queue processes one Media at a time and loads the configured faster-whisper
model lazily when the first queued job starts.