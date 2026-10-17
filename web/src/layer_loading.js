// Adopt only the newest completed layer read. Failed reads preserve the current document.
export class LayerLoading {
  revision = 0;
  async load(read, adopt) {
    const revision = ++this.revision;
    try {
      const document = await read();
      if (revision !== this.revision) return false;
      adopt(document);
      return true;
    } catch (error) {
      if (revision === this.revision) throw error;
      return false;
    }
  }
}
