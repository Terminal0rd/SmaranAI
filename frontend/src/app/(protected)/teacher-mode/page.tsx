/**
 * Teacher Mode - Main Entry Page
 * Subject selection and roadmap creation
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { GraduationCap, Loader2, Plus, BookOpen, TrendingUp, Award } from 'lucide-react';
import { Button, Card, CardContent } from '@/components/ui';
import { teacherAPI } from '@/lib/api';

export default function TeacherModePage() {
    const router = useRouter();
    const [subject, setSubject] = useState('');
    const [goal, setGoal] = useState('');
    const [loading, setLoading] = useState(false);
    const [roadmaps, setRoadmaps] = useState<any[]>([]);
    const [loadingRoadmaps, setLoadingRoadmaps] = useState(true);

    useEffect(() => {
        fetchRoadmaps();
    }, []);

    const fetchRoadmaps = async () => {
        try {
            const res = await teacherAPI.getAllRoadmaps();
            setRoadmaps(res.data || []);
        } catch (err) {
            console.error('Failed to fetch roadmaps:', err);
        } finally {
            setLoadingRoadmaps(false);
        }
    };

    const createRoadmap = async () => {
        if (!subject.trim()) return;

        setLoading(true);
        try {
            const res = await teacherAPI.createRoadmap({
                subject: subject.trim(),
                goal: goal.trim() || undefined
            });
            router.push(`/teacher-mode/${res.data.id}`);
        } catch (err) {
            console.error('Failed to create roadmap:', err);
            alert('Failed to create roadmap. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const subjectSuggestions = [
        'Machine Learning', 'Web Development', 'Data Structures',
        'Mathematics', 'Physics', 'Chemistry', 'Biology',
        'History', 'English Literature', 'Programming'
    ];

    const goalOptions = ['exam', 'understanding', 'projects'];

    return (
        <div className="min-h-screen bg-slate-950 p-4">
            <div className="max-w-6xl mx-auto">
                {/* Hero Section */}
                <motion.div
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="text-center mb-12 mt-8"
                >
                    <div className="flex items-center justify-center mb-4">
                        <GraduationCap className="w-16 h-16 text-violet-500 mr-3" />
                        <h1 className="text-5xl font-bold text-white">Teacher Mode</h1>
                    </div>
                    <p className="text-xl text-slate-400 max-w-2xl mx-auto">
                        AI-Guided Mastery Learning with Structured Roadmaps
                    </p>
                    <p className="text-sm text-slate-500 mt-2">
                        Progress through beginner to advanced modules with mastery gates
                    </p>
                </motion.div>

                {/* Create New Roadmap */}
                <motion.div
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                >
                    <Card className="!bg-gradient-to-br from-violet-900/20 to-purple-900/20 border-violet-500/30 mb-8">
                        <CardContent className="p-6">
                            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                                <Plus className="w-6 h-6" />
                                Create Learning Roadmap
                            </h2>

                            <div className="space-y-4">
                                {/* Subject Input */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Subject *
                                    </label>
                                    <input
                                        type="text"
                                        value={subject}
                                        onChange={(e) => setSubject(e.target.value)}
                                        placeholder="e.g., Machine Learning, Physics, Web Development"
                                        className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                                    />
                                    <div className="flex flex-wrap gap-2 mt-2">
                                        {subjectSuggestions.map(s => (
                                            <button
                                                key={s}
                                                onClick={() => setSubject(s)}
                                                className="px-3 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-full transition-colors"
                                            >
                                                {s}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Goal Selection */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Learning Goal (Optional)
                                    </label>
                                    <div className="flex gap-2">
                                        {goalOptions.map(g => (
                                            <button
                                                key={g}
                                                onClick={() => setGoal(goal === g ? '' : g)}
                                                className={`px-4 py-2 rounded-lg font-medium transition-all ${goal === g
                                                        ? 'bg-violet-500 text-white'
                                                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                                                    }`}
                                            >
                                                {g.charAt(0).toUpperCase() + g.slice(1)}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Create Button */}
                                <Button
                                    onClick={createRoadmap}
                                    disabled={!subject.trim() || loading}
                                    size="lg"
                                    className="w-full bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                            Creating AI Roadmap...
                                        </>
                                    ) : (
                                        <>
                                            <GraduationCap className="w-5 h-5 mr-2" />
                                            Create Roadmap
                                        </>
                                    )}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Existing Roadmaps */}
                <div>
                    <h2 className="text-2xl font-semibold text-white mb-4">Your Learning Paths</h2>

                    {loadingRoadmaps ? (
                        <div className="flex justify-center py-12">
                            <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
                        </div>
                    ) : roadmaps.length === 0 ? (
                        <Card className="!bg-slate-900/50">
                            <CardContent className="p-12 text-center">
                                <BookOpen className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <p className="text-slate-400">No roadmaps yet. Create your first one above!</p>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {roadmaps.map((roadmap, index) => (
                                <motion.div
                                    key={roadmap.id}
                                    initial={{ y: 20, opacity: 0 }}
                                    animate={{ y: 0, opacity: 1 }}
                                    transition={{ delay: index * 0.1 }}
                                >
                                    <Card
                                        className="!bg-slate-900 hover:!bg-slate-800 cursor-pointer transition-all border-slate-700 hover:border-violet-500"
                                        onClick={() => router.push(`/teacher-mode/${roadmap.id}`)}
                                    >
                                        <CardContent className="p-5">
                                            <div className="flex items-start justify-between mb-3">
                                                <div className="flex-1">
                                                    <h3 className="text-lg font-semibold text-white mb-1">
                                                        {roadmap.subject}
                                                    </h3>
                                                    {roadmap.goal && (
                                                        <span className="inline-block px-2 py-0.5 text-xs bg-violet-500/20 text-violet-300 rounded-full">
                                                            {roadmap.goal}
                                                        </span>
                                                    )}
                                                </div>
                                                <Award className={`w-5 h-5 ${roadmap.overall_progress === 1 ? 'text-yellow-500' : 'text-slate-600'
                                                    }`} />
                                            </div>

                                            {/* Progress */}
                                            <div className="mb-3">
                                                <div className="flex justify-between text-sm mb-1">
                                                    <span className="text-slate-400">Progress</span>
                                                    <span className="text-violet-400 font-medium">
                                                        {Math.round(roadmap.overall_progress * 100)}%
                                                    </span>
                                                </div>
                                                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${roadmap.overall_progress * 100}%` }}
                                                        transition={{ duration: 0.5 }}
                                                        className="h-full bg-gradient-to-r from-violet-500 to-purple-500"
                                                    />
                                                </div>
                                            </div>

                                            {/* Stats */}
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-slate-400">
                                                    {roadmap.completed_modules}/{roadmap.total_modules} modules
                                                </span>
                                                <TrendingUp className="w-4 h-4 text-green-500" />
                                            </div>
                                        </CardContent>
                                    </Card>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
