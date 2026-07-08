import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { Modal, Pressable, Text, View } from 'react-native';

import { useTheme } from './ThemeContext';

const DialogContext = createContext(null);

// Module-level handle so appAlert/appConfirm can be called from anywhere,
// including catch blocks and non-component code.
let _show = null;

export function DialogProvider({ children }) {
  const { colors } = useTheme();
  const [state, setState] = useState({ visible: false, title: '', message: '', actions: [] });

  const show = useCallback((opts) => {
    setState({
      visible: true,
      title: opts.title || '',
      message: opts.message || '',
      actions: opts.actions && opts.actions.length ? opts.actions : [{ label: 'OK' }],
    });
  }, []);

  const hide = useCallback(() => setState((s) => ({ ...s, visible: false })), []);

  useEffect(() => {
    _show = show;
    return () => {
      _show = null;
    };
  }, [show]);

  const press = (action) => {
    hide();
    if (action.onPress) setTimeout(action.onPress, 120); // let the modal close first
  };

  return (
    <DialogContext.Provider value={{ show, hide }}>
      {children}
      <Modal
        transparent
        visible={state.visible}
        animationType="fade"
        statusBarTranslucent
        onRequestClose={hide}
      >
        <Pressable
          onPress={hide}
          style={{
            flex: 1,
            backgroundColor: 'rgba(0,0,0,0.55)',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 24,
          }}
        >
          {/* stop taps inside the card from dismissing */}
          <Pressable
            onPress={() => {}}
            style={{
              width: '100%',
              maxWidth: 420,
              backgroundColor: colors.card,
              borderRadius: 16,
              overflow: 'hidden',
              borderWidth: 1,
              borderColor: colors.border,
            }}
          >
            {/* teal accent bar, matching the web card ::before */}
            <View style={{ height: 4, backgroundColor: colors.primary }} />
            <View style={{ padding: 20, gap: 10 }}>
              {state.title ? (
                <Text style={{ fontSize: 18, fontWeight: '800', color: colors.text }}>{state.title}</Text>
              ) : null}
              {state.message ? (
                <Text style={{ fontSize: 15, color: colors.text, lineHeight: 22 }}>{state.message}</Text>
              ) : null}
              <View style={{ flexDirection: 'row', justifyContent: 'flex-end', gap: 8, marginTop: 10 }}>
                {state.actions.map((a, i) => {
                  const cancel = a.variant === 'cancel';
                  const danger = a.variant === 'danger';
                  return (
                    <Pressable
                      key={i}
                      onPress={() => press(a)}
                      style={{
                        paddingVertical: 9,
                        paddingHorizontal: 18,
                        borderRadius: 10,
                        backgroundColor: cancel ? 'transparent' : danger ? colors.danger : colors.primary,
                      }}
                    >
                      <Text style={{ color: cancel ? colors.muted : '#fff', fontWeight: '700' }}>{a.label}</Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </DialogContext.Provider>
  );
}

export const useDialog = () => useContext(DialogContext);

/** Themed replacement for Alert.alert. `onOk` runs after the user taps OK. */
export function appAlert(title, message, onOk) {
  if (_show) _show({ title, message, actions: [{ label: 'OK', onPress: onOk }] });
}

/** Themed confirm dialog with Cancel + Confirm. */
export function appConfirm({ title, message, confirmLabel = 'Confirm', cancelLabel = 'Cancel', destructive, onConfirm }) {
  if (_show) {
    _show({
      title,
      message,
      actions: [
        { label: cancelLabel, variant: 'cancel' },
        { label: confirmLabel, variant: destructive ? 'danger' : 'primary', onPress: onConfirm },
      ],
    });
  }
}
