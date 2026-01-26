Implementation Plan: Chat History Feature with Prisma 7 and NeonDB
Overview
Add persistent chat history to ClauseCraft, similar to ChatGPT/Claude, using Prisma 7 and NeonDB PostgreSQL. Users will be able to create conversations, send messages, switch between conversations, and have full persistence across sessions. Single-user mode (no authentication for now).

Architecture Changes
Database Design
NeonDB PostgreSQL for conversation storage
Prisma 7 ORM with new configuration style
Two tables:
Conversation: id, title, created_at, updated_at
Message: id, conversation_id, role (user/assistant), content, metadata, created_at
Key Features
Create new conversations
Auto-generate conversation titles from first message
Persistent message history
Conversation sidebar with list
Switch between conversations
Delete conversations
Auto-save every message
Phase 1: Backend Setup (Prisma 7 + NeonDB)
1.1 Install Prisma Client Python

cd backend
pip install prisma
1.2 Create Prisma Schema
File: /backend/prisma/schema.prisma


generator client {
  provider = "prisma-client-py"
  interface = "asyncio"
}

datasource db {
  provider = "postgresql"
}

model Conversation {
  id        String   @id @default(uuid())
  title     String
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")
  messages  Message[]

  @@map("conversations")
}

model Message {
  id             String   @id @default(uuid())
  role           String
  content        String   @db.Text
  metadata       Json?
  createdAt      DateTime @default(now()) @map("created_at")
  conversationId String   @map("conversation_id")
  conversation   Conversation @relation(fields: [conversationId], references: [id], onDelete: Cascade)

  @@index([conversationId, createdAt])
  @@map("messages")
}
1.3 Configure Prisma 7 (New Style)
File: /backend/prisma.config.ts


import { defineConfig, env } from 'prisma/config'

export default defineConfig({
  schema: 'prisma/schema.prisma',
  datasource: {
    url: env('DATABASE_URL'),
    directUrl: env('DIRECT_URL'),
  },
})
1.4 Environment Variables
Add to: /backend/.env


# NeonDB Connection Strings
DATABASE_URL="postgresql://user:pass@ep-xxx.region.aws.neon.tech/clausecraft?sslmode=require&pgbouncer=true"
DIRECT_URL="postgresql://user:pass@ep-xxx.region.aws.neon.tech/clausecraft?sslmode=require"
Add to: /backend/.env.example


DATABASE_URL="your-neondb-pooled-connection-string-here"
DIRECT_URL="your-neondb-direct-connection-string-here"
1.5 Generate Prisma Client & Run Migrations

cd backend
prisma generate
prisma migrate dev --name init_chat_history
Phase 2: Backend Implementation
2.1 Database Client Singleton
Create: /backend/app/db/__init__.py (empty file)

Create: /backend/app/db/client.py

get_db_client() - Returns Prisma client singleton
disconnect_db() - Cleanup on shutdown
Handles connection lifecycle
2.2 Conversation Service Layer
Create: /backend/app/services/conversation_service.py

Key methods:

create_conversation(title) - Create new conversation
get_conversations(limit) - List all conversations
get_conversation(id) - Get single conversation with messages
delete_conversation(id) - Delete conversation (cascade to messages)
add_message(conversation_id, role, content, metadata) - Add message
get_conversation_history(conversation_id) - Get history in LLM format (tuples)
generate_title_from_message(message) - Auto-generate title (first 50 chars)
2.3 Update Request/Response Models
Update: /backend/app/models/requests.py
Add:

CreateConversationRequest - Optional title
SendMessageRequest - conversation_id, message, gemini_api_key, top_k
Update: /backend/app/models/responses.py
Add:

MessageResponse - id, role, content, metadata, created_at
ConversationListItem - id, title, created_at, updated_at, preview
ConversationDetail - id, title, created_at, updated_at, messages[]
ConversationListResponse - conversations[], total
2.4 New Conversation API Routes
Create: /backend/app/api/routes/conversations.py

Endpoints:

POST /api/conversations/ - Create new conversation
GET /api/conversations/ - List all conversations
GET /api/conversations/{id} - Get conversation with messages
DELETE /api/conversations/{id} - Delete conversation
POST /api/conversations/{id}/messages - Send message in conversation
The messages endpoint:

Loads conversation history from DB
Calls existing generate_chat_response() with history
Saves user message to DB
Saves assistant response to DB
Returns ChatResponse (response, sources_used)
2.5 Update Main App
Update: /backend/app/main.py

Import conversations router
Import DB client functions
Add DB connection to lifespan startup
Add DB disconnection to lifespan shutdown
Include conversations router: app.include_router(conversations.router)
2.6 Update Dependencies
Update: /backend/requirements.txt


prisma>=0.11.0
Phase 3: Frontend Implementation
3.1 Update TypeScript Types
Update: /frontend/types/chat.ts

Add:


export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    metadata?: {
        sources_used?: string[];
        top_k?: number;
    };
    created_at: string;
}

export interface Conversation {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    messages?: Message[];
}

export interface ConversationListItem {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    preview?: string;
}
3.2 Create Conversation API Client
Create: /frontend/lib/api/conversations.ts

Functions:

createConversation(title?) - Create new conversation
getConversations() - List all conversations
getConversation(conversationId) - Get conversation with messages
deleteConversation(conversationId) - Delete conversation
sendMessage(conversationId, message, apiKey, topK) - Send message
3.3 Update useChat Hook
Update: /frontend/lib/hooks/useChat.ts

Changes:

