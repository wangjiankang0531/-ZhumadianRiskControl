export type UploadPhase = "selected" | "uploading" | "success" | "failed";
export type UploadRecord = { uid: number; name: string; phase: UploadPhase; token: number };
export function attachmentUrl(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0 && value.length <= 16384 && !/[\u0000-\u001f\u007f;]/.test(value);
}
export function confirmedUpload(reply: unknown): string {
  const value = reply as { code?: unknown; data?: { url?: unknown } } | null;
  if (!value || value.code !== 0 || !attachmentUrl(value.data?.url)) throw Error("ATTACHMENT_UPLOAD_NOT_CONFIRMED");
  return value.data!.url as string;
}
/** One component's selection/request lifecycle. No remote-delete operation and no persistent credentials. */
export class AttachmentUploadState {
  private records = new Map<number, UploadRecord>();
  private sequence = 0;
  private closed = false;
  constructor(private changed: () => void) {}
  select(uid: number, name: string): void {
    if (this.closed || this.records.has(uid)) return;
    this.records.set(uid, { uid, name, phase: "selected", token: ++this.sequence }); this.changed();
  }
  begin(uid: number, name: string): number {
    if (this.closed) throw Error("ATTACHMENT_VIEW_CLOSED");
    const token = ++this.sequence;
    this.records.set(uid, { uid, name, phase: "uploading", token }); this.changed(); return token;
  }
  finish(uid: number, token: number, success: boolean): boolean {
    const value = this.records.get(uid);
    if (this.closed || !value || value.token !== token) return false;
    value.phase = success ? "success" : "failed"; this.changed(); return true;
  }
  remove(uid: number): void { this.records.delete(uid); this.changed(); }
  reset(): void { this.records.clear(); this.changed(); }
  dispose(): void { this.closed = true; this.reset(); }
  get disposed(): boolean { return this.closed; }
  get busy(): boolean { return [...this.records.values()].some(x => x.phase === "selected" || x.phase === "uploading"); }
  get failures(): UploadRecord[] { return [...this.records.values()].filter(x => x.phase === "failed").map(x => ({ ...x })); }
}
