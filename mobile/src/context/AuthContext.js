import React, { createContext, useContext, useEffect, useState } from 'react';

import { api, clearTokens, getRefreshToken, loadTokens, setOnAuthExpired, setTokens } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(true);

  // When a refresh fails (session expired), drop straight back to Login.
  useEffect(() => {
    setOnAuthExpired(() => setUser(null));
    return () => setOnAuthExpired(null);
  }, []);

  // On launch, restore any saved session.
  useEffect(() => {
    (async () => {
      try {
        const { access } = await loadTokens();
        if (access) {
          const me = await api.get('/auth/me/');
          setUser(me.data);
        }
      } catch (e) {
        await clearTokens();
      } finally {
        setBooting(false);
      }
    })();
  }, []);

  const login = async (username, password, remember = true) => {
    const resp = await api.post('/auth/login/', { username, password });
    await setTokens({ access: resp.data.access, refresh: resp.data.refresh, persist: remember });
    setUser(resp.data.user);
    return resp.data.user;
  };

  const register = async (payload) => {
    const resp = await api.post('/auth/register/', payload);
    return resp.data;
  };

  const refreshMe = async () => {
    const me = await api.get('/auth/me/');
    setUser(me.data);
    return me.data;
  };

  const logout = async () => {
    // Best-effort: invalidate the refresh token server-side so it can't be reused.
    const refresh = getRefreshToken();
    if (refresh) {
      try {
        await api.post('/auth/logout/', { refresh });
      } catch (e) {
        /* offline or already invalid — clear locally anyway */
      }
    }
    await clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, booting, login, register, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
