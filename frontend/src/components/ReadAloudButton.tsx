/**
 * Read Aloud Button Component
 * On-demand audio generation for AI responses
 */
'use client';

import { useState } from 'react';
import { Volume2, VolumeX, Loader2 } from 'lucide-react';
import axios from 'axios';

interface ReadAloudButtonProps {
    messageId: string;
    messageContent: string;
    className?: string;
}

export function ReadAloudButton({ messageId, messageContent, className = '' }: ReadAloudButtonProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [audio, setAudio] = useState<HTMLAudioElement | null>(null);

    const handleReadAloud = async () => {
        // If already have audio, just play/pause
        if (audioUrl && audio) {
            if (isPlaying) {
                audio.pause();
                setIsPlaying(false);
            } else {
                audio.play();
                setIsPlaying(true);
            }
            return;
        }

        // Generate audio
        setIsLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await axios.post(
                `http://localhost:8000/api/chat/read-aloud/${messageId}`,
                {},
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            const newAudioUrl = response.data.audio_url;
            setAudioUrl(newAudioUrl);

            // Create and play audio
            const newAudio = new Audio(`http://localhost:8000${newAudioUrl}`);
            newAudio.onended = () => setIsPlaying(false);
            newAudio.onplay = () => setIsPlaying(true);
            newAudio.onpause = () => setIsPlaying(false);

            setAudio(newAudio);
            newAudio.play();
            setIsPlaying(true);
        } catch (error) {
            console.error('Read aloud failed:', error);
            alert('Failed to generate audio. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <button
            onClick={handleReadAloud}
            disabled={isLoading}
            className={`flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition-colors ${isPlaying
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                } disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
            title="Read aloud"
        >
            {isLoading ? (
                <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                </>
            ) : isPlaying ? (
                <>
                    <VolumeX className="w-4 h-4" />
                    Playing...
                </>
            ) : (
                <>
                    <Volume2 className="w-4 h-4" />
                    Read Aloud
                </>
            )}
        </button>
    );
}
