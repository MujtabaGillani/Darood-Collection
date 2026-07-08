# Darood Collection — Mobile (Expo / React Native)

The Android/iOS app for Darood Collection. It talks to the **same Django
backend** as the website via the JSON API at `/api/v1/` (JWT auth) and mirrors
the web UI (teal/gold theme, charts, Urdu Fazail page, role-based screens).

## 1. Point the app at your backend

Edit `app.json` → `expo.extra.apiUrl`:

| Where you run the app | apiUrl | Backend bind |
|-----------------------|--------|--------------|
| MuMu emulator + adb reverse (**default**) | `http://127.0.0.1:8000` | `127.0.0.1:8000` |
| Android Studio AVD | `http://10.0.2.2:8000` | `0.0.0.0:8000` |
| Real phone on same Wi-Fi | `http://<your-PC-LAN-IP>:8000` (e.g. `http://192.168.18.20:8000`) | `0.0.0.0:8000` |
| Production | `https://your-domain.com` | — |

The committed default is `http://127.0.0.1:8000` for the MuMu + adb-reverse flow
(see **2b**). For a real phone or the APK build, switch it to your PC's LAN IP or
your domain — a phone can't reach `127.0.0.1` (that's the phone itself). Your LAN
IP is already allowed (`ALLOWED_HOSTS=*` in dev).

## 2. Install & run (development)

```bash
cd mobile
npm install
npx expo install        # reconciles native module versions with the SDK
npx expo start          # scan the QR with Expo Go, or press "a" for Android
```

Log in with any active account from the backend. New self-registered accounts
stay inactive until a Super Admin approves them (Dashboard → User Management).

## 2b. Run on an Android emulator (MuMu) via adb reverse

MuMu (and most emulators) sit behind NAT/firewall, so the cleanest way to reach
your PC is **`adb reverse`** — it maps the emulator's `localhost` to your PC, so
no firewall/LAN config is needed. For this, `app.json` → `extra.apiUrl` must be
`http://127.0.0.1:8000` (the default committed here).

1. Start MuMu, then find its adb address:

   ```bash
   "C:/Program Files/Netease/MuMuPlayer/nx_main/MuMuManager.exe" adb -v 0
   # -> {"adb_host": "192.168.18.60", "adb_port": 5555}
   ```

2. Connect adb and forward the backend (8000) and Metro (8081) ports:

   ```bash
   adb connect 192.168.18.60:5555
   adb -s 192.168.18.60:5555 reverse tcp:8000 tcp:8000
   adb -s 192.168.18.60:5555 reverse tcp:8081 tcp:8081
   adb devices                    # should list the device as "device"
   ```

3. Start the backend bound to localhost (that's where the tunnel points):

   ```bash
   cd ..
   ./venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
   ```

4. Start Expo in **localhost mode** so it advertises `127.0.0.1:8081` (which the
   adb tunnel forwards). Plain `expo start` uses your LAN IP, which Windows
   Firewall blocks from the emulator — so use:

   ```bash
   cd mobile
   npm run mumu   # = cross-env REACT_NATIVE_PACKAGER_HOSTNAME=127.0.0.1 expo start
   # press "a", OR in MuMu open Expo Go -> "Enter URL manually" -> exp://127.0.0.1:8081
   ```

   This binds Metro on all interfaces but advertises `127.0.0.1`, so the app
   loads through the adb tunnel. (Do **not** use `--localhost` — it binds Metro
   to IPv6-localhost only, which the IPv4 reverse tunnel can't reach.)

   > First launch will prompt to install the matching **Expo Go** on the device —
   > accept it. The project targets Expo SDK 56.

Log in with any active account (e.g. a Super Admin). Reset a password with
`python manage.py changepassword <username>`.

**Re-run after a PC/MuMu restart** (adb reverse is cleared when the connection
drops):

```bash
adb connect 192.168.18.60:5555
adb -s 192.168.18.60:5555 reverse tcp:8000 tcp:8000
adb -s 192.168.18.60:5555 reverse tcp:8081 tcp:8081
```

> Verify the tunnel: `adb -s 192.168.18.60:5555 shell 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/auth/login/'`
> should print `405` (backend reachable). `8081/status` should print `200` (Metro reachable).

## 3. Build an installable APK

Uses Expo Application Services (EAS) — the build runs in the cloud and gives you
a downloadable `.apk`.

```bash
npm install -g eas-cli
eas login
eas build:configure          # first time only
eas build -p android --profile preview
```

When it finishes, EAS prints a URL. Open it on the phone, download, and install
the `.apk` (allow "install from unknown sources"). The `preview` profile is
configured for APK output in `eas.json`.

Local build alternative (needs Android SDK + JDK):

```bash
eas build -p android --profile preview --local
```

## 4. Screens by role

- **Simple user:** My Progress (+ trend chart), Submit Darood, Fazail, Settings
- **Manager:** Overview, Add Darood, Approvals, Fazail, Settings
- **Super Admin:** Dashboard (stats + filtered trend + breakdowns + user
  management), Overview, Add Darood, Approvals, Settings

## Project layout

```
App.js                     providers + navigation
src/config.js              backend URL (from app.json extra.apiUrl)
src/api/client.js          axios + JWT storage + auto-refresh
src/context/               AuthContext, ThemeContext (light/dark, system)
src/theme/colors.js        web-matched palette
src/components/            UI kit + SVG TrendChart
src/screens/               one file per screen
src/data/fazail.js         Quran + hadith content (offline)
```
