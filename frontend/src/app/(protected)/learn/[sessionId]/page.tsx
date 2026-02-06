/**
 * Learning Session Page - Whiteboard Chat UI with Export
 */
'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send,
    ArrowLeft,
    Sparkles,
    FileText,
    Brain,
    Loader2,
    Youtube,
    Download,
    ClipboardList,
    FileDown,
    Presentation
} from 'lucide-react';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import { Button, Input, Card } from '@/components/ui';
import { sessionsAPI, chatAPI, subjectsAPI, exportAPI } from '@/lib/api';
import { formatTime } from '@/lib/utils';
import Link from 'next/link';

export default function SessionPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = params.sessionId as string;

    const [session, setSession] = useState<any>(null);
    const [subject, setSubject] = useState<any>(null);
    const [messages, setMessages] = useState<any[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);
    const [exporting, setExporting] = useState(false);
    const [activeSlide, setActiveSlide] = useState(0);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const fetchSession = async () => {
            try {
                const response = await sessionsAPI.getById(sessionId);
                setSession(response.data);
                setMessages(response.data.messages || []);

                const subjectRes = await subjectsAPI.getById(response.data.subject_id);
                setSubject(subjectRes.data);
            } catch (error) {
                toast.error('Failed to load session');
                router.push('/learn');
            } finally {
                setLoading(false);
            }
        };
        fetchSession();
    }, [sessionId, router]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        const assistantMessages = messages.filter(m => m.role === 'assistant');
        if (assistantMessages.length > 0) {
            setActiveSlide(assistantMessages.length - 1);
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || sending) return;

        const userMessage = {
            id: `temp-${Date.now()}`,
            role: 'user',
            content: input,
            created_at: new Date().toISOString(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setSending(true);

        try {
            const response = await chatAPI.sendMessage(sessionId, userMessage.content);

            const assistantMessage = {
                id: response.data.message_id,
                role: 'assistant',
                content: response.data.content,
                formatted_content: response.data.formatted_content,
                sources_used: response.data.sources,
                created_at: new Date().toISOString(),
            };

            setMessages(prev => [...prev.filter(m => m.id !== userMessage.id),
            { ...userMessage, id: `user-${Date.now()}` },
                assistantMessage
            ]);
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to get response');
            setMessages(prev => prev.filter(m => m.id !== userMessage.id));
        } finally {
            setSending(false);
            inputRef.current?.focus();
        }
    };

    const handleExportPDF = async () => {
        setExporting(true);
        try {
            const response = await exportAPI.downloadPDF(sessionId);
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${session?.title || 'session'}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('PDF downloaded!');
        } catch (error) {
            toast.error('Failed to export PDF');
        } finally {
            setExporting(false);
        }
    };

    const handleExportPPTX = async () => {
        setExporting(true);
        try {
            const response = await exportAPI.downloadPPTX(sessionId);
            const blob = new Blob([response.data], {
                type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${session?.title || 'session'}.pptx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('PowerPoint downloaded!');
        } catch (error) {
            toast.error('Failed to export PowerPoint');
        } finally {
            setExporting(false);
        }
    };

    const slides = messages.filter(m => m.role === 'assistant');
    const currentSlide = slides[activeSlide];

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            </div>
        );
    }

    return (
        /* FIXED: Position below global navbar (top-16) to prevent overlap */
        <div className="fixed inset-x-0 bottom-0 top-16 bg-slate-950 flex flex-col overflow-hidden z-40">
            {/* FIXED: Sticky Header - Always visible at top */}
            <header className="flex-shrink-0 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 px-4 py-3 z-50">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="sm" onClick={() => router.push('/learn')}>
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back
                        </Button>
                        <div className="flex items-center gap-2">
                            <span className="text-xl">{subject?.icon || '📚'}</span>
                            <div>
                                <h1 className="text-white font-medium">{session?.title || 'Learning Session'}</h1>
                                <p className="text-xs text-slate-400">{subject?.name}</p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* Export Buttons */}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleExportPDF}
                            disabled={exporting || messages.length === 0}
                        >
                            <FileDown className="w-4 h-4 mr-1" />
                            PDF
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleExportPPTX}
                            disabled={exporting || messages.length === 0}
                        >
                            <Presentation className="w-4 h-4 mr-1" />
                            PPT
                        </Button>
                        <Link href={`/mindmap/${session?.subject_id}`}>
                            <Button variant="ghost" size="sm">
                                <Brain className="w-4 h-4 mr-1" />
                                Mind Map
                            </Button>
                        </Link>
                        <Link href={`/quiz/${sessionId}`}>
                            <Button variant="outline" size="sm">
                                <ClipboardList className="w-4 h-4 mr-1" />
                                Take Quiz
                            </Button>
                        </Link>
                    </div>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                {/* Slide Timeline */}
                {slides.length > 0 && (
                    <aside className="w-20 lg:w-48 bg-slate-900/50 border-r border-slate-800 overflow-y-auto p-2">
                        <p className="text-xs text-slate-400 uppercase tracking-wider mb-3 px-2 hidden lg:block">
                            Slides ({slides.length})
                        </p>
                        {slides.map((slide, index) => (
                            <motion.button
                                key={slide.id}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => setActiveSlide(index)}
                                className={`w-full p-2 rounded-lg mb-2 text-left transition-colors ${activeSlide === index
                                    ? 'bg-violet-500/20 border border-violet-500'
                                    : 'bg-slate-800/50 border border-transparent hover:bg-slate-800'
                                    }`}
                            >
                                <div className="aspect-video bg-slate-800 rounded mb-1 flex items-center justify-center text-xs text-slate-500">
                                    {index + 1}
                                </div>
                                <p className="text-xs text-slate-400 truncate hidden lg:block">
                                    {slide.content.slice(0, 30)}...
                                </p>
                            </motion.button>
                        ))}
                    </aside>
                )}

                {/* Main Content - FIXED: Flex column with sticky input */}
                <main className="flex-1 flex flex-col h-full overflow-hidden">
                    {/* Scrollable Content Area */}
                    <div className="flex-1 overflow-y-auto p-6">
                        <AnimatePresence mode="wait">
                            {currentSlide ? (
                                <motion.div
                                    key={currentSlide.id}
                                    initial={{ opacity: 0, x: 50 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -50 }}
                                    transition={{ duration: 0.3 }}
                                    className="max-w-4xl mx-auto pb-6"
                                >
                                    {/* FIXED: Show user question before AI answer */}
                                    {(() => {
                                        const slideIndex = slides.indexOf(currentSlide);
                                        const userQuestion = messages.filter(m => m.role === 'user')[slideIndex];
                                        return userQuestion ? (
                                            <div className="mb-4 p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
                                                <p className="text-xs text-violet-400 uppercase tracking-wide mb-1">Your Question</p>
                                                <p className="text-white font-medium">{userQuestion.content}</p>
                                            </div>
                                        ) : null;
                                    })()}

                                    <Card variant="gradient" className="p-8">
                                        {/* Enhanced markdown prose classes */}
                                        <div className="prose prose-invert prose-violet max-w-none prose-headings:font-bold prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl prose-p:text-base prose-p:leading-relaxed prose-li:my-1 prose-ul:space-y-2 prose-ol:space-y-2">
                                            <ReactMarkdown>
                                                {currentSlide.formatted_content || currentSlide.content}
                                            </ReactMarkdown>
                                        </div>

                                        {currentSlide.sources_used?.length > 0 && (
                                            <div className="mt-6 pt-6 border-t border-slate-700">
                                                <p className="text-sm text-slate-400 mb-2">
                                                    <FileText className="w-4 h-4 inline mr-1" />
                                                    Sources Used:
                                                </p>
                                                <div className="flex flex-wrap gap-2">
                                                    {currentSlide.sources_used.map((source: any, i: number) => (
                                                        <span
                                                            key={i}
                                                            className="px-3 py-1 rounded-full text-xs bg-slate-800 text-slate-300"
                                                        >
                                                            {source.filename}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </Card>
                                </motion.div>
                            ) : (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="h-full flex items-center justify-center"
                                >
                                    <div className="text-center">
                                        <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-violet-500/20 to-indigo-500/20 rounded-2xl flex items-center justify-center">
                                            <Sparkles className="w-10 h-10 text-violet-400" />
                                        </div>
                                        <h2 className="text-xl font-semibold text-white mb-2">
                                            Ready to Learn?
                                        </h2>
                                        <p className="text-slate-400 max-w-md">
                                            Ask any question about {subject?.name} and I'll explain it on the whiteboard.
                                        </p>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                        <div ref={messagesEndRef} />
                    </div>

                    {/* FIXED: Sticky Input Bar - Always visible at bottom with padding */}
                    <div className="w-full flex-shrink-0 border-t border-slate-800 bg-slate-900/95 backdrop-blur-md p-4 pb-6">
                        <div className="max-w-4xl mx-auto flex gap-3">
                            <Input
                                ref={inputRef}
                                placeholder={`Ask about ${subject?.name || 'anything'}...`}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                                disabled={sending}
                                className="flex-1"
                            />
                            <Button onClick={handleSend} isLoading={sending} disabled={!input.trim()}>
                                <Send className="w-4 h-4" />
                            </Button>
                        </div>

                    </div>
                </main>
            </div>
        </div>
    );
}
