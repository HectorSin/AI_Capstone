import React from 'react';
import { View, Text, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
import { AINews } from '../data/aiNews';
import { Company } from '../data/companies';

interface HomeScreenProps {
  allLatestNews: AINews[];
  companies: Company[];
  onNewsPress: (newsId: number) => void;
  onCompanyPress: (companyId: number) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  allLatestNews,
  companies,
  onNewsPress,
  onCompanyPress,
}) => {
  return (
    <View style={styles.homeContainer}>
      {/* 상단 헤더 */}
      <View style={styles.homeHeader}>
        <Text style={styles.appName}>AI 정보 센터</Text>
      </View>
      
      {/* 홈: 구독 섹션 이동 안내 */}
      <View style={{ paddingHorizontal: 20, paddingTop: 20 }}>
        <Text style={{ fontSize: 16, color: '#666' }}>
          기업 구독 하단 탭의 '구독'에서 관리할 수 있어요.
        </Text>
      </View>
       
       {/* AI 뉴스 섹션 */}
       <View style={styles.newsSection}>
         <Text style={styles.newsSectionTitle}>최신 AI 소식</Text>
         <FlatList
           data={allLatestNews}
           showsVerticalScrollIndicator={false}
           keyExtractor={(item) => item.id.toString()}
           renderItem={({ item }) => {
             const company = companies.find(c => c.id === item.companyId);
             return (
               <TouchableOpacity 
                 style={styles.newsCard}
                 onPress={() => onNewsPress(item.id)}
               >
                 <View style={styles.newsHeader}>
                   <TouchableOpacity 
                     style={[styles.companyIconSmall, { backgroundColor: company?.color }]}
                     onPress={(e) => {
                       e.stopPropagation();
                       onCompanyPress(item.companyId);
                     }}
                   >
                     <Text style={styles.companyTextSmall}>{item.companyId}</Text>
                   </TouchableOpacity>
                   <View style={styles.newsHeaderText}>
                     <Text style={styles.companyNameSmall}>
                       {company?.name}
                     </Text>
                     <Text style={styles.newsDate}>{item.date}</Text>
                   </View>
                 </View>
                 <Text style={styles.newsTitle}>{item.title}</Text>
                 <Text style={styles.newsContent} numberOfLines={3}>
                   {item.content}
                 </Text>
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
  newsSection: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
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
