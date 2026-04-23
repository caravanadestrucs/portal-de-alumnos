import { Loader2 } from 'lucide-react';

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  className = '',
  type = 'button',
  ...props
}) {
  const baseClasses = 'font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2';

  const variants = {
    primary: 'btn-gradient shadow-md hover:shadow-lg',
    secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300',
    danger: 'bg-red-500 text-white hover:bg-red-600 shadow-md',
    outline: 'border-2 border-primary-500 text-primary-600 hover:bg-primary-50',
    ghost: 'text-primary-600 hover:bg-primary-50',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2.5 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const disabledClasses = disabled || loading ? 'opacity-50 cursor-not-allowed' : '';

  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${disabledClasses} ${className}`}
      {...props}
    >
      {loading && <Loader2 className="animate-spin" size={18} />}
      {children}
    </button>
  );
}
