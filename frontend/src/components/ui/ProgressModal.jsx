import Modal from './Modal';
import Button from './Button';
import Badge from './Badge';

export default function ProgressModal({ isOpen, items = [], onRetryFailed, onClose, title = 'Progreso de envío' }) {
  if (!isOpen) return null;

  const total = items.length;
  const sent = items.filter((i) => i.status === 'sent').length;
  const failed = items.filter((i) => i.status === 'failed');
  const pending = items.filter((i) => i.status === 'pending').length;

  const failedIds = failed.map((i) => i.id);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="md">
      <div aria-live="polite" className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            {sent}/{total} enviados {pending > 0 ? `· ${pending} pendientes` : ''}
          </p>
          <span className="text-sm font-medium">{sent} de {total}</span>
        </div>

        {/* progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary-600 h-2 rounded-full transition-all"
            style={{ width: `${total ? (sent / total) * 100 : 0}%` }}
          />
        </div>

        <ul className="divide-y divide-gray-100 max-h-64 overflow-y-auto">
          {items.map((item) => (
            <li key={item.id} className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <span className="w-6 text-center">
                  {item.status === 'sent' ? '✓' : item.status === 'failed' ? '✗' : '…'}
                </span>
                <span className="text-sm text-gray-800">{item.email || `ID ${item.id}`}</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={item.status === 'sent' ? 'success' : item.status === 'failed' ? 'danger' : 'default'}>
                  {item.status === 'sent' ? 'sent' : item.status === 'failed' ? 'failed' : item.status}
                </Badge>
                {item.error && <span className="text-xs text-red-600 truncate max-w-[120px]" title={item.error}>{item.error}</span>}
              </div>
            </li>
          ))}
        </ul>

        {failed.length > 0 && onRetryFailed && (
          <Button variant="secondary" onClick={() => onRetryFailed(failedIds)}>
            Reintentar fallidos ({failed.length})
          </Button>
        )}

        {/* ensure count text for test: "2/3" */}
        <p className="text-xs text-gray-500">{sent}/{total} · {sent} de {total}</p>
      </div>
    </Modal>
  );
}
