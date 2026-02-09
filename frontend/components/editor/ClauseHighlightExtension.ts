/**
 * ClauseHighlight - Custom TipTap Mark Extension
 * Highlights risky clauses with severity-based colors
 */
import { Mark, mergeAttributes } from '@tiptap/core';

export interface ClauseHighlightOptions {
    HTMLAttributes: Record<string, any>;
}

declare module '@tiptap/core' {
    interface Commands<ReturnType> {
        clauseHighlight: {
            setClauseHighlight: (attributes: {
                clauseId: string;
                severity: 'High' | 'Medium' | 'Low' | 'Accepted';
                category: string;
                explanation: string;
            }) => ReturnType;
            unsetClauseHighlight: () => ReturnType;
        };
    }
}

export const ClauseHighlight = Mark.create<ClauseHighlightOptions>({
    name: 'clauseHighlight',

    addOptions() {
        return {
            HTMLAttributes: {},
        };
    },

    addAttributes() {
        return {
            clauseId: {
                default: null,
                parseHTML: element => element.getAttribute('data-clause-id'),
                renderHTML: attributes => {
                    if (!attributes.clauseId) {
                        return {};
                    }
                    return {
                        'data-clause-id': attributes.clauseId,
                    };
                },
            },
            severity: {
                default: 'Medium',
                parseHTML: element => element.getAttribute('data-severity'),
                renderHTML: attributes => {
                    if (!attributes.severity) {
                        return {};
                    }
                    return {
                        'data-severity': attributes.severity,
                    };
                },
            },
            category: {
                default: '',
                parseHTML: element => element.getAttribute('data-category'),
                renderHTML: attributes => {
                    if (!attributes.category) {
                        return {};
                    }
                    return {
                        'data-category': attributes.category,
                    };
                },
            },
            explanation: {
                default: '',
                parseHTML: element => element.getAttribute('data-explanation'),
                renderHTML: attributes => {
                    if (!attributes.explanation) {
                        return {};
                    }
                    return {
                        'data-explanation': attributes.explanation,
                    };
                },
            },
        };
    },

    parseHTML() {
        return [
            {
                tag: 'mark[data-clause-id]',
            },
        ];
    },

    renderHTML({ HTMLAttributes }) {
        const severity = HTMLAttributes['data-severity'] || 'Medium';

        // Severity-based background colors
        const colorMap: Record<string, string> = {
            High: 'rgba(239, 68, 68, 0.3)', // red
            Medium: 'rgba(234, 179, 8, 0.3)', // yellow
            Low: 'rgba(34, 197, 94, 0.3)', // green (low risk)
            Accepted: 'rgba(34, 197, 94, 0.4)', // green (accepted/replaced)
        };

        const backgroundColor = colorMap[severity] || colorMap.Medium;

        return [
            'mark',
            mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
                style: `background-color: ${backgroundColor}; cursor: pointer; border-radius: 2px; padding: 1px 0;`,
                class: 'clause-highlight',
            }),
            0,
        ];
    },

    addCommands() {
        return {
            setClauseHighlight:
                attributes =>
                    ({ commands }) => {
                        return commands.setMark(this.name, attributes);
                    },
            unsetClauseHighlight:
                () =>
                    ({ commands }) => {
                        return commands.unsetMark(this.name);
                    },
        };
    },
});
