const submitButton = document.querySelector(".button");
const historyFileInput = document.getElementById("history-file");
const onlineInfoFileInput = document.getElementById("online-info-file");
let captchaVerified = false;
let captchaToken = "";

// Initialize Turnstile on page load
window.onloadTurnstileCallback = function () {
  turnstile.render("#cf-turnstile", {
    sitekey: "0x4AAAAAAA3QtOGlz4UGnf74",
    callback: function (token) {
      captchaVerified = true;
      captchaToken = token;
      submitButton.disabled = false;
    },
  });
};

// Form submission handler
const form = document.querySelector(".upload-form");
form.addEventListener("submit", function (e) {
  e.preventDefault(); // Prevent default form submission

  if (!captchaVerified) {
    alert("請先完成人機驗證 (CAPTCHA)");
    return;
  }

  const formData = new FormData();
  formData.append("history_file", historyFileInput.files[0]);
  formData.append("online_info_file", onlineInfoFileInput.files[0]);
  formData.append("cf-turnstile-response", captchaToken);

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
        historyFileInput.files[0].name.replace(/\.[^/.]+$/, "") + "-merged.xlsx";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("文件上傳失敗，請再試一次。");
    });
});

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
