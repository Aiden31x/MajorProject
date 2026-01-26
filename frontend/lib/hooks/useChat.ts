/**
 * Custom hook for chat functionality with conversation support
 */
import { useState, useCallback } from 'react';
import { Message } from '@/types/chat';
import * as conversationsApi from '@/lib/api/conversations';

interface UseChatReturn {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
    sendMessage: (message: string, apiKey: string, topK: number) => Promise<void>;
    setMessages: (messages: Message[]) => void;
    clearMessages: () => void;
}

export function useChat(conversationId?: string): UseChatReturn {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const sendMessage = useCallback(async (message: string, apiKey: string, topK: number = 5) => {
        if (!conversationId) {
            setError('No conversation selected');
            return;
        }

        setIsLoading(true);
        setError(null);

        // Optimistic update - add user message immediately
        const optimisticUserMessage: Message = {
            id: `temp-${Date.now()}`,
            role: 'user',
            content: message,
            createdAt: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, optimisticUserMessage]);

        try {
            const response = await conversationsApi.sendMessage(conversationId, {
                message,
                gemini_api_key: apiKey,
                top_k: topK,
            });

            // Replace optimistic message and add assistant response
            setMessages((prev) => {
                // Remove the optimistic message
                const withoutOptimistic = prev.filter((m) => m.id !== optimisticUserMessage.id);

                // Add the actual user message (saved in DB) and assistant response
                return [
                    ...withoutOptimistic,
                    {
                        id: `user-${Date.now()}`,
                        role: 'user' as const,
                        content: message,
                        createdAt: new Date().toISOString(),
                    },
                    {
                        id: response.messageId,
                        role: 'assistant' as const,
                        content: response.response,
                        metadata: {
                            sources_used: response.sources_used,
                            top_k: topK,
                        },
                        createdAt: new Date().toISOString(),
                    },
                ];
            });
        } catch (err) {
            // Remove optimistic message on error
            setMessages((prev) => prev.filter((m) => m.id !== optimisticUserMessage.id));
            setError(err instanceof Error ? err.message : 'An error occurred while sending the message');
        } finally {
            setIsLoading(false);
        }
    }, [conversationId]);

    const clearMessages = useCallback(() => {
        setMessages([]);
        setError(null);
    }, []);

    return {
        messages,
        isLoading,
        error,
        sendMessage,
        setMessages,
        clearMessages,
    };
}
