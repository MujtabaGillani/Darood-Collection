import React from 'react';
import { RefreshControl, Text, View } from 'react-native';

import { api, apiErrorMessage } from '../api/client';
import { Badge, Button, Card, Empty, Loading, Muted, Row, Screen, Title, fmt } from '../components/UI';
import { appAlert } from '../context/DialogContext';
import { useTheme } from '../context/ThemeContext';
import useFetch from '../hooks/useFetch';

export default function ApprovalsScreen() {
  const { colors } = useTheme();
  const { data, loading, error, refetch } = useFetch('/darood/approvals/', undefined, []);
  const [busy, setBusy] = React.useState(null);

  const review = async (id, decision) => {
    setBusy(id + decision);
    try {
      await api.post(`/darood/${id}/review/`, { decision });
      await refetch(true);
    } catch (e) {
      appAlert('Error', apiErrorMessage(e));
    } finally {
      setBusy(null);
    }
  };

  if (loading && !data) return <Loading />;

  return (
    <Screen refreshControl={<RefreshControl refreshing={false} onRefresh={() => refetch(true)} />}>
      {error ? <Muted style={{ color: colors.danger }}>{error}</Muted> : null}

      <Card style={{ gap: 12 }}>
        <Title icon="checkmark-done-outline">Pending ({data?.pending?.length || 0})</Title>
        {data?.pending?.length ? (
          data.pending.map((e) => (
            <View
              key={e.id}
              style={{ gap: 8, paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: colors.border }}
            >
              <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                <View>
                  <Text style={{ color: colors.text, fontWeight: '700' }}>{e.user_name}</Text>
                  <Muted>{fmt(e.count)} darood · {e.date}</Muted>
                </View>
                <Badge text="Pending" tone="warning" />
              </View>
              <Row>
                <Button
                  title="Approve"
                  icon="checkmark"
                  style={{ flex: 1 }}
                  loading={busy === e.id + 'approve'}
                  onPress={() => review(e.id, 'approve')}
                />
                <Button
                  title="Reject"
                  icon="close"
                  variant="danger"
                  style={{ flex: 1 }}
                  loading={busy === e.id + 'reject'}
                  onPress={() => review(e.id, 'reject')}
                />
              </Row>
            </View>
          ))
        ) : (
          <Empty text="Nothing awaiting review." icon="checkmark-circle-outline" />
        )}
      </Card>

      <Card style={{ gap: 8 }}>
        <Title icon="time-outline">Recently reviewed</Title>
        {data?.reviewed?.length ? (
          data.reviewed.map((e) => (
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
                <Muted>{fmt(e.count)} · {e.date}</Muted>
              </View>
              <Badge text={e.status_display} tone={e.status === 'approved' ? 'success' : 'danger'} />
            </View>
          ))
        ) : (
          <Empty text="No reviews yet." />
        )}
      </Card>
    </Screen>
  );
}
