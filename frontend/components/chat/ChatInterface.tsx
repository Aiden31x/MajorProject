/**
 * Chat Interface Component
 */
'use client';

import { useState, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';

interface ChatInterfaceProps {
    onSendMessage: (message: string) => void;
    isLoading: boolean;
    disabled?: boolean;
}

export function ChatInterface({ onSendMessage, isLoading, disabled }: ChatInterfaceProps) {
    const [message, setMessage] = useState('');

    const handleSend = () => {
        if (message.trim() && !isLoading && !disabled) {
            onSendMessage(message);
            setMessage('');
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <Card className="p-4">
            <div className="flex gap-2">
                <Textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask me anything about lease clauses..."
                    disabled={isLoading || disabled}
                    className="min-h-[60px]"
                />
                <Button
                    onClick={handleSend}
                    disabled={!message.trim() || isLoading || disabled}
                    size="icon"
                    className="h-[60px]"
                >
                    <Send className="w-4 h-4" />
                </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
                Press Enter to send, Shift+Enter for new line
            </p>
        </Card>
    );
}
