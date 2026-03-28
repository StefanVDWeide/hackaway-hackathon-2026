/**
 * Typed $fetch wrapper that automatically injects the Bearer token
 * from nuxt-auth into every request.
 */
export function useApi() {
  const { token } = useAuth();

  async function apiFetch<T>(
    path: string,
    options: Parameters<typeof $fetch>[1] = {},
  ): Promise<T> {
    return $fetch<T>(path, {
      ...options,
      headers: {
        ...(options.headers as Record<string, string> | undefined),
        ...(token.value ? { Authorization: `${token.value}` } : {}),
      },
    });
  }

  return { apiFetch };
}
