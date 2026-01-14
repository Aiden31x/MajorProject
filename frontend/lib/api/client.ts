/**
 * API Client Configuration
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 120000, // 2 minutes for PDF processing
    headers: {
        'Content-Type': 'application/json',
    },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            // Server responded with error
            const errorMessage = error.response.data?.message || error.response.data?.detail || 'An error occurred';
            throw new Error(errorMessage);
        } else if (error.request) {
            // Request made but no response
            throw new Error('No response from server. Please check if the backend is running.');
        } else {
            // Something else happened
            throw new Error(error.message);
        }
    }
);
