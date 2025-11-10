import { Link, useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { useAuth } from '@/providers/AuthProvider';
import { checkAvailability, API_BASE_URL } from '@/utils/api';

type Topic = {
  id: string;
  name: string;
  summary: string;
};

type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced';

export default function RegisterScreen() {
  const { signUp } = useAuth();
  const router = useRouter();

  // 단계 관리
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Step 1: 기본 정보
  const [email, setEmail] = useState('');
  const [nickname, setNickname] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Step 2: 난이도
  const [difficultyLevel, setDifficultyLevel] = useState<DifficultyLevel>('intermediate');

  // Step 3: 토픽
  const [selectedTopicIds, setSelectedTopicIds] = useState<string[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [isLoadingTopics, setIsLoadingTopics] = useState(false);

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
      setPasswordError('비밀번호는 8~32자이며, 영문과 숫자를 포함해야 합니다.');
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

  // 토픽 목록 가져오기
  useEffect(() => {
    const fetchTopics = async () => {
      setIsLoadingTopics(true);
      try {
        const response = await fetch(`${API_BASE_URL}/topics`, {
          method: 'GET',
          headers: {
            Accept: 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch topics');
        }

        const data = await response.json();
        setTopics(data.map((topic: any) => ({
          id: topic.id,
          name: topic.name,
          summary: topic.summary || topic.name,
        })));
      } catch (error) {
        console.warn('Failed to fetch topics:', error);
        Alert.alert('안내', '토픽 목록을 불러오는데 실패했습니다.');
      } finally {
        setIsLoadingTopics(false);
      }
    };

    fetchTopics();
  }, []);

  const canProceedToStep2 = useMemo(() => {
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

  const canProceedToStep3 = useMemo(() => {
    return !!difficultyLevel;
  }, [difficultyLevel]);

  const canSubmit = useMemo(() => {
    return selectedTopicIds.length >= 1;
  }, [selectedTopicIds]);

  const handleNextToStep2 = () => {
    if (!canProceedToStep2) {
      Alert.alert('안내', '입력값을 다시 확인해주세요.');
      return;
    }
    setStep(2);
  };

  const handleNextToStep3 = () => {
    if (!canProceedToStep3) {
      Alert.alert('안내', '난이도를 선택해주세요.');
      return;
    }
    setStep(3);
  };

  const handleBack = () => {
    if (step === 2) setStep(1);
    else if (step === 3) setStep(2);
  };

  const toggleTopic = (topicId: string) => {
    setSelectedTopicIds((prev) => {
      if (prev.includes(topicId)) {
        return prev.filter((id) => id !== topicId);
      } else {
        return [...prev, topicId];
      }
    });
  };

  const handleSubmit = async () => {
    if (!canSubmit) {
      Alert.alert('안내', '토픽을 최소 1개 이상 선택해주세요.');
      return;
    }

    setIsSubmitting(true);
    try {
      const success = await signUp({
        email: email.trim(),
        password,
        nickname: nickname.trim(),
        difficulty_level: difficultyLevel,
        topic_ids: selectedTopicIds,
      });

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
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Step 1: 기본 정보 */}
      {step === 1 && (
        <View>
          <Text style={styles.title}>새 계정 만들기</Text>
          <Text style={styles.subtitle}>기본 정보를 입력해주세요. (1/3)</Text>

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
              style={styles.input}
            />
            {passwordError && <Text style={styles.errorText}>{passwordError}</Text>}

            <TextInput
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="비밀번호 확인"
              secureTextEntry
              style={styles.input}
            />
            {confirmError && <Text style={styles.errorText}>{confirmError}</Text>}

            <Pressable
              style={[styles.button, !canProceedToStep2 && styles.buttonDisabled]}
              onPress={handleNextToStep2}
              disabled={!canProceedToStep2}
            >
              <Text style={styles.buttonText}>다음</Text>
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
      )}

      {/* Step 2: 난이도 선택 */}
      {step === 2 && (
        <View>
          <Text style={styles.title}>학습 난이도 선택</Text>
          <Text style={styles.subtitle}>선호하는 학습 난이도를 선택해주세요. (2/3)</Text>

          <View style={styles.form}>
            <Pressable
              style={[styles.optionCard, difficultyLevel === 'beginner' && styles.optionCardSelected]}
              onPress={() => setDifficultyLevel('beginner')}
            >
              <Text style={[styles.optionTitle, difficultyLevel === 'beginner' && styles.optionTitleSelected]}>
                초급 (하)
              </Text>
              <Text style={styles.optionDescription}>기초부터 차근차근 배우고 싶어요</Text>
            </Pressable>

            <Pressable
              style={[styles.optionCard, difficultyLevel === 'intermediate' && styles.optionCardSelected]}
              onPress={() => setDifficultyLevel('intermediate')}
            >
              <Text
                style={[styles.optionTitle, difficultyLevel === 'intermediate' && styles.optionTitleSelected]}
              >
                중급 (중)
              </Text>
              <Text style={styles.optionDescription}>기본 지식이 있고, 심화 내용을 원해요</Text>
            </Pressable>

            <Pressable
              style={[styles.optionCard, difficultyLevel === 'advanced' && styles.optionCardSelected]}
              onPress={() => setDifficultyLevel('advanced')}
            >
              <Text style={[styles.optionTitle, difficultyLevel === 'advanced' && styles.optionTitleSelected]}>
                고급 (상)
              </Text>
              <Text style={styles.optionDescription}>전문적이고 깊이 있는 내용을 원해요</Text>
            </Pressable>

            <View style={styles.buttonRow}>
              <Pressable style={[styles.button, styles.buttonSecondary]} onPress={handleBack}>
                <Text style={styles.buttonTextSecondary}>이전</Text>
              </Pressable>
              <Pressable
                style={[styles.button, styles.buttonPrimary, !canProceedToStep3 && styles.buttonDisabled]}
                onPress={handleNextToStep3}
                disabled={!canProceedToStep3}
              >
                <Text style={styles.buttonText}>다음</Text>
              </Pressable>
            </View>
          </View>
        </View>
      )}

      {/* Step 3: 토픽 선택 */}
      {step === 3 && (
        <View>
          <Text style={styles.title}>관심 토픽 선택</Text>
          <Text style={styles.subtitle}>
            관심 있는 토픽을 최소 1개 이상 선택해주세요. (3/3) {'\n'}
            선택됨: {selectedTopicIds.length}개
          </Text>

          <View style={styles.form}>
            {isLoadingTopics ? (
              <Text style={styles.helperText}>토픽 목록을 불러오는 중...</Text>
            ) : topics.length === 0 ? (
              <Text style={styles.errorText}>토픽 목록을 불러올 수 없습니다.</Text>
            ) : (
              topics.map((topic) => {
                const isSelected = selectedTopicIds.includes(topic.id);
                return (
                  <Pressable
                    key={topic.id}
                    style={[styles.topicCard, isSelected && styles.topicCardSelected]}
                    onPress={() => toggleTopic(topic.id)}
                  >
                    <Text style={[styles.topicTitle, isSelected && styles.topicTitleSelected]}>{topic.name}</Text>
                    <Text style={styles.topicDescription}>{topic.summary}</Text>
                  </Pressable>
                );
              })
            )}

            <View style={styles.buttonRow}>
              <Pressable style={[styles.button, styles.buttonSecondary]} onPress={handleBack}>
                <Text style={styles.buttonTextSecondary}>이전</Text>
              </Pressable>
              <Pressable
                style={[styles.button, styles.buttonPrimary, (!canSubmit || isSubmitting) && styles.buttonDisabled]}
                onPress={handleSubmit}
                disabled={!canSubmit || isSubmitting}
              >
                <Text style={styles.buttonText}>{isSubmitting ? '가입 중...' : '회원가입'}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  contentContainer: {
    paddingTop: 80,
    paddingHorizontal: 24,
    paddingBottom: 40,
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
  buttonPrimary: {
    flex: 1,
    backgroundColor: '#22c55e',
  },
  buttonSecondary: {
    flex: 1,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  buttonTextSecondary: {
    color: '#374151',
    fontSize: 16,
    fontWeight: '600',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
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
  optionCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    backgroundColor: '#fff',
  },
  optionCardSelected: {
    borderColor: '#22c55e',
    backgroundColor: '#f0fdf4',
  },
  optionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
    color: '#374151',
  },
  optionTitleSelected: {
    color: '#22c55e',
  },
  optionDescription: {
    fontSize: 14,
    color: '#6b7280',
  },
  topicCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    backgroundColor: '#fff',
  },
  topicCardSelected: {
    borderColor: '#22c55e',
    backgroundColor: '#f0fdf4',
  },
  topicTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
    color: '#374151',
  },
  topicTitleSelected: {
    color: '#22c55e',
  },
  topicDescription: {
    fontSize: 13,
    color: '#6b7280',
  },
});
