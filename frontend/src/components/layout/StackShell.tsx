// frontend/src/components/layout/StackShell.tsx
/**
 * Right-side stacked panels — extend registry per product.
 * KP full implementation: frontend/src/components/layout/StackShell.tsx
 */
import { useEffect, type ComponentType } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';
import { useStackStore, type StackItem, type StackItemType } from '@/stores/stackStore';

const PEEK_PX = 40;

const COMPONENT_REGISTRY: Record<StackItemType, ComponentType<{ item: StackItem }>> = {
  'entity-profile': EntityProfileQuickPanel,
  'item-detail': ItemDetailQuickPanel,
};

function EntityProfileQuickPanel({ item }: { item: StackItem }) {
  const { t } = useTranslation();
  return (
    <div className="p-6 space-y-4">
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('panels.quickViewHint')}</p>
      <p className="text-[color:var(--app-text-strong)] font-medium">{item.title}</p>
      <p className="text-xs text-[color:var(--app-text-muted)]">id: {item.id}</p>
    </div>
  );
}

function ItemDetailQuickPanel({ item }: { item: StackItem }) {
  return <EntityProfileQuickPanel item={item} />;
}

export function StackShell() {
  const { t } = useTranslation();
  const items = useStackStore((s) => s.items);
  const pop = useStackStore((s) => s.pop);
  const popTo = useStackStore((s) => s.popTo);

  useEffect(() => {
    if (!items.length) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [items.length]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && items.length) pop();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [items.length, pop]);

  if (!items.length) return null;

  return (
    <div className="fixed inset-0 z-[var(--z-overlay)] flex justify-end pointer-events-none">
      <button
        type="button"
        className="absolute inset-0 pointer-events-auto bg-[color-mix(in_oklab,var(--app-text)_12%,transparent)]"
        aria-label={t('panels.closeTop')}
        onClick={pop}
      />

      {items.map((item, index) => {
        const isTop = index === items.length - 1;
        const Panel = COMPONENT_REGISTRY[item.type];
        const offsetRight = (items.length - 1 - index) * PEEK_PX;

        if (!isTop && index < items.length - 2) {
          return (
            <button
              key={`${item.type}-${item.id}`}
              type="button"
              className="absolute top-4 bottom-4 w-10 pointer-events-auto rounded-l-xl bg-[color:var(--app-surface)] ring-1 ring-[color:var(--app-ring)]"
              style={{ right: offsetRight, zIndex: `calc(var(--z-panel) + ${index})` }}
              onClick={() => popTo(index)}
              aria-label={t('panels.focusPanel', { title: item.title })}
            />
          );
        }

        return (
          <section
            key={`${item.type}-${item.id}`}
            role="dialog"
            aria-modal="true"
            aria-labelledby={`panel-title-${item.type}-${item.id}`}
            className="absolute top-2 bottom-2 pointer-events-auto flex flex-col w-full max-w-[min(900px,100vw)] bg-[color:var(--app-surface)] ring-1 ring-[color:var(--app-ring)] rounded-l-xl shadow-lg"
            style={{ right: offsetRight, zIndex: `calc(var(--z-panel) + ${index})` }}
          >
            <header className="flex items-center gap-2 px-4 py-3 ring-b ring-[color:var(--app-ring)]">
              <h2
                id={`panel-title-${item.type}-${item.id}`}
                className="flex-1 truncate text-sm font-semibold text-[color:var(--app-text-strong)]"
              >
                {item.title}
              </h2>
              <button
                type="button"
                onClick={pop}
                className="min-h-11 min-w-11 inline-flex items-center justify-center rounded-lg focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
                aria-label={t('panels.close')}
              >
                <X className="h-4 w-4" aria-hidden />
              </button>
            </header>
            <div className="flex-1 min-h-0 overflow-y-auto">
              {Panel ? <Panel item={item} /> : <p className="p-6 text-sm">{t('panels.unknownType')}</p>}
            </div>
          </section>
        );
      })}
    </div>
  );
}
