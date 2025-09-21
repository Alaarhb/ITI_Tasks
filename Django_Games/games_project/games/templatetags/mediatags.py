from django import template
from django.conf import settings
from PIL import Image
import os

register = template.Library()

@register.simple_tag
def thumbnail_url(image_field, size='medium'):
    """Generate thumbnail URL for an image"""
    if not image_field:
        return ''
    
    # Get thumbnail path
    file_path = image_field.path
    base_path, ext = os.path.splitext(file_path)
    thumbnail_path = f"{base_path}_{size}{ext}"
    
    # Check if thumbnail exists
    if os.path.exists(thumbnail_path):
        # Return URL for thumbnail
        base_url, ext = os.path.splitext(image_field.url)
        return f"{base_url}_{size}{ext}"
    
    # Return original if thumbnail doesn't exist
    return image_field.url

@register.filter
def file_size(file_field):
    """Get human readable file size"""
    if not file_field:
        return ''
    
    try:
        size = file_field.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return ''

@register.filter
def image_dimensions(image_field):
    """Get image dimensions"""
    if not image_field:
        return ''
    
    try:
        with Image.open(image_field.path) as img:
            return f"{img.width} × {img.height}"
    except:
        return ''

@register.inclusion_tag('games/tags/media_gallery.html')
def media_gallery(images, title="Gallery"):
    """Render image gallery"""
    return {
        'images': [img for img in images if img],
        'title': title,
    }

print("🚀 Django Lab4 Advanced Features Created!")
print("📊 Custom QuerySet Methods: Advanced filtering and statistics")
print("📁 Media File Handling: Image upload, processing, and optimization")
print("🎯 Study Materials: QuerySet patterns and media file management")