import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';

import { useAuth } from '@/providers/AuthProvider';
import { NavigationHeader } from '@/components/NavigationHeader';

type TimePreference = {
  period: '오전' | '오후';
  hour: number;
  minute: number;
};

const ALL_DAYS = ['월', '화', '수', '목', '금', '토', '일'] as const;
const DAY_TO_INDEX: Record<typeof ALL_DAYS[number], number> = {
  월: 0,
  화: 1,
  수: 2,
  목: 3,
  금: 4,
  토: 5,
  일: 6,
};
const INDEX_TO_DAY = ALL_DAYS;

type DayPreset = 'daily' | 'weekday' | 'weekend' | 'custom';

const DAY_PRESET_OPTIONS: { key: DayPreset; label: string }[] = [
  { key: 'daily', label: '매일' },
  { key: 'weekday', label: '평일' },
  { key: 'weekend', label: '주말' },
  { key: 'custom', label: '사용자 설정' },
];

const PRESET_DAY_MAP: Record<Exclude<DayPreset, 'custom'>, string[]> = {
  daily: [...ALL_DAYS],
  weekday: ['월', '화', '수', '목', '금'],
  weekend: ['토', '일'],
};

const getPresetDays = (preset: DayPreset): string[] => {
  if (preset === 'custom') {
    return [];
  }
  return [...PRESET_DAY_MAP[preset]];
};

const detectDayPreset = (days: string[]): DayPreset => {
  const sorted = [...days].sort((a, b) => DAY_TO_INDEX[a as typeof ALL_DAYS[number]] - DAY_TO_INDEX[b as typeof ALL_DAYS[number]]);
  for (const option of DAY_PRESET_OPTIONS) {
    if (option.key === 'custom') continue;
    const presetDays = PRESET_DAY_MAP[option.key].slice().sort(
      (a, b) => DAY_TO_INDEX[a as typeof ALL_DAYS[number]] - DAY_TO_INDEX[b as typeof ALL_DAYS[number]]
    );
    if (presetDays.length === sorted.length && presetDays.every((day, index) => day === sorted[index])) {
      return option.key;
    }
  }
  return 'custom';
};

const toTimePreference = (hour: number, minute: number): TimePreference => {
  const period: '오전' | '오후' = hour >= 12 ? '오후' : '오전';
  const twelveHour = hour % 12 === 0 ? 12 : hour % 12;
  return { period, hour: twelveHour, minute };
};

const to24Hour = (time: TimePreference): { hour: number; minute: number } => {
  let hour = time.hour % 12;
  if (time.period === '오후') {
    hour += 12;
  }
  if (hour === 24) {
    hour = 0;
  }
  return { hour, minute: time.minute };
};

const ORDERED_DAYS = [...ALL_DAYS];

const normalizeDays = (days: string[]): string[] => {
  const unique = new Set(days);
  return ORDERED_DAYS.filter((day) => unique.has(day));
};

