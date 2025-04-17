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
      console.error("Upload error:", error);
      alert("文件上傳失敗，請再試一次。原因是：" + error.message);
    });
}

initializeDragAndDrop();
// Update footer year

/* Disclaimer Modal Functionality */
const disclaimerModal = document.getElementById("disclaimerModal");

function openDisclaimer(event) {
  event.preventDefault();
  disclaimerModal.style.display = "block";
}

function closeDisclaimer() {
  disclaimerModal.style.display = "none";
}

/* Image Modal Functionality */
const imageModal = document.getElementById("imageModal");
const modalImage = document.getElementById("modalImage");
const enlargeableImages = document.querySelectorAll(
  ".enlargeable, .images img, .image-container img"
);

/* Open Image Modal */
enlargeableImages.forEach((img) => {
  img.addEventListener("click", () => {
    imageModal.style.display = "flex";
    modalImage.src = img.src;
    modalImage.alt = img.alt;
  });
});

/* Close Image Modal */
function closeImageModal() {
  imageModal.style.display = "none";
}

/* Close modals when clicking outside */
window.onclick = function (event) {
  if (event.target === disclaimerModal) {
    closeDisclaimer();
  }
  if (event.target === imageModal) {
    closeImageModal();
  }
};

// Close the disclaimer when clicking outside the content
window.addEventListener("click", (event) => {
  if (event.target === disclaimerModal) {
    closeDisclaimer();
  }
});
