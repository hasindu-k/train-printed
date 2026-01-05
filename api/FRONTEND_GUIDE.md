# Next Steps - Frontend Development Guide

Now that you have a complete **FastAPI backend**, here's how to build a **Next.js frontend**.

## 📋 Recommended Next.js Frontend Features

### 1️⃣ Document Upload Page
```
- Drag & drop PDF upload
- Upload progress indicator
- Display uploaded documents list
```

### 2️⃣ Processing Pipeline
```
- Show PDF → TIFF conversion progress
- Show line extraction progress
- Show GT file creation status
```

### 3️⃣ Line Labeling Interface
```
- Display line image
- Show auto-detected text (if any)
- Text input for correction
- Verify/Unverify buttons
- Navigation: Next/Previous line
```

### 4️⃣ Verification Dashboard
```
- Show unverified lines count
- Filter by page, status, assigned reviewer
- Bulk operations (verify multiple)
- Statistics/progress charts
```

### 5️⃣ Dataset Management
```
- List documents with progress
- Export dataset button
- Download ZIP files
- Delete documents
```

### 6️⃣ User Management
```
- User registration/login
- Assign reviewers to lines
- Show user roles (admin, reviewer, annotator)
```

## 🛠️ Frontend Tech Stack Recommendation

```
- Framework: Next.js 14+ (with App Router)
- UI Library: Shadcn/ui + Tailwind CSS
- State Management: Zustand or TanStack Query
- Image Viewing: react-image-gallery or similar
- File Upload: react-dropzone
- HTTP Client: axios or fetch API
- Charts: recharts (for statistics)
- Forms: react-hook-form
```

## 📁 Suggested Next.js Folder Structure

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx (home)
│   ├── upload/
│   │   └── page.tsx (PDF upload)
│   ├── documents/
│   │   ├── page.tsx (document list)
│   │   └── [id]/
│   │       ├── page.tsx (document detail)
│   │       ├── pages/
│   │       │   └── page.tsx (pages list)
│   │       └── label/
│   │           └── page.tsx (line labeling)
│   ├── verify/
│   │   └── page.tsx (verification dashboard)
│   ├── users/
│   │   └── page.tsx (user management)
│   └── api/
│       └── ... (optional: API routes)
├── components/
│   ├── DocumentUpload.tsx
│   ├── LineLabeler.tsx
│   ├── DocumentList.tsx
│   ├── VerificationDashboard.tsx
│   └── ...
├── hooks/
│   ├── useDocuments.ts
│   ├── useLines.ts
│   ├── useUsers.ts
│   └── ...
├── lib/
│   ├── api.ts (API client)
│   ├── axios-config.ts
│   └── types.ts
├── public/
│   └── ... (images, icons)
├── styles/
│   └── globals.css
├── .env.local
├── next.config.ts
├── tailwind.config.ts
└── package.json
```

## 🔗 API Integration Examples

### Fetching Documents
```typescript
// lib/api.ts
import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  }
});

export const documentsAPI = {
  list: () => API.get('/documents'),
  get: (id: string) => API.get(`/documents/${id}`),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return API.post('/documents/upload', formData);
  },
  convertPages: (id: string) => API.post(`/documents/${id}/convert-pages`),
  getPages: (id: string) => API.get(`/documents/${id}/pages`),
  extractLines: (docId: string, pageId: string) => 
    API.post(`/documents/${docId}/pages/${pageId}/extract-lines`),
  getLines: (id: string, filters?: {}) => 
    API.get(`/documents/${id}/lines`, { params: filters }),
  export: (id: string) => API.get(`/documents/${id}/export`),
};

export const linesAPI = {
  get: (id: string) => API.get(`/lines/${id}`),
  correctText: (id: string, text: string) => 
    API.put(`/lines/${id}/corrected-text`, { corrected_text: text }),
  verify: (id: string) => API.put(`/lines/${id}/verify`),
  unverify: (id: string) => API.put(`/lines/${id}/unverify`),
};
```

### React Hook for Documents
```typescript
// hooks/useDocuments.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { documentsAPI } from '@/lib/api';

export const useDocuments = () => {
  return useQuery({
    queryKey: ['documents'],
    queryFn: documentsAPI.list,
  });
};

export const useUploadDocument = () => {
  return useMutation({
    mutationFn: (file: File) => documentsAPI.upload(file),
  });
};

