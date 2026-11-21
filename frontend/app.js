const state = {
  articles: [],
  view: "all",
  search: "",
  date: "",
  loading: false,
  visibleLimit: 24,
};

const elements = {
  grid: document.querySelector("#article-grid"),
  loading: document.querySelector("#loading-state"),
  empty: document.querySelector("#empty-state"),
  emptyTitle: document.querySelector("#empty-title"),
  emptyCopy: document.querySelector("#empty-copy"),
  error: document.querySelector("#error-state"),
  errorMessage: document.querySelector("#error-message"),
  articleCount: document.querySelector("#article-count"),
  unreadCount: document.querySelector("#unread-count"),
  resultCount: document.querySelector("#result-count"),
  lastUpdated: document.querySelector("#last-updated"),
  fetchButton: document.querySelector("#fetch-button"),
  searchInput: document.querySelector("#search-input"),
  dateFilter: document.querySelector("#date-filter"),
  clearFilters: document.querySelector("#clear-filters"),
  loadMore: document.querySelector("#load-more"),
  toast: document.querySelector("#toast"),
};

function requestJson(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  }).then(async (response) => {
    if (!response.ok) {
      let message = `Request failed with status ${response.status}`;
      try {
        const body = await response.json();
        message = body.detail || message;
      } catch {
        // Keep the status message when the response is not JSON.
      }
      throw new Error(message);
    }
    if (response.status === 204) {
      return null;
    }
    return response.json();
  });
}

function visibleArticles() {
  const query = state.search.trim().toLocaleLowerCase();

  return state.articles.filter((article) => {
    const matchesView =
      state.view === "all" ||
      (state.view === "read" && article.processed) ||
      (state.view === "unread" && !article.processed);
    const matchesSearch = !query || (article.title || "").toLocaleLowerCase().includes(query);
    const matchesDate = !state.date || article.published_day === state.date;
    return matchesView && matchesSearch && matchesDate;
  });
}

function formatDate(article) {
  const value = article.published_at || article.updated_at;
  if (!value) {
    return "Publication date unavailable";
  }

  const date = new Date(value);
  return Number.isNaN(date.valueOf())
    ? article.published_day || "Publication date unavailable"
    : new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      }).format(date);
}

function articleDomain(link) {
  try {
    return new URL(link).hostname.replace(/^www\./, "");
  } catch {
    return "News source";
  }
}

function buildArticleCard(article) {
  const card = document.createElement("article");
  card.className = `article-card${article.processed ? " is-read" : ""}`;

  const accent = document.createElement("div");
  accent.className = "card-accent";

  const content = document.createElement("div");
  content.className = "card-content";

  const topline = document.createElement("div");
  topline.className = "card-topline";

  const domain = document.createElement("span");
  domain.className = "source-domain";
  domain.textContent = articleDomain(article.link);

  const marker = document.createElement("span");
  marker.className = "read-marker";
  marker.title = article.processed ? "Read" : "Unread";

  topline.append(domain, marker);

  const title = document.createElement("h3");
  title.className = "article-title";
  const headline = document.createElement("a");
  headline.textContent = article.title || "Untitled story";
  headline.target = "_blank";
  headline.rel = "noopener noreferrer";
  if (article.link) {
    headline.href = article.link;
  } else {
    headline.removeAttribute("target");
  }
  title.append(headline);

  const date = document.createElement("p");
  date.className = "card-date";
  date.textContent = formatDate(article);

  const footer = document.createElement("div");
  footer.className = "card-footer";

  const open = document.createElement("a");
  open.className = "open-link";
  open.textContent = "Read story";
  if (article.link) {
    open.href = article.link;
    open.target = "_blank";
    open.rel = "noopener noreferrer";
  } else {
    open.setAttribute("aria-disabled", "true");
    open.addEventListener("click", (event) => event.preventDefault());
  }

  const mark = document.createElement("button");
  mark.className = "mark-button";
  mark.type = "button";
  mark.textContent = article.processed ? "Mark unread" : "Mark read";
  mark.addEventListener("click", () => toggleProcessed(article.id));

  footer.append(open, mark);
  content.append(topline, title, date, footer);
  card.append(accent, content);
  return card;
}

