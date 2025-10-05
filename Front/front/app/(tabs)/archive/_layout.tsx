import { Stack } from 'expo-router';

export default function ArchiveStackLayout() {
  return (
    <Stack
      screenOptions={{
        headerTitle: 'Archive',
        headerTitleAlign: 'left',
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen name="index" />
    </Stack>
  );
}
