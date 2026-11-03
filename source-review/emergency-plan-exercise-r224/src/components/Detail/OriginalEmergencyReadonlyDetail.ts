export type DetailKind = "plan" | "exercise";
export type DetailView = { loading: boolean; error: string; data: Record<string, any> | null; users: { id: string; realName: string }[]; namesPending: boolean; namesUnavailable: boolean };
export const emptyDetailView = (): DetailView => ({ loading: false, error: "", data: null, users: [], namesPending: false, namesUnavailable: false });
const record = (v: unknown): v is Record<string, any> => !!v && typeof v === "object" && !Array.isArray(v);
const id = (v: unknown): v is string => typeof v === "string" && v.length > 0 && v.length <= 128 && v.trim() === v && !/[\u0000-\u0020\u007f]/.test(v);
const directoryId = (v: string) => /^[A-Za-z0-9_-]{1,128}$/.test(v);
const planLists = ["emergencyExpertIdList", "emergencyExpertList", "emergencyGoodsManageIdList", "emergencyGoodsManageList", "emergencyTeamIdList", "emergencyTeamList", "emergencyPlanCompanyList", "emergencyPlanDeputyHeadList", "emergencyPlanOthermemberList", "fileList"];
export function checkedDetail(reply: unknown, expected: string, kind: DetailKind): Record<string, any> {
  if (!record(reply) || reply.code !== 0 || !record(reply.data) || !id(reply.data.id) || reply.data.id !== expected) throw Error("DETAIL_NOT_CONFIRMED");
  const result = { ...reply.data };
  for (const key of kind === "plan" ? planLists : ["fileList"]) {
    const rows = result[key] ?? [];
    if (!Array.isArray(rows) || rows.some(value => key.endsWith("IdList") ? !id(value) : !record(value))) throw Error("DETAIL_LIST_INVALID");
    result[key] = rows.map(value => record(value) ? { ...value } : value);
  }
  if (kind === "exercise" && result.participants != null && typeof result.participants !== "string") throw Error("DETAIL_PARTICIPANTS_INVALID");
  return result;
}
export function participantScope(data: Record<string, any>): { organizeId: string; ids: string[] } | null {
  const participants = typeof data.participants === "string" ? [...new Set(data.participants.split(",").map(v => v.trim()).filter(Boolean))] : [];
  const organizations = [...new Set([data.organizeDepartment, data.cooperatingUnit].flatMap(v => typeof v === "string" ? v.split(",").map(x => x.trim()).filter(Boolean) : []))];
  if (!participants.length || participants.length > 512 || !organizations.length || organizations.length > 16 || !participants.every(directoryId) || !organizations.every(directoryId)) return null;
  return { organizeId: organizations.join(","), ids: participants };
}
/** Original authenticated APIs only. Names supplement the detail and cannot prevent the record from displaying. */
export class EmergencyReadonlyDetail {
  private epoch = 0;
  private disposed = false;
  private view: DetailView = emptyDetailView();
  private labels: Promise<void> = Promise.resolve();
  constructor(private kind: DetailKind, private fetch: (p: { id: string }) => Promise<unknown>, private changed: (v: DetailView) => void,
    private names?: (p: { organizeId: string; ids: string }) => Promise<unknown>, private labelDeadlineMillis = 5000) {}
  private publish(patch: Partial<DetailView>): void { this.view = { ...this.view, ...patch }; this.changed({ ...this.view, users: [...this.view.users] }); }
  private current(epoch: number): boolean { return !this.disposed && epoch === this.epoch; }
  async load(value: unknown): Promise<boolean> {
    if (this.disposed) return false;
    const epoch = ++this.epoch;
    this.labels = Promise.resolve();
    this.publish({ ...emptyDetailView(), loading: true });
    if (!id(value)) { this.publish({ loading: false, error: "未指定有效记录，请返回列表重新选择。" }); return false; }
    let data: Record<string, any>;
    try { data = checkedDetail(await this.fetch({ id: value }), value, this.kind); }
    catch { if (this.current(epoch)) this.publish({ loading: false, error: "详情未取得或数据不完整，请重试。" }); return false; }
    if (!this.current(epoch)) return false;
    this.publish({ loading: false, error: "", data });
    if (this.kind === "exercise" && data.participants) this.labels = this.supplement(epoch, data);
    return true;
  }
  private async supplement(epoch: number, data: Record<string, any>): Promise<void> {
    const scope = participantScope(data);
    if (!scope || !this.names) { if (this.current(epoch)) this.publish({ namesUnavailable: true }); return; }
    this.publish({ namesPending: true });
    const users = new Map<string, { id: string; realName: string }>();
    const end = Date.now() + this.labelDeadlineMillis;
    let failed = false;
    try {
      for (let offset = 0; offset < scope.ids.length; offset += 50) {
        if (!this.current(epoch)) return;
        const wanted = scope.ids.slice(offset, offset + 50), left = end - Date.now();
        if (left <= 0) throw Error("DETAIL_NAMES_TIMEOUT");
        let timer: ReturnType<typeof setTimeout> | undefined;
        let reply: unknown;
        try { reply = await Promise.race([this.names({ organizeId: scope.organizeId, ids: wanted.join(",") }), new Promise((_, reject) => { timer = setTimeout(() => reject(Error("DETAIL_NAMES_TIMEOUT")), left); })]); }
        finally { if (timer) clearTimeout(timer); }
        if (!this.current(epoch)) return;
        if (!record(reply) || reply.code !== 0 || !Array.isArray(reply.data)) throw Error("DETAIL_NAMES_UNCONFIRMED");
        for (const value of reply.data) if (record(value) && typeof value.id === "string" && wanted.includes(value.id) && typeof value.realName === "string" && value.realName.trim()) users.set(value.id, { id: value.id, realName: value.realName });
      }
    } catch { failed = true; }
    if (this.current(epoch)) this.publish({ users: [...users.values()], namesPending: false, namesUnavailable: failed || users.size !== scope.ids.length });
  }
  async labelsSettled(): Promise<void> { await this.labels; }
  dispose(): void { this.disposed = true; ++this.epoch; }
}
