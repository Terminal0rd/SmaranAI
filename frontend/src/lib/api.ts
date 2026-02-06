/**
 * API Client for SmaranAI Backend
 */
import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true,
});

// Request interceptor to add auth token
api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Clear token and redirect to login
            if (typeof window !== 'undefined') {
                localStorage.removeItem('token');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

// Auth API
export const authAPI = {
    register: (data: RegisterData) => api.post('/api/auth/register', data),
    login: (email: string, password: string) => {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        return api.post('/api/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
    },
    getMe: () => api.get('/api/auth/me'),
    updateProfile: (data: Partial<User>) => api.put('/api/auth/profile', data),
};

// Subjects API
export const subjectsAPI = {
    getAll: () => api.get('/api/subjects'),
    getRecommended: () => api.get('/api/subjects/recommended'),
    create: (data: { name: string; description?: string; icon?: string }) =>
        api.post('/api/subjects', data),
    getById: (id: string) => api.get(`/api/subjects/${id}`),
};

// Sessions API
export const sessionsAPI = {
    getAll: (subjectId?: string) =>
        api.get('/api/sessions', { params: subjectId ? { subject_id: subjectId } : {} }),
    getLatest: () => api.get('/api/sessions/latest'),
    create: (data: { subject_id: string; title?: string }) => api.post('/api/sessions', data),
    getById: (id: string) => api.get(`/api/sessions/${id}`),
    update: (id: string, data: { title?: string; is_active?: boolean }) =>
        api.put(`/api/sessions/${id}`, data),
    getConcepts: (id: string) => api.get(`/api/sessions/${id}/concepts`),
};

// Chat API
export const chatAPI = {
    sendMessage: (sessionId: string, message: string) =>
        api.post('/api/chat', { session_id: sessionId, message }),
    getYouTubeRecommendations: (topic: string, subjectId: string) =>
        api.get('/api/chat/youtube-recommend', { params: { topic, subject_id: subjectId } }),
};

// MindMap API
export const mindmapAPI = {
    get: (subjectId: string) => api.get(`/api/mindmap/${subjectId}`),
    getWeakNodes: (subjectId: string) => api.get(`/api/mindmap/${subjectId}/weak-nodes`),
    updateNode: (nodeId: string, data: { x_position?: number; y_position?: number; mastery_level?: number }) =>
        api.put(`/api/mindmap/node/${nodeId}`, data),
};

// Quiz API
export const quizAPI = {
    generate: (sessionId: string, numQuestions?: number, questionTypes?: string[]) =>
        api.post('/api/quiz/generate', {
            session_id: sessionId,
            num_questions: numQuestions || 5,
            question_types: questionTypes || ['mcq', 'true_false', 'short_answer'],
        }),
    submit: (attemptId: string, answers: { question_id: string; answer: string }[]) =>
        api.post('/api/quiz/submit', { attempt_id: attemptId, answers }),
    getHistory: (subjectId?: string) =>
        api.get('/api/quiz/history', { params: subjectId ? { subject_id: subjectId } : {} }),
    getResult: (attemptId: string) => api.get(`/api/quiz/${attemptId}`),
};

// Progress API
export const progressAPI = {
    getOverall: () => api.get('/api/progress'),
    getDashboard: () => api.get('/api/progress/dashboard'),
    getBySubject: (subjectId: string) => api.get(`/api/progress/${subjectId}`),
};

// Documents API
export const documentsAPI = {
    upload: (file: File, subjectId: string) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('subject_id', subjectId);
        return api.post('/api/documents/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
    getAll: (subjectId?: string) =>
        api.get('/api/documents', { params: subjectId ? { subject_id: subjectId } : {} }),
    getStatus: (documentId: string) => api.get(`/api/documents/${documentId}/status`),
    delete: (documentId: string) => api.delete(`/api/documents/${documentId}`),
};

// Export API
export const exportAPI = {
    downloadPDF: (sessionId: string) =>
        api.get(`/api/export/${sessionId}/pdf`, { responseType: 'blob' }),
    downloadPPTX: (sessionId: string) =>
        api.get(`/api/export/${sessionId}/pptx`, { responseType: 'blob' }),
};

// LLM Status API
export const llmAPI = {
    getStatus: () => api.get('/api/llm/status'),
};

// Health API
export const healthAPI = {
    check: () => api.get('/health'),
};

// Types
export interface User {
    id: string;
    email: string;
    full_name: string;
    age?: number;
    class_standard?: string;
    branch_specialization?: string;
    learning_goal?: string;
    created_at: string;
    last_login?: string;
}

export interface RegisterData {
    email: string;
    password: string;
    full_name: string;
    age?: number;
    class_standard?: string;
    branch_specialization?: string;
    learning_goal?: string;
}

export interface Subject {
    id: string;
    name: string;
    description?: string;
    icon?: string;
    is_default: boolean;
    created_at: string;
}

export interface Session {
    id: string;
    user_id: string;
    subject_id: string;
    title?: string;
    summary?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    formatted_content?: string;
    sources_used?: { filename: string; chunk_preview: string }[];
    created_at: string;
}

export interface MindMapNode {
    id: string;
    label: string;
    description?: string;
    x_position: number;
    y_position: number;
    mastery_level: number;
    status: 'learning' | 'weak' | 'strong';
}

export interface MindMapEdge {
    id: string;
    source_node_id: string;
    target_node_id: string;
    relationship_type: string;
}

export interface QuizQuestion {
    id: string;
    question_type: 'mcq' | 'true_false' | 'short_answer';
    question_text: string;
    options?: string[];
    source_concept?: string;
}

export interface QuizResult {
    attempt_id: string;
    score: number;
    total_questions: number;
    correct_answers: number;
    weak_topics: string[];
    questions: {
        question_id: string;
        question_text: string;
        user_answer?: string;
        correct_answer: string;
        is_correct: boolean;
        source_concept?: string;
    }[];
}

// Teacher Mode API
export const teacherAPI = {
    createRoadmap: (data: { subject: string; goal?: string }) =>
        api.post('/api/teacher/roadmap/create', data),
    getAllRoadmaps: () =>
        api.get('/api/teacher/roadmap'),
    getRoadmap: (roadmapId: string) =>
        api.get(`/api/teacher/roadmap/${roadmapId}`),
    getModule: (roadmapId: string, moduleId: string) =>
        api.get(`/api/teacher/roadmap/${roadmapId}/module/${moduleId}`),
    generateTeach: (roadmapId: string, moduleId: string) =>
        api.post(`/api/teacher/roadmap/${roadmapId}/module/${moduleId}/teach`),
    generateCheck: (roadmapId: string, moduleId: string) =>
        api.post(`/api/teacher/roadmap/${roadmapId}/module/${moduleId}/check/generate`),
    submitCheck: (roadmapId: string, moduleId: string, answers: any[]) =>
        api.post(`/api/teacher/roadmap/${roadmapId}/module/${moduleId}/check/submit`, { answers }),
    generateReteach: (roadmapId: string, moduleId: string, weakTopics: string[]) =>
        api.post(`/api/teacher/roadmap/${roadmapId}/module/${moduleId}/reteach`, { weak_topics: weakTopics }),
    getMemoryCards: (roadmapId: string, moduleId: string) =>
        api.get(`/api/teacher/roadmap/${roadmapId}/module/${moduleId}/memory-cards`),
};

export default api;
