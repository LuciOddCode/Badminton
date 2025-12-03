import requests
from PIL import Image
import io

# Create a dummy image (100x100 black image)
image = Image.new('RGB', (100, 100), color = 'black')
img_byte_arr = io.BytesIO()
image.save(img_byte_arr, format='JPEG')
img_byte_arr = img_byte_arr.getvalue()

url = 'http://127.0.0.1:8000/predict'
files = {'file': ('test.jpg', img_byte_arr, 'image/jpeg')}

try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
