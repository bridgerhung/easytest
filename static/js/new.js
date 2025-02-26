const submitButton = document.querySelector(".button");
const historyFileInput = document.getElementById("history-file");
const onlineInfoFileInput = document.getElementById("online-info-file");

// 初始化時根據後端傳來的 show_captcha 決定按鈕狀態
const showCaptcha = "{{ show_captcha|lower }}";
submitButton.disabled = showCaptcha === "true";
console.log("Initial showCaptcha:", showCaptcha);

// 表單元素
const form = document.querySelector(".upload-form");

// Turnstile 渲染函數，只有在需要 CAPTCHA 時執行
window.onloadTurnstileCallback = function () {
  if (document.getElementById("cf-turnstile")) {
    turnstile.render("#cf-turnstile", {
      sitekey: "0x4AAAAAAA3QtOGlz4UGnf74",
      callback: function (token) {
        console.log(`Challenge Success ${token}`);
        submitButton.disabled = false;
        window.captchaToken = token;
        console.log("CAPTCHA verified, button enabled, token stored");
      },
    });
  } else {
    console.log("No CAPTCHA container found, assuming session verified");
  }
};

// Handle form submission
form.addEventListener("submit", function (e) {
  e.preventDefault();
  console.log("Form submit event triggered by user");
  handleFormSubmit();
});

// 處理表單提交的函數
function handleFormSubmit() {
  console.log("handleFormSubmit called");

  if (!historyFileInput.files[0] || !onlineInfoFileInput.files[0]) {
    console.log("Files missing:", {
      history: historyFileInput.files[0],
      online: onlineInfoFileInput.files[0],
    });
    alert("請選擇兩個檔案後再提交！");
    return;
  }

  const formData = new FormData();
  formData.append("history_file", historyFileInput.files[0]);
  formData.append("online_info_file", onlineInfoFileInput.files[0]);
  if (window.captchaToken) {
    formData.append("cf-turnstile-response", window.captchaToken);
    console.log("Appending CAPTCHA token:", window.captchaToken);
    delete window.captchaToken;
  } else {
    console.log("No CAPTCHA token, relying on session");
  }

  fetch("/new/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      console.log("Response status:", response.status);
      if (!response.ok) {
        return response.text().then((text) => {
          throw new Error(`Upload failed: ${text}`);
        });
      }
      return response.blob();
    })
    .then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = historyFileInput.files[0].name.replace(/\.[^/.]+$/, "") + "-count.xlsx";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      console.log("File downloaded successfully");
    })
    .catch((error) => {
      console.error("Upload error:", error);
      alert("文件上傳失敗，請再試一次。原因是：" + error.message);
    });
}

// 其他功能保持不變
document.getElementById("year").textContent = new Date().getFullYear();
function openDisclaimer(event) {
  event.preventDefault();
  const disclaimerModal = document.getElementById("disclaimerModal");
  disclaimerModal.style.display = "flex";
}
function closeDisclaimer() {
  const disclaimerModal = document.getElementById("disclaimerModal");
  disclaimerModal.style.display = "none";
}
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
window.addEventListener("click", function (event) {
  const disclaimerModal = document.getElementById("disclaimerModal");
  const imageModal = document.getElementById("imageModal");
  if (event.target === disclaimerModal) closeDisclaimer();
  if (event.target === imageModal) closeImageModal();
});
