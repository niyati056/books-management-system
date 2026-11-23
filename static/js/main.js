/**
 * BÓOKLY - Client-Side Interactive Engine
 * Literary UX: My Bookshelf, Quick View Modal, Live Previews, PDF Reader controls
 */

document.addEventListener('DOMContentLoaded', function () {
    initBookshelf();
    initQuickView();
    initFormImagePreview();
    initToasts();
});

/* ==========================================================
   MY BOOKSHELF (LOCALSTORAGE FAVORITES SYSTEM)
   ========================================================== */

const BOOKSHELF_KEY = 'bookly_saved_books';

function getSavedBooks() {
    try {
        const stored = localStorage.getItem(BOOKSHELF_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch (e) {
        return [];
    }
}

function saveBooks(books) {
    try {
        localStorage.setItem(BOOKSHELF_KEY, JSON.stringify(books));
    } catch (e) {
        console.error('Failed to save to localStorage', e);
    }
}

function updateBookshelfCount() {
    const books = getSavedBooks();
    const countBadges = document.querySelectorAll('.bookshelf-count-badge');
    countBadges.forEach(badge => {
        badge.textContent = books.length;
        badge.style.display = books.length > 0 ? 'inline-flex' : 'none';
    });
}

function renderBookshelfDrawer() {
    const listContainer = document.getElementById('bookshelfItemsList');
    if (!listContainer) return;

    const books = getSavedBooks();

    if (books.length === 0) {
        listContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="mb-3" style="font-size: 3rem; color: #C45536;">📖</div>
                <h5 class="fw-bold mb-1">Your bookshelf is empty</h5>
                <p class="text-muted small">Tap the heart icon on any book to curate your reading list.</p>
                <a href="/user-all/" class="btn btn-editorial-primary btn-sm mt-2">Explore Library</a>
            </div>
        `;
        return;
    }

    let html = '';
    books.forEach(b => {
        html += `
            <div class="bookshelf-item d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center gap-3">
                    <img src="${b.image || '/static/images/image.png'}" alt="${b.name}" style="width: 50px; height: 70px; object-fit: cover; border-radius: 4px;">
                    <div>
                        <h6 class="mb-1 font-serif fw-bold" style="font-size: 15px;">
                            <a href="${b.url}" class="text-dark">${b.name}</a>
                        </h6>
                        <p class="text-muted small mb-0">by ${b.author}</p>
                    </div>
                </div>
                <button class="btn btn-sm text-danger border-0" onclick="removeBookFromShelf(${b.id})" title="Remove from list">
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                        <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                    </svg>
                </button>
            </div>
        `;
    });

    html += `
        <div class="mt-4 pt-3 border-top d-flex justify-content-between align-items-center">
            <span class="small text-muted">${books.length} saved volume${books.length > 1 ? 's' : ''}</span>
            <button class="btn btn-sm btn-link text-muted p-0" onclick="clearBookshelf()">Clear All</button>
        </div>
    `;

    listContainer.innerHTML = html;
}

window.toggleSaveBook = function (btn, id, name, author, image, url) {
    let books = getSavedBooks();
    const existingIndex = books.findIndex(b => b.id === id);

    if (existingIndex > -1) {
        books.splice(existingIndex, 1);
        btn.classList.remove('active');
        btn.querySelector('svg').setAttribute('fill', 'none');
        showToast(`Removed "${name}" from your bookshelf`, 'info');
    } else {
        books.push({ id, name, author, image, url });
        btn.classList.add('active');
        btn.querySelector('svg').setAttribute('fill', '#E63946');
        showToast(`Saved "${name}" to your bookshelf!`, 'success');
    }

    saveBooks(books);
    updateBookshelfCount();
    renderBookshelfDrawer();
};

window.removeBookFromShelf = function (id) {
    let books = getSavedBooks();
    books = books.filter(b => b.id !== id);
    saveBooks(books);
    updateBookshelfCount();
    renderBookshelfDrawer();

    // Sync button state on current page
    const btn = document.querySelector(`.cover-action-favorite[data-id="${id}"]`);
    if (btn) {
        btn.classList.remove('active');
        btn.querySelector('svg').setAttribute('fill', 'none');
    }
};

window.clearBookshelf = function () {
    if (confirm('Clear all saved books from your bookshelf?')) {
        saveBooks([]);
        updateBookshelfCount();
        renderBookshelfDrawer();
        document.querySelectorAll('.cover-action-favorite').forEach(btn => {
            btn.classList.remove('active');
            btn.querySelector('svg').setAttribute('fill', 'none');
        });
    }
};

function initBookshelf() {
    updateBookshelfCount();
    renderBookshelfDrawer();

    // Mark active buttons on page load
    const saved = getSavedBooks();
    saved.forEach(b => {
        const btn = document.querySelector(`.cover-action-favorite[data-id="${b.id}"]`);
        if (btn) {
            btn.classList.add('active');
            btn.querySelector('svg').setAttribute('fill', '#E63946');
        }
    });
}

/* ==========================================================
   QUICK VIEW MODAL
   ========================================================== */

function initQuickView() {
    const modalEl = document.getElementById('quickViewModal');
    if (!modalEl) return;

    window.openQuickView = function (bookId) {
        const modal = new bootstrap.Modal(modalEl);
        const spinner = document.getElementById('quickViewLoading');
        const content = document.getElementById('quickViewContent');

        spinner.style.display = 'block';
        content.style.display = 'none';
        modal.show();

        fetch(`/api/quick-view/${bookId}/`)
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById('qvTitle').textContent = data.book_name;
                    document.getElementById('qvAuthor').textContent = `by ${data.author_name}`;
                    document.getElementById('qvCategory').textContent = data.category;
                    document.getElementById('qvRating').textContent = `★ ${data.rating}`;
                    document.getElementById('qvPages').textContent = data.pdf_pages ? `${data.pages} print pages • ${data.pdf_pages} PDF pages` : `${data.pages} pages`;
                    document.getElementById('qvLanguage').textContent = data.language;
                    document.getElementById('qvDescription').textContent = data.description;
                    document.getElementById('qvDetailLink').setAttribute('href', data.detail_url);

                    const imgEl = document.getElementById('qvCover');
                    if (data.image_url) {
                        imgEl.src = data.image_url;
                        imgEl.style.display = 'block';
                    } else {
                        imgEl.style.display = 'none';
                    }

                    const pdfBadge = document.getElementById('qvPdfBadge');
                    const pdfBtn = document.getElementById('qvPdfButton');
                    const readOnlineLink = document.getElementById('qvReadOnlineLink');
                    if (data.has_pdf) {
                        pdfBadge.style.display = 'inline-block';
                        pdfBtn.setAttribute('href', data.download_url);
                        pdfBtn.style.display = 'inline-flex';
                        if (readOnlineLink) {
                            readOnlineLink.setAttribute('href', `${data.detail_url}?read=1`);
                            readOnlineLink.style.display = 'inline-flex';
                        }
                    } else {
                        pdfBadge.style.display = 'none';
                        pdfBtn.style.display = 'none';
                        if (readOnlineLink) {
                            readOnlineLink.style.display = 'none';
                        }
                    }

                    spinner.style.display = 'none';
                    content.style.display = 'flex';
                }
            })
            .catch(err => {
                console.error('Quick view error:', err);
                spinner.innerHTML = '<div class="text-danger py-4">Failed to load book preview.</div>';
            });
    };
}

/* ==========================================================
   FORM IMAGE LIVE PREVIEW
   ========================================================== */

function initFormImagePreview() {
    const input = document.getElementById('bookImageInput');
    const preview = document.getElementById('imageLivePreview');
    const container = document.getElementById('imagePreviewContainer');

    if (input && preview && container) {
        input.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    preview.src = e.target.result;
                    container.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

/* ==========================================================
   TOASTS NOTIFICATIONS
   ========================================================== */

function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container-custom');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container-custom';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `editorial-toast ${type}`;
    toast.innerHTML = `
        <div style="font-size: 16px;">
            ${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}
        </div>
        <div class="flex-grow-1 small fw-semibold">${message}</div>
        <button type="button" class="btn-close btn-close-sm" style="font-size: 10px;" onclick="this.parentElement.remove()"></button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

function initToasts() {
    document.querySelectorAll('.django-message-toast').forEach(toast => {
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 400);
        }, 4500);
    });
}
