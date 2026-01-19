/**
 * Chat/RAG Query Page
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { MessageList } from '@/components/chat/MessageList';
import { KBStatsSidebar } from '@/components/chat/KBStatsSidebar';
import { useChat } from '@/lib/hooks/useChat';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, MessageSquare, AlertCircle, Sparkles } from 'lucide-react';

export default function ChatPage() {
    const [apiKey, setApiKey] = useState('');
    const [topK, setTopK] = useState(5);
    const { messages, isLoading, error, sendMessage, clearMessages } = useChat();

    const handleSendMessage = async (message: string) => {
        await sendMessage(message, apiKey || '', topK); // Use empty string if no API key provided (backend will use its own)
    };

    const exampleQueries = [
        "What are common red flags in lease agreements?",
        "Show me examples of unfair rent escalation clauses",
        "What should I look for in notice period clauses?",
        "Are there any concerning VAT-related clauses?",
        "What are typical lease extension terms?",
    ];

    return (
        <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
            {/* Header */}
            <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Link href="/">
                                <Button variant="ghost" size="icon">
                                    <ArrowLeft className="w-5 h-5" />
                                </Button>
                            </Link>
                            <MessageSquare className="w-8 h-8 text-primary" />
                            <div>
                                <h1 className="text-2xl font-bold">Query Knowledge Base</h1>
                                <p className="text-sm text-muted-foreground">Ask questions about your lease agreements</p>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="container mx-auto px-4 py-8 max-w-7xl">
                {/* Hero Section */}
                <div className="text-center space-y-4 py-4 mb-6">
                    <Badge variant="secondary" className="gap-1">
                        <Sparkles className="w-3 h-3" />
                        RAG-Powered Conversational AI
                    </Badge>
                    <h2 className="text-3xl font-bold tracking-tight">
                        Ask Questions About Your Lease Agreements
                    </h2>
                    <p className="text-muted-foreground max-w-2xl mx-auto">
                        Query the knowledge base containing all processed lease agreements stored page-by-page.
                        Get conversational, context-aware answers powered by AI.
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    {/* Main Chat Area */}
                    <div className="lg:col-span-3 space-y-6">
                        {/* Configuration */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Configuration</CardTitle>
                                <CardDescription>API key is optional (server uses configured key by default)</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <label htmlFor="chat-api-key" className="text-sm font-medium block mb-2">
                                        🔑 Gemini API Key <span className="text-muted-foreground font-normal">(Optional)</span>
                                    </label>
                                    <Input
                                        id="chat-api-key"
                                        type="password"
                                        placeholder="Leave empty to use server's API key"
                                        value={apiKey}
                                        onChange={(e) => setApiKey(e.target.value)}
                                    />
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Leave empty to use server's configured key or provide your own from{' '}
                                        <a
                                            href="https://aistudio.google.com/app/apikey"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-primary hover:underline"
                                        >
                                            Google AI Studio
                                        </a>
                                    </p>
                                </div>

                                <div>
                                    <label htmlFor="top-k" className="text-sm font-medium block mb-2">
                                        Number of relevant documents to retrieve: <strong>{topK}</strong>
                                    </label>
                                    <input
                                        id="top-k"
                                        type="range"
                                        min="3"
                                        max="10"
                                        value={topK}
                                        onChange={(e) => setTopK(Number(e.target.value))}
                                        className="w-full"
                                    />
                                    <p className="text-xs text-muted-foreground mt-1">
                                        More documents = better context but slower responses
                                    </p>
                                </div>

                                {messages.length > 0 && (
                                    <Button
                                        variant="outline"
                                        onClick={clearMessages}
                                        className="w-full"
                                    >
                                        Clear Conversation
                                    </Button>
                                )}
                            </CardContent>
                        </Card>

                        {/* Chat Messages */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Conversation</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {messages.length === 0 && !error ? (
                                    <div className="text-center py-12 space-y-4">
                                        <MessageSquare className="w-12 h-12 mx-auto text-muted-foreground" />
                                        <div>
                                            <p className="text-lg font-medium">No messages yet</p>
                                            <p className="text-sm text-muted-foreground">
                                                Start a conversation by typing a question below
                                            </p>
                                        </div>
                                    </div>
                                ) : (
                                    <MessageList messages={messages} isLoading={isLoading} />
                                )}

                                {error && (
                                    <Alert variant="destructive" className="mt-4">
                                        <AlertCircle className="h-4 w-4" />
                                        <AlertDescription>{error}</AlertDescription>
                                    </Alert>
                                )}
                            </CardContent>
                        </Card>

                        {/* Chat Input */}
                        <ChatInterface
                            onSendMessage={handleSendMessage}
                            isLoading={isLoading}
                            disabled={!apiKey}
                        />

                        {/* Example Queries */}
                        {messages.length === 0 && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>💡 Example Questions</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-1 gap-2">
                                        {exampleQueries.map((query, index) => (
                                            <Button
                                                key={index}
                                                variant="outline"
                                                className="justify-start text-left h-auto py-3"
                                                onClick={() => apiKey && handleSendMessage(query)}
                                                disabled={!apiKey}
                                            >
                                                {query}
                                            </Button>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Tips */}
                        <Card>
                            <CardHeader>
                                <CardTitle>💡 Tips</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm text-muted-foreground">
                                <ul className="list-disc list-inside space-y-1">
                                    <li>Ask follow-up questions - the assistant remembers conversation context</li>
                                    <li>Be specific about what you want to know</li>
                                    <li>Questions can be about specific clause types or general patterns</li>
                                    <li>The system searches across all stored lease clauses</li>
                                </ul>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Sidebar */}
                    <div className="lg:col-span-1">
                        <KBStatsSidebar />
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t mt-16 py-6 bg-muted/50">
                <div className="container max-w-7xl px-4 text-center text-sm text-muted-foreground">
                    <p>
                        ClauseCraft v2.0 • Powered by Next.js, FastAPI, Google Gemini & ChromaDB
                    </p>
                </div>
            </footer>
        </div>
    );
}
