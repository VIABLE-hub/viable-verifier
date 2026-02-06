import os
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from logging import getLogger

logger = getLogger("LOGGER")


def preprocess_image(path, resolution, keep_aspect_ratio=False):
    logger.info(f"🩺 HERZCHIRURG - preprocess_image called with path: {path}")
    try:
        img = Image.open(path)
        logger.info(f"🩺 Image loaded successfully - Size: {img.size}, Mode: {img.mode}")
        
        # Stelle sicher, dass das Bild gültig ist
        if img.size[0] <= 0 or img.size[1] <= 0:
            raise ValueError("Ungültige Bildgröße: {}".format(img.size))
            
        if img.mode != "RGB":
            if img.mode == "RGBA":
                # 🩺 HERZCHIRURG SMART FIX: Intelligent background color detection
                logger.info(f"🩺 RGBA detected - analyzing image to choose background color")
                
                # Analysiere die durchschnittliche Helligkeit der nicht-transparenten Pixel
                rgba_data = img.getdata()
                non_transparent_pixels = [pixel[:3] for pixel in rgba_data if pixel[3] > 128]  # Alpha > 128
                
                if non_transparent_pixels:
                    avg_brightness = sum(sum(pixel) for pixel in non_transparent_pixels) / (len(non_transparent_pixels) * 3)
                    logger.info(f"🩺 Average brightness of logo: {avg_brightness:.1f}")
                    
                    # Wenn das Logo hell ist (> 200), verwende einen dunklen Hintergrund
                    # Wenn das Logo dunkel ist (< 200), verwende einen hellen Hintergrund
                    if avg_brightness > 200:
                        bg_color = (40, 40, 40)  # Dunkler Hintergrund für helle Logos
                        logger.info(f"🩺 Light logo detected - using dark background: {bg_color}")
                    else:
                        bg_color = (255, 255, 255)  # Heller Hintergrund für dunkle Logos
                        logger.info(f"🩺 Dark logo detected - using light background: {bg_color}")
                else:
                    # Fallback: weißer Hintergrund
                    bg_color = (255, 255, 255)
                    logger.info(f"🩺 No non-transparent pixels found - using white background")
                
                smart_bg = Image.new('RGB', img.size, bg_color)
                smart_bg.paste(img, mask=img.split()[-1])  # Use alpha as mask
                img = smart_bg
            else:
                img = img.convert("RGB")
            logger.info(f"🩺 Image converted to RGB mode")

        if keep_aspect_ratio:
            original_width, original_height = img.size
            max_height = resolution[1]
            scale_factor = max_height / original_height
            new_width = int(original_width * scale_factor)
            img = img.resize((new_width, max_height))
            logger.info(f"🩺 Image resized (aspect ratio) to: {img.size}")
        else:
            img = img.resize(resolution)
            logger.info(f"🩺 Image resized to: {img.size}")

        # base 64 encode the image as jpg
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=90)  # Erhöhte Qualität
        img_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        logger.info(f"🩺 Image successfully encoded to base64, length: {len(img_data)}")
        return img_data
    except Exception as e:
        logger.error(f"🩺 HERZCHIRURG ERROR - Bildverarbeitung failed for {path}: {str(e)}")
        # Erstelle ein Standardbild mit den angeforderten Abmessungen
        fallback_img = Image.new('RGB', resolution, color='#f0f0f0')
        
        # Füge einen Text hinzu, um anzuzeigen, dass es ein Fallback ist
        draw = ImageDraw.Draw(fallback_img)
        text = "Placeholder"
        
        # Berechne Textposition für die Mitte des Bildes
        text_x = resolution[0] // 2
        text_y = resolution[1] // 2
        
        # Zeichne den Text
        draw.text((text_x, text_y), text, fill='#555555', anchor='mm')
        
        # Base64-Kodierung des Fallback-Bildes
        buffered = BytesIO()
        fallback_img.save(buffered, format="JPEG")
        fallback_img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        logger.info(f"🩺 Fallback image created, length: {len(fallback_img_str)}")
        return fallback_img_str


