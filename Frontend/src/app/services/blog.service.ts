import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Blog } from '../models/blog';
import { BlogExportData } from '../models/blog-export-data';
import { BlogUpdateRequest } from '../models/blog-update-request';

@Injectable({
  providedIn: 'root'
})
export class BlogService {
  private readonly apiUrl = 'http://localhost:8000/api';
  constructor(private http: HttpClient) { }

  getBlogs(q: string) {
    let params = new HttpParams();
    if (q) {
      params = params.set('q', q);
    }
    return this.http.get<Blog[]>(`${this.apiUrl}/blogs`, { params });
  }

  deleteBlog(id: number) {
    return this.http.delete(`${this.apiUrl}/blogs/${id}`);
  }

  getBlogDetails(id: string | number): Observable<Blog> {
    return this.http.get<Blog>(`${this.apiUrl}/blogs/${id}/`);
  }

  updateBlog(id: number, data: BlogUpdateRequest): Observable<Blog> {
    return this.http.patch<Blog>(`${this.apiUrl}/blogs/${id}/`, data);
  }

  // COPY TO CLIPBOARD METHOD
  async copyToClipboard(blogData: BlogExportData): Promise<boolean> {
    try {
      const plainText = this.stripHtml(blogData.content);
      const formattedContent = `${blogData.title}\n${'='.repeat(blogData.title.length)}\n\n${plainText}${blogData.sourceUrl ? `\n\nSource: ${blogData.sourceUrl}` : ''}`;

      await navigator.clipboard.writeText(formattedContent);
      return true;
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      return false;
    }
  }

  // DOWNLOAD METHODS

  //Generate and download HTML file
  downloadAsHTML(blogData: BlogExportData): void {
    const htmlContent = this.generateHTMLContent(blogData);
    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
    this.downloadFile(blob, `${this.sanitizeFilename(blogData.title)}.html`);
  }

  /**
   * Generate and download Markdown file
   */
  downloadAsMarkdown(blogData: BlogExportData): void {
    const markdownContent = this.convertToMarkdown(blogData.content);
    const fullContent = `# ${blogData.title}\n\n${markdownContent}${blogData.sourceUrl ? `\n\n---\n*Source: ${blogData.sourceUrl}*` : ''}`;

    const blob = new Blob([fullContent], { type: 'text/markdown;charset=utf-8' });
    this.downloadFile(blob, `${this.sanitizeFilename(blogData.title)}.md`);
  }

