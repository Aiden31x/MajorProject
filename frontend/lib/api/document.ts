/*
 * API client for document analysis endpoints
 */
import axios from 'axios';
import { ClauseHighlightData } from '@/types/document';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Extract clause positions from a PDF file
 * @param file PDF file to analyze
 * @param apiKey Gemini API key
 * @returns ClauseHighlightData with risk assessment and clause positions
 */
export async function extractClausePositions(
    file: File,
    apiKey: string
): Promise<ClauseHighlightData> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('gemini_api_key', apiKey);

    const response = await axios.post<ClauseHighlightData>(
        `${API_BASE_URL}/api/document/extract-clauses`,
        formData,
        {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: 300000, // 5 minutes (risk scoring + clause extraction)
        }
    );

    return response.data;
}
