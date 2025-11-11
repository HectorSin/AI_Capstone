import { Stack } from 'expo-router';

export default function ProfileStackLayout() {
  return (
    <Stack
      screenOptions={{
        headerTitleAlign: 'left',
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen name="index" options={{ headerTitle: '프로필' }} />
      <Stack.Screen name="notifications" options={{ headerShown: false }} />
      <Stack.Screen name="difficulty" options={{ headerShown: false }} />
    </Stack>
  );
}