export default function NotificationSettingsScreen() {
  const router = useRouter();
  const {
    notificationPreference,
    updateNotificationPreference,
    refreshNotificationPreference,
  } = useAuth();

  const [allowNotifications, setAllowNotifications] = useState(true);
  const [timeSettingEnabled, setTimeSettingEnabled] = useState(true);
  const [selectedDays, setSelectedDays] = useState<string[]>(() => getPresetDays('daily'));
  const [timePreference, setTimePreference] = useState<TimePreference>({ period: '오전', hour: 7, minute: 0 });
  const [dayPreset, setDayPreset] = useState<DayPreset>('daily');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!notificationPreference) {
      return;
    }

    const {
      allowed,
      timeEnabled,
      hour,
      minute,
      daysOfWeek,
    } = notificationPreference;

    setAllowNotifications(allowed);
    setTimeSettingEnabled(timeEnabled);

    const activeHour = hour ?? 7;
    const activeMinute = minute ?? 0;
    setTimePreference(toTimePreference(activeHour, activeMinute));

    const mappedDays = daysOfWeek.length
      ? normalizeDays(daysOfWeek.map((index) => INDEX_TO_DAY[index] ?? ''))
      : getPresetDays('weekday');
    setSelectedDays(mappedDays);

    const preset = detectDayPreset(mappedDays);
    setDayPreset(preset);
  }, [notificationPreference]);

  const scheduleEnabled = allowNotifications && timeSettingEnabled;
  const periodOptions: ('오전' | '오후')[] = ['오전', '오후'];
  const hourOptions = Array.from({ length: 12 }, (_, index) => index + 1);
  const minuteOptions = Array.from({ length: 12 }, (_, index) => index * 5);
  const formattedTime = `${timePreference.period} ${timePreference.hour
    .toString()
    .padStart(2, '0')}:${timePreference.minute.toString().padStart(2, '0')}`;

  const currentSnapshot = useMemo(() => {
    const { hour, minute } = to24Hour(timePreference);
    const scheduleActive = allowNotifications && timeSettingEnabled;
    return {
      allowed: allowNotifications,
      timeEnabled: timeSettingEnabled,
      hour: scheduleActive ? hour : null,
      minute: scheduleActive ? minute : null,
      days: scheduleActive ? [...selectedDays] : [],
    };
  }, [allowNotifications, timeSettingEnabled, selectedDays, timePreference]);

  const initialSnapshot = useMemo(() => {
    if (!notificationPreference) return null;
    return {
      allowed: notificationPreference.allowed,
      timeEnabled: notificationPreference.timeEnabled,
      hour: notificationPreference.timeEnabled ? notificationPreference.hour ?? 7 : null,
      minute: notificationPreference.timeEnabled ? notificationPreference.minute ?? 0 : null,
      days: notificationPreference.timeEnabled
        ? normalizeDays(notificationPreference.daysOfWeek.map((index) => INDEX_TO_DAY[index] ?? ''))
        : [],
    };
  }, [notificationPreference]);

  const isDirty = useMemo(() => {
    if (!initialSnapshot) return false;
    const currentDaysSorted = normalizeDays(currentSnapshot.days).join(',');
    const initialDaysSorted = normalizeDays(initialSnapshot.days).join(',');
    return (
      currentSnapshot.allowed !== initialSnapshot.allowed ||
      currentSnapshot.timeEnabled !== initialSnapshot.timeEnabled ||
      currentSnapshot.hour !== initialSnapshot.hour ||
      currentSnapshot.minute !== initialSnapshot.minute ||
      currentDaysSorted !== initialDaysSorted
    );
  }, [currentSnapshot, initialSnapshot]);

  const toggleAllowNotifications = (value: boolean) => {
    setAllowNotifications(value);
    if (!value) {
      setSelectedDays(getPresetDays('weekday'));
      setDayPreset('weekday');
    }
  };

  const toggleTimeSetting = (value: boolean) => {
    setTimeSettingEnabled(value);
    if (!value) {
      setSelectedDays(getPresetDays('weekday'));
      setDayPreset('weekday');
    } else if (selectedDays.length === 0) {
      setSelectedDays(['월']);
    }
  };

  const applyDayPreset = (preset: DayPreset) => {
    setDayPreset(preset);
    if (preset === 'custom') {
      setSelectedDays((prev) => (prev.length > 0 ? normalizeDays(prev) : ['월']));
      return;
    }
    setSelectedDays(getPresetDays(preset));
  };

  const toggleDay = (day: string) => {
    setSelectedDays((prev) => {
      if (prev.includes(day)) {
        const updated = prev.filter((item) => item !== day);
        return updated;
      }
      return normalizeDays([...prev, day]);
    });
  };

  const handleSelectDay = (day: string) => {
    if (dayPreset !== 'custom') {
      setDayPreset('custom');
    }
    toggleDay(day);
  };

  const selectPeriod = (period: '오전' | '오후') => {
    setTimePreference((current) => ({ ...current, period }));
  };

  const selectHour = (hour: number) => {
    setTimePreference((current) => ({ ...current, hour }));
  };

  const selectMinute = (minute: number) => {
    setTimePreference((current) => ({ ...current, minute }));
  };

  const handleSave = async () => {
    if (!notificationPreference) return;

    if (timeSettingEnabled && selectedDays.length === 0) {
      Alert.alert('안내', '희망 요일을 한 가지 이상 선택해주세요.');
      return;
    }

    setIsSaving(true);
    try {
      const { hour, minute } = to24Hour(timePreference);
      const success = await updateNotificationPreference({
        allowed: allowNotifications,
        timeEnabled: timeSettingEnabled,
        hour: timeSettingEnabled ? hour : null,
        minute: timeSettingEnabled ? minute : null,
        daysOfWeek: timeSettingEnabled
          ? selectedDays.map((day) => DAY_TO_INDEX[day as typeof ALL_DAYS[number]])
          : [],
        prompted: true,
      });

      if (success) {
        await refreshNotificationPreference();
        Alert.alert('안내', '알림 설정이 저장되었습니다.');
      } else {
        Alert.alert('안내', '알림 설정 저장에 실패했습니다.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <NavigationHeader
        title="알림 설정"
        onBack={() => router.back()}
        rightButton={{
          text: isSaving ? '저장 중' : '저장',
          onPress: handleSave,
          disabled: !isDirty || isSaving,
        }}
      />
      <View style={styles.content}>
        <View style={styles.row}>
          <Text style={styles.label}>알림 허용</Text>
          <Switch value={allowNotifications} onValueChange={toggleAllowNotifications} />
        </View>
        <View style={[styles.row, !allowNotifications && styles.disabledRow]}>
          <Text style={[styles.label, !allowNotifications && styles.disabledLabel]}>예약 시간 설정</Text>
          <Switch
            value={timeSettingEnabled}
            onValueChange={toggleTimeSetting}
            disabled={!allowNotifications}
          />
        </View>
        <View style={[styles.scheduleSection, !scheduleEnabled && styles.disabledRow]}>
          <Text style={[styles.sectionLabel, !scheduleEnabled && styles.disabledLabel]}>희망 요일</Text>
          <View style={styles.presetRow}>
            {DAY_PRESET_OPTIONS.map((option) => (
              <Pressable
                key={option.key}
                disabled={!scheduleEnabled}
                onPress={() => applyDayPreset(option.key)}
                style={({ pressed }) => [
                  styles.radioButton,
                  dayPreset === option.key && styles.radioSelected,
                  pressed && scheduleEnabled && styles.radioPressed,
                ]}
              >
                <Text
                  style={[
                    styles.radioLabel,
                    dayPreset === option.key && styles.radioLabelSelected,
                  ]}
                >
                  {option.label}
                </Text>
              </Pressable>
            ))}
          </View>
          {dayPreset === 'custom' ? (
            <View style={styles.dayGrid}>
              {ALL_DAYS.map((day) => {
                const active = selectedDays.includes(day);
                return (
                  <Pressable
                    key={day}
                    disabled={!scheduleEnabled}
                    onPress={() => handleSelectDay(day)}
                    style={({ pressed }) => [
                      styles.dayPill,
                      active && styles.dayPillActive,
                      pressed && scheduleEnabled && styles.dayPillPressed,
                    ]}
                  >
                    <Text style={[styles.dayText, active && styles.dayTextActive]}>{day}</Text>
                  </Pressable>
                );
              })}
            </View>
          ) : null}
        </View>
        <View
          style={[styles.scheduleSection, !scheduleEnabled && styles.disabledRow]}
          pointerEvents={scheduleEnabled && selectedDays.length > 0 ? 'auto' : 'none'}
        >
          <Text style={[styles.sectionLabel, (!scheduleEnabled || selectedDays.length === 0) && styles.disabledLabel]}>희망 시간</Text>
          {selectedDays.length === 0 ? (
            <Text style={[styles.placeholderText, !scheduleEnabled && styles.disabledLabel]}>희망 요일을 먼저 선택해 주세요.</Text>
          ) : (
            <View style={styles.timePickerCard}>
              <Text style={styles.timeSummary}>{formattedTime}</Text>
              <Text style={styles.timeSummaryHint}>목록을 위아래로 스크롤해 원하는 시간을 선택하세요.</Text>
              <View style={styles.pickerRow}>
                <View style={styles.pickerColumn}>
                  <Text style={styles.pickerColumnLabel}>구분</Text>
                  <ScrollView
                    showsVerticalScrollIndicator
                    style={styles.pickerScroll}
                    contentContainerStyle={styles.pickerContent}
                  >
                    {periodOptions.map((option) => {
                      const active = timePreference.period === option;
                      return (
                        <Pressable
                          key={option}
                          onPress={() => selectPeriod(option)}
                          style={({ pressed }) => [
                            styles.pickerItem,
                            active && styles.pickerItemActive,
                            pressed && styles.pickerItemPressed,
                          ]}
                        >
                          <Text style={[styles.pickerText, active && styles.pickerTextActive]}>{option}</Text>
                        </Pressable>
                      );
                    })}
                  </ScrollView>
                </View>
                <View style={styles.pickerColumn}>
                  <Text style={styles.pickerColumnLabel}>시</Text>
                  <ScrollView
                    showsVerticalScrollIndicator
                    style={styles.pickerScroll}
                    contentContainerStyle={styles.pickerContent}
                  >
                    {hourOptions.map((option) => {
                      const active = timePreference.hour === option;
                      return (
                        <Pressable
                          key={option}
                          onPress={() => selectHour(option)}
                          style={({ pressed }) => [
                            styles.pickerItem,
                            active && styles.pickerItemActive,
                            pressed && styles.pickerItemPressed,
                          ]}
                        >
                          <Text style={[styles.pickerText, active && styles.pickerTextActive]}>{option}</Text>
                        </Pressable>
                      );
                    })}
                  </ScrollView>
                </View>
                <View style={styles.pickerColumn}>
                  <Text style={styles.pickerColumnLabel}>분</Text>
                  <ScrollView
                    showsVerticalScrollIndicator
                    style={styles.pickerScroll}
                    contentContainerStyle={styles.pickerContent}
                  >
                    {minuteOptions.map((option) => {
                      const active = timePreference.minute === option;
                      return (
                        <Pressable
                          key={option}
                          onPress={() => selectMinute(option)}
                          style={({ pressed }) => [
                            styles.pickerItem,
                            active && styles.pickerItemActive,
                            pressed && styles.pickerItemPressed,
                          ]}
                        >
                          <Text style={[styles.pickerText, active && styles.pickerTextActive]}>{option.toString().padStart(2, '0')}</Text>
                        </Pressable>
                      );
                    })}
                  </ScrollView>
                </View>
              </View>
            </View>
          )}
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  content: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
    gap: 20,
  },
  row: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  label: {
    fontSize: 16,
    color: '#111827',
    fontWeight: '500',
  },
  disabledRow: {
    opacity: 0.5,
  },
  disabledLabel: {
    color: '#9ca3af',
  },
  scheduleSection: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 20,
    gap: 12,
  },
  sectionLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  presetRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  radioButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#d1d5db',
    backgroundColor: '#ffffff',
  },
  radioSelected: {
    borderColor: '#2563eb',
    backgroundColor: '#dbeafe',
  },
  radioPressed: {
    opacity: 0.7,
  },
  radioLabel: {
    fontSize: 14,
    color: '#1f2937',
  },
  radioLabelSelected: {
    color: '#1d4ed8',
    fontWeight: '600',
  },
  dayGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  dayPill: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#d1d5db',
    backgroundColor: '#ffffff',
  },
  dayPillActive: {
    borderColor: '#059669',
    backgroundColor: '#dcfce7',
  },
  dayPillPressed: {
    opacity: 0.7,
  },
  dayText: {
    fontSize: 14,
    color: '#1f2937',
  },
  dayTextActive: {
    color: '#047857',
    fontWeight: '600',
  },
  placeholderText: {
    fontSize: 14,
    color: '#6b7280',
  },
  timePickerCard: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    padding: 16,
    backgroundColor: '#f9fafb',
    gap: 12,
  },
  timeSummary: {
    fontSize: 24,
    fontWeight: '600',
    color: '#1f2937',
  },
  timeSummaryHint: {
    fontSize: 14,
    color: '#6b7280',
  },
  pickerRow: {
    flexDirection: 'row',
    gap: 12,
  },
  pickerColumn: {
    flex: 1,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    backgroundColor: '#ffffff',
  },
  pickerColumnLabel: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#e5e7eb',
  },
  pickerScroll: {
    maxHeight: 160,
  },
  pickerContent: {
    paddingVertical: 6,
  },
  pickerItem: {
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  pickerItemActive: {
    backgroundColor: '#e0f2fe',
  },
  pickerItemPressed: {
    opacity: 0.6,
  },
  pickerText: {
    fontSize: 14,
    color: '#1f2937',
  },
  pickerTextActive: {
    color: '#0c4a6e',
    fontWeight: '600',
  },
});
