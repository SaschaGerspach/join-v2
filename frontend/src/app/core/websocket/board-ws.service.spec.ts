import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { BoardWsService, isBoardWsEvent } from './board-ws.service';
import { AuthService } from '../auth/auth.service';
import { environment } from '../../../environments/environment';

describe('isBoardWsEvent', () => {
  const knownEvents = [
    'task_created', 'task_updated', 'task_deleted', 'tasks_reordered',
    'column_created', 'column_updated', 'column_deleted', 'columns_reordered',
    'automation_executed',
    'presence_list', 'presence_joined', 'presence_left',
  ];

  it('should accept every known event type', () => {
    for (const event of knownEvents) {
      expect(isBoardWsEvent({ event, data: {} })).withContext(event).toBe(true);
    }
  });

  it('should accept the real columns_reordered payload', () => {
    const payload = {
      event: 'columns_reordered',
      data: [{ id: 1, board: 7, title: 'To do', order: 0, wip_limit: null }],
    };
    expect(isBoardWsEvent(payload)).toBe(true);
  });

  it('should accept the real automation_executed payload', () => {
    const payload = {
      event: 'automation_executed',
      data: { rule_name: 'Auto assign', task_id: 42, actions: ['assign_user'] },
    };
    expect(isBoardWsEvent(payload)).toBe(true);
  });

  it('should reject unknown event types', () => {
    expect(isBoardWsEvent({ event: 'task_exploded', data: {} })).toBe(false);
  });

  it('should reject messages without a data field', () => {
    expect(isBoardWsEvent({ event: 'task_created' })).toBe(false);
  });

  it('should reject malformed values', () => {
    expect(isBoardWsEvent(null)).toBe(false);
    expect(isBoardWsEvent('task_created')).toBe(false);
    expect(isBoardWsEvent({ event: 5, data: {} })).toBe(false);
    expect(isBoardWsEvent({})).toBe(false);
  });
});

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];

  onopen: (() => void) | null = null;
  onmessage: ((msg: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  readonly sent: string[] = [];

  constructor(readonly url: string) {
    FakeWebSocket.instances.push(this);
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(): void {
    this.onclose?.();
  }

  serverAccepts(): void {
    this.onopen?.();
    this.onmessage?.({ data: JSON.stringify({ type: 'authenticated' }) });
  }

  serverDrops(): void {
    this.onclose?.();
  }
}

function makeToken(expiresInSeconds: number): string {
  const payload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + expiresInSeconds }));
  return `header.${payload}.signature`;
}

describe('BoardWsService reconnect', () => {
  const refreshUrl = `${environment.apiUrl}/auth/token/refresh/`;
  let service: BoardWsService;
  let auth: AuthService;
  let httpMock: HttpTestingController;
  let realWebSocket: unknown;

  beforeEach(() => {
    FakeWebSocket.instances = [];
    realWebSocket = window.WebSocket;
    (window as unknown as Record<string, unknown>)['WebSocket'] = FakeWebSocket;

    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(BoardWsService);
    auth = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    (window as unknown as Record<string, unknown>)['WebSocket'] = realWebSocket;
    httpMock.verify();
  });

  it('should refresh an expired token before reopening the socket', fakeAsync(() => {
    auth.setAccessToken(makeToken(-60));
    service.connect(1);
    FakeWebSocket.instances[0].serverAccepts();

    FakeWebSocket.instances[0].serverDrops();
    expect(service.status()).toBe('reconnecting');
    tick(1000);

    const req = httpMock.expectOne(refreshUrl);
    expect(FakeWebSocket.instances.length).toBe(1);

    req.flush({ access: makeToken(300) });
    expect(FakeWebSocket.instances.length).toBe(2);

    FakeWebSocket.instances[1].serverAccepts();
    const authFrame = JSON.parse(FakeWebSocket.instances[1].sent[0]);
    expect(authFrame.token).toBe(auth.getAccessToken());

    service.disconnect();
  }));

  it('should skip the refresh while the token is still valid', fakeAsync(() => {
    auth.setAccessToken(makeToken(3600));
    service.connect(1);
    FakeWebSocket.instances[0].serverAccepts();

    FakeWebSocket.instances[0].serverDrops();
    tick(1000);

    httpMock.expectNone(refreshUrl);
    expect(FakeWebSocket.instances.length).toBe(2);

    service.disconnect();
  }));

  it('should resync after a re-authentication but not on the first connect', fakeAsync(() => {
    auth.setAccessToken(makeToken(3600));
    let resyncs = 0;
    service.resync$.subscribe(() => resyncs++);

    service.connect(1);
    FakeWebSocket.instances[0].onopen?.();
    expect(resyncs).toBe(0);
    expect(service.status()).toBe('reconnecting');

    FakeWebSocket.instances[0].onmessage?.({ data: JSON.stringify({ type: 'authenticated' }) });
    expect(service.status()).toBe('connected');
    expect(resyncs).toBe(0);

    FakeWebSocket.instances[0].serverDrops();
    tick(1000);

    // Reopened, but not resynced until the consumer is back in the group.
    FakeWebSocket.instances[1].onopen?.();
    expect(resyncs).toBe(0);

    FakeWebSocket.instances[1].onmessage?.({ data: JSON.stringify({ type: 'authenticated' }) });
    expect(resyncs).toBe(1);

    service.disconnect();
  }));

  it('should share a single refresh across rapid reconnects', fakeAsync(() => {
    auth.setAccessToken(makeToken(-60));
    service.connect(1);
    FakeWebSocket.instances[0].serverAccepts();

    FakeWebSocket.instances[0].serverDrops();
    FakeWebSocket.instances[0].serverDrops();
    tick(2000);

    // A 401 in the same window goes through the same deduplicated refresh.
    const joined: string[] = [];
    auth.refreshAccessToken().subscribe((token) => joined.push(token));

    const req = httpMock.expectOne(refreshUrl);
    req.flush({ access: makeToken(300) });

    expect(joined).toEqual([auth.getAccessToken()!]);
    expect(FakeWebSocket.instances.length).toBe(2);

    service.disconnect();
  }));
});
