/**
 * Protected routes layout with auth check
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/auth-store';
import { Navbar } from '@/components/layout/Navbar';
import { Loader2 } from 'lucide-react';

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const { token, isAuthenticated, fetchUser } = useAuthStore();
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const checkAuth = async () => {
            const storedToken = localStorage.getItem('token');

            if (!storedToken) {
                router.push('/login');
                return;
            }

            if (!isAuthenticated) {
                try {
                    await fetchUser();
                } catch {
                    router.push('/login');
                    return;
                }
            }

            setIsLoading(false);
        };

        checkAuth();
    }, [isAuthenticated, fetchUser, router]);

    if (isLoading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-10 h-10 text-violet-500 animate-spin mx-auto mb-4" />
                    <p className="text-slate-400">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950">
            <Navbar />
            <main className="pt-16">
                {children}
            </main>
        </div>
    );
}
