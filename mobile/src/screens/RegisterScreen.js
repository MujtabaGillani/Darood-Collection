import React, { useState } from 'react';
import { Text, View } from 'react-native';

import { apiErrorMessage } from '../api/client';
import { Button, Card, Field, Muted, PasswordField, Screen } from '../components/UI';
import { useAuth } from '../context/AuthContext';
import { appAlert } from '../context/DialogContext';
import { useTheme } from '../context/ThemeContext';

export default function RegisterScreen({ navigation }) {
  const { colors } = useTheme();
  const { register } = useAuth();
  const [form, setForm] = useState({
    username: '',
    first_name: '',
    last_name: '',
    password: '',
    password2: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));

  const onSubmit = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await register({ ...form, username: form.username.trim() });
      appAlert('Registration successful', res.detail, () => navigation.navigate('Login'));
    } catch (e) {
      setError(apiErrorMessage(e, 'Registration failed.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <Card style={{ gap: 14 }}>
        <Text style={{ fontSize: 18, fontWeight: '700', color: colors.text }}>Create your account</Text>
        {error ? (
          <View style={{ backgroundColor: colors.danger + '22', borderRadius: 8, padding: 10 }}>
            <Text style={{ color: colors.danger }}>{error}</Text>
          </View>
        ) : null}
        <Field label="Username" value={form.username} onChangeText={set('username')} autoCapitalize="none" />
        <Field label="First name" value={form.first_name} onChangeText={set('first_name')} />
        <Field label="Last name" value={form.last_name} onChangeText={set('last_name')} />
        <PasswordField label="Password" value={form.password} onChangeText={set('password')} />
        <PasswordField label="Confirm password" value={form.password2} onChangeText={set('password2')} />
        <Button title="Register" icon="person-add-outline" onPress={onSubmit} loading={loading} />
        <Muted>Your account will be inactive until a Super Admin approves it.</Muted>
      </Card>
    </Screen>
  );
}
