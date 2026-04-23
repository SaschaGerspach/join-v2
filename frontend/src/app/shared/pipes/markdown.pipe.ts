import { Pipe, PipeTransform } from '@angular/core';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

marked.setOptions({ breaks: true, gfm: true });

const MENTION_RE = /@([\w.+-]+@[\w-]+\.[\w.-]+)/g;

@Pipe({ name: 'markdown', standalone: true })
export class MarkdownPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value) return '';
    const raw = marked.parse(value, { async: false }) as string;
    const withMentions = raw.replace(MENTION_RE, '<span class="mention">@$1</span>');
    return DOMPurify.sanitize(withMentions);
  }
}
