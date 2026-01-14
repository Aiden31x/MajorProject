/**
 * Message List Component
 */
'use client';

import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message } from '@/types/chat';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';

interface MessageListProps {
    messages: Message[];
    isLoading?: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    return (
        <ScrollArea className="h-[500px] pr-4">
            <div className="space-y-4">
                {messages.map((msg, index) => (
                    <div key={index} className="space-y-2">
                        {/* User Message */}
                        <div className="flex justify-end">
                            <Card className="max-w-[80%] bg-primary text-primary-foreground p-3">
                                <p className="text-sm">{msg.user}</p>
                            </Card>
                        </div>

                        {/* Assistant Message */}
                        <div className="flex justify-start">
                            <Card className="max-w-[80%] bg-muted p-3">
                                <div className="prose prose-sm dark:prose-invert max-w-none">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.assistant}
                                    </ReactMarkdown>
                                </div>
                            </Card>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <Card className="max-w-[80%] bg-muted p-3">
                            <Skeleton className="h-4 w-64 mb-2" />
                            <Skeleton className="h-4 w-48" />
                        </Card>
                    </div>
                )}

                <div ref={bottomRef} />
            </div>
        </ScrollArea>
    );
}
