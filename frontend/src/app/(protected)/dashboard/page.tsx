/**
 * Dashboard Page
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
    BookOpen,
    Brain,
    Target,
    Clock,
    TrendingUp,
    Plus,
    ArrowRight,
    Sparkles
} from 'lucide-react';
import { useAuthStore } from '@/lib/auth-store';
import { useSessionStore } from '@/lib/session-store';
import { subjectsAPI, sessionsAPI, progressAPI } from '@/lib/api';
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { formatDate, getTimeAgo } from '@/lib/utils';

export default function DashboardPage() {
    const { user } = useAuthStore();
    const { setSubjects } = useSessionStore();
    const [subjects, setLocalSubjects] = useState<any[]>([]);
    const [sessions, setSessions] = useState<any[]>([]);
    const [dashboardData, setDashboardData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [subjectsRes, sessionsRes, progressRes] = await Promise.all([
                    subjectsAPI.getAll(),
                    sessionsAPI.getAll(),
                    progressAPI.getDashboard(),
                ]);
                setLocalSubjects(subjectsRes.data);
                setSubjects(subjectsRes.data);
                setSessions(sessionsRes.data.slice(0, 5));
                setDashboardData(progressRes.data);
            } catch (error) {
                console.error('Failed to fetch dashboard data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [setSubjects]);

    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 12) return 'Good morning';
        if (hour < 17) return 'Good afternoon';
        return 'Good evening';
    };

    const stats = [
        {
            label: 'Total Sessions',
            value: dashboardData?.progress?.total_sessions || 0,
            icon: BookOpen,
            color: 'text-blue-400',
            bg: 'bg-blue-500/10',
        },
        {
            label: 'Quizzes Taken',
            value: dashboardData?.progress?.total_quizzes || 0,
            icon: Target,
            color: 'text-green-400',
            bg: 'bg-green-500/10',
        },
        {
            label: 'Avg Quiz Score',
            value: `${Math.round(dashboardData?.progress?.overall_avg_score || 0)}%`,
            icon: TrendingUp,
            color: 'text-violet-400',
            bg: 'bg-violet-500/10',
        },
        {
            label: 'Time Spent',
            value: `${dashboardData?.progress?.total_time_spent_minutes || 0}m`,
            icon: Clock,
            color: 'text-amber-400',
            bg: 'bg-amber-500/10',
        },
    ];

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <h1 className="text-3xl font-bold text-white mb-2">
                        {getGreeting()}, {user?.full_name?.split(' ')[0]}! 👋
                    </h1>
                    <p className="text-slate-400">
                        Ready to continue your learning journey?
                    </p>
                </motion.div>

                {/* Stats Grid */}
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

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Recent Sessions */}
                    <div className="lg:col-span-2">
                        <Card>
                            <CardHeader className="flex items-center justify-between">
                                <CardTitle>Recent Sessions</CardTitle>
                                <Link href="/learn">
                                    <Button size="sm" variant="ghost">
                                        View All
                                        <ArrowRight className="w-4 h-4 ml-1" />
                                    </Button>
                                </Link>
                            </CardHeader>
                            <CardContent>
                                {sessions.length > 0 ? (
                                    <div className="space-y-3">
                                        {sessions.map((session, index) => (
                                            <motion.div
                                                key={session.id}
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: index * 0.05 }}
                                            >
                                                <Link href={`/learn/${session.id}`}>
                                                    <div className="flex items-center gap-4 p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer">
                                                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-500/20 to-indigo-500/20 flex items-center justify-center">
                                                            <BookOpen className="w-5 h-5 text-violet-400" />
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <p className="text-white font-medium truncate">
                                                                {session.title || 'Untitled Session'}
                                                            </p>
                                                            <p className="text-sm text-slate-400">
                                                                {getTimeAgo(session.updated_at)}
                                                            </p>
                                                        </div>
                                                        <ArrowRight className="w-4 h-4 text-slate-500" />
                                                    </div>
                                                </Link>
                                            </motion.div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-8">
                                        <BookOpen className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                                        <p className="text-slate-400 mb-4">No sessions yet</p>
                                        <Link href="/learn">
                                            <Button size="sm">
                                                <Plus className="w-4 h-4 mr-1" />
                                                Start Learning
                                            </Button>
                                        </Link>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Quick Actions */}
                    <div className="space-y-6">
                        {/* Start New Session */}
                        <Card variant="gradient">
                            <CardContent className="text-center py-6">
                                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-2xl flex items-center justify-center">
                                    <Sparkles className="w-8 h-8 text-white" />
                                </div>
                                <h3 className="text-lg font-semibold text-white mb-2">
                                    Start New Session
                                </h3>
                                <p className="text-sm text-slate-400 mb-4">
                                    Begin learning a new topic with your AI tutor
                                </p>
                                <Link href="/learn">
                                    <Button className="w-full">
                                        <Plus className="w-4 h-4 mr-2" />
                                        New Session
                                    </Button>
                                </Link>
                            </CardContent>
                        </Card>

                        {/* Weak Topics */}
                        {dashboardData?.weak_topics?.length > 0 && (
                            <Card>
                                <CardHeader>
                                    <CardTitle className="text-base flex items-center gap-2">
                                        <Target className="w-4 h-4 text-amber-400" />
                                        Focus Areas
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex flex-wrap gap-2">
                                        {dashboardData.weak_topics.slice(0, 5).map((topic: string) => (
                                            <span
                                                key={topic}
                                                className="px-3 py-1 rounded-full text-sm bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                            >
                                                {topic}
                                            </span>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Subjects */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base flex items-center gap-2">
                                    <Brain className="w-4 h-4 text-violet-400" />
                                    Your Subjects
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 gap-2">
                                    {subjects.slice(0, 4).map((subject) => (
                                        <Link key={subject.id} href={`/mindmap/${subject.id}`}>
                                            <div className="p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer text-center">
                                                <span className="text-xl">{subject.icon || '📚'}</span>
                                                <p className="text-sm text-slate-300 mt-1 truncate">
                                                    {subject.name}
                                                </p>
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
}
