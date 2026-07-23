// frontend/src/features/items/types.ts
/** Mirror backend schemas/items.py — AGENT_DRIFT.md */
import type { CursorPage } from '@/hooks/useInfiniteList';

export type ItemStatus = 'draft' | 'active' | 'archived';

export interface Item {
  id: string;
  workspace_id: string;
  name: string;
  status: ItemStatus;
  created_at: string;
  updated_at: string;
  created_by_id: string | null;
  updated_by_id: string | null;
}

export type ItemListPage = CursorPage<Item>;

export interface ItemCreatePayload {
  name: string;
  status?: ItemStatus;
}

export interface ItemUpdatePayload {
  name?: string;
  status?: ItemStatus;
}
