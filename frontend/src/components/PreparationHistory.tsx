/**
 * Preparation History Sidebar Component
 * Shows list of past preparations with load/delete actions
 */
'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { X, Trash2, Calendar, BookOpen, Loader2 } from 'lucide-react';
import { preparationAPI } from '@/lib/api';
import toast from 'react-hot-toast';

interface HistoryItem {
    id: number;
    subject: string;
    university: string;
    exam_type: string;
    exam_date: string | null;
    created_at: string;
    has_notes: boolean;
    has_questions: boolean;
    has_mock: boolean;
}

interface PreparationHistoryProps {
    onSelect: (id: number) => void;
    onClose: () => void;
}

export function PreparationHistory({ onSelect, onClose }: PreparationHistoryProps) {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [deleting, setDeleting] = useState<number | null>(null);

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            setLoading(true);
            const data = await preparationAPI.getHistory(20, 0);
            setHistory(data.preparations);
        } catch (error) {
            console.error('Failed to load history:', error);
            toast.error('Failed to load history');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: number, e: React.MouseEvent) => {
        e.stopPropagation();

        if (!confirm('Delete this preparation?')) return;

        try {
            setDeleting(id);
            await preparationAPI.deletePreparation(id);
            toast.success('Preparation deleted');
            setHistory(history.filter(h => h.id !== id));
        } catch (error) {
            console.error('Delete failed:', error);
            toast.error('Failed to delete');
        } finally {
            setDeleting(null);
        }
    };

    return (
        <motion.div
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 300, opacity: 0 }}
            className="fixed inset-y-0 right-0 w-96 bg-slate-900 border-l border-slate-700 shadow-2xl z-50 overflow-hidden flex flex-col"
        >
            {/* Header */}
            <div className="p-6 border-b border-slate-700 flex items-center justify-between">
                <h2 className="text-xl font-bold text-white">History</h2>
                <button
                    onClick={onClose}
                    className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                >
                    <X className="w-5 h-5 text-slate-400" />
                </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
                    </div>
                ) : history.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                        No preparations yet
                    </div>
                ) : (
                    history.map((item) => (
                        <motion.div
                            key={item.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="p-4 bg-slate-800 hover:bg-slate-750 rounded-lg cursor-pointer transition-all group"
                            onClick={() => onSelect(item.id)}
                        >
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex-1">
                                    <h3 className="font-semibold text-white mb-1 group-hover:text-violet-400 transition-colors">
                                        {item.subject}
                                    </h3>
                                    <p className="text-sm text-slate-400">{item.university}</p>
                                </div>
                                <button
                                    onClick={(e) => handleDelete(item.id, e)}
                                    disabled={deleting === item.id}
                                    className="p-2 hover:bg-red-500/20 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                >
                                    {deleting === item.id ? (
                                        <Loader2 className="w-4 h-4 text-red-400 animate-spin" />
                                    ) : (
                                        <Trash2 className="w-4 h-4 text-red-400" />
                                    )}
                                </button>
                            </div>

                            <div className="flex items-center gap-2 text-xs text-slate-500 mb-3">
                                <Calendar className="w-3 h-3" />
                                {new Date(item.created_at).toLocaleDateString()}
                                <span>•</span>
                                <span>{item.exam_type}</span>
                            </div>

                            {/* Progress badges */}
                            <div className="flex flex-wrap gap-2">
                                {item.has_notes && (
                                    <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
                                        Notes
                                    </span>
                                )}
                                {item.has_questions && (
                                    <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
                                        Questions
                                    </span>
                                )}
                                {item.has_mock && (
                                    <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">
                                        Mock Test
                                    </span>
                                )}
                            </div>
                        </motion.div>
                    ))
                )}
            </div>
        </motion.div>
    );
}
