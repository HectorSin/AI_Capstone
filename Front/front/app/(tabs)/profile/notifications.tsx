import { useState } from 'react';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

type TimePreference = {
  period: '오전' | '오후';
  hour: number;
  minute: number;
};

const ALL_DAYS = ['월', '화', '수', '목', '금', '토', '일'] as const;
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

export default function NotificationSettingsScreen() {
  const router = useRouter();
  const [allowNotifications, setAllowNotifications] = useState(true);
  const [timeSettingEnabled, setTimeSettingEnabled] = useState(true);
  const [selectedDays, setSelectedDays] = useState<string[]>(() => getPresetDays('daily'));
  const [timePreference, setTimePreference] = useState<TimePreference>({ period: '오전', hour: 7, minute: 0 });
  const [dayPreset, setDayPreset] = useState<DayPreset>('daily');

  const toggleAllowNotifications = (value: boolean) => {
    setAllowNotifications(value);
    if (!value) {
      setTimeSettingEnabled(false);
      setSelectedDays(getPresetDays('daily'));
      setDayPreset('daily');
      setTimePreference({ period: '오전', hour: 7, minute: 0 });
    }
  };

  const toggleTimeSetting = (value: boolean) => {
    setTimeSettingEnabled(value);
    if (!value) {
      if (dayPreset === 'custom') {
        setSelectedDays((prev) => (prev.length > 0 ? prev : ['월']));
      } else {
        setSelectedDays(getPresetDays(dayPreset));
      }
    } else if (selectedDays.length === 0) {
      if (dayPreset === 'custom') {
        setSelectedDays(['월']);
      } else {
        setSelectedDays(getPresetDays(dayPreset));
      }
    }
  };

  const applyDayPreset = (preset: DayPreset) => {
    setDayPreset(preset);
    if (preset === 'custom') {
      setSelectedDays((prev) => (prev.length > 0 ? prev : ['월']));
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

      return [...prev, day];
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

  const scheduleActive = allowNotifications && timeSettingEnabled;
  const periodOptions: ('오전' | '오후')[] = ['오전', '오후'];
  const hourOptions = Array.from({ length: 12 }, (_, index) => index + 1);
  const minuteOptions = Array.from({ length: 12 }, (_, index) => index * 5);
  const formattedTime = `${timePreference.period} ${timePreference.hour
    .toString()
    .padStart(2, '0')}:${timePreference.minute.toString().padStart(2, '0')}`;

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.headerBar}>
        <Pressable onPress={() => router.back()} hitSlop={8} style={({ pressed }) => [styles.headerButton, pressed && styles.buttonPressed]}>
          <Text style={styles.backText}>뒤로</Text>
        </Pressable>
        <Text style={styles.headerTitle}>알림 설정</Text>
        <View style={styles.headerSpacer} />
      </View>
      <View style={styles.content}>
        <View style={styles.row}>
          <Text style={styles.label}>알림 허용</Text>
          <Switch value={allowNotifications} onValueChange={toggleAllowNotifications} />
        </View>
        <View style={[styles.row, !allowNotifications && styles.disabledRow]}>
          <Text style={[styles.label, !allowNotifications && styles.disabledLabel]}>시간 설정</Text>
          <Switch
            value={timeSettingEnabled}
            onValueChange={toggleTimeSetting}
            disabled={!allowNotifications}
          />
        </View>
        <View style={[styles.scheduleSection, !scheduleActive && styles.disabledRow]}>
          <Text style={[styles.sectionLabel, !scheduleActive && styles.disabledLabel]}>희망 요일</Text>
          <View style={styles.presetRow}>
            {DAY_PRESET_OPTIONS.map((option) => (
              <Pressable
                key={option.key}
                disabled={!scheduleActive}
                onPress={() => applyDayPreset(option.key)}
                style={({ pressed }) => [
                  styles.radioButton,
                  dayPreset === option.key && styles.radioSelected,
                  pressed && scheduleActive && styles.radioPressed,
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
                    disabled={!scheduleActive}
                    onPress={() => handleSelectDay(day)}
                    style={({ pressed }) => [
                      styles.dayPill,
                      active && styles.dayPillActive,
                      pressed && scheduleActive && styles.dayPillPressed,
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
          style={[styles.scheduleSection, !scheduleActive && styles.disabledRow]}
          pointerEvents={scheduleActive && selectedDays.length > 0 ? 'auto' : 'none'}
        >
          <Text style={[styles.sectionLabel, (!scheduleActive || selectedDays.length === 0) && styles.disabledLabel]}>희망 시간</Text>
          {selectedDays.length === 0 ? (
            <Text style={[styles.placeholderText, !scheduleActive && styles.disabledLabel]}>희망 요일을 먼저 선택해 주세요.</Text>
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
                    contentContainerStyle={styles.pickerScrollContent}
                  >
                    {periodOptions.map((period) => (
                      <Pressable
                        key={period}
                        onPress={() => selectPeriod(period)}
                        style={({ pressed }) => [
                          styles.optionButton,
                          timePreference.period === period && styles.optionSelected,
                          pressed && styles.optionPressed,
                        ]}
                      >
                        <Text
                          style={[
                            styles.optionText,
                            timePreference.period === period && styles.optionTextSelected,
                          ]}
                        >
                          {period}
                        </Text>
                      </Pressable>
                    ))}
                  </ScrollView>
                </View>
                <View style={styles.pickerColumn}>
                  <Text style={styles.pickerColumnLabel}>시</Text>
                  <ScrollView
                    showsVerticalScrollIndicator
                    style={styles.pickerScroll}
                    contentContainerStyle={styles.pickerScrollContent}
                  >
                    {hourOptions.map((hour) => (
                      <Pressable
                        key={hour}
                        onPress={() => selectHour(hour)}
                        style={({ pressed }) => [
                          styles.optionButton,
                          timePreference.hour === hour && styles.optionSelected,
                          pressed && styles.optionPressed,
                        ]}
                      >
                        <Text
                          style={[
                            styles.optionText,
                            timePreference.hour === hour && styles.optionTextSelected,
                          ]}
                        >
                          {hour.toString().padStart(2, '0')}
                        </Text>
                      </Pressable>
                    ))}
                  </ScrollView>
                </View>
                <View style={styles.pickerColumn}>
                  <Text style={styles.pickerColumnLabel}>분</Text>
                  <ScrollView
                    showsVerticalScrollIndicator
                    style={styles.pickerScroll}
                    contentContainerStyle={styles.pickerScrollContent}
                  >
                    {minuteOptions.map((minute) => (
                      <Pressable
                        key={minute}
                        onPress={() => selectMinute(minute)}
                        style={({ pressed }) => [
                          styles.optionButton,
                          timePreference.minute === minute && styles.optionSelected,
                          pressed && styles.optionPressed,
                        ]}
                      >
                        <Text
                          style={[
                            styles.optionText,
                            timePreference.minute === minute && styles.optionTextSelected,
                          ]}
                        >
                          {minute.toString().padStart(2, '0')}
                        </Text>
                      </Pressable>
                    ))}
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
    backgroundColor: '#ffffff',
  },
  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 4,
  },
  headerButton: {
    alignSelf: 'flex-start',
  },
  buttonPressed: {
    opacity: 0.5,
  },
  backText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  headerSpacer: {
    width: 48,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#111827',
  },
  content: {
    paddingHorizontal: 24,
    paddingVertical: 28,
    gap: 24,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  label: {
    fontSize: 17,
    fontWeight: '500',
    color: '#111827',
  },
  disabledRow: {
    opacity: 0.4,
  },
  disabledLabel: {
    color: '#6b7280',
  },
  scheduleSection: {
    gap: 12,
  },
  sectionLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: '#374151',
  },
  presetRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  radioButton: {
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 999,
    backgroundColor: '#f3f4f6',
  },
  radioSelected: {
    backgroundColor: '#111827',
  },
  radioPressed: {
    opacity: 0.7,
  },
  radioLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
  },
  radioLabelSelected: {
    color: '#ffffff',
  },
  placeholderText: {
    fontSize: 14,
    color: '#6b7280',
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
    borderColor: '#111827',
    backgroundColor: '#111827',
  },
  dayPillPressed: {
    opacity: 0.7,
  },
  dayText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
  },
  dayTextActive: {
    color: '#ffffff',
  },
  timePickerCard: {
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    backgroundColor: '#f9fafb',
    gap: 16,
    shadowColor: '#000000',
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 3,
  },
  timeSummary: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
  },
  timeSummaryHint: {
    fontSize: 13,
    color: '#6b7280',
    textAlign: 'center',
  },
  pickerRow: {
    flexDirection: 'row',
    gap: 16,
    alignItems: 'flex-start',
  },
  pickerColumn: {
    flex: 1,
    minWidth: 90,
    gap: 10,
  },
  pickerColumnLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4b5563',
    textAlign: 'center',
  },
  pickerScroll: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 14,
    backgroundColor: '#ffffff',
    maxHeight: 220,
  },
  pickerScrollContent: {
    paddingHorizontal: 6,
    paddingVertical: 10,
    gap: 8,
  },
  optionButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    backgroundColor: '#f9fafb',
  },
  optionSelected: {
    backgroundColor: '#111827',
    borderColor: '#111827',
  },
  optionPressed: {
    opacity: 0.75,
  },
  optionText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#111827',
  },
  optionTextSelected: {
    color: '#ffffff',
  },
});
