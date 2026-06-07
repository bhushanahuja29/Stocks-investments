import { fetchPins } from './pinAlertApi';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

async function fetchScrips() {
  const res = await fetch(`${API_URL}/api/scrips`);
  const data = await res.json();
  if (!data.success) {
    throw new Error('Failed to load scrips');
  }
  return data.scrips || [];
}

async function fetchPrice(symbol, marketType) {
  try {
    const res = await fetch(
      `${API_URL}/api/price/${encodeURIComponent(symbol)}?market_type=${marketType || 'crypto'}`
    );
    const data = await res.json();
    return data.success ? data.mark_price : null;
  } catch {
    return null;
  }
}

/**
 * Level triggers: price at or below support trigger (same logic as Navbar badge).
 */
export async function fetchTriggeredLevelAlerts() {
  const scrips = await fetchScrips();
  const prices = await Promise.all(
    scrips.map(async (scrip) => ({
      symbol: scrip.symbol,
      price: await fetchPrice(scrip.symbol, scrip.market_type),
    }))
  );
  const priceMap = Object.fromEntries(
    prices.filter((p) => p.price != null).map((p) => [p.symbol, p.price])
  );

  const triggered = [];
  scrips.forEach((scrip) => {
    const currentPrice = priceMap[scrip.symbol];
    if (currentPrice == null || !scrip.trigger_levels?.length) return;

    scrip.trigger_levels.forEach((level, levelIndex) => {
      if (level.alert_disabled) return;
      if (currentPrice <= level.trigger_price) {
        triggered.push({
          id: `${scrip.symbol}-${levelIndex}`,
          kind: 'level',
          symbol: scrip.symbol,
          market_type: scrip.market_type || 'crypto',
          timeframe: level.timeframe || '1w',
          trigger_price: level.trigger_price,
          current_price: currentPrice,
          level_index: levelIndex,
        });
      }
    });
  });

  return triggered.sort((a, b) => a.symbol.localeCompare(b.symbol));
}

/**
 * Pin alerts currently ringing (price crossed above/below threshold).
 */
export async function fetchRingingPinAlerts() {
  const pins = await fetchPins();
  return pins
    .filter((pin) => pin.alert_ringing)
    .map((pin) => ({
      id: `pin-${pin.symbol}`,
      kind: 'pin',
      symbol: pin.symbol,
      market_type: pin.market_type,
      current_price: pin.quote?.ltp ?? null,
      alert_above: pin.alert_above,
      alert_below: pin.alert_below,
      change_pct: pin.quote?.change_pct ?? null,
    }));
}

export async function fetchAllTriggeredNotifications() {
  const [levels, pins] = await Promise.all([
    fetchTriggeredLevelAlerts(),
    fetchRingingPinAlerts().catch(() => []),
  ]);
  return { levels, pins, total: levels.length + pins.length };
}
