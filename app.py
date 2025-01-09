from flask import Flask, request, send_file, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import os
import textwrap
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, 'images')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')
FONTS_FOLDER = os.path.join(BASE_DIR, 'fonts')
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(FONTS_FOLDER, exist_ok=True)

IMAGES = [
    'image.png',
    'image2.png',
    'image3.png'
    
    
]

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(STATIC_FOLDER, filename)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_meme(image_path, top_text, bottom_text, output_path, font_choice='impact', initial_font_size=150):
    top_text = top_text.upper()
    bottom_text = bottom_text.upper()

    try:
        image = Image.open(image_path).convert("RGBA")
    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
        return None
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

    image_width, image_height = image.size
    target_size = 1312
    scale_factor = max(target_size / image_width, target_size / image_height)
    new_width = int(image_width * scale_factor)
    new_height = int(image_height * scale_factor)
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = (new_width - target_size) // 2
    upper = (new_height - target_size) // 2
    right = (new_width + target_size) // 2
    lower = (new_height + target_size) // 2
    image = image.crop((left, upper, right, lower))

    font_path = os.path.join(FONTS_FOLDER, 'impact.ttf') if font_choice == 'impact' else os.path.join(FONTS_FOLDER, 'bubblegum.ttf')
    font_color = (255, 165, 0) if font_choice == 'bubblegum' else (255, 255, 255)

def get_fit_font(draw, text, image_width, max_width, font_path, initial_font_size):
    font_size = initial_font_size
    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        print(f"Error: Font file at {font_path} could not be opened.")
        font = ImageFont.load_default()  # Fallback font if the specific font can't be loaded
        font_size = initial_font_size

    # Calculate text width and reduce font size until it fits
    text_width = font.getbbox(text)[2]  # Get the width of the text
    while text_width > max_width:
        font_size -= 1
        try:
            font = ImageFont.truetype(font_path, font_size)
        except OSError:
            print(f"Error: Font file at {font_path} could not be opened.")
            font = ImageFont.load_default()  # Fallback to default font
        text_width = font.getbbox(text)[2]

    return font

# Helper function to draw centered text
def draw_centered_text(draw, text, y_position, image_width, font, text_color="white", outline_color="black", border_width=5):
    # Get the bounding box of the text to calculate its width and height
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate the x_position to center the text
    x_position = (image_width - text_width) // 2

    # Draw the outline (border) by drawing the text multiple times with larger offsets
    for dx in range(-border_width, border_width + 1):
        for dy in range(-border_width, border_width + 1):
            # Skip the main text position to avoid overwriting
            if dx != 0 or dy != 0:
                draw.text((x_position + dx, y_position + dy), text, font=font, fill=outline_color)

    # Draw the main text on top in the desired color
    draw.text((x_position, y_position), text, font=font, fill=text_color)


