(() => {
  const $ = (id) => document.getElementById(id);
  const text = $("text"), go = $("go"), count = $("count"), err = $("error"), res = $("result");

  text.addEventListener("input", () => (count.textContent = text.value.length));
  document.querySelectorAll(".chip").forEach((c) =>
    c.addEventListener("click", () => {
      text.value = c.textContent;
      count.textContent = text.value.length;
      analyze();
    })
  );
  go.addEventListener("click", analyze);
  text.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) analyze();
  });

  function showError(msg) {
    err.textContent = msg;
    err.hidden = false;
    res.hidden = true;
  }

  async function analyze() {
    err.hidden = true;
    const value = text.value.trim();
    if (!value) return showError("Введіть текст для аналізу.");
    go.disabled = true;
    go.textContent = "Аналізую…";
    try {
      const r = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: value }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) return showError(data.error || "Сталася помилка. Спробуйте ще раз.");
      render(data);
    } catch (e) {
      showError("Не вдалося зв'язатися із сервером. Перевірте з'єднання.");
    } finally {
      go.disabled = false;
      go.textContent = "Визначити емоцію";
    }
  }

  function render(d) {
    res.dataset.emotion = d.emotion;
    $("emoji").textContent = d.emoji;
    $("label").textContent = d.label;
    $("conf").textContent = "Впевненість моделі: " + Math.round(d.confidence * 100) + "%";
    $("headline").textContent = d.headline;
    $("advice").textContent = d.advice;
    $("quote").textContent = "«" + d.quote + "»";
    const tr = $("translated");
    if (d.translated_text) {
      tr.textContent = "Переклад для моделі: " + d.translated_text;
      tr.hidden = false;
    } else tr.hidden = true;

    const bars = $("bars");
    bars.replaceChildren();
    d.scores.forEach((s) => {
      const li = document.createElement("li");
      const name = document.createElement("span");
      name.textContent = s.emoji + " " + s.label;
      const track = document.createElement("div");
      track.className = "track";
      const fill = document.createElement("div");
      fill.className = "fill";
      fill.style.width = "0%";
      track.appendChild(fill);
      const pct = document.createElement("span");
      pct.className = "pct";
      pct.textContent = Math.round(s.score * 100) + "%";
      li.append(name, track, pct);
      bars.appendChild(li);
      requestAnimationFrame(() => (fill.style.width = Math.max(s.score * 100, 1) + "%"));
    });
    res.hidden = false;
    res.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
})();
