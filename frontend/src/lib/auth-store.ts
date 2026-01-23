/**
 * Auth Store using Zustand
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authAPI, User } from './api';

interface AuthState {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    isAuthenticated: boolean;

    // Actions
    setUser: (user: User | null) => void;
    setToken: (token: string | null) => void;
    login: (email: string, password: string) => Promise<void>;
    register: (data: any) => Promise<void>;
    logout: () => void;
    fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            user: null,
            token: null,
            isLoading: false,
            isAuthenticated: false,

            setUser: (user) => set({ user, isAuthenticated: !!user }),

            setToken: (token) => {
                if (token) {
                    localStorage.setItem('token', token);
                } else {
                    localStorage.removeItem('token');
                }
                set({ token });
            },

            login: async (email, password) => {
                set({ isLoading: true });
                try {
                    const response = await authAPI.login(email, password);
                    const { access_token } = response.data;
                    get().setToken(access_token);
                    await get().fetchUser();
                } catch (error) {
                    get().setToken(null);
                    throw error;
                } finally {
                    set({ isLoading: false });
                }
            },

            register: async (data) => {
                set({ isLoading: true });
                try {
                    const response = await authAPI.register(data);
                    const { access_token, user } = response.data;
                    get().setToken(access_token);
                    set({ user, isAuthenticated: true });
                } catch (error) {
                    throw error;
                } finally {
                    set({ isLoading: false });
                }
            },

            logout: () => {
                localStorage.removeItem('token');
                set({ user: null, token: null, isAuthenticated: false });
            },

            fetchUser: async () => {
                try {
                    const response = await authAPI.getMe();
                    set({ user: response.data, isAuthenticated: true });
                } catch {
                    get().logout();
                }
            },
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({ token: state.token }),
        }
    )
);
