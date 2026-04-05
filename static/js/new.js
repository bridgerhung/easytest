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
        return response
          .json()
          .then((payload) => {
            throw new Error(payload.error || "文件上傳失敗");
          })
          .catch(() => {
            throw new Error("文件上傳失敗");
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
      alert("文件上傳失敗，請再試一次。原因是：" + error.message);
    });
}

document.getElementById("year").textContent = new Date().getFullYear();
