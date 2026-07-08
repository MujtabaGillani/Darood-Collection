import React, { useState } from 'react';
import { Text, View } from 'react-native';

import { api, apiErrorMessage } from '../api/client';
import { Button, Card, Muted, PasswordField, Screen, Title } from '../components/UI';
import { appAlert } from '../context/DialogContext';
import { useTheme } from '../context/ThemeContext';

export default function ChangePasswordScreen({ navigation }) {
  const { colors } = useTheme();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setError('');
    if (!current || !next || !confirm) return setError('Please fill in all fields.');
    if (next !== confirm) return setError('The new passwords do not match.');
    setLoading(true);
    try {
      await api.post('/auth/change-password/', {
        current_password: current,
        new_password: next,
        new_password2: confirm,
      });
      appAlert('Password changed', 'Your password has been updated.', () => navigation.goBack());
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <Card style={{ gap: 12 }}>
        <Title icon="key-outline">Change Password</Title>
        <Muted>Enter your current password, then choose a new one.</Muted>
        {error ? (
          <View style={{ backgroundColor: colors.danger + '22', borderRadius: 8, padding: 10 }}>
            <Text style={{ color: colors.danger }}>{error}</Text>
          </View>
        ) : null}
        <PasswordField label="Current password" value={current} onChangeText={setCurrent} placeholder="••••••••" />
        <PasswordField label="New password" value={next} onChangeText={setNext} placeholder="••••••••" />
        <PasswordField label="Confirm new password" value={confirm} onChangeText={setConfirm} placeholder="••••••••" />
        <Button title="Update password" icon="checkmark-circle-outline" onPress={submit} loading={loading} />
      </Card>
    </Screen>
  );
}
