import requests
import base64
import io
from typing import List, Dict
from celery import shared_task
from app.core.config import settings
from PIL import Image
import cloudinary
import cloudinary.uploader
import json 

cloudinary.config( 
    cloud_name = "dgrckzaxa", 
    api_key = "596468498745612", 
    api_secret = "Rc4MD6MMwUFPQws4tZQranfleik",
    secure=True
)

@shared_task
def generate_images(prompt: str, num_images: int = 3, user_id: int = None) -> List[Dict[str, str]]:
    url = f"{settings.STABILITY_API_HOST}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.STABILITY_API_KEY}"
    }
    
    payload = {
        "text_prompts": [{"text": prompt}],
        "cfg_scale": 7,
        "height": 1024,
        "width": 1024,
        "samples": num_images,
        "steps": 30,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        # with open('/home/yash/Desktop/personal_projects/chaotix/StabilityImageGenerator/response.json') as f:
        #     data = json.load(f)
        res = []
        
        for idx, artifact in enumerate(data['artifacts']):
            image_data = base64.b64decode(artifact['base64'])
            image = Image.open(io.BytesIO(image_data))
            
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            upload_result = cloudinary.uploader.upload(img_byte_arr)
            cloudinary_url = upload_result['secure_url']
            
            res.append({
                "id":f"{generate_images.request.id}",
                "prompt": prompt,
                "image_url": cloudinary_url,
                "user_id": user_id
            })
        
        webhook_url = f"{settings.FASTAPI_BASE_URL}/image-gen/api/1/webhook/task-complete"
        requests.post(webhook_url, json={"task_id": generate_images.request.id, "result": res})
        
        return res
    except Exception as e:
        webhook_url = f"{settings.FASTAPI_BASE_URL}/image-gen/api/1/webhook/task-failed"
        requests.post(webhook_url, json={"task_id": generate_images.request.id, "error": str(e)})
        raise Exception(f"Image generation or upload failed: {str(e)}")