// Functions for rendering data to the UI

let selectedTopicId = null;
let editingTopicId = null;
let originalTopicData = null;
let uploadedImageFile = null;
let isAddingNewTopic = false;
const NEW_TOPIC_ID = 'NEW_TOPIC';

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

    // 새 토픽 추가 행을 테이블 최상단에 추가
    let newTopicRow = '';
    if (isAddingNewTopic) {
        newTopicRow = renderNewTopicRow();
    }

    let tableRows = topics.map(topic => {
        if (editingTopicId === topic.id) {
            return renderEditableRow(topic);
        } else {
            // image_uri를 절대 URL로 변환
            let imageUrl = topic.image_uri;
            if (imageUrl && !imageUrl.startsWith('http')) {
                // 상대 경로면 8000 포트로 변환
                imageUrl = `${window.location.protocol}//${window.location.hostname}:8000${imageUrl}`;
            }

            return `
                <tr class="topic-row" data-topic-id="${topic.id}">
                    <td>${topic.name}</td>
                    <td>${topic.type}</td>
                    <td>${topic.summary || 'N/A'}</td>
                    <td>
                        ${topic.image_uri
                            ? `<a href="${imageUrl}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">View Image</a>`
                            : 'N/A'}
                    </td>
                    <td>${topic.keywords && topic.keywords.length ? topic.keywords.join(', ') : 'N/A'}</td>
                    <td>${topic.created_at ? new Date(topic.created_at).toLocaleDateString() : 'N/A'}</td>
                    <td><a href="#" onclick="event.stopPropagation(); loadTopicDetails('${topic.id}'); return false;">View Details</a></td>
                </tr>
            `;
        }
    }).join('');

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
                ${newTopicRow}
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

function renderNewTopicRow() {
    return `
        <tr class="topic-row editing-row new-topic-row" data-topic-id="${NEW_TOPIC_ID}">
            <td><input type="text" class="edit-input" id="new-name" placeholder="토픽 이름" /></td>
            <td>
                <select class="edit-select" id="new-type">
                    <option value="company">company</option>
                    <option value="keyword">keyword</option>
                </select>
            </td>
            <td><input type="text" class="edit-input" id="new-summary" placeholder="요약" /></td>
            <td class="image-edit-cell">
                <input type="file" id="new-image-upload" accept="image/*" style="display:none" onchange="handleNewImageUpload(event)" />
                <button type="button" class="btn-small button-primary" onclick="document.getElementById('new-image-upload').click(); event.stopPropagation();">Upload</button>
                <span id="new-uploaded-file-name" style="font-size: 0.85em; color: #666; display: block; margin-top: 0.3rem;"></span>
            </td>
            <td><input type="text" class="edit-input" id="new-keywords" placeholder="쉼표로 구분" /></td>
            <td>-</td>
            <td class="edit-actions">
                <button type="button" class="btn-small button-success" onclick="saveNewTopic(); event.stopPropagation();">저장</button>
                <button type="button" class="btn-small" onclick="cancelAddTopic(); event.stopPropagation();">취소</button>
            </td>
        </tr>
    `;
}

window.handleAddTopic = async () => {
    // 이미 추가 중이거나 편집 중이면 무시
    if (isAddingNewTopic || editingTopicId) {
        alert('이미 편집 또는 추가 중입니다.');
        return;
    }

    // 추가 모드 진입
    isAddingNewTopic = true;
    uploadedImageFile = null;

    // 토픽 목록 다시 렌더링
    const topics = await fetchTopics();
    renderTopics(topics);
};

window.handleEditTopic = async () => {
    if (!selectedTopicId) {
        alert('수정할 토픽을 선택하세요.');
        return;
    }

    // 이미 편집 중이면 무시
    if (editingTopicId) {
        alert('이미 편집 중인 토픽이 있습니다.');
        return;
    }

    // 편집 모드 진입
    editingTopicId = selectedTopicId;
    uploadedImageFile = null;

    // 토픽 목록 다시 렌더링
    const topics = await fetchTopics();
    renderTopics(topics);
};

