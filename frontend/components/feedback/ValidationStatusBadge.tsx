/**
 * ValidationStatusBadge Component
 * 
 * Displays visual indicator for validation status (PASS/WARN/FAIL)
 */

import React from 'react';
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

interface ValidationStatusBadgeProps {
    status: 'PASS' | 'WARN' | 'FAIL';
    confidence: number;
}

export function ValidationStatusBadge({ status, confidence }: ValidationStatusBadgeProps) {
    const confidencePercentage = Math.round(confidence * 100);

    const statusConfig = {
        PASS: {
            icon: CheckCircle,
            bgColor: 'bg-green-50',
            textColor: 'text-green-700',
            borderColor: 'border-green-200',
            label: 'Passed Validation',
        },
        WARN: {
            icon: AlertTriangle,
            bgColor: 'bg-yellow-50',
            textColor: 'text-yellow-700',
            borderColor: 'border-yellow-200',
            label: 'Warning',
        },
        FAIL: {
            icon: XCircle,
            bgColor: 'bg-red-50',
            textColor: 'text-red-700',
            borderColor: 'border-red-200',
            label: 'Failed Validation',
        },
    };

    const config = statusConfig[status];
    const Icon = config.icon;

    return (
        <div
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${config.bgColor} ${config.borderColor}`}
        >
            <Icon className={`w-5 h-5 ${config.textColor}`} />
            <div className="flex-1">
                <div className={`text-sm font-semibold ${config.textColor}`}>
                    {config.label}
                </div>
                <div className={`text-xs ${config.textColor} opacity-75`}>
                    Confidence: {confidencePercentage}%
                </div>
            </div>
        </div>
    );
}
