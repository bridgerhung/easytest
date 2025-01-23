// Select necessary DOM elements
const submitButton = document.querySelector(".btn");
const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
submitButton.disabled = true;

let captchaVerified = false;

// CAPTCHA success callback
function onCaptchaSuccess(token) {
  console.log("CAPTCHA 驗證成功，令牌：", token);
  captchaVerified = true;
  submitButton.disabled = false; // Enable button after CAPTCHA verification
}

// Handle drag-and-drop functionality
function initializeDragAndDrop() {
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults, false);
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

// File selection event
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) {
    handleFileUpload(e.target.files[0]);
  }
});

// Click to open file dialog
submitButton.addEventListener("click", () => {
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
      a.download = file.name.replace(/\.[^/.]+$/, "") + "-processed.xlsx";
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

/* Disclaimer Modal */
function openDisclaimer(event) {
  event.preventDefault();
  const disclaimerModal = document.getElementById("disclaimerModal");
  disclaimerModal.style.display = "flex";
}

function closeDisclaimer() {
  const disclaimerModal = document.getElementById("disclaimerModal");
  disclaimerModal.style.display = "none";
}

/* Image Modal */
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

/* Close modals on outside click */
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
