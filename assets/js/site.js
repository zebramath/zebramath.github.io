(() => {
  const normalise = (value) => (value || '').toLocaleLowerCase().trim();

  document.querySelectorAll('[data-collection]').forEach((collection) => {
    const tabs = [...collection.querySelectorAll('[data-tab-target]')];
    const panels = [...collection.querySelectorAll('[data-tab-panel]')];
    const search = collection.querySelector('[data-collection-search]');
    const mediaFilters = [...collection.querySelectorAll('[data-media-filter]')];
    const mediaFilterRow = collection.querySelector('[data-media-filters]');
    const pageSize = Number(collection.dataset.pageSize) || 12;
    const pages = { media: 1, games: 1 };
    let activeTab = tabs[0]?.dataset.tabTarget || 'media';
    let activeMediaType = 'all';

    const pageTokens = (total, current) => {
      if (total <= 7) return Array.from({ length: total }, (_, index) => index + 1);
      const selected = [...new Set([1, total, current - 1, current, current + 1])]
        .filter((page) => page >= 1 && page <= total)
        .sort((a, b) => a - b);
      const tokens = [];
      selected.forEach((page, index) => {
        if (index && page - selected[index - 1] > 1) tokens.push('…');
        tokens.push(page);
      });
      return tokens;
    };

    const goToPage = (page) => {
      pages[activeTab] = page;
      updateCards();
      collection.querySelector('.collection-tabs')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    const renderPagination = (totalItems) => {
      const pagination = collection.querySelector(`[data-pagination="${activeTab}"]`);
      if (!pagination) return;
      const totalPages = Math.ceil(totalItems / pageSize);
      if (totalPages <= 1) {
        pagination.hidden = true;
        pagination.replaceChildren();
        return;
      }
      pages[activeTab] = Math.min(Math.max(pages[activeTab], 1), totalPages);
      const current = pages[activeTab];
      const zh = document.documentElement.lang.toLowerCase().startsWith('zh');
      const makeButton = (label, page, className = '') => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `pagination-button ${className}`.trim();
        button.textContent = label;
        button.addEventListener('click', () => goToPage(page));
        return button;
      };

      const previous = makeButton(zh ? '上一页' : 'Previous', current - 1, 'pagination-edge');
      previous.disabled = current === 1;
      const numbers = document.createElement('span');
      numbers.className = 'pagination-numbers';
      pageTokens(totalPages, current).forEach((token) => {
        if (token === '…') {
          const ellipsis = document.createElement('span');
          ellipsis.className = 'pagination-ellipsis';
          ellipsis.textContent = token;
          numbers.append(ellipsis);
          return;
        }
        const button = makeButton(String(token), token);
        if (token === current) {
          button.classList.add('is-active');
          button.setAttribute('aria-current', 'page');
        }
        numbers.append(button);
      });
      const status = document.createElement('span');
      status.className = 'pagination-status';
      status.textContent = zh ? `第 ${current} / ${totalPages} 页` : `Page ${current} of ${totalPages}`;
      const next = makeButton(zh ? '下一页' : 'Next', current + 1, 'pagination-edge');
      next.disabled = current === totalPages;
      const jump = document.createElement('form');
      jump.className = 'pagination-jump';
      const jumpLabel = document.createElement('label');
      jumpLabel.textContent = zh ? '跳至' : 'Go to';
      const jumpInput = document.createElement('input');
      jumpInput.type = 'text';
      jumpInput.inputMode = 'numeric';
      jumpInput.pattern = '[0-9]*';
      jumpInput.setAttribute('aria-label', zh ? '输入页码' : 'Page number');
      const jumpButton = document.createElement('button');
      jumpButton.type = 'submit';
      jumpButton.className = 'pagination-button';
      jumpButton.textContent = zh ? '跳转' : 'Go';
      jumpLabel.append(jumpInput);
      jump.append(jumpLabel, jumpButton);
      jump.addEventListener('submit', (event) => {
        event.preventDefault();
        const target = Number.parseInt(jumpInput.value, 10);
        if (!Number.isFinite(target)) return;
        goToPage(Math.min(Math.max(target, 1), totalPages));
      });
      pagination.replaceChildren(previous, numbers, status, next, jump);
      pagination.hidden = false;
    };

    const updateCards = () => {
      const query = normalise(search?.value);
      const matches = [];

      collection.querySelectorAll('[data-collection-card]').forEach((card) => {
        const inTab = card.dataset.collectionCard === activeTab;
        const inSearch = !query || normalise(card.textContent).includes(query);
        const inMediaType = activeTab !== 'media' || activeMediaType === 'all' || card.dataset.mediaType === activeMediaType;
        card.hidden = true;
        if (inTab && inSearch && inMediaType) matches.push(card);
      });

      const totalPages = Math.max(1, Math.ceil(matches.length / pageSize));
      pages[activeTab] = Math.min(Math.max(pages[activeTab], 1), totalPages);
      const start = (pages[activeTab] - 1) * pageSize;
      matches.slice(start, start + pageSize).forEach((card) => { card.hidden = false; });

      collection.querySelectorAll('[data-collection-empty]').forEach((empty) => {
        empty.hidden = empty.dataset.collectionEmpty !== activeTab || matches.length !== 0;
      });
      renderPagination(matches.length);
    };

    tabs.forEach((tab) => tab.addEventListener('click', () => {
      activeTab = tab.dataset.tabTarget;
      tabs.forEach((item) => {
        const selected = item === tab;
        item.classList.toggle('is-active', selected);
        item.setAttribute('aria-selected', String(selected));
      });
      panels.forEach((panel) => {
        panel.hidden = panel.dataset.tabPanel !== activeTab;
      });
      if (mediaFilterRow) mediaFilterRow.hidden = activeTab !== 'media';
      updateCards();
    }));

    mediaFilters.forEach((filter) => filter.addEventListener('click', () => {
      activeMediaType = filter.dataset.mediaFilter;
      pages.media = 1;
      mediaFilters.forEach((item) => {
        const selected = item === filter;
        item.classList.toggle('is-active', selected);
        item.setAttribute('aria-pressed', String(selected));
      });
      updateCards();
    }));

    search?.addEventListener('input', () => {
      pages[activeTab] = 1;
      updateCards();
    });
    updateCards();
  });

  document.querySelectorAll('[data-academic-search]').forEach((search) => {
    const scope = search.closest('[data-academic]');
    const empty = scope?.querySelector('[data-academic-empty]');
    search.addEventListener('input', () => {
      const query = normalise(search.value);
      let visible = 0;
      scope.querySelectorAll('[data-course]').forEach((course) => {
        course.hidden = query && !normalise(course.textContent).includes(query);
        if (!course.hidden) visible += 1;
      });
      if (empty) empty.hidden = visible !== 0;
    });
  });
})();