def preprocess_theme_icon(path, resolution, keep_aspect_ratio=False):
    """
    🩺 HERZCHIRURG FIX: Spezielle Verarbeitung für Theme-Icons die Transparenz beibehält
    """
    logger.info(f"🩺 HERZCHIRURG - preprocess_theme_icon called with path: {path}")
    try:
        img = Image.open(path)
        logger.info(f"🩺 Theme icon loaded successfully - Size: {img.size}, Mode: {img.mode}")
        
        # Stelle sicher, dass das Bild gültig ist
        if img.size[0] <= 0 or img.size[1] <= 0:
            raise ValueError("Ungültige Bildgröße: {}".format(img.size))
        
        # Für Theme-Icons behalten wir RGBA/Transparenz bei
        if img.mode != "RGBA":
            if img.mode == "RGB":
                # Konvertiere RGB zu RGBA (füge Alpha-Kanal hinzu)
                img = img.convert("RGBA")
                logger.info(f"🩺 RGB converted to RGBA for transparency support")
            elif img.mode in ("L", "P"):
                img = img.convert("RGBA")
                logger.info(f"🩺 {img.mode} converted to RGBA for transparency support")

        if keep_aspect_ratio:
            original_width, original_height = img.size
            max_height = resolution[1]
            scale_factor = max_height / original_height
            new_width = int(original_width * scale_factor)
            img = img.resize((new_width, max_height), Image.Resampling.LANCZOS)
            logger.info(f"🩺 Theme icon resized (aspect ratio) to: {img.size}")
        else:
            img = img.resize(resolution, Image.Resampling.LANCZOS)
            logger.info(f"🩺 Theme icon resized to: {img.size}")

        # Speichere als PNG um Transparenz zu erhalten
        buffered = BytesIO()
        img.save(buffered, format="PNG", optimize=True)
        img_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        logger.info(f"🩺 Theme icon successfully encoded to base64 PNG, length: {len(img_data)}")
        return img_data
        
    except Exception as e:
        logger.error(f"🩺 HERZCHIRURG ERROR - Theme icon processing failed for {path}: {str(e)}")
        # Erstelle ein transparentes Fallback-Bild
        fallback_img = Image.new('RGBA', resolution, color=(240, 240, 240, 128))  # Halbtransparent
        
        # Füge einen Text hinzu
        draw = ImageDraw.Draw(fallback_img)
        text = "Logo"
        text_x = resolution[0] // 2
        text_y = resolution[1] // 2
        draw.text((text_x, text_y), text, fill=(85, 85, 85, 255), anchor='mm')
        
        # Base64-Kodierung des Fallback-Bildes als PNG
        buffered = BytesIO()
        fallback_img.save(buffered, format="PNG")
        fallback_img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        logger.info(f"🩺 Transparent fallback theme icon created, length: {len(fallback_img_str)}")
        return fallback_img_str


def get_placeholders(logo_filename="studentVC-logo-sora-cropped-darkmode.png", profile_filename="student.png"):
    from flask import current_app, has_app_context
    import os
    
    if not has_app_context():
        # Fallback if called outside application context (e.g. during import)
        return None, None
    
    # Construct base paths
    # Note: Flask's static_folder is absolute
    static_folder = current_app.static_folder 
    img_folder = os.path.join(static_folder, 'img')
    
    # Check img folder first
    logo_path = os.path.join(img_folder, logo_filename)
    if not os.path.exists(logo_path):
        logo_path = os.path.join(static_folder, logo_filename)
        
    profile_path = os.path.join(img_folder, profile_filename)
    if not os.path.exists(profile_path):
        profile_path = os.path.join(static_folder, profile_filename)

    logger.info(f"🩺 get_placeholders: Logo path={logo_path}, Profile path={profile_path}")

    logo = preprocess_image(logo_path, (400, 300), keep_aspect_ratio=True)
    profile = preprocess_image(profile_path, (400, 400), keep_aspect_ratio=True)
    
    logger.info(f"🩺 Final logo base64 length: {len(logo) if logo else 'None'}")
    logger.info(f"🩺 Final profile base64 length: {len(profile) if profile else 'None'}")

    return logo, profile


if __name__ == "__main__":
    print(get_placeholders())
