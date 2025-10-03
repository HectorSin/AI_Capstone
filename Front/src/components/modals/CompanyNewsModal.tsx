import React from 'react';
import { Modal, View, Text, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
import { AINews } from '../../data/aiNews';
import { Company } from '../../data/companies';

interface CompanyNewsModalProps {
  visible: boolean;
  selectedCompanyId: number;
  companyNews: AINews[];
  company: Company | undefined;
  isSubscribed: boolean;
  onClose: () => void;
  onNewsPress: (newsId: number) => void;
  onToggleSubscription: (companyId: number) => void;
}

export const CompanyNewsModal: React.FC<CompanyNewsModalProps> = ({
  visible,
  selectedCompanyId,
  companyNews,
  company,
  isSubscribed,
  onClose,
  onNewsPress,
  onToggleSubscription,
}) => {
  return (
    <Modal
      animationType="slide"
      transparent={true}
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={styles.companyModalOverlay}>
        <View style={styles.companyModalContent}>
          <View style={styles.companyModalHeader}>
            <View style={styles.companyModalTitleContainer}>
              <View style={[
                styles.companyIconMedium, 
                { backgroundColor: company?.color }
              ]}>
                <Text style={styles.companyTextMedium}>{company?.id}</Text>
              </View>
              <Text style={styles.companyModalTitle}>
                {company?.name} 뉴스
              </Text>
            </View>
            <TouchableOpacity 
              style={styles.modalCloseButton}
              onPress={onClose}
            >
              <Text style={styles.modalCloseText}>✕</Text>
            </TouchableOpacity>
          </View>
          
          <FlatList
            data={companyNews}
            keyExtractor={(item) => item.id.toString()}
            showsVerticalScrollIndicator={false}
            renderItem={({ item }) => (
              <TouchableOpacity 
                style={styles.companyNewsItem}
                onPress={() => onNewsPress(item.id)}
              >
                <View style={styles.companyNewsHeader}>
                  <Text style={styles.companyNewsDate}>{item.date}</Text>
                </View>
                <Text style={styles.companyNewsTitle}>{item.title}</Text>
                <Text style={styles.companyNewsContent} numberOfLines={3}>
                  {item.content}
                </Text>
              </TouchableOpacity>
            )}
            contentContainerStyle={styles.companyNewsList}
          />
          
          {/* 구독 버튼 */}
          <View style={styles.subscribeButtonContainer}>
            <TouchableOpacity 
              style={[
                styles.subscribeButton,
                isSubscribed && styles.subscribeButtonActive
              ]}
              onPress={() => onToggleSubscription(selectedCompanyId)}
            >
              <Text style={[
                styles.subscribeButtonText,
                isSubscribed && styles.subscribeButtonTextActive
              ]}>
                {isSubscribed ? '구독 취소' : '구독하기'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  companyModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  companyModalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    minHeight: '70%',
  },
  companyModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  companyModalTitleContainer: {
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
  companyModalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
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
  companyNewsList: {
    padding: 20,
    paddingBottom: 100,
  },
  companyNewsItem: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  companyNewsHeader: {
    marginBottom: 8,
  },
  companyNewsDate: {
    fontSize: 12,
    color: '#666',
  },
  companyNewsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  companyNewsContent: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
  },
  subscribeButtonContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#e9ecef',
  },
  subscribeButton: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  subscribeButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  subscribeButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  subscribeButtonTextActive: {
    color: '#fff',
  },
});
