/**
 * Roadmap Overview - Module List Page  
 * Shows all modules with lock states and progress
 */
'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
    ArrowLeft, Loader2, Lock, PlayCircle, CheckCircle,
    Clock, TrendingUp, Target, Award
} from 'lucide-react';
import { Button, Card, CardContent } from '@/components/ui';
import { teacherAPI } from '@/lib/api';

export default function RoadmapPage() {
    const params = useParams();
    const router = useRouter();
    const roadmapId = params.roadmapId as string;

    const [roadmap, setRoadmap] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchRoadmap();
    }, [roadmapId]);

    const fetchRoadmap = async () => {
        try {
            const res = await teacherAPI.getRoadmap(roadmapId);
            setRoadmap(res.data);
        } catch (err) {
            console.error('Failed to fetch roadmap:', err);
        } finally {
            setLoading(false);
        }
    };

    const getLevelColor = (level: string) => {
        switch (level) {
            case 'beginner': return 'bg-green-500/20 text-green-400 border-green-500/30';
            case 'intermediate': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
            case 'advanced': return 'bg-red-500/20 text-red-400 border-red-500/30';
            default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'locked': return <Lock className="w-5 h-5 text-slate-500" />;
            case 'in_progress': return <PlayCircle className="w-5 h-5 text-violet-500" />;
            case 'mastered': return <CheckCircle className="w-5 h-5 text-green-500" />;
            default: return <Lock className="w-5 h-5 text-slate-500" />;
        }
    };

    const canStartModule = (module: any) => {
        return module.status === 'in_progress' || module.status === 'mastered';
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <Loader2 className="w-12 h-12 text-violet-500 animate-spin" />
            </div>
        );
    }

    if (!roadmap) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-slate-400">Roadmap not found</p>
                    <Button onClick={() => router.push('/teacher-mode')} className="mt-4">
                        Back to Teacher Mode
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-4">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => router.push('/teacher-mode')}
                        className="mb-4"
                    >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to Teacher Mode
                    </Button>

                    <div className="flex items-start justify-between">
                        <div>
                            <h1 className="text-4xl font-bold text-white mb-2">{roadmap.subject}</h1>
                            {roadmap.goal && (
                                <span className="inline-block px-3 py-1 bg-violet-500/20 text-violet-300 rounded-full text-sm">
                                    Goal: {roadmap.goal}
                                </span>
                            )}
                        </div>
                        <Award className={`w-12 h-12 ${roadmap.overall_progress === 1 ? 'text-yellow-500' : 'text-slate-600'
                            }`} />
                    </div>

                    {/* Progress Bar */}
                    <div className="mt-6">
                        <div className="flex justify-between text-sm mb-2">
                            <span className="text-slate-400">Overall Progress</span>
                            <span className="text-violet-400 font-semibold">
                                {Math.round(roadmap.overall_progress * 100)}% Complete
                            </span>
                        </div>
                        <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${roadmap.overall_progress * 100}%` }}
                                transition={{ duration: 0.8 }}
                                className="h-full bg-gradient-to-r from-violet-500 via-purple-500 to-pink-500"
                            />
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                            {roadmap.completed_modules} of {roadmap.total_modules} modules completed
                        </p>
                    </div>
                </div>

                {/* Module List */}
                <div className="space-y-4">
                    <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                        <Target className="w-6 h-6 text-violet-500" />
                        Learning Modules
                    </h2>

                    {roadmap.modules && roadmap.modules.map((module: any, index: number) => (
                        <motion.div
                            key={module.id}
                            initial={{ x: -20, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: index * 0.05 }}
                        >
                            <Card className={`!bg-slate-900 transition-all ${canStartModule(module)
                                    ? 'border-violet-500/30 hover:border-violet-500'
                                    : 'border-slate-800 opacity-60'
                                }`}>
                                <CardContent className="p-5">
                                    <div className="flex items-start gap-4">
                                        {/* Module Number */}
                                        <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${module.status === 'mastered' ? 'bg-green-500/20 text-green-400' :
                                                module.status === 'in_progress' ? 'bg-violet-500/20 text-violet-400' :
                                                    'bg-slate-800 text-slate-500'
                                            }`}>
                                            {index + 1}
                                        </div>

                                        {/* Module Content */}
                                        <div className="flex-1">
                                            <div className="flex items-start justify-between mb-2">
                                                <div>
                                                    <h3 className="text-xl font-semibold text-white mb-1">
                                                        {module.title}
                                                    </h3>
                                                    <div className="flex items-center gap-2">
                                                        <span className={`px-2 py-0.5 rounded-full text-xs border ${getLevelColor(module.level)}`}>
                                                            {module.level}
                                                        </span>
                                                        <span className="flex items-center text-xs text-slate-400">
                                                            <Clock className="w-3 h-3 mr-1" />
                                                            {module.estimated_minutes} min
                                                        </span>
                                                    </div>
                                                </div>
                                                {getStatusIcon(module.status)}
                                            </div>

                                            {/* Objectives Preview */}
                                            <div className="text-sm text-slate-400 mb-3">
                                                <p className="font-medium text-slate-300 mb-1">Learning Objectives:</p>
                                                <ul className="list-disc list-inside space-y-0.5">
                                                    {module.objectives.slice(0, 2).map((obj: string, i: number) => (
                                                        <li key={i}>{obj}</li>
                                                    ))}
                                                    {module.objectives.length > 2 && (
                                                        <li className="text-slate-500">+{module.objectives.length - 2} more</li>
                                                    )}
                                                </ul>
                                            </div>

                                            {/* Mastery Score */}
                                            {module.mastery_score > 0 && (
                                                <div className="mb-3">
                                                    <div className="flex justify-between text-xs mb-1">
                                                        <span className="text-slate-400">Mastery</span>
                                                        <span className={module.mastery_score >= 0.7 ? 'text-green-400' : 'text-yellow-400'}>
                                                            {Math.round(module.mastery_score * 100)}%
                                                        </span>
                                                    </div>
                                                    <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                        <div
                                                            className={`h-full ${module.mastery_score >= 0.7 ? 'bg-green-500' : 'bg-yellow-500'
                                                                }`}
                                                            style={{ width: `${module.mastery_score * 100}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            )}

                                            {/* Action Button */}
                                            <div className="flex items-center gap-3">
                                                {module.status === 'locked' ? (
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        disabled
                                                        className="opacity-50"
                                                    >
                                                        <Lock className="w-4 h-4 mr-2" />
                                                        Locked
                                                    </Button>
                                                ) : module.status === 'mastered' ? (
                                                    <Button
                                                        size="sm"
                                                        onClick={() => router.push(`/teacher-mode/${roadmapId}/module/${module.id}`)}
                                                        variant="outline"
                                                    >
                                                        <CheckCircle className="w-4 h-4 mr-2" />
                                                        Review
                                                    </Button>
                                                ) : (
                                                    <Button
                                                        size="sm"
                                                        onClick={() => router.push(`/teacher-mode/${roadmapId}/module/${module.id}`)}
                                                        className="bg-violet-500 hover:bg-violet-600"
                                                    >
                                                        <PlayCircle className="w-4 h-4 mr-2" />
                                                        {module.mastery_score > 0 ? 'Continue' : 'Start'}
                                                    </Button>
                                                )}

                                                {module.prerequisites && module.prerequisites.length > 0 && module.status === 'locked' && (
                                                    <span className="text-xs text-slate-500">
                                                        Complete module {module.prerequisites[0] + 1} first
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    ))}
                </div>

                {/* Stats Footer */}
                <div className="mt-8 grid grid-cols-3 gap-4">
                    <Card className="!bg-slate-900">
                        <CardContent className="p-4 text-center">
                            <TrendingUp className="w-6 h-6 text-green-500 mx-auto mb-2" />
                            <p className="text-2xl font-bold text-white">{roadmap.completed_modules}</p>
                            <p className="text-xs text-slate-400">Completed</p>
                        </CardContent>
                    </Card>
                    <Card className="!bg-slate-900">
                        <CardContent className="p-4 text-center">
                            <PlayCircle className="w-6 h-6 text-violet-500 mx-auto mb-2" />
                            <p className="text-2xl font-bold text-white">
                                {roadmap.modules.filter((m: any) => m.status === 'in_progress').length}
                            </p>
                            <p className="text-xs text-slate-400">In Progress</p>
                        </CardContent>
                    </Card>
                    <Card className="!bg-slate-900">
                        <CardContent className="p-4 text-center">
                            <Lock className="w-6 h-6 text-slate-500 mx-auto mb-2" />
                            <p className="text-2xl font-bold text-white">
                                {roadmap.modules.filter((m: any) => m.status === 'locked').length}
                            </p>
                            <p className="text-xs text-slate-400">Locked</p>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
