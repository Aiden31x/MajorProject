/**
 * PDF Uploader Component with drag-and-drop
 */
'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, FileText } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface PDFUploaderProps {
    file: File | null;
    onFileSelect: (file: File | null) => void;
    disabled?: boolean;
}

export function PDFUploader({ file, onFileSelect, disabled }: PDFUploaderProps) {
    const onDrop = useCallback(
        (acceptedFiles: File[]) => {
            if (acceptedFiles && acceptedFiles.length > 0) {
                onFileSelect(acceptedFiles[0]);
            }
        },
        [onFileSelect]
    );

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
        },
        multiple: false,
        disabled,
    });

    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    return (
        <Card className="p-6">
            {!file ? (
                <div
                    {...getRootProps()}
                    className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
            transition-colors duration-200
            ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
                >
                    <input {...getInputProps()} />
                    <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-lg font-medium mb-2">
                        {isDragActive ? 'Drop your PDF here' : 'Drag & drop a PDF file'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                        or click to browse
                    </p>
                </div>
            ) : (
                <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-3">
                        <FileText className="w-10 h-10 text-primary" />
                        <div>
                            <p className="font-medium">{file.name}</p>
                            <p className="text-sm text-muted-foreground">
                                {formatFileSize(file.size)}
                            </p>
                        </div>
                    </div>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onFileSelect(null)}
                        disabled={disabled}
                    >
                        <X className="w-4 h-4" />
                    </Button>
                </div>
            )}
        </Card>
    );
}
