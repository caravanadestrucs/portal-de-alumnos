export default function Card({
  children,
  title,
  subtitle,
  action,
  className = '',
  hover = true,
  gradient = false,
  ...props
}) {
  return (
    <div
      className={`
        glass p-6
        ${hover ? 'card-hover' : ''}
        ${className}
      `}
      {...props}
    >
      {(title || action) && (
        <div className="flex items-center justify-between mb-4">
          <div>
            {title && (
              <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-500">{subtitle}</p>
            )}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
