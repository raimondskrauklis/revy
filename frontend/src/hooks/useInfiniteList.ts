// frontend/src/hooks/useInfiniteList.ts
import { useEffect } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';

export interface CursorMeta {
  has_next: boolean;
  next_cursor: string | null;
}

export interface CursorPage<T> {
  items: T[];
  cursor: CursorMeta;
}

interface UseInfiniteListOptions<T> {
  queryKey: unknown[];
  queryFn: (cursor: string | null) => Promise<CursorPage<T>>;
  enabled?: boolean;
}

export function useInfiniteList<T>({
  queryKey,
  queryFn,
  enabled = true,
}: UseInfiniteListOptions<T>) {
  const { ref, inView } = useInView({ threshold: 0.2 });

  const query = useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) => queryFn(pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => (last.cursor.has_next ? last.cursor.next_cursor : undefined),
    enabled,
  });

  useEffect(() => {
    if (inView && query.hasNextPage && !query.isFetchingNextPage) {
      void query.fetchNextPage();
    }
  }, [inView, query.hasNextPage, query.isFetchingNextPage, query]);

  return {
    items: query.data?.pages.flatMap((p) => p.items) ?? [],
    isLoading: query.isLoading,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage,
    error: query.error,
    ref,
  };
}
