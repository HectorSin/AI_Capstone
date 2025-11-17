// Functions for rendering data to the UI

let selectedTopicId = null;

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


function renderTopics(topics, title = 'Topics', options = {}) {
    const { showToolbar = title === 'Topics' } = options;
    const content = document.getElementById('content');
    if (!topics || topics.length === 0) {
        content.innerHTML = `<h2>${title}</h2><p>No topics found.</p>`;
        return;
    }

    let tableRows = topics.map(topic => `
        <tr class="topic-row" data-topic-id="${topic.id}">
            <td>${topic.name}</td>
            <td>${topic.type}</td>
            <td>${topic.summary || 'N/A'}</td>
            <td>
                ${topic.image_uri
                    ? `<a href="${topic.image_uri}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">View Image</a>`
                    : 'N/A'}
            </td>
            <td>${topic.keywords && topic.keywords.length ? topic.keywords.join(', ') : 'N/A'}</td>
            <td>${topic.created_at ? new Date(topic.created_at).toLocaleDateString() : 'N/A'}</td>
            <td><a href="#" onclick="event.stopPropagation(); loadTopicDetails('${topic.id}'); return false;">View Details</a></td>
        </tr>
    `).join('');

    const toolbarHtml = showToolbar ? `
        <div class="topics-toolbar">
            <button type="button" class="button-success" onclick="handleAddTopic()">추가</button>
            <button type="button" id="topic-edit-btn" class="button-primary" onclick="handleEditTopic()" disabled>수정</button>
            <button type="button" id="topic-delete-btn" class="button-danger" onclick="handleDeleteTopic()" disabled>삭제</button>
        </div>
    ` : '';

    content.innerHTML = `
        <h2>${title}</h2>
        ${toolbarHtml}
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Summary</th>
                    <th>Image</th>
                    <th>Keywords</th>
                    <th>Created</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${tableRows}
            </tbody>
        </table>
    `;
    setupTopicsInteractionsIfNeeded(showToolbar);
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
    // TODO: Fetch and render related articles for this topic
}

function initializeTopicTableInteractions(container) {
    if (!container) {
        return;
    }
    const rows = container.querySelectorAll('tbody tr.topic-row');
    rows.forEach((row) => {
        row.addEventListener('click', () => {
            const topicId = row.dataset.topicId;
            selectedTopicId = selectedTopicId === topicId ? null : topicId;
            updateTopicRowSelection(container);
            updateTopicActionButtons();
        });
    });
    updateTopicActionButtons();
}

function updateTopicRowSelection(container) {
    if (!container) {
        return;
    }
    const rows = container.querySelectorAll('tbody tr.topic-row');
    rows.forEach((row) => {
        row.classList.toggle('selected', row.dataset.topicId === selectedTopicId);
    });
}

function updateTopicActionButtons() {
    const editButton = document.getElementById('topic-edit-btn');
    const deleteButton = document.getElementById('topic-delete-btn');

    if (editButton) {
        editButton.disabled = !selectedTopicId;
    }
    if (deleteButton) {
        deleteButton.disabled = !selectedTopicId;
    }
}

function setupTopicsInteractionsIfNeeded(showToolbar) {
    if (!showToolbar) {
        selectedTopicId = null;
        return;
    }
    selectedTopicId = null;
    const content = document.getElementById('content');
    initializeTopicTableInteractions(content);
}

window.handleAddTopic = () => {
    console.log('Add Topic clicked');
};

window.handleEditTopic = () => {
    if (!selectedTopicId) {
        alert('수정할 토픽을 선택하세요.');
        return;
    }
    console.log('Edit Topic clicked for', selectedTopicId);
};

window.handleDeleteTopic = () => {
    if (!selectedTopicId) {
        return;
    }
    console.log('Delete Topic clicked for', selectedTopicId);
    selectedTopicId = null;
    updateTopicRowSelection(document.getElementById('content'));
    updateTopicActionButtons();
};
