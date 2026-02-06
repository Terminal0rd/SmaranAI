/**
 * Quiz History Page - Review Past Quiz Attempts
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
    ClipboardList,
    Clock,
    CheckCircle,
    XCircle,
    ArrowLeft,
    ChevronRight,
    Loader2,
    Trophy,
    Brain
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { quizAPI } from '@/lib/api';
import { formatDate } from '@/lib/utils';

export default function QuizHistoryPage() {
    const router = useRouter();
    const [attempts, setAttempts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedAttempt, setSelectedAttempt] = useState<any>(null);
    const [viewingDetails, setViewingDetails] = useState(false);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const response = await quizAPI.getHistory();
                setAttempts(response.data);
            } catch (error) {
                toast.error('Failed to load quiz history');
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    const viewAttemptDetails = async (attemptId: string) => {
        setViewingDetails(true);
        try {
            const response = await quizAPI.getAttempt(attemptId);
            setSelectedAttempt(response.data);
        } catch (error) {
            toast.error('Failed to load quiz details');
        } finally {
            setViewingDetails(false);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-green-400';
        if (score >= 60) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getScoreBg = (score: number) => {
        if (score >= 80) return 'bg-green-500/10 border-green-500/20';
        if (score >= 60) return 'bg-yellow-500/10 border-yellow-500/20';
        return 'bg-red-500/10 border-red-500/20';
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            </div>
        );
    }

    if (selectedAttempt) {
        return (
            <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
                <div className="max-w-4xl mx-auto">
                    {/* Header */}
                    <div className="mb-6 flex items-center justify-between">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedAttempt(null)}
                        >
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back to History
                        </Button>
                        <div className="text-right">
                            <p className="text-sm text-slate-400">Quiz Score</p>
                            <p className={`text-3xl font-bold ${getScoreColor(selectedAttempt.score)}`}>
                                {selectedAttempt.score.toFixed(0)}%
                            </p>
                        </div>
                    </div>

                    {/* Quiz Results */}
                    <div className="space-y-4">
                        <Card>
                            <CardHeader>
                                <CardTitle>Quiz Summary</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="text-center">
                                        <p className="text-2xl font-bold text-white">
                                            {selectedAttempt.total_questions}
                                        </p>
                                        <p className="text-sm text-slate-400">Total Questions</p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-2xl font-bold text-green-400">
                                            {selectedAttempt.correct_answers}
                                        </p>
                                        <p className="text-sm text-slate-400">Correct</p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-2xl font-bold text-red-400">
                                            {selectedAttempt.total_questions - selectedAttempt.correct_answers}
                                        </p>
                                        <p className="text-sm text-slate-400">Incorrect</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Questions Review */}
                        {selectedAttempt.questions?.map((q: any, index: number) => (
                            <Card key={q.question_id}>
                                <CardContent className="pt-6">
                                    <div className="flex items-start gap-3">
                                        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${q.is_correct
                                                ? 'bg-green-500/20 text-green-400'
                                                : 'bg-red-500/20 text-red-400'
                                            }`}>
                                            {q.is_correct ? (
                                                <CheckCircle className="w-5 h-5" />
                                            ) : (
                                                <XCircle className="w-5 h-5" />
                                            )}
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-white font-medium mb-3">
                                                {index + 1}. {q.question_text}
                                            </p>

                                            {/* User Answer */}
                                            <div className={`mb-2 p-3 rounded-lg border ${q.is_correct
                                                    ? 'bg-green-500/5 border-green-500/20'
                                                    : 'bg-red-500/5 border-red-500/20'
                                                }`}>
                                                <p className="text-xs text-slate-400 mb-1">Your Answer:</p>
                                                <p className="text-white">{q.user_answer || 'No answer'}</p>
                                            </div>

                                            {/* Correct Answer (if wrong) */}
                                            {!q.is_correct && (
                                                <div className="p-3 rounded-lg border bg-green-500/5 border-green-500/20">
                                                    <p className="text-xs text-slate-400 mb-1">Correct Answer:</p>
                                                    <p className="text-green-400">{q.correct_answer}</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center">
                                <ClipboardList className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-white">Quiz History</h1>
                                <p className="text-slate-400">Review your past quiz attempts</p>
                            </div>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => router.push('/learn')}>
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back
                        </Button>
                    </div>

                    {/* Stats Overview */}
                    {attempts.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <Card>
                                <CardContent className="pt-6">
                                    <div className="flex items-center gap-3">
                                        <Trophy className="w-8 h-8 text-yellow-400" />
                                        <div>
                                            <p className="text-2xl font-bold text-white">
                                                {Math.round(
                                                    attempts.reduce((acc, a) => acc + a.score, 0) / attempts.length
                                                )}%
                                            </p>
                                            <p className="text-sm text-slate-400">Average Score</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardContent className="pt-6">
                                    <div className="flex items-center gap-3">
                                        <ClipboardList className="w-8 h-8 text-violet-400" />
                                        <div>
                                            <p className="text-2xl font-bold text-white">{attempts.length}</p>
                                            <p className="text-sm text-slate-400">Total Quizzes</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardContent className="pt-6">
                                    <div className="flex items-center gap-3">
                                        <Brain className="w-8 h-8 text-indigo-400" />
                                        <div>
                                            <p className="text-2xl font-bold text-white">
                                                {attempts.filter(a => a.score >= 80).length}
                                            </p>
                                            <p className="text-sm text-slate-400">High Scores (80%+)</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}
                </motion.div>

                {/* Quiz Attempts List */}
                {attempts.length === 0 ? (
                    <Card>
                        <CardContent className="py-16 text-center">
                            <ClipboardList className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                            <p className="text-slate-400">No quiz attempts yet</p>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => router.push('/learn')}
                                className="mt-4"
                            >
                                Start Learning
                            </Button>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="space-y-3">
                        {attempts.map((attempt, index) => (
                            <motion.div
                                key={attempt.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                            >
                                <Card className="hover:bg-slate-800/50 transition-colors cursor-pointer"
                                    onClick={() => viewAttemptDetails(attempt.id)}
                                >
                                    <CardContent className="py-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4 flex-1">
                                                {/* Score Badge */}
                                                <div className={`px-4 py-2 rounded-lg border ${getScoreBg(attempt.score)}`}>
                                                    <p className={`text-xl font-bold ${getScoreColor(attempt.score)}`}>
                                                        {attempt.score.toFixed(0)}%
                                                    </p>
                                                </div>

                                                {/* Info */}
                                                <div className="flex-1">
                                                    <p className="text-white font-medium">
                                                        {attempt.total_questions} Questions
                                                    </p>
                                                    <div className="flex items-center gap-4 mt-1">
                                                        <span className="text-sm text-slate-400 flex items-center gap-1">
                                                            <Clock className="w-3 h-3" />
                                                            {formatDate(attempt.completed_at)}
                                                        </span>
                                                        <span className="text-sm text-green-400">
                                                            {attempt.correct_answers} correct
                                                        </span>
                                                        <span className="text-sm text-red-400">
                                                            {attempt.total_questions - attempt.correct_answers} wrong
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Arrow */}
                                            <ChevronRight className="w-5 h-5 text-slate-500" />
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
