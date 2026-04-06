const submitButton = document.querySelector(".button");
const easytestFileInput = document.getElementById("easytest-file");
const myetFileInput = document.getElementById("myet-file");
const studentListFileInput = document.getElementById("student-list-file");
const form = document.querySelector(".upload-form");
const turnstileContainer = document.getElementById("cf-turnstile");
let turnstileWidgetId = null;

const showCaptcha = form?.dataset?.showCaptcha ?? "true";
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
  if (turnstileContainer && turnstileWidgetId === null && typeof turnstile !== "undefined") {
    const sitekey = turnstileContainer.dataset.sitekey;
    turnstileWidgetId = turnstile.render("#cf-turnstile", {
      sitekey,
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
  const easytestFile = easytestFileInput.files[0];
  const myetFile = myetFileInput.files[0];
  const studentListFile = studentListFileInput.files[0];

  const hasEasyTest = Boolean(easytestFile);
  const hasMyET = Boolean(myetFile);
  const hasStudentList = Boolean(studentListFile);

  if (!hasEasyTest && !hasMyET && !hasStudentList) {
    alert("請至少上傳 EasyTest 或 MyET 檔案。");
    return;
  }

  if (hasStudentList && !hasEasyTest && !hasMyET) {
    alert("不可只上傳學生名單，請至少再上傳 EasyTest 或 MyET 檔案。");
    return;
  }

  const formData = new FormData();
  if (easytestFile) {
    formData.append("easytest_file", easytestFile);
  }
  if (myetFile) {
    formData.append("myet_file", myetFile);
  }
  if (studentListFile) {
    formData.append("student_list_file", studentListFile);
  }

  if (window.captchaToken) {
    formData.append("cf-turnstile-response", window.captchaToken);
  }

  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        return response.text().then((text) => {
          let serverMessage = "文件上傳失敗";
          if (text) {
            try {
              const payload = JSON.parse(text);
              serverMessage = payload.error || serverMessage;
            } catch (_e) {
              serverMessage = text;
            }
          }

          const error = new Error(serverMessage);
          error.status = response.status;
          throw error;
        });
      }
      return response.blob();
    })
    .then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "result.xlsx";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      delete window.captchaToken;
    })
    .catch((error) => {
      console.error("Upload error:", error);
      alert(buildUploadErrorMessage(error));
    });
}

function buildUploadErrorMessage(error) {
  const rawMessage = String(error?.message || "").trim();
  const status = error?.status;

  if (rawMessage.includes("EasyTest 檔案欄位缺少")) {
    return [
      "EasyTest 檔案格式不符合需求。",
      `伺服器訊息：${rawMessage}`,
      "請確認：",
      "1. 檔案為 EasyTest 匯出的 history*.csv",
      "2. 第一列標題包含「使用者帳號」與「總時數」",
      "3. 沒有手動刪除或改名欄位",
    ].join("\n");
  }

  if (status === 413) {
    return `檔案太大，無法上傳。\n伺服器訊息：${rawMessage || "請縮小檔案後再試"}`;
  }

  if (rawMessage) {
    return `文件上傳失敗。\n伺服器訊息：${rawMessage}`;
  }

  return "文件上傳失敗，請再試一次。";
}

document.getElementById("year").textContent = new Date().getFullYear();
