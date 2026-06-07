/**
 * Wake a sleeping Render backend before loading data.
 * Returns { ok, cold } where cold=true if the first attempt was slow or failed.
 */
export async function wakeBackend(apiUrl, { timeoutMs = 90000, retries = 1 } = {}) {
  const base = apiUrl.replace(/\/$/, '');
  const url = `${base}/api/health`;
  let cold = false;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const started = Date.now();
    try {
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timer);
      if (res.ok) {
        if (attempt > 0 || Date.now() - started > 8000) {
          cold = true;
        }
        return { ok: true, cold };
      }
    } catch (err) {
      clearTimeout(timer);
      cold = true;
      if (attempt === retries) {
        return { ok: false, cold, error: err };
      }
    }
  }

  return { ok: false, cold: true };
}
