import { Ionicons } from '@expo/vector-icons';
import * as SecureStore from 'expo-secure-store';
import React, { useEffect, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { apiErrorMessage } from '../api/client';
import { Button, Card, Checkbox, Field, Muted, PasswordField } from '../components/UI';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const REMEMBER_KEY = 'dc_remember_creds';
const ASTANA = 'آستانہ عالیہ کشفیہ نظامیہ';
const VERSE =
  'بے شک اللہ اور اس کے فرشتے نبی پر درود بھیجتے ہیں۔ اے ایمان والو! تم بھی ان پر درود بھیجو اور خوب سلام بھیجا کرو۔';

export default function LoginScreen({ navigation }) {
  const { colors } = useTheme();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Prefill remembered credentials (stored in secure storage) on open.
  useEffect(() => {
    (async () => {
      try {
        const raw = await SecureStore.getItemAsync(REMEMBER_KEY);
        if (raw) {
          const c = JSON.parse(raw);
          setUsername(c.u || '');
          setPassword(c.p || '');
          setRemember(true);
        }
      } catch (e) {
        /* ignore corrupt value */
      }
    })();
  }, []);

  const onSubmit = async () => {
    setError('');
    setLoading(true);
    try {
      // Remember (or forget) the credentials for next time.
      if (remember) {
        await SecureStore.setItemAsync(REMEMBER_KEY, JSON.stringify({ u: username.trim(), p: password }));
      } else {
        await SecureStore.deleteItemAsync(REMEMBER_KEY);
      }
      await login(username.trim(), password, remember);
    } catch (e) {
      setError(apiErrorMessage(e, 'Login failed.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.primaryDark }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', padding: 20, gap: 18 }}
          keyboardShouldPersistTaps="handled"
        >
          <Card style={{ gap: 12, padding: 22 }}>
            {/* Astana name + gold divider (matches the web auth card) */}
            <Text
              style={{
                color: colors.primary,
                fontSize: 18,
                textAlign: 'center',
                writingDirection: 'rtl',
                fontWeight: '600',
              }}
            >
              {ASTANA}
            </Text>
            <View style={{ height: 1, backgroundColor: colors.accent, opacity: 0.55, marginBottom: 4 }} />

            {/* Brand */}
            <View style={{ alignItems: 'center', gap: 4, marginBottom: 6 }}>
              <Ionicons name="sparkles" size={34} color={colors.primary} />
              <Text style={{ fontSize: 22, fontWeight: '800', color: colors.text }}>Darood Collection</Text>
              <Muted>Sign in to continue</Muted>
            </View>

            {error ? (
              <View style={{ backgroundColor: colors.danger + '22', borderRadius: 8, padding: 10 }}>
                <Text style={{ color: colors.danger }}>{error}</Text>
              </View>
            ) : null}

            <Field
              label="Username"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              autoCorrect={false}
              placeholder="your username"
            />
            <PasswordField label="Password" value={password} onChangeText={setPassword} placeholder="••••••••" />

            <Checkbox checked={remember} onToggle={() => setRemember((r) => !r)} label="Remember me" />

            <Button title="Login" icon="log-in-outline" onPress={onSubmit} loading={loading} />

            <View style={{ flexDirection: 'row', justifyContent: 'center', gap: 6, marginTop: 2 }}>
              <Muted>No account?</Muted>
              <Pressable onPress={() => navigation.navigate('Register')}>
                <Text style={{ color: colors.primary, fontWeight: '700', textDecorationLine: 'underline' }}>
                  Register here
                </Text>
              </Pressable>
            </View>
          </Card>

          {/* Darood verse on the teal background, like the web auth footer */}
          <Text
            style={{
              color: 'rgba(255,255,255,0.9)',
              textAlign: 'center',
              writingDirection: 'rtl',
              fontSize: 14,
              lineHeight: 26,
              paddingHorizontal: 6,
            }}
          >
            {VERSE}
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