window.handleDeleteTopic = async () => {
    if (!selectedTopicId) {
        alert('삭제할 토픽을 선택하세요.');
        return;
    }

    // 확인 메시지
    if (!confirm('정말로 이 토픽을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
        return;
    }

    try {
        await deleteTopic(selectedTopicId);
        alert('토픽이 성공적으로 삭제되었습니다.');

        // 선택 해제 및 목록 새로고침
        selectedTopicId = null;

        const topics = await fetchTopics();
        renderTopics(topics);
    } catch (error) {
        console.error('Error deleting topic:', error);
        alert('토픽 삭제 중 오류가 발생했습니다: ' + error.message);
    }
};

function renderEditableRow(topic) {
    // 원본 데이터 저장
    if (!originalTopicData) {
        originalTopicData = { ...topic };
    }

    const keywordsStr = topic.keywords && topic.keywords.length ? topic.keywords.join(', ') : '';

    return `
        <tr class="topic-row editing-row" data-topic-id="${topic.id}">
            <td><input type="text" class="edit-input" id="edit-name" value="${topic.name}" /></td>
            <td>
                <select class="edit-select" id="edit-type">
                    <option value="company" ${topic.type === 'company' ? 'selected' : ''}>company</option>
                    <option value="keyword" ${topic.type === 'keyword' ? 'selected' : ''}>keyword</option>
                </select>
            </td>
            <td><input type="text" class="edit-input" id="edit-summary" value="${topic.summary || ''}" /></td>
            <td class="image-edit-cell">
                ${topic.image_uri ? `<div style="font-size: 0.85em; margin-bottom: 0.3rem;"><a href="${topic.image_uri}" target="_blank" rel="noopener noreferrer">Current</a></div>` : ''}
                <input type="file" id="edit-image-upload" accept="image/*" style="display:none" onchange="handleImageUpload(event)" />
                <button type="button" class="btn-small button-primary" onclick="document.getElementById('edit-image-upload').click(); event.stopPropagation();">Upload</button>
                ${topic.image_uri ? `<button type="button" class="btn-small button-danger" onclick="handleDeleteImage('${topic.id}'); event.stopPropagation();">Delete</button>` : ''}
                <span id="uploaded-file-name" style="font-size: 0.85em; color: #666; display: block; margin-top: 0.3rem;"></span>
            </td>
            <td><input type="text" class="edit-input" id="edit-keywords" value="${keywordsStr}" placeholder="쉼표로 구분" /></td>
            <td>${topic.created_at ? new Date(topic.created_at).toLocaleDateString() : 'N/A'}</td>
            <td class="edit-actions">
                <button type="button" class="btn-small button-success" onclick="saveTopicEdit('${topic.id}'); event.stopPropagation();">저장</button>
                <button type="button" class="btn-small" onclick="cancelTopicEdit(); event.stopPropagation();">취소</button>
            </td>
        </tr>
    `;
}

window.handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
        uploadedImageFile = file;
        const fileNameSpan = document.getElementById('uploaded-file-name');
        if (fileNameSpan) {
            fileNameSpan.textContent = `선택됨: ${file.name}`;
        }
    }
};

window.handleNewImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
        uploadedImageFile = file;
        const fileNameSpan = document.getElementById('new-uploaded-file-name');
        if (fileNameSpan) {
            fileNameSpan.textContent = `선택됨: ${file.name}`;
        }
    }
};

window.handleDeleteImage = async (topicId) => {
    if (!confirm('이미지를 삭제하시겠습니까?')) {
        return;
    }

    try {
        await deleteTopicImage(topicId);
        alert('이미지가 삭제되었습니다.');

        // 재렌더링
        const topics = await fetchTopics();
        renderTopics(topics);
    } catch (error) {
        console.error('Error deleting image:', error);
        alert('이미지 삭제 중 오류가 발생했습니다: ' + error.message);
    }
};

