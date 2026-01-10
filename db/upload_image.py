"""
Upload image to Supabase storage and get public URL
"""
import os
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime

load_dotenv()

def upload_image(image_path: str) -> str:
    """
    Upload an image file to Supabase storage bucket and return public URL
    
    Args:
        image_path: Path to the image file to upload
    
    Returns:
        str: Public URL of the uploaded image
    """
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET')
    
    if not all([SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET]):
        raise Exception("Missing Supabase configuration. Set SUPABASE_URL, SUPABASE_KEY, and SUPABASE_BUCKET in .env")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Check if file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Read image file
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Generate unique filename with timestamp
    file_ext = Path(image_path).suffix or '.png'
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    
    # Determine content type
    content_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    content_type = content_type_map.get(file_ext.lower(), 'image/png')
    
    # Upload to Supabase
    try:
        res = supabase.storage.from_(SUPABASE_BUCKET).upload(
            filename, 
            image_bytes, 
            {"content-type": content_type}
        )
        
        if not res:
            raise Exception("Failed to upload image to Supabase")
        
        # Get public URL
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
        
        print(f"✅ Image uploaded successfully: {filename}")
        print(f"📸 Public URL: {public_url}")
        
        return public_url
        
    except Exception as e:
        raise Exception(f"Failed to upload image to Supabase: {str(e)}")

if __name__ == "__main__":
    # Example usage
    result = upload_image("generated_image.png")
    print(f"Public URL: {result}")