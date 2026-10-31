const treeContainer = document.querySelector("#transcription-tree");
const title = document.querySelector("#file-title");
const content = document.querySelector("#file-content");

function renderTree(nodes, parent = treeContainer) {
    nodes.forEach((node) => {
        if (node.type === "folder") {
            const details = document.createElement("details");
            details.className = "list-group-item";
            details.innerHTML = `<summary class="fw-semibold">${node.name}</summary>`;
            renderTree(node.children, details);
            parent.append(details);
        } else {
            const button = document.createElement("button");
            button.className = "list-group-item list-group-item-action text-start text-break";
            button.textContent = node.path;
            button.addEventListener("click", () => loadFile(node.path));
            parent.append(button);
        }
    });
}

async function loadFile(path) {
    const response = await fetch(`/api/transcriptions/${path.split("/").map(encodeURIComponent).join("/")}`);
    title.textContent = path;
    content.textContent = response.ok ? await response.text() : "Unable to load this transcription.";
}

fetch("/api/transcriptions").then((response) => response.json()).then(renderTree);
