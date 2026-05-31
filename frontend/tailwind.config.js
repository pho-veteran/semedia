export default {
  darkMode: ['class', '[data-theme="dark"]'],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        display: ['Inter', 'sans-serif'],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        success: {
          DEFAULT: "hsl(var(--success))",
          foreground: "hsl(var(--success-foreground))",
        },
        warning: {
          DEFAULT: "hsl(var(--warning))",
          foreground: "hsl(var(--warning-foreground))",
        },
        info: {
          DEFAULT: "hsl(var(--info))",
          foreground: "hsl(var(--info-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        surface: {
          DEFAULT: "hsl(var(--surface))",
          elevated: "hsl(var(--surface-elevated))",
        },
        brand: {
          DEFAULT: "hsl(var(--brand))",
          foreground: "hsl(var(--brand-foreground))",
          muted: "hsl(var(--brand-muted))",
        },
      },
      borderRadius: {
        sm: "0.375rem",
        md: "calc(var(--radius))",
        lg: "0.75rem",
        xl: "1rem",
        '2xl': "1.5rem",
        '3xl': "2rem",
      },
      boxShadow: {
        'sm': "var(--shadow-sm)",
        'md': "var(--shadow-md)",
        'lg': "var(--shadow-lg)",
        'xl': "var(--shadow-xl)",
        'inner-sm': "inset 0 1px 2px 0 rgb(0 0 0 / 0.05)",
        'glow-brand': "0 0 24px -4px hsl(var(--brand) / 0.4)",
        'glow-sm': "0 0 12px -2px hsl(var(--brand) / 0.25)",
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, hsl(var(--brand)), hsl(var(--brand-muted)))',
        'gradient-surface': 'linear-gradient(180deg, hsl(var(--surface)), hsl(var(--surface-elevated)))',
        'gradient-mesh': 'radial-gradient(at 20% 20%, hsl(var(--brand) / 0.08) 0, transparent 50%), radial-gradient(at 80% 80%, hsl(var(--brand-muted) / 0.06) 0, transparent 50%)',
        'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E\")",
      },
      backdropBlur: {
        xs: '2px',
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
      zIndex: {
        base: "0",
        sidebar: "10",
        dropdown: "20",
        sticky: "30",
        overlay: "40",
        modal: "50",
        sheet: "60",
        toast: "70",
        tooltip: "80",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        fadeInUp: {
          from: { opacity: "0", transform: "translateY(12px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        fadeInScale: {
          from: { opacity: "0", transform: "scale(0.96)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        slideInFromLeft: {
          from: { opacity: "0", transform: "translateX(-16px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        slideInFromTop: {
          from: { transform: "translateY(-8px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 0 0 hsl(var(--brand) / 0)" },
          "50%": { boxShadow: "0 0 0 8px hsl(var(--brand) / 0.15)" },
        },
        spin: {
          to: { transform: "rotate(360deg)" },
        },
        statusPulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
      },
      animation: {
        'fade-in': 'fadeIn 200ms cubic-bezier(0.4, 0, 0.2, 1) both',
        'fade-in-up': 'fadeInUp 300ms cubic-bezier(0.16, 1, 0.3, 1) both',
        'fade-in-scale': 'fadeInScale 200ms cubic-bezier(0.34, 1.56, 0.64, 1) both',
        'slide-in-left': 'slideInFromLeft 250ms cubic-bezier(0.16, 1, 0.3, 1) both',
        'slide-in-top': 'slideInFromTop 200ms cubic-bezier(0.4, 0, 0.2, 1) both',
        'shimmer': 'shimmer 2s linear infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'status-pulse': 'statusPulse 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
