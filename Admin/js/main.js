// Main entry point for the admin page

// Global functions to be accessible from HTML onclick
window.loadDashboard = async () => {
    try {
        const stats = await fetchDashboardStats();
        renderDashboard(stats);
        const recentArticles = await fetchRecentArticles();
        renderRecentArticles(recentArticles);
    } catch (error) {
        console.error("Failed to load dashboard:", error);
    }
};

window.loadTopics = async () => {
    try {
        const topics = await fetchTopics();
        renderTopics(topics);
    } catch (error) {
        console.error("Failed to load topics:", error);
    }
};

window.loadTopicDetails = async (topicId) => {
    try {
        const topic = await fetchTopicDetails(topicId);
        renderTopicDetails(topic);
    } catch (error) {
        console.error("Failed to load topic details:", error);
    }
};

window.logout = () => {
    localStorage.removeItem('admin_token');
    window.location.href = 'login.html';
};


document.addEventListener('DOMContentLoaded', () => {
    // Check for auth token on every page load except login page
    // if (!localStorage.getItem('admin_token')) {
    //     window.location.href = 'login.html';
    //     return; // Stop further execution
    // }

    console.log('Admin page loaded');

    // Set up navigation
    document.querySelector('nav ul li a[href="#dashboard"]').addEventListener('click', (e) => {
        e.preventDefault();
        window.loadDashboard();
    });

    document.querySelector('nav ul li a[href="#topics"]').addEventListener('click', (e) => {
        e.preventDefault();
        window.loadTopics();
    });

    // Initial load
    window.loadDashboard(); 
});
