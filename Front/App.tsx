import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, Image, TouchableOpacity, Modal, TextInput, ScrollView } from 'react-native';
import { useState } from 'react';

// Import components
import { BottomNavigation } from './src/components/navigation/BottomNavigation';
import { NewsDetailModal } from './src/components/modals/NewsDetailModal';
import { CompanyNewsModal } from './src/components/modals/CompanyNewsModal';
import { PodcastPlayerModal } from './src/components/modals/PodcastPlayerModal';

// Import screens
import { HomeScreen } from './src/screens/HomeScreen';
import { SubscribeScreen } from './src/screens/SubscribeScreen';
import { ArchiveScreen } from './src/screens/ArchiveScreen';
import { SettingsScreen } from './src/screens/SettingsScreen';

// Import data and utils
import { companies } from './src/data/companies';
import { aiNewsData } from './src/data/aiNews';
import { podcastData } from './src/data/podcasts';
import { 
  getFilteredCompanies, 
  getAllLatestNews, 
  getLatestNews, 
  getCompanyNews, 
  getFilteredPodcasts,
  FilterType 
} from './src/utils/dataUtils';

export default function App() {
  // Login state
  const [loginModalVisible, setLoginModalVisible] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Navigation state
  const [currentScreen, setCurrentScreen] = useState('home');

  // Subscription state
  const [subscribedCompanies, setSubscribedCompanies] = useState<number[]>([]);
  const [filterType, setFilterType] = useState<FilterType>('all');

  // Toast state
  const [toastMessage, setToastMessage] = useState<string>('');
  const [showToast, setShowToast] = useState(false);
  const [toastTimer, setToastTimer] = useState<NodeJS.Timeout | null>(null);

  // Modal states
  const [companyNewsModal, setCompanyNewsModal] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState<number>(0);
  const [newsDetailModal, setNewsDetailModal] = useState(false);
  const [selectedNewsId, setSelectedNewsId] = useState<number>(0);
  const [fromCompanyModal, setFromCompanyModal] = useState(false);
  const [podcastPlayerModal, setPodcastPlayerModal] = useState(false);
  const [selectedPodcastId, setSelectedPodcastId] = useState<number>(0);

  // Search state
  const [searchText, setSearchText] = useState('');

  // Alarm settings state
  const [showAlarmSettings, setShowAlarmSettings] = useState(false);
  const [selectedDays, setSelectedDays] = useState<string[]>([]);
  const [alarmTimes, setAlarmTimes] = useState<{[key: string]: string}>({});
  const [timePickerVisible, setTimePickerVisible] = useState(false);
  const [selectedDayForTime, setSelectedDayForTime] = useState<string>('');
  const [selectedHour, setSelectedHour] = useState<number>(7);
  const [selectedMinute, setSelectedMinute] = useState<number>(30);

  // Podcast player state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalTime, setTotalTime] = useState(0);
  const [playbackTimer, setPlaybackTimer] = useState<NodeJS.Timeout | null>(null);

  // Constants
  const days = ['월', '화', '수', '목', '금', '토', '일'];
  const dayNames = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'];
  const hours = Array.from({length: 24}, (_, i) => i);
  const minutes = Array.from({length: 12}, (_, i) => i * 5);

  // Helper functions
  const showToastMessage = (message: string) => {
    if (toastTimer) {
      clearTimeout(toastTimer);
    }
    setToastMessage(message);
    setShowToast(true);
    const timer = setTimeout(() => {
      setShowToast(false);
      setToastMessage('');
    }, 1000);
    setToastTimer(timer);
  };

  const toggleSubscription = (companyId: number) => {
    setSubscribedCompanies(prev => {
      if (prev.includes(companyId)) {
        showToastMessage(`${companies.find(c => c.id === companyId)?.name} 구독이 취소되었습니다`);
        return prev.filter(id => id !== companyId);
      } else {
        showToastMessage(`${companies.find(c => c.id === companyId)?.name}이 구독되었습니다`);
        return [...prev, companyId];
      }
    });
  };

  const openNewsDetailModal = (newsId: number, fromCompany = false) => {
    setSelectedNewsId(newsId);
    setFromCompanyModal(fromCompany);
    setNewsDetailModal(true);
  };

  const openCompanyNewsModal = (companyId: number) => {
    setSelectedCompanyId(companyId);
    setCompanyNewsModal(true);
  };

  const openPodcastPlayer = (podcastId: number) => {
    const podcast = podcastData.find(p => p.id === podcastId);
    if (podcast) {
      setSelectedPodcastId(podcastId);
      setPodcastPlayerModal(true);
      
      // Parse duration (e.g., "15분 32초" -> 932 seconds)
      const durationMatch = podcast.duration.match(/(\d+)분\s*(\d+)초/);
      if (durationMatch) {
        const minutes = parseInt(durationMatch[1]);
        const seconds = parseInt(durationMatch[2]);
        setTotalTime(minutes * 60 + seconds);
      } else {
        setTotalTime(0);
      }
      
      setCurrentTime(0);
      setIsPlaying(false);
      
      // Clear any existing timer
      if (playbackTimer) {
        clearInterval(playbackTimer);
        setPlaybackTimer(null);
      }
    }
  };

  const togglePlayback = () => {
    setIsPlaying(prev => {
      if (!prev) {
        // Start playback
        const timer = setInterval(() => {
          setCurrentTime(prevTime => {
            if (prevTime >= totalTime) {
              setIsPlaying(false);
              clearInterval(timer);
              setPlaybackTimer(null);
              return 0;
            }
            return prevTime + 1;
          });
        }, 1000);
        setPlaybackTimer(timer);
        return true;
      } else {
        // Pause playback
        if (playbackTimer) {
          clearInterval(playbackTimer);
          setPlaybackTimer(null);
        }
        return false;
      }
    });
  };

  const rewind = () => {
    setCurrentTime(prev => Math.max(0, prev - 10));
  };

  const fastForward = () => {
    setCurrentTime(prev => Math.min(totalTime, prev + 10));
  };

  const seekTo = (percentage: number) => {
    setCurrentTime(Math.floor(totalTime * percentage));
  };

  const closePodcastPlayer = () => {
    setPodcastPlayerModal(false);
    setIsPlaying(false);
    setCurrentTime(0);
    if (playbackTimer) {
      clearInterval(playbackTimer);
      setPlaybackTimer(null);
    }
  };

  const resetPodcast = () => {
    setCurrentTime(0);
    setIsPlaying(false);
    if (playbackTimer) {
      clearInterval(playbackTimer);
      setPlaybackTimer(null);
    }
  };

  // Get data
  const filteredCompanies = getFilteredCompanies(filterType, subscribedCompanies);
  const allLatestNews = getAllLatestNews();
  const latestNews = getLatestNews(filterType, subscribedCompanies);
  const companyNews = getCompanyNews(selectedCompanyId);
  const filteredPodcasts = getFilteredPodcasts(searchText);
  const selectedNews = aiNewsData.find(n => n.id === selectedNewsId);
  
  // 뉴스 상세 모달이 열려있을 때는 뉴스의 companyId 사용, 그렇지 않으면 selectedCompanyId 사용
  let selectedCompany;
  if (newsDetailModal && selectedNews) {
    selectedCompany = companies.find(c => c.id === selectedNews.companyId);
  } else if (companyNewsModal && selectedCompanyId > 0) {
    selectedCompany = companies.find(c => c.id === selectedCompanyId);
  } else {
    selectedCompany = undefined;
  }
  
  const selectedPodcast = podcastData.find(p => p.id === selectedPodcastId);

  // Render login modal
  const renderLoginModal = () => (
    <Modal
      animationType="slide"
      transparent={true}
      visible={loginModalVisible}
      onRequestClose={() => setLoginModalVisible(false)}
    >
      <View style={styles.loginOverlay}>
        <View style={styles.loginContent}>
          <Text style={styles.loginTitle}>로그인</Text>
          
          <TextInput
            style={styles.loginInput}
            placeholder="이메일"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />
          
          <TextInput
            style={styles.loginInput}
            placeholder="비밀번호"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />
          
          <TouchableOpacity 
            style={styles.loginButton}
            onPress={() => {
              setIsLoggedIn(true);
              setLoginModalVisible(false);
            }}
          >
            <Text style={styles.loginButtonText}>로그인</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.googleLoginButton}>
            <Text style={styles.googleLoginText}>Google로 로그인</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  // Render alarm settings modal
  const renderAlarmSettingsModal = () => (
    <Modal
      animationType="slide"
      transparent={true}
      visible={showAlarmSettings}
      onRequestClose={() => setShowAlarmSettings(false)}
    >
      <View style={styles.alarmOverlay}>
        <View style={styles.alarmContent}>
          <Text style={styles.alarmTitle}>알림 설정</Text>
          
          <View style={styles.daysContainer}>
            {days.map((day, index) => (
              <TouchableOpacity
                key={day}
                style={[
                  styles.dayButton,
                  selectedDays.includes(day) && styles.dayButtonActive
                ]}
                onPress={() => {
                  setSelectedDays(prev => 
                    prev.includes(day) 
                      ? prev.filter(d => d !== day)
                      : [...prev, day]
                  );
                }}
              >
                <Text style={[
                  styles.dayButtonText,
                  selectedDays.includes(day) && styles.dayButtonTextActive
                ]}>
                  {day}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          
          
          {selectedDays.length > 0 && (
            <View style={styles.timeSettingsContainer}>
              <Text style={styles.timeSettingsTitle}>예약 시간</Text>
              {selectedDays
                .sort((a, b) => days.indexOf(a) - days.indexOf(b))
                .map(day => (
                  <View key={day} style={styles.timeRow}>
                    <Text style={styles.dayLabel}>{dayNames[days.indexOf(day)]}</Text>
                    <TouchableOpacity
                      style={styles.timeButton}
                      onPress={() => {
                        setSelectedDayForTime(day);
                        setTimePickerVisible(true);
                      }}
                    >
                      <Text style={styles.timeButtonText}>
                        {alarmTimes[day] || '시간 선택'}
                      </Text>
                    </TouchableOpacity>
                  </View>
                ))}
            </View>
          )}
          
          {timePickerVisible && (
            <View style={styles.timePickerOverlay}>
              <View style={styles.timePickerModal}>
                <Text style={styles.timePickerTitle}>
                  {dayNames[days.indexOf(selectedDayForTime)]} 시간 설정
                </Text>
                
                <View style={styles.timePickerRow}>
                  <View style={styles.timePickerColumn}>
                    <Text style={styles.timePickerLabel}>시간</Text>
                    <ScrollView style={styles.timePickerScroll} showsVerticalScrollIndicator={false}>
                      {hours.map(hour => (
                        <TouchableOpacity
                          key={hour}
                          style={[
                            styles.timePickerItem,
                            selectedHour === hour && styles.timePickerItemActive
                          ]}
                          onPress={() => setSelectedHour(hour)}
                        >
                          <Text style={[
                            styles.timePickerItemText,
                            selectedHour === hour && styles.timePickerItemTextActive
                          ]}>
                            {hour}시
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </ScrollView>
                  </View>
                  
                  <View style={styles.timePickerColumn}>
                    <Text style={styles.timePickerLabel}>분</Text>
                    <ScrollView style={styles.timePickerScroll} showsVerticalScrollIndicator={false}>
                      {minutes.map(minute => (
                        <TouchableOpacity
                          key={minute}
                          style={[
                            styles.timePickerItem,
                            selectedMinute === minute && styles.timePickerItemActive
                          ]}
                          onPress={() => setSelectedMinute(minute)}
                        >
                          <Text style={[
                            styles.timePickerItemText,
                            selectedMinute === minute && styles.timePickerItemTextActive
                          ]}>
                            {minute.toString().padStart(2, '0')}분
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </ScrollView>
                  </View>
                </View>
                
                <View style={styles.timePickerButtons}>
                  <TouchableOpacity
                    style={styles.timePickerCancelButton}
                    onPress={() => setTimePickerVisible(false)}
                  >
                    <Text style={styles.timePickerCancelText}>취소</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.timePickerConfirmButton}
                    onPress={() => {
                      const timeString = `${selectedHour}시 ${selectedMinute.toString().padStart(2, '0')}분`;
                      setAlarmTimes(prev => ({
                        ...prev,
                        [selectedDayForTime]: timeString
                      }));
                      setTimePickerVisible(false);
                    }}
                  >
                    <Text style={styles.timePickerConfirmText}>확인</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          )}
          
          <TouchableOpacity 
            style={styles.alarmConfirmButton}
            onPress={() => setShowAlarmSettings(false)}
          >
            <Text style={styles.alarmConfirmText}>확인</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  // Render toast
  const renderToast = () => {
    if (!showToast) return null;
    
    return (
      <View style={styles.toastContainer}>
        <Text style={styles.toastText}>{toastMessage}</Text>
      </View>
    );
  };

  // Render current screen
  const renderCurrentScreen = () => {
    if (!isLoggedIn) {
      return (
        <View style={styles.welcomeContainer}>
          <Image source={require('./assets/logo.png')} style={styles.logo} />
          <Text style={styles.slogan}>세상의 모든 AI 정보를 원하는 정보만</Text>
          <TouchableOpacity 
            style={styles.aiInfoButton}
            onPress={() => setLoginModalVisible(true)}
          >
            <Text style={styles.aiInfoButtonText}>AI 정보 받기</Text>
          </TouchableOpacity>
        </View>
      );
    }

    switch (currentScreen) {
      case 'home':
        return (
          <HomeScreen
            allLatestNews={allLatestNews}
            companies={companies}
            onNewsPress={openNewsDetailModal}
            onCompanyPress={openCompanyNewsModal}
          />
        );
      case 'subscribe':
        return (
          <SubscribeScreen
            filteredCompanies={filteredCompanies}
            latestNews={latestNews}
            companies={companies}
            filterType={filterType}
            subscribedCompanies={subscribedCompanies}
            onFilterChange={setFilterType}
            onToggleSubscription={toggleSubscription}
            onNewsPress={openNewsDetailModal}
            onCompanyPress={openCompanyNewsModal}
          />
        );
      case 'archive':
        return (
          <ArchiveScreen
            filteredPodcasts={filteredPodcasts}
            searchText={searchText}
            onSearchChange={setSearchText}
            onPodcastPlay={openPodcastPlayer}
          />
        );
      case 'settings':
        return (
          <SettingsScreen
            onBackToHome={() => setCurrentScreen('home')}
            onAlarmSettings={() => setShowAlarmSettings(true)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <View style={styles.container}>
      {renderCurrentScreen()}
      
      {isLoggedIn && (
        <BottomNavigation
          currentScreen={currentScreen}
          onNavigate={setCurrentScreen}
        />
      )}
      
      {renderToast()}
      {renderLoginModal()}
      {renderAlarmSettingsModal()}
      
      <NewsDetailModal
        visible={newsDetailModal}
        selectedNewsId={selectedNewsId}
        fromCompanyModal={fromCompanyModal}
        onClose={() => {
          setNewsDetailModal(false);
          if (fromCompanyModal) {
            setCompanyNewsModal(true);
          }
        }}
        onOpenCompanyNews={openCompanyNewsModal}
        news={selectedNews}
        company={selectedCompany}
      />
      
      <CompanyNewsModal
        visible={companyNewsModal}
        selectedCompanyId={selectedCompanyId}
        companyNews={companyNews}
        company={selectedCompany}
        isSubscribed={subscribedCompanies.includes(selectedCompanyId)}
        onClose={() => setCompanyNewsModal(false)}
        onNewsPress={(newsId) => {
          setCompanyNewsModal(false);
          openNewsDetailModal(newsId, true);
        }}
        onToggleSubscription={toggleSubscription}
      />
      
      <PodcastPlayerModal
        visible={podcastPlayerModal}
        selectedPodcastId={selectedPodcastId}
        podcast={selectedPodcast}
        isPlaying={isPlaying}
        currentTime={currentTime}
        totalTime={totalTime}
        onClose={closePodcastPlayer}
        onTogglePlayback={togglePlayback}
        onRewind={rewind}
        onFastForward={fastForward}
        onSeekTo={seekTo}
        onReset={resetPodcast}
      />
      
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  welcomeContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 20,
  },
  logo: {
    width: 120,
    height: 120,
    marginBottom: 20,
  },
  slogan: {
    fontSize: 18,
    color: '#333',
    textAlign: 'center',
    marginBottom: 40,
    lineHeight: 26,
  },
  aiInfoButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 40,
    paddingVertical: 16,
    borderRadius: 12,
  },
  aiInfoButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  loginOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginContent: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 30,
    width: '80%',
    maxWidth: 400,
  },
  loginTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30,
    color: '#333',
  },
  loginInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    marginBottom: 16,
    backgroundColor: '#f8f9fa',
  },
  loginButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 16,
  },
  loginButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  googleLoginButton: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  googleLoginText: {
    color: '#333',
    fontSize: 16,
    fontWeight: 'bold',
  },
  alarmOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  alarmContent: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 30,
    width: '90%',
    maxWidth: 400,
    maxHeight: '80%',
  },
  alarmTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30,
    color: '#333',
  },
  daysContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  dayButton: {
    width: '13%',
    aspectRatio: 1,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  dayButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  dayButtonText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#666',
  },
  dayButtonTextActive: {
    color: '#fff',
  },
  timeSettingsContainer: {
    marginBottom: 20,
  },
  timeSettingsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  timeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  dayLabel: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  timeButton: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  timeButtonText: {
    fontSize: 14,
    color: '#333',
  },
  timePickerOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  timePickerModal: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    width: '80%',
    maxWidth: 300,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  timePickerTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
    textAlign: 'center',
  },
  timePickerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  timePickerColumn: {
    flex: 1,
    marginHorizontal: 8,
  },
  timePickerLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#666',
    textAlign: 'center',
    marginBottom: 8,
  },
  timePickerScroll: {
    maxHeight: 150,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
  },
  timePickerItem: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    backgroundColor: '#fff',
  },
  timePickerItemActive: {
    backgroundColor: '#007AFF',
  },
  timePickerItemText: {
    fontSize: 14,
    color: '#333',
    textAlign: 'center',
  },
  timePickerItemTextActive: {
    color: '#fff',
  },
  timePickerButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  timePickerCancelButton: {
    flex: 1,
    backgroundColor: '#f0f0f0',
    paddingVertical: 12,
    borderRadius: 8,
    marginRight: 8,
  },
  timePickerCancelText: {
    color: '#666',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  timePickerConfirmButton: {
    flex: 1,
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 8,
    marginLeft: 8,
  },
  timePickerConfirmText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  alarmConfirmButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  alarmConfirmText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  toastContainer: {
    position: 'absolute',
    bottom: 100,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  toastText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
