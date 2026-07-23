// frontend/src/stores/listFilterStore.ts
/**
 * Generic list filter store — URL sync + optional persist.
 * Extend per feature; see docs/frontend/patterns/LIST_FILTERS.md.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ItemStatusFilter = 'all' | 'active' | 'archived';
export type ItemSortKey = 'created_at_desc' | 'name_asc';

export const ITEM_FILTER_DEFAULTS = {
  searchQuery: '',
  status: 'all' as ItemStatusFilter,
  sort: 'created_at_desc' as ItemSortKey,
};

export interface ItemFilterState {
  searchQuery: string;
  status: ItemStatusFilter;
  sort: ItemSortKey;
}

export interface ItemFilterActions {
  setSearchQuery: (q: string) => void;
  setStatus: (status: ItemStatusFilter) => void;
  setSort: (sort: ItemSortKey) => void;
  resetFilters: () => void;
  getActiveFilterCount: () => number;
}

export type ItemFilterStore = ItemFilterState & ItemFilterActions;

/** Params that define filter scope — used to detect URL vs persist init. */
export const ITEM_FILTER_URL_KEYS = ['q', 'status', 'sort'] as const;

const SEARCH_MIN_LEN = 2;

export function buildFilterUrlParams(state: ItemFilterState): URLSearchParams {
  const params = new URLSearchParams();
  const q = state.searchQuery.trim();
  if (q.length >= SEARCH_MIN_LEN) params.set('q', q);
  if (state.status !== ITEM_FILTER_DEFAULTS.status) params.set('status', state.status);
  if (state.sort !== ITEM_FILTER_DEFAULTS.sort) params.set('sort', state.sort);
  return params;
}

export function parseFilterUrlParams(searchParams: URLSearchParams): Partial<ItemFilterState> {
  const result: Partial<ItemFilterState> = {};
  const q = searchParams.get('q')?.trim();
  if (q) result.searchQuery = q;

  const status = searchParams.get('status')?.trim();
  if (status === 'active' || status === 'archived') result.status = status;

  const sort = searchParams.get('sort')?.trim();
  if (sort === 'created_at_desc' || sort === 'name_asc') result.sort = sort;

  return result;
}

export function hasItemFilterUrlParams(searchParams: URLSearchParams): boolean {
  return ITEM_FILTER_URL_KEYS.some((k) => searchParams.has(k));
}

/** Map store → API list query (snake_case params). */
export function filterStateToListParams(state: ItemFilterState): {
  search?: string;
  status?: string;
  sort?: string;
} {
  const q = state.searchQuery.trim();
  return {
    search: q.length >= SEARCH_MIN_LEN ? q : undefined,
    status: state.status === 'all' ? undefined : state.status,
    sort: state.sort === ITEM_FILTER_DEFAULTS.sort ? undefined : state.sort,
  };
}

export const useItemFilterStore = create<ItemFilterStore>()(
  persist(
    (set, get) => ({
      ...ITEM_FILTER_DEFAULTS,
      setSearchQuery: (searchQuery) => set({ searchQuery }),
      setStatus: (status) => set({ status }),
      setSort: (sort) => set({ sort }),
      resetFilters: () =>
        set({
          searchQuery: ITEM_FILTER_DEFAULTS.searchQuery,
          status: ITEM_FILTER_DEFAULTS.status,
        }),
      getActiveFilterCount: () => {
        const s = get();
        let n = 0;
        if (s.searchQuery.trim().length >= SEARCH_MIN_LEN) n += 1;
        if (s.status !== ITEM_FILTER_DEFAULTS.status) n += 1;
        return n;
      },
    }),
    {
      name: 'item-filters',
      version: 1,
      partialize: (s) => ({
        searchQuery: s.searchQuery,
        status: s.status,
        sort: s.sort,
      }),
    },
  ),
);