  /**
   * Advanced PDF generation using browser print
   */
  generateAdvancedPDF(blogData: BlogExportData): void {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(this.generatePrintableHTML(blogData));
      printWindow.document.close();
      printWindow.focus();

      setTimeout(() => {
        printWindow.print();
        printWindow.close();
      }, 250);
    }
  }

  /**
   * Export as JSON
   */
  exportAsJSON(blogData: BlogExportData): void {
    const exportData = {
      ...blogData,
      exportDate: new Date().toISOString(),
      version: '1.0'
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json;charset=utf-8'
    });
    this.downloadFile(blob, `${this.sanitizeFilename(blogData.title)}.json`);
  }

  // SHARING METHODS

  /**
   * Share to LinkedIn
   */
  shareToLinkedIn(blogData: BlogExportData, currentUrl: string): void {
    const text = encodeURIComponent(
      `${blogData.title}\n\n${this.stripHtml(blogData.content).substring(0, 200)}...`
    );
    const url = encodeURIComponent(currentUrl);

    const linkedInUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${url}&summary=${text}`;
    window.open(linkedInUrl, '_blank', 'width=600,height=600');
  }

  /**
   * Share to Twitter/X
   */
  shareToTwitter(blogData: BlogExportData, currentUrl: string): void {
    const text = encodeURIComponent(
      `${blogData.title}\n\n${this.stripHtml(blogData.content).substring(0, 200)}...`
    );
    const url = encodeURIComponent(currentUrl);

    const twitterUrl = `https://twitter.com/intent/tweet?text=${text}&url=${url}`;
    window.open(twitterUrl, '_blank', 'width=600,height=400');
  }

  /**
   * Share via Email
   */
  shareViaEmail(blogData: BlogExportData): void {
    const subject = encodeURIComponent(`Article: ${blogData.title}`);
    const plainTextContent = this.stripHtml(blogData.content);

    const body = encodeURIComponent(`
Hi there,

I wanted to share this article with you:

${blogData.title}
${'='.repeat(blogData.title.length)}

${plainTextContent}

${blogData.sourceUrl ? `Original source: ${blogData.sourceUrl}` : ''}

Best regards,
${blogData.author || 'Anonymous'}
    `.trim());

    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  }

  /**
   * Share to WhatsApp
   */
  shareToWhatsApp(blogData: BlogExportData, currentUrl: string): void {
    const text = `${blogData.title}\n\n${this.stripHtml(blogData.content).substring(0, 300)}...\n\nRead more: ${currentUrl}`;
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(whatsappUrl, '_blank');
  }

  /**
   * Share to Facebook
   */
  shareToFacebook(currentUrl: string): void {
    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(currentUrl)}`;
    window.open(facebookUrl, '_blank', 'width=600,height=400');
  }

  /**
   * Copy link to clipboard
   */
  async copyLink(url: string): Promise<boolean> {
    try {
      await navigator.clipboard.writeText(url);
      return true;
    } catch (error) {
      console.error('Failed to copy link:', error);
      return false;
    }
  }

  // PRIVATE UTILITY METHODS

  /**
   * Generate HTML content for export
   */
  private generateHTMLContent(blogData: BlogExportData): string {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${blogData.title}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #fff;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2.5rem;
        }
        h2 {
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.8rem;
        }
        h3 {
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.4rem;
        }
        p {
            margin-bottom: 20px;
            font-size: 16px;
        }
        blockquote {
            border-left: 4px solid #3498db;
            margin: 30px 0;
            padding: 15px 30px;
            background: #f8f9fa;
            font-style: italic;
            color: #555;
        }
        code {
            background: #f1f2f6;
            padding: 3px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 14px;
        }
        ul, ol {
            margin: 20px 0;
            padding-left: 30px;
        }
        li {
            margin: 10px 0;
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .metadata {
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 30px;
            padding: 15px;
            background: #ecf0f1;
            border-radius: 8px;
            border-left: 4px solid #95a5a6;
        }
        .footer {
            margin-top: 60px;
            padding-top: 30px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        @media print {
            body {
                font-size: 12pt;
                line-height: 1.4;
            }
            h1 {
                font-size: 18pt;
            }
            h2 {
                font-size: 14pt;
            }
            h3 {
                font-size: 12pt;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>${blogData.title}</h1>
        <div class="metadata">
            ${blogData.author ? `Author: ${blogData.author}` : ''}
            ${blogData.publishDate ? ` | Published: ${blogData.publishDate.toLocaleDateString()}` : ''}
            ${blogData.sourceUrl ? ` | <a href="${blogData.sourceUrl}" target="_blank">View Source</a>` : ''}
        </div>
    </header>
    
    <main>
        ${blogData.content}
    </main>
    
    <footer class="footer">
        ${blogData.sourceUrl ? `<p>Original source: <a href="${blogData.sourceUrl}" target="_blank">${blogData.sourceUrl}</a></p>` : ''}
        <p>Exported on ${new Date().toLocaleDateString()} from IntelliBlogger</p>
    </footer>
</body>
</html>`.trim();
  }

  /**
   * Generate printable HTML for PDF
   */
  private generatePrintableHTML(blogData: BlogExportData): string {
    return `
      <!DOCTYPE html>
      <html>
      <head>
          <title>${blogData.title}</title>
          <style>
              @page { 
                  margin: 1in; 
                  size: A4;
              }
              body { 
                  font-family: Georgia, 'Times New Roman', serif;
                  font-size: 12pt; 
                  line-height: 1.6;
                  color: #000;
                  margin: 0;
                  padding: 0;
              }
              h1 { 
                  font-size: 20pt; 
                  color: #000; 
                  border-bottom: 2pt solid #000; 
                  padding-bottom: 10pt;
                  margin-bottom: 20pt;
                  page-break-after: avoid;
              }
              h2 { 
                  font-size: 16pt; 
                  color: #000;
                  margin-top: 24pt;
                  margin-bottom: 12pt;
                  page-break-after: avoid;
              }
              h3 { 
                  font-size: 14pt; 
                  color: #000;
                  margin-top: 18pt;
                  margin-bottom: 9pt;
                  page-break-after: avoid;
              }
              p {
                  margin-bottom: 12pt;
                  text-align: justify;
                  orphans: 2;
                  widows: 2;
              }
              blockquote { 
                  border-left: 3pt solid #000; 
                  margin: 16pt 0; 
                  padding: 8pt 16pt; 
                  background: #f5f5f5;
                  page-break-inside: avoid;
              }
              ul, ol {
                  margin: 12pt 0;
                  padding-left: 24pt;
              }
              li {
                  margin: 6pt 0;
              }
              img {
                  max-width: 100%;
                  height: auto;
                  page-break-inside: avoid;
              }
              .metadata {
                  font-size: 10pt;
                  color: #666;
                  margin-bottom: 20pt;
                  border-bottom: 1pt solid #ccc;
                  padding-bottom: 10pt;
              }
              .no-print { 
                  display: none; 
              }
              a {
                  color: #000;
                  text-decoration: underline;
              }
              @media print {
                  .no-print {
                      display: none !important;
                  }
              }
          </style>
      </head>
      <body>
          <div class="metadata">
              ${blogData.author ? `Author: ${blogData.author}` : ''}
              ${blogData.publishDate ? ` | Date: ${blogData.publishDate.toLocaleDateString()}` : ''}
          </div>
          <h1>${blogData.title}</h1>
          ${blogData.content}
          ${blogData.sourceUrl ? `<p style="margin-top: 30pt; font-size: 10pt; color: #666;">Source: ${blogData.sourceUrl}</p>` : ''}
      </body>
      </html>`;
  }

  /**
   * Convert HTML to Markdown (basic conversion)
   */
  private convertToMarkdown(html: string): string {
    return html
      .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
      .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
      .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
      .replace(/<h4[^>]*>(.*?)<\/h4>/gi, '#### $1\n\n')
      .replace(/<h5[^>]*>(.*?)<\/h5>/gi, '##### $1\n\n')
      .replace(/<h6[^>]*>(.*?)<\/h6>/gi, '###### $1\n\n')
      .replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n')
      .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
      .replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**')
      .replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*')
      .replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*')
      .replace(/<u[^>]*>(.*?)<\/u>/gi, '$1')
      .replace(/<blockquote[^>]*>(.*?)<\/blockquote>/gis, (match, content) => {
        return '> ' + content.replace(/<[^>]+>/g, '').trim() + '\n\n';
      })
      .replace(/<ul[^>]*>(.*?)<\/ul>/gis, '$1\n')
      .replace(/<ol[^>]*>(.*?)<\/ol>/gis, '$1\n')
      .replace(/<li[^>]*>(.*?)<\/li>/gi, '- $1\n')
      .replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)')
      .replace(/<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>/gi, '![$2]($1)')
      .replace(/<img[^>]*src="([^"]*)"[^>]*>/gi, '![]($1)')
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<[^>]+>/g, '') // Remove remaining HTML tags
      .replace(/\n\s*\n\s*\n/g, '\n\n') // Clean up excessive newlines
      .trim();
  }

  /**
   * Strip HTML tags and get plain text
   */
  private stripHtml(html: string): string {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  }

  /**
   * Sanitize filename for download
   */
  private sanitizeFilename(filename: string): string {
    return filename
      .replace(/[^a-z0-9]/gi, '_')
      .replace(/_{2,}/g, '_')
      .replace(/^_|_$/g, '')
      .toLowerCase()
      .substring(0, 50); // Limit filename length
  }

  /**
   * Download file helper
   */
  private downloadFile(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

