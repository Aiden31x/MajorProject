/**
 * PDF Analysis Types
 */

export interface PDFAnalysisResult {
    classification_results: string;
    analysis_results: string;
    pages_processed: number;
    total_characters: number;
    source_document: string;
    stored_in_kb: boolean;
    total_kb_count: number;
}

export interface AnalysisState {
    isAnalyzing: boolean;
    progress: number;
    error: string | null;
    result: PDFAnalysisResult | null;
}
