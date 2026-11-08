const treeContainer = document.querySelector("#transcription-tree");
const title = document.querySelector("#file-title");
const content = document.querySelector("#file-content");

function renderTree(nodes, parent = treeContainer) {
    nodes.forEach((node, index) => {
        const branch = index === nodes.length - 1 ? "└── " : "├── ";
        if (node.type === "folder") {
            const details = document.createElement("details");
            const summary = document.createElement("summary");
            summary.innerHTML = `<span class="tree-branch">${branch}</span><span class="tree-folder-icon">▰</span><span>${node.name}</span>`;
            details.append(summary);
            const children = document.createElement("div");
            children.className = "tree-children";
            renderTree(node.children, children);
            details.append(children);
            parent.append(details);
        } else {
            const button = document.createElement("button");
            button.className = "tree-file";
            button.innerHTML = `<span class="tree-branch">${branch}</span><span class="tree-file-icon">▱</span><span class="tree-file-name">${node.name}</span>`;
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