# Main function to generate meme
def generate_meme(image_path, top_text, bottom_text, output_path, font_choice='impact', initial_font_size=150):
    # Determine font path based on font_choice
    font_path = os.path.join(FONTS_FOLDER, f'{font_choice}.ttf')  # Path to font in fonts folder
    if not os.path.isfile(font_path):
        print(f"Error: Font file {font_path} does not exist.")
        return None

    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size

    # Set default text color
    text_color = (255, 255, 255)

    # Draw top text
    if top_text:
        top_font = get_fit_font(draw, top_text, image_width, image_width * 0.95, font_path, initial_font_size)
        draw_centered_text(draw, top_text, 10, image_width, top_font)

    # Draw bottom text
    if bottom_text:
        wrapped_lines = textwrap.wrap(bottom_text, width=20)
        total_text_height = sum(get_fit_font(draw, line, image_width, image_width * 0.95, font_path, initial_font_size).getbbox(line)[3] for line in wrapped_lines)
        bottom_y = image_height - total_text_height - 20
        for line in wrapped_lines:
            bottom_font = get_fit_font(draw, line, image_width, image_width * 0.95, font_path, initial_font_size)
            draw_centered_text(draw, line, bottom_y, image_width, bottom_font)
            bottom_y += bottom_font.getbbox(line)[3] - bottom_font.getbbox(line)[1] + 5  # Add space between lines



    image.convert("RGB").save(output_path, "JPEG")
    return output_path


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        uploaded_file = request.files.get('uploaded_image')
        selected_image = request.form.get('image')

        # Check if an image is uploaded
        if uploaded_file:
            if not allowed_file(uploaded_file.filename):
                return "Error: Unsupported file format. Please upload a .jpg, .jpeg, or .png image."

            filename = secure_filename(uploaded_file.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(image_path)

        # Check if a preset image is selected
        elif selected_image:
            image_path = os.path.join(STATIC_FOLDER, selected_image)
        else:
            return "Error: No image selected or uploaded. Please try again."

        # Retrieve text and position inputs
        text_position = request.form.get('text_position')
        top_text = request.form.get('top_text') if text_position in ('top', 'both') else ''
        bottom_text = request.form.get('bottom_text') if text_position in ('bottom', 'both') else ''

        # Get font choice
        font_choice = request.form.get('font_select', 'impact')

        # Generate meme
        output_path = os.path.join(OUTPUT_FOLDER, 'generated_meme.jpg')
        result_path = generate_meme(image_path, top_text, bottom_text, output_path, font_choice=font_choice)
        if not result_path:
            return "Error generating meme. Please try again."

        return send_file(result_path, mimetype='image/jpeg', as_attachment=True)

    # Generate HTML for preset images
    images_html = ''.join([
        f'<label class="image-label"><input type="radio" name="image" value="{img}"><img src="/images/{img}" alt="{img}"></label>'
        for img in IMAGES
    ])

    

    return f'''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>$PRAWN Meme Generator</title>
        <style>
                       @import url('https://fonts.googleapis.com/css2?family=Fredoka+One&display=swap');
            body {{
                font-family: 'Fredoka One', cursive;
                background: linear-gradient(135deg, #FF7A00, #FF3D3D);
                color: #fff;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}
            .container {{
                background: #fff;
                color: #333;
                box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
                border-radius: 15px;
                padding: 25px;
                width: 90%;
                max-width: 600px;
                text-align: center;
            }}
            h1 {{
                font-size: 32px;
                color: #FF4500;
                margin-bottom: 20px;
            }}
            label {{
                font-size: 16px;
                margin-top: 10px;
                display: block;
                color: #555;
            }}
            input[type=text] {{
                width: 100%;
                padding: 12px;
                margin-top: 8px;
                border: 2px solid #FF7A00;
                border-radius: 8px;
                font-size: 16px;
                box-sizing: border-box;
                outline: none;
            }}
            input[type=radio] {{
                display: none;
            }}
            input[type=submit] {{
                background: linear-gradient(90deg, #FF7A00, #FF4500);
                color: white;
                border: none;
                padding: 12px;
                font-size: 18px;
                cursor: pointer;
                border-radius: 8px;
                margin-top: 20px;
            }}
            footer {{
                margin-top: 20px;
                font-size: 14px;
                color: #777;
            }}
            footer a {{
                color: #FF4500;
                text-decoration: none;
                margin: 0 5px;
                font-weight: bold;
            }}
            .images-container {{
                display: flex;
                justify-content: space-around;
                align-items: center;
                flex-wrap: wrap;
            }}
            .image-label img {{
                width: 150px;
                height: 150px;
                object-fit: cover;
                border-radius: 10px;
                cursor: pointer;
                border: 2px solid transparent;
                transition: border 0.3s;
            }}
            .image-label input:checked + img {{
                border: 2px solid #FF4500;
            }}
            .hidden {{
                display: none;
            }}
        </style>
        <script>
        function updateTextFields() {{
            const position = document.querySelector('#text_position').value;
            const topTextField = document.querySelector('#top_text_field');
            const bottomTextField = document.querySelector('#bottom_text_field');

            // Show/hide text fields based on selection
            if (position === 'bottom') {{
                topTextField.style.display = 'none';
                bottomTextField.style.display = 'block';
            }} else if (position === 'top') {{
                topTextField.style.display = 'block';
                bottomTextField.style.display = 'none';
            }} else {{
                topTextField.style.display = 'block';
                bottomTextField.style.display = 'block';
            }}
         }}

                 // Ensure correct initial state
        document.addEventListener('DOMContentLoaded', updateTextFields);
        
        </script>
    </head>
    <body>
    <div class="container">
        <h1>Create Your Pepe the King Prawn Meme</h1>
        <form method="post" enctype="multipart/form-data">
            <div>
                <h2>Select a Prawn image:</h2>
                <div class="images-container">
                    <!-- Placeholder for image options -->
                    <!-- Add your dynamic images here as per your backend -->
                    <label class="image-label">
                        <input type="radio" name="image" value="image.png">
                        <img src="/images/image.png" alt="Image 1">
                    </label>
                    <label class="image-label">
                        <input type="radio" name="image" value="image2.png">
                        <img src="/images/image2.png" alt="Image 2">
                    </label>
                    <label class="image-label">
                        <input type="radio" name="image" value="image3.png">
                        <img src="/images/image3.png" alt="Image 3">
                    </label>
                </div>
            </div>
            <div>
                <h2>Or upload your own image:</h2>
                <input type="file" name="uploaded_image" accept="image/*">
            </div>
            <div>
                <label for="text_position">Text Position:</label>
                <select name="text_position" id="text_position" onchange="updateTextFields()">
                    <option value="top">Top</option>
                    <option value="bottom">Bottom</option>
                    <option value="both">Both</option>
                </select>
            </div>
            <div>
                <label for="font_select">Select Text Style:</label>
                <select name="font_select" id="font_select">
                    <option value="impact">Classic</option>
                    <option value="bubblegum">Unique</option>
                </select>
            </div>
            <div id="top_text_field">
                <label for="top_text">Top Text:</label>
                <input type="text" name="top_text">
            </div>
            <div id="bottom_text_field">
                <label for="bottom_text">Bottom Text:</label>
                <input type="text" name="bottom_text">
            </div>
            <input type="submit" value="Generate Meme">
        </form>
        <footer>
            🦐 $PRAWN on Solana | CA: 6b7NtVRo6jDSUZ75qfhHgpy99XVkSu1kfoTFu2E3pump<br>
            <a href="https://x.com/PepeKing_Prawn" target="_blank">X</a> | 
            <a href="https://t.me/PrawnOnSol" target="_blank">Telegram</a> | 
            <a href="https://www.instagram.com/pepethekingprawn_sol/" target="_blank">Instagram</a> | 
            <a href="https://prawnsol.com/" target="_blank">Website</a> | 
            <a href="https://dexscreener.com/solana/YGSV5UKCXz3WLAyfviB7oWHQRQbvm5ETtyFVPfystmh" target="_blank">Dexscreener</a>
        </footer>
    </div>
    </body>
    </html>
    '''


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
