from PIL import Image, ImageDraw, ImageFont
import os

def generate_pixel_scoreboard_icon():
    size = 512
    image = Image.new("RGB", (size, size), color="#121212")  # Dark dashboard background
    draw = ImageDraw.Draw(image)

    # 1. Circular ring border inside Android's safe-zone
    ring_margin = 44
    draw.ellipse(
        [ring_margin, ring_margin, size - ring_margin, size - ring_margin],
        outline="#00ff00",  # Dashboard green
        width=12
    )

    # 2. Try to load a blocky/pixel-style or standard monospace font
    # You can drop a TrueType pixel font (like 'PressStart2P.ttf') in your folder, 
    # and it will automatically use it for that arcade scoreboard look!
    font_path = "PressStart2P-Regular.ttf"
    try:
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 110)
        else:
            # Fallback to standard bold monospace/arial if pixel font isn't present
            font = ImageFont.truetype("arialbd.ttf", 150)
    except IOError:
        font = ImageFont.load_default()

    # 3. Draw the clean, retro scoreboard identifier '// S'
    text = "// S"
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (size - text_width) / 2 - bbox[0]
    text_y = (size - text_height) / 2 - bbox[1] + 5  # Optical centering

    draw.text((text_x, text_y), text, fill="#00ff00", font=font)

    # Save output
    output_path = "app_icon_pixel.png"
    image.save(output_path)
    print(f"Pixel scoreboard app icon saved to {output_path}!")

if __name__ == "__main__":
    generate_pixel_scoreboard_icon()