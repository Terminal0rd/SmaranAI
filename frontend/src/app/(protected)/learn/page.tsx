/**
 * Learn Page - Subject & Session Selection
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { BookOpen, Plus, Clock, ArrowRight, Search, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { Button, Input, Card, CardContent } from '@/components/ui';
import { subjectsAPI, sessionsAPI } from '@/lib/api';
import { getTimeAgo } from '@/lib/utils';

export default function LearnPage() {
    const router = useRouter();
    const [subjects, setSubjects] = useState<any[]>([]);
    const [sessions, setSessions] = useState<any[]>([]);
    const [selectedSubject, setSelectedSubject] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [showNewSubject, setShowNewSubject] = useState(false);
    const [newSubjectName, setNewSubjectName] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [subjectsRes, sessionsRes] = await Promise.all([
                    subjectsAPI.getAll(),
                    sessionsAPI.getAll(),
                ]);
                setSubjects(subjectsRes.data);
                setSessions(sessionsRes.data);
            } catch (error) {
                console.error('Failed to fetch data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleStartSession = async () => {
        if (!selectedSubject) {
            toast.error('Please select a subject');
            return;
        }

        setCreating(true);
        try {
            const response = await sessionsAPI.create({
                subject_id: selectedSubject.id,
            });
            router.push(`/learn/${response.data.id}`);
        } catch (error) {
            toast.error('Failed to create session');
            setCreating(false);
        }
    };

    const handleAddSubject = async () => {
        if (!newSubjectName.trim()) return;

        try {
            const response = await subjectsAPI.create({
                name: newSubjectName.trim(),
            });
            setSubjects([...subjects, response.data]);
            setNewSubjectName('');
            setShowNewSubject(false);
            toast.success('Subject added!');
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to add subject');
        }
    };

    const filteredSessions = selectedSubject
        ? sessions.filter((s) => s.subject_id === selectedSubject.id)
        : sessions;

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-6xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <h1 className="text-3xl font-bold text-white mb-2">Learn</h1>
                    <p className="text-slate-400">Choose a subject and start learning with your AI tutor</p>
                </motion.div>

                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Subject Selection */}
                    <div className="lg:col-span-1">
                        <h2 className="text-lg font-semibold text-white mb-4">Select Subject</h2>
                        <div className="space-y-2">
                            {subjects.map((subject, index) => (
                                <motion.div
                                    key={subject.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                >
                                    <button
                                        onClick={() => setSelectedSubject(subject)}
                                        className={`w-full flex items-center gap-3 p-4 rounded-xl transition-all ${selectedSubject?.id === subject.id
                                                ? 'bg-violet-500/20 border-2 border-violet-500'
                                                : 'bg-slate-800/50 border-2 border-transparent hover:border-slate-700'
                                            }`}
                                    >
                                        <span className="text-2xl">{subject.icon || '📚'}</span>
                                        <span className="text-white font-medium">{subject.name}</span>
                                    </button>
                                </motion.div>
                            ))}

                            {/* Add Subject */}
                            {showNewSubject ? (
                                <div className="p-4 rounded-xl bg-slate-800/50 border-2 border-dashed border-slate-700">
                                    <Input
                                        placeholder="Subject name"
                                        value={newSubjectName}
                                        onChange={(e) => setNewSubjectName(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && handleAddSubject()}
                                    />
                                    <div className="flex gap-2 mt-3">
                                        <Button size="sm" onClick={handleAddSubject}>Add</Button>
                                        <Button size="sm" variant="ghost" onClick={() => setShowNewSubject(false)}>
                                            Cancel
                                        </Button>
                                    </div>
                                </div>
                            ) : (
                                <button
                                    onClick={() => setShowNewSubject(true)}
                                    className="w-full flex items-center justify-center gap-2 p-4 rounded-xl border-2 border-dashed border-slate-700 text-slate-400 hover:text-white hover:border-slate-600 transition-colors"
                                >
                                    <Plus className="w-5 h-5" />
                                    Add Subject
                                </button>
                            )}
                        </div>

                        {/* Start Session Button */}
                        <Button
                            className="w-full mt-6"
                            size="lg"
                            onClick={handleStartSession}
                            isLoading={creating}
                            disabled={!selectedSubject}
                        >
                            Start New Session
                            <ArrowRight className="w-5 h-5 ml-2" />
                        </Button>
                    </div>

                    {/* Recent Sessions */}
                    <div className="lg:col-span-2">
                        <h2 className="text-lg font-semibold text-white mb-4">
                            {selectedSubject ? `${selectedSubject.name} Sessions` : 'Recent Sessions'}
                        </h2>

                        {filteredSessions.length > 0 ? (
                            <div className="grid sm:grid-cols-2 gap-4">
                                {filteredSessions.slice(0, 6).map((session, index) => (
                                    <motion.div
                                        key={session.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: index * 0.05 }}
                                        whileHover={{ y: -4 }}
                                        onClick={() => router.push(`/learn/${session.id}`)}
                                        className="cursor-pointer"
                                    >
                                        <Card hover>
                                            <CardContent>
                                                <div className="flex items-start justify-between mb-3">
                                                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-500/20 to-indigo-500/20 flex items-center justify-center">
                                                        <BookOpen className="w-5 h-5 text-violet-400" />
                                                    </div>
                                                    <span className="text-xs text-slate-500">
                                                        {getTimeAgo(session.updated_at)}
                                                    </span>
                                                </div>
                                                <h3 className="text-white font-medium mb-1 truncate">
                                                    {session.title || 'Untitled Session'}
                                                </h3>
                                                <p className="text-sm text-slate-400 line-clamp-2">
                                                    {session.summary || 'Continue where you left off...'}
                                                </p>
                                            </CardContent>
                                        </Card>
                                    </motion.div>
                                ))}
                            </div>
                        ) : (
                            <Card>
                                <CardContent className="text-center py-12">
                                    <BookOpen className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                                    <h3 className="text-lg font-medium text-white mb-2">No Sessions Yet</h3>
                                    <p className="text-slate-400 mb-6">
                                        {selectedSubject
                                            ? `Start your first ${selectedSubject.name} session`
                                            : 'Select a subject and start learning'}
                                    </p>
                                    <Button onClick={handleStartSession} disabled={!selectedSubject}>
                                        <Plus className="w-4 h-4 mr-2" />
                                        Start First Session
                                    </Button>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
