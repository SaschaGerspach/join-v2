import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TranslateModule } from '@ngx-translate/core';
import { AssigneePickerComponent } from './assignee-picker.component';
import { Contact } from '../../../../core/contacts/contacts-api.service';

function contact(id: number, first: string, last: string): Contact {
  return { id, first_name: first, last_name: last, email: `${first.toLowerCase()}@example.com`, phone: '' };
}

describe('AssigneePickerComponent', () => {
  let fixture: ComponentFixture<AssigneePickerComponent>;
  let component: AssigneePickerComponent;

  const contacts = [
    contact(1, 'Laura', 'Mueller'),
    contact(2, 'Thomas', 'Schmidt'),
    contact(3, 'Markus', 'Fischer'),
  ];

  function key(name: string): KeyboardEvent {
    return new KeyboardEvent('keydown', { key: name, cancelable: true });
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [AssigneePickerComponent, TranslateModule.forRoot()],
    });
    fixture = TestBed.createComponent(AssigneePickerComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('contacts', contacts);
    fixture.componentRef.setInput('selectedIds', [2]);
    fixture.detectChanges();
  });

  it('should resolve selected ids to contacts', () => {
    expect(component.selectedContacts().map(c => c.id)).toEqual([2]);
  });

  it('should exclude already selected contacts from suggestions', () => {
    expect(component.suggestions().map(c => c.id)).toEqual([1, 3]);
  });

  it('should filter suggestions by name or email', () => {
    component.onInput('fisch');
    expect(component.suggestions().map(c => c.id)).toEqual([3]);
    component.onInput('laura@');
    expect(component.suggestions().map(c => c.id)).toEqual([1]);
  });

  it('should add a contact and clear the query', () => {
    component.onInput('mark');
    component.add(contacts[2]);
    expect(component.selectedIds()).toEqual([2, 3]);
    expect(component.query()).toBe('');
  });

  it('should remove a contact', () => {
    component.remove(2);
    expect(component.selectedIds()).toEqual([]);
  });

  it('should add the active suggestion on Enter after arrow navigation', () => {
    component.open.set(true);
    component.onKeydown(key('ArrowDown'));
    const enter = key('Enter');
    component.onKeydown(enter);
    expect(component.selectedIds()).toEqual([2, 3]);
    expect(enter.defaultPrevented).toBeTrue();
  });

  it('should remove the last contact on Backspace with an empty query', () => {
    component.onKeydown(key('Backspace'));
    expect(component.selectedIds()).toEqual([]);
  });

  it('should keep contacts on Backspace while typing', () => {
    component.onInput('x');
    component.onKeydown(key('Backspace'));
    expect(component.selectedIds()).toEqual([2]);
  });

  it('should close suggestions on Escape without letting it reach the modal', () => {
    component.open.set(true);
    const escape = key('Escape');
    spyOn(escape, 'stopPropagation');
    component.onKeydown(escape);
    expect(component.open()).toBeFalse();
    expect(escape.stopPropagation).toHaveBeenCalled();
  });

  it('should offer every matching contact for scrolling', () => {
    const many = Array.from({ length: 100 }, (_, i) => contact(100 + i, `Person${i}`, 'Test'));
    fixture.componentRef.setInput('contacts', many);
    fixture.componentRef.setInput('selectedIds', []);
    expect(component.suggestions().length).toBe(100);
  });

  it('should render the suggestion list in an overlay when focused', () => {
    const input: HTMLInputElement = fixture.nativeElement.querySelector('.picker-input');
    input.dispatchEvent(new Event('focus'));
    fixture.detectChanges();
    const options = document.querySelectorAll(`#${component.listboxId} [role="option"]`);
    expect(options.length).toBe(2);
    expect(fixture.nativeElement.querySelector('.suggestions')).toBeNull();
  });
});
