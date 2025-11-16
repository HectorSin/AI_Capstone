// Functions for rendering data to the UI

function renderDashboard(stats) {
    const content = document.getElementById('content');
    if (!stats) {
        content.innerHTML = '<p>Error loading dashboard data.</p>';
        return;
    }
    content.innerHTML = `
        <h2>Dashboard Overview</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Topics</h3>
                <p>${stats.total_topics}</p>
            </div>
            <div class="stat-card">
                <h3>Total Articles</h3>
                <p>${stats.total_articles}</p>
            </div>
            <div class="stat-card">
                <h3>Total Podcasts</h3>
                <p>${stats.total_podcasts}</p>
            </div>
        </div>
        <h3>Recent Articles</h3>
        <div id="recent-articles-list">Loading recent articles...</div>
    `;
}

function renderRecentArticles(articles) {
    const recentArticlesList = document.getElementById('recent-articles-list');
    if (!recentArticlesList) return;

    if (!articles || articles.length === 0) {
        recentArticlesList.innerHTML = '<p>No recent articles found.</p>';
        return;
    }

    const articleItems = articles.map(article => `
        <div class="article-item">
            <h4>${article.title}</h4>
            <p>${article.summary}</p>
            <small>${new Date(article.created_at).toLocaleDateString()}</small>
        </div>
    `).join('');
    recentArticlesList.innerHTML = `<div class="articles-container">${articleItems}</div>`;
}


function renderTopics(topics) {
    const content = document.getElementById('content');
    if (!topics || topics.length === 0) {
        content.innerHTML = '<h2>Topics</h2><p>No topics found.</p>';
        return;
    }

    let tableRows = topics.map(topic => `
        <tr>
            <td>${topic.name}</td>
            <td>${topic.type}</td>
            <td>${topic.keywords ? topic.keywords.join(', ') : 'N/A'}</td>
            <td><a href="#" onclick="loadTopicDetails('${topic.id}')">View Details</a></td>
        </tr>
    `).join('');

    content.innerHTML = `
        <h2>Topics</h2>
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Keywords</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${tableRows}
            </tbody>
        </table>
    `;
}

function renderTopicDetails(topic) {
    const content = document.getElementById('content');
    if (!topic) {
        content.innerHTML = '<p>Error loading topic details.</p>';
        return;
    }

    content.innerHTML = `
        <h2>Topic: ${topic.name}</h2>
        <p><strong>Type:</strong> ${topic.type}</p>
        <p><strong>Summary:</strong> ${topic.summary || 'N/A'}</p>
        <p><strong>Keywords:</strong> ${topic.keywords ? topic.keywords.join(', ') : 'N/A'}</p>
        <p><strong>Created At:</strong> ${new Date(topic.created_at).toLocaleDateString()}</p>
        <button onclick="loadTopics()">Back to Topics</button>
        <h3>Related Articles</h3>
        <div id="topic-articles-list">Loading related articles...</div>
    `;
}

function renderTopicArticles(articles) {
    const articlesContainer = document.getElementById('topic-articles-list');
    if (!articlesContainer) return;

    if (!articles || articles.length === 0) {
        articlesContainer.innerHTML = '<p>No articles found for this topic.</p>';
        return;
    }

    const articleRows = articles.map(article => `
        <tr>
            <td>${article.title}</td>
            <td>${article.status}</td>
            <td>${article.date ? new Date(article.date).toLocaleDateString() : 'N/A'}</td>
            <td>${new Date(article.created_at).toLocaleDateString()}</td>
            <td>
                ${article.source_url
                    ? `<a href="${article.source_url}" target="_blank">Source</a>`
                    : 'N/A'}
            </td>
        </tr>
    `).join('');

    articlesContainer.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Article Date</th>
                    <th>Created At</th>
                    <th>Source</th>
                </tr>
            </thead>
            <tbody>
                ${articleRows}
            </tbody>
        </table>
    `;
}
