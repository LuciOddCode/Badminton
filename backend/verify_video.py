import cv2
import sys

video_path = r"e:\Badminton\backend\outputs\processed_b38f4854-a3eb-466f-9747-a8717c643403.mp4"

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("ERROR: Could not open video")
    sys.exit(1)

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps if fps > 0 else 0

print(f"✅ Video successfully created!")
print(f"📐 Dimensions: {width}x{height}")
print(f"🎬 FPS: {fps:.2f}")
print(f"⏱️  Total frames: {total_frames}")
print(f"⏰ Duration: {duration:.2f} seconds")

# Check if animation frames are at the end (should be last ~4 seconds)
animation_duration = 4.0
expected_animation_frames = int(fps * animation_duration)
print(f"\n🎨 Expected animation frames: ~{expected_animation_frames} (last {animation_duration}s)")

# Seek to near end to verify animation exists
if total_frames > expected_animation_frames + 10:
    # Go to just before where animation should start
    animation_start_frame = total_frames - expected_animation_frames - 5
    cap.set(cv2.CAP_PROP_POS_FRAMES, animation_start_frame)
    ret, frame = cap.read()
    if ret and frame is not None:
        print(f"✅ Can read frames near animation section (frame {animation_start_frame})")
    else:
        print("⚠️  Could not read frames near animation")

cap.release()
print("\n🎉 Video verification complete!")
