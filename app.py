from flask import Flask, request, send_file, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, 'images')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')
FONTS_FOLDER = os.path.join(BASE_DIR, 'fonts')
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(FONTS_FOLDER, exist_ok=True)

IMAGES = [
    'image.png',
    'image2.png',
    'image3.png'
]

# Serve static files from the images directory
@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(STATIC_FOLDER, filename)

def generate_meme(image_path, top_text, bottom_text, output_path, font_path=None, initial_font_size=150):
    """Generate a meme with bold, large text placement."""
    top_text = top_text.upper()  # Convert to uppercase
    bottom_text = bottom_text.upper()  # Convert to uppercase
    
    # Load the image
    try:
        image = Image.open(image_path).convert("RGBA")  # Ensure image is in RGBA mode
    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
        return None
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

    image_width, image_height = image.size

    # Load the font
    if font_path is None:
        font_path = os.path.join(FONTS_FOLDER, 'Impact.ttf')  # Use Impact font for memes
    try:
        font = ImageFont.truetype(font_path, initial_font_size)
    except IOError:
        print(f"Error: Font file not found at {font_path}. Falling back to default font.")
        font = ImageFont.load_default()
    except Exception as e:
        print(f"Error loading font: {e}")
        return None

    draw = ImageDraw.Draw(image)

    def draw_centered_text(draw, text, initial_y, font, image_width, max_width=0.95, border_width=5):
        """Draw centered, bold, and large text."""
        max_text_width = image_width * max_width
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            text_width = font.getbbox(test_line)[2]

            if text_width > max_text_width:  # If the line exceeds the maximum width
                current_line.pop()  # Remove the last word
                lines.append(' '.join(current_line))  # Finalize the current line
                current_line = [word]  # Start a new line

        if current_line:
            lines.append(' '.join(current_line))

        while True:
            largest_line_width = max(font.getbbox(line)[2] for line in lines)
            total_text_height = sum(font.getbbox(line)[3] for line in lines) + (len(lines) - 1) * 5

            if largest_line_width <= max_text_width or font.size <= 10:
                break
            font = ImageFont.truetype(font.path, font.size - 5)

        y = initial_y
        if total_text_height > image_height - initial_y:
            y = max(0, image_height - total_text_height - 20)

        for line in lines:
            text_bbox = font.getbbox(line)
            text_width = text_bbox[2]
            text_height = text_bbox[3]
            x = (image_width - text_width) // 2  # Center horizontally

            for dx in [-border_width, 0, border_width]:
                for dy in [-border_width, 0, border_width]:
                    draw.text((x + dx, y + dy), line, font=font, fill="black")
            draw.text((x, y), line, font=font, fill="white")
            y += text_height + 5  # Move to the next line with minimal padding

    # Draw top text
    if top_text:
        draw_centered_text(draw, top_text, initial_y=10, font=font, image_width=image_width)

    # Draw bottom text
    if bottom_text:
        total_bottom_text_height = sum(
            font.getbbox(line)[3] for line in bottom_text.split('\n')
        ) + (len(bottom_text.split('\n')) - 1) * 5
        bottom_initial_y = image_height - total_bottom_text_height - 20
        draw_centered_text(draw, bottom_text, initial_y=bottom_initial_y, font=font, image_width=image_width)

    # Save the final image
    try:
        rgb_image = image.convert("RGB")
        rgb_image.save(output_path, format="JPEG")
    except IOError as e:
        print(f"Error saving meme: {e}")
        return None

    return output_path

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        selected_image = request.form.get('image')
        text_position = request.form.get('text_position')
        top_text = request.form.get('top_text') if text_position in ('top', 'both') else ''
        bottom_text = request.form.get('bottom_text') if text_position in ('bottom', 'both') else ''

        if not selected_image:
            return "Error: No image selected. Please try again."

        image_path = os.path.join(STATIC_FOLDER, selected_image)
        if not os.path.exists(image_path):
            print(f"Error: Image file not found at {image_path}")
            return "Error: Image file not found. Please try again."

        output_path = os.path.join(OUTPUT_FOLDER, 'generated_meme.jpg')  # Updated output file name

        result_path = generate_meme(image_path, top_text, bottom_text, output_path)
        if not result_path:
            print(f"Debug Info: image_path={image_path}, top_text={top_text}, bottom_text={bottom_text}, output_path={output_path}")
            return "Error generating meme. Possible issues: missing font, image not found, or insufficient permissions."

        return send_file(result_path, mimetype='image/jpeg', as_attachment=True)

    images_html = ''.join([
        f'<label class="image-label"><input type="radio" name="image" value="{img}" required><img src="/images/{img}" alt="{img}"></label>'
        for img in IMAGES
    ])

    return f'''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meme Generator</title>
        <style>
            /* Your CSS code */
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Create Your Meme</h1>
            <form method="post">
                <div class="images-container">
                    {images_html}
                </div>
                <label for="text_position">Text Position:</label>
                <select name="text_position" required onchange="updateTextFields()">
                    <option value="top">Top</option>
                    <option value="bottom">Bottom</option>
                    <option value="both">Both</option>
                </select>
                <div id="top_text_field">
                    <label for="top_text">Top Text:</label>
                    <input type="text" name="top_text" placeholder="Enter top text">
                </div>
                <div id="bottom_text_field">
                    <label for="bottom_text">Bottom Text:</label>
                    <input type="text" name="bottom_text" placeholder="Enter bottom text">
                </div>
                <input type="submit" value="Generate Meme">
            </form>
        </div>
    </body>
    </html>
    '''

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
