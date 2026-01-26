/**
 * Chat and RAG Types
 */

// Legacy message format (kept for backward compatibility)
export interface LegacyMessage {
    user: string;
    assistant: string;
}

// New persistent message format
export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    metadata?: {
        sources_used?: string[];
        top_k?: number;
    };
    createdAt: string;
}

export interface Conversation {
    id: string;
    title: string;
    createdAt: string;
    updatedAt: string;
    messages?: Message[];
}

export interface ConversationListItem {
    id: string;
    title: string;
    createdAt: string;
    updatedAt: string;
    preview?: string;
}

export interface ChatState {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
}

export interface KBStatistics {
    total_clauses: number;
    red_flags_count: number;
    collection_name: string;
    status: string;
}

export interface ChatRequest {
    message: string;
    gemini_api_key: string;
    top_k: number;
    history: LegacyMessage[];
}

export interface ChatResponse {
    response: string;
    sources_used: string[];
}

