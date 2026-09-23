import { Pipe, PipeTransform } from '@angular/core';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

marked.setOptions({ breaks: true, gfm: true });

const MENTION_RE = /@([\w.+-]+@[\w-]+\.[\w.-]+)/g;

// Security note:
//  - The only path rendering untrusted user HTML is THIS markdown pipe
//    (comments, task descriptions). It runs DOMPurify.sanitize() as the
//    final stage, independent of Angular's sanitizer, so an Angular
//    sanitizer bypass cannot reach the DOM.
//  - IMPORTANT: this protection depends on DOMPurify remaining the final
//    sanitization stage of this pipe. Do not remove or reorder it, and do
//    not route untrusted HTML around it.
//  - bypassSecurityTrustResourceUrl is used only on app-generated blob:
//    URLs; all other [src]/[href] bindings are URL-context, not HTML/SVG.
// History: this defence-in-depth argument kept the CI npm audit gate at
// 'critical' while Angular <=18 carried unpatched XSS advisories. The
// Angular 21 upgrade (2026-09-23) resolved them and the gate is now 'high'.
@Pipe({ name: 'markdown' })
export class MarkdownPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value) return '';
    const raw = marked.parse(value, { async: false }) as string;
    const withMentions = raw.replace(MENTION_RE, '<span class="mention">@$1</span>');
    return DOMPurify.sanitize(withMentions);
  }
}
