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

window.handleDeleteTopic = () => {
    if (!selectedTopicId) {
        return;
    }
    console.log('Delete Topic clicked for', selectedTopicId);
    selectedTopicId = null;
    updateTopicRowSelection(document.getElementById('content'));
    updateTopicActionButtons();
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
