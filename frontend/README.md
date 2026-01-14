# ClauseCraft Frontend

Modern Next.js 14 frontend for ClauseCraft lease agreement analyzer.

## Features

- 📄 **PDF Analysis** - Upload and analyze lease agreements with AI
- 💬 **RAG Chat** - Query your knowledge base with conversational search
- 🎨 **Beautiful UI** - Built with shadcn/ui and Tailwind CSS
- ⚡ **Fast** - Powered by Next.js 14 with App Router
- 📱 **Responsive** - Works on all devices

## Setup

1. **Install dependencies**:
```bash
npm install
```

2. **Configure environment**:
```bash
# .env.local is already created with defaults
# Edit if your backend runs on a different port
```

3. **Run development server**:
```bash
npm run dev
```

The app will be available at http://localhost:3000

## Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # PDF analysis page
│   ├── chat/
│   │   └── page.tsx          # Chat interface page
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── components/
│   ├── ui/                   # shadcn/ui components
│   ├── pdf/                  # PDF-related components
│   │   ├── PDFUploader.tsx
│   │   └── AnalysisResults.tsx
│   └── chat/                 # Chat-related components
│       ├── ChatInterface.tsx
│       ├── MessageList.tsx
│       └── KBStatsSidebar.tsx
├── lib/
│   ├── api/                  # API client functions
│   │   ├── client.ts
│   │   ├── pdf.ts
│   │   └── chat.ts
│   ├── hooks/                # Custom React hooks
│   │   ├── usePDFAnalysis.ts
│   │   └── useChat.ts
│   └── utils.ts              # Utility functions
└── types/                    # TypeScript type definitions
    ├── pdf.ts
    └── chat.ts
```

## Technologies

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Beautiful, accessible UI components
- **Axios** - HTTP client for API calls
- **React Markdown** - Markdown rendering for AI responses
- **Lucide React** - Beautiful icon library

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000` by default.

All API calls are handled through the `lib/api/` directory:
- `client.ts` - Axios instance with error handling
- `pdf.ts` - PDF analysis endpoints
- `chat.ts` - Chat and KB statistics endpoints

## Environment Variables

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL (default: http://localhost:8000)

## Development Tips

- The app uses **server components** by default for better performance
- Interactive components are marked with `'use client'`
- API calls use custom hooks for state management
- All components are fully typed with TypeScript

## Troubleshooting

**Backend connection errors**: Make sure the FastAPI backend is running on port 8000.

**Build errors**: Try deleting `.next` folder and running `npm run dev` again.

**Type errors**: Run `npm run build` to check for TypeScript errors.
