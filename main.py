from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ALiCaS-B Backend",
    description="API for Automated Line Call System for Badminton using YOLOv8",
    version="1.0.0"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global variable to hold the model
model = None

@app.on_event("startup")
async def load_model():
    global model
    try:
        logger.info("Loading YOLOv8 model...")
        # Load the custom trained model
        # Ensure 'best.pt' is in the same directory or provide absolute path
        model = YOLO("best.pt")
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Could not load model: {e}")

@app.get("/")
async def root():
    return {"message": "Welcome to ALiCaS-B API. Use /predict to get inference."}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Upload an image file to get object detection results.
    """
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")

    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    try:
        # Read image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Run inference
        results = model(image)

        # Process results
        detections = []
        for result in results:
            # Iterate through boxes for more control
            for box in result.boxes:
                detection = {
                    "class": int(box.cls[0]),
                    "class_name": model.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bbox": box.xyxy[0].tolist() # [x1, y1, x2, y2]
                }
                detections.append(detection)

        return JSONResponse(content={"detections": detections})

    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
