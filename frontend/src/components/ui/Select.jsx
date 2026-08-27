import { useId } from 'react';

export default function Select({ label, error, helper, children, className = '', id, required, ...props }) {
  const autoId = useId();
  const selectId = id || `select-${autoId}`;
  const errorId = `${selectId}-error`;
  const helperId = `${selectId}-helper`;

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={selectId} className="block text-sm font-medium text-gray-700 mb-1.5">
          {label}
          {required && (
            <span className="text-red-500 ml-1" aria-hidden="true">
              *
            </span>
          )}
        </label>
      )}
      <select
        id={selectId}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : helper ? helperId : undefined}
        className={`w-full px-4 py-2.5 rounded-xl input-glass ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : ''} ${className}`}
        {...props}
      >
        {children}
      </select>
      {error && (
        <p id={errorId} role="alert" className="mt-1 text-sm text-red-500">
          {error}
        </p>
      )}
      {helper && !error && (
        <p id={helperId} className="mt-1 text-sm text-gray-500">
          {helper}
        </p>
      )}
    </div>
  );
}
