/**
 * ValidationIssuesList Component
 * 
 * Displays list of validation issues grouped by severity
 */

import React, { useState } from 'react';
import { AlertOctagon, AlertTriangle, Info, ChevronDown, ChevronRight } from 'lucide-react';
import { ValidationIssue } from '@/types/validation';

interface ValidationIssuesListProps {
    issues: ValidationIssue[];
}

export function ValidationIssuesList({ issues }: ValidationIssuesListProps) {
    const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set());

    if (issues.length === 0) {
        return null;
    }

    // Group issues by severity
    const criticalIssues = issues.filter((i) => i.severity === 'critical');
    const majorIssues = issues.filter((i) => i.severity === 'major');
    const minorIssues = issues.filter((i) => i.severity === 'minor');

    const toggleIssue = (index: number) => {
        const newExpanded = new Set(expandedIssues);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedIssues(newExpanded);
    };

    const renderIssueGroup = (
        groupIssues: ValidationIssue[],
        severity: 'critical' | 'major' | 'minor',
        Icon: React.ElementType,
        colorClass: string
    ) => {
        if (groupIssues.length === 0) return null;

        return (
            <div className="space-y-2">
                <div className={`text-xs font-semibold ${colorClass} uppercase tracking-wide`}>
                    {severity} Issues ({groupIssues.length})
                </div>
                {groupIssues.map((issue, index) => {
                    const globalIndex = issues.indexOf(issue);
                    const isExpanded = expandedIssues.has(globalIndex);

                    return (
                        <div
                            key={globalIndex}
                            className={`border rounded-md ${severity === 'critical'
                                    ? 'border-red-200 bg-red-50'
                                    : severity === 'major'
                                        ? 'border-yellow-200 bg-yellow-50'
                                        : 'border-blue-200 bg-blue-50'
                                }`}
                        >
                            <button
                                onClick={() => toggleIssue(globalIndex)}
                                className="w-full flex items-start gap-2 p-3 text-left hover:opacity-80 transition"
                            >
                                <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${colorClass}`} />
                                <div className="flex-1 min-w-0">
                                    <div className={`text-sm font-medium ${colorClass}`}>
                                        {issue.issue_type.replace(/_/g, ' ').toUpperCase()}
                                    </div>
                                    {!isExpanded && (
                                        <div className="text-xs text-gray-600 mt-1 truncate">
                                            {issue.description}
                                        </div>
                                    )}
                                </div>
                                {isExpanded ? (
                                    <ChevronDown className="w-4 h-4 flex-shrink-0 text-gray-500" />
                                ) : (
                                    <ChevronRight className="w-4 h-4 flex-shrink-0 text-gray-500" />
                                )}
                            </button>

                            {isExpanded && (
                                <div className="px-3 pb-3 space-y-2">
                                    <div className="text-sm text-gray-700">{issue.description}</div>
                                    {issue.location_hint && (
                                        <div className="text-xs text-gray-600">
                                            <span className="font-semibold">Location:</span> {issue.location_hint}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="space-y-4 mt-3">
            <div className="text-xs font-semibold text-gray-700 mb-2">Validation Issues:</div>
            {renderIssueGroup(criticalIssues, 'critical', AlertOctagon, 'text-red-700')}
            {renderIssueGroup(majorIssues, 'major', AlertTriangle, 'text-yellow-700')}
            {renderIssueGroup(minorIssues, 'minor', Info, 'text-blue-700')}
        </div>
    );
}