export const useConvertPages = () => {
  return useMutation({
    mutationFn: (docId: string) => documentsAPI.convertPages(docId),
  });
};
```

### Line Labeler Component
```typescript
// components/LineLabeler.tsx
'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { linesAPI } from '@/lib/api';

export default function LineLabeler({ lineId }: { lineId: string }) {
  const [correction, setCorrection] = useState('');
  
  const { data: line } = useQuery({
    queryKey: ['line', lineId],
    queryFn: () => linesAPI.get(lineId),
  });
  
  const saveCorrection = useMutation({
    mutationFn: () => linesAPI.correctText(lineId, correction),
    onSuccess: () => {
      setCorrection('');
      // Refetch line data
    }
  });
  
  const verify = useMutation({
    mutationFn: () => linesAPI.verify(lineId),
  });
  
  return (
    <div className="p-4 max-w-2xl">
      {/* Display line image */}
      <img 
        src={line?.image_url} 
        alt="Line" 
        className="mb-4 max-h-32"
      />
      
      {/* Display auto text */}
      <div className="mb-4 p-2 bg-gray-100 rounded">
        <p className="text-sm text-gray-600">Auto-detected:</p>
        <p>{line?.auto_text || 'No text detected'}</p>
      </div>
      
      {/* Correction input */}
      <textarea
        value={correction}
        onChange={(e) => setCorrection(e.target.value)}
        placeholder="Enter corrected text"
        className="w-full p-2 border rounded mb-4"
      />
      
      {/* Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => saveCorrection.mutate()}
          disabled={saveCorrection.isPending}
          className="px-4 py-2 bg-blue-500 text-white rounded"
        >
          Save Correction
        </button>
        
        <button
          onClick={() => verify.mutate()}
          disabled={verify.isPending}
          className="px-4 py-2 bg-green-500 text-white rounded"
        >
          Verify
        </button>
      </div>
    </div>
  );
}
```

## 📦 Setup New Next.js Project

```bash
# Create new Next.js app
npx create-next-app@latest frontend --typescript --tailwind

cd frontend

# Install additional dependencies
npm install @tanstack/react-query axios zustand
npm install shadcn-ui
npx shadcn-ui@latest init

# Install UI components
npx shadcn-ui@latest add button input card dialog
```

## 🚀 Backend Requirements for Frontend

Your current API already provides:
- ✅ PDF upload
- ✅ Document listing
- ✅ Page retrieval
- ✅ Line image serving
- ✅ Line correction
- ✅ Verification workflow
- ✅ Export functionality
- ✅ CORS enabled (allows frontend requests)

## 🔐 Future Security Enhancements

For production frontend, add to backend:

1. **JWT Authentication**
   ```python
   # In app/auth.py
   from fastapi_jwt_extended import JWTManager
   ```

2. **Protect Endpoints**
   ```python
   @router.post("/lines/{id}/verify")
   def verify_line(id: UUID, current_user: User = Depends(get_current_user)):
       # Only reviewers/admins can verify
       if current_user.role not in ["reviewer", "admin"]:
           raise HTTPException(status_code=403)
   ```

3. **CORS Configuration**
   ```python
   # Update in main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

## 🧪 Testing Frontend with Backend

```bash
# Terminal 1: Backend
cd api
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Access at http://localhost:3000
```

## 📚 Frontend Development Checklist

- [ ] Create Next.js project
- [ ] Setup API client (axios/fetch)
- [ ] Create document upload page
- [ ] Create document list page
- [ ] Create line labeling interface
- [ ] Create verification dashboard
- [ ] Add user authentication
- [ ] Add error handling
- [ ] Add loading states
- [ ] Add success notifications
- [ ] Test all workflows
- [ ] Deploy both frontend and backend

## 🎯 Key Integration Points

1. **Form Submissions** → POST/PUT to API
2. **Data Fetching** → GET from API  
3. **File Uploads** → FormData to POST /documents/upload
4. **Real-time Updates** → React Query or polling
5. **Error Handling** → Display API error messages
6. **Authentication** → Store JWT, add to headers

## 💡 Pro Tips

1. Use React Query for caching and refetching
2. Add loading skeletons while fetching
3. Show progress bars during conversions
4. Use optimistic updates for better UX
5. Add keyboard shortcuts for power users
6. Implement undo/redo for corrections
7. Add bulk operations (verify multiple lines)
8. Show statistics dashboard

---

**Your backend is ready! Start building the frontend now! 🚀**
