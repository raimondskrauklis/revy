// frontend/src/stores/stackStore.ts
/**
 * Stacked panel state — right-side quick-detail overlays.
 * See docs/frontend/patterns/STACKED_PANELS.md
 */
import { create } from 'zustand';

/** Extend per product — keep registry in StackShell in sync */
export type StackItemType = 'entity-profile' | 'item-detail';

export interface StackItem {
  id: string;
  type: StackItemType;
  title: string;
  data?: unknown;
  params?: Record<string, unknown>;
}

interface StackState {
  items: StackItem[];
  expandedIndex: number | null;
  push: (item: StackItem) => void;
  pop: () => void;
  popTo: (index: number) => void;
  clear: () => void;
  updateParamsById: (type: StackItemType, id: string, params: Record<string, unknown>) => void;
  toggleExpand: (index: number) => void;
}

const MAX_STACK_DEPTH = 6;

export const useStackStore = create<StackState>((set, get) => ({
  items: [],
  expandedIndex: null,

  push: (item) => {
    const { items } = get();
    const top = items[items.length - 1];
    if (top?.id === item.id && top.type === item.type) {
      const next = [...items];
      next[items.length - 1] = {
        ...top,
        title: item.title || top.title,
        data: { ...(top.data ?? {}), ...(item.data ?? {}) },
      };
      set({ items: next });
      return;
    }

    const dupIdx = items.findIndex((i) => i.id === item.id && i.type === item.type);
    if (dupIdx !== -1) {
      const existing = items[dupIdx]!;
      const merged: StackItem = {
        ...existing,
        title: item.title || existing.title,
        data: { ...(existing.data ?? {}), ...(item.data ?? {}) },
      };
      const without = items.filter((_, i) => i !== dupIdx);
      set({ items: [...without, merged], expandedIndex: null });
      return;
    }

    if (items.length >= MAX_STACK_DEPTH) {
      set({ items: [...items.slice(1), item], expandedIndex: null });
      return;
    }

    set({ items: [...items, item] });
  },

  pop: () => {
    const { items, expandedIndex } = get();
    if (!items.length) return;
    const newExpanded = expandedIndex === items.length - 1 ? null : expandedIndex;
    set({ items: items.slice(0, -1), expandedIndex: newExpanded });
  },

  popTo: (index) => {
    const { items, expandedIndex } = get();
    if (index < 0 || index >= items.length) return;
    const newExpanded = expandedIndex !== null && expandedIndex > index ? null : expandedIndex;
    set({ items: items.slice(0, index + 1), expandedIndex: newExpanded });
  },

  clear: () => set({ items: [], expandedIndex: null }),

  updateParamsById: (type, id, params) => {
    const { items } = get();
    const index = items.findIndex((i) => i.type === type && i.id === id);
    if (index === -1) return;
    const next = [...items];
    next[index] = { ...next[index], params: { ...next[index].params, ...params } };
    set({ items: next });
  },

  toggleExpand: (index) => {
    const { expandedIndex } = get();
    set({ expandedIndex: expandedIndex === index ? null : index });
  },
}));
