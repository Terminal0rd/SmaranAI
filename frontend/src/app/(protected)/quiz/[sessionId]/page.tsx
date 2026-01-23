/**
 * Quiz Page
 */
'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, ArrowRight, CheckCircle, XCircle, Loader2, Trophy } from 'lucide-react';
import toast from 'react-hot-toast';
import { Button, Card, CardContent } from '@/components/ui';
import { quizAPI } from '@/lib/api';
import { cn } from '@/lib/utils';

export default function QuizPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = params.sessionId as string;

    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [attemptId, setAttemptId] = useState<string | null>(null);
    const [questions, setQuestions] = useState<any[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [result, setResult] = useState<any>(null);

    useEffect(() => {
        const generateQuiz = async () => {
            try {
                const response = await quizAPI.generate(sessionId, 5);
                setAttemptId(response.data.attempt_id);
                setQuestions(response.data.questions);
            } catch (error) {
                toast.error('Failed to generate quiz');
                router.push(`/learn/${sessionId}`);
            } finally {
                setLoading(false);
            }
        };
        generateQuiz();
    }, [sessionId, router]);

    const currentQuestion = questions[currentIndex];

    const handleAnswer = (answer: string) => {
        setAnswers({ ...answers, [currentQuestion.id]: answer });
    };

    const handleNext = () => {
        if (currentIndex < questions.length - 1) {
            setCurrentIndex(currentIndex + 1);
        }
    };

    const handlePrev = () => {
        if (currentIndex > 0) {
            setCurrentIndex(currentIndex - 1);
        }
    };

    const handleSubmit = async () => {
        if (!attemptId) return;

        setSubmitting(true);
        try {
            const answerList = Object.entries(answers).map(([question_id, answer]) => ({
                question_id,
                answer,
            }));

            const response = await quizAPI.submit(attemptId, answerList);
            setResult(response.data);
        } catch (error) {
            toast.error('Failed to submit quiz');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-10 h-10 text-violet-500 animate-spin mx-auto mb-4" />
                    <p className="text-slate-400">Generating quiz...</p>
                </div>
            </div>
        );
    }

    // Result View
    if (result) {
        return (
            <div className="min-h-screen bg-slate-950 p-6">
                <div className="max-w-2xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="text-center mb-8"
                    >
                        <div className="w-24 h-24 mx-auto mb-4 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-full flex items-center justify-center">
                            <Trophy className="w-12 h-12 text-white" />
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2">Quiz Complete!</h1>
                        <p className="text-5xl font-bold text-violet-400 mb-4">
                            {Math.round(result.score)}%
                        </p>
                        <p className="text-slate-400">
                            {result.correct_answers} of {result.total_questions} correct
                        </p>
                    </motion.div>

                    {result.weak_topics?.length > 0 && (
                        <Card className="mb-6">
                            <CardContent>
                                <h3 className="text-white font-medium mb-3">Focus Areas</h3>
                                <div className="flex flex-wrap gap-2">
                                    {result.weak_topics.map((topic: string) => (
                                        <span
                                            key={topic}
                                            className="px-3 py-1 rounded-full text-sm bg-amber-500/10 text-amber-400"
                                        >
                                            {topic}
                                        </span>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    <div className="space-y-4">
                        {result.questions.map((q: any, i: number) => (
                            <Card key={q.question_id} variant={q.is_correct ? 'default' : 'default'}>
                                <CardContent className="flex items-start gap-4">
                                    <div className={`p-2 rounded-full ${q.is_correct ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                                        {q.is_correct ? (
                                            <CheckCircle className="w-5 h-5 text-green-500" />
                                        ) : (
                                            <XCircle className="w-5 h-5 text-red-500" />
                                        )}
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-white mb-2">{q.question_text}</p>
                                        {!q.is_correct && (
                                            <p className="text-sm text-slate-400">
                                                Correct answer: <span className="text-green-400">{q.correct_answer}</span>
                                            </p>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>

                    <div className="flex gap-4 mt-8">
                        <Button variant="outline" onClick={() => router.push(`/learn/${sessionId}`)} className="flex-1">
                            Back to Session
                        </Button>
                        <Button onClick={() => router.push('/dashboard')} className="flex-1">
                            Dashboard
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    // Quiz View
    return (
        <div className="min-h-screen bg-slate-950 p-6">
            <div className="max-w-2xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <Button variant="ghost" onClick={() => router.push(`/learn/${sessionId}`)}>
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Exit Quiz
                    </Button>
                    <span className="text-slate-400">
                        Question {currentIndex + 1} of {questions.length}
                    </span>
                </div>

                {/* Progress */}
                <div className="flex gap-1 mb-8">
                    {questions.map((_, i) => (
                        <div
                            key={i}
                            className={cn(
                                'h-2 flex-1 rounded-full transition-colors',
                                i === currentIndex
                                    ? 'bg-violet-500'
                                    : answers[questions[i]?.id]
                                        ? 'bg-violet-500/50'
                                        : 'bg-slate-700'
                            )}
                        />
                    ))}
                </div>

                {/* Question */}
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentIndex}
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -50 }}
                    >
                        <Card className="mb-6">
                            <CardContent>
                                <span className="text-xs text-violet-400 uppercase tracking-wider mb-2 block">
                                    {currentQuestion.question_type.replace('_', ' ')}
                                </span>
                                <h2 className="text-xl text-white font-medium">
                                    {currentQuestion.question_text}
                                </h2>
                            </CardContent>
                        </Card>

                        {/* Options */}
                        <div className="space-y-3">
                            {currentQuestion.question_type === 'mcq' && currentQuestion.options?.map((option: string, i: number) => (
                                <motion.button
                                    key={i}
                                    whileHover={{ scale: 1.01 }}
                                    whileTap={{ scale: 0.99 }}
                                    onClick={() => handleAnswer(option.charAt(0))}
                                    className={cn(
                                        'w-full p-4 rounded-xl text-left transition-all',
                                        answers[currentQuestion.id] === option.charAt(0)
                                            ? 'bg-violet-500/20 border-2 border-violet-500 text-white'
                                            : 'bg-slate-800/50 border-2 border-transparent hover:border-slate-700 text-slate-300'
                                    )}
                                >
                                    {option}
                                </motion.button>
                            ))}

                            {currentQuestion.question_type === 'true_false' && ['True', 'False'].map((option) => (
                                <motion.button
                                    key={option}
                                    whileHover={{ scale: 1.01 }}
                                    whileTap={{ scale: 0.99 }}
                                    onClick={() => handleAnswer(option)}
                                    className={cn(
                                        'w-full p-4 rounded-xl text-left transition-all',
                                        answers[currentQuestion.id] === option
                                            ? 'bg-violet-500/20 border-2 border-violet-500 text-white'
                                            : 'bg-slate-800/50 border-2 border-transparent hover:border-slate-700 text-slate-300'
                                    )}
                                >
                                    {option}
                                </motion.button>
                            ))}

                            {currentQuestion.question_type === 'short_answer' && (
                                <input
                                    type="text"
                                    placeholder="Type your answer..."
                                    value={answers[currentQuestion.id] || ''}
                                    onChange={(e) => handleAnswer(e.target.value)}
                                    className="w-full p-4 rounded-xl bg-slate-800/50 border-2 border-slate-700 text-white focus:border-violet-500 focus:outline-none"
                                />
                            )}
                        </div>
                    </motion.div>
                </AnimatePresence>

                {/* Navigation */}
                <div className="flex gap-4 mt-8">
                    <Button
                        variant="outline"
                        onClick={handlePrev}
                        disabled={currentIndex === 0}
                        className="flex-1"
                    >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Previous
                    </Button>

                    {currentIndex < questions.length - 1 ? (
                        <Button onClick={handleNext} className="flex-1">
                            Next
                            <ArrowRight className="w-4 h-4 ml-2" />
                        </Button>
                    ) : (
                        <Button
                            onClick={handleSubmit}
                            isLoading={submitting}
                            disabled={Object.keys(answers).length < questions.length}
                            className="flex-1"
                        >
                            Submit Quiz
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
}