function renderArticles() {
  const matches = visibleArticles();
  const articles = matches.slice(0, state.visibleLimit);
  elements.grid.replaceChildren(...articles.map(buildArticleCard));

  elements.loading.hidden = true;
  elements.error.hidden = true;
  elements.grid.hidden = articles.length === 0;
  elements.empty.hidden = articles.length !== 0;
  elements.loadMore.hidden = articles.length >= matches.length || articles.length === 0;
  elements.resultCount.textContent =
    matches.length > articles.length
      ? `Showing ${articles.length} of ${matches.length} stories`
      : `${matches.length} ${matches.length === 1 ? "story" : "stories"}`;

  const hasFilters = Boolean(state.search || state.date || state.view !== "all");
  elements.clearFilters.hidden = !hasFilters;

  if (articles.length === 0) {
    if (state.articles.length === 0) {
      elements.emptyTitle.textContent = "Your reading list is empty";
      elements.emptyCopy.textContent = "Refresh the feeds to collect your first stories.";
    } else {
      elements.emptyTitle.textContent = "No stories match";
      elements.emptyCopy.textContent = "Try changing your search, date, or reading status.";
    }
  }
}

function updateSummary() {
  elements.articleCount.textContent = state.articles.length;
  elements.unreadCount.textContent = state.articles.filter((article) => !article.processed).length;
  elements.lastUpdated.textContent = `Updated ${new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date())}`;
}

function showError(error) {
  elements.loading.hidden = true;
  elements.grid.hidden = true;
  elements.empty.hidden = true;
  elements.error.hidden = false;
  elements.errorMessage.textContent = error.message || "Check that the API is running and try again.";
  elements.resultCount.textContent = "News is temporarily unavailable";
}

function setLoading(isLoading) {
  state.loading = isLoading;
  elements.loading.hidden = !isLoading;
  elements.grid.hidden = isLoading;
  elements.empty.hidden = true;
  elements.error.hidden = true;
  elements.fetchButton.disabled = isLoading;
  elements.fetchButton.classList.toggle("is-loading", isLoading);
  elements.fetchButton.querySelector("span").textContent = isLoading ? "Refreshing…" : "Refresh feeds";
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.hidden = false;
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => {
    elements.toast.hidden = true;
  }, 3600);
}

async function loadArticles() {
  setLoading(true);
  try {
    const params = new URLSearchParams();
    if (state.date) {
      params.set("published_on", state.date);
    }
    const query = params.toString();
    state.articles = await requestJson(`/articles${query ? `?${query}` : ""}`);
    updateSummary();
    renderArticles();
  } catch (error) {
    showError(error);
    return false;
  } finally {
    state.loading = false;
    elements.fetchButton.disabled = false;
    elements.fetchButton.classList.remove("is-loading");
    elements.fetchButton.querySelector("span").textContent = "Refresh feeds";
  }
  return true;
}

async function refreshFeeds() {
  if (state.loading) return;
  setLoading(true);
  try {
    const articles = await requestJson("/articles/fetch", { method: "POST" });
    const loaded = await loadArticles();
    if (loaded) {
      showToast(`${articles.length} new ${articles.length === 1 ? "story" : "stories"} added`);
    }
  } catch (error) {
    showError(error);
  }
}

async function toggleProcessed(articleId) {
  const article = state.articles.find((item) => item.id === articleId);
  if (!article) return;

  try {
    const updated = await requestJson(`/articles/${articleId}`, {
      method: "PUT",
      body: JSON.stringify({ processed: !article.processed }),
    });
    state.articles = state.articles.map((item) => (item.id === articleId ? updated : item));
    updateSummary();
    renderArticles();
    showToast(updated.processed ? "Story marked as read" : "Story moved back to unread");
  } catch (error) {
    showToast(error.message);
  }
}

elements.searchInput.addEventListener("input", (event) => {
  state.search = event.target.value;
  state.visibleLimit = 24;
  renderArticles();
});

elements.dateFilter.addEventListener("change", (event) => {
  state.date = event.target.value;
  state.visibleLimit = 24;
  loadArticles();
});

document.querySelectorAll(".view-button").forEach((button) => {
  button.addEventListener("click", () => {
    state.view = button.dataset.view;
    state.visibleLimit = 24;
    document.querySelectorAll(".view-button").forEach((item) => {
      item.classList.toggle("is-active", item === button);
    });
    renderArticles();
  });
});

elements.clearFilters.addEventListener("click", () => {
  state.search = "";
  state.date = "";
  state.view = "all";
  state.visibleLimit = 24;
  elements.searchInput.value = "";
  elements.dateFilter.value = "";
  document.querySelectorAll(".view-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === "all");
  });
  loadArticles();
});

elements.loadMore.addEventListener("click", () => {
  state.visibleLimit += 24;
  renderArticles();
});

elements.fetchButton.addEventListener("click", refreshFeeds);
document.querySelector("#empty-refresh").addEventListener("click", refreshFeeds);
document.querySelector("#retry-button").addEventListener("click", loadArticles);

loadArticles();
