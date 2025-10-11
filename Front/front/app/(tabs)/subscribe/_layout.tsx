import { Stack } from 'expo-router';

export default function SubscribeStackLayout() {
  return (
    <Stack
      screenOptions={{
        headerTitle: 'Subscribe',
        headerTitleAlign: 'left',
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen name="index" />
    </Stack>
  );
}