window.saveTopicEdit = async (topicId) => {
    try {
        // 폼 데이터 수집
        const name = document.getElementById('edit-name').value.trim();
        const type = document.getElementById('edit-type').value;
        const summary = document.getElementById('edit-summary').value.trim();
        const keywordsInput = document.getElementById('edit-keywords').value.trim();
        const keywords = keywordsInput ? keywordsInput.split(',').map(k => k.trim()).filter(k => k) : [];

        // 검증
        if (!name) {
            alert('토픽 이름은 필수입니다.');
            return;
        }

        // 이미지 업로드 (선택사항)
        let currentImageUri = originalTopicData.image_uri;
        if (uploadedImageFile) {
            try {
                const imageResult = await uploadTopicImage(topicId, uploadedImageFile);
                if (imageResult && imageResult.image_uri) {
                    currentImageUri = imageResult.image_uri;
                }
            } catch (error) {
                alert('이미지 업로드 실패: ' + error.message);
                return;
            }
        }

        // 업데이트할 데이터
        const updateData = {
            name,
            type,
            summary,
            image_uri: currentImageUri,
            keywords
        };

        // 토픽 업데이트
        await updateTopic(topicId, updateData);

        alert('토픽이 성공적으로 업데이트되었습니다.');

        // 편집 모드 종료 및 재렌더링
        editingTopicId = null;
        originalTopicData = null;
        uploadedImageFile = null;
        selectedTopicId = null;

        const topics = await fetchTopics();
        renderTopics(topics);

    } catch (error) {
        console.error('Error saving topic:', error);
        alert('토픽 업데이트 중 오류가 발생했습니다: ' + error.message);
    }
};

window.cancelTopicEdit = async () => {
    editingTopicId = null;
    originalTopicData = null;
    uploadedImageFile = null;

    const topics = await fetchTopics();
    renderTopics(topics);
};

window.saveNewTopic = async () => {
    try {
        // 폼 데이터 수집
        const name = document.getElementById('new-name').value.trim();
        const type = document.getElementById('new-type').value;
        const summary = document.getElementById('new-summary').value.trim();
        const keywordsInput = document.getElementById('new-keywords').value.trim();
        const keywords = keywordsInput ? keywordsInput.split(',').map(k => k.trim()).filter(k => k) : [];

        // 검증
        if (!name) {
            alert('토픽 이름은 필수입니다.');
            return;
        }

        // 토픽 생성 데이터 (sources는 빈 배열로)
        const newTopicData = {
            name,
            type,
            summary,
            image_uri: '',
            keywords,
            sources: []
        };

        // 토픽 생성
        const createdTopic = await createTopic(newTopicData);

        // 이미지 업로드 (선택사항)
        if (uploadedImageFile && createdTopic && createdTopic.id) {
            try {
                await uploadTopicImage(createdTopic.id, uploadedImageFile);
            } catch (error) {
                console.error('이미지 업로드 실패:', error);
                alert('토픽은 생성되었으나 이미지 업로드에 실패했습니다: ' + error.message);
            }
        }

        alert('새 토픽이 성공적으로 생성되었습니다.');

        // 추가 모드 종료 및 재렌더링
        isAddingNewTopic = false;
        uploadedImageFile = null;
        selectedTopicId = null;

        const topics = await fetchTopics();
        renderTopics(topics);

    } catch (error) {
        console.error('Error creating topic:', error);
        alert('토픽 생성 중 오류가 발생했습니다: ' + error.message);
    }
};

window.cancelAddTopic = async () => {
    isAddingNewTopic = false;
    uploadedImageFile = null;

    const topics = await fetchTopics();
    renderTopics(topics);
};

// ==================== Article 관련 렌더링 함수 ====================
let selectedArticleId = null;
let selectedDifficulty = 'intermediate';
let selectedContentType = 'article'; // 'article' or 'script'

