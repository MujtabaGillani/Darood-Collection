import { Ionicons } from '@expo/vector-icons';
import { DarkTheme, DefaultTheme, NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import React, { useEffect, useState } from 'react';
import { Pressable } from 'react-native';

import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Loading } from '../components/UI';

import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';
import DashboardScreen from '../screens/DashboardScreen';
import OverviewScreen from '../screens/OverviewScreen';
import AddDaroodScreen from '../screens/AddDaroodScreen';
import MyProgressScreen from '../screens/MyProgressScreen';
import SubmitDaroodScreen from '../screens/SubmitDaroodScreen';
import ApprovalsScreen from '../screens/ApprovalsScreen';
import UserDetailScreen from '../screens/UserDetailScreen';
import FazailScreen from '../screens/FazailScreen';
import SettingsScreen from '../screens/SettingsScreen';
import ChangePasswordScreen from '../screens/ChangePasswordScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const ICONS = {
  Dashboard: 'grid-outline',
  Overview: 'bar-chart-outline',
  Add: 'add-circle-outline',
  Approvals: 'checkmark-done-outline',
  Progress: 'trending-up-outline',
  Submit: 'send-outline',
  Fazail: 'book-outline',
  Settings: 'settings-outline',
};

function RoleTabs() {
  const { user } = useAuth();
  const { colors, scheme, toggle } = useTheme();
  const [pending, setPending] = useState(0);

  // Poll the pending-approvals count for the tab badge (managers/superadmins).
  useEffect(() => {
    if (!user?.can_add_darood) return undefined;
    let alive = true;
    const load = () =>
      api
        .get('/darood/approvals/')
        .then((r) => alive && setPending(r.data.pending?.length || 0))
        .catch(() => {});
    load();
    const t = setInterval(load, 60000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [user]);

  const screenOptions = ({ route }) => ({
    headerStyle: { backgroundColor: colors.primary },
    headerTintColor: '#fff',
    headerTitleStyle: { fontWeight: '700' },
    // Quick light/dark toggle in the header, on every tab.
    headerRight: () => (
      <Pressable onPress={toggle} hitSlop={12} style={{ marginRight: 14 }}>
        <Ionicons name={scheme === 'dark' ? 'sunny-outline' : 'moon-outline'} size={22} color="#fff" />
      </Pressable>
    ),
    tabBarActiveTintColor: colors.primary,
    tabBarInactiveTintColor: colors.muted,
    tabBarStyle: { backgroundColor: colors.card, borderTopColor: colors.border },
    tabBarIcon: ({ color, size }) => (
      <Ionicons name={ICONS[route.name] || 'ellipse-outline'} size={size} color={color} />
    ),
  });

  const superadmin = user?.is_superadmin;
  const manager = user?.is_manager;

  return (
    <Tab.Navigator screenOptions={screenOptions}>
      {superadmin && <Tab.Screen name="Dashboard" component={DashboardScreen} />}
      {(superadmin || manager) && (
        <Tab.Screen name="Overview" component={OverviewScreen} options={{ title: 'Overview' }} />
      )}
      {(superadmin || manager) && (
        <Tab.Screen name="Add" component={AddDaroodScreen} options={{ title: 'Add Darood' }} />
      )}
      {!superadmin && !manager && (
        <Tab.Screen name="Progress" component={MyProgressScreen} options={{ title: 'My Progress' }} />
      )}
      {!superadmin && !manager && (
        <Tab.Screen name="Submit" component={SubmitDaroodScreen} options={{ title: 'Submit Darood' }} />
      )}
      {(superadmin || manager) && (
        <Tab.Screen
          name="Approvals"
          component={ApprovalsScreen}
          options={{ title: 'Approvals', tabBarBadge: pending || undefined }}
        />
      )}
      {!superadmin && (
        <Tab.Screen name="Fazail" component={FazailScreen} options={{ title: 'Fazail-e-Darood' }} />
      )}
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

function AuthStack() {
  const { colors } = useTheme();
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: '#fff',
      }}
    >
      <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
      <Stack.Screen name="Register" component={RegisterScreen} options={{ title: 'Create Account' }} />
    </Stack.Navigator>
  );
}

function MainStack() {
  const { colors } = useTheme();
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '700' },
      }}
    >
      <Stack.Screen name="Tabs" component={RoleTabs} options={{ headerShown: false }} />
      <Stack.Screen name="UserDetail" component={UserDetailScreen} options={{ title: 'User Detail' }} />
      <Stack.Screen name="Fazail" component={FazailScreen} options={{ title: 'Fazail-e-Darood' }} />
      <Stack.Screen name="Submit" component={SubmitDaroodScreen} options={{ title: 'Submit Darood' }} />
      <Stack.Screen name="ChangePassword" component={ChangePasswordScreen} options={{ title: 'Change Password' }} />
    </Stack.Navigator>
  );
}

export default function RootNavigator() {
  const { user, booting } = useAuth();
  const { scheme, colors } = useTheme();

  const base = scheme === 'dark' ? DarkTheme : DefaultTheme;
  const navTheme = { ...base, colors: { ...base.colors, background: colors.bg } };

  if (booting) return <Loading text="Loading…" />;

  return (
    <NavigationContainer theme={navTheme}>
      {user ? <MainStack /> : <AuthStack />}
    </NavigationContainer>
  );
}
