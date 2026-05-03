# AI Image Generator Specification - AI Kid Storybook Publisher

## 1. System Overview
Standalone Flask microservice that provides AI image generation capabilities using Hugging Face Inference API. Designed specifically for generating high quality children's book illustrations with support for multiple output formats.

## 2. Technology Stack
- **Runtime**: Python 3.11+
- **Framework**: Flask 3.x
- **AI Provider**: Hugging Face Inference Client
- **Default Model**: FLUX.1-schnell (black-forest-labs)
- **Image Processing**: Pillow (PIL)
- **Containerization**: Docker
- **Storage**: Local filesystem for generated images

## 3. Environment Variables
| Variable | Required | Default | Description |
|---|---|---|---|
| `HF_TOKEN` | ✅ | None | Hugging Face API access token |
| `IMAGE_GENERATOR_URL` | ❌ | `http://python:5000` | Public base URL for image serving |
| `PORT` | ❌ | `5000` | Server port |
| `DEBUG` | ❌ | `False` | Flask debug mode |

## 4. API Endpoints

### Health Check
```
GET /health
```
Returns service status and health information.

### Generate Image (JSON)
```
POST /generate-image
```
**Request Body:**
| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `prompt` | String | ✅ | - | Text description for image generation |
| `model` | String | ❌ | FLUX.1-schnell | Hugging Face model name |
| `width` | Integer | ❌ | 1024 | Image width (256-2048 px) |
| `height` | Integer | ❌ | 768 | Image height (256-2048 px) |
| `return_type` | String | ❌ | `url` | Output format: `url` or `base64` |

**Success Response:**
```json
{
  "success": true,
  "image_url": "http://host/images/filename.png",
  "model": "black-forest-labs/FLUX.1-schnell",
  "prompt": "original prompt text",
  "width": 1024,
  "height": 768
}
```

### Generate Image (File Download)
```
POST /generate-image/file
```
Generates image and returns it directly as downloadable PNG file. Same request parameters as above.

### Serve Generated Image
```
GET /images/{filename}
```
Serves previously generated image files from local storage.

## 5. Core Features
- ✅ Aspect ratio support optimized for storybook pages (4:3 default)
- ✅ Duplicate prompt handling with unique filename generation
- ✅ Both base64 and public URL output options
- ✅ Direct file download endpoint
- ✅ CLI mode for testing from terminal
- ✅ Proper error handling and logging
- ✅ Health check endpoint for orchestration
- ✅ Dimension validation (256px - 2048px range)

## 6. Deployment & Operation
- **Dockerized**: Multi-stage build with Python slim runtime
- **Storage**: `generated_images/` directory with automatic creation
- **Port**: Default `5000`
- **Resource Requirements**: Minimal CPU, no GPU required (uses HF cloud inference)
- **Rate Limiting**: Subject to Hugging Face API rate limits

## 7. Integration with Storybook System
This service is designed to be used by the backend `StoryGenerationService` for creating page illustrations. Supports the exact dimensions required for PDF generation and provides stable public URLs that can be stored in database records.