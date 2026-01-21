export function getErrorMessage(error: unknown, fallback = 'Ошибка') {
  if (!error) return fallback;
  if (typeof error === 'string') return error;
  if (error instanceof Error) return error.message || fallback;
  try {
    const e = error as { response?: { data?: { detail?: string } }; message?: string };
    return e?.response?.data?.detail || e?.message || fallback;
  } catch {
    return fallback;
  }
}
