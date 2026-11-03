import { participantScope } from "@/components/Detail/OriginalEmergencyReadonlyDetail";

type User = { id: string; realName: string };
type Directory = (query: { organizeId: string; ids: string }) => Promise<unknown>;
const record = (value: unknown): value is Record<string, any> => !!value && typeof value === "object" && !Array.isArray(value);

/** Names supplement only the records already returned by the authenticated list API. */
export class OriginalExerciseListUsers {
  private epoch = 0;
  private disposed = false;
  constructor(private directory: Directory, private publish: (users: User[]) => void, private budgetMillis = 5000) {}

  async load(rows: unknown): Promise<void> {
    if (this.disposed) return;
    const epoch = ++this.epoch;
    const current = () => !this.disposed && this.epoch === epoch;
    this.publish([]);
    if (!Array.isArray(rows) || rows.length > 500) return;
    const groups = new Map<string, Set<string>>();
    for (const row of rows) {
      if (!record(row)) continue;
      const scope = participantScope(row);
      if (!scope) continue;
      let ids = groups.get(scope.organizeId);
      if (!ids) { ids = new Set(); groups.set(scope.organizeId, ids); }
      scope.ids.forEach(id => ids!.add(id));
    }
    if (groups.size > 32 || [...groups.values()].some(ids => ids.size > 512)) return;
    const users = new Map<string, User>();
    const deadline = Date.now() + this.budgetMillis;
    try {
      for (const [organizeId, ids] of groups) {
        const values = [...ids];
        for (let offset = 0; offset < values.length; offset += 50) {
          if (!current()) return;
          const wanted = values.slice(offset, offset + 50), left = deadline - Date.now();
          if (left <= 0) throw Error("EXERCISE_LIST_NAMES_TIMEOUT");
          let timer: ReturnType<typeof setTimeout> | undefined;
          let reply: unknown;
          try {
            reply = await Promise.race([
              this.directory({ organizeId, ids: wanted.join(",") }),
              new Promise((_, reject) => { timer = setTimeout(() => reject(Error("EXERCISE_LIST_NAMES_TIMEOUT")), left); })
            ]);
          } finally { if (timer) clearTimeout(timer); }
          if (!current()) return;
          if (!record(reply) || reply.code !== 0 || !Array.isArray(reply.data)) throw Error("EXERCISE_LIST_NAMES_UNCONFIRMED");
          for (const user of reply.data) if (record(user) && wanted.includes(user.id) && typeof user.realName === "string" && user.realName.trim()) {
            users.set(user.id, { id: user.id, realName: user.realName });
          }
        }
      }
    } catch { /* The existing list renders participant IDs when names are unavailable. */ }
    if (current()) this.publish([...users.values()]);
  }

  dispose(): void { this.disposed = true; ++this.epoch; }
}
