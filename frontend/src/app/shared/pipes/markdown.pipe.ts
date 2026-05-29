import { Pipe, PipeTransform } from '@angular/core';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

marked.setOptions({ breaks: true, gfm: true });

const MENTION_RE = /@([\w.+-]+@[\w-]+\.[\w.-]+)/g;

// Security note (Angular XSS CVE assessment, 2026-05-29):
// npm audit reports 10 high CVEs in @angular/core <=18.2.14, incl.
// GHSA-jrmj-c5cx-3cw6 (SVG sanitizer bypass) and two i18n XSS CVEs
// (GHSA-prjf-86w9-mfqv, GHSA-g93w-mfhg-p222).
// Read-only exposure review concluded: NOT practically exploitable here.
//  - i18n CVEs target Angular's built-in $localize/i18n; this app uses
//    ngx-translate -> not affected.
//  - The only path rendering untrusted user HTML is THIS markdown pipe
//    (comments, task descriptions). It runs DOMPurify.sanitize() as the
//    final stage, independent of Angular's sanitizer, so an Angular
//    sanitizer bypass cannot reach the DOM.
//  - IMPORTANT: this protection depends on DOMPurify remaining the final
//    sanitization stage of this pipe. Do not remove or reorder it, and do
//    not route untrusted HTML around it.
//  - bypassSecurityTrustResourceUrl is used only on app-generated blob:
//    URLs; all other [src]/[href] bindings are URL-context, not HTML/SVG.
// Decision: audit gate stays at 'critical'; raising to 'high' is deferred
// until the Angular 17->19 major upgrade. Re-evaluate when DOMPurify or
// the markdown rendering path changes.
@Pipe({ name: 'markdown', standalone: true })
export class MarkdownPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value) return '';
    const raw = marked.parse(value, { async: false }) as string;
    const withMentions = raw.replace(MENTION_RE, '<span class="mention">@$1</span>');
    return DOMPurify.sanitize(withMentions);
  }
}
