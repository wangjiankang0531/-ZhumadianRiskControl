/** Adapt original native file images to this project's API mount; preserve other sources. */
export function projectAvatarImageSource(value: unknown, apiPrefix: unknown, pageOrigin = ""): string {
  if (typeof value !== "string") return "";
  const source = value.trim();
  if (!source || typeof apiPrefix !== "string") return source;
  const base = apiPrefix.trim().replace(/\/+$/, "");
  if (base.includes("//") || !/^\/[A-Za-z0-9_/-]+\/api$/.test(base)) return source;
  let nativePath = source;
  if (/^https?:\/\//.test(source) || source.startsWith("//")) {
    try {
      const parsed = new URL(source, pageOrigin);
      if (parsed.origin !== pageOrigin || parsed.username || parsed.password) return source;
      nativePath = parsed.pathname + parsed.search + parsed.hash;
    } catch { return source; }
  }
  return nativePath.startsWith("/api/file/") ? base + "/jnpf" + nativePath.slice(4) : source;
}
