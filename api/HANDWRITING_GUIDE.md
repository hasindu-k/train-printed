# Handwriting Endpoint Guide

## Overview

The handwriting endpoints allow users (both authenticated and guest) to practice handwriting by writing Sinhala sentences at different difficulty levels. Each user gets a single document per difficulty tier that accumulates their submissions.

## Corpus Data

- **Tier-1 (Beginner)**: Simple Sinhala words and names (1091 sentences)
- **Tier-2 (Intermediate)**: Complex Sinhala sentences (1751 sentences)

## Endpoints

### 1. Get Corpus Sentences (No Auth Required)

**GET** `/handwriting/corpus/{tier}`

Gets random sentences from the corpus for handwriting practice.

**Parameters:**

- `tier` (path): `tier-1` or `tier-2`
- `limit` (query): Number of sentences to return (default: 10)

**Example Request:**

```bash
GET /handwriting/corpus/tier-1?limit=5
```

**Response:**

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

---

### 2. Submit Handwriting (Guest or Authenticated)

**POST** `/handwriting/submit`

Submit a handwritten image for a sentence. Guest users are automatically assigned to a guest user account. Authenticated users use their own account.

**Form Data:**

- `tier` (query): `tier-1` or `tier-2`
- `sentence` (query): The sentence text that was written
- `file` (file): The handwritten image (PNG, JPG, JPEG, WEBP)

**Example Request:**

```bash
curl -X POST "http://localhost:8000/handwriting/submit?tier=tier-1&sentence=විජය%20රජු" \
  -F "file=@handwriting.png"
```

**Response:**

```json
{
  "status": "success",
  "line_id": "123e4567-e89b-12d3-a456-426614174000",
  "document_id": "223e4567-e89b-12d3-a456-426614174000",
  "message": "Handwriting submitted successfully"
}
```

---

### 3. Get User's Handwriting Document

**GET** `/handwriting/document/{user_id}/{tier}`

Retrieve all handwritten submissions for a specific user and difficulty tier. Shows them as a single cohesive document.

**Parameters:**

- `user_id` (path): UUID of the user
- `tier` (path): `tier-1` or `tier-2`

**Example Request:**

```bash
GET /handwriting/document/123e4567-e89b-12d3-a456-426614174000/tier-1
```

**Response:**

```json
{
  "document_id": "223e4567-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "tier": "tier-1",
  "title": "Handwriting Practice - TIER-1",
  "total_submissions": 3,
  "created_at": "2026-01-27T10:30:00",
  "line_images": [
    {
      "id": "323e4567-e89b-12d3-a456-426614174000",
      "image_path": "lines/handwriting-tier-1-123e4567.../line_0001.png",
      "png_path": "lines/handwriting-tier-1-123e4567.../line_0001.png",
      "text": "විජය රජු",
      "verified": false,
      "created_at": "2026-01-27T10:31:00"
    },
    {
      "id": "423e4567-e89b-12d3-a456-426614174000",
      "image_path": "lines/handwriting-tier-1-123e4567.../line_0002.png",
      "png_path": "lines/handwriting-tier-1-123e4567.../line_0002.png",
      "text": "පණ්ඩුවාසදේව රජු",
      "verified": false,
      "created_at": "2026-01-27T10:32:00"
    }
  ]
}
```

---

### 4. Get Document Submissions

**GET** `/handwriting/submissions/{document_id}`

Get all line image submissions for a specific handwriting document.

**Parameters:**

- `document_id` (path): UUID of the handwriting document

**Example Request:**

```bash
GET /handwriting/submissions/223e4567-e89b-12d3-a456-426614174000
```

**Response:**
Array of LineImageResponse objects with full details.

---

## Database Structure

### Document

Each user gets ONE document per tier (`handwriting-tier-1` or `handwriting-tier-2`) that acts as a container for all their submissions.

**Fields:**

- `id`: UUID
- `original_filename`: "Handwriting Practice - TIER-1"
- `document_type`: `handwriting-tier-1` or `handwriting-tier-2`
- `uploaded_by`: User ID
- `status`: Always "processed"

### Page

Each handwriting document has ONE virtual page to hold line images.

### LineImage

Each submitted handwritten image creates a LineImage record with:

- `image_path`: Path to the submitted image
- `gt_text_path`: Path to `.gt.txt` file with the sentence
- `corrected_text`: The sentence text
- `verified`: Whether the image has been verified

---

## File Storage

```
/handwriting/                           # Handwriting endpoint directory
  └── (empty - metadata only)

/lines/
  └── handwriting-tier-1-{user_id}/    # Tier-1 submissions for user
      ├── line_0001.png                # Handwritten image
      ├── line_0001.gt.txt             # Ground truth text
      ├── line_0002.png
      ├── line_0002.gt.txt
      └── ...

  └── handwriting-tier-2-{user_id}/    # Tier-2 submissions for user
      └── ...

/pages/
  └── handwriting-tier-1-{user_id}/    # Virtual page directory
      └── page_0001.tif
```

---

## Image Verification

To verify the handwritten images exist and are accessible:

```bash
# Check all Tier-1 submissions for a user
ls -la lines/handwriting-tier-1-{user_id}/

# View a submitted image
file lines/handwriting-tier-1-{user_id}/line_0001.png

# Check the ground truth text
cat lines/handwriting-tier-1-{user_id}/line_0001.gt.txt
```

---

## Guest User Behavior

- First submission without authentication creates a guest user account
- Guest email: `guest@handwriting.local`
- Guest role: `guest`
- Subsequent guest submissions use the same account
- All guest submissions accumulate in the guest user's documents

---

## Authentication

- **No auth required** for `/corpus/{tier}` endpoint
- **Optional auth** for `/submit` endpoint (works for both authenticated and guest users)
- **Open access** for `/document/{user_id}/{tier}` to retrieve any user's submissions
- **Open access** for `/submissions/{document_id}` to retrieve any document's submissions

---

## Testing

### Get corpus sentences:

```bash
curl http://localhost:8000/handwriting/corpus/tier-1?limit=3
```

### Submit a test image:

```bash
# Create a simple test image first
curl -X POST "http://localhost:8000/handwriting/submit?tier=tier-1&sentence=test" \
  -F "file=@test_image.png"
```

### Get user's handwriting:

```bash
curl http://localhost:8000/handwriting/document/{user_id}/tier-1
```

---

## Notes

- Images are stored as PNG/JPG/JPEG/WEBP
- Ground truth text is stored in UTF-8 encoded `.gt.txt` files
- Each user has one logical document per tier (even if they submit multiple images)
- Images are validated on submission
- The system uses guest users to allow unauthenticated handwriting practice
