import { Ionicons } from '@expo/vector-icons';
import React, { useMemo, useState } from 'react';
import { Modal, Pressable, Text, View } from 'react-native';

import { useTheme } from '../context/ThemeContext';

// Local YYYY-MM-DD (avoids the UTC off-by-one that toISOString() causes).
export function toISODate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function todayISO() {
  return toISODate(new Date());
}

const WEEKDAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];
const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function ymd(d) {
  return d.getFullYear() * 10000 + d.getMonth() * 100 + d.getDate();
}

/**
 * Tap-to-open calendar date field, fully themed to the app palette (no native
 * dialog, so it looks the same on every platform and in light/dark).
 * `value` is a 'YYYY-MM-DD' string; `onChange` receives the same. Future dates
 * (after `maximumDate`) are disabled.
 */
export default function DateField({ label, value, onChange, maximumDate = new Date() }) {
  const { colors } = useTheme();
  const [open, setOpen] = useState(false);

  const selected = value ? new Date(`${value}T00:00:00`) : new Date();
  const [view, setView] = useState(new Date(selected.getFullYear(), selected.getMonth(), 1));

  const maxKey = ymd(maximumDate);
  const selKey = value ? ymd(selected) : -1;

  const cells = useMemo(() => {
    const year = view.getFullYear();
    const month = view.getMonth();
    const firstDow = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const arr = [];
    for (let i = 0; i < firstDow; i++) arr.push(null);
    for (let d = 1; d <= daysInMonth; d++) arr.push(new Date(year, month, d));
    return arr;
  }, [view]);

  const canGoNext =
    view.getFullYear() < maximumDate.getFullYear() ||
    (view.getFullYear() === maximumDate.getFullYear() && view.getMonth() < maximumDate.getMonth());

  const openPicker = () => {
    setView(new Date(selected.getFullYear(), selected.getMonth(), 1));
    setOpen(true);
  };

  const pick = (d) => {
    onChange(toISODate(d));
    setOpen(false);
  };

  const headerLabel = value
    ? `${DOW[selected.getDay()]}, ${MONTHS[selected.getMonth()].slice(0, 3)} ${selected.getDate()}`
    : 'Select a date';

  return (
    <View style={{ gap: 6 }}>
      {label ? <Text style={{ color: colors.text, fontWeight: '600' }}>{label}</Text> : null}
      <Pressable
        onPress={openPicker}
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: colors.inputBg,
          borderColor: colors.border,
          borderWidth: 1,
          borderRadius: 10,
          paddingHorizontal: 12,
          paddingVertical: 12,
        }}
      >
        <Text style={{ color: value ? colors.text : colors.muted, fontSize: 15 }}>
          {value || 'Select a date'}
        </Text>
        <Ionicons name="calendar-outline" size={18} color={colors.primary} />
      </Pressable>

      <Modal transparent visible={open} animationType="fade" statusBarTranslucent onRequestClose={() => setOpen(false)}>
        <Pressable
          onPress={() => setOpen(false)}
          style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.55)', alignItems: 'center', justifyContent: 'center', padding: 24 }}
        >
          <Pressable
            onPress={() => {}}
            style={{ width: '100%', maxWidth: 360, backgroundColor: colors.card, borderRadius: 16, overflow: 'hidden', borderWidth: 1, borderColor: colors.border }}
          >
            {/* Header — teal, shows the selected date */}
            <View style={{ backgroundColor: colors.primary, padding: 18 }}>
              <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 14, fontWeight: '600' }}>
                {selected.getFullYear()}
              </Text>
              <Text style={{ color: '#fff', fontSize: 26, fontWeight: '800' }}>{headerLabel}</Text>
            </View>

            <View style={{ padding: 14 }}>
              {/* Month nav */}
              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <Pressable
                  onPress={() => setView(new Date(view.getFullYear(), view.getMonth() - 1, 1))}
                  hitSlop={10}
                  style={{ padding: 6 }}
                >
                  <Ionicons name="chevron-back" size={20} color={colors.text} />
                </Pressable>
                <Text style={{ color: colors.text, fontWeight: '700', fontSize: 15 }}>
                  {MONTHS[view.getMonth()]} {view.getFullYear()}
                </Text>
                <Pressable
                  onPress={() => canGoNext && setView(new Date(view.getFullYear(), view.getMonth() + 1, 1))}
                  hitSlop={10}
                  style={{ padding: 6, opacity: canGoNext ? 1 : 0.25 }}
                  disabled={!canGoNext}
                >
                  <Ionicons name="chevron-forward" size={20} color={colors.text} />
                </Pressable>
              </View>

              {/* Weekday header */}
              <View style={{ flexDirection: 'row' }}>
                {WEEKDAYS.map((w, i) => (
                  <Text key={i} style={{ flex: 1, textAlign: 'center', color: colors.muted, fontSize: 12, fontWeight: '600' }}>
                    {w}
                  </Text>
                ))}
              </View>

              {/* Day grid */}
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 6 }}>
                {cells.map((d, i) => {
                  if (!d) return <View key={i} style={{ width: `${100 / 7}%`, height: 40 }} />;
                  const key = ymd(d);
                  const isSel = key === selKey;
                  const disabled = key > maxKey;
                  return (
                    <View key={i} style={{ width: `${100 / 7}%`, height: 40, alignItems: 'center', justifyContent: 'center' }}>
                      <Pressable
                        onPress={() => !disabled && pick(d)}
                        disabled={disabled}
                        style={{
                          width: 34,
                          height: 34,
                          borderRadius: 17,
                          alignItems: 'center',
                          justifyContent: 'center',
                          backgroundColor: isSel ? colors.primary : 'transparent',
                        }}
                      >
                        <Text
                          style={{
                            color: isSel ? '#fff' : disabled ? colors.muted : colors.text,
                            opacity: disabled ? 0.4 : 1,
                            fontWeight: isSel ? '800' : '500',
                          }}
                        >
                          {d.getDate()}
                        </Text>
                      </Pressable>
                    </View>
                  );
                })}
              </View>

              {/* Actions */}
              <View style={{ flexDirection: 'row', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                <Pressable onPress={() => setOpen(false)} style={{ paddingVertical: 8, paddingHorizontal: 14 }}>
                  <Text style={{ color: colors.muted, fontWeight: '700' }}>CANCEL</Text>
                </Pressable>
                <Pressable onPress={() => setOpen(false)} style={{ paddingVertical: 8, paddingHorizontal: 14 }}>
                  <Text style={{ color: colors.primary, fontWeight: '700' }}>OK</Text>
                </Pressable>
              </View>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}
