# Image Verification Guide

## Existing Images Verified ✓

The handwriting system can access the following verified image directories and files:

### 1. Pages Directory

```
pages/
├── 20242025-OL-History-Past-Paper-Sinhala-Medium/
│   ├── page_0001.tif (26.1 MB)
│   ├── page_0002.tif (26.1 MB)
│   ├── page_0003.tif (26.1 MB)
│   ├── page_0004.tif (26.1 MB)
│   ├── page_0005.tif (26.1 MB)
│   ├── page_0006.tif (26.1 MB)
│   ├── page_0007.tif (26.1 MB)
│   ├── page_0008.tif (26.1 MB)
│   ├── page_0009.tif (26.1 MB)
│   └── page_0010.tif (27.5 MB)
│
├── 3ddc6c52-35a0-4a74-acb7-e17e32ae6b1e_Sample Text Book Grade 6-1-lesson/
│   ├── page_0001.tif (25.2 MB)
│   └── page_0002.tif (25.2 MB)
│
├── bb1a8fb49ce448b9b2d62ca52cca5929/
│   └── page_0001.tif (254 KB)
│
└── history 10 S first-lesson/
    ├── page_0001.tif (25.2 MB)
    ├── page_0002.tif (25.2 MB)
    ├── page_0003.tif (25.2 MB)
    ├── page_0004.tif (25.2 MB)
    ├── page_0005.tif (25.2 MB)
    ├── page_0006.tif (25.2 MB)
    └── page_0007.tif (25.2 MB)
```

### 2. Lines Directory (Extracted Line Images)

```
lines/
└── 20242025-OL-History-Past-Paper-Sinhala-Medium/
    └── page_0001/
        ├── line_0001.png (4.7 KB)
        ├── line_0001.tif (414 KB)
        ├── line_0001.gt.txt (0 bytes - empty)
        ├── line_0002.png (790 KB)
        ├── line_0002.tif (7.0 MB)
        ├── line_0003.gt.txt (6 bytes)
        ├── line_0003.png (3.4 KB)
        ├── line_0003.tif (16 KB)
        ├── line_0004.gt.txt (20 bytes)
        ├── line_0004.png (5.2 KB)
        ├── line_0004.tif (20 KB)
        ├── line_0005.gt.txt (134 bytes)
        ├── line_0005.png (4.5 KB)
        ├── line_0005.tif (15 KB)
        ├── line_10.gt.txt
        └── ... (many more line images)
```

## File Format Details

### TIF/TIFF Files

- **Purpose**: Original high-quality scanned page/line images
- **Color Space**: Typically grayscale or RGB
- **Resolution**: High DPI (usually 300+ DPI for OCR)
- **Size**: Varies from 15 KB to 27.5 MB depending on page complexity

### PNG Files

- **Purpose**: Browser-compatible preview of line images
- **Color Space**: Typically RGB or RGBA
- **Resolution**: Web-optimized
- **Size**: Smaller than TIF files (3-800 KB)

### GT.txt Files (Ground Truth)

- **Purpose**: Contains the correct text transcription for the line image
- **Format**: UTF-8 encoded plain text
- **Content**: Sinhala text or empty if not yet transcribed
- **Examples**:
  - `line_0001.gt.txt` → (empty)
  - `line_0003.gt.txt` → Contains transcribed text
  - `line_0004.gt.txt` → Contains transcribed text

## Image Accessibility

### For Handwriting Submission

When users submit handwriting through the API:

1. **Upload**: Image → `lines/handwriting-tier-1-{user_id}/line_XXXX.{ext}`
2. **Store GT**: Text → `lines/handwriting-tier-1-{user_id}/line_XXXX.gt.txt`
3. **Database**: LineImage record created with paths

### For Retrieval

Images are served through the FastAPI static file mount:

```
/lines/<document_name>/<page>/<line_image_files>
/pages/<document_name>/<page_image_files>
```

## Verification Commands

### Check Pages Directory Size

```powershell
Get-ChildItem -Path "c:\github\train-printed\api\pages" -Recurse | Measure-Object -Property Length -Sum
```

### Count All Line Images

```powershell
Get-ChildItem -Path "c:\github\train-printed\api\lines" -Recurse -Filter "*.png" | Measure-Object
Get-ChildItem -Path "c:\github\train-printed\api\lines" -Recurse -Filter "*.tif" | Measure-Object
Get-ChildItem -Path "c:\github\train-printed\api\lines" -Recurse -Filter "*.gt.txt" | Measure-Object
```

### View a Specific GT File

```powershell
Get-Content "c:\github\train-printed\api\lines\20242025-OL-History-Past-Paper-Sinhala-Medium\page_0001\line_0003.gt.txt" -Encoding UTF8
```

### List All Transcribed Lines (Non-empty GT Files)

```powershell
Get-ChildItem -Path "c:\github\train-printed\api\lines" -Recurse -Filter "*.gt.txt" |
  Where-Object { (Get-Content $_.FullName -Encoding UTF8 -Raw).Length -gt 0 } |
  Select-Object FullName, @{N="Size";E={$_.Length}}
```

## Database Integration

When handwriting submissions are made, the system:

1. ✓ Creates a Document record with:
   - `document_type = "handwriting-tier-1"` or `"handwriting-tier-2"`
   - `uploaded_by = {user_id}`
   - `status = "processed"`

2. ✓ Creates a Page record (virtual page per document)

3. ✓ Creates LineImage record with:
   - `image_path` → Points to PNG/JPG/etc
   - `gt_text_path` → Points to `.gt.txt` file
   - `corrected_text` → Stores the sentence
   - `verified = false` (can be marked as verified later)

4. ✓ Files are stored in:
   - Images: `lines/handwriting-{tier}-{user_id}/line_XXXX.{ext}`
   - GT Text: `lines/handwriting-{tier}-{user_id}/line_XXXX.gt.txt`

## Image Format Support

### Accepted Formats

- PNG ✓
- JPG/JPEG ✓
- WEBP ✓
- GIF ✗ (not supported)
- BMP ✗ (not supported)

### File Size Recommendations

- **Minimum**: 100x50 pixels (very small text)
- **Optimal**: 300x100 pixels to 2000x200 pixels
- **Maximum**: 10 MB per file (validation in place)

## Notes

- All line images are properly extracted and categorized
- GT files contain ground truth for transcription verification
- The system handles both authenticated users and guest submissions
- Images are accessible both through database records and static file mounting
- The corpus files (tier-1, tier-2) are ready for sentence selection
