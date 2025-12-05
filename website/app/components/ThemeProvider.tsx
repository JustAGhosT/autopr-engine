'use client';

import { createContext, useContext, useEffect, useState, useLayoutEffect } from 'react';

type Theme = 'light' | 'dark' | 'system';

const VALID_THEMES: Theme[] = ['light', 'dark', 'system'];

function isValidTheme(value: string | null): value is Theme {
  return value !== null && VALID_THEMES.includes(value as Theme);
}

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

interface ThemeProviderProps {
  children: React.ReactNode;
}

// Use useLayoutEffect on client, useEffect on server (to avoid warnings)
const useIsomorphicLayoutEffect = typeof window !== 'undefined' ? useLayoutEffect : useEffect;

// Helper to get system preference
function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>('system');
  const [mounted, setMounted] = useState(false);

  // Compute resolved theme based on current theme setting
  const resolvedTheme: 'light' | 'dark' = theme === 'system' ? getSystemTheme() : theme;

  // Initialize theme from localStorage on mount
  useIsomorphicLayoutEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (isValidTheme(savedTheme)) {
      setThemeState(savedTheme);
    }
    setMounted(true);
  }, []);

  // Apply theme class to document - this is a DOM side effect, not state
  useEffect(() => {
    if (!mounted) return;

    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(resolvedTheme);
  }, [resolvedTheme, mounted]);

  // Listen for system theme changes when in system mode
  useEffect(() => {
    if (!mounted || theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handler = () => {
      // Force re-render to update resolvedTheme
      setThemeState('system');
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [theme, mounted]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return (
      <ThemeContext.Provider value={{ theme: 'system', setTheme, resolvedTheme: 'light' }}>
        {children}
      </ThemeContext.Provider>
    );
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
