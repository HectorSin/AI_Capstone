import { Link, useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { useAuth } from '@/providers/AuthProvider';
import { checkAvailability } from '@/utils/api';

// 개발 모드: 비밀번호 검증 완화 (true로 설정하면 최소 4자만 입력하면 됨)
const DEV_MODE_WEAK_PASSWORD = true;

export default function RegisterScreen() {
  const { signUp } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [nickname, setNickname] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [emailStatus, setEmailStatus] = useState<'idle' | 'checking' | 'available' | 'taken'>('idle');
  const [nicknameStatus, setNicknameStatus] = useState<'idle' | 'checking' | 'available' | 'taken'>('idle');
  const [emailError, setEmailError] = useState<string | null>(null);
  const [nicknameError, setNicknameError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  const isEmailValidFormat = useMemo(() => {
    if (!email) return false;
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return pattern.test(email.trim());
  }, [email]);

  const isPasswordStrong = useMemo(() => {
    if (!password) return false;
    
    // 개발 모드: 최소 4자만 입력하면 통과
    if (DEV_MODE_WEAK_PASSWORD) {
      return password.length >= 4;
    }
    
    // 프로덕션 모드: 강력한 비밀번호 검증
    const hasLetter = /[A-Za-z]/.test(password);
    const hasNumber = /\d/.test(password);
    return password.length >= 8 && password.length <= 32 && hasLetter && hasNumber;
  }, [password]);

  useEffect(() => {
    if (!email) {
      setEmailStatus('idle');
      setEmailError(null);
      return;
    }

    if (!isEmailValidFormat) {
      setEmailStatus('idle');
      setEmailError('올바른 이메일 형식을 입력해주세요.');
      return;
    }

    let isActive = true;
    const controller = new AbortController();
    setEmailStatus('checking');
    setEmailError(null);

    const timer = setTimeout(async () => {
      try {
        const available = await checkAvailability('check-email', email.trim(), controller.signal);
        if (!isActive) return;
        setEmailStatus(available ? 'available' : 'taken');
        setEmailError(available ? null : '이미 등록된 이메일입니다.');
      } catch (error) {
        if (!controller.signal.aborted && isActive) {
          console.warn('email check failed', error);
          setEmailStatus('idle');
          setEmailError('이메일 중복 확인에 실패했습니다.');
        }
      }
    }, 400);

    return () => {
      isActive = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, [email, isEmailValidFormat]);

  useEffect(() => {
    if (!nickname) {
      setNicknameStatus('idle');
      setNicknameError(null);
      return;
    }

    let isActive = true;
    const controller = new AbortController();
    setNicknameStatus('checking');
    setNicknameError(null);

    const timer = setTimeout(async () => {
      try {
        const available = await checkAvailability('check-nickname', nickname.trim(), controller.signal);
        if (!isActive) return;
        setNicknameStatus(available ? 'available' : 'taken');
        setNicknameError(available ? null : '이미 사용 중인 닉네임입니다.');
      } catch (error) {
        if (!controller.signal.aborted && isActive) {
          console.warn('nickname check failed', error);
          setNicknameStatus('idle');
          setNicknameError('닉네임 중복 확인에 실패했습니다.');
        }
      }
    }, 400);

    return () => {
      isActive = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, [nickname]);

  useEffect(() => {
    if (!password) {
      setPasswordError(null);
      return;
    }

    if (!isPasswordStrong) {
      if (DEV_MODE_WEAK_PASSWORD) {
        setPasswordError('비밀번호는 최소 4자 이상 입력해주세요.');
      } else {
        setPasswordError('비밀번호는 8~32자이며, 영문과 숫자를 포함해야 합니다.');
      }
    } else {
      setPasswordError(null);
    }
  }, [password, isPasswordStrong]);

  useEffect(() => {
    if (!confirmPassword) {
      setConfirmError(null);
      return;
    }

    if (password !== confirmPassword) {
      setConfirmError('비밀번호 확인이 일치하지 않습니다.');
    } else {
      setConfirmError(null);
    }
  }, [password, confirmPassword]);

  const canSubmit = useMemo(() => {
    return (
      !!email &&
      !!nickname &&
      !!password &&
      !!confirmPassword &&
      isEmailValidFormat &&
      emailStatus === 'available' &&
      nicknameStatus === 'available' &&
      isPasswordStrong &&
      password === confirmPassword &&
      !emailError &&
      !nicknameError &&
      !passwordError &&
      !confirmError
    );
  }, [
    email,
    nickname,
    password,
    confirmPassword,
    isEmailValidFormat,
    emailStatus,
    nicknameStatus,
    isPasswordStrong,
    emailError,
    nicknameError,
    passwordError,
    confirmError,
  ]);

  const handleSubmit = async () => {
    if (!canSubmit) {
      Alert.alert('안내', '입력값을 다시 확인해주세요.');
      return;
    }

    setIsSubmitting(true);
    try {
      const success = await signUp({ email: email.trim(), password, nickname: nickname.trim() });
      if (success) {
        Alert.alert('안내', '회원가입이 완료되었습니다. 로그인해주세요.', [
          {
            text: '확인',
            onPress: () => router.back(),
          },
        ]);
        return;
      }

      Alert.alert('안내', '회원가입에 실패했습니다. 다시 시도해주세요.');
    } catch (error) {
      console.warn('signUp failed', error);
      Alert.alert('안내', '회원가입 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>새 계정 만들기</Text>
      <Text style={styles.subtitle}>몇 가지 정보만 입력하면 바로 사용할 수 있어요.</Text>

      <View style={styles.form}>
        <TextInput
          value={email}
          onChangeText={setEmail}
          placeholder="이메일"
          keyboardType="email-address"
          autoCapitalize="none"
          style={styles.input}
        />
        {emailStatus === 'checking' && <Text style={styles.helperText}>이메일 중복 확인 중...</Text>}
        {emailError && <Text style={styles.errorText}>{emailError}</Text>}
        {!emailError && emailStatus === 'available' && email && (
          <Text style={styles.successText}>사용 가능한 이메일입니다.</Text>
        )}

        <TextInput
          value={nickname}
          onChangeText={setNickname}
          placeholder="닉네임"
          autoCapitalize="none"
          style={styles.input}
        />
        {nicknameStatus === 'checking' && <Text style={styles.helperText}>닉네임 중복 확인 중...</Text>}
        {nicknameError && <Text style={styles.errorText}>{nicknameError}</Text>}
        {!nicknameError && nicknameStatus === 'available' && nickname && (
          <Text style={styles.successText}>사용 가능한 닉네임입니다.</Text>
        )}

        <TextInput
          value={password}
          onChangeText={setPassword}
          placeholder="비밀번호"
          secureTextEntry
          textContentType="none"
          autoComplete="off"
          style={styles.input}
        />
        {passwordError && <Text style={styles.errorText}>{passwordError}</Text>}

        <TextInput
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          placeholder="비밀번호 확인"
          secureTextEntry
          textContentType="none"
          autoComplete="off"
          style={styles.input}
        />
        {confirmError && <Text style={styles.errorText}>{confirmError}</Text>}

        <Pressable
          style={[styles.button, (!canSubmit || isSubmitting) && styles.buttonDisabled]}
          onPress={handleSubmit}
          disabled={!canSubmit || isSubmitting}
        >
          <Text style={styles.buttonText}>{isSubmitting ? '가입 중...' : '회원가입'}</Text>
        </Pressable>
      </View>

      <Text style={styles.footerText}>
        이미 계정이 있다면{' '}
        <Link href="/(auth)/login" asChild>
          <Pressable>
            <Text style={styles.link}>로그인</Text>
          </Pressable>
        </Link>
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 80,
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 32,
  },
  form: {
    gap: 12,
  },
  input: {
    height: 52,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#d1d5db',
    backgroundColor: '#fff',
  },
  helperText: {
    fontSize: 13,
    color: '#6b7280',
  },
  errorText: {
    fontSize: 13,
    color: '#dc2626',
  },
  successText: {
    fontSize: 13,
    color: '#16a34a',
  },
  button: {
    height: 52,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#22c55e',
    marginTop: 12,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  footerText: {
    marginTop: 24,
    fontSize: 14,
    color: '#4b5563',
  },
  link: {
    color: '#2563eb',
    fontWeight: '600',
  },
});
