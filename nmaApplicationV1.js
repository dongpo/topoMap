const apiRoot = new URL(document.querySelector('meta[name="nma-api-root"]')?.content || "./api/", document.baseURI);
const runtimeState = document.querySelector("#runtime-state");
const runtimeLabel = document.querySelector("#runtime-label");

async function inspectRuntime() {
  try {
    const response = await fetch(new URL("nma/runtime", apiRoot), {headers: {Accept: "application/json"}});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const expected = ["school", "road", "build"];
    const domains = Array.isArray(payload.domains) ? payload.domains : [];
    if (payload.schema !== "nma.unified-runtime-capabilities/1.0" || expected.some((domain) => !domains.includes(domain))) {
      throw new Error("runtime capability contract mismatch");
    }
    runtimeState.classList.add("is-ready");
    runtimeLabel.textContent = "NMA Runtime 已連線 · 3 個工作可用";
  } catch (error) {
    runtimeState.classList.add("is-offline");
    runtimeLabel.textContent = "未連線本機 Runtime · 操作頁會明確停止";
    runtimeState.title = String(error);
  }
}

inspectRuntime();
