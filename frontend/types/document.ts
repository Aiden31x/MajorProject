/*
 * TypeScript interfaces for document analysis with clause highlighting
 */
import { ValidationResult } from './validation';

export interface ClausePosition {
    clause_text: string;
    page_number: number;
    start_char: number;
    end_char: number;
    risk_score: number;
    risk_severity: string;
    risk_category: string;
    risk_explanation: string;
    recommended_action: string;
    confidence: number;
    validation_result?: ValidationResult;  // NEW: Optional validation result
    bounding_box?: {
        x: number;
        y: number;
        width: number;
        height: number;
    };
}

export interface PDFMetadata {
    total_pages: number;
    file_size: number;
    filename: string;
}

export interface ClauseHighlightData {
    risk_assessment: any; // Risk assessment data (matches backend structure)
    clause_positions: ClausePosition[];
    pdf_metadata: PDFMetadata;
    pdf_base64: string;
}

// Helper type: clauses grouped by page number
export type ClausesByPage = Record<number, ClausePosition[]>;
