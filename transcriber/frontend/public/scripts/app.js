const treeContainer = document.querySelector("#folder-tree");
const jobsContainer = document.querySelector("#jobs");
const message = document.querySelector("#message");

function showMessage(text, kind = "success") {
    message.textContent = text;
    message.className = `alert alert-${kind}`;
}

function renderTree(nodes, parent = treeContainer, prefix = "") {
    nodes.forEach((node, index) => {
        const branch = index === nodes.length - 1 ? "└── " : "├── ";
        const path = prefix ? `${prefix}/${node.name}` : node.name;
        if (node.type === "folder") {
            const details = document.createElement("details");
            const summary = document.createElement("summary");
            summary.innerHTML = `<span class="tree-branch">${branch}</span><span class="tree-folder-icon">▰</span><span>${node.name}</span>`;
            details.append(summary);
            const children = document.createElement("div");
            children.className = "tree-children";
            renderTree(node.children, children, path);
            details.append(children);
            parent.append(details);
        } else {
            const label = document.createElement("label");
            label.className = "tree-file";
            label.innerHTML = `<span class="tree-branch">${branch}</span><input class="video-check" type="checkbox" value="${node.path}" ${node.status === "completed" ? "disabled" : ""}><span class="tree-file-icon">▱</span><span class="tree-file-name">${node.name}</span><span class="tree-status ${node.status}">${node.status}</span>`;
            parent.append(label);
        }
    });
}

async function loadTree() {
    const response = await fetch("/api/tree");
    if (!response.ok) throw new Error("Unable to load videos.");

    treeContainer.replaceChildren();
    renderTree(await response.json());
}

async function loadJobs() {
    const response = await fetch("/api/jobs");
    const jobs = await response.json();
    jobsContainer.innerHTML = jobs.length ? jobs.map((job) => `<div class="list-group-item d-flex justify-content-between"><span class="text-break">${job.path}</span><span class="badge text-bg-${job.status === "failed" ? "danger" : "secondary"}">${job.status}</span></div>`).join("") : '<div class="text-muted">No queued videos.</div>';
}

document.querySelector("#queue-button").addEventListener("click", async () => {
    const paths = [...document.querySelectorAll(".video-check:checked")].map((input) => input.value);
    if (!paths.length) return showMessage("Select at least one video.", "warning");
    const response = await fetch("/api/queue", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({paths})});
    if (!response.ok) return showMessage((await response.json()).detail, "danger");
    showMessage(`${paths.length} video(s) added to the queue.`);
    await loadJobs();
    await loadTree();
});

loadTree().catch(() => showMessage("Unable to load videos.", "danger"));
loadJobs().catch(() => showMessage("Unable to load queue status.", "danger"));
setInterval(loadJobs, 3000);
