import { useEffect, useRef } from 'react';
import { playAlertSound } from './alertSound';

function defaultState(above, below) {
  return {
    above,
    below,
    prevLtp: null,
    aboveArmed: true,
    belowArmed: true,
    hadFirstQuote: false,
    localRinging: false,
  };
}

function checkPinCross(pin, state) {
  const ltp = pin.quote?.ltp;
  if (ltp == null || typeof ltp !== 'number') return false;
  if (pin.alert_above == null && pin.alert_below == null) return false;

  const above = pin.alert_above;
  const below = pin.alert_below;
  const current = Number(ltp);
  let fired = false;

  if (!state.hadFirstQuote) {
    state.hadFirstQuote = true;
    state.prevLtp = current;
    if (above != null && current >= above) {
      fired = true;
      state.aboveArmed = false;
      state.localRinging = true;
    }
    if (below != null && current <= below) {
      fired = true;
      state.belowArmed = false;
      state.localRinging = true;
    }
    return fired;
  }

  const prev = state.prevLtp;
  if (above != null && state.aboveArmed && prev != null && prev < above && current >= above) {
    fired = true;
    state.aboveArmed = false;
    state.localRinging = true;
  }
  if (current < (above ?? Infinity)) {
    state.aboveArmed = true;
  }

  if (below != null && state.belowArmed && prev != null && prev > below && current >= below) {
    fired = true;
    state.belowArmed = false;
    state.localRinging = true;
  }
  if (current > (below ?? 0)) {
    state.belowArmed = true;
  }

  state.prevLtp = current;
  return fired;
}

function isRinging(pin, state) {
  if (pin.alert_ringing) return true;
  return Boolean(state?.localRinging);
}

/** Clear local ringing state for a symbol (after Stop Alert). */
export function clearLocalPinRinging(stateRef, symbol) {
  if (stateRef.current[symbol]) {
    stateRef.current[symbol].localRinging = false;
  }
}

/**
 * Watch pin quotes — repeat sound while alert is ringing until stopped.
 */
export function usePinAlertSound(pins, stateRef) {
  const ref = stateRef || useRef({});

  useEffect(() => {
    if (!pins?.length) return;

    const activeSymbols = new Set(pins.map((p) => p.symbol));
    Object.keys(ref.current).forEach((sym) => {
      if (!activeSymbols.has(sym)) delete ref.current[sym];
    });

    let shouldPlay = false;
    pins.forEach((pin) => {
      const { symbol } = pin;
      const above = pin.alert_above;
      const below = pin.alert_below;
      let state = ref.current[symbol];

      if (!state || state.above !== above || state.below !== below) {
        state = defaultState(above, below);
        ref.current[symbol] = state;
      }

      if (!pin.alert_ringing) {
        state.localRinging = false;
      }

      if (checkPinCross(pin, state)) {
        shouldPlay = true;
      } else if (isRinging(pin, state)) {
        shouldPlay = true;
      }
    });

    if (shouldPlay) {
      playAlertSound();
    }
  }, [pins, ref]);
}

export function getRingingPins(pins, stateRef) {
  if (!pins?.length) return [];
  return pins.filter((pin) => {
    const state = stateRef.current[pin.symbol];
    return isRinging(pin, state);
  });
}
