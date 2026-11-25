/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './api/templates/**/*.html',
    './api/static/**/*.js',
    './api/static/modules/**/*.js'
  ],
  safelist: [
    'toast-success',
    'toast-error',
    'toast-warning',
    'toast-info',
    'toast-hide',
    'active',
    'invalid',
    'loading',
    'blue',
    'green',
    'purple',
    'red',
    'orange',
    'is-tab-loading',
    // Dynamic classes from JS
    'bg-primary-50', 'bg-primary-100', 'bg-primary-500', 'bg-primary-600',
    'bg-success-50', 'bg-success-100', 'bg-success-500', 'bg-success-600',
    'bg-warning-50', 'bg-warning-100', 'bg-warning-500', 'bg-warning-600',
    'bg-danger-50', 'bg-danger-100', 'bg-danger-500', 'bg-danger-600',
    'bg-info-50', 'bg-info-100', 'bg-info-500', 'bg-info-600',
    'text-primary-600', 'text-primary-700', 'text-success-600', 'text-success-700',
    'text-warning-600', 'text-warning-700', 'text-danger-600', 'text-danger-700',
    'text-info-600', 'text-info-700',
    'border-primary-200', 'border-primary-300', 'border-success-200', 'border-success-300',
    'border-warning-200', 'border-warning-300', 'border-danger-200', 'border-danger-300',
    'border-info-200', 'border-info-300',
    'hover:bg-primary-50', 'hover:bg-success-50', 'hover:bg-warning-50', 'hover:bg-danger-50', 'hover:bg-info-50',
    'animate-fadeIn', 'animate-slideUp', 'animate-scaleIn', 'animate-shimmer',
    'badge-success', 'badge-warning', 'badge-danger', 'badge-info', 'badge-gray',
    'card-stats-warning', 'card-stats-danger', 'card-stats-hover',
    'btn-primary', 'btn-secondary', 'btn-success', 'btn-danger', 'btn-warning', 'btn-ghost', 'btn-outline',
    'btn-xs', 'btn-sm', 'btn-lg', 'btn-xl', 'btn-icon',
    'form-input', 'form-select', 'form-textarea', 'form-label', 'form-group',
    'modal-sm', 'modal-md', 'modal-lg', 'modal-xl'
  ],
  theme: {
    extend: {
      colors: {
        // Primary - Medical Teal/Emerald (Modern Clinic Theme)
        primary: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
          950: '#022c22',
          DEFAULT: '#059669',
          light: '#10b981',
          dark: '#047857',
          glow: 'rgba(16, 185, 129, 0.18)'
        },
        // Surface colors for cards/panels
        surface: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617'
        },
        // Semantic Colors
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
          DEFAULT: '#22c55e',
          light: '#dcfce7'
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
          DEFAULT: '#f59e0b',
          light: '#fef3c7'
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
          DEFAULT: '#ef4444',
          light: '#fee2e2'
        },
        info: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          DEFAULT: '#3b82f6',
          light: '#dbeafe'
        },
        // App-specific colors (backward compatibility)
        app: {
          primary: '#059669',
          'primary-light': '#10b981',
          'primary-dark': '#047857',
          warning: '#f59e0b',
          bg: '#f8fafc',
          card: '#ffffff',
          border: '#e2e8f0',
          text: '#0f172a',
          muted: '#64748b',
          sidebar: '#022c22'
        },
        // Legacy color aliases used in input.css
        'app-primary': '#059669',
        'app-primary-light': '#10b981',
        'app-primary-dark': '#047857',
        'app-bg': '#f8fafc',
        'app-card': '#ffffff',
        'app-border': '#e2e8f0',
        'app-text': '#0f172a',
        'app-muted': '#64748b',
        'app-sidebar': '#022c22',
        'app-warning': '#f59e0b'
      },
      borderRadius: {
        none: '0',
        xs: '4px',
        sm: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        '2xl': '24px',
        full: '9999px',
        app: '8px',
        card: '12px',
        button: '8px',
        input: '8px',
        modal: '16px'
      },
      boxShadow: {
        xs: '0 1px 2px rgba(15, 23, 42, 0.05)',
        sm: '0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.06)',
        md: '0 4px 6px rgba(15, 23, 42, 0.07), 0 2px 4px rgba(15, 23, 42, 0.06)',
        lg: '0 10px 15px rgba(15, 23, 42, 0.08), 0 4px 6px rgba(15, 23, 42, 0.05)',
        xl: '0 20px 25px rgba(15, 23, 42, 0.1), 0 10px 10px rgba(15, 23, 42, 0.04)',
        '2xl': '0 25px 50px rgba(15, 23, 42, 0.12)',
        inner: 'inset 0 2px 4px rgba(15, 23, 42, 0.06)',
        // App-specific shadows (legacy aliases)
        app: '0 2px 10px rgba(16, 35, 31, 0.035)',
        'app-md': '0 8px 22px rgba(16, 35, 31, 0.06)',
        'app-lg': '0 12px 34px rgba(16, 35, 31, 0.08)',
        'app-hover': '0 12px 28px rgba(15, 118, 110, 0.15)',
        // App-specific shadows (new)
        card: '0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.06)',
        'card-hover': '0 10px 25px rgba(15, 23, 42, 0.1), 0 4px 6px rgba(15, 23, 42, 0.05)',
        'card-elevated': '0 20px 25px rgba(15, 23, 42, 0.12), 0 10px 10px rgba(15, 23, 42, 0.04)',
        modal: '0 25px 50px rgba(15, 23, 42, 0.15), 0 10px 10px rgba(15, 23, 42, 0.04)',
        dropdown: '0 10px 15px rgba(15, 23, 42, 0.1), 0 4px 6px rgba(15, 23, 42, 0.05)',
        focus: '0 0 0 3px rgba(16, 185, 129, 0.2)',
        'focus-danger': '0 0 0 3px rgba(239, 68, 68, 0.2)'
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        display: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif']
      },
      fontSize: {
        '2xs': ['10px', { lineHeight: '1.5', letterSpacing: '0.02em' }],
        xs: ['12px', { lineHeight: '1.5', letterSpacing: '0.01em' }],
        sm: ['13px', { lineHeight: '1.5', letterSpacing: '0.01em' }],
        base: ['14px', { lineHeight: '1.5', letterSpacing: '0' }],
        lg: ['15px', { lineHeight: '1.5', letterSpacing: '0' }],
        xl: ['16px', { lineHeight: '1.5', letterSpacing: '0' }],
        '2xl': ['18px', { lineHeight: '1.4', letterSpacing: '-0.01em' }],
        '3xl': ['22px', { lineHeight: '1.3', letterSpacing: '-0.02em' }],
        '4xl': ['28px', { lineHeight: '1.2', letterSpacing: '-0.02em' }],
        '5xl': ['36px', { lineHeight: '1.1', letterSpacing: '-0.03em' }]
      },
      fontWeight: {
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        extrabold: '800'
      },
      spacing: {
        '0': '0',
        '0.5': '2px',
        '1': '4px',
        '1.5': '6px',
        '2': '8px',
        '2.5': '10px',
        '3': '12px',
        '3.5': '14px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '7': '28px',
        '8': '32px',
        '9': '36px',
        '10': '40px',
        '11': '44px',
        '12': '48px',
        '14': '56px',
        '16': '64px',
        '20': '80px',
        '24': '96px',
        '28': '112px',
        '32': '128px'
      },
      transitionDuration: {
        '50': '50ms',
        '75': '75ms',
        '100': '100ms',
        '150': '150ms',
        '200': '200ms',
        '250': '250ms',
        '300': '300ms',
        '350': '350ms',
        '400': '400ms',
        '500': '500ms',
        '700': '700ms',
        '1000': '1000ms'
      },
      transitionTimingFunction: {
        'ease-in': 'cubic-bezier(0.4, 0, 1, 1)',
        'ease-out': 'cubic-bezier(0, 0, 0.2, 1)',
        'ease-in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'ease-bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'ease-spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)'
      },
      keyframes: {
        // Toast animations
        toastIn: {
          from: { opacity: '0', transform: 'translateY(8px) scale(0.95)' },
          to: { opacity: '1', transform: 'translateY(0) scale(1)' }
        },
        toastOut: {
          from: { opacity: '1', transform: 'translateY(0) scale(1)' },
          to: { opacity: '0', transform: 'translateY(-8px) scale(0.95)' }
        },
        // Loading animations
        spin: {
          to: { transform: 'rotate(360deg)' }
        },
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' }
        },
        // Entrance animations
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' }
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to: { opacity: '1', transform: 'translateY(0)' }
        },
        slideDown: {
          from: { opacity: '0', transform: 'translateY(-16px)' },
          to: { opacity: '1', transform: 'translateY(0)' }
        },
        slideInRight: {
          from: { opacity: '0', transform: 'translateX(16px)' },
          to: { opacity: '1', transform: 'translateX(0)' }
        },
        slideInLeft: {
          from: { opacity: '0', transform: 'translateX(-16px)' },
          to: { opacity: '1', transform: 'translateX(0)' }
        },
        scaleIn: {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to: { opacity: '1', transform: 'scale(1)' }
        },
        scaleInCenter: {
          from: { opacity: '0', transform: 'scale(0.9)' },
          to: { opacity: '1', transform: 'scale(1)' }
        },
        // Ripple effect
        ripple: {
          '0%': { transform: 'scale(0)', opacity: '0.5' },
          '100%': { transform: 'scale(4)', opacity: '0' }
        },
        // Accordion
        accordionDown: {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' }
        },
        accordionUp: {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' }
        },
        // Skeleton
        skeleton: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' }
        }
      },
      animation: {
        // Toast
        toastIn: 'toastIn 0.2s ease-out',
        toastOut: 'toastOut 0.15s ease-in',
        // Loading
        spin: 'spin 1s linear infinite',
        spinFast: 'spin 0.6s linear infinite',
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        shimmer: 'shimmer 1.5s ease-in-out infinite',
        skeleton: 'skeleton 1.5s ease-in-out infinite',
        // Entrance
        fadeIn: 'fadeIn 0.25s ease-out',
        slideUp: 'slideUp 0.3s ease-out',
        slideDown: 'slideDown 0.3s ease-out',
        slideInRight: 'slideInRight 0.3s ease-out',
        slideInLeft: 'slideInLeft 0.3s ease-out',
        scaleIn: 'scaleIn 0.2s ease-out',
        scaleInCenter: 'scaleInCenter 0.25s ease-out',
        // Ripple
        ripple: 'ripple 0.6s ease-out',
        // Accordion
        accordionDown: 'accordionDown 0.25s ease-out',
        accordionUp: 'accordionUp 0.25s ease-out'
      },
      zIndex: {
        '0': '0',
        '10': '10',
        '20': '20',
        '30': '30',
        '40': '40',
        '50': '50',
        dropdown: '100',
        sticky: '200',
        modal: '300',
        popover: '400',
        tooltip: '500',
        toast: '600'
      },
      screens: {
        'xs': '480px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
        '3xl': '1920px'
      },
      container: {
        center: true,
        padding: {
          DEFAULT: '1.5rem',
          sm: '2rem',
          lg: '2.5rem',
          xl: '3rem',
          '2xl': '4rem'
        }
      }
    }
  },
  plugins: []
};