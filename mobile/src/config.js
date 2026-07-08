import Constants from 'expo-constants';

// Backend base URL. Set this in app.json -> expo.extra.apiUrl.
//  - Testing on a real phone over Wi-Fi: use your PC's LAN IP, e.g.
//    http://192.168.1.10:8000  (NOT 127.0.0.1 — that's the phone itself)
//  - Android emulator: http://10.0.2.2:8000
//  - Production: https://your-domain.com
const extra =
  Constants.expoConfig?.extra ?? Constants.manifest?.extra ?? {};

export const API_URL = extra.apiUrl || 'http://127.0.0.1:8000';
export const API_BASE = `${API_URL.replace(/\/$/, '')}/api/v1`;
