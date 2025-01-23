const dropZone = document.querySelector(".upload-zone");
const fileInput = document.getElementById("fileInput");
const submitButton = document.querySelector(".button");
let captchaVerified = false;
let captchaToken = "";

// Initialize Turnstile on page load
window.onloadTurnstileCallback = function () {
  turnstile.render("#cf-turnstile", {
    sitekey: "0x4AAAAAAA3QtOGlz4UGnf74",
    callback: function (token) {
      captchaVerified = true;
      captchaToken = token;
      submitButton.disabled = false; // Enable submit button after CAPTCHA success
    },
  });
};

// Handle drag-and-drop functionality
function initializeDragAndDrop() {
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add("dragover"), false);
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove("dragover"), false);
  });

  dropZone.addEventListener("drop", handleDrop, false);
}

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

function handleDrop(e) {
  const dt = e.dataTransfer;
  const file = dt.files[0];
  if (!file) return;

  handleFileUpload(file);
}

// Handle file selection and upload
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) {
    handleFileUpload(e.target.files[0]);
  }
});

dropZone.addEventListener("click", () => {
  if (!captchaVerified) {
    alert("請先完成人機驗證 (CAPTCHA)");
    return;
  }
  fileInput.click();
});

function handleFileUpload(file) {
  if (!captchaVerified) {
    alert("請先完成人機驗證 (CAPTCHA)");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("cf-turnstile-response", captchaToken);

  fetch("/legacy/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Upload failed");
      }
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

// Update footer year
document.getElementById("year").textContent = new Date().getFullYear();

/* Disclaimer Modal Functionality */
function openDisclaimer(event) {
  event.preventDefault();
  const disclaimerModal = document.getElementById("disclaimerModal");
  disclaimerModal.style.display = "flex";
}

function closeDisclaimer() {
  const disclaimerModal = document.getElementById("disclaimerModal");
  disclaimerModal.style.display = "none";
}

/* Image Modal Functionality */
function openImageModal(src) {
  const imageModal = document.getElementById("imageModal");
  const modalImage = document.getElementById("modalImage");
  modalImage.src = src;
  imageModal.style.display = "flex";
}

function closeImageModal() {
  const imageModal = document.getElementById("imageModal");
  imageModal.style.display = "none";
}

/* Close modals when clicking outside */
window.addEventListener("click", function (event) {
  const disclaimerModal = document.getElementById("disclaimerModal");
  const imageModal = document.getElementById("imageModal");

  if (event.target === disclaimerModal) {
    closeDisclaimer();
  }

  if (event.target === imageModal) {
    closeImageModal();
  }
});

// Initialize drag-and-drop functionality
initializeDragAndDrop();
