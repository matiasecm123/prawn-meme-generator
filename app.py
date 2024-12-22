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

def generate_meme(image_path, top_text, bottom_text, output_path, font_path=None, initial_font_size=150, font_choice='impact'):
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

    # Resize the image to ensure it is large enough to be cropped to 1312x1312
    image_width, image_height = image.size
    target_size = 1312

    # Calculate the scaling factor to make sure the shortest dimension is at least 1312
    scale_factor = max(target_size / image_width, target_size / image_height)
    new_width = int(image_width * scale_factor)
    new_height = int(image_height * scale_factor)
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Crop the center of the image to 1312x1312
    left = (new_width - target_size) // 2
    upper = (new_height - target_size) // 2
    right = (new_width + target_size) // 2
    lower = (new_height + target_size) // 2

    image = image.crop((left, upper, right, lower))

    # Adjust font size for 'bubblegum.ttf' to make it fit better
    if font_choice == 'bubblegum':
        font_size = initial_font_size - 30  # Reduce size for Bubblegum font
        font_color = (255, 165, 0)  # Orange color
    else:
        font_size = initial_font_size
        font_color = (255, 255, 255)  # White color

    # Load the selected font based on the user's choice
    try:
        if font_choice == 'bubblegum':
            font_path = os.path.join(FONTS_FOLDER, 'bubblegum.ttf')
        else:
            font_path = os.path.join(FONTS_FOLDER, 'Impact.ttf')
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print(f"Error loading font: {e}")
        return None

    draw = ImageDraw.Draw(image)

    def draw_centered_text(draw, text, initial_y, font, image_width, max_width=0.95, border_width=5, text_color=(255, 255, 255)):
        max_text_width = image_width * max_width
        lines = textwrap.wrap(text, width=20)  # Adjust wrap width based on font size
        y = initial_y

        for line in lines:
            # Use getbbox() to calculate text dimensions
            bbox = font.getbbox(line)  # Returns a tuple (left, top, right, bottom)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (image_width - text_width) // 2

            # Draw text with border
            for dx in [-border_width, 0, border_width]:
                for dy in [-border_width, 0, border_width]:
                    draw.text((x + dx, y + dy), line, font=font, fill="black")

            # Draw the text
            draw.text((x, y), line, font=font, fill=text_color)
            y += text_height + 5  # Move to the next line

    if top_text:
        draw_centered_text(draw, top_text, 10, font, image.width, text_color=font_color)

    if bottom_text:
        wrapped_lines = textwrap.wrap(bottom_text, width=20)
        total_text_height = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in wrapped_lines) + (len(wrapped_lines) - 1) * 5

        # Set initial Y position dynamically so the text fits above the bottom edge
        bottom_initial_y = image.height - total_text_height - 20  # Add padding from the bottom
        bottom_initial_y -= 20  # Adjust this value to control the height of the bottom text

        draw_centered_text(draw, bottom_text, bottom_initial_y, font, image.width, text_color=font_color)

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
            <a href="https://x.com/PepeKing_Prawn" target="_blank">Twitter</a> | 
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
