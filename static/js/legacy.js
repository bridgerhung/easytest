document.getElementById("year").textContent = new Date().getFullYear();
const dropZone = document.querySelector(".upload-zone");
const fileInput = document.getElementById("fileInput");
const imageModal = document.getElementById("imageModal");
const modalImage = document.getElementById("modalImage");

// Turnstile 渲染函數，只有在需要 CAPTCHA 時執行
window.onloadTurnstileCallback = function () {
  if (document.getElementById("cf-turnstile")) { // 檢查是否存在 CAPTCHA 容器
    turnstile.render("#cf-turnstile", {
      sitekey: "0x4AAAAAAA3QtOGlz4UGnf74",
      callback: function (token) {
        console.log(`Challenge Success ${token}`);
        handleFileUpload(fileInput.files[0], token); // 驗證成功後立即上傳
      },
    });
  }
};

// 初始化拖放功能
function initializeDragAndDrop() {
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, highlight, false);
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, unhighlight, false);
  });

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
  e.preventDefault();
  e.stopPropagation();
  const dt = e.dataTransfer;
  const file = dt.files[0];
  if (!file) return;

  handleFileUpload(file); // 直接處理檔案上傳
}

// 點擊上傳區域時觸發檔案選取
dropZone.addEventListener("click", () => {
  fileInput.click(); // 直接觸發檔案選擇，無需檢查 CAPTCHA
});

// 處理檔案選取變更
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) {
    handleFileUpload(e.target.files[0]); // 直接處理檔案上傳
  }
});

// 初始化拖放
initializeDragAndDrop();

// 開啟圖片模態框
function openImageModal(src) {
  const imageModal = document.getElementById("imageModal");
  const modalImage = document.getElementById("modalImage");
  modalImage.src = src;
  imageModal.style.display = "flex";
}

// 關閉圖片模態框
function closeImageModal() {
  const imageModal = document.getElementById("imageModal");
  imageModal.style.display = "none";
}

// 點擊模態框外部區域關閉
window.onclick = function (event) {
  if (event.target == imageModal) {
    imageModal.style.display = "none";
  }
};

// 處理檔案上傳
function handleFileUpload(file, token = null) {
  const formData = new FormData();
  formData.append("file", file);
  if (token) {
    formData.append("cf-turnstile-response", token); // 僅在首次驗證時附加 token
  }

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