Accept conversationId parameter
Use new Message type (not LegacyMessage)
Call sendMessage from conversations API
Implement optimistic updates (show message immediately)
Handle errors gracefully (remove optimistic message on error)
Add setMessages() for loading conversation history
3.4 Create Conversation Sidebar
Create: /frontend/components/chat/ConversationSidebar.tsx

Features:

"New Conversation" button at top
Scrollable list of conversations
Show title, preview, and date for each conversation
Highlight current conversation
Delete button (appears on hover)
Click to navigate to conversation
Empty state when no conversations
3.5 Update MessageList Component
Update: /frontend/components/chat/MessageList.tsx

Changes:

Use new Message type (not LegacyMessage)
Separate rendering for user vs assistant messages
Display msg.role === 'user' or 'assistant'
Show sources from metadata.sources_used
No functional changes to layout/styling
3.6 Create Dynamic Conversation Page
Create: /frontend/app/chat/[conversationId]/page.tsx

Main conversation page with:

Conversation sidebar (collapsible)
Chat interface (messages + input)
KB stats sidebar
Load conversation on mount
Title in header
Configuration (API key, top-K)
Message list
Chat input
Layout:


[ConversationSidebar] [MainChat] [KBStats]
     3 cols              6 cols     3 cols
3.7 Update Main Chat Page
Update: /frontend/app/chat/page.tsx

Automatically create new conversation
Redirect to /chat/{new-conversation-id}
Show loading state
Phase 4: Critical Files Summary
Must Create (Backend)
/backend/prisma/schema.prisma - Database schema
/backend/prisma.config.ts - Prisma 7 config
/backend/app/db/client.py - DB client singleton
/backend/app/services/conversation_service.py - Business logic
/backend/app/api/routes/conversations.py - API endpoints
Must Create (Frontend)
/frontend/lib/api/conversations.ts - API client
/frontend/components/chat/ConversationSidebar.tsx - Sidebar UI
/frontend/app/chat/[conversationId]/page.tsx - Main conversation page
Must Update (Backend)
/backend/requirements.txt - Add prisma
/backend/.env - Add DATABASE_URL, DIRECT_URL
/backend/app/models/requests.py - Add conversation requests
/backend/app/models/responses.py - Add conversation responses
/backend/app/main.py - DB lifecycle + router
Must Update (Frontend)
/frontend/types/chat.ts - Add new types
/frontend/lib/hooks/useChat.ts - Support conversations
/frontend/components/chat/MessageList.tsx - Use new Message type
/frontend/app/chat/page.tsx - Redirect logic
Phase 5: Important Prisma 7 Notes
Key Changes from Previous Versions
Configuration now in prisma.config.ts (not in schema.prisma)
Must run prisma generate explicitly (no longer automatic)
Need both DATABASE_URL (pooled) and DIRECT_URL (direct) for NeonDB
NeonDB Connection Strings
Get from NeonDB dashboard:

Pooled connection (for app queries): Has ?pgbouncer=true
Direct connection (for migrations): No pgbouncer
Prisma Commands

# Generate client (must run after schema changes)
prisma generate

# Create and apply migration
prisma migrate dev --name migration_name

# Apply migrations in production
prisma migrate deploy

# View database in browser
prisma studio

# Reset database (dev only)
prisma migrate reset
Phase 6: Implementation Order
Setup NeonDB

Create NeonDB account and project
Get connection strings
Add to .env
Backend Database Setup

Install prisma
Create schema
Create config
Generate client
Run migrations
Backend Code

DB client
Service layer
Models
API routes
Update main.py
Frontend Code

Update types
Create API client
Update useChat
Create sidebar
Update MessageList
Create conversation page
Update main chat page
Testing

Test conversation creation
Test message sending
Test conversation switching
Test deletion
Test persistence (page refresh)
Verification Plan
Backend Verification
Start backend: cd backend && uvicorn app.main:app --reload
Check logs for "Database connected successfully!"
Open Prisma Studio: prisma studio (should see tables)
Test endpoints with curl/Postman:
POST /api/conversations/ (creates conversation)
GET /api/conversations/ (lists conversations)
POST /api/conversations/{id}/messages (sends message)
GET /api/conversations/{id} (gets messages)
DELETE /api/conversations/{id} (deletes conversation)
Frontend Verification
Start frontend: cd frontend && npm run dev
Navigate to /chat (should redirect to new conversation)
Verify conversation appears in sidebar
Send a message (should appear immediately)
Refresh page (messages should persist)
Create new conversation (via sidebar button)
Switch between conversations (should load different messages)
Delete conversation (should remove from sidebar)
Integration Testing
Send message with RAG context (should retrieve clauses)
Check sources are displayed
Verify conversation title updates after first message
Test with/without API key
Test error handling (invalid conversation ID, network errors)
Edge Cases to Test
Empty conversations (no messages yet)
Very long messages
Special characters in messages
Rapid message sending
Multiple browser tabs
Database connection failures
Migration Notes
From Current System
Current /api/chat/query endpoint can remain for backward compatibility
New users automatically use conversation system
No data migration needed (current system has no persistence)
Data Flow Changes
Before: React state only (lost on refresh)


User → Frontend State → Backend API → Response → Frontend State
After: Database-backed persistence


User → Optimistic UI Update → Backend API → Save to DB → Response → UI Update
Future Enhancements
Multi-user authentication (add User model)
Conversation search
Export conversations
Better title generation (use LLM)
Conversation folders/tags
Message editing
Regenerate responses
Conversation sharing
Stayed in plan mode