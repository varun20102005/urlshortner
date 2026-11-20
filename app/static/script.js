
const form = document.getElementById("shorten-form");
const urlInput = document.getElementById("url-input");
const formMessage = document.getElementById("form-message");
const shortenBtn = document.getElementById("shorten-btn");

const urlsTable = document.getElementById("urls-table");
const searchInput = document.getElementById("search-input");
const refreshBtn = document.getElementById("refresh-btn");

const totalLinksElement = document.getElementById("total-links");
const totalClicksElement = document.getElementById("total-clicks");

const clickChart = document.getElementById("click-chart");

let allUrls = [];

// -----------------------------
// Validate HTML Elements
// -----------------------------

const requiredElements = {
    form,
    urlInput,
    formMessage,
    shortenBtn,
    urlsTable,
    searchInput,
    refreshBtn,
    totalLinksElement,
    totalClicksElement,
    clickChart
};

const missingElements = Object.entries(requiredElements)
    .filter(([name, element]) => element === null)
    .map(([name]) => name);

if (missingElements.length > 0) {
    console.error("Missing HTML elements:", missingElements);
}

// -----------------------------
// Create Short URL
// -----------------------------

if (form) {
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const originalUrl = urlInput.value.trim();

        if (!originalUrl) {
            showMessage("Please enter a URL.", "error");
            return;
        }

        shortenBtn.disabled = true;
        shortenBtn.textContent = "Creating...";

        try {
            const response = await fetch("/api/shorten", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    url: originalUrl
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Failed to shorten URL.");
            }

            showMessage(
                `Short URL created: ${window.location.origin}/${data.short_code}`,
                "success"
            );

            urlInput.value = "";

            await loadUrls();

        } catch (error) {
            showMessage(error.message, "error");
        } finally {
            shortenBtn.disabled = false;
            shortenBtn.innerHTML = 'Shorten URL <span>→</span>';
        }
    });
}

// -----------------------------
// Messages
// -----------------------------

function showMessage(message, type) {
    if (!formMessage) return;

    formMessage.textContent = message;

    formMessage.style.color =
        type === "error" ? "#dc2626" : "#16a34a";
}

// -----------------------------
// Load URLs
// -----------------------------

