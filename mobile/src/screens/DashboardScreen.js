import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, RefreshControl, Text, View } from 'react-native';

import { api, apiErrorMessage } from '../api/client';
import TrendChart from '../components/Chart';
import MultiSelect from '../components/MultiSelect';
import {
  Badge, Button, Card, Empty, Field, Loading, Muted, Row, Screen, Segmented, StatTile, Title, fmt,
} from '../components/UI';
import { RANGES, formatRange, rangeParams } from '../constants';
import { appAlert } from '../context/DialogContext';
import { useTheme } from '../context/ThemeContext';
import useFetch from '../hooks/useFetch';

function Breakdown({ title, icon, datasets, start, end }) {
  const { colors } = useTheme();
  const [order, setOrder] = useState('desc');
  const rows = useMemo(() => {
    const list = (datasets || []).map((d) => ({
      label: d.label,
      total: d.data.reduce((a, b) => a + (b || 0), 0),
    }));
    list.sort((a, b) => (order === 'asc' ? a.total - b.total : b.total - a.total));
    return list;
  }, [datasets, order]);

  return (
    <Card style={{ gap: 8 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <View>
          <Title icon={icon}>{title}</Title>
          {start && end ? <Muted>{formatRange(start, end)}</Muted> : null}
        </View>
        <Segmented
          options={[{ value: 'desc', label: 'Highest' }, { value: 'asc', label: 'Lowest' }]}
          value={order}
          onChange={setOrder}
        />
      </View>
      {rows.length ? (
        rows.map((r, i) => (
          <View
            key={r.label + i}
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingVertical: 7,
              borderBottomWidth: 0.5,
              borderBottomColor: colors.border,
            }}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
              <View style={{ width: 24, height: 24, borderRadius: 12, backgroundColor: colors.primary + '22', alignItems: 'center', justifyContent: 'center' }}>
                <Text style={{ color: colors.primary, fontWeight: '700', fontSize: 11 }}>{i + 1}</Text>
              </View>
              <Text style={{ color: colors.text }}>{r.label}</Text>
            </View>
            <Badge text={fmt(r.total)} />
          </View>
        ))
      ) : (
        <Empty text="No data." />
      )}
    </Card>
  );
}

