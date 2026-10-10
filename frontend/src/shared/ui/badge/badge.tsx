import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'warning' | 'info' | 'dark';
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'info' }) => {
  const variants = {
    success: 'bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-400 dark:border-emerald-800/60',
    warning: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-400 dark:border-amber-800/60',
    info: 'bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-800/60',
    dark: 'bg-slate-800 text-white border-transparent dark:bg-slate-200 dark:text-slate-900',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium border ${variants[variant]}`}>
      {children}
    </span>
  );
};