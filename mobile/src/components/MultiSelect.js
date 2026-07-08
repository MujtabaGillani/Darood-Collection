import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { Modal, Pressable, ScrollView, Text, View } from 'react-native';

import { useTheme } from '../context/ThemeContext';

/**
 * Compact dropdown multi-select. Button shows "Label · N" (or the empty text),
 * and tapping opens a themed bottom-sheet checkbox list.
 *
 * options: [{ id, name }], selected: id[], onChange: (id[]) => void
 */
export default function MultiSelect({ label, emptyText = 'All', icon, options, selected, onChange }) {
  const { colors } = useTheme();
  const [open, setOpen] = useState(false);

  const toggle = (id) =>
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);

  const count = selected.length;

  return (
    <>
      <Pressable
        onPress={() => setOpen(true)}
        style={{
          flex: 1,
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderWidth: 1,
          borderColor: colors.primary,
          borderRadius: 10,
          paddingVertical: 9,
          paddingHorizontal: 12,
          gap: 6,
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, flexShrink: 1 }}>
          {icon ? <Ionicons name={icon} size={16} color={colors.primary} /> : null}
          <Text numberOfLines={1} style={{ color: colors.primary, fontWeight: '700', fontSize: 13 }}>
            {label} · {count ? count : emptyText}
          </Text>
        </View>
        <Ionicons name="chevron-down" size={16} color={colors.primary} />
      </Pressable>

      <Modal transparent visible={open} animationType="slide" statusBarTranslucent onRequestClose={() => setOpen(false)}>
        <Pressable onPress={() => setOpen(false)} style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.55)', justifyContent: 'flex-end' }}>
          <Pressable
            onPress={() => {}}
            style={{
              backgroundColor: colors.card,
              borderTopLeftRadius: 20,
              borderTopRightRadius: 20,
              maxHeight: '70%',
            }}
          >
            <View style={{ height: 4, width: 44, backgroundColor: colors.border, borderRadius: 2, alignSelf: 'center', marginTop: 10 }} />
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 }}>
              <Text style={{ color: colors.text, fontWeight: '800', fontSize: 16 }}>{label}</Text>
              {count > 0 ? (
                <Pressable onPress={() => onChange([])}>
                  <Text style={{ color: colors.primary, fontWeight: '700' }}>Clear</Text>
                </Pressable>
              ) : null}
            </View>

            <ScrollView>
              {options.map((o) => {
                const active = selected.includes(o.id);
                return (
                  <Pressable
                    key={o.id}
                    onPress={() => toggle(o.id)}
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      gap: 12,
                      paddingVertical: 13,
                      paddingHorizontal: 16,
                      borderTopWidth: 0.5,
                      borderTopColor: colors.border,
                    }}
                  >
                    <Ionicons
                      name={active ? 'checkbox' : 'square-outline'}
                      size={22}
                      color={active ? colors.primary : colors.muted}
                    />
                    <Text style={{ color: colors.text, fontSize: 15 }}>{o.name}</Text>
                  </Pressable>
                );
              })}
              {options.length === 0 ? <Text style={{ color: colors.muted, padding: 16 }}>No options.</Text> : null}
            </ScrollView>

            <View style={{ padding: 16 }}>
              <Pressable
                onPress={() => setOpen(false)}
                style={{ backgroundColor: colors.primary, borderRadius: 12, paddingVertical: 13, alignItems: 'center' }}
              >
                <Text style={{ color: '#fff', fontWeight: '700', fontSize: 15 }}>Done</Text>
              </Pressable>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </>
  );
}
