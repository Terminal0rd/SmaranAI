/**
 * Tabs Component
 * Tab navigation system for organizing content
 */
import React, { createContext, useContext, useState } from 'react';

interface TabsContextType {
    value: string;
    onValueChange: (value: string) => void;
}

const TabsContext = createContext<TabsContextType | undefined>(undefined);

interface TabsProps {
    value: string;
    onValueChange: (value: string) => void;
    children: React.ReactNode;
    className?: string;
}

export function Tabs({ value, onValueChange, children, className = '' }: TabsProps) {
    return (
        <TabsContext.Provider value={{ value, onValueChange }}>
            <div className={`w-full ${className}`}>
                {children}
            </div>
        </TabsContext.Provider>
    );
}

interface TabsListProps {
    children: React.ReactNode;
    className?: string;
}

export function TabsList({ children, className = '' }: TabsListProps) {
    return (
        <div className={`inline-flex items-center justify-center rounded-lg bg-slate-800/50 p-1 ${className}`}>
            {children}
        </div>
    );
}

interface TabsTriggerProps {
    value: string;
    children: React.ReactNode;
    className?: string;
}

export function TabsTrigger({ value, children, className = '' }: TabsTriggerProps) {
    const context = useContext(TabsContext);
    if (!context) throw new Error('TabsTrigger must be used within Tabs');

    const isActive = context.value === value;

    return (
        <button
            onClick={() => context.onValueChange(value)}
            className={`
                inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium
                transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500
                disabled:pointer-events-none disabled:opacity-50
                ${isActive
                    ? 'bg-violet-600 text-white shadow-sm'
                    : 'text-slate-400 hover:bg-slate-700/50 hover:text-white'
                }
                ${className}
            `}
        >
            {children}
        </button>
    );
}

interface TabsContentProps {
    value: string;
    children: React.ReactNode;
    className?: string;
}

export function TabsContent({ value, children, className = '' }: TabsContentProps) {
    const context = useContext(TabsContext);
    if (!context) throw new Error('TabsContent must be used within Tabs');

    if (context.value !== value) return null;

    return (
        <div className={`mt-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 ${className}`}>
            {children}
        </div>
    );
}
