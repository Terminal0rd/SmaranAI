// Conversational Teaching Page
// frontend/src/app/(protected)/teacher-mode/[roadmapId]/[moduleId]/teach/page.tsx

"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";

interface Message {
    speaker: "ai" | "student";
    text: string;
    concept?: string;
}

interface Progress {
    current: number;
    total: number;
    concepts: string[];
    mastery_scores?: Record<string, number>;
}

export default function ConversationalTeachingPage() {
    const params = useParams();
    const router = useRouter();
    const roadmapId = params.roadmapId as string;
    const moduleId = params.moduleId as string;

    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState<Progress | null>(null);
    const [allDone, setAllDone] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Start teaching session
    useEffect(() => {
        startTeaching();
    }, []);

    const startTeaching = async () => {
        try {
            const response = await axios.post(
                `/api/teacher/roadmap/${roadmapId}/module/${moduleId}/teach/start`
            );

            setMessages([
                {
                    speaker: "ai",
                    text: response.data.message,
                    concept: response.data.current_concept,
                },
            ]);
            setProgress(response.data.progress);
        } catch (error) {
            console.error("Failed to start teaching:", error);
        }
    };

    const sendMessage = async () => {
        if (!input.trim() || loading) return;

        const studentMessage = input.trim();
        setInput("");
        setLoading(true);

        // Add student message
        setMessages((prev) => [
            ...prev,
            { speaker: "student", text: studentMessage },
        ]);

        try {
            const response = await axios.post(
                `/api/teacher/roadmap/${roadmapId}/module/${moduleId}/teach/respond`,
                { message: studentMessage }
            );

            // Add AI response
            setMessages((prev) => [
                ...prev,
                {
                    speaker: "ai",
                    text: response.data.message,
                    concept: response.data.current_concept,
                },
            ]);

            setProgress(response.data.progress);
            setAllDone(response.data.all_concepts_done);
        } catch (error) {
            console.error("Failed to send message:", error);
            setMessages((prev) => [
                ...prev,
                { speaker: "ai", text: "Sorry, I encountered an error. Try again?" },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const goToAssessment = () => {
        router.push(`/teacher-mode/${roadmapId}/${moduleId}/check`);
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header with Progress */}
            <div className="bg-white shadow px-6 py-4">
                <h1 className="text-2xl font-bold mb-2">AI Tutor Session</h1>
                {progress && (
                    <div>
                        <p className="text-sm text-gray-600 mb-2">
                            Concepts Mastered: {progress.current} / {progress.total}
                        </p>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                                className="bg-blue-600 h-2 rounded-full transition-all"
                                style={{
                                    width: `${(progress.current / progress.total) * 100}%`,
                                }}
                            />
                        </div>
                        <div className="flex gap-2 mt-2 flex-wrap">
                            {progress.concepts.map((concept, i) => {
                                const mastered =
                                    progress.mastery_scores &&
                                    progress.mastery_scores[concept] >= 0.7;
                                return (
                                    <span
                                        key={i}
                                        className={`px-2 py-1 rounded text-xs ${mastered
                                                ? "bg-green-100 text-green-800"
                                                : "bg-gray-100 text-gray-600"
                                            }`}
                                    >
                                        {mastered && "✓ "}
                                        {concept}
                                    </span>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-6">
                <div className="max-w-3xl mx-auto space-y-4">
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex ${msg.speaker === "student" ? "justify-end" : "justify-start"
                                }`}
                        >
                            <div
                                className={`max-w-[80%] rounded-lg px-4 py-3 ${msg.speaker === "student"
                                        ? "bg-blue-600 text-white ml-auto"
                                        : "bg-white shadow"
                                    }`}
                            >
                                <div className="flex items-start gap-2">
                                    <span className="text-xl">
                                        {msg.speaker === "ai" ? "🤖" : "👤"}
                                    </span>
                                    <p className="whitespace-pre-wrap">{msg.text}</p>
                                </div>
                                {msg.concept && msg.speaker === "ai" && (
                                    <p className="text-xs text-gray-500 mt-2">
                                        Topic: {msg.concept}
                                    </p>
                                )}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-white shadow rounded-lg px-4 py-3">
                                <div className="flex items-center gap-2">
                                    <span className="text-xl">🤖</span>
                                    <p className="text-gray-500">Thinking...</p>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className="bg-white border-t px-6 py-4">
                <div className="max-w-3xl mx-auto">
                    {allDone ? (
                        <div className="text-center">
                            <p className="text-lg font-semibold text-green-600 mb-4">
                                🎉 All concepts covered! You're ready for the assessment.
                            </p>
                            <button
                                onClick={goToAssessment}
                                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700"
                            >
                                Take Assessment
                            </button>
                        </div>
                    ) : (
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                                placeholder="Type your answer or question..."
                                className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                disabled={loading}
                            />
                            <button
                                onClick={sendMessage}
                                disabled={loading || !input.trim()}
                                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Send
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
