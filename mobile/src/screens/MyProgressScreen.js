import React, { useState } from 'react';
import { RefreshControl, Text, View } from 'react-native';

import { api } from '../api/client';
import TrendChart from '../components/Chart';
import { Badge, Card, Empty, Loading, Muted, Row, Screen, Segmented, StatTile, Title, fmt } from '../components/UI';
import { RANGES, rangeParams } from '../constants';
import { useTheme } from '../context/ThemeContext';
import useFetch from '../hooks/useFetch';

const PERIOD_OPTS = [
  { value: 'day', label: 'Today' },
  { value: 'week', label: 'Week' },
  { value: 'month', label: 'Month' },
  { value: 'year', label: 'Year' },
  { value: 'all', label: 'All' },
];

function statusTone(s) {
  return s === 'approved' ? 'success' : s === 'pending' ? 'warning' : 'danger';
}

export default function MyProgressScreen() {
  const { colors } = useTheme();
  const [period, setPeriod] = useState('month');
  const [range, setRange] = useState('7d');
  const { data, loading, error, refetch } = useFetch('/darood/mine/', { period }, [period]);

  const [trend, setTrend] = useState(null);
  React.useEffect(() => {
    let alive = true;
    api
      .get('/charts/trend/', { params: rangeParams(range, { scope: 'mine' }) })
      .then((r) => alive && setTrend(r.data))
      .catch(() => alive && setTrend(null));
    return () => {
      alive = false;
    };
  }, [range]);

  if (loading && !data) return <Loading />;

  return (
    <Screen refreshControl={<RefreshControl refreshing={false} onRefresh={() => refetch(true)} />}>
      {error ? <Muted style={{ color: colors.danger }}>{error}</Muted> : null}

      <Row>
        <StatTile label="Total (period)" value={fmt(data?.total)} icon="sparkles" color={colors.primary} />
        <StatTile label="Entries" value={fmt(data?.entry_count)} icon="list-outline" />
      </Row>
      <Row>
        <StatTile label="Pending" value={fmt(data?.pending_count)} icon="hourglass-outline" color={colors.warning} />
      </Row>

      <Segmented options={PERIOD_OPTS} value={period} onChange={setPeriod} />

      <Card style={{ gap: 10 }}>
        <Title icon="trending-up-outline">My Trend</Title>
        <Segmented options={RANGES.map((r) => ({ value: r.key, label: r.label }))} value={range} onChange={setRange} />
        {trend ? (
          <TrendChart labels={trend.labels} datasets={[{ label: 'Darood', data: trend.totals }]} />
        ) : (
          <Muted>Loading chart…</Muted>
        )}
      </Card>

      <Card style={{ gap: 10 }}>
        <Title icon="time-outline">Recent</Title>
        {data?.recent?.length ? (
          data.recent.map((e) => (
            <View
              key={e.id}
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
                <Text style={{ color: colors.text, fontWeight: '700' }}>{fmt(e.count)} darood</Text>
                <Muted>{e.date}{e.manager_name ? ` · ${e.manager_name}` : ''}</Muted>
              </View>
              <Badge text={e.status_display} tone={statusTone(e.status)} />
            </View>
          ))
        ) : (
          <Empty text="No entries yet." />
        )}
      </Card>
    </Screen>
  );
}
