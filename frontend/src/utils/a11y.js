// Placeholder for axe-core integration
// TODO: Install axe-core and implement real check with axe.run(document)
// For now, stub that filters critical/serious violations
export function hasNoCriticalViolations(violations) {
  if (!Array.isArray(violations)) return true;
  return !violations.some((v) => v.impact === 'critical' || v.impact === 'serious');
}

// TODO S3: wire axe-core in Playwright or vitest-axe
// Example future: import { axe } from 'vitest-axe' and assert results.violations
