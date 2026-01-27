# Handwriting System Architecture & Flow Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Handwriting Endpoint System                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼────────┐ ┌────▼────────┐ ┌───▼─────────┐
        │  Corpus Files  │ │   User      │ │   Images    │
        │                │ │  Database   │ │   Storage   │
        ├────────────────┤ ├─────────────┤ ├─────────────┤
        │ tier-1: 1091   │ │ Users       │ │ lines/      │
        │ tier-2: 1751   │ │ Documents   │ │ pages/      │
        └────────────────┘ │ Pages       │ │             │
                           │ LineImages  │ └─────────────┘
                           └─────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
            ┌───────▼────────┐     ┌────────▼───────┐
            │   API Routes   │     │   File System  │
            ├────────────────┤     ├────────────────┤
            │ /corpus/{tier} │     │ Async File I/O │
            │ /submit        │     │ Directory Mgmt │
            │ /document/...  │     │ Path Handling  │
            │ /submissions   │     │ Validation     │
            └────────────────┘     └────────────────┘
```

## Request/Response Flow Diagrams

### 1. Get Corpus Sentences

```
User (Browser/Client)
    │
    └──── GET /handwriting/corpus/tier-1?limit=5
             │
             ▼
    ┌─────────────────────────┐
    │  Load Corpus File       │
    │  corpus-tier-1.txt      │
    └──────────┬──────────────┘
               │
               ▼
    ┌─────────────────────────┐
    │  Select Random Sample   │
    │  (min(limit, len))      │
    └──────────┬──────────────┘
               │
               ▼
    200 OK + JSON Array
    {
      "tier": "tier-1",
      "count": 5,
      "sentences": [...]
    }
```

### 2. Submit Handwriting (Guest User)

```
Guest User (No Auth)
    │
    ├──── POST /handwriting/submit
    │      tier=tier-1
    │      sentence="විජය රජු"
    │      file=handwriting.png
    │
    ▼
┌─────────────────────────────────┐
│ Check/Create Guest User         │
│ (guest@handwriting.local)       │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Get/Create Document             │
│ (handwriting-tier-1-{user_id})  │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Create Virtual Page             │
│ (page_0001)                     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Save Image File                 │
│ lines/.../line_0001.png         │
│                                 │
│ Create GT Text File             │
│ lines/.../line_0001.gt.txt      │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Create LineImage DB Record      │
│ - image_path                    │
│ - gt_text_path                  │
│ - corrected_text                │
│ - verified=false                │
└──────────────┬──────────────────┘
               │
               ▼
200 OK + JSON
{
  "status": "success",
  "line_id": "...",
  "document_id": "..."
}
```

### 3. Get User's Handwriting Document

```
Client
    │
    └──── GET /handwriting/document/{user_id}/tier-1
             │
             ▼
    ┌─────────────────────────┐
    │ Find Document           │
    │ (uploaded_by={user_id}) │
    │ (type=handwriting-tier-1)
    └──────────────┬──────────┘
                   │
                   ▼
    ┌─────────────────────────┐
    │ Get All Pages           │
    │ (typically 1 virtual)   │
    └──────────────┬──────────┘
                   │
                   ▼
    ┌─────────────────────────┐
    │ Get All LineImages      │
    │ for each page           │
    │ (all submissions)       │
    └──────────────┬──────────┘
                   │
                   ▼
    200 OK + JSON
    {
      "document_id": "...",
      "user_id": "...",
      "tier": "tier-1",
      "total_submissions": 3,
      "line_images": [
        {
          "id": "...",
          "image_path": "...",
          "text": "විජය රජු",
          "verified": false
        },
        ...
      ]
    }
```

## Database Entity Relationship

```
┌──────────────┐
│    User      │
├──────────────┤
│ id (UUID)    │
│ name         │
│ email        │
│ role         │
│ is_active    │
└────────┬─────┘
         │ (1:N)
         │ uploaded_by
         │
         ▼
    ┌──────────────────────┐
    │    Document          │
    ├──────────────────────┤
    │ id (UUID)            │
    │ original_filename    │
    │ document_type        │◄─── "handwriting-tier-{1,2}"
    │ status               │◄─── "processed"
    │ total_pages          │◄─── 1 (virtual)
    │ uploaded_by (FK)     │
    └────────┬─────────────┘
             │ (1:N)
             │
             ▼
         ┌──────────┐
         │   Page   │
         ├──────────┤
         │ id (UUID)│
         │ page_num │◄─── 1 (virtual)
         │ status   │
         └────┬─────┘
              │ (1:N)
              │
              ▼
         ┌────────────────┐
         │   LineImage    │
         ├────────────────┤
         │ id (UUID)      │
         │ image_path     │◄─── .png file
         │ gt_text_path   │◄─── .gt.txt file
         │ corrected_text │◄─── sentence
         │ verified       │
         │ is_invalid     │
         └────────────────┘
