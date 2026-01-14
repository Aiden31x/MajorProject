/**
 * Chat and Knowledge Base API Functions
 */
import { apiClient } from './client';
import { ChatRequest, ChatResponse, KBStatistics } from '@/types/chat';

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/api/chat/query', request);
    return response.data;
}

export async function getKBStatistics(): Promise<KBStatistics> {
    const response = await apiClient.get<KBStatistics>('/api/kb/stats');
    return response.data;
}
