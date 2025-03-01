document.getElementById("year").textContent = new Date().getFullYear();
const dropZone = document.querySelector(".upload-zone");
const fileInput = document.getElementById("fileInput");

window.onloadTurnstileCallback = function () {
  if (document.getElementById("cf-turnstile")) {
    turnstile.render("#cf-turnstile", {
      sitekey: "0x4AAAAAAA3QtOGlz4UGnf74",
      callback: function (token) {
        window.captchaToken = token;
      },
    });
  }
};

function initializeDragAndDrop() {
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });
  ["dragenter", "dragover"].forEach((eventName) =>
    dropZone.addEventListener(eventName, highlight, false)
  );
  ["dragleave", "drop"].forEach((eventName) =>
    dropZone.addEventListener(eventName, unhighlight, false)
  );
  dropZone.addEventListener("drop", handleDrop, false);
}

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

function highlight(e) {
  dropZone.classList.add("dragover");
}

function unhighlight(e) {
  dropZone.classList.remove("dragover");
}

function handleDrop(e) {
  const file = e.dataTransfer.files[0];
  if (file) handleFileUpload(file);
}

dropZone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) handleFileUpload(e.target.files[0]);
});

function handleFileUpload(file) {
  const formData = new FormData();
  formData.append("file", file);
  if (window.captchaToken) {
    formData.append("cf-turnstile-response", window.captchaToken);
    delete window.captchaToken;
  }

  fetch("/legacy/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) throw new Error("Upload failed");
      return response.blob();
    })
    .then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name.replace(/\.[^/.]+$/, "") + "-count.xlsx";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("文件上傳失敗，請再試一次。");
    });
}

initializeDragAndDrop();
