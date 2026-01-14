/**
 * Custom hook for chat functionality
 */
import { useState } from 'react';
import { sendChatMessage } from '@/lib/api/chat';
import { Message } from '@/types/chat';

interface UseChatReturn {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
    sendMessage: (message: string, apiKey: string, topK: number) => Promise<void>;
    clearMessages: () => void;
}

export function useChat(): UseChatReturn {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const sendMessage = async (message: string, apiKey: string, topK: number = 5) => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await sendChatMessage({
                message,
                gemini_api_key: apiKey,
                top_k: topK,
                history: messages,
            });

            // Add the new message pair to the history
            const newMessage: Message = {
                user: message,
                assistant: response.response,
            };

            setMessages((prev) => [...prev, newMessage]);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred while sending the message');
        } finally {
            setIsLoading(false);
        }
    };

    const clearMessages = () => {
        setMessages([]);
        setError(null);
    };

    return {
        messages,
        isLoading,
        error,
        sendMessage,
        clearMessages,
    };
}
