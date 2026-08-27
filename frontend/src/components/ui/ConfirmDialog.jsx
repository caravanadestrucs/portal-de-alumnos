import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import Button from './Button';

export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title = '¿Estás seguro?',
  message,
  impactSummary,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  variant = 'danger',
  requireConfirmText,
  isLoading = false,
}) {
  const [typed, setTyped] = useState('');

  const canConfirm = requireConfirmText ? typed === requireConfirmText : true;

  useEffect(() => {
    if (!isOpen) setTyped('');
  }, [isOpen]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="md"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            {cancelText}
          </Button>
          <Button
            variant={variant === 'danger' ? 'danger' : 'primary'}
            onClick={onConfirm}
            disabled={!canConfirm || isLoading}
            loading={isLoading}
          >
            {isLoading ? 'Procesando...' : confirmText}
          </Button>
        </>
      }
    >
      {message && <p className="text-gray-700">{message}</p>}
      {impactSummary && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm font-medium text-red-800">Impacto:</p>
          <p className="text-sm text-red-700">{impactSummary}</p>
        </div>
      )}
      {requireConfirmText && (
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-2">
            Escribí <strong>{requireConfirmText}</strong> para confirmar:
          </p>
          <input
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            placeholder={requireConfirmText}
            className="w-full px-4 py-2.5 rounded-xl input-glass"
            autoComplete="off"
          />
        </div>
      )}
    </Modal>
  );
}
