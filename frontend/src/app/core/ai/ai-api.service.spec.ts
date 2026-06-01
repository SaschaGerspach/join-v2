import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AiApiService, AI_FEATURE } from './ai-api.service';
import { environment } from '../../../environments/environment';

describe('AiApiService', () => {
  let service: AiApiService;
  let httpMock: HttpTestingController;

  const base = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AiApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should generate a description and unwrap the payload', () => {
    service.generateDescription('Title', 'kw').subscribe(text => expect(text).toBe('Drafted.'));
    const req = httpMock.expectOne(`${base}/ai/generate-description/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ title: 'Title', keywords: 'kw' });
    req.flush({ description: 'Drafted.' });
  });

  it('should suggest subtasks and unwrap the array', () => {
    service.suggestSubtasks('Title').subscribe(subs => expect(subs).toEqual(['A', 'B']));
    const req = httpMock.expectOne(`${base}/ai/suggest-subtasks/`);
    expect(req.request.method).toBe('POST');
    req.flush({ subtasks: ['A', 'B'] });
  });

  it('should categorize and return the full payload', () => {
    service.categorize('Title', 'Desc').subscribe(res => {
      expect(res.priority).toBe('urgent');
      expect(res.labels).toEqual(['bug']);
    });
    const req = httpMock.expectOne(`${base}/ai/categorize/`);
    expect(req.request.body).toEqual({ title: 'Title', description: 'Desc' });
    req.flush({ priority: 'urgent', labels: ['bug'] });
  });

  it('should load enabled features once and expose them via isEnabled', () => {
    service.ensureLoaded();
    const req = httpMock.expectOne(`${base}/ai/features/`);
    expect(req.request.method).toBe('GET');
    req.flush({ features: [AI_FEATURE.generateDescription] });

    expect(service.isEnabled(AI_FEATURE.generateDescription)).toBe(true);
    expect(service.isEnabled(AI_FEATURE.summarize)).toBe(false);

    // Second call must not trigger another request.
    service.ensureLoaded();
    httpMock.expectNone(`${base}/ai/features/`);
  });

  it('should treat a failed feature load as no features enabled', () => {
    service.ensureLoaded();
    const req = httpMock.expectOne(`${base}/ai/features/`);
    req.flush('error', { status: 500, statusText: 'Server Error' });

    expect(service.enabled()).toEqual([]);
    expect(service.isEnabled(AI_FEATURE.generateDescription)).toBe(false);
  });

  it('isEnabled should be false before features are loaded', () => {
    expect(service.isEnabled(AI_FEATURE.categorize)).toBe(false);
  });
});
