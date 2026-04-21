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
    Sparkles,
    GraduationCap
} from 'lucide-react';
import { useAuthStore } from '@/lib/auth-store';
import { useSessionStore } from '@/lib/session-store';
import { subjectsAPI, sessionsAPI, progressAPI, preparationAPI } from '@/lib/api';
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { formatDate, getTimeAgo } from '@/lib/utils';

export default function DashboardPage() {
    const { user } = useAuthStore();
    const { setSubjects } = useSessionStore();
    const [subjects, setLocalSubjects] = useState<any[]>([]);
    const [sessions, setSessions] = useState<any[]>([]);
    const [preparations, setPreparations] = useState<any[]>([]);
    const [dashboardData, setDashboardData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [subjectsRes, sessionsRes, progressRes, preparationsRes] = await Promise.all([
                    subjectsAPI.getAll(),
                    sessionsAPI.getAll(),
                    progressAPI.getDashboard(),
                    preparationAPI.getHistory().catch(() => ({ data: [] })),
                ]);
                setLocalSubjects(subjectsRes.data);
                setSubjects(subjectsRes.data);
                setSessions(sessionsRes.data.slice(0, 5));
                setPreparations(preparationsRes.data || []);
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
                            <CardHeader>
                                <CardTitle className="text-base flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Clock className="w-4 h-4 text-violet-400" />
                                        Recent Sessions
                                    </div>
                                    <Link href="/learn">
                                        <Button variant="ghost" size="sm">
                                            View All
                                            <ArrowRight className="w-3 h-3 ml-1" />
                                        </Button>
                                    </Link>
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                {sessions.length === 0 ? (
                                    <p className="text-sm text-slate-400 text-center py-4">
                                        No sessions yet. Start learning!
                                    </p>
                                ) : (
                                    <div className="space-y-2">
                                        {sessions.map((session: any) => (
                                            <Link key={session.id} href={`/learn/${session.id}`}>
                                                <div className="p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer">
                                                    <div className="flex items-start justify-between gap-2">
                                                        <div className="flex-1 min-w-0">
                                                            <p className="text-sm text-white truncate">
                                                                {session.title || 'Untitled Session'}
                                                            </p>
                                                            <p className="text-xs text-slate-400 mt-1">
                                                                {getTimeAgo(new Date(session.created_at))}
                                                            </p>
                                                        </div>
                                                        <ArrowRight className="w-4 h-4 text-slate-500 flex-shrink-0 mt-1" />
                                                    </div>
                                                </div>
                                            </Link>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Recent Preparations - NEW */}
                        <Card className="mt-6">
                            <CardHeader>
                                <CardTitle className="text-base flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <GraduationCap className="w-4 h-4 text-emerald-400" />
                                        Recent Preparations
                                    </div>
                                    <Link href="/preparation">
                                        <Button variant="ghost" size="sm">
                                            View All
                                            <ArrowRight className="w-3 h-3 ml-1" />
                                        </Button>
                                    </Link>
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                {preparations.length === 0 ? (
                                    <p className="text-sm text-slate-400 text-center py-4">
                                        No preparations yet. Generate your first one!
                                    </p>
                                ) : (
                                    <div className="space-y-2">
                                        {preparations.slice(0, 3).map((prep: any) => (
                                            <div key={prep.id}>
                                                <div className="p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer">
                                                    <div className="flex items-start justify-between gap-2">
                                                        <div className="flex-1 min-w-0">
                                                            <p className="text-sm text-white truncate font-medium">
                                                                {prep.subject}
                                                            </p>
                                                            <p className="text-xs text-slate-400 mt-1">
                                                                {prep.university} • {prep.exam_type}
                                                            </p>
                                                            <p className="text-xs text-slate-500 mt-1">
                                                                {getTimeAgo(new Date(prep.created_at))}
                                                            </p>
                                                        </div>
                                                        <ArrowRight className="w-4 h-4 text-slate-500 flex-shrink-0 mt-1" />
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
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

                        {/* Preparation Mode */}
                        <Card variant="gradient">
                            <CardContent className="text-center py-6">
                                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center">
                                    <GraduationCap className="w-8 h-8 text-white" />
                                </div>
                                <h3 className="text-lg font-semibold text-white mb-2">
                                    Preparation Mode
                                </h3>
                                <p className="text-sm text-slate-400 mb-4">
                                    AI-powered semester prep: notes, questions, mock tests
                                </p>
                                <Link href="/preparation">
                                    <Button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white">
                                        <Sparkles className="w-4 h-4 mr-2" />
                                        Generate Prep
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
