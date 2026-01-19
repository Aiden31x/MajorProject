"use client";

import { useState, useMemo } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ClausePosition, ClausesByPage } from '@/types/document';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker - use unpkg CDN as fallback
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFViewerWithHighlightsProps {
    pdfFile: File | null;
    pdfBase64?: string;
    clausePositions?: ClausePosition[];
    onClauseClick: (clause: ClausePosition) => void;
    onPageClick?: (pageNum: number) => void;
}

export function PDFViewerWithHighlights({
    pdfFile,
    pdfBase64,
    clausePositions = [],
    onClauseClick,
    onPageClick
}: PDFViewerWithHighlightsProps) {
    const [numPages, setNumPages] = useState(0);
    const [pageNumber, setPageNumber] = useState(1);
    const [loading, setLoading] = useState(true);

    // Group clauses by page for efficient rendering
    const clausesByPage: ClausesByPage = useMemo(() => {
        const grouped: ClausesByPage = {};
        clausePositions.forEach(clause => {
            const pageNum = clause.page_number;
            if (!grouped[pageNum]) {
                grouped[pageNum] = [];
            }
            grouped[pageNum].push(clause);
        });
        return grouped;
    }, [clausePositions]);

    // Get page risk level (highest risk on page)
    const getPageRiskLevel = (pageNum: number): { severity: string; score: number; count: number } => {
        const clauses = clausesByPage[pageNum];
        if (!clauses || clauses.length === 0) {
            return { severity: 'Low', score: 0, count: 0 };
        }

        const maxScore = Math.max(...clauses.map(c => c.risk_score));
        let severity = 'Low';
        if (maxScore >= 70) severity = 'High';
        else if (maxScore >= 40) severity = 'Medium';

        return { severity, score: maxScore, count: clauses.length };
    };

    const getHighlightColor = (severity: string) => {
        switch (severity) {
            case 'High':
                return 'rgba(239, 68, 68, 0.2)'; // red with transparency
            case 'Medium':
                return 'rgba(234, 179, 8, 0.2)'; // yellow/amber
            case 'Low':
                return 'rgba(34, 197, 94, 0.2)'; // green
            default:
                return 'transparent';
        }
    };

    const getBorderColor = (severity: string) => {
        switch (severity) {
            case 'High':
                return 'rgb(239, 68, 68)';
            case 'Medium':
                return 'rgb(234, 179, 8)';
            case 'Low':
                return 'rgb(34, 197, 94)';
            default:
                return 'transparent';
        }
    };

    const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
        setNumPages(numPages);
        setLoading(false);
    };

    const currentPageRisk = getPageRiskLevel(pageNumber);
    const hasRisksOnPage = currentPageRisk.count > 0;

    // Prepare PDF data
    const pdfData = useMemo(() => {
        if (pdfBase64) {
            // Convert base64 to data URL
            return `data:application/pdf;base64,${pdfBase64}`;
        }
        return pdfFile;
    }, [pdfFile, pdfBase64]);

    if (!pdfData) {
        return (
            <Card className="flex items-center justify-center h-full p-8">
                <div className="text-center text-muted-foreground">
                    <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No PDF file loaded</p>
                </div>
            </Card>
        );
    }

    return (
        <div className="flex flex-col h-full bg-slate-50">
            {/* PDF Document Display */}
            <div className="flex-1 overflow-auto relative">
                <div className="flex justify-center py-4">
                    <div className="relative">
                        <Document
                            file={pdfData}
                            onLoadSuccess={onDocumentLoadSuccess}
                            loading={
                                <div className="flex items-center justify-center p-12">
                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                                </div>
                            }
                            error={
                                <Card className="p-8 text-center">
                                    <AlertCircle className="h-12 w-12 mx-auto mb-4 text-destructive" />
                                    <p className="text-destructive">Error loading PDF</p>
                                </Card>
                            }
                        >
                            <div className="relative">
                                <Page
                                    pageNumber={pageNumber}
                                    renderTextLayer={true}
                                    renderAnnotationLayer={false}
                                    className="shadow-lg"
                                />

                                {/* Page-level highlight overlay */}
                                {hasRisksOnPage && (
                                    <div
                                        className="absolute inset-0 pointer-events-none border-4 rounded"
                                        style={{
                                            backgroundColor: getHighlightColor(currentPageRisk.severity),
                                            borderColor: getBorderColor(currentPageRisk.severity),
                                        }}
                                    />
                                )}
                            </div>
                        </Document>

                        {/* Page Risk Badge */}
                        {hasRisksOnPage && (
                            <div className="absolute top-4 right-4 pointer-events-auto">
                                <Badge
                                    variant={
                                        currentPageRisk.severity === 'High'
                                            ? 'destructive'
                                            : currentPageRisk.severity === 'Medium'
                                                ? 'default'
                                                : 'secondary'
                                    }
                                    className="text-sm font-semibold"
                                >
                                    {currentPageRisk.count} Risk{currentPageRisk.count !== 1 ? 's' : ''} Found
                                </Badge>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Navigation Controls */}
            <Card className="border-t rounded-none p-4">
                <div className="flex items-center justify-between max-w-4xl mx-auto">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPageNumber(p => Math.max(1, p - 1))}
                        disabled={pageNumber <= 1 || loading}
                    >
                        <ChevronLeft className="h-4 w-4 mr-1" />
                        Previous
                    </Button>

                    <div className="flex items-center gap-4">
                        <span className="text-sm text-muted-foreground">
                            Page {pageNumber} of {numPages || '...'}
                        </span>

                        {hasRisksOnPage && (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                    // Click the first clause on this page
                                    const clauses = clausesByPage[pageNumber];
                                    if (clauses && clauses.length > 0) {
                                        onClauseClick(clauses[0]);
                                    }
                                    onPageClick?.(pageNumber);
                                }}
                            >
                                View Risks
                            </Button>
                        )}
                    </div>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}
                        disabled={pageNumber >= numPages || loading}
                    >
                        Next
                        <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                </div>

                {/* Quick jump to risky pages */}
                {Object.keys(clausesByPage).length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                        <p className="text-xs text-muted-foreground mb-2">Jump to risky pages:</p>
                        <div className="flex flex-wrap gap-2">
                            {Object.keys(clausesByPage)
                                .map(Number)
                                .sort((a, b) => a - b)
                                .map(page => {
                                    const risk = getPageRiskLevel(page);
                                    return (
                                        <Button
                                            key={page}
                                            variant={pageNumber === page ? 'default' : 'outline'}
                                            size="sm"
                                            onClick={() => setPageNumber(page)}
                                            className="text-xs"
                                        >
                                            <Badge
                                                variant={
                                                    risk.severity === 'High'
                                                        ? 'destructive'
                                                        : risk.severity === 'Medium'
                                                            ? 'default'
                                                            : 'secondary'
                                                }
                                                className="mr-1 h-4 w-4 p-0 flex items-center justify-center"
                                            >
                                                {risk.count}
                                            </Badge>
                                            Page {page}
                                        </Button>
                                    );
                                })}
                        </div>
                    </div>
                )}
            </Card>
        </div>
    );
}
