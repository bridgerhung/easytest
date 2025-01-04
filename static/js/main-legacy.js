const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const uploadForm = document.getElementById("uploadForm");
const selectBtn = document.querySelector(".select-btn");

/* Image Modal Elements */
const imageModal = document.getElementById("imageModal");
const modalImage = document.getElementById("modalImage");
const enlargeableImages = document.querySelectorAll(".enlargeable");

// Handle file selection and upload
function handleFileUpload(file) {
  const formData = new FormData(uploadForm);
  formData.set("file", file); // Ensure only one file is set

  fetch("/legacy/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      const contentType = response.headers.get("content-type");
      if (!response.ok) {
        if (contentType && contentType.includes("application/json")) {
          return response.json().then((data) => {
            throw new Error(data.error || "上傳失敗");
          });
        }
        throw new Error("上傳失敗");
      }
      if (contentType && contentType.includes("application/json")) {
        return response.json();
      }
      return response.blob();
    })
    .then((data) => {
      if (data instanceof Blob) {
        const url = window.URL.createObjectURL(data);
        const a = document.createElement("a");
        a.href = url;
        a.download = file.name.replace(/\.[^/.]+$/, "") + "-count.xlsx";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else if (data.download_url) {
        window.location.href = data.download_url;
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert(error.message);
    });
}

// File input change event
fileInput.addEventListener("change", function (e) {
  if (this.files && this.files[0]) {
    handleFileUpload(this.files[0]);
  }
});

// Click event for the select button
selectBtn.addEventListener("click", function (e) {
  e.stopPropagation(); // Prevent the event from bubbling up to dropZone
  fileInput.click();
});

// Drag and drop event listeners
["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, highlight, false);
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
  dropZone.classList.add("dragover");
}

function unhighlight(e) {
  dropZone.classList.remove("dragover");
}

// Drop event handler
dropZone.addEventListener("drop", function (e) {
  const dt = e.dataTransfer;
  const file = dt.files[0];
  handleFileUpload(file);
});

/* Image Modal Functionality */

// Open Image Modal
enlargeableImages.forEach((img) => {
  img.addEventListener("click", () => {
    imageModal.style.display = "flex";
    modalImage.src = img.src;
    modalImage.alt = img.alt;
  });
});

// Close Image Modal
function closeImageModal() {
  imageModal.style.display = "none";
}

// Modal controls for disclaimer
function openDisclaimer(event) {
  event.preventDefault();
  document.getElementById("disclaimerModal").style.display = "block";
}

function closeDisclaimer() {
  document.getElementById("disclaimerModal").style.display = "none";
}

window.onclick = function (event) {
  const disclaimerModal = document.getElementById("disclaimerModal");
  const imageModalTarget = document.getElementById("imageModal");
  if (event.target == disclaimerModal) {
    closeDisclaimer();
  }
  if (event.target == imageModalTarget) {
    closeImageModal();
  }
};