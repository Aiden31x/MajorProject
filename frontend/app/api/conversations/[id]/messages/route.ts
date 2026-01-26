/**
 * API Routes: /api/conversations/[id]/messages
 * Handles sending messages within a conversation
 */

import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/db/prisma';
import { LegacyMessage } from '@/types/chat';

// POST /api/conversations/[id]/messages - Send message in conversation
export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id: conversationId } = await params;
        const body = await request.json();
        const { message, gemini_api_key, top_k = 5 } = body;

        // 1. Save user message to database
        const userMessage = await prisma.message.create({
            data: {
                conversationId,
                role: 'user',
                content: message,
                metadata: { top_k },
            },
        });

        // 2. Load conversation history from database
        const conversation = await prisma.conversation.findUnique({
            where: { id: conversationId },
            include: {
                messages: {
                    where: {
                        createdAt: {
                            lt: userMessage.createdAt, // Get messages before the current one
                        },
                    },
                    orderBy: {
                        createdAt: 'asc',
                    },
                },
            },
        });

        if (!conversation) {
            return NextResponse.json(
                { error: 'Conversation not found' },
                { status: 404 }
            );
        }

        // 3. Format history for FastAPI backend (legacy format)
        const history: LegacyMessage[] = [];
        for (let i = 0; i < conversation.messages.length; i += 2) {
            const userMsg = conversation.messages[i];
            const assistantMsg = conversation.messages[i + 1];
            if (userMsg && assistantMsg) {
                history.push({
                    user: userMsg.content,
                    assistant: assistantMsg.content,
                });
            }
        }

        // 4. Call FastAPI backend for RAG processing
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/api/chat/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                gemini_api_key,
                top_k,
                history,
            }),
        });

        if (!response.ok) {
            throw new Error(`Backend API error: ${response.statusText}`);
        }

        const chatResponse = await response.json();

        // 5. Save assistant response to database
        const assistantMessage = await prisma.message.create({
            data: {
                conversationId,
                role: 'assistant',
                content: chatResponse.response,
                metadata: {
                    sources_used: chatResponse.sources_used || [],
                    top_k,
                },
            },
        });

        // 6. Update conversation title if it's the first message
        if (conversation.messages.length === 0) {
            const title = message.length > 50
                ? message.substring(0, 50) + '...'
                : message;
            await prisma.conversation.update({
                where: { id: conversationId },
                data: { title },
            });
        }

        // 7. Return response
        return NextResponse.json({
            response: chatResponse.response,
            sources_used: chatResponse.sources_used || [],
            messageId: assistantMessage.id,
        });
    } catch (error) {
        console.error('Error sending message:', error);
        return NextResponse.json(
            { error: 'Failed to send message' },
            { status: 500 }
        );
    }
}