```

## File System Organization

```
project_root/
│
├── corpus-tier-1.txt        (1091 sentences)
├── corpus-tier-2.txt        (1751 sentences)
│
├── lines/
│   ├── 20242025-OL-History-Past-Paper-Sinhala-Medium/
│   │   └── page_0001/
│   │       ├── line_0001.png
│   │       ├── line_0001.gt.txt
│   │       ├── line_0002.png
│   │       └── line_0002.gt.txt
│   │
│   └── handwriting-tier-1-{user_id}/         (new on first submission)
│       ├── line_0001.png                     (uploaded image)
│       ├── line_0001.gt.txt                  (sentence text)
│       ├── line_0002.png
│       └── line_0002.gt.txt
│
└── pages/
    ├── 20242025-OL-History-Past-Paper-Sinhala-Medium/
    │   ├── page_0001.tif
    │   └── page_0002.tif
    │
    └── handwriting-tier-1-{user_id}/         (new on first submission)
        └── page_0001.tif                     (virtual page)
```

## User Journey

### Guest User - No Authentication

```
Start
  │
  ▼
┌─────────────────────────────────┐
│ 1. Get Sentences                │
│    GET /corpus/tier-1           │
│    No auth needed               │
└──────────────┬──────────────────┘
               │
               ▼
        Display Sentences
        User chooses to write
               │
               ▼
┌─────────────────────────────────┐
│ 2. Write & Submit               │
│    POST /submit                 │
│    - sentence text              │
│    - image file                 │
│    - No auth token required     │
└──────────────┬──────────────────┘
               │
        (First time only)
        ▼
┌─────────────────────────────────┐
│ Auto-create Guest User          │
│ guest@handwriting.local         │
└──────────────┬──────────────────┘
               │
               ▼
        Create Document
        (handwriting-tier-1)
               │
               ▼
        Save image & text
               │
               ▼
┌─────────────────────────────────┐
│ 3. View Progress                │
│    GET /document/{user_id}/     │
│    tier-1                       │
└──────────────┬──────────────────┘
               │
               ▼
        Show all submissions
        in one document
               │
               ▼
             End
```

### Authenticated User

```
Start
  │
  │ POST /login
  │ (get JWT token)
  ▼
┌─────────────────────────────────┐
│ 1. Get Sentences                │
│    GET /corpus/tier-1           │
│    No auth needed               │
└──────────────┬──────────────────┘
               │
               ▼
        Display Sentences
               │
               ▼
┌─────────────────────────────────┐
│ 2. Submit with Auth             │
│    POST /submit                 │
│    Header: Authorization: Bearer
│    {token}                      │
└──────────────┬──────────────────┘
               │
        (First time only)
        ▼
        Create Document
        (with authenticated user)
               │
               ▼
        Save image & text
               │
               ▼
        Return document ID
               │
               ▼
┌─────────────────────────────────┐
│ 3. View Personal Progress       │
│    GET /document/{own_id}/      │
│    tier-1                       │
└──────────────┬──────────────────┘
               │
               ▼
        Show personalized
        submissions
               │
               ▼
             End
```

## Data Flow Summary

```
┌─────────────────────────────────────────────────────┐
│              Request Arrives                        │
└─────────────────────────────────┬───────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ Validate Request           │
                    │ - Check tier              │
                    │ - Check file type         │
                    └──────────┬─────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Authenticate (opt)   │
                    │ - Get current_user   │
                    │ - Create guest if no │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Database Operations  │
                    │ - Create/Get Doc     │
                    │ - Create Page        │
                    │ - Create LineImage   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ File Operations      │
                    │ - Save image         │
                    │ - Save GT text       │
                    │ - Create dirs        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Return Response      │
                    │ - Status: 200/400    │
                    │ - JSON data          │
                    └──────────────────────┘
```

## Error Handling Flow

```
Request
  │
  ▼
┌──────────────────┐
│ Validation       │
└────┬─────────────┘
     │
     ├─ Invalid tier? ──→ 400 Bad Request
     │
     ├─ Missing file? ──→ 422 Unprocessable
     │
     ├─ Invalid format? ─→ 400 Bad Request
     │
     └─ OK? Continue ──→
              │
              ▼
        ┌─────────────┐
        │ Processing  │
        └────┬────────┘
             │
             ├─ File save error? ──→ 500 Internal
             │
             ├─ DB error? ─────────→ 500 Internal
             │
             └─ Success ──────────→ 200 OK
```

## Performance Characteristics

### Request Time (Estimated)

- **Corpus fetch**: 10-50ms (file read + random selection)
- **Submit handwriting**: 50-200ms (file I/O + DB insert)
- **Get document**: 20-100ms (DB query + assembly)

### Storage Usage

- **Corpus files**: ~50 KB total
- **Image file**: ~100 KB - 1 MB per submission
- **GT text file**: < 1 KB per submission
- **Database overhead**: < 1 KB per submission

### Scaling Considerations

- File operations async (non-blocking)
- Database queries indexed on user_id and document_type
- No in-memory caching (scalable for multiple instances)
- Static file serving via FastAPI mount

---

This architecture supports:
✓ Multiple concurrent users
✓ Guest and authenticated access
✓ Large number of submissions
✓ Future expansion (export, analytics, etc.)
