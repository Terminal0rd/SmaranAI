/**
 * Session Store using Zustand
 */
import { create } from 'zustand';
import { Session, Message, Subject } from './api';

interface SessionState {
    currentSession: Session | null;
    messages: Message[];
    subjects: Subject[];
    selectedSubject: Subject | null;
    isLoading: boolean;

    // Actions
    setCurrentSession: (session: Session | null) => void;
    setMessages: (messages: Message[]) => void;
    addMessage: (message: Message) => void;
    setSubjects: (subjects: Subject[]) => void;
    setSelectedSubject: (subject: Subject | null) => void;
    setLoading: (loading: boolean) => void;
    clearSession: () => void;
}

export const useSessionStore = create<SessionState>()((set) => ({
    currentSession: null,
    messages: [],
    subjects: [],
    selectedSubject: null,
    isLoading: false,

    setCurrentSession: (session) => set({ currentSession: session }),

    setMessages: (messages) => set({ messages }),

    addMessage: (message) => set((state) => ({
        messages: [...state.messages, message]
    })),

    setSubjects: (subjects) => set({ subjects }),

    setSelectedSubject: (subject) => set({ selectedSubject: subject }),

    setLoading: (isLoading) => set({ isLoading }),

    clearSession: () => set({
        currentSession: null,
        messages: [],
        selectedSubject: null
    }),
}));
