import { Ionicons } from '@expo/vector-icons';
import React, { useEffect, useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { api, apiErrorMessage } from '../api/client';
import DateField, { todayISO } from '../components/DateField';
import { Button, Card, Field, Muted, Screen, Title, fmt } from '../components/UI';
import { appAlert } from '../context/DialogContext';
import { useTheme } from '../context/ThemeContext';

export default function AddDaroodScreen() {
  const { colors } = useTheme();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [date, setDate] = useState(todayISO());
  const [count, setCount] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [newUsername, setNewUsername] = useState('');

  // Search-as-you-type (debounced). Only query once the user has typed
  // something — an empty box shows no list rather than every user.
  useEffect(() => {
    if (selected) return;
    const q = query.trim();
    if (q.length < 1) {
      setResults([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const r = await api.get('/users/search/', { params: { q } });
        setResults(r.data);
      } catch (e) {
        /* ignore */
      }
    }, 250);
    return () => clearTimeout(t);
  }, [query, selected]);

  const record = async () => {
    setError('');
    if (!selected) return setError('Please search and select a user.');
    if (!count || Number(count) < 1) return setError('Enter a count of at least 1.');
    setSaving(true);
    try {
      const r = await api.post('/darood/record/', {
        user: selected.id,
        date,
        count: Number(count),
      });
      appAlert('Recorded', `${fmt(r.data.count)} darood for ${r.data.user_name} on ${r.data.date}.`);
      setSelected(null);
      setQuery('');
      setCount('');
      setResults([]);
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const quickAdd = async () => {
    if (!newUsername.trim()) return;
    try {
      const r = await api.post('/users/quick-add/', { username: newUsername.trim() });
      appAlert('User created', `${r.data.user.username} (password: ${r.data.default_password})`);
      setSelected(r.data.user);
      setNewUsername('');
      setShowQuickAdd(false);
    } catch (e) {
      appAlert('Could not create user', apiErrorMessage(e));
    }
  };

  return (
    <Screen>
      <Card style={{ gap: 12 }}>
        <Title icon="add-circle-outline">Record Darood</Title>
        {error ? <Muted style={{ color: colors.danger }}>{error}</Muted> : null}

        {selected ? (
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: colors.chipBg,
              borderColor: colors.chipBorder,
              borderWidth: 1,
              borderRadius: 10,
              padding: 12,
            }}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Ionicons name="person-circle-outline" size={22} color={colors.primary} />
              <View>
                <Text style={{ color: colors.text, fontWeight: '700' }}>{selected.full_name}</Text>
                <Muted>{selected.username} · {selected.role_display}</Muted>
              </View>
            </View>
            <Pressable onPress={() => setSelected(null)}>
              <Ionicons name="close-circle" size={22} color={colors.muted} />
            </Pressable>
          </View>
        ) : (
          <>
            <Field
              label="Search user"
              value={query}
              onChangeText={setQuery}
              placeholder="name or username"
              autoCapitalize="none"
            />
            {results.map((u) => (
              <Pressable
                key={u.id}
                onPress={() => setSelected(u)}
                style={{ paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: colors.border }}
              >
                <Text style={{ color: colors.text, fontWeight: '600' }}>{u.full_name}</Text>
                <Muted>{u.username} · {u.role_display}</Muted>
              </Pressable>
            ))}
            {query.trim().length < 1 ? (
              <Muted>Type a name or username to search.</Muted>
            ) : results.length === 0 ? (
              <Muted>No matching users.</Muted>
            ) : null}
          </>
        )}

        <DateField label="Date" value={date} onChange={setDate} />
        <Field label="Count" value={count} onChangeText={setCount} placeholder="e.g. 500" keyboardType="number-pad" />
        <Button title="Record Darood" icon="checkmark-circle-outline" onPress={record} loading={saving} />
      </Card>

      <Card style={{ gap: 10 }}>
        <Pressable
          onPress={() => setShowQuickAdd((v) => !v)}
          style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <Title icon="person-add-outline">Quick add user</Title>
          <Ionicons name={showQuickAdd ? 'chevron-up' : 'chevron-down'} size={18} color={colors.muted} />
        </Pressable>
        {showQuickAdd ? (
          <>
            <Field label="Username" value={newUsername} onChangeText={setNewUsername} autoCapitalize="none" />
            <Button title="Create Simple User" variant="outline" icon="add-outline" onPress={quickAdd} />
            <Muted>Created active with the default password so you can record right away.</Muted>
          </>
        ) : null}
      </Card>
    </Screen>
  );
}
