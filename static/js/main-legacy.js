const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const uploadForm = document.getElementById("uploadForm");

fileInput.addEventListener("change", function (e) {
  if (this.files && this.files[0]) {
    const formData = new FormData(uploadForm);

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
        a.download =
          this.files[0].name.replace(/\.[^/.]+$/, "") + "-count.xlsx";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("上傳失敗，請稍後再試");
      });
  }
});

dropZone.onclick = () => fileInput.click();

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

function openDisclaimer() {
  document.getElementById("disclaimerModal").style.display = "block";
}

function closeDisclaimer() {
  document.getElementById("disclaimerModal").style.display = "none";
}

window.onclick = function (event) {
  const modal = document.getElementById("disclaimerModal");
  if (event.target == modal) {
    modal.style.display = "none";
  }
};
