#!/usr/bin/env python3
# coding: utf-8
"""
FastAPI backend for the Baltika Digit Replacer.

Provides a POST /process endpoint that accepts an uploaded image, replaces
digits using EasyOCR, and returns the processed PNG image.

Secured with an API key passed in the X-API-Key request header.

Run with:
    API_KEY=your-secret-key uvicorn api:app --host 0.0.0.0 --port 8000
"""

import io
import os
import tempfile

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from replace_digits import replace_digits_in_image, PICS_DIR

_API_KEY = os.environ.get("API_KEY", "")

app = FastAPI(title="Baltika Digit Replacer API")


@app.on_event("startup")
def _check_config() -> None:
    """Refuse to start if the API key is not set."""
    if not _API_KEY:
        raise RuntimeError(
            "API_KEY environment variable is not set. "
            "Set it before starting the server: "
            "API_KEY=your-secret-key uvicorn api:app ..."
        )


def _verify_key(x_api_key: str) -> None:
    """Raise HTTP 401 if the provided key does not match the server key."""
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
def health():
    """Simple liveness check."""
    return {"status": "ok"}


@app.post("/process")
async def process_image(
    file: UploadFile = File(...),
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Accept an uploaded image, replace its digits with beer bottle images,
    and return the resulting PNG.
    """
    _verify_key(x_api_key)

    contents = await file.read()
    ext = os.path.splitext(file.filename or "image.png")[1] or ".png"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_in:
        tmp_in.write(contents)
        input_path = tmp_in.name

    output_path = input_path + "_out.png"
    try:
        replace_digits_in_image(input_path, output_path, PICS_DIR)
        with open(output_path, "rb") as f:
            result = f.read()
    finally:
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)

    return StreamingResponse(io.BytesIO(result), media_type="image/png")
