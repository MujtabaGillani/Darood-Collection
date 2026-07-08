import React, { useState } from 'react';
import { Text, View } from 'react-native';

import { Card, Empty, Loading, Muted, Row, Screen, Segmented, StatTile, Title, fmt } from '../components/UI';
import { useTheme } from '../context/ThemeContext';
import useFetch from '../hooks/useFetch';

const PERIOD_OPTS = [
  { value: 'day', label: 'Today' },
  { value: 'week', label: 'Week' },
  { value: 'month', label: 'Month' },
  { value: 'year', label: 'Year' },
  { value: 'all', label: 'All' },
];

export default function UserDetailScreen({ route, navigation }) {
  const { id, name } = route.params || {};
  const { colors } = useTheme();
  const [period, setPeriod] = useState('month');
  const { data, loading, error } = useFetch(`/users/${id}/`, { period }, [id, period]);

  React.useEffect(() => {
    if (name) navigation.setOptions({ title: name });
  }, [name, navigation]);

  if (loading && !data) return <Loading />;

  return (
    <Screen>
      {error ? <Muted style={{ color: colors.danger }}>{error}</Muted> : null}
      <Card>
        <Title icon="person-circle-outline">{data?.user?.full_name}</Title>
        <Muted>{data?.user?.username} · {data?.user?.role_display}</Muted>
      </Card>

      <Segmented options={PERIOD_OPTS} value={period} onChange={setPeriod} />

      <Row>
        <StatTile label="Total (period)" value={fmt(data?.total)} icon="sparkles" color={colors.primary} />
        <StatTile label="Entries" value={fmt(data?.entry_count)} icon="list-outline" />
      </Row>

      <Card style={{ gap: 8 }}>
        <Title icon="time-outline">Recent</Title>
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
              <Muted>{e.date}{e.recorded_by_name ? ` · by ${e.recorded_by_name}` : ''}</Muted>
              <Text style={{ color: colors.primary, fontWeight: '700' }}>{fmt(e.count)}</Text>
            </View>
          ))
        ) : (
          <Empty text="No approved darood for this period." />
        )}
      </Card>
    </Screen>
  );
}
