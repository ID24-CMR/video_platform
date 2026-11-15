document.addEventListener("DOMContentLoaded", function () {
    const video = document.getElementById("videoPlayer");
    const rewindButton = document.getElementById("rewindButton");
    const forwardButton = document.getElementById("forwardButton");

    if (!video || !rewindButton || !forwardButton) {
        return;
    }

    rewindButton.addEventListener("click", function () {
        video.currentTime = Math.max(0, video.currentTime - 10);
    });

    forwardButton.addEventListener("click", function () {
        if (Number.isFinite(video.duration)) {
            video.currentTime = Math.min(
                video.duration,
                video.currentTime + 10
            );
        }
    });
});