import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui';
import { useTheme } from '../contexts/ThemeContext';

interface ThemeToggleProps {
  showLabel?: boolean;
}

export function ThemeToggle({ showLabel = false }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme();

  if (showLabel) {
    return (
      <Button
        variant="ghost"
        onClick={toggleTheme}
        aria-label="Toggle theme"
        className="w-full justify-start gap-3 px-3 py-2 h-auto"
      >
        {theme === 'light' ? (
          <Moon className="h-5 w-5" />
        ) : (
          <Sun className="h-5 w-5" />
        )}
        <span className="text-sm">{theme === 'light' ? 'Dark Mode' : 'Light Mode'}</span>
      </Button>
    );
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label="Toggle theme"
    >
      {theme === 'light' ? (
        <Moon className="h-5 w-5" />
      ) : (
        <Sun className="h-5 w-5" />
      )}
    </Button>
  );
}
