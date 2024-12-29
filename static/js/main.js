document.getElementById("year").textContent = new Date().getFullYear();

function openModal(src, alt) {
  document.getElementById("myModal").style.display = "flex";
  document.getElementById("img01").src = src;
}

function closeModal() {
  document.getElementById("myModal").style.display = "none";
}

// Close modal when clicking outside of the image
window.onclick = function (event) {
  if (event.target == document.getElementById("myModal")) {
    closeModal();
  }
  if (event.target == document.getElementById("disclaimerModal")) {
    closeDisclaimer();
  }
};

function openDisclaimer(event) {
  event.preventDefault();
  document.getElementById("disclaimerModal").style.display = "block";
}

function closeDisclaimer() {
  document.getElementById("disclaimerModal").style.display = "none";
}
