from processing.engine import ProcessingEngine
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

def run():
    engine = ProcessingEngine()
    video_path = Path("shuttle.mp4")
    output_path = Path("outputs/test_output.mp4")
    
    if not video_path.exists():
        print(f"Error: {video_path} does not exist.")
        return

    print(f"Processing {video_path}...")
    try:
        engine.process_video(video_path, output_path, mode="doubles", shot_type="rally")
        print("Processing complete.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
