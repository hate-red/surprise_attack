import React from 'react';

export const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => {
  return (
    <div className={`bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm dark:shadow-none p-5 ${className}`}>
      {children}
    </div>
  );
};