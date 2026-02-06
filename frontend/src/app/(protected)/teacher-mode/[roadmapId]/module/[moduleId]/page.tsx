/**
 * Module Lesson Page
 * Teach → Check → Reteach flow with Memory Cards
 */
'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ArrowLeft, ArrowRight, Loader2, BookOpen, Target, RefreshCw,
    CheckCircle, XCircle, Lightbulb, Award, Sparkles
} from 'lucide-react';
import { Button, Card, CardContent } from '@/components/ui';
import { teacherAPI } from '@/lib/api';

type Phase = 'teach' | 'check' | 'reteach' | 'cards';

export default function ModuleLessonPage() {
    const params = useParams();
    const router = useRouter();
    const roadmapId = params.roadmapId as string;
    const moduleId = params.moduleId as string;

    const [module, setModule] = useState<any>(null);
    const [phase, setPhase] = useState<Phase>('teach');
    const [loading, setLoading] = useState(true);

    // Teach phase
    const [teachContent, setTeachContent] = useState<any>(null);
    const [loadingTeach, setLoadingTeach] = useState(false);
    const [showChat, setShowChat] = useState(false);
    const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'assistant', message: string }[]>([]);
    const [chatInput, setChatInput] = useState('');
    const [loadingChat, setLoadingChat] = useState(false);

    // Check phase
    const [questions, setQuestions] = useState<any[]>([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [loadingCheck, setLoadingCheck] = useState(false);
    const [checkResult, setCheckResult] = useState<any>(null);

    // Reteach phase
    const [reteachContent, setReteachContent] = useState<any>(null);

    // Memory cards
    const [memoryCards, setMemoryCards] = useState<any[]>([]);
    const [flippedCard, setFlippedCard] = useState<number | null>(null);
    const [currentCardIndex, setCurrentCardIndex] = useState(0);

    useEffect(() => {
        fetchModule();
    }, [moduleId]);

    const fetchModule = async () => {
        try {
            const res = await teacherAPI.getModule(roadmapId, moduleId);
            setModule(res.data);

            // Set initial phase based on module state
            if (res.data.current_phase) {
                setPhase(res.data.current_phase);
            }
        } catch (err) {
            console.error('Failed to fetch module:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadTeachContent = async () => {
        setLoadingTeach(true);
        try {
            const res = await teacherAPI.generateTeach(roadmapId, moduleId);
            setTeachContent(res.data);
        } catch (err) {
            console.error('Failed to load teach content:', err);
        } finally {
            setLoadingTeach(false);
        }
    };

    const startCheck = async () => {
        setLoadingCheck(true);
        try {
            const res = await teacherAPI.generateCheck(roadmapId, moduleId);
            setQuestions(res.data.questions || []);
            setCurrentQuestionIndex(0);
            setAnswers({});
            setPhase('check');
        } catch (err) {
            console.error('Failed to generate check:', err);
        } finally {
            setLoadingCheck(false);
        }
    };

    const submitCheck = async () => {
        setLoadingCheck(true);
        try {
            const answerArray = questions.map(q => ({
                question_id: q.question_id,
                answer: answers[q.question_id] || ''
            }));

            const res = await teacherAPI.submitCheck(roadmapId, moduleId, answerArray);
            setCheckResult(res.data);

            if (res.data.passed) {
                // Load memory cards
                loadMemoryCards();
            }
        } catch (err) {
            console.error('Failed to submit check:', err);
        } finally {
            setLoadingCheck(false);
        }
    };

    const loadReteach = async (weakTopics: string[]) => {
        setLoadingCheck(true);
        try {
            const res = await teacherAPI.generateReteach(roadmapId, moduleId, weakTopics);
            setReteachContent(res.data);
            setPhase('reteach');
        } catch (err) {
            console.error('Failed to load reteach:', err);
        } finally {
            setLoadingCheck(false);
        }
    };

    const loadMemoryCards = async () => {
        try {
            const res = await teacherAPI.getMemoryCards(roadmapId, moduleId);
            setMemoryCards(res.data.cards || []);
            setPhase('cards');
        } catch (err) {
            console.error('Failed to load memory cards:', err);
        }
    };

    const sendChatMessage = async () => {
        if (!chatInput.trim() || loadingChat) return;

        const userMessage = chatInput.trim();
        setChatInput('');
        setChatMessages(prev => [...prev, { role: 'user', message: userMessage }]);
        setLoadingChat(true);

        try {
            const res = await teacherAPI.teachChat(roadmapId, moduleId, userMessage);
            setChatMessages(prev => [...prev, { role: 'assistant', message: res.data.response }]);
        } catch (err) {
            console.error('Failed to send chat:', err);
            setChatMessages(prev => [...prev, { role: 'assistant', message: 'Sorry, I encountered an error. Please try again.' }]);
        } finally {
            setLoadingChat(false);
        }
    };

    // Auto-load teach content
    useEffect(() => {
        if (phase === 'teach' && !teachContent && !loading && module) {
            loadTeachContent();
        }
    }, [phase, loading, module]);

    // Auto-load memory cards
    useEffect(() => {
        if (phase === 'cards' && memoryCards.length === 0 && !loading && module) {
            loadMemoryCards();
        }
    }, [phase, loading, module]);

    const getSectionIcon = (type: string) => {
        switch (type) {
            case 'intro': return '👋';
            case 'definition': return '📖';
            case 'concept': return '💡';
            case 'example': return '🔍';
            case 'practice': return '🎯';
            case 'mistake': return '⚠️';
            case 'summary': return '✨';
            default: return '📝';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <Loader2 className="w-12 h-12 text-violet-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-4">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-6">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => router.push(`/teacher-mode/${roadmapId}`)}
                        className="mb-4"
                    >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to Roadmap
                    </Button>

                    <h1 className="text-3xl font-bold text-white mb-2">{module?.title}</h1>
                    <div className="flex items-center gap-2">
                        <span className="px-2 py-1 bg-violet-500/20 text-violet-300 rounded-full text-xs">
                            {module?.level}
                        </span>
                        <span className="text-slate-400 text-sm">{module?.estimated_minutes} minutes</span>
                    </div>
                </div>

                {/* Phase Indicator */}
                <div className="flex items-center justify-center gap-2 mb-8">
                    {['teach', 'check', 'cards'].map((p, i) => (
                        <div key={p} className="flex items-center">
                            <div className={`px-4 py-2 rounded-lg font-medium transition-all ${phase === p ? 'bg-violet-500 text-white' : 'bg-slate-800 text-slate-400'
                                }`}>
                                {i + 1}. {p.charAt(0).toUpperCase() + p.slice(1)}
                            </div>
                            {i < 2 && <div className="w-8 h-0.5 bg-slate-700 mx-1" />}
                        </div>
                    ))}
                </div>

                {/* Content based on phase */}
                {phase === 'teach' && (
                    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                        {/* LEFT: Whiteboard Content - 60% */}
                        <div className="lg:col-span-3">
                            <Card className="!bg-slate-900 h-full">
                                <CardContent className="p-6">
                                    <div className="flex items-center gap-2 mb-4">
                                        <BookOpen className="w-6 h-6 text-violet-500" />
                                        <h2 className="text-2xl font-semibold text-white">Class Whiteboard</h2>
                                    </div>

                                    {loadingTeach ? (
                                        <div className="flex flex-col items-center justify-center py-12">
                                            <Loader2 className="w-8 h-8 text-violet-500 animate-spin mb-4" />
                                            <p className="text-slate-400">Generating teaching content...</p>
                                        </div>
                                    ) : teachContent && teachContent.sections ? (
                                        <div className="space-y-6 max-h-[600px] overflow-y-auto pr-2">
                                            {teachContent.sections.map((section: any, i: number) => (
                                                <div key={i} className="border-l-4 border-violet-500 pl-4 py-2">
                                                    <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-2">
                                                        <span>{getSectionIcon(section.type)}</span>
                                                        {section.title}
                                                    </h3>
                                                    <div className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                                                        {section.content}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center py-12">
                                            <p className="text-slate-400">Loading teaching content...</p>
                                        </div>
                                    )}

                                    {teachContent && (
                                        <Button
                                            onClick={() => startCheck()}
                                            disabled={loadingCheck}
                                            size="lg"
                                            className="w-full mt-6 bg-violet-500 hover:bg-violet-600"
                                        >
                                            {loadingCheck ? (
                                                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                            ) : (
                                                <Target className="w-5 h-5 mr-2" />
                                            )}
                                            Ready for the Check
                                        </Button>
                                    )}
                                </CardContent>
                            </Card>
                        </div>

                        {/* RIGHT: Q&A Panel - 40% */}
                        {teachContent && (
                            <div className="lg:col-span-2">
                                <Card className="!bg-slate-900 h-full sticky top-6">
                                    <CardContent className="p-6 flex flex-col h-full">
                                        <div className="flex items-center gap-2 mb-4">
                                            <Lightbulb className="w-5 h-5 text-violet-500" />
                                            <h3 className="text-xl font-semibold text-white">Have Questions? Ask Me!</h3>
                                        </div>

                                        {/* Chat Messages */}
                                        <div className="flex-1 bg-slate-800 rounded-lg p-4 mb-4 overflow-y-auto space-y-3" style={{ minHeight: '400px', maxHeight: '500px' }}>
                                            {chatMessages.length === 0 ? (
                                                <p className="text-slate-400 text-sm text-center py-4">
                                                    Ask any question about this module, and I'll help you understand better!
                                                </p>
                                            ) : (
                                                chatMessages.map((msg, i) => (
                                                    <div
                                                        key={i}
                                                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                                    >
                                                        <div
                                                            className={`max-w-[85%] px-4 py-2 rounded-lg ${msg.role === 'user'
                                                                    ? 'bg-violet-500 text-white'
                                                                    : 'bg-slate-700 text-slate-100'
                                                                }`}
                                                        >
                                                            <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                                                        </div>
                                                    </div>
                                                ))
                                            )}
                                            {loadingChat && (
                                                <div className="flex justify-start">
                                                    <div className="bg-slate-700 px-4 py-2 rounded-lg">
                                                        <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Chat Input */}
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                value={chatInput}
                                                onChange={(e) => setChatInput(e.target.value)}
                                                onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                                                placeholder="Type your question..."
                                                className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-violet-500"
                                                disabled={loadingChat}
                                            />
                                            <Button
                                                onClick={sendChatMessage}
                                                disabled={!chatInput.trim() || loadingChat}
                                                className="bg-violet-500 hover:bg-violet-600"
                                            >
                                                {loadingChat ? (
                                                    <Loader2 className="w-4 h-4 animate-spin" />
                                                ) : (
                                                    'Ask'
                                                )}
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        )}
                    </div>
                )}

                {phase === 'check' && !checkResult && (
                    <motion.div
                        key="check"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                    >
                        <Card className="!bg-slate-900 mb-6">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
                                        <Target className="w-6 h-6 text-violet-500" />
                                        Check Your Understanding
                                    </h2>
                                    <div className="flex items-center gap-3">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => setPhase('teach')}
                                            className="text-slate-400 hover:text-white"
                                        >
                                            <ArrowLeft className="w-4 h-4 mr-1" />
                                            Back to Teaching
                                        </Button>
                                        <span className="text-slate-400">
                                            Question {currentQuestionIndex + 1} of {questions.length}
                                        </span>
                                    </div>
                                </div>

                                {questions[currentQuestionIndex] && (
                                    <div className="space-y-4">
                                        <p className="text-lg text-white">
                                            {questions[currentQuestionIndex].question_text}
                                        </p>

                                        {questions[currentQuestionIndex].question_type === 'mcq' && questions[currentQuestionIndex].options ? (
                                            <div className="space-y-2">
                                                {questions[currentQuestionIndex].options.map((option: string, i: number) => (
                                                    <button
                                                        key={i}
                                                        onClick={() => setAnswers(prev => ({
                                                            ...prev,
                                                            [questions[currentQuestionIndex].question_id]: option
                                                        }))}
                                                        className={`w-full p-4 rounded-lg text-left transition-all ${answers[questions[currentQuestionIndex].question_id] === option
                                                            ? 'bg-violet-500 text-white'
                                                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                                                            }`}
                                                    >
                                                        {option}
                                                    </button>
                                                ))}
                                            </div>
                                        ) : (
                                            <textarea
                                                value={answers[questions[currentQuestionIndex].question_id] || ''}
                                                onChange={(e) => setAnswers(prev => ({
                                                    ...prev,
                                                    [questions[currentQuestionIndex].question_id]: e.target.value
                                                }))}
                                                placeholder="Type your answer here..."
                                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white resize-none focus:outline-none focus:ring-2 focus:ring-violet-500"
                                                rows={4}
                                            />
                                        )}

                                        <div className="flex gap-2">
                                            {currentQuestionIndex < questions.length - 1 ? (
                                                <Button
                                                    onClick={() => setCurrentQuestionIndex(prev => prev + 1)}
                                                    className="flex-1"
                                                >
                                                    Next Question
                                                </Button>
                                            ) : (
                                                <Button
                                                    onClick={submitCheck}
                                                    disabled={loadingCheck}
                                                    className="flex-1 bg-green-600 hover:bg-green-700"
                                                >
                                                    {loadingCheck ? (
                                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                                    ) : (
                                                        'Submit Check'
                                                    )}
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </motion.div>
                )}

                {checkResult && (
                    <motion.div
                        key="result"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                    >
                        <Card className={`!bg-slate-900 mb-6 border-2 ${checkResult.passed ? 'border-green-500' : 'border-red-500'
                            }`}>
                            <CardContent className="p-6 text-center">
                                {checkResult.passed ? (
                                    <>
                                        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                                        <h2 className="text-3xl font-bold text-white mb-2">Mastery Achieved!</h2>
                                        <p className="text-green-400 text-lg mb-4">
                                            Score: {Math.round(checkResult.score * 100)}%
                                        </p>
                                        <Button
                                            onClick={() => setPhase('cards')}
                                            size="lg"
                                            className="bg-green-600 hover:bg-green-700"
                                        >
                                            <Award className="w-5 h-5 mr-2" />
                                            View Memory Cards
                                        </Button>
                                    </>
                                ) : (
                                    <>
                                        <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                                        <h2 className="text-3xl font-bold text-white mb-2">Need More Practice</h2>
                                        <p className="text-red-400 text-lg mb-4">
                                            Score: {Math.round(checkResult.score * 100)}%
                                        </p>
                                        {checkResult.weak_topics && checkResult.weak_topics.length > 0 && (
                                            <div className="mb-4">
                                                <p className="text-slate-400 text-sm mb-2">Topics to review:</p>
                                                <div className="flex flex-wrap gap-2 justify-center">
                                                    {checkResult.weak_topics.map((topic: string, i: number) => (
                                                        <span key={i} className="px-3 py-1 bg-red-500/20 text-red-300 rounded-full text-sm">
                                                            {topic}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        <div className="flex gap-2 justify-center">
                                            <Button
                                                onClick={() => loadReteach(checkResult.weak_topics || [])}
                                                size="lg"
                                                className="bg-violet-600 hover:bg-violet-700"
                                            >
                                                <Lightbulb className="w-5 h-5 mr-2" />
                                                Get Help
                                            </Button>
                                            <Button
                                                onClick={() => {
                                                    setCheckResult(null);
                                                    startCheck();
                                                }}
                                                size="lg"
                                                variant="outline"
                                            >
                                                <RefreshCw className="w-5 h-5 mr-2" />
                                                Retry Check
                                            </Button>
                                        </div>
                                    </>
                                )}
                            </CardContent>
                        </Card>
                    </motion.div>
                )}

                {phase === 'reteach' && reteachContent && (
                    <motion.div
                        key="reteach"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <Card className="!bg-slate-900 mb-6">
                            <CardContent className="p-6">
                                <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                                    <Lightbulb className="w-6 h-6 text-yellow-500" />
                                    Let's Review Together
                                </h2>

                                <div className="space-y-6">
                                    {reteachContent.explanations?.map((exp: any, i: number) => (
                                        <div key={i} className="p-4 bg-slate-800 rounded-lg">
                                            <h3 className="font-semibold text-violet-400 mb-2">{exp.topic}</h3>
                                            <p className="text-slate-300">{exp.explanation}</p>
                                        </div>
                                    ))}
                                </div>

                                <Button
                                    onClick={() => {
                                        setCheckResult(null);
                                        startCheck();
                                    }}
                                    size="lg"
                                    className="w-full mt-6 bg-violet-500 hover:bg-violet-600"
                                >
                                    <Target className="w-5 h-5 mr-2" />
                                    Try Check Again
                                </Button>
                            </CardContent>
                        </Card>
                    </motion.div>
                )}

                {phase === 'cards' && (
                    <motion.div
                        key="cards"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <Card className="!bg-slate-900 mb-6">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between mb-6">
                                    <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
                                        <Sparkles className="w-6 h-6 text-yellow-500" />
                                        Memory Cards for Retention
                                    </h2>
                                    {memoryCards.length > 0 && (
                                        <span className="text-slate-400">
                                            Card {currentCardIndex + 1} of {memoryCards.length}
                                        </span>
                                    )}
                                </div>

                                {memoryCards.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center py-12">
                                        <Loader2 className="w-8 h-8 text-violet-500 animate-spin mb-4" />
                                        <p className="text-slate-400">Generating memory cards...</p>
                                    </div>
                                ) : (
                                    <div className="space-y-6">
                                        {/* Current Card */}
                                        <div
                                            onClick={() => setFlippedCard(flippedCard === currentCardIndex ? null : currentCardIndex)}
                                            className="cursor-pointer"
                                        >
                                            <div className="relative h-64">
                                                {/* Card Container with flip animation */}
                                                <motion.div
                                                    className="w-full h-full"
                                                    animate={{ rotateY: flippedCard === currentCardIndex ? 180 : 0 }}
                                                    transition={{ duration: 0.6 }}
                                                    style={{ transformStyle: 'preserve-3d' }}
                                                >
                                                    {/* Front */}
                                                    <div
                                                        className="absolute inset-0 p-8 bg-gradient-to-br from-violet-500/20 to-indigo-500/20 border-2 border-violet-500 rounded-xl flex flex-col items-center justify-center"
                                                        style={{
                                                            backfaceVisibility: 'hidden',
                                                            transform: 'rotateY(0deg)'
                                                        }}
                                                    >
                                                        <p className="text-2xl text-white text-center font-semibold mb-4">
                                                            {memoryCards[currentCardIndex].front_text}
                                                        </p>
                                                        <p className="text-sm text-slate-400">Click to reveal answer</p>
                                                    </div>

                                                    {/* Back */}
                                                    <div
                                                        className="absolute inset-0 p-8 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border-2 border-emerald-500 rounded-xl flex flex-col items-center justify-center"
                                                        style={{
                                                            backfaceVisibility: 'hidden',
                                                            transform: 'rotateY(180deg)'
                                                        }}
                                                    >
                                                        <p className="text-lg text-slate-100 text-center leading-relaxed">
                                                            {memoryCards[currentCardIndex].back_text}
                                                        </p>
                                                    </div>
                                                </motion.div>
                                            </div>
                                        </div>

                                        {/* Progress Bar */}
                                        <div className="bg-slate-800 rounded-full h-2 overflow-hidden">
                                            <div
                                                className="bg-violet-500 h-full transition-all duration-300"
                                                style={{ width: `${((currentCardIndex + 1) / memoryCards.length) * 100}%` }}
                                            />
                                        </div>

                                        {/* Navigation */}
                                        <div className="flex gap-3">
                                            <Button
                                                onClick={() => setCurrentCardIndex(prev => Math.max(0, prev - 1))}
                                                disabled={currentCardIndex === 0}
                                                variant="outline"
                                                className="flex-1"
                                            >
                                                <ArrowLeft className="w-4 h-4 mr-2" />
                                                Previous
                                            </Button>
                                            <Button
                                                onClick={() => setCurrentCardIndex(prev => Math.min(memoryCards.length - 1, prev + 1))}
                                                disabled={currentCardIndex === memoryCards.length - 1}
                                                className="flex-1 bg-violet-500 hover:bg-violet-600"
                                            >
                                                Next
                                                <ArrowRight className="w-4 h-4 ml-2" />
                                            </Button>
                                        </div>

                                        {/* Keyboard Hint */}
                                        <p className="text-center text-sm text-slate-500">
                                            💡 Tip: Click card to flip • Use buttons to navigate cards
                                        </p>
                                    </div>
                                )}

                                {/* Actions */}
                                <div className="flex gap-3 mt-6">
                                    <Button
                                        onClick={() => setPhase('teach')}
                                        variant="outline"
                                        size="lg"
                                        className="flex-1"
                                    >
                                        <BookOpen className="w-5 h-5 mr-2" />
                                        Review Teaching
                                    </Button>
                                    <Button
                                        onClick={() => router.push(`/teacher-mode/${roadmapId}`)}
                                        size="lg"
                                        className="flex-1 bg-green-600 hover:bg-green-700"
                                    >
                                        <Award className="w-5 h-5 mr-2" />
                                        Complete Module
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                )}
            </div>
        </div >
    );
}
