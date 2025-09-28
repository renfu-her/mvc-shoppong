import os
from PIL import Image
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def convert_to_webp(image_path, output_path=None, quality=85):
    """Convert image to WebP format"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Generate output path if not provided
            if not output_path:
                base_name = os.path.splitext(image_path)[0]
                output_path = f"{base_name}.webp"
            
            # Save as WebP
            img.save(output_path, 'WebP', quality=quality, optimize=True)
            return output_path
    except Exception as e:
        print(f"Error converting to WebP: {e}")
        return None

def resize_image(image_path, output_path, size, quality=85):
    """Resize image to specified dimensions"""
    try:
        with Image.open(image_path) as img:
            # Resize image maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Create new image with exact size and paste resized image
            new_img = Image.new('RGB', size, (255, 255, 255))
            # Center the image
            x = (size[0] - img.size[0]) // 2
            y = (size[1] - img.size[1]) // 2
            new_img.paste(img, (x, y))
            
            # Convert to WebP and save
            new_img.save(output_path, 'WebP', quality=quality, optimize=True)
            return output_path
    except Exception as e:
        print(f"Error resizing image: {e}")
        return None

def generate_thumbnail(image_path, output_path, size=Config.THUMBNAIL_SIZE, quality=85):
    """Generate thumbnail from image"""
    return resize_image(image_path, output_path, size, quality)

def process_product_image(file, product_id, is_primary=False, sort_order=0):
    """Process and save product image"""
    if not allowed_file(file.filename):
        return None, "Invalid file type"
    
    try:
        # Create directory if it doesn't exist
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, 'products', str(product_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{sort_order}_{int(time.time())}{ext}"
        
        # Save original file
        original_path = os.path.join(upload_dir, unique_filename)
        file.save(original_path)
        
        # Convert to WebP
        webp_filename = f"{name}_{sort_order}_{int(time.time())}.webp"
        webp_path = os.path.join(upload_dir, webp_filename)
        
        if convert_to_webp(original_path, webp_path):
            # Remove original file
            os.remove(original_path)
            
            # Generate thumbnail
            thumb_filename = f"thumb_{webp_filename}"
            thumb_path = os.path.join(upload_dir, thumb_filename)
            generate_thumbnail(webp_path, thumb_path)
            
            # Return relative path for database storage
            relative_path = '/'.join(['uploads', 'products', str(product_id), webp_filename])
            return relative_path, None
        else:
            # If WebP conversion failed, remove original and return error
            os.remove(original_path)
            return None, "Failed to process image"
            
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

def process_ad_image(file, ad_id, image_type='desktop'):
    """Process and save advertisement image"""
    if not allowed_file(file.filename):
        return None, "Invalid file type"
    
    try:
        # Create directory if it doesn't exist
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, 'ads', str(ad_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{image_type}_{name}_{int(time.time())}{ext}"
        
        # Save original file
        original_path = os.path.join(upload_dir, unique_filename)
        file.save(original_path)
        
        # Convert to WebP
        webp_filename = f"{image_type}_{name}_{int(time.time())}.webp"
        webp_path = os.path.join(upload_dir, webp_filename)
        
        # Get target size based on image type
        target_size = Config.AD_IMAGE_SIZE.get(image_type, Config.PRODUCT_IMAGE_SIZE)
        
        if resize_image(original_path, webp_path, target_size):
            # Remove original file
            os.remove(original_path)
            
            # Return relative path for database storage
            relative_path = '/'.join(['uploads', 'ads', str(ad_id), webp_filename])
            return relative_path, None
        else:
            # If processing failed, remove original and return error
            os.remove(original_path)
            return None, "Failed to process image"
            
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

def delete_image(image_path):
    """Delete image file and its thumbnail if exists"""
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            
            # Try to delete thumbnail
            dir_name = os.path.dirname(image_path)
            file_name = os.path.basename(image_path)
            thumb_path = os.path.join(dir_name, f"thumb_{file_name}")
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
                
        return True
    except Exception as e:
        print(f"Error deleting image: {e}")
        return False

def get_image_url(image_path, thumbnail=False):
    """Get full URL for image"""
    if not image_path:
        return None
    
    if thumbnail:
        # Try to get thumbnail version
        dir_name = os.path.dirname(image_path)
        file_name = os.path.basename(image_path)
        thumb_path = os.path.join(dir_name, f"thumb_{file_name}")
        
        # Check if thumbnail exists
        if os.path.exists(os.path.join('static', thumb_path)):
            return f"/static/{thumb_path}"
    
    # Return original image
    return f"/static/{image_path.replace('\\', '/')}"

# Import time for unique filename generation
import time