export default function DashboardScreen({ navigation }) {
  const { colors } = useTheme();
  const [range, setRange] = useState('7d');
  const [mgrIds, setMgrIds] = useState([]);
  const [usrIds, setUsrIds] = useState([]);

  const dash = useFetch('/stats/dashboard/', undefined, []);
  const [tops, setTops] = useState(null);
  const [mgrSeries, setMgrSeries] = useState(null);
  const [usrSeries, setUsrSeries] = useState(null);

  // User management: searchable + paginated so ALL users are reachable.
  const [userQ, setUserQ] = useState('');
  const [users, setUsers] = useState([]);
  const [userPage, setUserPage] = useState(1);
  const [userHasNext, setUserHasNext] = useState(false);
  const [usersLoading, setUsersLoading] = useState(false);

  const loadUsers = async (page, q) => {
    setUsersLoading(true);
    try {
      const r = await api.get('/users/', { params: { page, q } });
      setUsers((prev) => (page === 1 ? r.data.results : [...prev, ...r.data.results]));
      setUserHasNext(Boolean(r.data.next));
      setUserPage(page);
    } catch (e) {
      /* ignore */
    } finally {
      setUsersLoading(false);
    }
  };

  // Debounced search; also performs the initial load (q = '').
  useEffect(() => {
    const t = setTimeout(() => loadUsers(1, userQ), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userQ]);

  const applyUser = (updated) =>
    // Preserve darood_total (the update endpoint doesn't annotate it).
    setUsers((prev) => prev.map((u) => (u.id === updated.id ? { ...u, ...updated, darood_total: u.darood_total } : u)));

  useEffect(() => {
    const p = rangeParams(range);
    api.get('/stats/tops/', { params: p }).then((r) => setTops(r.data)).catch(() => {});
    api
      .get('/charts/managers/', { params: rangeParams(range, mgrIds.length ? { managers: mgrIds.join(',') } : {}) })
      .then((r) => setMgrSeries(r.data))
      .catch(() => {});
    api
      .get('/charts/users/', { params: rangeParams(range, usrIds.length ? { users: usrIds.join(',') } : {}) })
      .then((r) => setUsrSeries(r.data))
      .catch(() => {});
  }, [range, mgrIds, usrIds]);

  const chartDatasets = useMemo(() => {
    const ds = [...(mgrSeries?.datasets || [])];
    if (usrIds.length && usrSeries?.datasets) ds.push(...usrSeries.datasets);
    return ds;
  }, [mgrSeries, usrSeries, usrIds]);

  const setRole = async (u, role) => {
    try {
      const r = await api.patch(`/users/${u.id}/update/`, { role });
      applyUser(r.data);
      dash.refetch(true);
    } catch (e) {
      appAlert('Error', apiErrorMessage(e));
    }
  };
  const toggleActive = async (u) => {
    try {
      const r = await api.patch(`/users/${u.id}/update/`, { is_active: !u.is_active });
      applyUser(r.data);
      dash.refetch(true);
    } catch (e) {
      appAlert('Error', apiErrorMessage(e));
    }
  };

  if (dash.loading && !dash.data) return <Loading />;
  const d = dash.data || {};

  return (
    <Screen refreshControl={<RefreshControl refreshing={false} onRefresh={() => { dash.refetch(true); loadUsers(1, userQ); }} />}>
      <Row>
        <StatTile label="Total Darood" value={fmt(d.grand_total)} icon="sparkles" color={colors.accent} />
        <StatTile label="Users" value={fmt(d.total_users)} icon="people-outline" color={colors.primary} />
      </Row>
      <Row>
        <StatTile label="Active" value={fmt(d.active_count)} icon="person-outline" color={colors.success} />
        <StatTile label="Pending" value={fmt(d.pending_count)} icon="hourglass-outline" color={colors.danger} />
      </Row>

      <Row>
        <Card style={{ flex: 1 }}>
          <Muted>🏆 Top Collector</Muted>
          <Text style={{ color: colors.text, fontSize: 18, fontWeight: '800' }}>{tops?.top_manager?.name || '—'}</Text>
          <Muted>{fmt(tops?.top_manager?.total)} collected</Muted>
        </Card>
        <Card style={{ flex: 1 }}>
          <Muted>⭐ Top Reciter</Muted>
          <Text style={{ color: colors.text, fontSize: 18, fontWeight: '800' }}>{tops?.top_user?.name || '—'}</Text>
          <Muted>{fmt(tops?.top_user?.total)} darood</Muted>
        </Card>
      </Row>

      <Card style={{ gap: 10 }}>
        <Title icon="bar-chart-outline">Collection Trend</Title>
        {mgrSeries?.start ? <Muted>{formatRange(mgrSeries.start, mgrSeries.end)}</Muted> : null}
        <Segmented options={RANGES.map((r) => ({ value: r.key, label: r.label }))} value={range} onChange={setRange} />
        <Row>
          <MultiSelect
            label="Managers"
            emptyText="All"
            icon="ribbon-outline"
            options={d.managers || []}
            selected={mgrIds}
            onChange={setMgrIds}
          />
          <MultiSelect
            label="Users"
            emptyText="None"
            icon="person-outline"
            options={d.users || []}
            selected={usrIds}
            onChange={setUsrIds}
          />
        </Row>
        {mgrSeries ? (
          <TrendChart labels={mgrSeries.labels} datasets={chartDatasets} />
        ) : (
          <Muted>Loading chart…</Muted>
        )}
      </Card>

      <Breakdown title="Managers" icon="ribbon-outline" datasets={mgrSeries?.datasets} start={mgrSeries?.start} end={mgrSeries?.end} />
      <Breakdown title="Users" icon="person-outline" datasets={usrSeries?.datasets} start={usrSeries?.start} end={usrSeries?.end} />

      <Card style={{ gap: 10 }}>
        <Title icon="settings-outline">User Management</Title>
        <Field
          value={userQ}
          onChangeText={setUserQ}
          placeholder="Search users…"
          autoCapitalize="none"
          autoCorrect={false}
        />
        {users.map((u) => (
          <View key={u.id} style={{ gap: 8, paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: colors.border }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <Pressable onPress={() => navigation.navigate('UserDetail', { id: u.id, name: u.full_name })}>
                <Text style={{ color: colors.text, fontWeight: '700' }}>{u.full_name}</Text>
                <Muted>{u.username} · {fmt(u.darood_total)} darood</Muted>
              </Pressable>
              <Badge text={u.is_active ? 'Active' : 'Pending'} tone={u.is_active ? 'success' : 'muted'} />
            </View>
            {u.is_superadmin ? (
              <Badge text="Super Admin" tone="primary" />
            ) : (
              <Row>
                <Segmented
                  style={{ flex: 1 }}
                  options={[{ value: 'simple', label: 'Simple' }, { value: 'manager', label: 'Manager' }]}
                  value={u.role}
                  onChange={(role) => role !== u.role && setRole(u, role)}
                />
                <Button
                  title={u.is_active ? 'Deactivate' : 'Activate'}
                  variant={u.is_active ? 'danger' : 'outline'}
                  onPress={() => toggleActive(u)}
                />
              </Row>
            )}
          </View>
        ))}
        {users.length === 0 && !usersLoading ? <Empty text="No users found." /> : null}
        {userHasNext ? (
          <Button
            title={usersLoading ? 'Loading…' : 'Load more'}
            variant="outline"
            icon="chevron-down"
            loading={usersLoading}
            onPress={() => loadUsers(userPage + 1, userQ)}
          />
        ) : null}
      </Card>
    </Screen>
  );
}
