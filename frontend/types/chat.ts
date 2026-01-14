/**
 * Chat and RAG Types
 */

export interface Message {
    user: string;
    assistant: string;
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
    history: Message[];
}

export interface ChatResponse {
    response: string;
    sources_used: string[];
}
