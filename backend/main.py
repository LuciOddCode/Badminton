from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from pathlib import Path


from processing.engine import ProcessingEngine

from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager

engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    # Initialize Engine here to avoid loading it in the parent process during reload
    engine = ProcessingEngine()
    yield
    engine = None

app = FastAPI(title="ALiCaS-B Backend", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

@app.get("/")
async def root():
    return {"message": "ALiCaS-B Backend is running"}

import uuid

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    try:
        # Generate a safe filename using UUID
        file_extension = Path(file.filename).suffix
        safe_filename = f"{uuid.uuid4()}{file_extension}"
        file_location = UPLOAD_DIR / safe_filename
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "filename": safe_filename, 
            "original_filename": file.filename,
            "location": str(file_location), 
            "message": "Video uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/{filename}")
async def process_video(filename: str):
    video_path = UPLOAD_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    output_filename = f"processed_{filename}"
    output_path = OUTPUT_DIR / output_filename
    
    try:
        results = engine.process_video(video_path, output_path)
        return {
            "message": "Processing complete",
            "output_video": str(output_path),
            "results_summary": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
