# Handwriting API Quick Reference

## Setup

```bash
# Ensure you're in the API directory
cd c:\github\train-printed\api

# Start the API
uvicorn app.main:app --reload
# Server will run at http://localhost:8000
```

## Test the Corpus Endpoints

### Get Tier-1 Sentences (Beginner Level)

```bash
curl "http://localhost:8000/handwriting/corpus/tier-1?limit=5"
```

Response:

```json
{
  "tier": "tier-1",
  "count": 5,
  "sentences": [
    "විජය රජු",
    "පණ්ඩුවාසදේව රජු",
    "අභය රජතුමා",
    "පණ්ඩුකාභය මහරජ",
    "මුටසීව රජු"
  ]
}
```

### Get Tier-2 Sentences (Intermediate Level)

```bash
curl "http://localhost:8000/handwriting/corpus/tier-2?limit=3"
```

Response:

```json
{
  "tier": "tier-2",
  "count": 3,
  "sentences": [
    "පුරාණ රජුන් මහා වැව් රාශියක් ඉදි කළහ.",
    "අනුරාධපුර යුගයේදී බුදු දහම ලංකාවට ලැබුණි.",
    "දුටුගැමුණු රජතුමා රට එක්සේසත් කිරීමට කටයුතු කළේය."
  ]
}
```

## Test Handwriting Submission

### Submit Handwriting (Guest User)

```bash
# With a PNG/JPG image file
curl -X POST "http://localhost:8000/handwriting/submit?tier=tier-1&sentence=විජය%20රජු" \
  -F "file=@path/to/handwriting.png"
```

Response:

```json
{
  "status": "success",
  "line_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "message": "Handwriting submitted successfully"
}
```

### Submit with Authenticated User

```bash
# Include Authorization header
curl -X POST "http://localhost:8000/handwriting/submit?tier=tier-2&sentence=පුරාණ%20රජුන්" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@handwriting.png"
```

## Retrieve Submissions

### Get All Handwriting for a User

```bash
curl "http://localhost:8000/handwriting/document/{user_id}/tier-1"
```

Example with actual UUID:

```bash
curl "http://localhost:8000/handwriting/document/550e8400-e29b-41d4-a716-446655440000/tier-1"
```

Response:

```json
{
  "document_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "tier": "tier-1",
  "title": "Handwriting Practice - TIER-1",
  "total_submissions": 3,
  "created_at": "2026-01-27T10:30:00",
  "line_images": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440000",
      "image_path": "lines/handwriting-tier-1-550e8400.../line_0001.png",
      "png_path": "lines/handwriting-tier-1-550e8400.../line_0001.png",
      "text": "විජය රජු",
      "verified": false,
      "created_at": "2026-01-27T10:31:00"
    }
  ]
}
```

### Get Document Submissions

```bash
curl "http://localhost:8000/handwriting/submissions/{document_id}"
```

## Python Test Script

Run the included test script:

```bash
python test_handwriting.py
```

This will test:

- ✓ Corpus endpoints
- ✓ Guest handwriting submission
- ✓ Invalid file format rejection

## Interactive Testing with cURL

### Create a Test Image

Using ImageMagick (if installed):

```bash
convert -size 200x100 xc:white test.png
```

Or using Python:

```python
from PIL import Image
img = Image.new('RGB', (200, 100), color='white')
img.save('test.png')
```

### Submit Test Image

```bash
curl -X POST "http://localhost:8000/handwriting/submit?tier=tier-1&sentence=test" \
  -F "file=@test.png"
```

## OpenAPI/Swagger UI

View all endpoints interactively:

- Go to: http://localhost:8000/docs
- Or: http://localhost:8000/redoc

## File Structure After First Submission

```
lines/
└── handwriting-tier-1-{guest_user_id}/
    ├── line_0001.png          (submitted image)
    └── line_0001.gt.txt       (sentence text)

Database:
- User: "Guest User" (guest@handwriting.local)
- Document: "Handwriting Practice - TIER-1" (type: handwriting-tier-1)
- Page: Virtual page_0001
- LineImage: Records for each submission
```

## Error Handling

### Invalid Tier

```bash
curl "http://localhost:8000/handwriting/corpus/tier-3?limit=5"
```

Response (400 Bad Request):

```json
{
  "detail": "Invalid tier. Use 'tier-1' or 'tier-2'"
}
```

### Invalid File Format

```bash
curl -X POST "http://localhost:8000/handwriting/submit?tier=tier-1&sentence=test" \
  -F "file=@test.txt"
```

Response (400 Bad Request):

```json
{
  "detail": "Invalid file type. Only PNG, JPG, JPEG, WEBP allowed"
}
```

### Missing Image File

```bash
curl -X POST "http://localhost:8000/handwriting/submit?tier=tier-1&sentence=test"
```

Response (422 Unprocessable Entity):

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "file"],
      "msg": "Field required"
    }
  ]
}
```

## Notes

- No authentication required for corpus or guest submissions
- Guest users automatically created on first submission
- Each user gets ONE document per tier
- Multiple submissions accumulate in the same document
- Ground truth (.gt.txt) files created automatically
- Images must be PNG, JPG, JPEG, or WEBP
- Sinhala text supported in sentence field (UTF-8)
