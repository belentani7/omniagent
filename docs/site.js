(() => {
  const year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());

  const button = document.querySelector("[data-copy-url]");
  const status = document.querySelector(".copy-status");
  if (!button || !status) return;

  button.addEventListener("click", async () => {
    const url = button.dataset.copyUrl;
    if (!url) return;
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard API unavailable");
      await navigator.clipboard.writeText(url);
      status.textContent = "Enlace copiado al portapapeles.";
    } catch {
      status.textContent = `Copia este enlace: ${url}`;
    }
  });
})();
