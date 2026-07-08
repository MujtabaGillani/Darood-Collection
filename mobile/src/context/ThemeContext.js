import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { createContext, useContext, useEffect, useState } from 'react';
import { Appearance } from 'react-native';

import { dark, light } from '../theme/colors';

const ThemeContext = createContext(null);
const STORAGE_KEY = 'theme_mode'; // 'system' | 'light' | 'dark'

export function ThemeProvider({ children }) {
  const [mode, setMode] = useState('system');
  const [systemScheme, setSystemScheme] = useState(Appearance.getColorScheme() || 'light');

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((v) => v && setMode(v));
    const sub = Appearance.addChangeListener(({ colorScheme }) =>
      setSystemScheme(colorScheme || 'light'),
    );
    return () => sub.remove();
  }, []);

  const effective = mode === 'system' ? systemScheme : mode;
  const colors = effective === 'dark' ? dark : light;

  const changeMode = (m) => {
    setMode(m);
    AsyncStorage.setItem(STORAGE_KEY, m);
  };

  // Quick flip between light/dark (used by the header toggle).
  const toggle = () => changeMode(effective === 'dark' ? 'light' : 'dark');

  return (
    <ThemeContext.Provider value={{ colors, mode, scheme: effective, setMode: changeMode, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
