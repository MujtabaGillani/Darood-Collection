import React, { useState } from 'react';
import { Pressable, RefreshControl, Text, View } from 'react-native';

import { Badge, Card, Empty, Loading, Muted, Row, Screen, Segmented, StatTile, Title, fmt } from '../components/UI';
import { useTheme } from '../context/ThemeContext';
import useFetch from '../hooks/useFetch';

const PERIOD_OPTS = [
  { value: 'day', label: 'Today' },
  { value: 'week', label: 'Week' },
  { value: 'month', label: 'Month' },
  { value: 'year', label: 'Year' },
  { value: 'all', label: 'All' },
];

export default function OverviewScreen({ navigation }) {
  const { colors } = useTheme();
  const [period, setPeriod] = useState('month');
  const { data, loading, error, refetch } = useFetch('/darood/overview/', { period }, [period]);

  if (loading && !data) return <Loading />;

  return (
    <Screen refreshControl={<RefreshControl refreshing={false} onRefresh={() => refetch(true)} />}>
      {error ? <Muted style={{ color: colors.danger }}>{error}</Muted> : null}
      <Segmented options={PERIOD_OPTS} value={period} onChange={setPeriod} />

      <Row>
        <StatTile label="Total darood" value={fmt(data?.total)} icon="sparkles" color={colors.primary} />
        <StatTile label="Entries" value={fmt(data?.entry_count)} icon="list-outline" />
      </Row>
      <Row>
        <StatTile label="Contributors" value={fmt(data?.contributor_count)} icon="people-outline" />
      </Row>

      <Card style={{ gap: 6 }}>
        <Title icon="trophy-outline">Leaderboard</Title>
        {data?.leaderboard?.length ? (
          data.leaderboard.map((row, i) => (
            <Pressable
              key={row.user_id}
              onPress={() => navigation.navigate('UserDetail', { id: row.user_id, name: row.name })}
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingVertical: 9,
                borderBottomWidth: 0.5,
                borderBottomColor: colors.border,
              }}
            >
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                <View
                  style={{
                    width: 26,
                    height: 26,
                    borderRadius: 13,
                    backgroundColor: colors.primary + '22',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Text style={{ color: colors.primary, fontWeight: '700', fontSize: 12 }}>{i + 1}</Text>
                </View>
                <Text style={{ color: colors.text, fontWeight: '600' }}>{row.name}</Text>
              </View>
              <Badge text={fmt(row.total)} />
            </Pressable>
          ))
        ) : (
          <Empty text="No data for this period." />
        )}
      </Card>

      <Card style={{ gap: 8 }}>
        <Title icon="time-outline">Recent entries</Title>
        {data?.recent?.length ? (
          data.recent.map((e) => (
            <View
              key={e.id}
              style={{
                flexDirection: 'row',
                justifyContent: 'space-between',
                paddingVertical: 7,
                borderBottomWidth: 0.5,
                borderBottomColor: colors.border,
              }}
            >
              <View>
                <Text style={{ color: colors.text, fontWeight: '600' }}>{e.user_name}</Text>
                <Muted>{e.date}{e.recorded_by_name ? ` · by ${e.recorded_by_name}` : ''}</Muted>
              </View>
              <Text style={{ color: colors.primary, fontWeight: '700' }}>{fmt(e.count)}</Text>
            </View>
          ))
        ) : (
          <Empty text="No recent entries." />
        )}
      </Card>
    </Screen>
  );
}
