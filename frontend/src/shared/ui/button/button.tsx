import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  icon,
  className = '',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors rounded-lg px-4 py-2 text-sm focus:outline-none disabled:opacity-50';
  
  const variants = {
    primary: 'bg-[#cc1f14] hover:bg-[#d03b2c] text-white shadow-sm dark:bg-[#b0170e] dark:hover:bg-[#cc1f14]',
    secondary: 'bg-slate-100 hover:bg-slate-200 text-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200',
    outline: 'border border-slate-300 hover:bg-slate-50 text-slate-700 dark:border-slate-700 dark:hover:bg-slate-800/80 dark:text-slate-200',
    ghost: 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
  };

  return (
    <button className={`${baseStyles} ${variants[variant]} ${className}`} {...props}>
      {icon && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
};