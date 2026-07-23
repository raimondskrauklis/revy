// frontend/src/features/items/hooks/useItemsList.ts
import { useInfiniteList } from '@/hooks/useInfiniteList';
import { fetchItems } from '@/features/items/api';
import type { Item } from '@/features/items/types';

export function useItemsList(enabled = true) {
  return useInfiniteList<Item>({
    queryKey: ['items', 'list'],
    queryFn: fetchItems,
    enabled,
  });
}
