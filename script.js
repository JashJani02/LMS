// Load videos
fetch("/videos")
.then(res => res.json())
.then(data => {
    const container = document.getElementById("videos");

    data.forEach(v => {
        const vid = document.createElement("video");
        vid.src = v.path;
        vid.controls = true;
        vid.width = 300;

        vid.onended = () => {
            fetch("/watch/" + v.id, { method: "POST" })
                .then(() => loadProgress());
        };

        container.appendChild(vid);
    });
});


// Load progress
function loadProgress() {
    fetch("/progress")
    .then(res => res.json())
    .then(data => {
        document.getElementById("progress").innerText =
            "Completion: " + data.progress.toFixed(2) + "%";
    });
}

loadProgress();


// Certificate
function getCertificate() {
    window.location.href = "/certificate";
}