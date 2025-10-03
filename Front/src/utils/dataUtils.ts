import { companies, Company } from '../data/companies';
import { aiNewsData, AINews } from '../data/aiNews';
import { podcastData, Podcast } from '../data/podcasts';

export type FilterType = 'all' | 'subscribed' | 'unsubscribed';

export const getFilteredCompanies = (filterType: FilterType, subscribedCompanies: number[]): Company[] => {
  switch (filterType) {
    case 'subscribed':
      return companies.filter(company => subscribedCompanies.includes(company.id));
    case 'unsubscribed':
      return companies.filter(company => !subscribedCompanies.includes(company.id));
    default:
      return companies;
  }
};

export const getAllLatestNews = (): AINews[] => {
  return aiNewsData.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
};

export const getLatestNews = (filterType: FilterType, subscribedCompanies: number[]): AINews[] => {
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

export const getCompanyNews = (companyId: number): AINews[] => {
  return aiNewsData
    .filter(news => news.companyId === companyId)
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
};

export const getFilteredPodcasts = (searchText: string): Podcast[] => {
  if (!searchText.trim()) {
    return podcastData;
  }
  return podcastData.filter(podcast => 
    podcast.content.toLowerCase().includes(searchText.toLowerCase()) ||
    podcast.description.toLowerCase().includes(searchText.toLowerCase()) ||
    podcast.date.includes(searchText)
  );
};
