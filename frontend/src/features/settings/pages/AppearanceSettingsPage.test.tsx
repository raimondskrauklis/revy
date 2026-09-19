// frontend/src/features/settings/pages/AppearanceSettingsPage.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AppearanceSettingsPage } from '@/features/settings/pages/AppearanceSettingsPage';

describe('AppearanceSettingsPage', () => {
  it('states console-only with no Light control', () => {
    render(<AppearanceSettingsPage />);

    expect(screen.getByRole('heading', { name: /appearance/i })).toBeInTheDocument();
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    expect(screen.queryByText(/^light$/i)).not.toBeInTheDocument();
    expect(screen.getByText(/console/i)).toBeInTheDocument();
  });
});
