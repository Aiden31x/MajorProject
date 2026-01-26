/**
 * API Routes: /api/conversations/[id]
 * Handles individual conversation operations
 */

import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/db/prisma';

// GET /api/conversations/[id] - Get conversation with messages
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        const conversation = await prisma.conversation.findUnique({
            where: { id },
            include: {
                messages: {
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

        // Format response
        const formattedConversation = {
            id: conversation.id,
            title: conversation.title,
            createdAt: conversation.createdAt.toISOString(),
            updatedAt: conversation.updatedAt.toISOString(),
            messages: conversation.messages.map((msg) => ({
                id: msg.id,
                role: msg.role,
                content: msg.content,
                metadata: msg.metadata,
                createdAt: msg.createdAt.toISOString(),
            })),
        };

        return NextResponse.json(formattedConversation);
    } catch (error) {
        console.error('Error fetching conversation:', error);
        return NextResponse.json(
            { error: 'Failed to fetch conversation' },
            { status: 500 }
        );
    }
}

// DELETE /api/conversations/[id] - Delete conversation
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        await prisma.conversation.delete({
            where: { id },
        });

        return NextResponse.json({ success: true, message: 'Conversation deleted' });
    } catch (error) {
        console.error('Error deleting conversation:', error);
        return NextResponse.json(
            { error: 'Failed to delete conversation' },
            { status: 500 }
        );
    }
}
