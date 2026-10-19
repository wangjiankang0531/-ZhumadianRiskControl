// Server-recognized scopes; accepting a known scope never grants it.
export const apiPermissions=Object.freeze(['spatial:read','business:read','focus:read','focus:track','focus:feedback','gas:read','gas:ingest','gas:verify','gas:cooperate','gas:handoff']);
export const knownPermissions=value=>Array.isArray(value)&&new Set(value).size===value.length&&value.every(p=>apiPermissions.includes(p));
