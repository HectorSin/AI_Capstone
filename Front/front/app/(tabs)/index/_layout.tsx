import { Stack } from 'expo-router';

export default function HomeStackLayout() {
  return (
    <Stack screenOptions={{ headerShadowVisible: false }}>
      <Stack.Screen
        name="index"
        options={{
          headerTitle: 'Home',
          headerTitleAlign: 'left',
          headerShadowVisible: false,
        }}
      />
    </Stack>
  );
}