async function renderArticles(articles, topics) {
    const content = document.getElementById('content');
    if (!articles || articles.length === 0) {
        content.innerHTML = '<h2>Articles</h2><p>No articles found.</p>';
        return;
    }

    // topic_id로 topic 정보를 매핑
    const topicMap = {};
    if (topics && topics.length > 0) {
        topics.forEach(topic => {
            topicMap[topic.id] = topic;
        });
    }

    // 테이블 행 생성
    const tableRows = articles.map(article => {
        const topic = topicMap[article.topic_id];
        const topicName = topic ? topic.name : 'Unknown';

        // article_data에서 summary 추출
        let summary = 'N/A';
        if (article.article_data && article.article_data.summary) {
            summary = article.article_data.summary.substring(0, 100) + '...';
        }

        return `
            <tr class="article-row ${selectedArticleId === article.id ? 'selected' : ''}"
                data-article-id="${article.id}"
                onclick="selectArticle('${article.id}')">
                <td>${topicName}</td>
                <td>${article.title}</td>
                <td>${summary}</td>
                <td>${new Date(article.created_at).toLocaleDateString()}</td>
            </tr>
        `;
    }).join('');

    content.innerHTML = `
        <h2>Articles</h2>
        <div class="articles-layout">
            <div class="articles-table-panel">
                <table>
                    <thead>
                        <tr>
                            <th>Topic</th>
                            <th>Title</th>
                            <th>Summary</th>
                            <th>Created</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows}
                    </tbody>
                </table>
            </div>
            <div class="article-detail-panel">
                <div id="article-detail-content">
                    <p class="placeholder-text">Select an article to view details</p>
                </div>
            </div>
        </div>
    `;
}

window.selectArticle = async (articleId) => {
    selectedArticleId = articleId;

    // 테이블 행 선택 상태 업데이트
    document.querySelectorAll('.article-row').forEach(row => {
        row.classList.toggle('selected', row.dataset.articleId === articleId);
    });

    // Article 상세 정보 가져오기
    const articles = await fetchAllArticles();
    const article = articles.find(a => a.id === articleId);

    if (!article) {
        return;
    }

    // Topic 정보 가져오기
    const topics = await fetchTopics();
    const topic = topics.find(t => t.id === article.topic_id);
    const topicName = topic ? topic.name : 'Unknown';

    renderArticleDetail(article, topicName);
};

function renderArticleDetail(article, topicName) {
    const detailContent = document.getElementById('article-detail-content');

    if (!detailContent) {
        return;
    }

    // 난이도별 데이터 확인
    const hasArticleData = article.article_data &&
        (article.article_data.beginner || article.article_data.intermediate || article.article_data.advanced);
    const hasScriptData = article.script_data &&
        (article.script_data.beginner || article.script_data.intermediate || article.script_data.advanced);

    if (!hasArticleData && !hasScriptData) {
        detailContent.innerHTML = `
            <div class="article-detail-header">
                <h3>${article.title}</h3>
                <p><strong>Topic:</strong> ${topicName}</p>
                <p><strong>Date:</strong> ${new Date(article.created_at).toLocaleDateString()}</p>
                <p><strong>Status:</strong> ${article.status}</p>
            </div>
            <p>No article or script data available.</p>
        `;
        return;
    }

    // 콘텐츠 타입 드롭다운
    const contentTypeOptions = [];
    if (hasArticleData) contentTypeOptions.push('<option value="article">Article</option>');
    if (hasScriptData) contentTypeOptions.push('<option value="script">Script</option>');

    // 현재 선택된 콘텐츠 타입의 데이터
    const currentData = selectedContentType === 'article' ? article.article_data : article.script_data;
    const difficultyData = currentData ? currentData[selectedDifficulty] : null;

    let contentHtml = '';
    if (difficultyData && difficultyData.content) {
        contentHtml = `<div class="article-content">${difficultyData.content.replace(/\n/g, '<br>')}</div>`;
    } else {
        contentHtml = `<p>No content available for ${selectedDifficulty} level.</p>`;
    }

    detailContent.innerHTML = `
        <div class="article-detail-header">
            <h3>${article.title}</h3>
            <p><strong>Topic:</strong> ${topicName}</p>
            <p><strong>Date:</strong> ${new Date(article.created_at).toLocaleDateString()}</p>
            <p><strong>Status:</strong> ${article.status}</p>

            <div class="article-controls">
                <label for="content-type-select">Content Type:</label>
                <select id="content-type-select" onchange="changeContentType(this.value)">
                    ${contentTypeOptions.join('')}
                </select>
            </div>
        </div>

        <div class="difficulty-tabs">
            <button class="tab-button ${selectedDifficulty === 'beginner' ? 'active' : ''}"
                    onclick="changeDifficulty('beginner')">Beginner</button>
            <button class="tab-button ${selectedDifficulty === 'intermediate' ? 'active' : ''}"
                    onclick="changeDifficulty('intermediate')">Intermediate</button>
            <button class="tab-button ${selectedDifficulty === 'advanced' ? 'active' : ''}"
                    onclick="changeDifficulty('advanced')">Advanced</button>
        </div>

        ${contentHtml}
    `;

    // 드롭다운 값 설정
    const contentTypeSelect = document.getElementById('content-type-select');
    if (contentTypeSelect) {
        contentTypeSelect.value = selectedContentType;
    }
}

