/**
 * Progress Dashboard Page
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
    Target,
    TrendingUp,
    Clock,
    BookOpen,
    Brain,
    Loader2,
    ArrowUpRight,
    ClipboardList,
    CheckCircle,
    XCircle,
    ChevronRight
} from 'lucide-react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar
} from 'recharts';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { progressAPI, quizAPI } from '@/lib/api';
import { getScoreColor, formatDate } from '@/lib/utils';

export default function ProgressPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<any>(null);
    const [quizHistory, setQuizHistory] = useState<any[]>([]);

    useEffect(() => {
        const fetchProgress = async () => {
            try {
                const [progressRes, quizRes] = await Promise.all([
                    progressAPI.getDashboard(),
                    quizAPI.getHistory().catch(() => ({ data: [] })),
                ]);
                setData(progressRes.data);
                setQuizHistory(quizRes.data || []);
            } catch (error) {
                console.error('Failed to fetch progress:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchProgress();
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            </div>
        );
    }

    const getScoreBg = (score: number) => {
        if (score >= 80) return 'bg-green-500/10 border-green-500/20';
        if (score >= 60) return 'bg-yellow-500/10 border-yellow-500/20';
        return 'bg-red-500/10 border-red-500/20';
    };

    const stats = [
        {
            label: 'Total Sessions',
            value: data?.progress?.total_sessions || 0,
            icon: BookOpen,
            color: 'text-blue-400',
            bg: 'bg-blue-500/10',
        },
        {
            label: 'Quizzes Taken',
            value: data?.progress?.total_quizzes || 0,
            icon: Target,
            color: 'text-green-400',
            bg: 'bg-green-500/10',
        },
        {
            label: 'Average Score',
            value: `${Math.round(data?.progress?.overall_avg_score || 0)}%`,
            icon: TrendingUp,
            color: 'text-violet-400',
            bg: 'bg-violet-500/10',
        },
        {
            label: 'Time Spent',
            value: `${data?.progress?.total_time_spent_minutes || 0}m`,
            icon: Clock,
            color: 'text-amber-400',
            bg: 'bg-amber-500/10',
        },
    ];

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <h1 className="text-3xl font-bold text-white mb-2">Progress Dashboard</h1>
                    <p className="text-slate-400">Track your learning journey</p>
                </motion.div>

                {/* Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    {stats.map((stat, index) => (
                        <motion.div
                            key={stat.label}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <Card variant="glass">
                                <CardContent className="flex items-center gap-4">
                                    <div className={`p-3 rounded-lg ${stat.bg}`}>
                                        <stat.icon className={`w-5 h-5 ${stat.color}`} />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-white">{stat.value}</p>
                                        <p className="text-sm text-slate-400">{stat.label}</p>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    ))}
                </div>

                <div className="grid lg:grid-cols-3 gap-6 mb-8">
                    {/* Quiz Score History */}
                    <Card className="lg:col-span-2">
                        <CardHeader>
                            <CardTitle>Quiz Performance</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {data?.quiz_scores_history?.length > 0 ? (
                                <ResponsiveContainer width="100%" height={250}>
                                    <LineChart data={data.quiz_scores_history}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis
                                            dataKey="date"
                                            stroke="#64748b"
                                            tickFormatter={(val) => formatDate(val)}
                                        />
                                        <YAxis stroke="#64748b" domain={[0, 100]} />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: '#1e293b',
                                                border: '1px solid #334155',
                                                borderRadius: '8px',
                                            }}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="score"
                                            stroke="#8b5cf6"
                                            strokeWidth={2}
                                            dot={{ fill: '#8b5cf6', strokeWidth: 2 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-[250px] flex items-center justify-center text-slate-500">
                                    No quiz data yet
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Weak Topics */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Target className="w-4 h-4 text-amber-400" />
                                Focus Areas
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {data?.weak_topics?.length > 0 ? (
                                <div className="space-y-2">
                                    {data.weak_topics.slice(0, 8).map((topic: string, i: number) => (
                                        <div
                                            key={topic}
                                            className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50"
                                        >
                                            <span className="text-sm text-white">{topic}</span>
                                            <span className="text-xs text-amber-400">Review</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-8">
                                    <Target className="w-10 h-10 text-slate-600 mx-auto mb-2" />
                                    <p className="text-slate-400 text-sm">No weak areas detected</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Subject Progress */}
                <Card>
                    <CardHeader>
                        <CardTitle>Subject Progress</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {data?.progress?.subjects?.length > 0 ? (
                            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {data.progress.subjects.map((subject: any, i: number) => (
                                    <motion.div
                                        key={subject.subject_id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: i * 0.05 }}
                                    >
                                        <Link href={`/mindmap/${subject.subject_id}`}>
                                            <div className="p-4 rounded-xl bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer">
                                                <div className="flex items-center justify-between mb-3">
                                                    <h3 className="text-white font-medium">{subject.subject_name}</h3>
                                                    <ArrowUpRight className="w-4 h-4 text-slate-500" />
                                                </div>
                                                <div className="grid grid-cols-3 gap-2 text-center">
                                                    <div>
                                                        <p className="text-lg font-bold text-white">{subject.total_sessions}</p>
                                                        <p className="text-xs text-slate-400">Sessions</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-lg font-bold text-white">{subject.total_quizzes}</p>
                                                        <p className="text-xs text-slate-400">Quizzes</p>
                                                    </div>
                                                    <div>
                                                        <p className={`text-lg font-bold ${getScoreColor(subject.avg_quiz_score)}`}>
                                                            {Math.round(subject.avg_quiz_score)}%
                                                        </p>
                                                        <p className="text-xs text-slate-400">Avg</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </Link>
                                    </motion.div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <Brain className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <p className="text-slate-400">Start learning to track progress</p>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Quiz History */}
                <Card className="mt-6">
                    <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <ClipboardList className="w-4 h-4 text-violet-400" />
                                Quiz History
                            </div>
                            <Link href="/quiz/history">
                                <button className="text-sm text-violet-400 hover:text-violet-300 flex items-center gap-1">
                                    View All <ChevronRight className="w-3 h-3" />
                                </button>
                            </Link>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {quizHistory.length > 0 ? (
                            <div className="space-y-2">
                                {quizHistory.slice(0, 8).map((attempt: any, i: number) => (
                                    <motion.div
                                        key={attempt.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: i * 0.03 }}
                                        onClick={() => router.push('/quiz/history')}
                                        className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer group"
                                    >
                                        <div className="flex items-center gap-3 flex-1 min-w-0">
                                            {/* Score badge */}
                                            <div className={`px-3 py-1.5 rounded-lg border flex-shrink-0 ${getScoreBg(attempt.score)}`}>
                                                <span className={`text-sm font-bold ${getScoreColor(attempt.score)}`}>
                                                    {attempt.score.toFixed(0)}%
                                                </span>
                                            </div>
                                            {/* Info */}
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-white font-medium truncate">
                                                    {attempt.subject_name || 'Quiz'} — {attempt.total_questions} Qs
                                                </p>
                                                <div className="flex items-center gap-3 mt-0.5">
                                                    <span className="text-xs text-green-400 flex items-center gap-1">
                                                        <CheckCircle className="w-3 h-3" />{attempt.correct_answers}
                                                    </span>
                                                    <span className="text-xs text-red-400 flex items-center gap-1">
                                                        <XCircle className="w-3 h-3" />{attempt.total_questions - attempt.correct_answers}
                                                    </span>
                                                    <span className="text-xs text-slate-500">
                                                        {formatDate(attempt.completed_at)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 flex-shrink-0" />
                                    </motion.div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <ClipboardList className="w-10 h-10 text-slate-600 mx-auto mb-2" />
                                <p className="text-slate-400 text-sm">No quizzes taken yet</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
