import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, Image, TouchableOpacity, Modal, TextInput, ScrollView, FlatList } from 'react-native';
import { useState } from 'react';

export default function App() {
  const [loginModalVisible, setLoginModalVisible] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showAlarmSettings, setShowAlarmSettings] = useState(false);
  const [currentScreen, setCurrentScreen] = useState('home'); // 'home', 'settings', 'archive', 'subscribe'
  const [subscribedCompanies, setSubscribedCompanies] = useState<number[]>([]); // 구독한 기업 ID 배열
  const [toastMessage, setToastMessage] = useState<string>('');
  const [showToast, setShowToast] = useState(false);
  const [toastTimer, setToastTimer] = useState<NodeJS.Timeout | null>(null);
  const [filterType, setFilterType] = useState<'all' | 'subscribed' | 'unsubscribed'>('all');
  const [companyNewsModal, setCompanyNewsModal] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState<number>(0);
  const [newsDetailModal, setNewsDetailModal] = useState(false);
  const [selectedNewsId, setSelectedNewsId] = useState<number>(0);
  const [fromCompanyModal, setFromCompanyModal] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [podcastPlayerModal, setPodcastPlayerModal] = useState(false);
  const [selectedPodcastId, setSelectedPodcastId] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalTime, setTotalTime] = useState(0);
  const [playbackTimer, setPlaybackTimer] = useState<NodeJS.Timeout | null>(null);
  
  // 알림 설정 상태
  const [selectedDays, setSelectedDays] = useState<string[]>([]);
  const [alarmTimes, setAlarmTimes] = useState<{[key: string]: string}>({});
  const [timePickerVisible, setTimePickerVisible] = useState(false);
  const [selectedDayForTime, setSelectedDayForTime] = useState<string>('');
  const [selectedHour, setSelectedHour] = useState<number>(7);
  const [selectedMinute, setSelectedMinute] = useState<number>(30);
  
  const days = ['월', '화', '수', '목', '금', '토', '일'];
  const dayNames = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'];
  
  // 시간 선택 옵션
  const hours = Array.from({length: 24}, (_, i) => i);
  const minutes = Array.from({length: 12}, (_, i) => i * 5);
  
  // 기업 아이콘 데이터
  const companies = [
    { id: 1, name: '기업1', color: '#FF6B6B' },
    { id: 2, name: '기업2', color: '#4ECDC4' },
    { id: 3, name: '기업3', color: '#45B7D1' },
    { id: 4, name: '기업4', color: '#96CEB4' },
    { id: 5, name: '기업5', color: '#FFEAA7' },
    { id: 6, name: '기업6', color: '#DDA0DD' },
    { id: 7, name: '기업7', color: '#98D8C8' },
    { id: 8, name: '기업8', color: '#F7DC6F' },
    { id: 9, name: '기업9', color: '#BB8FCE' },
    { id: 10, name: '기업10', color: '#85C1E9' },
  ];

  // AI 뉴스 데이터 (샘플) - 기업별로 여러 뉴스 가능, 날짜순 정렬
  const aiNewsData = [
    { 
      id: 1, 
      companyId: 7, 
      title: '금융 AI 보안 강화', 
      content: '금융 거래에서 AI 기반 보안 시스템이 사기 탐지율을 크게 높였습니다.', 
      date: '2025.01.20',
      summary: '새로운 AI 보안 시스템으로 금융 사기 예방',
      keyPoints: ['사기 탐지율 95% 향상', '실시간 위험 분석', '고객 피해 70% 감소'],
      impact: '연간 1000억원 규모의 금융 사기 예방 효과',
      technology: 'Machine Learning, 패턴 인식, 실시간 분석'
    },
    { 
      id: 2, 
      companyId: 3, 
      title: '자율주행 AI 업데이트', 
      content: '자율주행 시스템의 안전성이 크게 향상되었습니다. 새로운 센서 기술과 함께 도입됩니다.', 
      date: '2025.01.19',
      summary: '자율주행 안전성 획기적 개선으로 상용화 앞당겨',
      keyPoints: ['사고율 90% 감소', '악천후 대응 강화', '도심 주행 정확도 향상'],
      impact: '2025년 하반기 상용 서비스 시작 예정',
      technology: 'LiDAR, Computer Vision, 딥러닝'
    },
    { 
      id: 3, 
      companyId: 7, 
      title: '블록체인 기반 AI 결제 시스템', 
      content: '금융 AI가 블록체인과 결합하여 더욱 안전한 결제 환경을 제공합니다.', 
      date: '2025.01.18',
      summary: 'AI + 블록체인 융합으로 결제 보안 혁신',
      keyPoints: ['해킹 불가능한 결제', '수수료 50% 절감', '즉시 결제 완료'],
      impact: '전 세계 금융기관에서 도입 검토 중',
      technology: '블록체인, 스마트계약, AI 검증'
    },
    { 
      id: 4, 
      companyId: 10, 
      title: '환경 AI 모니터링', 
      content: '환경 오염 실시간 모니터링 AI 시스템이 도시 전역에 도입됩니다.', 
      date: '2025.01.17',
      summary: 'AI로 환경오염 실시간 감시 및 예측',
      keyPoints: ['미세먼지 예측 정확도 98%', '오염원 자동 탐지', '시민 건강 알림'],
      impact: '스마트시티 환경관리의 새로운 표준',
      technology: 'IoT 센서, 위성 데이터, 예측 알고리즘'
    },
    { 
      id: 5, 
      companyId: 1, 
      title: 'ChatGPT 신기능 업데이트', 
      content: 'OpenAI가 새로운 멀티모달 기능을 발표했습니다. 이번 업데이트로 더욱 향상된 AI 경험을 제공합니다.', 
      date: '2025.01.16',
      summary: '텍스트, 이미지, 음성을 한번에 처리하는 GPT',
      keyPoints: ['멀티모달 통합 처리', '응답 속도 3배 향상', '창의성 지수 40% 증가'],
      impact: 'AI 어시스턴트 시장의 게임 체인저',
      technology: 'Transformer, 멀티모달 학습, GPT-5'
    },
    { 
      id: 6, 
      companyId: 7, 
      title: 'AI 투자 자문 서비스', 
      content: '개인 맞춤형 AI 투자 자문이 일반 투자자들에게 확대 제공됩니다.', 
      date: '2025.01.15',
      summary: '개인 투자자도 AI 자문으로 수익률 향상',
      keyPoints: ['수익률 평균 15% 향상', '위험도 맞춤 포트폴리오', '24시간 시장 분석'],
      impact: '투자 민주화와 수익 격차 해소',
      technology: '강화학습, 시장 예측, 리스크 모델링'
    },
    { 
      id: 7, 
      companyId: 5, 
      title: '음성 인식 AI 개선', 
      content: '다국어 음성 인식 성능이 대폭 개선되어 실시간 번역이 가능해졌습니다.', 
      date: '2025.01.14',
      summary: '100개 언어 실시간 번역으로 언어 장벽 해소',
      keyPoints: ['100개 언어 지원', '방언 인식률 95%', '실시간 번역 지연 0.1초'],
      impact: '글로벌 비즈니스 및 여행 혁신',
      technology: '음성인식, 자연어처리, 실시간 번역'
    },
    { 
      id: 8, 
      companyId: 2, 
      title: 'AI 이미지 생성 기술 혁신', 
      content: '새로운 이미지 생성 알고리즘이 개발되어 더욱 사실적인 결과물을 만들어냅니다.', 
      date: '2025.01.13',
      summary: '실사와 구별 불가능한 AI 생성 이미지',
      keyPoints: ['실사 구별률 99.9%', '생성 시간 10배 단축', '저작권 문제 해결'],
      impact: '창작 산업과 마케팅 분야 혁신',
      technology: 'Diffusion Model, GAN, 고해상도 생성'
    },
    { 
      id: 9, 
      companyId: 7, 
      title: '대화형 AI 금융 상담', 
      content: '24시간 AI 금융 상담 서비스가 모든 고객에게 제공됩니다.', 
      date: '2025.01.12',
      summary: '24시간 AI 상담사로 금융 서비스 혁신',
      keyPoints: ['상담 만족도 95%', '대기시간 제로', '개인별 맞춤 상품 추천'],
      impact: '금융 접근성 향상과 비용 절감',
      technology: '대화형 AI, 금융 지식베이스, 감정 인식'
    },
    { 
      id: 10, 
      companyId: 9, 
      title: '농업 AI 작물 관리', 
      content: 'AI를 활용한 스마트 농업 시스템으로 작물 수확량이 30% 증가했습니다.', 
      date: '2025.01.11',
      summary: '스마트팜 AI로 농업 생산성 혁신',
      keyPoints: ['수확량 30% 증가', '물 사용량 40% 절약', '농약 사용 50% 감소'],
      impact: '지속가능한 농업과 식량 안보 강화',
      technology: '드론 모니터링, 작물 생육 예측, 자동 관개'
    },
    { 
      id: 11, 
      companyId: 8, 
      title: '교육 AI 맞춤형 학습', 
      content: '개인별 학습 패턴을 분석하여 맞춤형 교육 콘텐츠를 제공합니다.', 
      date: '2025.01.10',
      summary: '개인 맞춤 AI 튜터로 학습 효과 극대화',
      keyPoints: ['학습 효과 50% 향상', '개별 진도 관리', '약점 자동 보완'],
      impact: '교육 격차 해소와 학습 민주화',
      technology: '적응형 학습, 학습 분석, 개인화 알고리즘'
    },
    { 
      id: 12, 
      companyId: 4, 
      title: '의료 AI 진단 정확도 향상', 
      content: '의료 분야에서 AI 진단 시스템의 정확도가 95%까지 향상되었습니다.', 
      date: '2025.01.09',
      summary: '의료진보다 정확한 AI 진단으로 생명 구하기',
      keyPoints: ['진단 정확도 95%', '조기 발견률 80% 향상', '오진율 90% 감소'],
      impact: '의료 서비스 질 향상과 생명 구조',
      technology: '의료 영상 분석, 딥러닝 진단, 패턴 인식'
    },
    { 
      id: 13, 
      companyId: 7, 
      title: 'AI 신용평가 시스템 도입', 
      content: '더욱 정확하고 공정한 AI 기반 신용평가 시스템이 도입됩니다.', 
      date: '2025.01.08',
      summary: '공정하고 정확한 AI 신용평가로 금융 포용성 확대',
      keyPoints: ['평가 정확도 20% 향상', '편견 없는 공정 평가', '신용 접근성 확대'],
      impact: '금융 소외계층의 신용 기회 확대',
      technology: '머신러닝, 대안 데이터 분석, 공정성 알고리즘'
    },
    { 
      id: 14, 
      companyId: 6, 
      title: '게임 AI NPC 지능 향상', 
      content: '게임 내 NPC들이 더욱 자연스러운 대화와 행동을 보여줍니다.', 
      date: '2025.01.07',
      summary: '현실과 구별 안되는 똑똑한 게임 캐릭터',
      keyPoints: ['자연스러운 대화', '학습하는 NPC', '플레이어 적응형 AI'],
      impact: '게임 몰입도와 재미 혁신적 향상',
      technology: '대화형 AI, 행동 학습, 게임 AI'
    },
    { 
      id: 15, 
      companyId: 3, 
      title: '자율주행 AI 도심 테스트', 
      content: '도심에서의 자율주행 AI 테스트가 성공적으로 완료되었습니다.', 
      date: '2025.01.06',
      summary: '복잡한 도심에서도 완벽한 자율주행 성공',
      keyPoints: ['도심 주행 성공률 99%', '복잡한 교차로 완벽 처리', '보행자 안전 보장'],
      impact: '도심 자율주행 상용화 현실화',
      technology: '도심 주행 AI, 실시간 의사결정, 안전 시스템'
    },
  ];

  // 팟캐스트 아카이브 데이터 (샘플)
  const podcastData = [
    {
      id: 1,
      date: '25.09.10 수',
      title: '한 줄 요약',
      content: 'AI 금융 혁신과 자율주행 기술의 최신 동향',
      description: '오늘의 주요 AI 뉴스를 한 줄로 요약해드립니다.',
      duration: '15분 32초',
      isNew: true
    },
    {
      id: 2,
      date: '25.09.09 화',
      title: '한 줄 요약',
      content: '의료 AI 진단 시스템의 정확도 향상 소식',
      description: '의료 분야 AI 기술의 혁신적 발전을 다룹니다.',
      duration: '18분 45초',
      isNew: false
    },
    {
      id: 3,
      date: '25.09.08 월',
      title: '한 줄 요약',
      content: '교육 AI와 농업 스마트팜 기술 발전',
      description: '교육과 농업 분야의 AI 활용 사례를 소개합니다.',
      duration: '16분 28초',
      isNew: false
    },
    {
      id: 4,
      date: '25.09.07 일',
      title: '한 줄 요약',
      content: '게임 AI NPC와 음성 인식 기술 개선',
      description: '게임과 음성 인식 분야의 최신 AI 기술을 다룹니다.',
      duration: '14분 15초',
      isNew: false
    },
    {
      id: 5,
      date: '25.09.06 토',
      title: '한 줄 요약',
      content: '블록체인 AI 결제와 환경 모니터링 시스템',
      description: '블록체인과 환경 분야 AI 기술의 융합을 소개합니다.',
      duration: '17분 52초',
      isNew: false
    },
    {
      id: 6,
      date: '25.09.05 금',
      title: '한 줄 요약',
      content: 'ChatGPT 멀티모달 업데이트와 이미지 생성 AI',
      description: '대화형 AI와 창작 AI의 최신 발전상을 다룹니다.',
      duration: '19분 33초',
      isNew: false
    },
    {
      id: 7,
      date: '25.09.04 목',
      title: '한 줄 요약',
      content: 'AI 투자 자문과 신용평가 시스템 도입',
      description: '금융 AI 서비스의 확산과 그 영향을 분석합니다.',
      duration: '16분 07초',
      isNew: false
    },
    {
      id: 8,
      date: '25.09.03 수',
      title: '한 줄 요약',
      content: '자율주행 도심 테스트와 보안 강화 기술',
      description: '자율주행과 보안 분야 AI 기술의 현재와 미래를 조망합니다.',
      duration: '15분 41초',
      isNew: false
    }
  ];

  // 필터링된 기업 목록
  const getFilteredCompanies = () => {
    switch (filterType) {
      case 'subscribed':
        return companies.filter(company => subscribedCompanies.includes(company.id));
      case 'unsubscribed':
        return companies.filter(company => !subscribedCompanies.includes(company.id));
      default:
        return companies;
    }
  };

  // 구독한 기업의 뉴스만 필터링 (설정창용)
  const getSubscribedNews = () => {
    return aiNewsData.filter(news => subscribedCompanies.includes(news.companyId));
  };

  // 홈 화면용 최신 AI 뉴스 (구독 상태와 상관없이 모든 뉴스, 날짜순 정렬)
  const getAllLatestNews = () => {
    return aiNewsData.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  };

  // 최신 AI 뉴스 (날짜순 정렬, 필터 적용) - 구독 화면용
  const getLatestNews = () => {
    let filteredNews = aiNewsData;
    
    // 필터 타입에 따라 뉴스 필터링
    switch (filterType) {
      case 'subscribed':
        filteredNews = aiNewsData.filter(news => subscribedCompanies.includes(news.companyId));
        break;
      case 'unsubscribed':
        filteredNews = aiNewsData.filter(news => !subscribedCompanies.includes(news.companyId));
        break;
      default:
        filteredNews = aiNewsData;
    }
    
    return filteredNews.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  };

  // 특정 기업의 뉴스만 가져오기 (날짜순 정렬)
  const getCompanyNews = (companyId: number) => {
    return aiNewsData
      .filter(news => news.companyId === companyId)
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  };

  // 검색된 팟캐스트 가져오기
  const getFilteredPodcasts = () => {
    if (!searchText.trim()) {
      return podcastData;
    }
    return podcastData.filter(podcast => 
      podcast.content.toLowerCase().includes(searchText.toLowerCase()) ||
      podcast.description.toLowerCase().includes(searchText.toLowerCase()) ||
      podcast.date.includes(searchText)
    );
  };

  // 기업 뉴스 모달 열기
  const openCompanyNewsModal = (companyId: number) => {
    setSelectedCompanyId(companyId);
    setCompanyNewsModal(true);
  };

  // 뉴스 상세 모달 열기
  const openNewsDetailModal = (newsId: number, fromCompany = false) => {
    console.log('뉴스 상세 모달 열기:', newsId, '기업모달에서:', fromCompany);
    setSelectedNewsId(newsId);
    setFromCompanyModal(fromCompany);
    setNewsDetailModal(true);
  };

  // 팟캐스트 플레이어 모달 열기
  const openPodcastPlayer = (podcastId: number) => {
    console.log('팟캐스트 플레이어 열기:', podcastId);
    setSelectedPodcastId(podcastId);
    setPodcastPlayerModal(true);
    
    // 선택된 팟캐스트의 실제 재생 시간 설정
    const podcast = podcastData.find(p => p.id === podcastId);
    if (podcast) {
      // duration을 파싱해서 초 단위로 변환
      const [minutes, seconds] = podcast.duration.replace(/[분초]/g, '').split(' ').map(Number);
      setTotalTime(minutes * 60 + seconds);
    } else {
      setTotalTime(15 * 60 + 32); // 기본값
    }
    
    setCurrentTime(0);
    setIsPlaying(false);
    
    // 기존 타이머가 있으면 정리
    if (playbackTimer) {
      clearInterval(playbackTimer);
      setPlaybackTimer(null);
    }
  };

  // 재생/일시정지 토글
  const togglePlayback = () => {
    if (isPlaying) {
      // 일시정지
      if (playbackTimer) {
        clearInterval(playbackTimer);
        setPlaybackTimer(null);
      }
      setIsPlaying(false);
    } else {
      // 재생 시작
      setIsPlaying(true);
      const timer = setInterval(() => {
        setCurrentTime(prevTime => {
          if (prevTime >= totalTime) {
            // 재생 완료
            clearInterval(timer);
            setPlaybackTimer(null);
            setIsPlaying(false);
            return totalTime;
          }
          return prevTime + 1;
        });
      }, 1000);
      setPlaybackTimer(timer);
    }
  };

  // 되감기 (15초)
  const rewind = () => {
    setCurrentTime(prevTime => Math.max(0, prevTime - 15));
  };

  // 빨리감기 (15초)
  const fastForward = () => {
    setCurrentTime(prevTime => Math.min(totalTime, prevTime + 15));
  };

  // 진행 바 클릭으로 시간 이동
  const seekTo = (percentage: number) => {
    const newTime = Math.floor(totalTime * percentage);
    setCurrentTime(newTime);
  };

  // 플레이어 모달 닫기
  const closePodcastPlayer = () => {
    if (playbackTimer) {
      clearInterval(playbackTimer);
      setPlaybackTimer(null);
    }
    setIsPlaying(false);
    setPodcastPlayerModal(false);
    setSelectedPodcastId(0);
    setCurrentTime(0);
    setTotalTime(0);
  };

  // 공통 팟캐스트 플레이어 모달 렌더러 (어느 화면에서나 열리도록 각 화면 JSX에 포함)
  // 뉴스 상세 모달 렌더링 (공통)
  const renderNewsDetailModal = () => (
    <Modal
      animationType="slide"
      transparent={true}
      visible={newsDetailModal}
      onRequestClose={() => setNewsDetailModal(false)}
    >
      <View style={styles.newsDetailOverlay}>
        <View style={styles.newsDetailContent}>
          {selectedNewsId > 0 && (() => {
            const news = aiNewsData.find(n => n.id === selectedNewsId);
            const company = companies.find(c => c.id === news?.companyId);
            console.log('뉴스 상세 모달 - selectedNewsId:', selectedNewsId, 'news:', news);
            if (!news) return <Text>뉴스를 찾을 수 없습니다.</Text>;
            
            return (
              <>
                <View style={styles.newsDetailHeader}>
                  <View style={styles.newsDetailTitleContainer}>
                    <TouchableOpacity 
                      style={[
                        styles.companyIconMedium, 
                        { backgroundColor: company?.color }
                      ]}
                      onPress={() => {
                        setNewsDetailModal(false);
                        setSelectedCompanyId(news.companyId);
                        setCompanyNewsModal(true);
                        setFromCompanyModal(false);
                      }}
                    >
                      <Text style={styles.companyTextMedium}>{news.companyId}</Text>
                    </TouchableOpacity>
                    <View style={styles.newsDetailTitleText}>
                      <Text style={styles.newsDetailCompany}>{company?.name}</Text>
                      <Text style={styles.newsDetailDate}>{news.date}</Text>
                    </View>
                  </View>
                  <TouchableOpacity 
                    style={styles.modalCloseButton}
                    onPress={() => {
                      setNewsDetailModal(false);
                      if (fromCompanyModal) {
                        setCompanyNewsModal(true);
                      }
                    }}
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
              </>
            );
          })()}
        </View>
      </View>
    </Modal>
  );

  // 기업 뉴스 모달 렌더링 (공통)
  const renderCompanyNewsModal = () => (
    <Modal
      animationType="slide"
      transparent={true}
      visible={companyNewsModal}
      onRequestClose={() => setCompanyNewsModal(false)}
    >
      <View style={styles.companyModalOverlay}>
        <View style={styles.companyModalContent}>
          {selectedCompanyId > 0 && (
            <>
              <View style={styles.companyModalHeader}>
                <View style={styles.companyModalTitleContainer}>
                  <View style={[
                    styles.companyIconMedium, 
                    { backgroundColor: companies.find(c => c.id === selectedCompanyId)?.color }
                  ]}>
                    <Text style={styles.companyTextMedium}>{selectedCompanyId}</Text>
                  </View>
                  <Text style={styles.companyModalTitle}>
                    {companies.find(c => c.id === selectedCompanyId)?.name} 뉴스
                  </Text>
                </View>
                <TouchableOpacity 
                  style={styles.modalCloseButton}
                  onPress={() => setCompanyNewsModal(false)}
                >
                  <Text style={styles.modalCloseText}>✕</Text>
                </TouchableOpacity>
              </View>
              
            <FlatList
              data={getCompanyNews(selectedCompanyId)}
              keyExtractor={(item) => item.id.toString()}
              showsVerticalScrollIndicator={false}
              renderItem={({ item }) => (
                <TouchableOpacity 
                  style={styles.companyNewsItem}
                  onPress={() => {
                    setCompanyNewsModal(false);
                    openNewsDetailModal(item.id, true);
                  }}
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
                    subscribedCompanies.includes(selectedCompanyId) && styles.subscribeButtonActive
                  ]}
                  onPress={() => {
                    toggleSubscription(selectedCompanyId);
                  }}
                >
                  <Text style={[
                    styles.subscribeButtonText,
                    subscribedCompanies.includes(selectedCompanyId) && styles.subscribeButtonTextActive
                  ]}>
                    {subscribedCompanies.includes(selectedCompanyId) ? '구독 취소' : '구독하기'}
                  </Text>
                </TouchableOpacity>
              </View>
            </>
          )}
        </View>
      </View>
    </Modal>
  );

  const renderPodcastModal = () => (
    <Modal
      animationType="slide"
      transparent={false}
      visible={podcastPlayerModal}
      onRequestClose={closePodcastPlayer}
    >
      <View style={styles.podcastPlayerContainer}>
        {/* 헤더 */}
        <View style={styles.playerHeader}>
          <TouchableOpacity 
            style={styles.playerBackButton}
            onPress={closePodcastPlayer}
          >
            <Text style={styles.playerBackText}>◀</Text>
          </TouchableOpacity>
          <Text style={styles.playerHeaderTitle}>팟캐스트</Text>
          <View style={styles.playerHeaderSpace} />
        </View>

        {(() => {
          const podcast = podcastData.find(p => p.id === selectedPodcastId);
          if (!podcast) {
            return (
              <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                <Text>팟캐스트를 찾을 수 없습니다.</Text>
              </View>
            );
          }

          const formatTime = (seconds: number) => {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}:${secs.toString().padStart(2, '0')}`;
          };

          return (
            <>
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
                      seekTo(Math.max(0, Math.min(1, percentage)));
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
                  <TouchableOpacity style={styles.controlButton} onPress={closePodcastPlayer}>
                    <Text style={styles.controlButtonText}>✕</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.controlButton} onPress={rewind}>
                    <Text style={styles.controlButtonText}>⏪</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.playPauseButton} onPress={togglePlayback}>
                    <Text style={styles.playPauseText}>{isPlaying ? '⏸' : '▶'}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.controlButton} onPress={fastForward}>
                    <Text style={styles.controlButtonText}>⏩</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={styles.controlButton}
                    onPress={() => {
                      setCurrentTime(0);
                      setIsPlaying(false);
                      if (playbackTimer) {
                        clearInterval(playbackTimer);
                        setPlaybackTimer(null);
                      }
                    }}
                  >
                    <Text style={styles.controlButtonText}>🔁</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </>
          );
        })()}
      </View>
    </Modal>
  );

  const handleLogin = () => {
    // 로그인 로직 구현
    console.log('로그인 시도:', { email, password });
    setLoginModalVisible(false);
    setEmail('');
    setPassword('');
    setIsLoggedIn(true); // 로그인 성공 시 홈 화면으로 이동
  };

  const handleGoogleLogin = () => {
    console.log('Google 로그인 시도');
    setLoginModalVisible(false);
    setIsLoggedIn(true); // Google 로그인 성공 시 홈 화면으로 이동
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setShowAlarmSettings(false);
    setCurrentScreen('home');
    setSelectedDays([]);
    setAlarmTimes({});
    setSubscribedCompanies([]);
  };

  const showToastMessage = (message: string) => {
    // 기존 타이머가 있으면 취소
    if (toastTimer) {
      clearTimeout(toastTimer);
    }
    
    setToastMessage(message);
    setShowToast(true);
    
    // 새로운 타이머 설정 (1초 후 사라짐)
    const newTimer = setTimeout(() => {
      setShowToast(false);
      setToastTimer(null);
    }, 1000);
    
    setToastTimer(newTimer);
  };

  const toggleSubscription = (companyId: number) => {
    const isSubscribed = subscribedCompanies.includes(companyId);
    const companyName = companies.find(c => c.id === companyId)?.name || `기업 ${companyId}`;
    
    if (isSubscribed) {
      // 구독 취소
      setSubscribedCompanies(subscribedCompanies.filter(id => id !== companyId));
      showToastMessage(`${companyName} 구독이 취소되었습니다`);
      console.log(`구독 취소: 기업 ${companyId}`, {
        companyId,
        action: 'unsubscribe',
        timestamp: new Date().toISOString(),
        subscribedCompanies: subscribedCompanies.filter(id => id !== companyId)
      });
    } else {
      // 구독
      setSubscribedCompanies([...subscribedCompanies, companyId]);
      showToastMessage(`${companyName}이 구독되었습니다`);
      console.log(`구독: 기업 ${companyId}`, {
        companyId,
        action: 'subscribe',
        timestamp: new Date().toISOString(),
        subscribedCompanies: [...subscribedCompanies, companyId]
      });
    }
  };

  const toggleDay = (day: string) => {
    if (selectedDays.includes(day)) {
      setSelectedDays(selectedDays.filter(d => d !== day));
      const newAlarmTimes = { ...alarmTimes };
      delete newAlarmTimes[day];
      setAlarmTimes(newAlarmTimes);
    } else {
      setSelectedDays([...selectedDays, day]);
      setAlarmTimes({...alarmTimes, [day]: '07:30'});
    }
  };

  const handleTimeChange = (day: string, time: string) => {
    setAlarmTimes({...alarmTimes, [day]: time});
  };

  const openTimePicker = (day: string) => {
    setSelectedDayForTime(day);
    const currentTime = alarmTimes[day] || '07:30';
    const [hour, minute] = currentTime.split(':').map(Number);
    setSelectedHour(hour);
    setSelectedMinute(minute);
    setTimePickerVisible(true);
  };

  const confirmTimeSelection = () => {
    const timeString = `${selectedHour.toString().padStart(2, '0')}:${selectedMinute.toString().padStart(2, '0')}`;
    handleTimeChange(selectedDayForTime, timeString);
    setTimePickerVisible(false);
  };

  const cancelTimeSelection = () => {
    setTimePickerVisible(false);
  };

  const handleAlarmConfirm = () => {
    console.log('알림 설정 완료:', { selectedDays, alarmTimes });
    setShowAlarmSettings(false);
    // 여기서 다음 화면으로 이동하거나 설정 저장
  };

  // 알림 설정 화면 표시
  if (showAlarmSettings) {
    return (
      <View style={styles.alarmContainer}>
        <View style={styles.alarmHeader}>
          <TouchableOpacity 
            style={styles.backButton}
            onPress={() => setShowAlarmSettings(false)}
          >
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>
          <Text style={styles.alarmTitle}>알림 시간 설정</Text>
          <View style={styles.placeholder} />
        </View>
        
        <ScrollView style={styles.alarmContent}>
          <View style={styles.alarmCard}>
            <Text style={styles.sectionTitle}>희망 요일</Text>
            <View style={styles.daysContainer}>
              {days.map((day, index) => (
                <TouchableOpacity
                  key={day}
                  style={[
                    styles.dayButton,
                    selectedDays.includes(day) && styles.dayButtonSelected
                  ]}
                  onPress={() => toggleDay(day)}
                >
                  <Text style={[
                    styles.dayButtonText,
                    selectedDays.includes(day) && styles.dayButtonTextSelected
                  ]}>
                    {day}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            
            <View style={styles.timeSection}>
              <Text style={styles.sectionTitle}>예약 시간</Text>
              {selectedDays.map((day) => (
                <View key={day} style={styles.timeItem}>
                  <Text style={styles.timeLabel}>{dayNames[days.indexOf(day)]}</Text>
                  <View style={styles.timeSliderContainer}>
                    <Text style={styles.timeDisplay}>{alarmTimes[day] || '07:30'}</Text>
                    <TouchableOpacity 
                      style={styles.timeButton}
                      onPress={() => openTimePicker(day)}
                    >
                      <Text style={styles.timeButtonText}>시간 변경</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))}
            </View>
            
            <TouchableOpacity 
              style={styles.confirmButton}
              onPress={handleAlarmConfirm}
            >
              <Text style={styles.confirmButtonText}>확인</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
        
        {/* 시간 선택 모달 */}
        <Modal
          animationType="slide"
          transparent={true}
          visible={timePickerVisible}
          onRequestClose={cancelTimeSelection}
        >
          <View style={styles.timePickerOverlay}>
            <View style={styles.timePickerModal}>
              <Text style={styles.timePickerTitle}>
                {dayNames[days.indexOf(selectedDayForTime)]} 시간 설정
              </Text>
              
              <View style={styles.timePickerContent}>
                <View style={styles.timePickerColumn}>
                  <Text style={styles.timePickerLabel}>시간</Text>
                  <ScrollView style={styles.timePickerScroll} showsVerticalScrollIndicator={false}>
                    {hours.map((hour) => (
                      <TouchableOpacity
                        key={hour}
                        style={[
                          styles.timePickerItem,
                          selectedHour === hour && styles.timePickerItemSelected
                        ]}
                        onPress={() => setSelectedHour(hour)}
                      >
                        <Text style={[
                          styles.timePickerItemText,
                          selectedHour === hour && styles.timePickerItemTextSelected
                        ]}>
                          {hour.toString().padStart(2, '0')}시
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                </View>
                
                <View style={styles.timePickerColumn}>
                  <Text style={styles.timePickerLabel}>분</Text>
                  <ScrollView style={styles.timePickerScroll} showsVerticalScrollIndicator={false}>
                    {minutes.map((minute) => (
                      <TouchableOpacity
                        key={minute}
                        style={[
                          styles.timePickerItem,
                          selectedMinute === minute && styles.timePickerItemSelected
                        ]}
                        onPress={() => setSelectedMinute(minute)}
                      >
                        <Text style={[
                          styles.timePickerItemText,
                          selectedMinute === minute && styles.timePickerItemTextSelected
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
                  onPress={cancelTimeSelection}
                >
                  <Text style={styles.timePickerCancelText}>취소</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={styles.timePickerConfirmButton}
                  onPress={confirmTimeSelection}
                >
                  <Text style={styles.timePickerConfirmText}>확인</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
        
        <StatusBar style="auto" />
      </View>
    );
  }

  // 로그인된 상태면 화면 표시
  if (isLoggedIn) {
    // 홈 화면
    if (currentScreen === 'home') {
      return (
        <View style={styles.homeContainer}>
          {/* 상단 헤더 */}
          <View style={styles.homeHeader}>
            <Text style={styles.appName}>AI 정보 센터</Text>
            <View style={styles.headerIcons}>
              <TouchableOpacity style={styles.headerIcon}>
                <Text style={styles.headerIconText}>🔔</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.headerIcon}>
                <Text style={styles.headerIconText}>🔍</Text>
              </TouchableOpacity>
            </View>
          </View>
          
          {/* 홈: 구독 섹션 이동 안내 */}
          <View style={{ paddingHorizontal: 20, paddingTop: 20 }}>
            <Text style={{ fontSize: 16, color: '#666' }}>
              기업 구독 하단 탭의 ‘구독’에서 관리할 수 있어요.
            </Text>
          </View>
           
           {/* AI 뉴스 섹션 */}
           <View style={styles.newsSection}>
             <Text style={styles.newsSectionTitle}>최신 AI 소식</Text>
             <FlatList
               data={getAllLatestNews()}
               showsVerticalScrollIndicator={false}
               keyExtractor={(item) => item.id.toString()}
               renderItem={({ item }) => {
                 const company = companies.find(c => c.id === item.companyId);
                 return (
                   <TouchableOpacity 
                     style={styles.newsCard}
                     onPress={() => openNewsDetailModal(item.id)}
                   >
                     <View style={styles.newsHeader}>
                       <TouchableOpacity 
                         style={[styles.companyIconSmall, { backgroundColor: company?.color }]}
                         onPress={(e) => {
                           e.stopPropagation();
                           openCompanyNewsModal(item.companyId);
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
           
           {/* 하단 네비게이션 */}
          <View style={styles.bottomNav}>
            <TouchableOpacity 
              style={[styles.navItem, styles.navItemActive]}
              onPress={() => setCurrentScreen('home')}
            >
              <Text style={[styles.navIcon, styles.navIconActive]}>🏠</Text>
              <Text style={[styles.navText, styles.navTextActive]}>홈</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.navItem}>
              <Text style={styles.navIcon}>📰</Text>
              <Text style={styles.navText}>뉴스레터</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('archive')}
            >
              <Text style={styles.navIcon}>📦</Text>
              <Text style={styles.navText}>아카이브</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('subscribe')}
            >
              <Text style={styles.navIcon}>❤️</Text>
              <Text style={styles.navText}>구독</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('settings')}
            >
              <Text style={styles.navIcon}>👤</Text>
              <Text style={styles.navText}>마이</Text>
            </TouchableOpacity>
          </View>
          
          {/* 토스트 메시지 */}
          {showToast && (
            <View style={styles.toastContainer}>
              <View style={styles.toastMessage}>
                <Text style={styles.toastText}>{toastMessage}</Text>
              </View>
            </View>
          )}
          
          {/* 공통 모달들 */}
          {renderCompanyNewsModal()}
          {renderNewsDetailModal()}
          {renderPodcastModal()}

          <StatusBar style="auto" />
        </View>
      );
    }
    
    // 아카이브 화면
    if (currentScreen === 'archive') {
      return (
        <View style={styles.archiveContainer}>
          {/* 아카이브 헤더 */}
          <View style={styles.archiveHeader}>
            <Text style={styles.archiveTitle}>아카이브</Text>
            <TouchableOpacity style={styles.searchIcon}>
              <Text style={styles.searchIconText}>🔍</Text>
            </TouchableOpacity>
          </View>
          
          {/* 검색 바 */}
          <View style={styles.searchContainer}>
            <TextInput
              style={styles.searchInput}
              placeholder="팟캐스트 검색..."
              value={searchText}
              onChangeText={setSearchText}
              placeholderTextColor="#999"
            />
          </View>
          
          {/* 팟캐스트 목록 */}
          <FlatList
            data={getFilteredPodcasts()}
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
                <Text style={styles.podcastDescription} numberOfLines={2}>
                  {item.description}
                </Text>
                <View style={styles.podcastFooter}>
                  <TouchableOpacity 
                    style={styles.playButton}
                    onPress={() => openPodcastPlayer(item.id)}
                  >
                    <Text style={styles.playButtonText}>팟캐스트 재생</Text>
                  </TouchableOpacity>
                  <Text style={styles.podcastDuration}>{item.duration}</Text>
                </View>
              </View>
            )}
            contentContainerStyle={styles.podcastList}
          />
          
          {/* 하단 네비게이션 */}
          <View style={styles.bottomNav}>
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('home')}
            >
              <Text style={styles.navIcon}>🏠</Text>
              <Text style={styles.navText}>홈</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.navItem}>
              <Text style={styles.navIcon}>📰</Text>
              <Text style={styles.navText}>뉴스레터</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.navItem, styles.navItemActive]}
              onPress={() => setCurrentScreen('archive')}
            >
              <Text style={[styles.navIcon, styles.navIconActive]}>📦</Text>
              <Text style={[styles.navText, styles.navTextActive]}>아카이브</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('subscribe')}
            >
              <Text style={styles.navIcon}>❤️</Text>
              <Text style={styles.navText}>구독</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('settings')}
            >
              <Text style={styles.navIcon}>👤</Text>
              <Text style={styles.navText}>마이</Text>
            </TouchableOpacity>
          </View>
          
          {/* 공통 모달들 */}
          {renderCompanyNewsModal()}
          {renderNewsDetailModal()}
          {renderPodcastModal()}

          <StatusBar style="auto" />
        </View>
      );
    }

    // 구독 화면 (기업 아이콘 + 필터 + 최신 소식 섹션)
    if (currentScreen === 'subscribe') {
      return (
        <View style={styles.homeContainer}>
          {/* 상단 헤더 */}
          <View style={styles.homeHeader}>
            <Text style={styles.appName}>구독 관리</Text>
            <View style={styles.headerIcons}>
              <TouchableOpacity style={styles.headerIcon}>
                <Text style={styles.headerIconText}>🔔</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.headerIcon}>
                <Text style={styles.headerIconText}>🔍</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* 기업 아이콘 + 필터 */}
          <View style={styles.companiesSection}>
            <FlatList
              data={getFilteredCompanies()}
              horizontal
              showsHorizontalScrollIndicator={false}
              keyExtractor={(item) => item.id.toString()}
              renderItem={({ item }) => {
                const isSubscribed = subscribedCompanies.includes(item.id);
                return (
                  <TouchableOpacity 
                    style={styles.companyIcon}
                    onPress={() => toggleSubscription(item.id)}
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
                onPress={() => setFilterType('all')}
              >
                <Text style={[styles.filterButtonText, filterType === 'all' && styles.filterButtonTextActive]}>전체</Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.filterButton, filterType === 'subscribed' && styles.filterButtonActive]}
                onPress={() => setFilterType('subscribed')}
              >
                <Text style={[styles.filterButtonText, filterType === 'subscribed' && styles.filterButtonTextActive]}>구독</Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.filterButton, filterType === 'unsubscribed' && styles.filterButtonActive]}
                onPress={() => setFilterType('unsubscribed')}
              >
                <Text style={[styles.filterButtonText, filterType === 'unsubscribed' && styles.filterButtonTextActive]}>미구독</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* 구독 화면에도 최신 소식 리스트 (필터 적용) */}
          <View style={styles.newsSection}>
            <Text style={styles.newsSectionTitle}>최신 AI 소식</Text>
            <FlatList
              data={getLatestNews()}
              showsVerticalScrollIndicator={false}
              keyExtractor={(item) => item.id.toString()}
              renderItem={({ item }) => {
                const company = companies.find(c => c.id === item.companyId);
                return (
                  <TouchableOpacity style={styles.newsCard} onPress={() => openNewsDetailModal(item.id)}>
                    <View style={styles.newsHeader}>
                      <TouchableOpacity 
                        style={[styles.companyIconSmall, { backgroundColor: company?.color }]}
                        onPress={(e) => { e.stopPropagation(); openCompanyNewsModal(item.companyId); }}
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

          {/* 하단 네비게이션 */}
          <View style={styles.bottomNav}>
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('home')}
            >
              <Text style={styles.navIcon}>🏠</Text>
              <Text style={styles.navText}>홈</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.navItem}>
              <Text style={styles.navIcon}>📰</Text>
              <Text style={styles.navText}>뉴스레터</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('archive')}
            >
              <Text style={styles.navIcon}>📦</Text>
              <Text style={styles.navText}>아카이브</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.navItem, styles.navItemActive]}
              onPress={() => setCurrentScreen('subscribe')}
            >
              <Text style={[styles.navIcon, styles.navIconActive]}>❤️</Text>
              <Text style={[styles.navText, styles.navTextActive]}>구독</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('settings')}
            >
              <Text style={styles.navIcon}>👤</Text>
              <Text style={styles.navText}>마이</Text>
            </TouchableOpacity>
          </View>

          {/* 공통 모달들 */}
          {renderCompanyNewsModal()}
          {renderNewsDetailModal()}
          {renderPodcastModal()}

          <StatusBar style="auto" />
        </View>
      );
    }
    // 설정창
    if (currentScreen === 'settings') {
      return (
        <View style={styles.settingsContainer}>
          <View style={styles.settingsHeader}>
            <TouchableOpacity 
              style={styles.backToHomeButton}
              onPress={() => setCurrentScreen('home')}
            >
              <Text style={styles.backToHomeText}>← 홈으로</Text>
            </TouchableOpacity>
            <Text style={styles.settingsTitle}>설정</Text>
            <View style={styles.placeholder} />
          </View>
          
          <View style={styles.settingsContent}>
            <Text style={styles.settingsMainTitle}>설정 창</Text>
            <Text style={styles.settingsSubtitle}>설정해주세요</Text>
            
            <View style={styles.featureContainer}>
              <TouchableOpacity 
                style={styles.featureButton}
                onPress={() => setShowAlarmSettings(true)}
              >
                <Text style={styles.featureIcon}>⏰</Text>
                <Text style={styles.featureText}>알림 설정</Text>
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.featureButton}>
                <Text style={styles.featureIcon}>📊</Text>
                <Text style={styles.featureText}>AI 트렌드</Text>
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.featureButton}>
                <Text style={styles.featureIcon}>💡</Text>
                <Text style={styles.featureText}>AI 구독 상태</Text>
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.featureButton}>
                <Text style={styles.featureIcon}>🔍</Text>
                <Text style={styles.featureText}>AI 검색</Text>
              </TouchableOpacity>
            </View>
          </View>
          
          {/* 하단 네비게이션 */}
          <View style={styles.bottomNav}>
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('home')}
            >
              <Text style={styles.navIcon}>🏠</Text>
              <Text style={styles.navText}>홈</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.navItem}>
              <Text style={styles.navIcon}>📰</Text>
              <Text style={styles.navText}>뉴스레터</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('archive')}
            >
              <Text style={styles.navIcon}>📦</Text>
              <Text style={styles.navText}>아카이브</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.navItem}
              onPress={() => setCurrentScreen('subscribe')}
            >
              <Text style={styles.navIcon}>❤️</Text>
              <Text style={styles.navText}>구독</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.navItem, styles.navItemActive]}
              onPress={() => setCurrentScreen('settings')}
            >
              <Text style={[styles.navIcon, styles.navIconActive]}>👤</Text>
              <Text style={[styles.navText, styles.navTextActive]}>마이</Text>
            </TouchableOpacity>
          </View>
          
          {/* 공통 모달들 */}
          {renderCompanyNewsModal()}
          {renderNewsDetailModal()}
          {renderPodcastModal()}

          <StatusBar style="auto" />
        </View>
      );
    }
  }

  return (
    <View style={styles.container}>
      <Image 
        source={require('./assets/logo.png')} 
        style={styles.logo}
        resizeMode="contain"
      />
      <Text style={styles.slogan}>세상의 모든 AI 정보를 원하는 정보만</Text>
      <Text style={styles.welcomeText}>반갑습니다</Text>
      
      <TouchableOpacity 
        style={styles.aiButton}
        onPress={() => setLoginModalVisible(true)}
      >
        <Text style={styles.aiButtonText}>AI 정보 받기</Text>
      </TouchableOpacity>

      <Modal
        animationType="slide"
        transparent={true}
        visible={loginModalVisible}
        onRequestClose={() => setLoginModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>로그인</Text>
            
            <TextInput
              style={styles.input}
              placeholder="이메일"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />
            
            <TextInput
              style={styles.input}
              placeholder="비밀번호"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />
            
            <View style={styles.buttonContainer}>
              <TouchableOpacity 
                style={styles.cancelButton}
                onPress={() => setLoginModalVisible(false)}
              >
                <Text style={styles.cancelButtonText}>취소</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.loginButton}
                onPress={handleLogin}
              >
                <Text style={styles.loginButtonText}>로그인</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>또는</Text>
              <View style={styles.dividerLine} />
            </View>

            <TouchableOpacity 
              style={styles.googleButton}
              onPress={handleGoogleLogin}
            >
              <Text style={styles.googleButtonText}>🔍 Google로 로그인</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* 공통 모달들 */}
      {renderCompanyNewsModal()}
      {renderNewsDetailModal()}
      {renderPodcastModal()}

      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 100,
  },
  logo: {
    width: 200,
    height: 200,
    marginBottom: 15,
  },
  slogan: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
    paddingHorizontal: 20,
    lineHeight: 22,
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 50,
  },
  aiButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 40,
    paddingVertical: 15,
    borderRadius: 25,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  aiButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 30,
    width: '80%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30,
    color: '#333',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    fontSize: 16,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  cancelButton: {
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10,
    flex: 1,
    marginRight: 10,
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: '600',
  },
  loginButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10,
    flex: 1,
    marginLeft: 10,
  },
  loginButtonText: {
    color: '#fff',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: '600',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#ddd',
  },
  dividerText: {
    marginHorizontal: 15,
    color: '#666',
    fontSize: 14,
  },
  googleButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  googleButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '600',
  },
  // 홈 화면 스타일
  homeContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  welcomeBackText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  logoutButton: {
    backgroundColor: '#dc3545',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 15,
  },
  logoutButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  homeContent: {
    flex: 1,
    padding: 20,
  },
  homeTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 10,
  },
  homeSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 40,
  },
  featureContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  featureButton: {
    backgroundColor: '#fff',
    width: '48%',
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  featureIcon: {
    fontSize: 30,
    marginBottom: 10,
  },
  featureText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
  },
  // 알림 설정 화면 스타일
  alarmContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  alarmHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  backButton: {
    padding: 10,
  },
  backButtonText: {
    fontSize: 24,
    color: '#007AFF',
  },
  alarmTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  placeholder: {
    width: 44,
  },
  alarmContent: {
    flex: 1,
    padding: 20,
  },
  alarmCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    borderWidth: 2,
    borderColor: '#007AFF',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 20,
  },
  daysContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  dayButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  dayButtonSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  dayButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  dayButtonTextSelected: {
    color: '#fff',
  },
  timeSection: {
    backgroundColor: '#e3f2fd',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
  },
  timeItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#bbdefb',
  },
  timeLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  timeSliderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeDisplay: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
    marginRight: 10,
    minWidth: 50,
  },
  timeButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
  },
  timeButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  confirmButton: {
    backgroundColor: '#e3f2fd',
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  confirmButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: 'bold',
  },
  // 시간 선택 모달 스타일
  timePickerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  timePickerModal: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 20,
    width: '85%',
    maxWidth: 400,
    maxHeight: '70%',
  },
  timePickerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
    color: '#333',
  },
  timePickerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  timePickerColumn: {
    flex: 1,
    marginHorizontal: 10,
  },
  timePickerLabel: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 10,
    color: '#007AFF',
  },
  timePickerScroll: {
    maxHeight: 200,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 10,
  },
  timePickerItem: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    alignItems: 'center',
  },
  timePickerItemSelected: {
    backgroundColor: '#007AFF',
  },
  timePickerItemText: {
    fontSize: 16,
    color: '#333',
  },
  timePickerItemTextSelected: {
    color: '#fff',
    fontWeight: '600',
  },
  timePickerButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  timePickerCancelButton: {
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 10,
    flex: 1,
    marginRight: 10,
  },
  timePickerCancelText: {
    color: '#666',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: '600',
  },
  timePickerConfirmButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 10,
    flex: 1,
    marginLeft: 10,
  },
  timePickerConfirmText: {
    color: '#fff',
    fontSize: 16,
    textAlign: 'center',
    fontWeight: '600',
  },
  // 새로운 홈 화면 스타일
  homeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  appName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  headerIcons: {
    flexDirection: 'row',
  },
  headerIcon: {
    marginLeft: 15,
    padding: 8,
  },
  headerIconText: {
    fontSize: 20,
  },
  companiesSection: {
    flex: 0.4,
    paddingVertical: 10,
  },
  filterSection: {
    
    flexDirection: 'row',
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#f8f9fa',

  },
  filterButton: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    marginHorizontal: 5,
    borderRadius: 20,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  filterButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  filterButtonText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  filterButtonTextActive: {
    color: '#fff',
  },
  homeDividerLine: {
    height: 1,
    backgroundColor: '#e0e0e0',
    marginHorizontal: 20,
    marginVertical: 10,
  },
  // 뉴스 섹션 스타일
  newsSection: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  newsSectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  newsList: {
    paddingBottom: 20,
  },
  newsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#f0f0f0',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  newsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  companyIconSmall: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  companyTextSmall: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  newsHeaderText: {
    flex: 1,
  },
  companyNameSmall: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  newsDate: {
    fontSize: 12,
    color: '#999',
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
    color: '#666',
    lineHeight: 20,
  },
  noNewsContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  noNewsText: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  noNewsSubText: {
    fontSize: 14,
    color: '#999',
  },
  subscribedNewsCard: {
    borderColor: '#007AFF',
    borderWidth: 2,
  },
  subscribedBadge: {
    position: 'absolute',
    top: -3,
    right: -3,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    width: 16,
    height: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  subscribedBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  subscribedCompanyText: {
    color: '#007AFF',
    fontWeight: 'bold',
  },
  // 기업 뉴스 모달 스타일
  companyModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  companyModalContent: {
    backgroundColor: '#fff',
    borderRadius: 20,
    width: '90%',
    maxHeight: '80%',
    paddingBottom: 20,
  },
  companyModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  companyModalTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  companyIconMedium: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  companyTextMedium: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  companyModalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  modalCloseButton: {
    padding: 10,
  },
  modalCloseText: {
    fontSize: 20,
    color: '#666',
  },
  companyNewsList: {
    paddingHorizontal: 20,
  },
  companyNewsItem: {
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f5f5f5',
  },
  companyNewsHeader: {
    marginBottom: 8,
  },
  companyNewsDate: {
    fontSize: 12,
    color: '#999',
    fontWeight: '500',
  },
  companyNewsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
    lineHeight: 22,
  },
  companyNewsContent: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  subscribeButtonContainer: {
    paddingHorizontal: 20,
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  subscribeButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  subscribeButtonActive: {
    backgroundColor: '#ff4757',
  },
  subscribeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  subscribeButtonTextActive: {
    color: '#fff',
  },
  // 뉴스 상세 모달 스타일
  newsDetailOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  newsDetailContent: {
    backgroundColor: '#fff',
    borderRadius: 20,
    width: '95%',
    height: '90%',
    paddingBottom: 20,
    overflow: 'hidden',
  },
  newsDetailHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  newsDetailTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  newsDetailTitleText: {
    marginLeft: 15,
    flex: 1,
  },
  newsDetailCompany: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  newsDetailDate: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  newsDetailScroll: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 10,
  },
  newsDetailTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
    lineHeight: 30,
  },
  newsDetailSummary: {
    fontSize: 16,
    color: '#555',
    lineHeight: 24,
    marginBottom: 25,
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  infoSection: {
    marginBottom: 25,
  },
  infoSectionTitle: {
    fontSize: 18,
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
    fontSize: 15,
    color: '#555',
    lineHeight: 22,
    flex: 1,
  },
  infoText: {
    fontSize: 15,
    color: '#555',
    lineHeight: 22,
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 8,
  },
  // 아카이브 화면 스타일
  archiveContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  archiveHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  archiveTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  searchIcon: {
    padding: 8,
  },
  searchIconText: {
    fontSize: 20,
  },
  searchContainer: {
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#f8f9fa',
  },
  searchInput: {
    backgroundColor: '#fff',
    borderRadius: 10,
    paddingHorizontal: 15,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  podcastList: {
    paddingHorizontal: 20,
    paddingBottom: 100,
  },
  podcastCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 20,
    marginVertical: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  podcastHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  podcastDate: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  newBadge: {
    backgroundColor: '#FF3B30',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  newBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  podcastTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  podcastContent: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
    fontWeight: '600',
  },
  podcastDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 15,
  },
  podcastFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  playButton: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  playButtonText: {
    color: '#333',
    fontSize: 14,
    fontWeight: '500',
  },
  podcastDuration: {
    fontSize: 12,
    color: '#999',
  },
  // 팟캐스트 플레이어 모달 스타일
  podcastPlayerContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  playerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  playerBackButton: {
    padding: 8,
  },
  playerBackText: {
    fontSize: 20,
    color: '#007AFF',
  },
  playerHeaderTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  playerHeaderSpace: {
    width: 36,
  },
  infographicsContainer: {
    flex: 1,
    paddingHorizontal: 20,
    paddingVertical: 20,
    justifyContent: 'center',
  },
  infographicsPlaceholder: {
    backgroundColor: '#f8f9fa',
    borderRadius: 15,
    padding: 30,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderStyle: 'dashed',
  },
  infographicsTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  infographicsSubtitle: {
    fontSize: 18,
    color: '#007AFF',
    marginBottom: 20,
    fontWeight: '600',
  },
  infographicsDescription: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 25,
  },
  infographicsStats: {
    alignItems: 'center',
    marginBottom: 20,
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  statsText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 5,
  },
  statsSubText: {
    fontSize: 12,
    color: '#999',
  },
  pdfNote: {
    fontSize: 12,
    color: '#999',
    fontStyle: 'italic',
  },
  podcastInfo: {
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  podcastPlayerDate: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  podcastPlayerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  podcastPlayerContent: {
    fontSize: 16,
    color: '#555',
    lineHeight: 22,
  },
  audioPlayer: {
    paddingHorizontal: 20,
    paddingVertical: 20,
    backgroundColor: '#f8f9fa',
  },
  progressContainer: {
    marginBottom: 25,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
    position: 'relative',
    marginBottom: 10,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 2,
  },
  progressThumb: {
    position: 'absolute',
    top: -8,
    marginLeft: -10,
    width: 20,
    height: 20,
    backgroundColor: '#007AFF',
    borderRadius: 10,
    borderWidth: 3,
    borderColor: '#fff',
  },
  timeContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  timeText: {
    fontSize: 14,
    color: '#666',
  },
  controlsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 20,
  },
  controlButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  controlButtonText: {
    fontSize: 20,
    color: '#333',
  },
  playPauseButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playPauseText: {
    fontSize: 28,
    color: '#fff',
  },
  companiesList: {
    paddingHorizontal: 10,
  },
  companyIcon: {
    alignItems: 'center',
    marginRight: 10,
    width: 70,
  },
  companyCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  companyText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  companyName: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  subscribedCompanyName: {
    color: '#007AFF',
    fontWeight: '600',
  },
  subscribedIndicator: {
    position: 'absolute',
    top: -5,
    right: -5,
    backgroundColor: '#007AFF',
    borderRadius: 10,
    width: 20,
    height: 20,
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
  bottomNav: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e9ecef',
    paddingVertical: 10,
    paddingHorizontal: 10,
  },
  navItem: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
  },
  navItemActive: {
    // 활성 상태 스타일
  },
  navIcon: {
    fontSize: 20,
    marginBottom: 4,
  },
  navIconActive: {
    // 활성 아이콘 스타일
  },
  navText: {
    fontSize: 12,
    color: '#666',
  },
  navTextActive: {
    color: '#007AFF',
    fontWeight: '600',
  },
  // 설정창 스타일
  settingsContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  settingsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  backToHomeButton: {
    padding: 10,
  },
  backToHomeText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
  settingsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  settingsContent: {
    flex: 1,
    padding: 20,
  },
  settingsMainTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 10,
  },
  settingsSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 40,
  },
  // 토스트 메시지 스타일
  toastContainer: {
    position: 'absolute',
    bottom: 100, // 하단 네비게이션 위에 위치
    left: 0,
    right: 0,
    alignItems: 'center',
    zIndex: 1000,
  },
  toastMessage: {
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
    marginHorizontal: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  toastText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});