window.changeDifficulty = async (difficulty) => {
    selectedDifficulty = difficulty;

    if (!selectedArticleId) return;

    const articles = await fetchAllArticles();
    const article = articles.find(a => a.id === selectedArticleId);

    if (!article) return;

    const topics = await fetchTopics();
    const topic = topics.find(t => t.id === article.topic_id);
    const topicName = topic ? topic.name : 'Unknown';

    renderArticleDetail(article, topicName);
};

window.changeContentType = async (contentType) => {
    selectedContentType = contentType;

    if (!selectedArticleId) return;

    const articles = await fetchAllArticles();
    const article = articles.find(a => a.id === selectedArticleId);

    if (!article) return;

    const topics = await fetchTopics();
    const topic = topics.find(t => t.id === article.topic_id);
    const topicName = topic ? topic.name : 'Unknown';

    renderArticleDetail(article, topicName);
};

// ==================== Jobs 페이지 렌더링 함수 ====================
let selectedJobTopicId = null;
let jobMonitorInterval = null;

async function renderJobs(topics) {
    const content = document.getElementById('content');

    if (!topics || topics.length === 0) {
        content.innerHTML = '<h2>Podcast Jobs</h2><p>No topics found.</p>';
        return;
    }

    // 토픽 카드 생성
    const topicCards = topics.map(topic => `
        <div class="topic-card ${selectedJobTopicId === topic.id ? 'selected' : ''}"
             data-topic-id="${topic.id}"
             onclick="selectJobTopic('${topic.id}')">
            <div class="topic-card-header">
                <h3>${topic.name}</h3>
                <span class="topic-type-badge">${topic.type}</span>
            </div>
            <p class="topic-summary">${topic.summary || 'No summary'}</p>
            <div class="topic-card-actions">
                <button class="btn-small button-success" onclick="event.stopPropagation(); generatePodcastForTopic('${topic.id}')">
                    Generate Podcast
                </button>
            </div>
        </div>
    `).join('');

    content.innerHTML = `
        <h2>Podcast Jobs</h2>
        <div class="jobs-layout">
            <div class="topics-grid-panel">
                <h3>Topics</h3>
                <div class="topics-grid">
                    ${topicCards}
                </div>
            </div>
            <div class="job-monitor-panel">
                <div id="job-monitor-content">
                    <p class="placeholder-text">Select a topic to view job status</p>
                </div>
            </div>
        </div>
    `;
}

window.selectJobTopic = async (topicId) => {
    selectedJobTopicId = topicId;

    // 카드 선택 상태 업데이트
    document.querySelectorAll('.topic-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.topicId === topicId);
    });

    // 모니터링 시작
    await updateJobMonitor(topicId);

    // 기존 인터벌 클리어
    if (jobMonitorInterval) {
        clearInterval(jobMonitorInterval);
    }

    // 5초마다 상태 업데이트
    jobMonitorInterval = setInterval(async () => {
        await updateJobMonitor(topicId);
    }, 5000);
};

