from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock, Thread
from typing import Literal
import sys

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transcribe import (  # noqa: E402
    INPUT_DIR,
    OUTPUT_DIR,
    VIDEO_EXTENSION,
    load_model,
    output_path_for,
    transcribe_and_save,
)

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


class QueueRequest(BaseModel):
    paths: list[str] = Field(min_length=1)


@dataclass
class Job:
    path: str
    status: Literal["queued", "processing", "completed", "failed"]
    error: str | None = None


@dataclass
class QueueManager:
    jobs: dict[str, Job] = field(default_factory=dict)
    pending: list[str] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)
    worker_started: bool = False

    def enqueue(self, paths: list[str]) -> list[Job]:
        added: list[Job] = []
        with self.lock:
            for path in paths:
                existing = self.jobs.get(path)
                if existing and existing.status in {"queued", "processing"}:
                    continue
                job = Job(path=path, status="queued")
                self.jobs[path] = job
                self.pending.append(path)
                added.append(job)
            if added and not self.worker_started:
                self.worker_started = True
                Thread(target=self._run, daemon=True).start()
        return added

    def _run(self) -> None:
        model = None
        try:
            while True:
                with self.lock:
                    if not self.pending:
                        self.worker_started = False
                        return
                    relative_path = self.pending.pop(0)
                    job = self.jobs[relative_path]
                    job.status = "processing"
                try:
                    video_path = safe_input_path(relative_path)
                    if model is None:
                        model = load_model()
                    transcribe_and_save(model, video_path)
                    with self.lock:
                        job.status = "completed"
                except Exception as error:
                    with self.lock:
                        job.status = "failed"
                        job.error = str(error)
        except Exception:
            with self.lock:
                self.worker_started = False
            raise

    def snapshot(self) -> list[dict]:
        with self.lock:
            return [job.__dict__.copy() for job in self.jobs.values()]


queue_manager = QueueManager()
app = FastAPI(title="Videolesson Transcriber")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "public"), name="static")


def safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise HTTPException(status_code=400, detail="Invalid media path")
    return path


def safe_input_path(value: str) -> Path:
    relative_path = safe_relative_path(value)
    candidate = (INPUT_DIR / relative_path).resolve()
    try:
        candidate.relative_to(INPUT_DIR.resolve())
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid media path") from error
    if not candidate.is_file() or candidate.suffix.lower() != VIDEO_EXTENSION:
        raise HTTPException(status_code=404, detail="Video not found")
    return candidate


def tree_for(root: Path, extension: str | None = None, base_root: Path | None = None) -> list[dict]:
    if not root.exists():
        return []
    base_root = base_root or root
    result = []
    for path in sorted(root.iterdir(), key=lambda item: (item.is_file(), item.name.lower())):
        if path.is_dir():
            result.append(
                {
                    "name": path.name,
                    "type": "folder",
                    "children": tree_for(path, extension, base_root),
                }
            )
        elif extension is None or path.suffix.lower() == extension:
            relative = path.relative_to(base_root).as_posix()
            result.append({"name": path.name, "type": "file", "path": relative})
    return result


def input_tree() -> list[dict]:
    tree = tree_for(INPUT_DIR, VIDEO_EXTENSION, INPUT_DIR)
    jobs = {job["path"]: job for job in queue_manager.snapshot()}

    def annotate(nodes: list[dict]) -> None:
        for node in nodes:
            if node["type"] == "folder":
                annotate(node["children"])
            else:
                output_exists = output_path_for(INPUT_DIR / node["path"]).exists()
                node["status"] = jobs.get(node["path"], {}).get(
                    "status", "completed" if output_exists else "pending"
                )
    annotate(tree)
    return tree


@app.get("/", response_class=HTMLResponse)
def home() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "views" / "index.html")


@app.get("/transcriptions", response_class=HTMLResponse)
def transcriptions_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "views" / "transcriptions.html")


@app.get("/api/tree")
def get_tree() -> list[dict]:
    return input_tree()


@app.post("/api/queue")
def queue_videos(request: QueueRequest) -> dict:
    for path in request.paths:
        safe_input_path(path)
    return {"jobs": queue_manager.enqueue(request.paths)}


@app.get("/api/jobs")
def get_jobs() -> list[dict]:
    return queue_manager.snapshot()


@app.get("/api/transcriptions")
def get_transcriptions() -> list[dict]:
    return tree_for(OUTPUT_DIR, ".txt")


@app.get("/api/transcriptions/{path:path}", response_class=PlainTextResponse)
def get_transcription(path: str) -> PlainTextResponse:
    relative_path = safe_relative_path(path)
    candidate = (OUTPUT_DIR / relative_path).resolve()
    try:
        candidate.relative_to(OUTPUT_DIR.resolve())
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid transcription path") from error
    if not candidate.is_file() or candidate.suffix.lower() != ".txt":
        raise HTTPException(status_code=404, detail="Transcription not found")
    return PlainTextResponse(candidate.read_text(encoding="utf-8"))
