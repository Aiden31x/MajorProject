/**
 * Main Chat Page - Redirects to new conversation
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import * as conversationsApi from '@/lib/api/conversations';

export default function ChatPage() {
    const router = useRouter();
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const createAndRedirect = async () => {
            try {
                // Create a new conversation
                const conversation = await conversationsApi.createConversation();
                // Redirect to the new conversation page
                router.push(`/chat/${conversation.id}`);
            } catch (err) {
                console.error('Failed to create conversation:', err);
                setError('Failed to create conversation. Please try again.');
            }
        };

        createAndRedirect();
    }, [router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-muted/20">
            <Card className="w-96">
                <CardContent className="pt-6">
                    {error ? (
                        <div className="text-center space-y-4">
                            <p className="text-destructive">{error}</p>
                            <button
                                onClick={() => window.location.reload()}
                                className="text-sm text-primary hover:underline"
                            >
                                Try again
                            </button>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center space-y-4">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                            <p className="text-sm text-muted-foreground">Creating new conversation...</p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
