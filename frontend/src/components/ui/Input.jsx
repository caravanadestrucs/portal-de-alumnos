import { forwardRef, useId } from 'react';

const Input = forwardRef(({ label, error, helper, type = 'text', className = '', id, required, ...props }, ref) => {
  const autoId = useId();
  const inputId = id || `input-${autoId}`;
  const errorId = `${inputId}-error`;
  const helperId = `${inputId}-helper`;
  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1.5">
          {label}{required && <span className="text-red-500 ml-1" aria-hidden="true">*</span>}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        type={type}
        required={required}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : helper ? helperId : undefined}
        className={`w-full px-4 py-2.5 rounded-xl input-glass ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : ''} ${className}`}
        {...props}
      />
      {error && <p id={errorId} role="alert" className="mt-1 text-sm text-red-500">{error}</p>}
      {helper && !error && <p id={helperId} className="mt-1 text-sm text-gray-500">{helper}</p>}
    </div>
  );
});
Input.displayName = 'Input';
export default Input;
