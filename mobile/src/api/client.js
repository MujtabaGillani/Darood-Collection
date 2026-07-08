import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

import { API_BASE } from '../config';

const ACCESS_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

// In-memory cache so interceptors don't hit SecureStore on every request.
let accessToken = null;
let refreshToken = null;
// Whether tokens are written to disk. "Remember me" off => session-only.
let persistPref = true;

// Callback fired when the session can't be recovered (refresh failed), so the
// app can drop back to the login screen. Registered by AuthContext.
let onAuthExpired = null;
export function setOnAuthExpired(fn) {
  onAuthExpired = fn;
}

export async function loadTokens() {
  accessToken = await SecureStore.getItemAsync(ACCESS_KEY);
  refreshToken = await SecureStore.getItemAsync(REFRESH_KEY);
  return { access: accessToken, refresh: refreshToken };
}

export async function setTokens({ access, refresh, persist }) {
  accessToken = access;
  if (refresh !== undefined) refreshToken = refresh;
  if (persist !== undefined) persistPref = persist;

  if (persistPref) {
    if (access) await SecureStore.setItemAsync(ACCESS_KEY, access);
    if (refresh) await SecureStore.setItemAsync(REFRESH_KEY, refresh);
  } else {
    // Session-only: keep tokens in memory, write nothing to disk.
    await SecureStore.deleteItemAsync(ACCESS_KEY);
    await SecureStore.deleteItemAsync(REFRESH_KEY);
  }
}

export async function clearTokens() {
  accessToken = null;
  refreshToken = null;
  await SecureStore.deleteItemAsync(ACCESS_KEY);
  await SecureStore.deleteItemAsync(REFRESH_KEY);
}

export function getRefreshToken() {
  return refreshToken;
}

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

// On a 401, try one refresh with the stored refresh token, then replay.
let refreshing = null;

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;

    if (status === 401 && !original._retry) {
      original._retry = true;
      try {
        if (!refreshing) {
          refreshing = (async () => {
            if (!refreshToken) throw new Error('no refresh token');
            const resp = await axios.post(`${API_BASE}/auth/refresh/`, { refresh: refreshToken });
            // Preserve the persist choice (don't start writing to disk if the
            // user logged in without "Remember me").
            await setTokens({ access: resp.data.access, refresh: resp.data.refresh });
            return resp.data.access;
          })();
        }
        const newAccess = await refreshing;
        refreshing = null;
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      } catch (e) {
        // Refresh failed (refresh token expired/invalid) -> session is over.
        refreshing = null;
        await clearTokens();
        if (onAuthExpired) onAuthExpired(); // send the user back to Login
        throw error;
      }
    }
    throw error;
  },
);

// Turn a DRF error response into a readable string.
export function apiErrorMessage(error, fallback = 'Something went wrong.') {
  const data = error?.response?.data;
  if (!data) return error?.message || fallback;
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  // Field errors: join the first message of each field.
  const parts = [];
  for (const [key, val] of Object.entries(data)) {
    const msg = Array.isArray(val) ? val[0] : val;
    parts.push(key === 'non_field_errors' ? msg : `${key}: ${msg}`);
  }
  return parts.join('\n') || fallback;
}