async function updateJobMonitor(topicId) {
    const monitorContent = document.getElementById('job-monitor-content');
    if (!monitorContent) return;

    try {
        // 상태 및 파일 정보 가져오기
        const [status, files, topics] = await Promise.all([
            fetchPodcastStatus(topicId),
            fetchGeneratedFiles(topicId),
            fetchTopics()
        ]);

        const topic = topics.find(t => t.id === topicId);
        const topicName = topic ? topic.name : 'Unknown';

        // 상태 정보 렌더링
        let statusHtml = '';
        if (status) {
            const statusCounts = status.status_counts || {};
            statusHtml = `
                <div class="status-section">
                    <h4>Status Overview</h4>
                    <div class="status-grid">
                        <div class="status-item">
                            <span class="status-label">Total Articles:</span>
                            <span class="status-value">${status.total_articles}</span>
                        </div>
                        ${Object.entries(statusCounts).map(([s, count]) => `
                            <div class="status-item">
                                <span class="status-label">${s}:</span>
                                <span class="status-value status-${s}">${count}</span>
                            </div>
                        `).join('')}
                    </div>

                    <h5>Recent Articles</h5>
                    <div class="articles-list">
                        ${status.recent_articles && status.recent_articles.length > 0
                            ? status.recent_articles.map(article => `
                                <div class="article-status-item">
                                    <div class="article-status-header">
                                        <strong>${article.title}</strong>
                                        <span class="status-badge status-${article.status}">${article.status}</span>
                                    </div>
                                    ${article.error_message ? `<p class="error-message">${article.error_message}</p>` : ''}
                                    <small>${new Date(article.created_at).toLocaleString()}</small>
                                </div>
                            `).join('')
                            : '<p>No recent articles</p>'
                        }
                    </div>
                </div>
            `;
        }

        // 파일 정보 렌더링
        let filesHtml = '';
        if (files && files.files && files.files.length > 0) {
            filesHtml = `
                <div class="files-section">
                    <h4>Generated Files (${files.total_files})</h4>
                    <div class="files-list">
                        ${files.files.map(file => `
                            <div class="file-item">
                                <div class="file-icon">${getFileIcon(file.type)}</div>
                                <div class="file-info">
                                    <strong>${file.name}</strong>
                                    <small>${formatFileSize(file.size)} • ${new Date(file.modified * 1000).toLocaleString()}</small>
                                    <div class="file-path">${file.path}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        } else {
            filesHtml = `
                <div class="files-section">
                    <h4>Generated Files</h4>
                    <p class="placeholder-text">No files generated yet</p>
                </div>
            `;
        }

        monitorContent.innerHTML = `
            <div class="job-monitor-header">
                <h3>${topicName}</h3>
                <button class="btn-small" onclick="refreshJobMonitor()">Refresh</button>
            </div>
            ${statusHtml}
            ${filesHtml}
        `;

    } catch (error) {
        console.error('Error updating job monitor:', error);
        monitorContent.innerHTML = '<p class="error-message">Error loading job information</p>';
    }
}

window.generatePodcastForTopic = async (topicId) => {
    if (!confirm('Are you sure you want to generate a podcast for this topic? This may take some time.')) {
        return;
    }

    try {
        const result = await generatePodcast(topicId);
        alert(`Podcast generation started: ${result.message}`);

        // 모니터링 업데이트
        if (selectedJobTopicId === topicId) {
            await updateJobMonitor(topicId);
        }
    } catch (error) {
        console.error('Error generating podcast:', error);
        alert('Failed to generate podcast: ' + error.message);
    }
};

window.refreshJobMonitor = async () => {
    if (selectedJobTopicId) {
        await updateJobMonitor(selectedJobTopicId);
    }
};

function getFileIcon(fileType) {
    const icons = {
        '.json': '📄',
        '.mp3': '🎵',
        '.wav': '🎵',
        '.txt': '📝',
        '.md': '📝',
        '.pdf': '📕',
        '.jpg': '🖼️',
        '.jpeg': '🖼️',
        '.png': '🖼️'
    };
    return icons[fileType] || '📎';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 페이지를 떠날 때 인터벌 클리어
window.addEventListener('hashchange', () => {
    if (jobMonitorInterval) {
        clearInterval(jobMonitorInterval);
        jobMonitorInterval = null;
    }
});
