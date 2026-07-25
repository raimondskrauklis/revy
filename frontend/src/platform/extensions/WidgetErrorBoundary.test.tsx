// frontend/src/platform/extensions/WidgetErrorBoundary.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { WidgetErrorBoundary } from '@/platform/extensions/WidgetErrorBoundary';

function BrokenWidget(): null {
  throw new Error('boom');
}

describe('WidgetErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <WidgetErrorBoundary>
        <p>Widget content</p>
      </WidgetErrorBoundary>,
    );

    expect(screen.getByText('Widget content')).toBeInTheDocument();
  });

  it('shows fallback when child throws', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <WidgetErrorBoundary>
        <BrokenWidget />
      </WidgetErrorBoundary>,
    );

    expect(screen.getByRole('alert')).toHaveTextContent(/could not be loaded/i);
    consoleError.mockRestore();
  });
});
