import React from 'react';
import { Modal, View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { AINews } from '../../data/aiNews';
import { Company, companies } from '../../data/companies';

interface NewsDetailModalProps {
  visible: boolean;
  selectedNewsId: number;
  fromCompanyModal: boolean;
  onClose: () => void;
  onOpenCompanyNews: (companyId: number) => void;
  news: AINews | undefined;
  company: Company | undefined;
}

export const NewsDetailModal: React.FC<NewsDetailModalProps> = ({
  visible,
  selectedNewsId,
  fromCompanyModal,
  onClose,
  onOpenCompanyNews,
  news,
  company,
}) => {
  if (!news) return null;
  
  // 뉴스에서 직접 회사 정보 찾기 (fallback)
  const newsCompany = company || companies.find(c => c.id === news.companyId);

  return (
    <Modal
      animationType="slide"
      transparent={true}
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={styles.newsDetailOverlay}>
        <View style={styles.newsDetailContent}>
          <View style={styles.newsDetailHeader}>
            <View style={styles.newsDetailTitleContainer}>
              <TouchableOpacity 
                style={[
                  styles.companyIconMedium, 
                  { backgroundColor: newsCompany?.color }
                ]}
                onPress={() => {
                  onClose();
                  onOpenCompanyNews(news.companyId);
                }}
              >
                <Text style={styles.companyTextMedium}>{news.companyId}</Text>
              </TouchableOpacity>
              <View style={styles.newsDetailTitleText}>
                <Text style={styles.newsDetailCompany}>{newsCompany?.name}</Text>
                <Text style={styles.newsDetailDate}>{news.date}</Text>
              </View>
            </View>
            <TouchableOpacity 
              style={styles.modalCloseButton}
              onPress={onClose}
            >
              <Text style={styles.modalCloseText}>✕</Text>
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.newsDetailScroll} showsVerticalScrollIndicator={false}>
            <Text style={styles.newsDetailTitle}>{news.title}</Text>
            <Text style={styles.newsDetailSummary}>{news.summary}</Text>
            
            <View style={styles.infoSection}>
              <Text style={styles.infoSectionTitle}>🔥 핵심 포인트</Text>
              {news.keyPoints.map((point, index) => (
                <View key={index} style={styles.keyPointItem}>
                  <Text style={styles.keyPointBullet}>•</Text>
                  <Text style={styles.keyPointText}>{point}</Text>
                </View>
              ))}
            </View>
            
            <View style={styles.infoSection}>
              <Text style={styles.infoSectionTitle}>💡 기대 효과</Text>
              <Text style={styles.infoText}>{news.impact}</Text>
            </View>
            
            <View style={styles.infoSection}>
              <Text style={styles.infoSectionTitle}>⚡ 핵심 기술</Text>
              <Text style={styles.infoText}>{news.technology}</Text>
            </View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  newsDetailOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  newsDetailContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    minHeight: '70%',
  },
  newsDetailHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  newsDetailTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  companyIconMedium: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  companyTextMedium: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  newsDetailTitleText: {
    flex: 1,
  },
  newsDetailCompany: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  newsDetailDate: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  modalCloseButton: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#f8f9fa',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalCloseText: {
    fontSize: 16,
    color: '#666',
  },
  newsDetailScroll: {
    flex: 1,
    padding: 20,
  },
  newsDetailTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
    lineHeight: 28,
  },
  newsDetailSummary: {
    fontSize: 16,
    color: '#555',
    marginBottom: 20,
    lineHeight: 24,
  },
  infoSection: {
    marginBottom: 24,
  },
  infoSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  keyPointItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  keyPointBullet: {
    fontSize: 16,
    color: '#007AFF',
    marginRight: 8,
    marginTop: 2,
  },
  keyPointText: {
    flex: 1,
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
  },
  infoText: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
  },
});
