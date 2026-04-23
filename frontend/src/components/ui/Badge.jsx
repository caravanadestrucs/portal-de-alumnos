export default function Badge({
  children,
  variant = 'default',
  className = '',
}) {
  const variants = {
    default: 'bg-gray-100 text-gray-700',
    success: 'badge-success',
    warning: 'badge-warning',
    danger: 'badge-danger',
    info: 'bg-blue-100 text-blue-700',
  };

  return (
    <span className={`${variants[variant]} ${className}`}>
      {children}
    </span>
  );
}
