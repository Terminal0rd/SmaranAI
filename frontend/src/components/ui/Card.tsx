/**
 * Card Component
 */
'use client';

import { HTMLAttributes, forwardRef } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '@/lib/utils';

interface CardProps extends HTMLMotionProps<'div'> {
    variant?: 'default' | 'gradient' | 'glass';
    hover?: boolean;
}

const variants = {
    default: 'bg-slate-800/50 border border-slate-700',
    gradient: 'bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700',
    glass: 'bg-slate-800/30 backdrop-blur-md border border-slate-700/50',
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
    ({ className, variant = 'default', hover = false, children, ...props }, ref) => {
        return (
            <motion.div
                ref={ref}
                whileHover={hover ? { y: -4, scale: 1.01 } : undefined}
                className={cn(
                    'rounded-xl p-6',
                    variants[variant],
                    hover && 'cursor-pointer transition-shadow hover:shadow-xl hover:shadow-violet-500/10',
                    className
                )}
                {...props}
            >
                {children}
            </motion.div>
        );
    }
);

Card.displayName = 'Card';

export const CardHeader = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
    <div className={cn('mb-4', className)} {...props} />
);

export const CardTitle = ({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) => (
    <h3 className={cn('text-xl font-semibold text-white', className)} {...props} />
);

export const CardDescription = ({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) => (
    <p className={cn('text-sm text-slate-400 mt-1', className)} {...props} />
);

export const CardContent = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
    <div className={cn('', className)} {...props} />
);
