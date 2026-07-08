import { Ionicons } from '@expo/vector-icons';
import React from 'react';
import { Text, View } from 'react-native';

import { Button, Card, Muted, Row, Screen, Segmented, Title } from '../components/UI';
import { API_URL } from '../config';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

export default function SettingsScreen({ navigation }) {
  const { colors, mode, setMode } = useTheme();
  const { user, logout } = useAuth();

  return (
    <Screen>
      <Card style={{ gap: 6 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <Ionicons name="person-circle-outline" size={40} color={colors.primary} />
          <View>
            <Text style={{ color: colors.text, fontSize: 18, fontWeight: '800' }}>{user?.full_name}</Text>
            <Muted>{user?.username} · {user?.role_display}</Muted>
          </View>
        </View>
      </Card>

      <Card style={{ gap: 10 }}>
        <Title icon="contrast-outline">Appearance</Title>
        <Segmented
          options={[
            { value: 'system', label: 'System' },
            { value: 'light', label: 'Light' },
            { value: 'dark', label: 'Dark' },
          ]}
          value={mode}
          onChange={setMode}
        />
      </Card>

      <Card style={{ gap: 10 }}>
        <Title icon="lock-closed-outline">Account</Title>
        <Button
          title="Change password"
          variant="outline"
          icon="key-outline"
          onPress={() => navigation.navigate('ChangePassword')}
        />
      </Card>

      <Card style={{ gap: 10 }}>
        <Title icon="book-outline">Learn</Title>
        <Button
          title="Fazail-e-Darood"
          variant="outline"
          icon="book-outline"
          onPress={() => navigation.navigate('Fazail')}
        />
      </Card>

      <Button title="Log out" variant="danger" icon="log-out-outline" onPress={logout} />

      <Muted style={{ textAlign: 'center' }}>Darood Collection · connected to {API_URL}</Muted>
    </Screen>
  );
}
