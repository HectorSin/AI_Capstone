import Ionicons from '@expo/vector-icons/Ionicons';
import { Redirect, Tabs } from 'expo-router';
import { useColorScheme } from 'react-native';

import { useAuth } from '@/providers/AuthProvider';

export default function TabsLayout() {
  const { isSignedIn } = useAuth();
  if (!isSignedIn) {
    return <Redirect href="/(auth)/login" />;
  }

  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        tabBarActiveTintColor: isDark ? '#f3f4f6' : '#1f2937',
        tabBarInactiveTintColor: isDark ? '#6b7280' : '#9ca3af',
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, focused, size }) => (
            <Ionicons name={focused ? 'home' : 'home-outline'} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="archive"
        options={{
          title: 'Archive',
          tabBarIcon: ({ color, focused, size }) => (
            <Ionicons name={focused ? 'archive' : 'archive-outline'} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="subscribe"
        options={{
          title: 'Subscribe',
          tabBarIcon: ({ color, focused, size }) => (
            <Ionicons name={focused ? 'notifications' : 'notifications-outline'} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, focused, size }) => (
            <Ionicons name={focused ? 'person' : 'person-outline'} size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
