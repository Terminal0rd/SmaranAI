/**
 * Document Upload Page
 */
'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Upload,
    FileText,
    Loader2,
    CheckCircle,
    Trash2,
    AlertCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { documentsAPI, subjectsAPI } from '@/lib/api';
import { formatDate } from '@/lib/utils';

export default function UploadPage() {
    const [subjects, setSubjects] = useState<any[]>([]);
    const [documents, setDocuments] = useState<any[]>([]);
    const [selectedSubject, setSelectedSubject] = useState<string>('');
    const [uploading, setUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [subjectsRes, docsRes] = await Promise.all([
                    subjectsAPI.getAll(),
                    documentsAPI.getAll(),
                ]);
                setSubjects(subjectsRes.data);
                setDocuments(docsRes.data.documents || []);
                if (subjectsRes.data.length > 0) {
                    setSelectedSubject(subjectsRes.data[0].id);
                }
            } catch (error) {
                console.error('Failed to fetch data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback(async (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        const files = e.dataTransfer.files;
        if (files && files[0]) {
            await uploadFile(files[0]);
        }
    }, [selectedSubject]);

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files[0]) {
            await uploadFile(files[0]);
        }
    };

    const uploadFile = async (file: File) => {
        // Subject is now optional - backend will auto-classify if not provided

        if (!file.name.toLowerCase().endsWith('.pdf')) {
            toast.error('Only PDF files are allowed');
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            toast.error('File size must be less than 10MB');
            return;
        }

        setUploading(true);
        try {
            // Pass selectedSubject (empty string triggers auto-classification)
            const response = await documentsAPI.upload(file, selectedSubject || '');
            setDocuments(prev => [response.data, ...prev]);
            toast.success('Document uploaded! Processing...');

            // Poll for processing status
            const checkStatus = async () => {
                const status = await documentsAPI.getStatus(response.data.id);
                if (status.data.is_processed) {
                    setDocuments(prev =>
                        prev.map(d => d.id === response.data.id ? { ...d, is_processed: true, chunks_count: status.data.chunks_count } : d)
                    );
                    toast.success('Document processed successfully!');
                } else {
                    setTimeout(checkStatus, 3000);
                }
            };
            setTimeout(checkStatus, 3000);
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (documentId: string) => {
        if (!confirm('Are you sure you want to delete this document?')) return;

        try {
            await documentsAPI.delete(documentId);
            setDocuments(prev => prev.filter(d => d.id !== documentId));
            toast.success('Document deleted');
        } catch (error) {
            toast.error('Failed to delete document');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-4xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <h1 className="text-3xl font-bold text-white mb-2">Upload Documents</h1>
                    <p className="text-slate-400">
                        Add PDF documents to enhance the AI's knowledge base
                    </p>
                </motion.div>

                {/* Subject Selection - NOW OPTIONAL */}
                <Card className="mb-6">
                    <CardContent className="pt-6">
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Select Subject (Optional)
                            <span className="ml-2 text-xs text-slate-500">
                                ✨ Leave empty to auto-detect
                            </span>
                        </label>
                        <select
                            value={selectedSubject}
                            onChange={(e) => setSelectedSubject(e.target.value)}
                            className="w-full p-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-violet-500 focus:outline-none"
                        >
                            <option value="">🤖 Auto-detect subject</option>
                            {subjects.map((subject) => (
                                <option key={subject.id} value={subject.id}>
                                    {subject.icon} {subject.name}
                                </option>
                            ))}
                        </select>
                        <p className="mt-2 text-xs text-slate-500">
                            AI will automatically classify your PDF if no subject is selected
                        </p>
                    </CardContent>
                </Card>

                {/* Upload Area */}
                <Card className="mb-8">
                    <CardContent className="pt-6">
                        <div
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                            className={`
                relative border-2 border-dashed rounded-xl p-12 text-center transition-colors
                ${dragActive
                                    ? 'border-violet-500 bg-violet-500/10'
                                    : 'border-slate-700 hover:border-slate-600'
                                }
              `}
                        >
                            <input
                                type="file"
                                accept=".pdf"
                                onChange={handleFileSelect}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                disabled={uploading}
                            />

                            {uploading ? (
                                <div>
                                    <Loader2 className="w-12 h-12 text-violet-500 animate-spin mx-auto mb-4" />
                                    <p className="text-white font-medium">Uploading...</p>
                                </div>
                            ) : (
                                <>
                                    <Upload className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                                    <p className="text-white font-medium mb-2">
                                        Drop your PDF here or click to browse
                                    </p>
                                    <p className="text-sm text-slate-400">
                                        Maximum file size: 10MB
                                    </p>
                                </>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Document List */}
                <Card>
                    <CardHeader>
                        <CardTitle>Uploaded Documents</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {documents.length > 0 ? (
                            <div className="space-y-3">
                                <AnimatePresence>
                                    {documents.map((doc, index) => (
                                        <motion.div
                                            key={doc.id}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, x: -100 }}
                                            transition={{ delay: index * 0.05 }}
                                            className="flex items-center gap-4 p-4 rounded-lg bg-slate-800/50"
                                        >
                                            <div className={`p-2 rounded-lg ${doc.is_processed ? 'bg-green-500/10' : 'bg-amber-500/10'}`}>
                                                {doc.is_processed ? (
                                                    <CheckCircle className="w-5 h-5 text-green-500" />
                                                ) : (
                                                    <Loader2 className="w-5 h-5 text-amber-500 animate-spin" />
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-white font-medium truncate">{doc.original_name}</p>
                                                <p className="text-sm text-slate-400">
                                                    {formatDate(doc.uploaded_at)}
                                                    {doc.is_processed && doc.chunks_count && ` • ${doc.chunks_count} chunks`}
                                                </p>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => handleDelete(doc.id)}
                                                className="text-slate-400 hover:text-red-400"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </motion.div>
                                    ))}
                                </AnimatePresence>
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <p className="text-slate-400">No documents uploaded yet</p>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Info */}
                <div className="mt-6 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    <div className="flex gap-3">
                        <AlertCircle className="w-5 h-5 text-violet-400 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-slate-400">
                            <p className="font-medium text-slate-300 mb-1">How it works</p>
                            <p>
                                Uploaded PDFs are processed and added to the global knowledge base.
                                The AI tutor will use this content to provide better, more accurate answers.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
