import { describe, it, expect } from 'vitest';
import { hasNoCriticalViolations } from './a11y';

describe('a11y placeholder', () => {
  it('hasNoCriticalViolations returns true for clean placeholder', () => {
    expect(hasNoCriticalViolations([])).toBe(true);
  });

  it('detects critical violations', () => {
    expect(hasNoCriticalViolations([{ impact: 'critical' }])).toBe(false);
    expect(hasNoCriticalViolations([{ impact: 'serious' }])).toBe(false);
  });

  it('ignores minor violations', () => {
    expect(hasNoCriticalViolations([{ impact: 'minor' }, { impact: 'moderate' }])).toBe(true);
  });
});
