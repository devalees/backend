import re
import html
from typing import Optional, List, Tuple

class RichTextFormatter:
    """Handles formatting of rich text content"""
    
    def __init__(self):
        self.formatting_rules = {
            # Basic formatting
            r'\*\*(.*?)\*\*': r'<strong>\1</strong>',  # Bold
            r'\*(.*?)\*': r'<em>\1</em>',              # Italic
            r'`(.*?)`': r'<code>\1</code>',            # Code
            
            # Headers
            r'^# (.*?)$': r'<h1>\1</h1>',              # H1
            r'^## (.*?)$': r'<h2>\1</h2>',             # H2
            r'^### (.*?)$': r'<h3>\1</h3>',            # H3
            
            # Horizontal rules
            r'^---$': r'<hr>',                         # Horizontal rule
        }
        
        # Multi-line patterns that need special handling
        self.multiline_patterns = {
            'media': self._format_media,  # Media must be first to prevent link formatting from interfering
            'links': self._format_links,
            'lists': self._format_lists,
            'tables': self._format_tables,
            'blockquotes': self._format_blockquotes,
        }
    
    def _format_lists(self, content: str) -> str:
        """Format lists (both ordered and unordered)"""
        lines = content.split('\n')
        in_list = False
        list_type = None
        result = []
        
        for line in lines:
            # Check for unordered list items
            if line.strip().startswith('- '):
                if not in_list or list_type != 'ul':
                    if in_list:
                        result.append(f'</{list_type}>')
                    result.append('<ul>')
                    in_list = True
                    list_type = 'ul'
                result.append(f'<li>{line.strip()[2:]}</li>')
            # Check for ordered list items
            elif re.match(r'^\s*\d+\.\s+', line):
                if not in_list or list_type != 'ol':
                    if in_list:
                        result.append(f'</{list_type}>')
                    result.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li>{re.sub(r"^\s*\d+\.\s+", "", line)}</li>')
            else:
                if in_list:
                    result.append(f'</{list_type}>')
                    in_list = False
                result.append(line)
        
        if in_list:
            result.append(f'</{list_type}>')
        
        return '\n'.join(result)
    
    def _format_tables(self, content: str) -> str:
        """Format tables"""
        lines = content.split('\n')
        in_table = False
        result = []
        header_row = None
        
        for line in lines:
            if '|' in line:
                cells = [cell.strip() for cell in line.strip('|').split('|')]
                if not in_table:
                    in_table = True
                    header_row = cells
                    result.append('<table>\n<thead><tr>')
                    result.extend([f'<th>{cell}</th>' for cell in cells])
                    result.append('</tr></thead>\n<tbody>')
                elif all('-' in cell for cell in cells):
                    continue
                else:
                    result.append('<tr>')
                    result.extend([f'<td>{cell}</td>' for cell in cells])
                    result.append('</tr>')
            else:
                if in_table:
                    result.append('</tbody>\n</table>')
                    in_table = False
                result.append(line)
        
        if in_table:
            result.append('</tbody>\n</table>')
        
        return '\n'.join(result)
    
    def _format_blockquotes(self, content: str) -> str:
        """Format multi-line blockquotes"""
        lines = content.split('\n')
        in_blockquote = False
        result = []
        
        for line in lines:
            if line.startswith('> '):
                if not in_blockquote:
                    result.append('<blockquote>')
                    in_blockquote = True
                result.append(line[2:])
            else:
                if in_blockquote:
                    result.append('</blockquote>')
                    in_blockquote = False
                result.append(line)
        
        if in_blockquote:
            result.append('</blockquote>')
        
        return '\n'.join(result)
    
    def _format_links(self, content):
        def replace_link(match):
            text = match.group(1)
            url = match.group(2)
            title = match.group(3) if len(match.groups()) > 2 and match.group(3) else None
            
            # Clean up the URL and title
            url = url.strip()
            if title:
                title = title.strip()
                return f'<a href="{url}" title="{title}">{text}</a>'
            return f'<a href="{url}">{text}</a>'
        
        # Handle both types of links with a single pattern
        pattern = r'\[(.*?)\]\((.*?)(?:\s+"([^"]*)")?\)'
        return re.sub(pattern, replace_link, content)
    
    def _format_media(self, content: str) -> str:
        """Format media (images, etc.)"""
        return re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1">', content)
    
    def _format_headers(self, content):
        for i in range(6, 0, -1):
            pattern = r'^#{' + str(i) + r'}\s+(.+)$'
            content = re.sub(pattern, rf'<h{i}>\1</h{i}>', content, flags=re.MULTILINE)
        return content

    def _format_horizontal_rules(self, content):
        return re.sub(r'^---+$', '<hr>', content, flags=re.MULTILINE)

    def _format_bold(self, content):
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)

    def _format_italic(self, content):
        return re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)

    def _format_code(self, content):
        return re.sub(r'`(.+?)`', r'<code>\1</code>', content)
    
    def format(self, content: str) -> str:
        """Format the content according to rich text rules"""
        if not content:
            return ""
            
        # Format block-level elements that shouldn't be escaped first
        formatted = content
        formatted = self._format_blockquotes(formatted)
        
        # Now escape the content to prevent XSS attacks, but preserve quotes
        formatted = html.escape(formatted, quote=False)
        
        # Format the remaining content
        formatted = self._format_headers(formatted)
        formatted = self._format_horizontal_rules(formatted)
        formatted = self._format_tables(formatted)
        formatted = self._format_lists(formatted)
        formatted = self._format_bold(formatted)
        formatted = self._format_italic(formatted)
        formatted = self._format_code(formatted)
        formatted = self._format_media(formatted)
        formatted = self._format_links(formatted)
        
        # Wrap in paragraph if not already wrapped in a block element
        if not any(tag in formatted for tag in ['<h1>', '<h2>', '<h3>', '<h4>', '<h5>', '<h6>', '<ul>', '<ol>', '<table>', '<blockquote>']):
            formatted = f"<p>{formatted}</p>"
        
        # Unescape HTML tags
        formatted = re.sub(r'&lt;(\/?(?:p|strong|em|code|a|img|ul|ol|li|table|thead|tbody|tr|th|td|blockquote|h[1-6])[^&]*)&gt;', r'<\1>', formatted)
        
        return formatted
    
    def validate(self, content: str) -> bool:
        """Validate the content for security and formatting"""
        if content is None:
            return False
            
        # Check for matching markdown syntax
        if content.count('**') % 2 != 0:
            return False
            
        if content.count('*') % 2 != 0:
            return False
            
        if content.count('`') % 2 != 0:
            return False
            
        # Check for potential XSS attacks
        xss_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+=',
            r'data:',
            r'vbscript:',
            r'<iframe.*?>',
            r'<object.*?>',
            r'<embed.*?>'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False
            
        return True

class RichTextMessage:
    """Represents a rich text message with formatting and validation"""
    
    def __init__(self, content: str):
        self.raw_content = content
        self.formatter = RichTextFormatter()
        self._formatted_content = None
    
    @property
    def formatted_content(self) -> str:
        """Get the formatted content, formatting if necessary"""
        if self._formatted_content is None:
            if not self.formatter.validate(self.raw_content):
                raise ValueError("Invalid content detected")
            self._formatted_content = self.formatter.format(self.raw_content)
        return self._formatted_content
    
    def generate_preview(self, max_length: int = 100) -> str:
        """Generate a preview of the message"""
        # Remove formatting for preview
        preview = re.sub(r'<[^>]+>', '', self.formatted_content)
        
        # Truncate if necessary
        if len(preview) > max_length:
            preview = preview[:max_length] + "..."
            
        return preview 