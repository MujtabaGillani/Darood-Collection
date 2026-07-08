import React, { useEffect, useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { api, apiErrorMessage } from '../api/client';
import DateField, { todayISO } from '../components/DateField';
import { Button, Card, Field, Muted, Screen, Title, fmt } from '../components/UI';
import { appAlert } from '../context/DialogContext';
import { useTheme } from '../context/ThemeContext';

export default function SubmitDaroodScreen() {
  const { colors } = useTheme();
  const [managers, setManagers] = useState([]);
  const [managerId, setManagerId] = useState(null);
  const [date, setDate] = useState(todayISO());
  const [count, setCount] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/users/managers/').then((r) => setManagers(r.data)).catch(() => {});
  }, []);

  const submit = async () => {
    setError('');
    if (!managerId) return setError('Please choose a manager.');
    if (!count || Number(count) < 1) return setError('Enter a count of at least 1.');
    setSaving(true);
    try {
      const r = await api.post('/darood/submit/', { manager: managerId, date, count: Number(count) });
      appAlert('Submitted', `${fmt(r.data.count)} darood sent for approval. It will count once approved.`);
      setCount('');
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Screen>
      <Card style={{ gap: 12 }}>
        <Title icon="send-outline">Submit Darood</Title>
        <Muted>Send your count to a manager. It counts once they approve it.</Muted>
        {error ? <Muted style={{ color: colors.danger }}>{error}</Muted> : null}

        <Text style={{ color: colors.text, fontWeight: '600' }}>Send to manager</Text>
        <View style={{ gap: 8 }}>
          {managers.map((m) => {
            const active = m.id === managerId;
            return (
              <Pressable
                key={m.id}
                onPress={() => setManagerId(m.id)}
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  gap: 8,
                  padding: 10,
                  borderRadius: 10,
                  borderWidth: 1,
                  borderColor: active ? colors.primary : colors.border,
                  backgroundColor: active ? colors.chipBg : 'transparent',
                }}
              >
                <View
                  style={{
                    width: 18,
                    height: 18,
                    borderRadius: 9,
                    borderWidth: 2,
                    borderColor: colors.primary,
                    backgroundColor: active ? colors.primary : 'transparent',
                  }}
                />
                <Text style={{ color: colors.text }}>{m.full_name}</Text>
              </Pressable>
            );
          })}
          {managers.length === 0 ? <Muted>No managers available yet.</Muted> : null}
        </View>

        <DateField label="Date" value={date} onChange={setDate} />
        <Field label="Count" value={count} onChangeText={setCount} placeholder="e.g. 500" keyboardType="number-pad" />
        <Button title="Submit for approval" icon="paper-plane-outline" onPress={submit} loading={saving} />
      </Card>
    </Screen>
  );
}
