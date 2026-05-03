"""
AI Image Generator API using Hugging Face Inference Client
"""
import os
import io
import base64
import logging
from flask import Flask, request, jsonify, send_file
from huggingface_hub import InferenceClient
from PIL import Image
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Hugging Face client
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    logger.error("❌ HF_TOKEN environment variable is NOT SET!")
    logger.error("   Please set your Hugging Face API token before running:")
    logger.error("   export HF_TOKEN=your_huggingface_token_here")
    logger.error("   Image generation functionality will NOT work without this token.")
    # Don't exit immediately - allow server to start for health checks
    client = None
else:
    client = InferenceClient(
        token=HF_TOKEN,
    )
    logger.info(f"✅ Successfully initialized Hugging Face client")

# Default model configuration
DEFAULT_MODEL = "black-forest-labs/FLUX.1-schnell"
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 768

BASE_URL = os.environ.get("IMAGE_GENERATOR_URL", "http://python:5000").rstrip("/")
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "generated_images")
os.makedirs(IMAGES_DIR, exist_ok=True)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "ai-storybook-publisher-python"}), 200


def save_generated_image(image: Image.Image, prompt: str) -> str:
    filename = f"image_{abs(hash(prompt + str(os.urandom(8))))}.png"
    path = os.path.join(IMAGES_DIR, filename)
    image.save(path, format="PNG")
    return f"{BASE_URL}/images/{filename}"


@app.route("/images/<path:filename>", methods=["GET"])
def serve_image(filename):
    return send_file(os.path.join(IMAGES_DIR, filename), mimetype="image/png")


@app.route("/generate-image", methods=["POST"])
def generate_image():
    """
    Generate image from text prompt
    
    Request body:
    {
        "prompt": "string (required) - The text description for image generation",
        "model": "string (optional) - HF model name, defaults to FLUX.1-dev",
        "width": "integer (optional) - Image width in pixels, default 1024",
        "height": "integer (optional) - Image height in pixels, default 768",
        "return_type": "string (optional) - 'url' or 'base64', defaults to 'url'"
    }
    
    Returns:
    {
        "success": true,
        "image_url": "string or base64 encoded image",
        "model": "string - model used",
        "prompt": "string - prompt used"
    }
    """
    try:
        data = request.get_json()
        
        if not data or "prompt" not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'prompt' in request body"
            }), 400
        
        prompt = data.get("prompt", "").strip()
        if not prompt:
            return jsonify({
                "success": False,
                "error": "'prompt' cannot be empty"
            }), 400
        
        model = data.get("model", DEFAULT_MODEL)
        width = data.get("width", DEFAULT_WIDTH)
        height = data.get("height", DEFAULT_HEIGHT)
        return_type = data.get("return_type", "url").lower()
        
        # Validate dimensions
        if not isinstance(width, int) or not isinstance(height, int):
            return jsonify({
                "success": False,
                "error": "width and height must be integers"
            }), 400
        
        if width < 256 or height < 256 or width > 2048 or height > 2048:
            return jsonify({
                "success": False,
                "error": "width and height must be between 256 and 2048"
            }), 400
        
        if return_type not in ["url", "base64"]:
            return jsonify({
                "success": False,
                "error": "return_type must be 'url' or 'base64'"
            }), 400
        
        logger.info(f"Generating image with prompt: {prompt[:100]}... using model: {model}")
        
        if not client:
            return jsonify({
                "success": False,
                "error": "Hugging Face client not initialized. HF_TOKEN environment variable is required."
            }), 500

        image = client.text_to_image(
            prompt=prompt,
            model=model,
            height=height,
            width=width,
        )

        if return_type == "base64":
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            base64_str = base64.b64encode(img_byte_arr.getvalue()).decode()
            
            return jsonify({
                "success": True,
                "image": f"data:image/png;base64,{base64_str}",
                "model": model,
                "prompt": prompt,
                "width": width,
                "height": height
            }), 200

        image_url = save_generated_image(image, prompt)
        return jsonify({
            "success": True,
            "image_url": image_url,
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/generate-image/file", methods=["POST"])
def generate_image_file():
    """
    Generate image and return as downloadable file
    
    Request body:
    {
        "prompt": "string (required) - The text description for image generation",
        "model": "string (optional) - HF model name, defaults to FLUX.1-dev",
        "width": "integer (optional) - Image width in pixels, default 1024",
        "height": "integer (optional) - Image height in pixels, default 768"
    }
    
    Returns: PNG image file
    """
    try:
        data = request.get_json()
        
        if not data or "prompt" not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'prompt' in request body"
            }), 400
        
        prompt = data.get("prompt", "").strip()
        if not prompt:
            return jsonify({
                "success": False,
                "error": "'prompt' cannot be empty"
            }), 400
        
        model = data.get("model", DEFAULT_MODEL)
        width = data.get("width", DEFAULT_WIDTH)
        height = data.get("height", DEFAULT_HEIGHT)
        
        logger.info(f"Generating image file with prompt: {prompt[:100]}... using model: {model}")
        
        if not client:
            return jsonify({
                "success": False,
                "error": "Hugging Face client not initialized. HF_TOKEN environment variable is required."
            }), 500

        # Generate image using Hugging Face Inference Client
        image = client.text_to_image(
            prompt=prompt,
            model=model,
            height=height,
            width=width,
        )
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return send_file(
            img_byte_arr,
            mimetype='image/png',
            as_attachment=True,
            download_name='generated_image.png'
        )
    
    except Exception as e:
        logger.error(f"Error generating image file: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


if __name__ == "__main__":
    import sys
    
    # Check if running in CLI mode (pass prompt as command line argument)
    if len(sys.argv) > 1:
        # CLI mode: generate image directly from terminal
        prompt = ' '.join(sys.argv[1:])
        
        if not client:
            print("\n❌ ERROR: HF_TOKEN environment variable is not set!")
            print("   Please set your Hugging Face API token first:")
            print("   export HF_TOKEN=your_huggingface_token_here\n")
            sys.exit(1)
            
        print(f"\n🖼️  Generating image for prompt: {prompt[:100]}...")
        print(f"🔍 Using model: {DEFAULT_MODEL}")
        
        try:
            image = client.text_to_image(
                prompt=prompt,
                model=DEFAULT_MODEL,
                height=DEFAULT_HEIGHT,
                width=DEFAULT_WIDTH,
            )
            
            filename = f"terminal_generated_{abs(hash(prompt))}.png"
            image.save(filename)
            print(f"\n✅ Success! Image saved as: {filename}")
            print(f"📂 Full path: {os.path.abspath(filename)}\n")
            
        except Exception as e:
            print(f"\n❌ Failed to generate image: {str(e)}\n")
            sys.exit(1)
            
    else:
        # Web server mode
        port = int(os.environ.get("PORT", 5000))
        debug = os.environ.get("DEBUG", "False").lower() == "true"
        
        logger.info(f"Starting AI Image Generator API on port {port}")
        logger.info(f"Using HF model: {DEFAULT_MODEL}")
        logger.info(f"Debug mode: {debug}")
        
        app.run(host="0.0.0.0", port=port, debug=debug)
