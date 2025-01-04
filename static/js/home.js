// Update footer year
document.getElementById("year").textContent = new Date().getFullYear();

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
