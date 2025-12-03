import sys
import os

# Add the current directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    from processing.detectors import ShuttlecockDetector, CourtDetector
    from processing.decision import DecisionEngine
    from processing.engine import ProcessingEngine
    print("Imports successful.")

    print("Loading models (this might take a moment)...")
    # We can try to instantiate the engine to check if models load
    # Note: This requires the model files to exist at the specified paths
    engine = ProcessingEngine()
    print("Models loaded successfully.")
    
    print("System check passed!")

except Exception as e:
    print(f"System check failed: {e}")
    import traceback
    traceback.print_exc()
