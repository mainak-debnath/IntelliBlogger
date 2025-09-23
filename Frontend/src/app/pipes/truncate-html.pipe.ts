import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'truncateHtml',
  standalone: true
})
export class TruncateHtmlPipe implements PipeTransform {
  transform(htmlContent: string, wordLimit: number = 25): string {
    if (!htmlContent) return '';

    // Create a temporary div to parse HTML and count words
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;

    // Get plain text content for word counting
    const textContent = tempDiv.textContent || tempDiv.innerText || '';
    const words = textContent.trim().split(/\s+/).filter(word => word.length > 0);

    // If content is within limit, return original HTML
    if (words.length <= wordLimit) {
      return htmlContent;
    }

    // If we need to truncate, we'll do a simple approach:
    // Get the first N words as plain text and return with ellipsis
    const truncatedText = words.slice(0, wordLimit).join(' ') + '...';

    // For a more advanced approach that preserves some HTML structure:
    // You could traverse the DOM nodes and build truncated HTML
    // But for simplicity, we'll return plain text with ellipsis

    return this.truncateHtmlAdvanced(htmlContent, wordLimit);
  }

  private truncateHtmlAdvanced(htmlContent: string, wordLimit: number): string {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;

    let wordCount = 0;
    const result: string[] = [];

    const processNode = (node: Node): boolean => {
      if (wordCount >= wordLimit) return false;

      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent || '';
        const words = text.trim().split(/\s+/).filter(w => w.length > 0);

        for (let i = 0; i < words.length && wordCount < wordLimit; i++) {
          result.push(words[i]);
          wordCount++;
        }

        return wordCount < wordLimit;
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        const element = node as Element;
        const tagName = element.tagName.toLowerCase();

        // Add opening tag
        const attrs = Array.from(element.attributes)
          .map(attr => `${attr.name}="${attr.value}"`)
          .join(' ');
        result.push(`<${tagName}${attrs ? ' ' + attrs : ''}>`);

        // Process children
        let shouldContinue = true;
        for (const child of Array.from(element.childNodes)) {
          if (!processNode(child)) {
            shouldContinue = false;
            break;
          }
        }

        // Add closing tag
        result.push(`</${tagName}>`);

        return shouldContinue;
      }

      return true;
    };

    // Process all child nodes
    for (const child of Array.from(tempDiv.childNodes)) {
      if (!processNode(child)) break;
    }

    // Add ellipsis if we truncated
    if (wordCount >= wordLimit) {
      result.push('...');
    }

    return result.join(' ').replace(/>\s+</g, '><'); // Clean up spacing
  }
}