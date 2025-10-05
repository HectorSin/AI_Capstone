import { Stack } from 'expo-router';

export default function HomeStackLayout() {
  return (
    <Stack screenOptions={{ headerShadowVisible: false }}>
      <Stack.Screen
        name="index"
        options={{
          headerTitle: 'Home',
          headerTitleAlign: 'left',
          headerTitleContainerStyle: {
            width: '50%',
          },
          headerStyle: {
            elevation: 0,
            shadowOpacity: 0,
            borderBottomWidth: 0,
          },
          headerTitleStyle: {
            marginBottom: 0,
          },
        }}
      />
    </Stack>
  );
}
