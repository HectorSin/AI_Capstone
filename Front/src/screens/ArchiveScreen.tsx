import React from 'react';
import { View, Text, TouchableOpacity, FlatList, TextInput, StyleSheet } from 'react-native';
import { Podcast } from '../data/podcasts';

interface ArchiveScreenProps {
  filteredPodcasts: Podcast[];
  searchText: string;
  onSearchChange: (text: string) => void;
  onPodcastPlay: (podcastId: number) => void;
}

export const ArchiveScreen: React.FC<ArchiveScreenProps> = ({
  filteredPodcasts,
  searchText,
  onSearchChange,
  onPodcastPlay,
}) => {
  return (
    <View style={styles.archiveContainer}>
      {/* 아카이브 헤더 */}
      <View style={styles.archiveHeader}>
        <Text style={styles.archiveTitle}>아카이브</Text>
      </View>
      
      {/* 검색 바 */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="팟캐스트 검색..."
          value={searchText}
          onChangeText={onSearchChange}
          placeholderTextColor="#999"
        />
      </View>
      
      {/* 팟캐스트 목록 */}
      <FlatList
        data={filteredPodcasts}
        keyExtractor={(item) => item.id.toString()}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <View style={styles.podcastCard}>
            <View style={styles.podcastHeader}>
              <Text style={styles.podcastDate}>{item.date}</Text>
              {item.isNew && (
                <View style={styles.newBadge}>
                  <Text style={styles.newBadgeText}>NEW</Text>
                </View>
              )}
            </View>
            <Text style={styles.podcastTitle}>{item.title}</Text>
            <Text style={styles.podcastContent}>{item.content}</Text>
            <Text style={styles.podcastDescription}>{item.description}</Text>
            <View style={styles.podcastFooter}>
              <Text style={styles.podcastDuration}>{item.duration}</Text>
              <TouchableOpacity 
                style={styles.playButton}
                onPress={() => onPodcastPlay(item.id)}
              >
                <Text style={styles.playButtonText}>팟캐스트 재생</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
        contentContainerStyle={styles.podcastList}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  archiveContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  archiveHeader: {
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
  archiveTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  searchContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
  },
  searchInput: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#333',
  },
  podcastList: {
    padding: 20,
    paddingBottom: 100,
  },
  podcastCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  podcastHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  podcastDate: {
    fontSize: 12,
    color: '#666',
  },
  newBadge: {
    backgroundColor: '#FF3B30',
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  newBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  podcastTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  podcastContent: {
    fontSize: 14,
    color: '#555',
    marginBottom: 8,
    lineHeight: 20,
  },
  podcastDescription: {
    fontSize: 12,
    color: '#666',
    marginBottom: 12,
    lineHeight: 16,
  },
  podcastFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  podcastDuration: {
    fontSize: 12,
    color: '#666',
  },
  playButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  playButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
});
