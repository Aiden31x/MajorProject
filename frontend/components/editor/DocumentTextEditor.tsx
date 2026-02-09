"use client";

import { useEffect, useCallback, forwardRef, useImperativeHandle } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { ClauseHighlight } from './ClauseHighlightExtension';
import { EditorClausePosition } from '@/types/editor';

interface DocumentTextEditorProps {
    fullText: string;
    clausePositions: EditorClausePosition[];
    onClauseClick?: (clause: EditorClausePosition) => void;
}

export interface DocumentTextEditorRef {
    replaceClauseText: (clauseId: string, newText: string) => void;
    getText: () => string;
    getEditor: () => any;
}

export const DocumentTextEditor = forwardRef<DocumentTextEditorRef, DocumentTextEditorProps>(
    ({ fullText, clausePositions, onClauseClick }, ref) => {
        const editor = useEditor({
            extensions: [
                StarterKit,
                ClauseHighlight,
            ],
            content: fullText,
            editorProps: {
                attributes: {
                    class: 'prose prose-sm max-w-none focus:outline-none min-h-[600px] p-6',
                },
            },
        });

        // Apply highlights when clauses change
        useEffect(() => {
            if (!editor || !clausePositions.length) return;

            // Clear existing highlights
            editor.commands.clearContent();
            editor.commands.setContent(fullText);

            // Sort descending to apply from end to start (avoids position shifts)
            const sorted = [...clausePositions].sort((a, b) => b.absolute_start - a.absolute_start);

            // Apply each highlight
            sorted.forEach(clause => {
                try {
                    // TipTap uses 1-indexed positions
                    const from = clause.absolute_start + 1;
                    const to = clause.absolute_end + 1;

                    editor
                        .chain()
                        .setTextSelection({ from, to })
                        .setClauseHighlight({
                            clauseId: clause.id,
                            severity: clause.risk_severity,
                            category: clause.risk_category,
                            explanation: clause.risk_explanation,
                        })
                        .run();
                } catch (error) {
                    console.error('Error applying highlight:', error, clause);
                }
            });

            // Reset selection to end
            editor.commands.setTextSelection(editor.state.doc.content.size);
        }, [editor, fullText, clausePositions]);

        // Handle clause clicks
        useEffect(() => {
            if (!editor || !onClauseClick) return;

            const handleClick = (event: MouseEvent) => {
                const target = event.target as HTMLElement;

                // Check if clicked element is a highlighted clause
                if (target.classList.contains('clause-highlight')) {
                    const clauseId = target.getAttribute('data-clause-id');

                    if (clauseId) {
                        const clause = clausePositions.find(c => c.id === clauseId);
                        if (clause) {
                            onClauseClick(clause);
                        }
                    }
                }
            };

            const editorElement = editor.view.dom;
            editorElement.addEventListener('click', handleClick);

            return () => {
                editorElement.removeEventListener('click', handleClick);
            };
        }, [editor, clausePositions, onClauseClick]);

        // Expose methods via ref
        useImperativeHandle(ref, () => ({
            replaceClauseText: (clauseId: string, newText: string) => {
                if (!editor) return;

                const clause = clausePositions.find(c => c.id === clauseId);
                if (!clause) return;

                try {
                    // TipTap uses 1-indexed positions
                    const from = clause.absolute_start + 1;
                    const to = clause.absolute_end + 1;

                    // Step 1: Remove the old highlight and text
                    editor
                        .chain()
                        .setTextSelection({ from, to })
                        .unsetClauseHighlight()
                        .deleteSelection()
                        .run();

                    // Step 2: Insert new text at the position
                    editor
                        .chain()
                        .insertContentAt(from, newText)
                        .run();

                    // Step 3: Apply green "Accepted" highlight to the new text
                    const newTo = from + newText.length;
                    editor
                        .chain()
                        .setTextSelection({ from, to: newTo })
                        .setClauseHighlight({
                            clauseId: `${clauseId}-accepted`,
                            severity: 'Accepted',
                            category: clause.risk_category,
                            explanation: 'This clause has been revised and accepted',
                        })
                        .run();

                    // Reset selection to end of replaced text
                    editor.commands.setTextSelection(newTo);

                    console.log(`✅ Replaced clause ${clauseId} with green highlight`);
                } catch (error) {
                    console.error('Error replacing clause text:', error);
                }
            },
            getText: () => {
                return editor?.getText() || '';
            },
            getEditor: () => editor,
        }));

        if (!editor) {
            return <div>Loading editor...</div>;
        }

        return (
            <div className="h-full flex flex-col border rounded-lg bg-white">
                <div className="border-b px-4 py-2 bg-slate-50">
                    <p className="text-sm text-muted-foreground">
                        Click on highlighted clauses to view details and suggestions
                    </p>
                </div>
                <div className="flex-1 overflow-auto">
                    <EditorContent editor={editor} />
                </div>
            </div>
        );
    }
);

DocumentTextEditor.displayName = 'DocumentTextEditor';
