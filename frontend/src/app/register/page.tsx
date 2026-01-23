/**
 * Register Page
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Brain, Mail, Lock, User, GraduationCap, Target, Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';
import { Button, Input } from '@/components/ui';
import { useAuthStore } from '@/lib/auth-store';

const learningGoals = [
    { value: 'exam', label: 'Exam Preparation', icon: '📚' },
    { value: 'understanding', label: 'Deep Understanding', icon: '🧠' },
    { value: 'projects', label: 'Build Projects', icon: '🚀' },
];

export default function RegisterPage() {
    const router = useRouter();
    const { register, isLoading } = useAuthStore();
    const [showPassword, setShowPassword] = useState(false);
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        full_name: '',
        age: '',
        class_standard: '',
        branch_specialization: '',
        learning_goal: '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (step === 1) {
            setStep(2);
            return;
        }

        try {
            await register({
                ...formData,
                age: formData.age ? parseInt(formData.age) : undefined,
            });
            toast.success('Account created successfully!');
            router.push('/dashboard');
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Registration failed');
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md"
            >
                {/* Logo */}
                <Link href="/" className="flex items-center justify-center gap-2 mb-8">
                    <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-xl flex items-center justify-center">
                        <Brain className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-2xl font-bold bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent">
                        SmaranAI
                    </span>
                </Link>

                {/* Card */}
                <div className="bg-slate-800/50 backdrop-blur-md rounded-2xl border border-slate-700 p-8">
                    <h1 className="text-2xl font-bold text-white text-center mb-2">
                        {step === 1 ? 'Create Account' : 'Tell Us About You'}
                    </h1>
                    <p className="text-slate-400 text-center mb-6">
                        {step === 1 ? 'Start your learning journey' : 'Help us personalize your experience'}
                    </p>

                    {/* Progress */}
                    <div className="flex gap-2 mb-8">
                        <div className={`h-1 flex-1 rounded-full ${step >= 1 ? 'bg-violet-500' : 'bg-slate-700'}`} />
                        <div className={`h-1 flex-1 rounded-full ${step >= 2 ? 'bg-violet-500' : 'bg-slate-700'}`} />
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {step === 1 ? (
                            <>
                                <Input
                                    label="Full Name"
                                    placeholder="John Doe"
                                    icon={<User className="w-5 h-5" />}
                                    value={formData.full_name}
                                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                    required
                                />

                                <Input
                                    label="Email"
                                    type="email"
                                    placeholder="you@example.com"
                                    icon={<Mail className="w-5 h-5" />}
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    required
                                />

                                <div className="relative">
                                    <Input
                                        label="Password"
                                        type={showPassword ? 'text' : 'password'}
                                        placeholder="••••••••"
                                        icon={<Lock className="w-5 h-5" />}
                                        value={formData.password}
                                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                        required
                                        minLength={6}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-9 text-slate-400 hover:text-white"
                                    >
                                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="grid grid-cols-2 gap-4">
                                    <Input
                                        label="Age"
                                        type="number"
                                        placeholder="18"
                                        value={formData.age}
                                        onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                                        min={5}
                                        max={100}
                                    />
                                    <Input
                                        label="Class/Standard"
                                        placeholder="B.Tech 3rd Year"
                                        icon={<GraduationCap className="w-5 h-5" />}
                                        value={formData.class_standard}
                                        onChange={(e) => setFormData({ ...formData, class_standard: e.target.value })}
                                    />
                                </div>

                                <Input
                                    label="Branch/Specialization"
                                    placeholder="Computer Science"
                                    value={formData.branch_specialization}
                                    onChange={(e) => setFormData({ ...formData, branch_specialization: e.target.value })}
                                />

                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-3">
                                        Learning Goal
                                    </label>
                                    <div className="grid grid-cols-1 gap-2">
                                        {learningGoals.map((goal) => (
                                            <button
                                                key={goal.value}
                                                type="button"
                                                onClick={() => setFormData({ ...formData, learning_goal: goal.value })}
                                                className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${formData.learning_goal === goal.value
                                                        ? 'border-violet-500 bg-violet-500/10 text-white'
                                                        : 'border-slate-700 bg-slate-800/50 text-slate-400 hover:border-slate-600'
                                                    }`}
                                            >
                                                <span className="text-xl">{goal.icon}</span>
                                                <span className="font-medium">{goal.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}

                        <div className="flex gap-3">
                            {step === 2 && (
                                <Button
                                    type="button"
                                    variant="outline"
                                    className="flex-1"
                                    onClick={() => setStep(1)}
                                >
                                    Back
                                </Button>
                            )}
                            <Button
                                type="submit"
                                className="flex-1"
                                isLoading={isLoading}
                            >
                                {step === 1 ? 'Continue' : 'Create Account'}
                            </Button>
                        </div>
                    </form>

                    <p className="mt-6 text-center text-slate-400 text-sm">
                        Already have an account?{' '}
                        <Link href="/login" className="text-violet-400 hover:text-violet-300 font-medium">
                            Sign in
                        </Link>
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
