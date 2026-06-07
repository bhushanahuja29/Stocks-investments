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
 * Monitor scrip support levels that have triggered (price at or below trigger).
 * Pins are separate — see /pins and push notifications for pin alerts.
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
