// frontend/src/features/items/api.ts
/** Items API client — mirror api/v1/items.py */
import apiClient, { parseSuccess } from '@/lib/api';
import type { Item, ItemCreatePayload, ItemListPage, ItemUpdatePayload } from '@/features/items/types';

export async function fetchItems(cursor: string | null): Promise<ItemListPage> {
  const response = await apiClient.get('/items', {
    params: cursor ? { cursor } : undefined,
  });
  return parseSuccess<ItemListPage>(response);
}

export async function fetchItem(itemId: string): Promise<Item> {
  const response = await apiClient.get(`/items/${itemId}`);
  return parseSuccess<Item>(response);
}

export async function createItem(payload: ItemCreatePayload): Promise<Item> {
  const response = await apiClient.post('/items', payload);
  return parseSuccess<Item>(response);
}

export async function updateItem(itemId: string, payload: ItemUpdatePayload): Promise<Item> {
  const response = await apiClient.patch(`/items/${itemId}`, payload);
  return parseSuccess<Item>(response);
}

export async function deleteItem(itemId: string): Promise<void> {
  await apiClient.delete(`/items/${itemId}`);
}
