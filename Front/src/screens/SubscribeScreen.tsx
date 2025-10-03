import React from 'react';
import { View, Text, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
import { AINews } from '../data/aiNews';
import { Company } from '../data/companies';
import { FilterType } from '../utils/dataUtils';

interface SubscribeScreenProps {
  filteredCompanies: Company[];
  latestNews: AINews[];
  companies: Company[];
  filterType: FilterType;
  subscribedCompanies: number[];
  onFilterChange: (filterType: FilterType) => void;
  onToggleSubscription: (companyId: number) => void;
  onNewsPress: (newsId: number) => void;
  onCompanyPress: (companyId: number) => void;
}

export const SubscribeScreen: React.FC<SubscribeScreenProps> = ({
  filteredCompanies,
  latestNews,
  companies,
  filterType,
  subscribedCompanies,
  onFilterChange,
  onToggleSubscription,
  onNewsPress,
  onCompanyPress,
}) => {
  return (
    <View style={styles.homeContainer}>
      {/* 상단 헤더 */}
      <View style={styles.homeHeader}>
        <Text style={styles.appName}>구독 관리</Text>
      </View>

      {/* 기업 아이콘 + 필터 */}
      <View style={styles.companiesSection}>
        <FlatList
          data={filteredCompanies}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => {
            const isSubscribed = subscribedCompanies.includes(item.id);
            return (
              <TouchableOpacity 
                style={styles.companyIcon}
                onPress={() => onToggleSubscription(item.id)}
              >
                <View style={[
                  styles.companyCircle, 
                  { 
                    backgroundColor: isSubscribed ? item.color : item.color + '80',
                    borderWidth: isSubscribed ? 3 : 1,
                    borderColor: isSubscribed ? '#007AFF' : '#ddd'
                  }
                ]}>
                  <Text style={styles.companyText}>{item.id}</Text>
                  {isSubscribed && (
                    <View style={styles.subscribedIndicator}>
                      <Text style={styles.subscribedText}>✓</Text>
                    </View>
                  )}
                </View>
                <Text style={[
                  styles.companyName,
                  isSubscribed && styles.subscribedCompanyName
                ]}>
                  {item.name}
                </Text>
              </TouchableOpacity>
            );
          }}
          contentContainerStyle={styles.companiesList}
        />

        {/* 구분선 */}
        <View style={styles.homeDividerLine} />

        {/* 필터 버튼들 */}
        <View style={styles.filterSection}>
          <TouchableOpacity 
            style={[styles.filterButton, filterType === 'all' && styles.filterButtonActive]}
            onPress={() => onFilterChange('all')}
          >
            <Text style={[styles.filterButtonText, filterType === 'all' && styles.filterButtonTextActive]}>전체</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.filterButton, filterType === 'subscribed' && styles.filterButtonActive]}
            onPress={() => onFilterChange('subscribed')}
          >
            <Text style={[styles.filterButtonText, filterType === 'subscribed' && styles.filterButtonTextActive]}>구독</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.filterButton, filterType === 'unsubscribed' && styles.filterButtonActive]}
            onPress={() => onFilterChange('unsubscribed')}
          >
            <Text style={[styles.filterButtonText, filterType === 'unsubscribed' && styles.filterButtonTextActive]}>미구독</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* 구독 화면에도 최신 소식 리스트 (필터 적용) */}
      <View style={styles.newsSection}>
        <Text style={styles.newsSectionTitle}>최신 AI 소식</Text>
        <FlatList
          data={latestNews}
          showsVerticalScrollIndicator={false}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => {
            const company = companies.find(c => c.id === item.companyId);
            return (
              <TouchableOpacity style={styles.newsCard} onPress={() => onNewsPress(item.id)}>
                <View style={styles.newsHeader}>
                  <TouchableOpacity 
                    style={[styles.companyIconSmall, { backgroundColor: company?.color }]}
                    onPress={(e) => { e.stopPropagation(); onCompanyPress(item.companyId); }}
                  >
                    <Text style={styles.companyTextSmall}>{item.companyId}</Text>
                  </TouchableOpacity>
                  <View style={styles.newsHeaderText}>
                    <Text style={styles.companyNameSmall}>{company?.name}</Text>
                    <Text style={styles.newsDate}>{item.date}</Text>
                  </View>
                </View>
                <Text style={styles.newsTitle}>{item.title}</Text>
                <Text style={styles.newsContent} numberOfLines={3}>{item.content}</Text>
              </TouchableOpacity>
            );
          }}
          contentContainerStyle={styles.newsList}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  homeContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  homeHeader: {
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
  appName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  companiesSection: {
    paddingTop: 20,
  },
  companiesList: {
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  companyIcon: {
    alignItems: 'center',
    marginRight: 20,
  },
  companyCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
    position: 'relative',
  },
  companyText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  subscribedIndicator: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#fff',
  },
  subscribedText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  companyName: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  subscribedCompanyName: {
    color: '#007AFF',
    fontWeight: 'bold',
  },
  homeDividerLine: {
    height: 1,
    backgroundColor: '#e9ecef',
    marginHorizontal: 20,
    marginBottom: 12,
  },
  filterSection: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  filterButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#f8f9fa',
    marginRight: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  filterButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  filterButtonText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#666',
  },
  filterButtonTextActive: {
    color: '#fff',
  },
  newsSection: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  newsSectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  newsList: {
    paddingBottom: 20,
  },
  newsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  newsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  companyIconSmall: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  companyTextSmall: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  newsHeaderText: {
    flex: 1,
  },
  companyNameSmall: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  newsDate: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  newsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
    lineHeight: 22,
  },
  newsContent: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
  },
});
