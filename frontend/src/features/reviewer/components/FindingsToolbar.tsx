// frontend/src/features/reviewer/components/FindingsToolbar.tsx
import { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, X } from 'lucide-react';
import type { FindingSeverity, FindingCategory, FindingGroupState, ReconciledFinding } from '@/features/reviewer/types';
import { useDebouncedValue } from '@/lib/useDebouncedValue';

type SortField = 'severity' | 'file_path' | 'updated_at';
type SortDir = 'asc' | 'desc';

const SEVERITY_ORDER: Record<FindingSeverity, number> = {
  critical: 0,
  error: 1,
  warning: 2,
  info: 3,
};

interface FindingsToolbarProps {
  findings: ReconciledFinding[];
  /** Render prop — receives filtered + sorted findings for the table below. */
  children: (filtered: ReconciledFinding[]) => React.ReactNode;
}

export function FindingsToolbar({ findings, children }: FindingsToolbarProps) {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const deferredSearch = useDebouncedValue(search, 300);
  const [severityFilter, setSeverityFilter] = useState<Set<FindingSeverity>>(new Set());
  const [stateFilter, setStateFilter] = useState<Set<FindingGroupState>>(new Set());
  const [categoryFilter, setCategoryFilter] = useState<Set<FindingCategory>>(new Set());
  const [sortField, setSortField] = useState<SortField>('severity');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const allSeverities: FindingSeverity[] = ['critical', 'error', 'warning', 'info'];
  const allCategories: FindingCategory[] = useMemo(
    () => [...new Set(findings.map((f) => f.category))].filter((c): c is FindingCategory => Boolean(c)).sort(),
    [findings],
  );
  const allStates: FindingGroupState[] = useMemo(
    () => [...new Set(findings.map((f) => f.state))].filter((s): s is FindingGroupState => Boolean(s)).sort(),
    [findings],
  );

  const filtered = useMemo(() => {
    let result = findings;

    if (deferredSearch.trim()) {
      const q = deferredSearch.toLowerCase();
      result = result.filter(
        (f) =>
          f.title.toLowerCase().includes(q) ||
          f.message.toLowerCase().includes(q) ||
          (f.file_path ?? '').toLowerCase().includes(q),
      );
    }

    if (severityFilter.size > 0) {
      result = result.filter((f) => severityFilter.has(f.severity));
    }

    if (stateFilter.size > 0) {
      result = result.filter((f) => stateFilter.has(f.state));
    }

    if (categoryFilter.size > 0) {
      result = result.filter((f) => categoryFilter.has(f.category));
    }

    result = [...result].sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case 'severity':
          cmp = (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99);
          break;
        case 'file_path':
          cmp = (a.file_path ?? '').localeCompare(b.file_path ?? '');
          break;
        case 'updated_at':
          cmp = a.updated_at.localeCompare(b.updated_at);
          break;
      }
      return sortDir === 'desc' ? -cmp : cmp;
    });
    return result;
  }, [findings, deferredSearch, severityFilter, stateFilter, categoryFilter, sortField, sortDir]);

  const toggleSort = useCallback(
    (field: SortField) => {
      if (sortField === field) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
      } else {
        setSortField(field);
        setSortDir('asc');
      }
    },
    [sortField],
  );

  const toggleFilter = useCallback(
    <T,>(setter: React.Dispatch<React.SetStateAction<Set<T>>>, value: T) => {
      setter((prev) => {
        const next = new Set(prev);
        if (next.has(value)) {
          next.delete(value);
        } else {
          next.add(value);
        }
        return next;
      });
    },
    [],
  );

  const clearFilters = useCallback(() => {
    setSearch('');
    setSeverityFilter(new Set());
    setStateFilter(new Set());
    setCategoryFilter(new Set());
  }, []);

  const hasFilters =
    search.trim() !== '' ||
    severityFilter.size > 0 ||
    stateFilter.size > 0 ||
    categoryFilter.size > 0;

  const sortArrow = (field: SortField) => {
    if (sortField !== field) return '';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[160px]">
          <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--app-text-muted)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('reviewer.toolbar.searchPlaceholder')}
            className="w-full rounded-[var(--app-radius-md)] border border-[color:var(--app-ring)] bg-[color:var(--app-input-bg)] pl-8 pr-3 py-1.5 text-sm placeholder:text-[color:var(--app-text-muted)] focus:outline-none focus:ring-2 focus:ring-[color:var(--app-ring-strong)]"
          />
        </div>
        <span className="text-sm text-[color:var(--app-text-muted)]">
          {t('reviewer.toolbar.resultCount', { count: filtered.length })}
        </span>
        {hasFilters && (
          <button
            type="button"
            onClick={clearFilters}
            className="inline-flex items-center gap-1 rounded-[var(--app-radius-sm)] px-2 py-1 text-xs text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]"
          >
            <X className="h-3 w-3" />
            {t('reviewer.toolbar.clearFilters')}
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
        <div className="flex flex-wrap items-center gap-1">
          <span className="text-xs text-[color:var(--app-text-muted)]">
            {t('reviewer.toolbar.severity')}:
          </span>
          {allSeverities.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => toggleFilter(setSeverityFilter, s)}
              className={`rounded-full px-2 py-0.5 text-xs border ${
                severityFilter.has(s)
                  ? 'bg-[color:var(--app-chip-active)] border-[color:var(--app-ring-strong)] text-[color:var(--app-text-strong)]'
                  : 'border-[color:var(--app-ring)] text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]'
              }`}
            >
              {t(`reviewer.severity.${s}`)}
            </button>
          ))}
        </div>

        {allCategories.length > 0 && (
          <div className="flex flex-wrap items-center gap-1">
            <span className="text-xs text-[color:var(--app-text-muted)]">
              {t('reviewer.toolbar.category')}:
            </span>
            {allCategories.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => toggleFilter(setCategoryFilter, c)}
                className={`rounded-full px-2 py-0.5 text-xs border ${
                  categoryFilter.has(c)
                    ? 'bg-[color:var(--app-chip-active)] border-[color:var(--app-ring-strong)] text-[color:var(--app-text-strong)]'
                    : 'border-[color:var(--app-ring)] text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]'
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        )}

        {allStates.length > 0 && (
          <div className="flex flex-wrap items-center gap-1">
            <span className="text-xs text-[color:var(--app-text-muted)]">
              {t('reviewer.toolbar.state')}:
            </span>
            {allStates.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => toggleFilter(setStateFilter, s)}
                className={`rounded-full px-2 py-0.5 text-xs border ${
                  stateFilter.has(s)
                    ? 'bg-[color:var(--app-chip-active)] border-[color:var(--app-ring-strong)] text-[color:var(--app-text-strong)]'
                    : 'border-[color:var(--app-ring)] text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <div className="flex items-center gap-2 ml-auto">
          <span className="text-xs text-[color:var(--app-text-muted)]">
            {t('reviewer.toolbar.sort')}:
          </span>
          {(['severity', 'file_path', 'updated_at'] as SortField[]).map((field) => (
            <button
              key={field}
              type="button"
              onClick={() => toggleSort(field)}
              className={`text-xs ${
                sortField === field
                  ? 'text-[color:var(--app-text-strong)] font-medium'
                  : 'text-[color:var(--app-text-muted)] hover:text-[color:var(--app-text-strong)]'
              }`}
            >
              {t(`reviewer.toolbar.sort.${field}`)}
              {sortField === field && sortArrow(field)}
            </button>
          ))}
        </div>
      </div>

      {children(filtered)}
    </div>
  );
}