// frontend/src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';
import { handleError } from '@/shared/errors/handlers';

function createQueryClient(): QueryClient {
  const client = new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: false,
        staleTime: 5 * 60 * 1000,
      },
      mutations: { retry: false },
    },
  });

  client.getQueryCache().subscribe((event) => {
    const query = event?.query;
    if (!query?.state.error || !query.meta?.domain) return;
    const meta = query.meta as { domain?: string; suppressGlobalErrorToast?: boolean };
    if (meta.suppressGlobalErrorToast) return;
    handleError(query.state.error, {
      domain: meta.domain,
      operation: (query.meta as { operation?: string }).operation ?? 'fetch',
    });
  });

  client.getMutationCache().subscribe((event) => {
    const mutation = event?.mutation;
    if (!mutation?.state.error || !mutation.meta?.domain) return;
    handleError(mutation.state.error, {
      domain: mutation.meta.domain as string,
      operation: (mutation.meta.operation as string) ?? 'update',
    });
  });

  return client;
}

export const queryClient = createQueryClient();