async function loadUrls() {
    try {
        const response = await fetch("/api/urls");

        if (!response.ok) {
            throw new Error(`Failed to load URLs: ${response.status}`);
        }

        allUrls = await response.json();

        renderUrls(allUrls);

    } catch (error) {
        console.error("Load URLs error:", error);

        if (urlsTable) {
            urlsTable.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state">
                        Unable to load URLs.
                    </td>
                </tr>
            `;
        }

        if (totalLinksElement) {
            totalLinksElement.textContent = "0";
        }

        if (totalClicksElement) {
            totalClicksElement.textContent = "0";
        }

        if (clickChart) {
            renderClickChart([]);
        }
    }
}

// -----------------------------
// Render Dashboard
// -----------------------------

function renderUrls(urls) {
    if (!urlsTable) {
        console.error("Cannot render URLs: urls-table is missing.");
        return;
    }

    if (totalLinksElement) {
        totalLinksElement.textContent = allUrls.length;
    }

    const totalClicks = allUrls.reduce(
        (total, url) => total + (url.total_clicks || 0),
        0
    );

    if (totalClicksElement) {
        totalClicksElement.textContent = totalClicks;
    }

    if (clickChart) {
        renderClickChart(allUrls);
    }

    const searchTerm = searchInput
        ? searchInput.value.toLowerCase().trim()
        : "";

    const filteredUrls = urls.filter(url =>
        url.short_code.toLowerCase().includes(searchTerm) ||
        url.original_url.toLowerCase().includes(searchTerm)
    );

    if (filteredUrls.length === 0) {
        urlsTable.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    No URLs found.
                </td>
            </tr>
        `;
        return;
    }

    urlsTable.innerHTML = "";

    filteredUrls.forEach(url => {
        const row = document.createElement("tr");

        const shortUrl =
            `${window.location.origin}/${url.short_code}`;

        const expiration = getExpirationStatus(url.expires_at);

        const shortUrlCell = document.createElement("td");

        const shortUrlLink = document.createElement("a");
        shortUrlLink.href = shortUrl;
        shortUrlLink.target = "_blank";
        shortUrlLink.rel = "noopener noreferrer";
        shortUrlLink.textContent = shortUrl;

        shortUrlCell.appendChild(shortUrlLink);

        const originalUrlCell = document.createElement("td");

        const originalUrlDiv = document.createElement("div");
        originalUrlDiv.className = "original-url";
        originalUrlDiv.textContent = url.original_url;

        originalUrlCell.appendChild(originalUrlDiv);

        const clicksCell = document.createElement("td");
        clicksCell.textContent = url.total_clicks;

        const expirationCell = document.createElement("td");
        expirationCell.textContent = expiration;

        const actionsCell = document.createElement("td");

        const copyButton = document.createElement("button");
        copyButton.className = "copy-btn";
        copyButton.dataset.code = url.short_code;
        copyButton.textContent = "Copy";

        const deleteButton = document.createElement("button");
        deleteButton.className = "delete-btn";
        deleteButton.dataset.code = url.short_code;
        deleteButton.textContent = "Delete";

        actionsCell.appendChild(copyButton);
        actionsCell.appendChild(deleteButton);

        row.appendChild(shortUrlCell);
        row.appendChild(originalUrlCell);
        row.appendChild(clicksCell);
        row.appendChild(expirationCell);
        row.appendChild(actionsCell);

        urlsTable.appendChild(row);
    });

    attachActionListeners();
}

// -----------------------------
// Analytics Chart
// -----------------------------

function renderClickChart(urls) {
    if (!clickChart) return;

    clickChart.innerHTML = "";

    if (!urls || urls.length === 0) {
        clickChart.innerHTML = `
            <p class="chart-empty">
                No link analytics available yet.
            </p>
        `;
        return;
    }

    const topUrls = [...urls]
        .sort((a, b) => b.total_clicks - a.total_clicks)
        .slice(0, 5);

    const maxClicks = Math.max(
        1,
        ...topUrls.map(url => url.total_clicks)
    );

    topUrls.forEach(url => {
        const row = document.createElement("div");
        row.className = "chart-row";

        const label = document.createElement("div");
        label.className = "chart-label";

        const code = document.createElement("span");
        code.className = "chart-code";
        code.textContent = url.short_code;

        const count = document.createElement("span");
        count.className = "chart-count";
        count.textContent = `${url.total_clicks} clicks`;

        label.appendChild(code);
        label.appendChild(count);

        const track = document.createElement("div");
        track.className = "chart-track";

        const bar = document.createElement("div");
        bar.className = "chart-bar";

        const percentage =
            (url.total_clicks / maxClicks) * 100;

        bar.style.width = `${percentage}%`;

        track.appendChild(bar);

        row.appendChild(label);
        row.appendChild(track);

        clickChart.appendChild(row);
    });
}

// -----------------------------
// Expiration Status
// -----------------------------

function getExpirationStatus(expiresAt) {
    if (!expiresAt) {
        return "Never expires";
    }

    const expirationDate = new Date(expiresAt);

    if (expirationDate <= new Date()) {
        return "Expired";
    }

    return expirationDate.toLocaleString();
}

// -----------------------------
// Copy & Delete Actions
// -----------------------------

function attachActionListeners() {
    document.querySelectorAll(".copy-btn").forEach(button => {
        button.addEventListener("click", async () => {
            const shortCode = button.dataset.code;

            const shortUrl =
                `${window.location.origin}/${shortCode}`;

            try {
                await navigator.clipboard.writeText(shortUrl);

                button.textContent = "Copied!";

                setTimeout(() => {
                    button.textContent = "Copy";
                }, 1500);

            } catch (error) {
                alert("Unable to copy URL.");
            }
        });
    });

    document.querySelectorAll(".delete-btn").forEach(button => {
        button.addEventListener("click", async () => {
            const shortCode = button.dataset.code;

            const confirmed = confirm(
                "Are you sure you want to delete this URL?"
            );

            if (!confirmed) {
                return;
            }

            try {
                const response = await fetch(
                    `/api/urls/${shortCode}`,
                    {
                        method: "DELETE"
                    }
                );

                if (!response.ok) {
                    throw new Error("Failed to delete URL.");
                }

                await loadUrls();

            } catch (error) {
                alert(error.message);
            }
        });
    });
}

// -----------------------------
// Search
// -----------------------------

if (searchInput) {
    searchInput.addEventListener("input", () => {
        renderUrls(allUrls);
    });
}

// -----------------------------
// Refresh
// -----------------------------

if (refreshBtn) {
    refreshBtn.addEventListener("click", loadUrls);
}

// -----------------------------
// Initial Load
// -----------------------------

loadUrls();
