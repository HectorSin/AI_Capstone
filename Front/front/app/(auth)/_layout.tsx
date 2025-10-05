import { Stack, useRouter } from 'expo-router';
import { useEffect } from 'react';

import { useAuth } from '@/providers/AuthProvider';

export default function AuthLayout() {
  const { isSignedIn } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isSignedIn) {
      router.replace('/(tabs)' as any);
    }
  }, [isSignedIn, router]);

  return (
    <Stack>
      <Stack.Screen name="login" options={{ title: '로그인' }} />
      <Stack.Screen name="register" options={{ title: '회원가입' }} />
    </Stack>
  );
}
