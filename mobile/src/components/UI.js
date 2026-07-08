import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useTheme } from '../context/ThemeContext';

export function Screen({ children, scroll = true, refreshControl, contentStyle }) {
  const { colors } = useTheme();
  const body = (
    <View style={[{ padding: 16, gap: 14 }, contentStyle]}>{children}</View>
  );
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }} edges={['top']}>
      {scroll ? (
        <ScrollView
          contentContainerStyle={{ paddingBottom: 32 }}
          keyboardShouldPersistTaps="handled"
          refreshControl={refreshControl}
        >
          {body}
        </ScrollView>
      ) : (
        body
      )}
    </SafeAreaView>
  );
}

export function Card({ children, style }) {
  const { colors } = useTheme();
  return (
    <View
      style={[
        {
          backgroundColor: colors.card,
          borderRadius: 16,
          padding: 16,
          borderWidth: StyleSheet.hairlineWidth,
          borderColor: colors.border,
          shadowColor: '#000',
          shadowOpacity: 0.06,
          shadowRadius: 10,
          shadowOffset: { width: 0, height: 4 },
          elevation: 2,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}

export function Title({ children, icon, style }) {
  const { colors } = useTheme();
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
      {icon ? <Ionicons name={icon} size={18} color={colors.primary} /> : null}
      <Text style={[{ fontSize: 17, fontWeight: '700', color: colors.text }, style]}>
        {children}
      </Text>
    </View>
  );
}

export function Muted({ children, style }) {
  const { colors } = useTheme();
  return <Text style={[{ color: colors.muted, fontSize: 13 }, style]}>{children}</Text>;
}

export function StatTile({ label, value, icon, color }) {
  const { colors } = useTheme();
  return (
    <Card style={{ flex: 1, minWidth: 140 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <View>
          <Muted>{label}</Muted>
          <Text style={{ fontSize: 24, fontWeight: '800', color: color || colors.text }}>
            {value}
          </Text>
        </View>
        {icon ? <Ionicons name={icon} size={26} color={color || colors.primary} /> : null}
      </View>
    </Card>
  );
}

export function Button({ title, onPress, variant = 'primary', icon, loading, disabled, style }) {
  const { colors } = useTheme();
  const outlined = variant === 'outline';
  const danger = variant === 'danger';
  const bg = outlined ? 'transparent' : danger ? colors.danger : colors.primary;
  const fg = outlined ? colors.primary : danger ? '#fff' : colors.onPrimary;
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        {
          backgroundColor: bg,
          borderColor: colors.primary,
          borderWidth: outlined ? 1.5 : 0,
          paddingVertical: 12,
          paddingHorizontal: 16,
          borderRadius: 12,
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          opacity: pressed || disabled ? 0.7 : 1,
        },
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={fg} />
      ) : (
        <>
          {icon ? <Ionicons name={icon} size={18} color={fg} /> : null}
          <Text style={{ color: fg, fontWeight: '700', fontSize: 15 }}>{title}</Text>
        </>
      )}
    </Pressable>
  );
}

export function Field({ label, error, ...props }) {
  const { colors } = useTheme();
  return (
    <View style={{ gap: 6 }}>
      {label ? <Text style={{ color: colors.text, fontWeight: '600' }}>{label}</Text> : null}
      <TextInput
        placeholderTextColor={colors.muted}
        style={{
          backgroundColor: colors.inputBg,
          borderColor: error ? colors.danger : colors.border,
          borderWidth: 1,
          borderRadius: 10,
          paddingHorizontal: 12,
          paddingVertical: 10,
          color: colors.text,
          fontSize: 15,
        }}
        {...props}
      />
      {error ? <Text style={{ color: colors.danger, fontSize: 12 }}>{error}</Text> : null}
    </View>
  );
}

export function PasswordField({ label, value, onChangeText, placeholder, error, ...props }) {
  const { colors } = useTheme();
  const [hidden, setHidden] = useState(true);
  const borderColor = error ? colors.danger : colors.border;
  return (
    <View style={{ gap: 6 }}>
      {label ? <Text style={{ color: colors.text, fontWeight: '600' }}>{label}</Text> : null}
      <View style={{ flexDirection: 'row' }}>
        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={colors.muted}
          secureTextEntry={hidden}
          autoCapitalize="none"
          autoCorrect={false}
          style={{
            flex: 1,
            backgroundColor: colors.inputBg,
            borderColor,
            borderWidth: 1,
            borderRightWidth: 0,
            borderTopLeftRadius: 10,
            borderBottomLeftRadius: 10,
            paddingHorizontal: 12,
            paddingVertical: 10,
            color: colors.text,
            fontSize: 15,
          }}
          {...props}
        />
        <Pressable
          onPress={() => setHidden((h) => !h)}
          style={{
            paddingHorizontal: 14,
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: colors.inputBg,
            borderColor,
            borderWidth: 1,
            borderTopRightRadius: 10,
            borderBottomRightRadius: 10,
          }}
        >
          <Ionicons name={hidden ? 'eye-outline' : 'eye-off-outline'} size={20} color={colors.muted} />
        </Pressable>
      </View>
      {error ? <Text style={{ color: colors.danger, fontSize: 12 }}>{error}</Text> : null}
    </View>
  );
}

export function Checkbox({ checked, onToggle, label }) {
  const { colors } = useTheme();
  return (
    <Pressable onPress={onToggle} style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
      <Ionicons name={checked ? 'checkbox' : 'square-outline'} size={22} color={colors.primary} />
      <Text style={{ color: colors.text }}>{label}</Text>
    </Pressable>
  );
}

export function Segmented({ options, value, onChange, style }) {
  const { colors } = useTheme();
  return (
    <View style={[{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, style]}>
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <Pressable
            key={String(opt.value)}
            onPress={() => onChange(opt.value)}
            style={{
              paddingVertical: 7,
              paddingHorizontal: 12,
              borderRadius: 8,
              borderWidth: 1,
              borderColor: colors.primary,
              backgroundColor: active ? colors.primary : 'transparent',
            }}
          >
            <Text style={{ color: active ? colors.onPrimary : colors.primary, fontWeight: '600', fontSize: 13 }}>
              {opt.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function Badge({ text, tone = 'primary' }) {
  const { colors } = useTheme();
  const map = {
    primary: colors.primary,
    success: colors.success,
    danger: colors.danger,
    warning: colors.warning,
    muted: colors.muted,
  };
  const c = map[tone] || colors.primary;
  return (
    <View
      style={{
        alignSelf: 'center', // don't stretch to the row height; stay pill-sized
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: c + '22',
        borderRadius: 999,
        paddingHorizontal: 12,
        paddingVertical: 5,
      }}
    >
      <Text style={{ color: c, fontWeight: '700', fontSize: 12 }} numberOfLines={1}>
        {text}
      </Text>
    </View>
  );
}

export function Loading({ text }) {
  const { colors } = useTheme();
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40, gap: 10 }}>
      <ActivityIndicator size="large" color={colors.primary} />
      {text ? <Muted>{text}</Muted> : null}
    </View>
  );
}

export function Empty({ text, icon = 'file-tray-outline' }) {
  const { colors } = useTheme();
  return (
    <View style={{ alignItems: 'center', padding: 28, gap: 8 }}>
      <Ionicons name={icon} size={34} color={colors.muted} />
      <Muted style={{ textAlign: 'center' }}>{text}</Muted>
    </View>
  );
}

export function Row({ children, style }) {
  return <View style={[{ flexDirection: 'row', gap: 10 }, style]}>{children}</View>;
}

export function fmt(n) {
  return Number(n || 0).toLocaleString();
}
