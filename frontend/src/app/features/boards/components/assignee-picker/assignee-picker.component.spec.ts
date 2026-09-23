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

  // The virtual viewport renders and updates its visible range on animation frames.
  async function settle(): Promise<void> {
    fixture.detectChanges();
    await fixture.whenStable();
    for (let frame = 0; frame < 2; frame++) {
      await new Promise(resolve => requestAnimationFrame(resolve));
      fixture.detectChanges();
    }
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

  it('should open on ArrowDown with the first suggestion active', () => {
    component.onKeydown(key('ArrowDown'));
    expect(component.open()).toBeTrue();
    expect(component.activeIndex()).toBe(0);
    component.onKeydown(key('Enter'));
    expect(component.selectedIds()).toEqual([2, 1]);
  });

  it('should keep a valid active index when there are no suggestions', () => {
    fixture.componentRef.setInput('selectedIds', [1, 2, 3]);
    component.open.set(true);
    component.onKeydown(key('ArrowDown'));
    expect(component.activeIndex()).toBe(0);
  });

  it('should remove the last contact on Backspace with an empty query', () => {
    component.onKeydown(key('Backspace'));
    expect(component.selectedIds()).toEqual([]);
  });

  it('should not remove assignees without a chip on Backspace', () => {
    fixture.componentRef.setInput('selectedIds', [2, 99]);
    component.onKeydown(key('Backspace'));
    expect(component.selectedIds()).toEqual([99]);
    component.onKeydown(key('Backspace'));
    expect(component.selectedIds()).toEqual([99]);
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

  it('should render the suggestion list in an overlay when focused', async () => {
    const input: HTMLInputElement = fixture.nativeElement.querySelector('.picker-input');
    input.dispatchEvent(new Event('focus'));
    await settle();
    const options = document.querySelectorAll(`#${component.listboxId} [role="option"]`);
    expect(options.length).toBe(2);
    expect(fixture.nativeElement.querySelector('.suggestions')).toBeNull();
  });

  describe('with a large address book', () => {
    beforeEach(async () => {
      const many = Array.from({ length: 500 }, (_, i) => contact(1000 + i, `Person${i}`, 'Test'));
      fixture.componentRef.setInput('contacts', many);
      fixture.componentRef.setInput('selectedIds', []);
      component.openList();
      await settle();
    });

    it('should render only the visible rows', () => {
      const options = document.querySelectorAll(`#${component.listboxId} [role="option"]`);
      expect(options.length).toBeGreaterThan(0);
      expect(options.length).toBeLessThan(50);
      expect(options[0].getAttribute('aria-setsize')).toBe('500');
    });

    it('should scroll the active row into view on keyboard navigation', async () => {
      for (let i = 0; i < 20; i++) component.onKeydown(key('ArrowDown'));
      await settle();
      expect(component.activeIndex()).toBe(20);
      expect(component.viewport!.measureScrollOffset('top')).toBe(21 * component.optionHeight - component.listHeight());
      expect(document.getElementById(component.optionId(20))).not.toBeNull();
    });
  });

  it('should reopen the suggestion list when the focused input is clicked', () => {
    const input: HTMLInputElement = fixture.nativeElement.querySelector('.picker-input');
    component.open.set(false);
    input.click();
    expect(component.open()).toBeTrue();
  });
});
