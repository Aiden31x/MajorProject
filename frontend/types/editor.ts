/**
 * Editor-specific TypeScript types for TipTap document editor
 */

export interface EditorClausePosition {
    id: string;
    clause_text: string;
    absolute_start: number;
    absolute_end: number;
    page_number: number;
    risk_score: number;
    risk_severity: 'High' | 'Medium' | 'Low';
    risk_category: string;
    risk_explanation: string;
    recommended_action: string;
    confidence: number;
}

export interface PDFMetadata {
    total_pages: number;
    file_size: number;
    filename: string;
}

export interface EditorDocumentResponse {
    full_text: string;
    clause_positions: EditorClausePosition[];
    page_boundaries: number[];
    risk_assessment: Record<string, any>;
    pdf_metadata: PDFMetadata;
}

export interface EditorNegotiationState {
    selectedClause: EditorClausePosition | null;
    isLoadingSuggestions: boolean;
    suggestions: NegotiationRound[] | null;
    error: string | null;
}

export interface NegotiationRound {
    round_number: number;
    counter_clause: string;
    justification: string;
    risk_reduction: number;
    rejection_text?: string;
}
