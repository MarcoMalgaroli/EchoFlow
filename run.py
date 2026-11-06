import argparse
import uvicorn

parser = argparse.ArgumentParser(
    description="Videolesson transcriber powered by Faster-Whisper"
)

device_group = parser.add_mutually_exclusive_group()

device_group.add_argument(
    "-c", "--cpu",
    dest="device",
    action="store_const",
    const="cpu",
    help="Use the CPU"
)

device_group.add_argument(
    "-g", "--gpu",
    dest="device",
    action="store_const",
    const="cuda",
    help="Use the NVIDIA GPU (default)"
)

parser.set_defaults(device="cuda")
args = parser.parse_args()

import os
os.environ["WHISPER_DEVICE"] = args.device

uvicorn.run(
    "transcriber.backend.app:app",
    host="127.0.0.1",
    port=8000
)