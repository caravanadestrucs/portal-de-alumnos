import { useState, useEffect } from 'react';
export function useSidebarCollapsed() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebarCollapsed') === 'true');
  useEffect(() => localStorage.setItem('sidebarCollapsed', String(collapsed)), [collapsed]);
  return [collapsed, setCollapsed];
}
