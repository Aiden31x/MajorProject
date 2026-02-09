/**
 * Editor API client functions
 */
import axios from 'axios';
import { EditorDocumentResponse } from '@/types/editor';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Extract PDF and transform to editor format with absolute positions
 */
export async function extractForEditor(
    file: File,
    apiKey: string
): Promise<EditorDocumentResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('gemini_api_key', apiKey);

    const response = await axios.post<EditorDocumentResponse>(
        `${API_BASE_URL}/api/editor/extract-for-editor`,
        formData,
        {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: 600000, // 10 minutes for analysis
        }
    );

    return response.data;
}

/**
 * Re-analyze edited text from the editor
 */
export async function reanalyzeText(
    text: string,
    apiKey: string
): Promise<EditorDocumentResponse> {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('gemini_api_key', apiKey);

    const response = await axios.post<EditorDocumentResponse>(
        `${API_BASE_URL}/api/editor/reanalyze-text`,
        formData,
        {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: 600000, // 10 minutes for re-analysis
        }
    );

    return response.data;
}
