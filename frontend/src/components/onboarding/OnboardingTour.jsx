import { useState, useEffect, useRef } from 'react';
import { BookOpen, CreditCard, GraduationCap, X } from 'lucide-react';

const STORAGE_KEY = 'onboarding_seen_v1';

const STEPS = [
  {
    id: 1,
    title: 'Tus calificaciones',
    description: 'Consulta tu historial académico, promedios y estado de cada materia en un solo lugar.',
    icon: BookOpen,
    target: 'calificaciones',
  },
  {
    id: 2,
    title: 'Pagos',
    description: 'Revisa tu estado de cuenta, pagos pendientes y fechas límite para evitar recargos.',
    icon: CreditCard,
    target: 'pagos',
  },
  {
    id: 3,
    title: 'Requisitos',
    description: 'Sigue tu avance en prácticas profesionales y requisitos de titulación paso a paso.',
    icon: GraduationCap,
    target: 'requisitos',
  },
];

export const ONBOARDING_STORAGE_KEY = STORAGE_KEY;
export const ONBOARDING_STEPS = STEPS;

export function shouldShowOnboarding(user) {
  if (typeof window === 'undefined') return false;
  if (user?.rol !== 'alumno') return false;
  return !localStorage.getItem(STORAGE_KEY);
}

export function persistOnboardingSeen() {
  localStorage.setItem(STORAGE_KEY, 'true');
}

export default function OnboardingTour({ isOpen, onComplete, onSkip, onClose }) {
  const [step, setStep] = useState(0);
  const dialogRef = useRef(null);
  const nextBtnRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    setStep(0);
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    // focus management: focus dialog or next button
    const t = setTimeout(() => {
      if (nextBtnRef.current) nextBtnRef.current.focus();
      else dialogRef.current?.focus();
    }, 30);
    const handleEsc = (e) => {
      if (e.key === 'Escape') handleSkip();
    };
    document.addEventListener('keydown', handleEsc);
    return () => {
      clearTimeout(t);
      document.removeEventListener('keydown', handleEsc);
    };
  }, [isOpen, step]);

  if (!isOpen) return null;

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;
  const isFirst = step === 0;
  const Icon = current.icon;

  const handleNext = () => {
    if (isLast) {
      persistOnboardingSeen();
      onComplete?.();
      onClose?.();
    } else {
      setStep((s) => s + 1);
    }
  };

  const handlePrev = () => {
    if (!isFirst) setStep((s) => s - 1);
  };

  const handleSkip = () => {
    persistOnboardingSeen();
    onSkip?.();
    onClose?.();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={handleSkip} aria-hidden="true" />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="onboarding-title"
        tabIndex={-1}
        className="relative w-full max-w-lg glass rounded-2xl shadow-2xl p-6 animate-fadeIn outline-none"
      >
        <button
          onClick={handleSkip}
          aria-label="Cerrar tour"
          className="absolute top-3 right-3 p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <X size={18} className="text-gray-500" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg">
            <Icon size={24} className="text-white" />
          </div>
          <div>
            <p className="text-xs font-semibold text-primary-600 uppercase tracking-wide">
              Paso {step + 1} de {STEPS.length}
            </p>
            <h2 id="onboarding-title" className="text-xl font-bold text-gray-800">
              {current.title}
            </h2>
          </div>
        </div>

        <p className="text-sm text-gray-600 mb-6 leading-relaxed">{current.description}</p>

        <div className="flex items-center justify-center gap-1.5 mb-6">
          {STEPS.map((_, idx) => (
            <span
              key={idx}
              className={`h-2 rounded-full transition-all ${idx === step ? 'w-8 bg-primary-600' : idx < step ? 'w-2 bg-primary-300' : 'w-2 bg-gray-200'}`}
              aria-hidden="true"
            />
          ))}
        </div>

        <div className="flex items-center justify-between gap-3">
          <button
            onClick={handleSkip}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
          >
            Saltar tour
          </button>
          <div className="flex items-center gap-2">
            {!isFirst && (
              <button
                onClick={handlePrev}
                className="px-4 py-2 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Anterior
              </button>
            )}
            <button
              ref={nextBtnRef}
              onClick={handleNext}
              className="px-6 py-2 rounded-xl bg-primary-600 text-white text-sm font-semibold hover:bg-primary-700 transition-colors shadow"
            >
              {isLast ? 'Finalizar' : 'Siguiente'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
