import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ArchiveRemoteTab } from '@/components/archive/ArchiveRemoteTab';
import { ArchiveDownloadsTab } from '@/components/archive/ArchiveDownloadsTab';

const TAB_OPTIONS = [
  { key: 'remote', label: '보관함' },
  { key: 'downloads', label: '다운로드' },
] as const;

type ArchiveTabKey = typeof TAB_OPTIONS[number]['key'];

export default function ArchiveScreen() {
  const [activeTab, setActiveTab] = useState<ArchiveTabKey>('remote');

  return (
    <View style={styles.container}>
      <View style={styles.tabBar}>
        {TAB_OPTIONS.map((option) => {
          const isActive = option.key === activeTab;
          return (
            <Pressable
              key={option.key}
              onPress={() => setActiveTab(option.key)}
              style={({ pressed }) => [
                styles.tabButton,
                isActive && styles.tabButtonActive,
                pressed && styles.tabButtonPressed,
              ]}
            >
              <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>{option.label}</Text>
            </Pressable>
          );
        })}
      </View>
      <View style={styles.content}>{activeTab === 'remote' ? <ArchiveRemoteTab /> : <ArchiveDownloadsTab />}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  content: {
    flex: 1,
  },
  tabBar: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  tabButton: {
    flex: 1,
    borderRadius: 999,
    paddingVertical: 10,
    alignItems: 'center',
    backgroundColor: '#f3f4f6',
  },
  tabButtonActive: {
    backgroundColor: '#111827',
  },
  tabButtonPressed: {
    opacity: 0.7,
  },
  tabLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4b5563',
  },
  tabLabelActive: {
    color: '#ffffff',
  },
});
