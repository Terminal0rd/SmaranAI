/**
 * AI Semester Preparation Engine - Main Page
 */
'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Sparkles,
    GraduationCap,
    Calendar,
    Building2,
    BookOpen,
    Loader2,
    ArrowLeft,
    History
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button, Input, Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { PreparationTabs } from '@/components/PreparationTabs';
import { PreparationHistory } from '@/components/PreparationHistory';
import toast from 'react-hot-toast';
import axios from 'axios';

const LOADING_STAGES = [
    "Analyzing syllabus structure...",
    "Generating smart notes...",
    "Preparing 5-mark questions...",
    "Creating 10-mark questions...",
    "Predicting important questions...",
    "Building mock test paper...",
    "Preparing viva questions...",
    "Designing PPT content...",
    "Creating study planner..."
];

export default function PreparationPage() {
    const router = useRouter();

    const [formData, setFormData] = useState({
        subject: '',
        university: '',
        examType: 'Regular',
        examDate: ''
    });

    const [isGenerating, setIsGenerating] = useState(false);
    const [currentStage, setCurrentStage] = useState(0);
    const [preparationData, setPreparationData] = useState<any>(null);
    const [showHistory, setShowHistory] = useState(false);

    const handleGenerate = async () => {
        if (!formData.subject || !formData.university) {
            toast.error('Please fill in subject and university');
            return;
        }

        setIsGenerating(true);
        setCurrentStage(0);

        // Animate through loading stages
        const stageInterval = setInterval(() => {
            setCurrentStage(prev => {
                if (prev < LOADING_STAGES.length - 1) return prev + 1;
                return prev;
            });
        }, 2000);

        try {
            const token = localStorage.getItem('token');
            const response = await axios.post(
                'http://localhost:8000/api/preparation/generate',
                {
                    subject: formData.subject,
                    university: formData.university,
                    exam_type: formData.examType,
                    exam_date: formData.examDate || null,
                    use_rag: true
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            clearInterval(stageInterval);

            console.log('DEBUG: Backend response:', response.data);

            // Merge response with form data for complete preparation object
            const prepData = {
                ...response.data,
                subject: formData.subject,
                university: formData.university,
                exam_type: formData.examType,
                exam_date: formData.examDate || null
            };

            console.log('DEBUG: Final preparation data with ID:', prepData.id, prepData);
            setPreparationData(prepData);

            toast.success('Preparation generated successfully!');

        } catch (error: any) {
            clearInterval(stageInterval);
            console.error('Generation failed:', error);
            toast.error(error.response?.data?.detail || 'Failed to generate preparation');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleReset = () => {
        setPreparationData(null);
        setFormData({
            subject: '',
            university: '',
            examType: 'Regular',
            examDate: ''
        });
    };

    const handleLoadPreparation = async (id: number) => {
        try {
            const data = await axios.get(
                `http://localhost:8000/api/preparation/history/${id}`,
                {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem('token')}`
                    }
                }
            );

            console.log('DEBUG: Loaded preparation:', data.data);
            setPreparationData(data.data);
            setShowHistory(false);
            toast.success('Preparation loaded');
        } catch (error: any) {
            console.error('Load failed:', error);
            toast.error('Failed to load preparation');
        }
    };

    if (preparationData) {
        return (
            <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
                <div className="max-w-7xl mx-auto">
                    {/* Header */}
                    <div className="mb-6 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleReset}
                            >
                                <ArrowLeft className="w-4 h-4 mr-2" />
                                New Preparation
                            </Button>
                            <div>
                                <h1 className="text-2xl font-bold text-white">
                                    {preparationData.subject} - Exam Preparation
                                </h1>
                                <p className="text-sm text-slate-400">
                                    {preparationData.university} • {preparationData.exam_type}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Tabs */}
                    <PreparationTabs data={preparationData} />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-8"
                >
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex-1" />
                        <div className="w-20 h-20 mx-auto bg-gradient-to-br from-violet-500 to-indigo-600 rounded-3xl flex items-center justify-center">
                            <Sparkles className="w-10 h-10 text-white" />
                        </div>
                        <div className="flex-1 flex justify-end">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setShowHistory(!showHistory)}
                                className="gap-2"
                            >
                                <History className="w-4 h-4" />
                                History
                            </Button>
                        </div>
                    </div>
                    <h1 className="text-4xl font-bold text-white mb-3">
                        AI Semester Preparation Engine
                    </h1>
                    <p className="text-slate-400 text-lg">
                        One-click complete exam preparation with notes, questions, mock tests & more
                    </p>
                </motion.div>

                <AnimatePresence mode="wait">
                    {!isGenerating ? (
                        <motion.div
                            key="form"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                        >
                            <Card variant="gradient">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <GraduationCap className="w-5 h-5" />
                                        Preparation Details
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-5">
                                    {/* Subject */}
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            <BookOpen className="w-4 h-4 inline mr-1" />
                                            Subject Name *
                                        </label>
                                        <Input
                                            placeholder="e.g., Data Structures and Algorithms"
                                            value={formData.subject}
                                            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                                            className="w-full"
                                        />
                                    </div>

                                    {/* University */}
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            <Building2 className="w-4 h-4 inline mr-1" />
                                            University Name *
                                        </label>
                                        <Input
                                            placeholder="e.g., Mumbai University"
                                            value={formData.university}
                                            onChange={(e) => setFormData({ ...formData, university: e.target.value })}
                                            className="w-full"
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        {/* Exam Type */}
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                                Exam Type
                                            </label>
                                            <select
                                                value={formData.examType}
                                                onChange={(e) => setFormData({ ...formData, examType: e.target.value })}
                                                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
                                            >
                                                <option value="Regular">Regular</option>
                                                <option value="Backlog">Backlog</option>
                                                <option value="Competitive">Competitive</option>
                                            </select>
                                        </div>

                                        {/* Exam Date */}
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                                <Calendar className="w-4 h-4 inline mr-1" />
                                                Exam Date (Optional)
                                            </label>
                                            <Input
                                                type="date"
                                                value={formData.examDate}
                                                onChange={(e) => setFormData({ ...formData, examDate: e.target.value })}
                                                className="w-full"
                                            />
                                        </div>
                                    </div>

                                    <Button
                                        onClick={handleGenerate}
                                        className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white font-semibold py-3"
                                        size="lg"
                                    >
                                        <Sparkles className="w-5 h-5 mr-2" />
                                        Generate Complete Preparation
                                    </Button>
                                </CardContent>
                            </Card>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="loading"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="text-center"
                        >
                            <Card variant="glass">
                                <CardContent className="py-12">
                                    <Loader2 className="w-16 h-16 text-violet-500 animate-spin mx-auto mb-6" />
                                    <h3 className="text-2xl font-bold text-white mb-2">
                                        Generating Your Preparation...
                                    </h3>
                                    <p className="text-slate-400 mb-8">
                                        This may take 15-30 seconds
                                    </p>

                                    {/* Progress Stages */}
                                    <div className="space-y-3 max-w-md mx-auto">
                                        {LOADING_STAGES.map((stage, index) => (
                                            <motion.div
                                                key={stage}
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{
                                                    opacity: index <= currentStage ? 1 : 0.3,
                                                    x: 0
                                                }}
                                                className="flex items-center gap-3"
                                            >
                                                {index < currentStage ? (
                                                    <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
                                                        <div className="w-2 h-2 bg-white rounded-full" />
                                                    </div>
                                                ) : index === currentStage ? (
                                                    <Loader2 className="w-5 h-5 text-violet-500 animate-spin" />
                                                ) : (
                                                    <div className="w-5 h-5 rounded-full border-2 border-slate-700" />
                                                )}
                                                <span className={`text-sm ${index <= currentStage ? 'text-white' : 'text-slate-600'}`}>
                                                    {stage}
                                                </span>
                                            </motion.div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* History Sidebar */}
                <AnimatePresence>
                    {showHistory && (
                        <PreparationHistory
                            onSelect={handleLoadPreparation}
                            onClose={() => setShowHistory(false)}
                        />
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
