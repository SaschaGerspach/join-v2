const DB_NAME = 'join_offline';
const DB_VERSION = 1;
const STORE_NAME = 'queue';

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function tx(db: IDBDatabase, mode: IDBTransactionMode): IDBObjectStore {
  return db.transaction(STORE_NAME, mode).objectStore(STORE_NAME);
}

export type QueuedRequest = {
  id?: number;
  method: string;
  url: string;
  body: unknown;
  timestamp: number;
};

export async function getAllQueued(): Promise<QueuedRequest[]> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const req = tx(db, 'readonly').getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function putQueued(entry: QueuedRequest): Promise<void> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const store = tx(db, 'readwrite');
    const req = store.put(entry);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function deleteQueued(id: number): Promise<void> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const req = tx(db, 'readwrite').delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function clearQueue(): Promise<void> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const req = tx(db, 'readwrite').clear();
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}
