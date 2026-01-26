/**
 * Conversation Sidebar Component
 * Displays list of conversations with create, select, and delete functionality
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Plus, Trash2, MessageSquare } from 'lucide-react';
import { ConversationListItem } from '@/types/chat';
import * as conversationsApi from '@/lib/api/conversations';
import { formatDistanceToNow } from 'date-fns';

interface ConversationSidebarProps {
    currentConversationId?: string;
}

export function ConversationSidebar({ currentConversationId }: ConversationSidebarProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [conversations, setConversations] = useState<ConversationListItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [conversationToDelete, setConversationToDelete] = useState<string | null>(null);

    const loadConversations = async () => {
        try {
            setIsLoading(true);
            const data = await conversationsApi.getConversations();
            setConversations(data.conversations);
        } catch (error) {
            console.error('Failed to load conversations:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadConversations();
    }, []);

    const handleCreateConversation = async () => {
        try {
            const newConv = await conversationsApi.createConversation();
            router.push(`/chat/${newConv.id}`);
            loadConversations(); // Refresh list
        } catch (error) {
            console.error('Failed to create conversation:', error);
        }
    };

    const handleSelectConversation = (id: string) => {
        router.push(`/chat/${id}`);
    };

    const handleDeleteClick = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setConversationToDelete(id);
        setDeleteDialogOpen(true);
    };

    const handleConfirmDelete = async () => {
        if (!conversationToDelete) return;

        try {
            await conversationsApi.deleteConversation(conversationToDelete);

            // If deleting current conversation, navigate to create new one
            if (conversationToDelete === currentConversationId) {
                router.push('/chat');
            }

            loadConversations(); // Refresh list
        } catch (error) {
            console.error('Failed to delete conversation:', error);
        } finally {
            setDeleteDialogOpen(false);
            setConversationToDelete(null);
        }
    };

    return (
        <>
            <div className="flex flex-col h-full border-r bg-muted/10">
                {/* Header with New Conversation Button */}
                <div className="p-4 border-b">
                    <Button
                        onClick={handleCreateConversation}
                        className="w-full"
                        size="sm"
                    >
                        <Plus className="mr-2 h-4 w-4" />
                        New Conversation
                    </Button>
                </div>

                {/* Conversations List */}
                <ScrollArea className="flex-1">
                    <div className="p-2 space-y-2">
                        {isLoading ? (
                            // Loading skeletons
                            Array.from({ length: 5 }).map((_, i) => (
                                <Skeleton key={i} className="h-20 w-full" />
                            ))
                        ) : conversations.length === 0 ? (
                            // Empty state
                            <div className="flex flex-col items-center justify-center py-8 text-center">
                                <MessageSquare className="h-12 w-12 text-muted-foreground mb-2" />
                                <p className="text-sm text-muted-foreground">
                                    No conversations yet
                                </p>
                                <p className="text-xs text-muted-foreground mt-1">
                                    Click "New Conversation" to start
                                </p>
                            </div>
                        ) : (
                            // Conversation list
                            conversations.map((conv) => (
                                <Card
                                    key={conv.id}
                                    className={`p-3 cursor-pointer hover:bg-accent transition-colors group relative ${conv.id === currentConversationId ? 'bg-accent border-primary' : ''
                                        }`}
                                    onClick={() => handleSelectConversation(conv.id)}
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <h4 className="text-sm font-medium truncate mb-1">
                                                {conv.title}
                                            </h4>
                                            {conv.preview && (
                                                <p className="text-xs text-muted-foreground truncate">
                                                    {conv.preview}
                                                </p>
                                            )}
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {formatDistanceToNow(new Date(conv.updatedAt), { addSuffix: true })}
                                            </p>
                                        </div>

                                        {/* Delete button (visible on hover) */}
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                                            onClick={(e) => handleDeleteClick(conv.id, e)}
                                        >
                                            <Trash2 className="h-3 w-3" />
                                        </Button>
                                    </div>
                                </Card>
                            ))
                        )}
                    </div>
                </ScrollArea>
            </div>

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Conversation</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete this conversation? This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={handleConfirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}
