const panel = document.querySelector(".state-panel");
const title = document.getElementById("title");
const message = document.getElementById("message");
const retry = document.getElementById("retry");

async function startApplication() {
  panel.classList.remove("failed");
  retry.hidden = true;
  title.textContent = "Menyiapkan aplikasi";
  message.textContent = "Sedang memuat data klinik. Mohon tunggu sebentar...";

  try {
    const url = await window.__TAURI__.core.invoke("start_backend");
    window.location.replace(url);
  } catch (error) {
    panel.classList.add("failed");
    title.textContent = "Aplikasi belum siap";
    const detail = String(error || "").replace(/^.*?:\s*/, "").trim();
    const reason = detail ? ` Detail: ${detail}` : "";
    message.textContent = `Backend lokal gagal dijalankan.${reason} Log tersedia di folder data aplikasi: logs\\desktop_sidecar.log.`;
    retry.hidden = false;
  }
}

retry.addEventListener("click", startApplication);
startApplication();
