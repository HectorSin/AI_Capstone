// Main entry point for the admin page

const DEFAULT_ROUTE = '#/dashboard';

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

window.loadArticles = async () => {
    try {
        const topics = await fetchTopics();
        renderTopics(topics, 'Articles', { showToolbar: false });
    } catch (error) {
        console.error("Failed to load articles:", error);
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

const routes = {
    '#/dashboard': window.loadDashboard,
    '#/topics': window.loadTopics,
    '#/articles': window.loadArticles
};

function setActiveNav(route) {
    document.querySelectorAll('nav ul li a').forEach((link) => {
        if (link.getAttribute('href') === route) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

function handleRouteChange() {
    const currentHash = window.location.hash;

    if (!currentHash) {
        window.location.hash = DEFAULT_ROUTE;
        return;
    }

    const routeHandler = routes[currentHash];
    if (!routeHandler) {
        window.location.hash = DEFAULT_ROUTE;
        return;
    }

    setActiveNav(currentHash);
    routeHandler();
}

window.addEventListener('hashchange', handleRouteChange);

document.addEventListener('DOMContentLoaded', () => {
    // Check for auth token on every page load except login page
    if (!localStorage.getItem('admin_token')) {
        window.location.href = 'login.html';
        return; // Stop further execution
    }

    console.log('Admin page loaded');
    if (!window.location.hash) {
        window.location.hash = DEFAULT_ROUTE;
    }
    handleRouteChange();
});
