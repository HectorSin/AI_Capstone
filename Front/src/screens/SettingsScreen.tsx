import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface SettingsScreenProps {
  onBackToHome: () => void;
  onAlarmSettings: () => void;
}

export const SettingsScreen: React.FC<SettingsScreenProps> = ({
  onBackToHome,
  onAlarmSettings,
}) => {
  return (
    <View style={styles.settingsContainer}>
      <View style={styles.settingsHeader}>
        <TouchableOpacity 
          style={styles.backToHomeButton}
          onPress={onBackToHome}
        >
          <Text style={styles.backToHomeText}>← 홈으로</Text>
        </TouchableOpacity>
        <Text style={styles.settingsTitle}>설정</Text>
        <View style={styles.placeholder} />
      </View>
      
      <View style={styles.settingsContent}>
        <Text style={styles.settingsMainTitle}>설정</Text>
        <Text style={styles.settingsSubtitle}>계정 및 앱 설정을 관리하세요</Text>
        
        <View style={styles.featureContainer}>
          <TouchableOpacity 
            style={styles.featureButton}
            onPress={onAlarmSettings}
          >
            <Text style={styles.featureIcon}>⏰</Text>
            <Text style={styles.featureText}>알림 설정</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.featureButton}>
            <Text style={styles.featureIcon}>📊</Text>
            <Text style={styles.featureText}>AI 트렌드</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.featureButton}>
            <Text style={styles.featureIcon}>🔔</Text>
            <Text style={styles.featureText}>AI 구독 상태</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.featureButton}>
            <Text style={styles.featureIcon}>🔍</Text>
            <Text style={styles.featureText}>AI 검색</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  settingsContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  settingsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  backToHomeButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  backToHomeText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: 'bold',
  },
  settingsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  placeholder: {
    width: 60,
  },
  settingsContent: {
    flex: 1,
    padding: 20,
  },
  settingsMainTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  settingsSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 40,
  },
  featureContainer: {
    gap: 16,
  },
  featureButton: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  featureIcon: {
    fontSize: 24,
    marginRight: 16,
  },
  featureText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
});
