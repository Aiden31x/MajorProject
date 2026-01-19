/**
 * Analysis Results Component with markdown rendering
 */
'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface AnalysisResultsProps {
    title: string;
    content: string;
}

export function AnalysisResults({ title, content }: AnalysisResultsProps) {
    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle className="flex items-center justify-between">
                    <span>{title}</span>
                    <span className="text-xs font-normal text-muted-foreground">
                        {content.length.toLocaleString()} characters
                    </span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <ScrollArea className="h-[600px] pr-4">
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {content}
                        </ReactMarkdown>
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
