// const dropZone = document.getElementById("dropZone");
// const fileInput = document.getElementById("fileInput");
const submitButton = document.querySelector(".button"); // Existing submit button reference
const historyFileInput = document.getElementById("history-file");
const onlineInfoFileInput = document.getElementById("online-info-file");

// 初始化時根據後端傳來的 show_captcha 決定按鈕狀態
const showCaptcha = "{{ show_captcha|lower }}"; // 从 Flask 模板获取（注意大小写）
submitButton.disabled = showCaptcha === "true"; // 若需要 CAPTCHA，按鈕初始禁用

// 表單元素
const form = document.querySelector(".upload-form");

// Turnstile 渲染函數，只有在需要 CAPTCHA 時執行
window.onloadTurnstileCallback = function () {
  if (document.getElementById("cf-turnstile")) { // 檢查是否存在 CAPTCHA 容器
    turnstile.render("#cf-turnstile", {
      sitekey: "0x4AAAAAAA3QtOGlz4UGnf74",
      callback: function (token) {
        console.log(`Challenge Success ${token}`);
        submitButton.disabled = false; // 啟用提交按鈕
        handleFormSubmit(token); // 驗證成功後直接提交
      },
    });
  }
};

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
function openImageModal(src, alt) {
  const imageModal = document.getElementById("imageModal");
  const modalImage = document.getElementById("modalImage");
  modalImage.src = src;
  modalImage.alt = alt;
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

// Handle form submission
form.addEventListener("submit", function (e) {
  e.preventDefault(); // Prevent default form submission
  handleFormSubmit(); // 直接處理提交
});

// 處理表單提交的函數
function handleFormSubmit(token = null) {
  const formData = new FormData();
  formData.append("history_file", historyFileInput.files[0]);
  formData.append("online_info_file", onlineInfoFileInput.files[0]);
  if (token) {
    formData.append("cf-turnstile-response", token); // 僅在首次驗證時附加 token
  }

  fetch("/new/upload", {
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
      a.download =
        historyFileInput.files[0].name.replace(/\.[^/.]+$/, "") + "-count.xlsx";
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
