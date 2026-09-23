import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ContactsApiService, Contact } from './contacts-api.service';
import { environment } from '../../../environments/environment';

describe('ContactsApiService', () => {
  let service: ContactsApiService;
  let httpMock: HttpTestingController;

  const base = environment.apiUrl;

  function contact(id: number): Contact {
    return { id, first_name: `First${id}`, last_name: `Last${id}`, email: `c${id}@example.com`, phone: '' };
  }

  function expectPage(page: number) {
    return httpMock.expectOne(r =>
      r.url === `${base}/contacts/` && r.params.get('page') === String(page) && r.params.get('page_size') === '500',
    );
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ContactsApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should return a single page of contacts', () => {
    let result: Contact[] = [];
    service.getAll().subscribe(c => result = c);
    expectPage(1).flush({ next: null, results: [contact(1), contact(2)] });
    expect(result.map(c => c.id)).toEqual([1, 2]);
  });

  it('should follow pagination until the last page', () => {
    let result: Contact[] = [];
    service.getAll().subscribe(c => result = c);
    expectPage(1).flush({ next: 'http://ignored/contacts/?page=2', results: [contact(1)] });
    expectPage(2).flush({ next: 'http://ignored/contacts/?page=3', results: [contact(2)] });
    expectPage(3).flush({ next: null, results: [contact(3)] });
    expect(result.map(c => c.id)).toEqual([1, 2, 3]);
  });
});
