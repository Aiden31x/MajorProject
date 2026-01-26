/**
 * Conversation API Client
 * Communicates with Next.js API routes for conversation management
 */

import { Conversation, ConversationListItem, Message } from '@/types/chat';

const API_BASE = ''; // Empty string uses same origin (Next.js app)

export interface CreateConversationRequest {
    title?: string;
}

export interface SendMessageRequest {
    message: string;
    gemini_api_key: string;
    top_k?: number;
}

export interface SendMessageResponse {
    response: string;
    sources_used: string[];
    messageId: string;
}

/**
 * Create a new conversation
 */
export async function createConversation(
    title?: string
): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/api/conversations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
    });

    if (!response.ok) {
        throw new Error('Failed to create conversation');
    }

    return response.json();
}

/**
 * Get all conversations
 */
export async function getConversations(): Promise<{
    conversations: ConversationListItem[];
    total: number;
}> {
    const response = await fetch(`${API_BASE}/api/conversations`);

    if (!response.ok) {
        throw new Error('Failed to fetch conversations');
    }

    return response.json();
}

/**
 * Get a single conversation with all messages
 */
export async function getConversation(
    conversationId: string
): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/api/conversations/${conversationId}`);

    if (!response.ok) {
        throw new Error('Failed to fetch conversation');
    }

    return response.json();
}

/**
 * Delete a conversation
 */
export async function deleteConversation(
    conversationId: string
): Promise<void> {
    const response = await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        throw new Error('Failed to delete conversation');
    }
}

/**
 * Send a message in a conversation
 */
export async function sendMessage(
    conversationId: string,
    request: SendMessageRequest
): Promise<SendMessageResponse> {
    const response = await fetch(
        `${API_BASE}/api/conversations/${conversationId}/messages`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        }
    );

    if (!response.ok) {
        throw new Error('Failed to send message');
    }

    return response.json();
}
