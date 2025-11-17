// Functions for communicating with the backend API
// 현재 호스트의 8001 포트 사용 (Nginx를 통해 프록시됨)
const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:8001/api/v1/admin`;

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
        let url = `${API_BASE_URL}/topics/?skip=${skip}&limit=${limit}`;
        if (name) {
            url += `&name=${encodeURIComponent(name)}`;
        }
        console.log('Fetching topics from:', url);
        const response = await fetch(url, { headers: getAuthHeaders() });
        const data = await handleApiResponse(response);
        console.log('Topics response:', data);
        return data;
    } catch (error) {
        console.error('Error fetching topics:', error);
        return [];
    }
}

async function fetchTopicDetails(topicId) {
    try {
        const response = await fetch(`${API_BASE_URL}/topics/${topicId}/`, { headers: getAuthHeaders() });
        return handleApiResponse(response);
    } catch (error) {
        console.error(`Error fetching topic details for ${topicId}:`, error);
        return null;
    }
}

async function fetchTopicArticles(topicId, skip = 0, limit = 20) {
    try {
        const response = await fetch(`${API_BASE_URL}/topics/${topicId}/articles/?skip=${skip}&limit=${limit}`, { headers: getAuthHeaders() });
        return handleApiResponse(response);
    } catch (error) {
        console.error(`Error fetching articles for topic ${topicId}:`, error);
        return [];
    }
}

async function updateTopic(topicId, topicData) {
    try {
        const headers = getAuthHeaders();
        headers['Content-Type'] = 'application/json';

        const response = await fetch(`${API_BASE_URL}/topics/${topicId}/`, {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify(topicData)
        });
        return handleApiResponse(response);
    } catch (error) {
        console.error(`Error updating topic ${topicId}:`, error);
        throw error;
    }
}

async function uploadTopicImage(topicId, imageFile) {
    try {
        const headers = getAuthHeaders();
        const formData = new FormData();
        formData.append('file', imageFile);

        const response = await fetch(`${API_BASE_URL}/topics/${topicId}/image/`, {
            method: 'POST',
            headers: headers,
            body: formData
        });
        return handleApiResponse(response);
    } catch (error) {
        console.error(`Error uploading image for topic ${topicId}:`, error);
        throw error;
    }
}

async function deleteTopicImage(topicId) {
    try {
        const headers = getAuthHeaders();

        const response = await fetch(`${API_BASE_URL}/topics/${topicId}/image/`, {
            method: 'DELETE',
            headers: headers
        });
        return handleApiResponse(response);
    } catch (error) {
        console.error(`Error deleting image for topic ${topicId}:`, error);
        throw error;
    }
}
