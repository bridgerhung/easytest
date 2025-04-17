const submitButton = document.querySelector(".button");
const historyFileInput = document.getElementById("history-file");
const onlineInfoFileInput = document.getElementById("online-info-file");
const form = document.querySelector(".upload-form");

const showCaptcha = "{{ show_captcha|lower }}";
submitButton.disabled = showCaptcha === "true";
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

window.onloadTurnstileCallback = function () {
  if (document.getElementById("cf-turnstile")) {
    turnstile.render("#cf-turnstile", {
      sitekey: "0x4AAAAAAA3QtOGlz4UGnf74",
      callback: function (token) {
        submitButton.disabled = false;
        window.captchaToken = token;
      },
    });
  }
};

form.addEventListener("submit", function (e) {
  e.preventDefault();
  handleFormSubmit();
});

function handleFormSubmit() {
  if (!historyFileInput.files[0] || !onlineInfoFileInput.files[0]) {
    alert("請選擇兩個檔案後再提交！");
    return;
  }

  const formData = new FormData();
  formData.append("history_file", historyFileInput.files[0]);
  formData.append("online_info_file", onlineInfoFileInput.files[0]);
  if (window.captchaToken) {
    formData.append("cf-turnstile-response", window.captchaToken);
    delete window.captchaToken;
  }

  fetch("/new/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok)
        return response.text().then((text) => {
          throw new Error(text);
        });
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
      console.error("Upload error:", error);
      alert("文件上傳失敗，請再試一次。原因是：" + error.message);
    });
}

document.getElementById("year").textContent = new Date().getFullYear();
