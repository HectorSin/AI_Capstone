// Functions for communicating with the backend API
const API_BASE_URL = '/api/v1/admin';

function getAuthHeaders() {
    const token = localStorage.getItem('admin_token');
    if (!token) {
        window.location.href = 'login.html';
        throw new Error('No authentication token found');
    }
    return {
        'Authorization': `Bearer ${token}`
    };
}

async function handleApiResponse(response) {
    if (response.status === 401) {
        localStorage.removeItem('admin_token');
        window.location.href = 'login.html';
        throw new Error('Unauthorized');
    }
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

async function fetchDashboardStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/stats`, { headers: getAuthHeaders() });
        return handleApiResponse(response);
    } catch (error) {
        console.error('Error fetching dashboard stats:', error);
        return null;
    }
}

async function fetchRecentArticles(limit = 5) {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/recent-articles?limit=${limit}`, { headers: getAuthHeaders() });
        return handleApiResponse(response);
    } catch (error) {
        console.error('Error fetching recent articles:', error);
        return [];
    }
}

async function fetchTopics(skip = 0, limit = 10, name = '') {
    try {
        let url = `${API_BASE_URL}/topics?skip=${skip}&limit=${limit}`;
        if (name) {
            url += `&name=${encodeURIComponent(name)}`;
        }
        const response = await fetch(url, { headers: getAuthHeaders() });
        return handleApiResponse(response);
    } catch (error) {
        console.error('Error fetching topics:', error);
        return [];
    }
}

async function fetchTopicDetails(topicId) {
    try {
        const response = await fetch(`${API_BASE_URL}/topics/${topicId}`, { headers: getAuthHeaders() });
        return handleApiResponse(response);
    } catch (error) {
        console.error(`Error fetching topic details for ${topicId}:`, error);
        return null;
    }
}

async function fetchTopicArticles(topicId, skip = 0, limit = 20) {
    try {
        const response = await fetch(`${API_BASE_URL}/topics/${topicId}/articles?skip=${skip}&limit=${limit}`, { headers: getAuthHeaders() });
        return handleApiResponse(response);
    } catch (error) {
        console.error(`Error fetching articles for topic ${topicId}:`, error);
        return [];
    }
}
