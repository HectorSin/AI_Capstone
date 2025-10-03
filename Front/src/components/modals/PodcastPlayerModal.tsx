import React from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Podcast } from '../../data/podcasts';

interface PodcastPlayerModalProps {
  visible: boolean;
  selectedPodcastId: number;
  podcast: Podcast | undefined;
  isPlaying: boolean;
  currentTime: number;
  totalTime: number;
  onClose: () => void;
  onTogglePlayback: () => void;
  onRewind: () => void;
  onFastForward: () => void;
  onSeekTo: (percentage: number) => void;
  onReset: () => void;
}

export const PodcastPlayerModal: React.FC<PodcastPlayerModalProps> = ({
  visible,
  selectedPodcastId,
  podcast,
  isPlaying,
  currentTime,
  totalTime,
  onClose,
  onTogglePlayback,
  onRewind,
  onFastForward,
  onSeekTo,
  onReset,
}) => {
  if (!podcast) {
    return (
      <Modal
        animationType="slide"
        transparent={false}
        visible={visible}
        onRequestClose={onClose}
      >
        <View style={styles.podcastPlayerContainer}>
          <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
            <Text>팟캐스트를 찾을 수 없습니다.</Text>
          </View>
        </View>
      </Modal>
    );
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Modal
      animationType="slide"
      transparent={false}
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={styles.podcastPlayerContainer}>
        {/* 헤더 */}
        <View style={styles.playerHeader}>
          <TouchableOpacity 
            style={styles.playerBackButton}
            onPress={onClose}
          >
            <Text style={styles.playerBackText}>◀</Text>
          </TouchableOpacity>
          <Text style={styles.playerHeaderTitle}>팟캐스트</Text>
          <View style={styles.playerHeaderSpace} />
        </View>

        {/* 인포그래픽스 영역 (PDF 자리) */}
        <View style={styles.infographicsContainer}>
          <View style={styles.infographicsPlaceholder}>
            <Text style={styles.infographicsTitle}>AI 팟캐스트</Text>
            <Text style={styles.infographicsSubtitle}>청취의 미래를 열다</Text>
            <Text style={styles.infographicsDescription}>
              인공지능 기술의 최신 동향을 전문가가 쉽게 풀어 설명합니다. 오늘의 핫 토픽과 미래 전망까지 한 번에 확인하세요.
            </Text>
            <View style={styles.infographicsStats}>
              <Text style={styles.statsText}>약 3,060억 달러</Text>
              <Text style={styles.statsSubText}>글로벌 AI 시장 규모</Text>
            </View>
            <Text style={styles.pdfNote}>📄 상세 인포그래픽스는 PDF로 제공됩니다</Text>
          </View>
        </View>

        {/* 팟캐스트 정보 */}
        <View style={styles.podcastInfo}>
          <Text style={styles.podcastPlayerDate}>{podcast.date}</Text>
          <Text style={styles.podcastPlayerTitle}>{podcast.title}</Text>
          <Text style={styles.podcastPlayerContent}>{podcast.content}</Text>
        </View>

        {/* 오디오 플레이어 (임시 동작) */}
        <View style={styles.audioPlayer}>
          <View style={styles.progressContainer}>
            <TouchableOpacity 
              style={styles.progressBar}
              onPress={(e) => {
                const { locationX } = e.nativeEvent;
                const barWidth = 300; // 임시 너비
                const percentage = locationX / barWidth;
                onSeekTo(Math.max(0, Math.min(1, percentage)));
              }}
            >
              <View 
                style={[styles.progressFill, { width: totalTime > 0 ? `${(currentTime / totalTime) * 100}%` : '0%' }]} 
              />
              <View 
                style={[styles.progressThumb, { left: totalTime > 0 ? `${(currentTime / totalTime) * 100}%` : '0%' }]} 
              />
            </TouchableOpacity>
            <View style={styles.timeContainer}>
              <Text style={styles.timeText}>{formatTime(currentTime)}</Text>
              <Text style={styles.timeText}>{formatTime(totalTime)}</Text>
            </View>
          </View>

          <View style={styles.controlsContainer}>
            <TouchableOpacity style={styles.controlButton} onPress={onClose}>
              <Text style={styles.controlButtonText}>✕</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.controlButton} onPress={onRewind}>
              <Text style={styles.controlButtonText}>⏪</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.playPauseButton} onPress={onTogglePlayback}>
              <Text style={styles.playPauseText}>{isPlaying ? '⏸' : '▶'}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.controlButton} onPress={onFastForward}>
              <Text style={styles.controlButtonText}>⏩</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.controlButton} onPress={onReset}>
              <Text style={styles.controlButtonText}>🔁</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  podcastPlayerContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  playerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  playerBackButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playerBackText: {
    fontSize: 18,
    color: '#333',
  },
  playerHeaderTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
  },
  playerHeaderSpace: {
    width: 40,
  },
  infographicsContainer: {
    padding: 20,
  },
  infographicsPlaceholder: {
    backgroundColor: '#f8f9fa',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
  },
  infographicsTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  infographicsSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 16,
  },
  infographicsDescription: {
    fontSize: 14,
    color: '#555',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  infographicsStats: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  statsText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
  },
  statsSubText: {
    fontSize: 12,
    color: '#fff',
    textAlign: 'center',
    marginTop: 4,
  },
  pdfNote: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  podcastInfo: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  podcastPlayerDate: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  podcastPlayerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  podcastPlayerContent: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
  },
  audioPlayer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e9ecef',
    padding: 20,
  },
  progressContainer: {
    marginBottom: 20,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#e9ecef',
    borderRadius: 2,
    position: 'relative',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 2,
  },
  progressThumb: {
    position: 'absolute',
    top: -6,
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: '#007AFF',
    transform: [{ translateX: -8 }],
  },
  timeContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  timeText: {
    fontSize: 12,
    color: '#666',
  },
  controlsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  controlButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#f8f9fa',
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 8,
  },
  controlButtonText: {
    fontSize: 20,
    color: '#333',
  },
  playPauseButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 8,
  },
  playPauseText: {
    fontSize: 24,
    color: '#fff',
  },
});
