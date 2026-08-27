import Button from './Button';

export default function EmptyState({ icon: Icon, title, description, actionLabel, onAction }) {
  return (
    <div className="text-center py-12">
      {Icon && <Icon size={48} className="mx-auto text-gray-300 mb-4" />}
      {title && <p className="text-gray-500 font-medium">{title}</p>}
      {description && <p className="text-sm text-gray-400 mt-1">{description}</p>}
      {actionLabel && (
        <div className="mt-4">
          <Button onClick={onAction}>{actionLabel}</Button>
        </div>
      )}
    </div>
  );
}
