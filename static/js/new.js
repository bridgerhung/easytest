// const dropZone = document.getElementById("dropZone");
// const fileInput = document.getElementById("fileInput");
const submitButton = document.querySelector(".button"); // Existing submit button reference

const historyFileInput = document.getElementById("history-file");
const onlineInfoFileInput = document.getElementById("online-info-file");

// Disable submit button initially
submitButton.disabled = true;

let captchaVerified = false;
let captchaToken = "";

// Disable form submission initially
const form = document.querySelector(".upload-form");
// const submitButton = form.querySelector('button[type="submit"]'); // Removed duplicate declaration

window.onloadTurnstileCallback = function () {
  turnstile.render("#cf-turnstile", {
    sitekey: "0x4AAAAAAA3QtOGlz4UGnf74",
    callback: function (token) {
      console.log(`Challenge Success ${token}`);
      captchaVerified = true;
      captchaToken = token;
      submitButton.disabled = false; // Enable submit button after CAPTCHA success
    },
  });
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

/* Drag and Drop Functionality */

// Open file dialog on drop zone click
// dropZone.onclick = () => fileInput.click();

// Handle file input change
// fileInput.addEventListener("change", function (e) {
//   if (this.files && this.files[0]) {
//     if (!captchaVerified) {
//       alert("請先完成人機驗證 (CAPTCHA)");
//       return;
//     }
//     const formData = new FormData();
//     formData.append(
//       "history_file",
//       document.getElementById("history-file").files[0]
//     ); // Append EasyTest CSV file
//     formData.append(
//       "online_info_file",
//       document.getElementById("online-info-file").files[0]
//     ); // Append MyET XLSX file
//     formData.append("cf-turnstile-response", captchaToken); // Include CAPTCHA token

//     fetch("/new/upload", {
//       method: "POST",
//       body: formData,
//     })
//       .then((response) => {
//         if (!response.ok) {
//           throw new Error("Upload failed");
//         }
//         return response.blob();
//       })
//       .then((blob) => {
//         const url = window.URL.createObjectURL(blob);
//         const a = document.createElement("a");
//         a.href = url;
//         a.download =
//           document
//             .getElementById("history-file")
//             .files[0].name.replace(/\.[^/.]+$/, "") + "-count.xlsx";
//         document.body.appendChild(a);
//         a.click();
//         document.body.removeChild(a);
//         window.URL.revokeObjectURL(url);
//       })
//       .catch((error) => {
//         console.error("Error:", error);
//         alert("文件上傳失敗，請再試一次。");
//       });
//   }
// });

// Handle form submission
form.addEventListener("submit", function (e) {
  e.preventDefault(); // Prevent default form submission

  if (!captchaVerified) {
    alert("請先完成人機驗證 (CAPTCHA)");
    return;
  }

  const formData = new FormData();
  formData.append("history_file", historyFileInput.files[0]);
  formData.append("online_info_file", onlineInfoFileInput.files[0]);
  formData.append("cf-turnstile-response", captchaToken); // Include CAPTCHA token

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
});

// Remove drag-and-drop event listeners if not used
// ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
//   dropZone.addEventListener(eventName, preventDefaults, false);
//   document.body.addEventListener(eventName, preventDefaults, false);
// });

// function preventDefaults(e) {
//   e.preventDefault();
//   e.stopPropagation();
// }

// ["dragenter", "dragover"].forEach((eventName) => {
//   dropZone.addEventListener(eventName, highlight, false);
// });

// ["dragleave", "drop"].forEach((eventName) => {
//   dropZone.addEventListener(eventName, unhighlight, false);
// });

// function highlight() {
//   dropZone.classList.add("dragover");
// }

// function unhighlight() {
//   dropZone.classList.remove("dragover");
// }
