"use client";

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ClausePosition, ClauseHighlightData } from '@/types/document';
import { EditorDocumentResponse, EditorClausePosition } from '@/types/editor';
import { PDFViewerWithHighlights } from '@/components/document/PDFViewerWithHighlights';
import { ClauseRiskSummary } from '@/components/document/ClauseRiskSummary';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { DocumentTextEditor, DocumentTextEditorRef } from '@/components/editor/DocumentTextEditor';
import { EditorNegotiationPanel } from '@/components/editor/EditorNegotiationPanel';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, ArrowLeft, Loader2, FileText, BookOpen } from 'lucide-react';
import { extractClausePositions } from '@/lib/api/document';
import { extractForEditor } from '@/lib/api/editor';
import { sendChatMessage } from '@/lib/api/chat';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

export default function DocumentAnalysisPage() {
    const router = useRouter();
    const editorRef = useRef<DocumentTextEditorRef>(null);

    const [pdfFile, setPdfFile] = useState<File | null>(null);
    const [apiKey, setApiKey] = useState<string>('');
    const [viewMode, setViewMode] = useState<'pdf' | 'editor'>('pdf');

    // PDF View state
    const [analysis, setAnalysis] = useState<ClauseHighlightData | null>(null);
    const [selectedClauses, setSelectedClauses] = useState<ClausePosition[] | null>(null);
    const [selectedPageNumber, setSelectedPageNumber] = useState<number | undefined>();

    // Editor View state
    const [editorData, setEditorData] = useState<EditorDocumentResponse | null>(null);
    const [selectedEditorClause, setSelectedEditorClause] = useState<EditorClausePosition | null>(null);

    // Track accepted clauses (by clause text for matching across views)
    const [acceptedClauses, setAcceptedClauses] = useState<Set<string>>(new Set());

    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analyzeError, setAnalyzeError] = useState<string | null>(null);

    // Chat state
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [isChatLoading, setIsChatLoading] = useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file && file.type === 'application/pdf') {
            setPdfFile(file);
            setAnalysis(null);
            setEditorData(null);
            setSelectedClauses(null);
            setSelectedEditorClause(null);
            setAnalyzeError(null);
            setAcceptedClauses(new Set()); // Reset accepted clauses
        }
    };

    const handleAnalyze = async () => {
        if (!pdfFile || !apiKey) {
            setAnalyzeError('Please upload a PDF and provide an API key');
            return;
        }

        setIsAnalyzing(true);
        setAnalyzeError(null);

        try {
            // Fetch both PDF view and Editor view data
            const [pdfResult, editorResult] = await Promise.all([
                extractClausePositions(pdfFile, apiKey),
                extractForEditor(pdfFile, apiKey),
            ]);

            setAnalysis(pdfResult);
            setEditorData(editorResult);
        } catch (error: any) {
            console.error('Analysis error:', error);
            setAnalyzeError(error.response?.data?.detail || error.message || 'Failed to analyze PDF');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleClauseClick = (clause: ClausePosition) => {
        // Find all clauses on the same page
        if (analysis?.clause_positions) {
            const clausesOnPage = analysis.clause_positions.filter(
                c => c.page_number === clause.page_number
            );
            setSelectedClauses(clausesOnPage);
            setSelectedPageNumber(clause.page_number);
        }
    };

    const handlePageClick = (pageNum: number) => {
        if (analysis?.clause_positions) {
            const clausesOnPage = analysis.clause_positions.filter(
                c => c.page_number === pageNum
            );
            setSelectedClauses(clausesOnPage);
            setSelectedPageNumber(pageNum);
        }
    };

    const handleSendMessage = async (message: string) => {
        if (!apiKey) return;

        // Add user message
        const userMessage: ChatMessage = { role: 'user', content: message };
        setChatMessages(prev => [...prev, userMessage]);
        setIsChatLoading(true);

        try {
            // Optionally include clause context in the query
            let contextualMessage = message;
            if (selectedClauses && selectedClauses.length > 0) {
                const clauseContext = selectedClauses.map(c =>
                    `[${c.risk_category}] ${c.clause_text}`
                ).join('\n');
                contextualMessage = `Context: The user is viewing these risky clauses:\n${clauseContext}\n\nUser question: ${message}`;
            }

            const response = await sendChatMessage({
                message: contextualMessage,
                gemini_api_key: apiKey,
                top_k: 5,
                history: chatMessages.map(m => ({
                    user: m.role === 'user' ? m.content : '',
                    assistant: m.role === 'assistant' ? m.content : ''
                })).filter(h => h.user || h.assistant)
            });

            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: response.response
            };
            setChatMessages(prev => [...prev, assistantMessage]);
        } catch (error: any) {
            console.error('Chat error:', error);
            const errorMessage: ChatMessage = {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.'
            };
            setChatMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsChatLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-background">
            {/* Header */}
            <header className="border-b p-4">
                <div className="container mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => router.push('/')}
                        >
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            Back
                        </Button>
                        <h1 className="text-2xl font-bold">Document Analysis</h1>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {!analysis || !editorData ? (
                    /* Upload Section */
                    <div className="flex-1 flex items-center justify-center p-8">
                        <Card className="w-full max-w-2xl">
                            <CardHeader>
                                <CardTitle>Upload PDF for Analysis</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-2">
                                        Gemini API Key
                                    </label>
                                    <Input
                                        type="password"
                                        placeholder="Enter your Gemini API key"
                                        value={apiKey}
                                        onChange={(e) => setApiKey(e.target.value)}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-2">
                                        PDF File
                                    </label>
                                    <div className="border-2 border-dashed rounded-lg p-8 text-center">
                                        <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                                        <Input
                                            type="file"
                                            accept=".pdf"
                                            onChange={handleFileChange}
                                            className="max-w-xs mx-auto"
                                        />
                                        {pdfFile && (
                                            <p className="mt-2 text-sm text-muted-foreground">
                                                Selected: {pdfFile.name}
                                            </p>
                                        )}
                                    </div>
                                </div>

                                {analyzeError && (
                                    <div className="bg-destructive/10 text-destructive p-3 rounded">
                                        {analyzeError}
                                    </div>
                                )}

                                <Button
                                    onClick={handleAnalyze}
                                    disabled={!pdfFile || !apiKey || isAnalyzing}
                                    className="w-full"
                                    size="lg"
                                >
                                    {isAnalyzing ? (
                                        <>
                                            <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                                            Analyzing... (may take 1-2 minutes)
                                        </>
                                    ) : (
                                        <>
                                            <Upload className="h-5 w-5 mr-2" />
                                            Analyze Document
                                        </>
                                    )}
                                </Button>
                            </CardContent>
                        </Card>
                    </div>
                ) : (
                    /* Tabbed View */
                    <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'pdf' | 'editor')} className="flex-1 flex flex-col">
                        {/* Tab Headers */}
                        <div className="border-b px-4">
                            <TabsList>
                                <TabsTrigger value="pdf" className="flex items-center gap-2">
                                    <FileText className="h-4 w-4" />
                                    PDF View
                                </TabsTrigger>
                                <TabsTrigger value="editor" className="flex items-center gap-2">
                                    <BookOpen className="h-4 w-4" />
                                    Editor View
                                </TabsTrigger>
                            </TabsList>
                        </div>

                        {/* PDF View Tab */}
                        <TabsContent value="pdf" className="flex-1 flex m-0 overflow-hidden">
                            <>
                                {/* Left Panel: PDF Viewer */}
                                <div className="w-3/5 border-r flex flex-col overflow-hidden">
                                    <PDFViewerWithHighlights
                                        pdfFile={pdfFile}
                                        pdfBase64={analysis.pdf_base64}
                                        clausePositions={analysis.clause_positions}
                                        onClauseClick={handleClauseClick}
                                        onPageClick={handlePageClick}
                                    />
                                </div>

                                {/* Right Panel: Clause Summary + Chat */}
                                <div className="w-2/5 flex flex-col overflow-hidden">
                                    {/* Clause Risk Summary - Scrollable */}
                                    <div className="flex-1 overflow-auto border-b">
                                        <ClauseRiskSummary
                                            selectedClauses={selectedClauses}
                                            pageNumber={selectedPageNumber}
                                            acceptedClauses={acceptedClauses}
                                        />
                                    </div>

                                    {/* Chat Interface */}
                                    <div className="flex-1 flex flex-col p-4 overflow-hidden">
                                        <h3 className="text-lg font-semibold mb-4">
                                            Ask Questions About the Document
                                        </h3>

                                        {/* Chat Messages */}
                                        <ScrollArea className="flex-1 mb-4 border rounded-lg p-4 bg-slate-50">
                                            {chatMessages.length === 0 ? (
                                                <div className="text-center text-muted-foreground py-8">
                                                    <p>No messages yet. Ask a question about the document!</p>
                                                    {selectedClauses && selectedClauses.length > 0 && (
                                                        <p className="mt-2 text-sm">
                                                            Currently viewing {selectedClauses.length} clause(s) from page {selectedPageNumber}
                                                        </p>
                                                    )}
                                                </div>
                                            ) : (
                                                <div className="space-y-4">
                                                    {chatMessages.map((msg, idx) => (
                                                        <div
                                                            key={idx}
                                                            className={`p-3 rounded-lg ${msg.role === 'user'
                                                                ? 'bg-blue-100 ml-12'
                                                                : 'bg-white border mr-12'
                                                                }`}
                                                        >
                                                            <p className="text-sm font-semibold mb-1">
                                                                {msg.role === 'user' ? 'You' : 'Assistant'}
                                                            </p>
                                                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                                                        </div>
                                                    ))}
                                                    {isChatLoading && (
                                                        <div className="bg-white border mr-12 p-3 rounded-lg">
                                                            <Loader2 className="h-4 w-4 animate-spin" />
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </ScrollArea>

                                        {/* Chat Input */}
                                        <ChatInterface
                                            onSendMessage={handleSendMessage}
                                            isLoading={isChatLoading}
                                            disabled={!apiKey}
                                        />
                                    </div>
                                </div>
                            </>
                        </TabsContent>

                        {/* Editor View Tab */}
                        <TabsContent value="editor" className="flex-1 flex m-0 overflow-hidden">
                            <>
                                {/* Left Panel: TipTap Editor */}
                                <div className="w-3/5 border-r p-4 flex flex-col overflow-hidden">
                                    <DocumentTextEditor
                                        ref={editorRef}
                                        fullText={editorData.full_text}
                                        clausePositions={editorData.clause_positions}
                                        onClauseClick={(clause) => setSelectedEditorClause(clause)}
                                    />
                                </div>

                                {/* Right Panel: Negotiation Panel */}
                                <div className="w-2/5 overflow-hidden">
                                    <EditorNegotiationPanel
                                        selectedClause={selectedEditorClause}
                                        apiKey={apiKey}
                                        onAcceptSuggestion={(newText) => {
                                            if (selectedEditorClause) {
                                                editorRef.current?.replaceClauseText(selectedEditorClause.id, newText);

                                                // Track accepted clause for PDF view indicators
                                                setAcceptedClauses(prev => {
                                                    const updated = new Set(prev);
                                                    updated.add(selectedEditorClause.clause_text);
                                                    return updated;
                                                });

                                                setSelectedEditorClause(null);
                                            }
                                        }}
                                    />
                                </div>
                            </>
                        </TabsContent>
                    </Tabs>
                )}
            </div>
        </div>
    );
}
