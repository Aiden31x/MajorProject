/**
 * API Routes: /api/conversations
 * Handles conversation creation and listing
 */

import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/db/prisma';

// POST /api/conversations - Create new conversation
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { title } = body;

        // Generate title from first message or use default
        const conversationTitle = title || `New Conversation - ${new Date().toLocaleDateString()}`;

        const conversation = await prisma.conversation.create({
            data: {
                title: conversationTitle,
            },
        });

        return NextResponse.json(conversation, { status: 201 });
    } catch (error) {
        console.error('Error creating conversation:', error);
        return NextResponse.json(
            { error: 'Failed to create conversation' },
            { status: 500 }
        );
    }
}

// GET /api/conversations - List all conversations
export async function GET() {
    try {
        const conversations = await prisma.conversation.findMany({
            orderBy: {
                updatedAt: 'desc',
            },
            include: {
                messages: {
                    take: 1,
                    orderBy: {
                        createdAt: 'asc',
                    },
                    select: {
                        content: true,
                        role: true,
                    },
                },
            },
        });

        // Format response with preview
        const conversationsWithPreview = conversations.map((conv) => ({
            id: conv.id,
            title: conv.title,
            createdAt: conv.createdAt.toISOString(),
            updatedAt: conv.updatedAt.toISOString(),
            preview: conv.messages[0]?.content.substring(0, 100) || '',
        }));

        return NextResponse.json({
            conversations: conversationsWithPreview,
            total: conversations.length,
        });
    } catch (error) {
        console.error('Error fetching conversations:', error);
        return NextResponse.json(
            { error: 'Failed to fetch conversations' },
            { status: 500 }
        );
    }
}
