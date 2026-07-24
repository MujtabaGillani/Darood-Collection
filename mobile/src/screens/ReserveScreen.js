import React, { useState } from 'react';
import { RefreshControl, Text, View } from 'react-native';

import { api, apiErrorMessage } from '../api/client';
import DateField, { todayISO } from '../components/DateField';
import {
  Badge,
  Button,
  Card,
  Empty,
  Field,
  Loading,
  Muted,
  Row,
  Screen,
  Segmented,
  StatTile,
  Title,
  fmt,
} from '../components/UI';
import { appAlert } from '../context/DialogContext';
import { useTheme } from '../context/ThemeContext';
import useFetch from '../hooks/useFetch';

const MODE_OPTS = [
  { value: 'add', label: 'Add to reserve' },
  { value: 'use', label: 'Use reserve' },
];

export default function ReserveScreen() {
  const { colors } = useTheme();
  const { data, loading, refetch } = useFetch('/darood/reserve/');

  const [mode, setMode] = useState('add');
  const [date, setDate] = useState(todayISO());
  const [count, setCount] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const balance = data?.balance || 0;

  const submit = async () => {
    setError('');
    const n = Number(count);
    if (!count || n < 1) return setError('Enter a count of at least 1.');
    if (mode === 'use' && n > balance) return setError(`You only have ${fmt(balance)} darood in reserve.`);
    setSaving(true);
    try {
      const path = mode === 'add' ? '/darood/reserve/add/' : '/darood/reserve/submit/';
      await api.post(path, { date, count: n });
      appAlert(
        mode === 'add' ? 'Added to reserve' : 'Submitted',
        mode === 'add'
          ? `${fmt(n)} darood added to your reserve for ${date}.`
          : `${fmt(n)} darood submitted from your reserve for ${date}. It now counts toward the total.`
      );
      setCount('');
      refetch(true);
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  if (loading && !data) return <Loading />;

  return (
    <Screen refreshControl={<RefreshControl refreshing={false} onRefresh={() => refetch(true)} />}>
      <Row>
        <StatTile label="In reserve" value={fmt(balance)} icon="lock-closed-outline" color={colors.primary} />
        <StatTile label="Added" value={fmt(data?.added)} icon="add-outline" />
      </Row>
      <Row>
        <StatTile label="Submitted" value={fmt(data?.submitted)} icon="checkmark-done-outline" color={colors.success} />
      </Row>

      <Card style={{ gap: 12 }}>
        <Title icon="lock-closed-outline">Reserve Darood</Title>
        <Muted>
          Privately stash darood, then submit it later. It stays hidden and does not count until you submit it.
        </Muted>

        <Segmented options={MODE_OPTS} value={mode} onChange={setMode} />
        {error ? <Muted style={{ color: colors.danger }}>{error}</Muted> : null}

        {mode === 'use' && balance < 1 ? (
          <Muted>Your reserve is empty. Add some darood first.</Muted>
        ) : (
          <>
            {mode === 'use' ? (
              <Muted>You have {fmt(balance)} darood in reserve. Choose how many to submit.</Muted>
            ) : null}
            <DateField label="Date" value={date} onChange={setDate} />
            <Field label="Quantity" value={count} onChangeText={setCount} placeholder="e.g. 500" keyboardType="number-pad" />
            <Button
              title={mode === 'add' ? 'Add to Reserve' : 'Submit from Reserve'}
              icon={mode === 'add' ? 'lock-closed-outline' : 'arrow-up-circle-outline'}
              onPress={submit}
              loading={saving}
            />
          </>
        )}
      </Card>

      <Card style={{ gap: 10 }}>
        <Title icon="time-outline">Reserve History</Title>
        {data?.history?.length ? (
          data.history.map((t) => (
            <View
              key={t.id}
              style={{
                flexDirection: 'row',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingVertical: 8,
                borderBottomWidth: 0.5,
                borderBottomColor: colors.border,
              }}
            >
              <View>
                <Text style={{ color: colors.text, fontWeight: '700' }}>{fmt(t.count)} darood</Text>
                <Muted>{t.date}</Muted>
              </View>
              <Badge text={t.kind === 'add' ? 'Added' : 'Submitted'} tone={t.kind === 'add' ? 'muted' : 'success'} />
            </View>
          ))
        ) : (
          <Empty text="No reserve activity yet." />
        )}
      </Card>
    </Screen>
  );
}
