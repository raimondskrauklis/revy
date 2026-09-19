// frontend/src/components/auth/RevyLogo.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { RevyLogo } from '@/components/auth/RevyLogo';

describe('RevyLogo', () => {
  it('renders wordmark and wedge svg, not a letter-R tile', () => {
    const { container } = render(
      <MemoryRouter>
        <RevyLogo />
      </MemoryRouter>,
    );
    expect(screen.getByText('revy')).toBeInTheDocument();
    expect(container.querySelector('svg')).not.toBeNull();
    expect(container.textContent).not.toMatch(/\bR\b/);
    expect(container.querySelector('svg')?.textContent).not.toBe('>');
  });

  it('hides wordmark when showWordmark is false', () => {
    render(
      <MemoryRouter>
        <RevyLogo showWordmark={false} />
      </MemoryRouter>,
    );
    expect(screen.queryByText('revy')).not.toBeInTheDocument();
  });
});
