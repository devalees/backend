import re
import html
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

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
        """Format media (images, videos, audio, etc.)"""
        def replace_media(match):
            alt_text = match.group(1)
            url = match.group(2)
            media_type = match.group(3) if len(match.groups()) > 2 else None
            
            # Clean up the URL and alt text
            url = url.strip()
            alt_text = alt_text.strip()
            
            # URL encode spaces in the URL
            url = url.replace(' ', '%20')
            
            # Escape special characters in alt text
            alt_text = html.escape(alt_text, quote=True)
            
            # Determine media type from URL extension if not specified
            if not media_type:
                ext = url.lower().split('.')[-1]
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    media_type = 'image'
                elif ext in ['mp4', 'webm', 'ogg']:
                    media_type = 'video'
                elif ext in ['mp3', 'wav', 'ogg']:
                    media_type = 'audio'
                else:
                    media_type = 'image'  # Default to image if unknown
            
            # Format based on media type
            if media_type == 'image':
                return f'<img src="{url}" alt="{alt_text}" class="rich-text-media">'
            elif media_type == 'video':
                return f'<video src="{url}" controls class="rich-text-media"><p>{alt_text}</p></video>'
            elif media_type == 'audio':
                return f'<audio src="{url}" controls class="rich-text-media"><p>{alt_text}</p></audio>'
            else:
                return f'<img src="{url}" alt="{alt_text}" class="rich-text-media">'
        
        # Pattern for media with optional type specification: ![alt](url) or ![alt](url){type}
        pattern = r'!\[(.*?)\]\((.*?)(?:\{([^}]*)\})?\)'
        return re.sub(pattern, replace_media, content)
    
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
    
    def _escape_text_preserve_tags(self, content: str) -> str:
        """Escape text content while preserving HTML tags"""
        # Split content into text and HTML tags
        parts = re.split(r'(<[^>]*>)', content)
        escaped_parts = []
        
        for part in parts:
            if part.startswith('<') and part.endswith('>'):
                # This is an HTML tag, preserve it
                escaped_parts.append(part)
            else:
                # This is text content, escape it
                escaped_parts.append(html.escape(part, quote=True))
        
        return ''.join(escaped_parts)
    
    def format(self, content: str) -> str:
        """Format the content according to rich text rules"""
        if not content:
            return ""
            
        # Format block-level elements first
        formatted = content
        formatted = self._format_blockquotes(formatted)
        
        # Format media and links
        formatted = self._format_media(formatted)
        formatted = self._format_links(formatted)
        
        # Format inline elements
        formatted = self._format_bold(formatted)
        formatted = self._format_italic(formatted)
        formatted = self._format_code(formatted)
        formatted = self._format_headers(formatted)
        formatted = self._format_horizontal_rules(formatted)
        formatted = self._format_tables(formatted)
        formatted = self._format_lists(formatted)
        
        # Wrap in paragraph if not already wrapped in a block element
        if not any(tag in formatted for tag in ['<h1>', '<h2>', '<h3>', '<h4>', '<h5>', '<h6>', '<ul>', '<ol>', '<table>', '<blockquote>']):
            formatted = f"<p>{formatted}</p>"
        
        # Escape text content while preserving HTML tags
        formatted = self._escape_text_preserve_tags(formatted)
        
        return formatted
    
    def validate(self, content: str) -> bool:
        """Validate the content for security and formatting"""
        if content is None:
            return False
            
        logger.debug(f"Validating content: {content}")
            
        # Check for matching markdown syntax
        if content.count('**') % 2 != 0:
            logger.debug("Unmatched bold markers")
            return False
            
        if content.count('*') % 2 != 0:
            logger.debug("Unmatched italic markers")
            return False
            
        if content.count('`') % 2 != 0:
            logger.debug("Unmatched code markers")
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
                logger.debug(f"XSS pattern detected: {pattern}")
                return False

        # Define allowed extensions for each media type
        allowed_extensions = {
            'image': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'],
            'video': ['mp4', 'webm', 'ogg'],
            'audio': ['mp3', 'wav', 'ogg', 'm4a']
        }

        # Validate media file types
        media_pattern = r'!\[(.*?)\]\((.*?)\)(?:\{(.*?)\})?'
        for match in re.finditer(media_pattern, content):
            url = match.group(2).strip()
            media_type = match.group(3).strip() if match.group(3) else None
            
            logger.debug(f"Found media: url={url}, type={media_type}")
            
            # Get file extension, handling query parameters
            url_parts = url.split('?')[0].lower()  # Remove query parameters
            if '.' not in url_parts:
                logger.debug("URL has no extension")
                continue  # Skip validation for URLs without extensions
            ext = url_parts.split('.')[-1]
            
            logger.debug(f"File extension: {ext}")
            
            # Special handling for .ogg files which can be both audio and video
            if ext == 'ogg':
                if media_type and media_type in ['audio', 'video']:
                    continue  # Both audio and video are valid for .ogg
                elif not media_type:
                    # If no type specified, default to audio (or could be video)
                    continue
            
            # Determine the expected media type based on extension
            expected_type = None
            for type_name, extensions in allowed_extensions.items():
                if ext in extensions:
                    expected_type = type_name
                    break
            
            # If media type is specified, validate against that type
            if media_type:
                if media_type not in allowed_extensions:
                    logger.debug(f"Invalid media type: {media_type}")
                    return False
                if ext not in allowed_extensions[media_type]:
                    logger.debug(f"Extension {ext} not allowed for type {media_type}")
                    return False
                # Skip media type matching for .ogg files
                if ext != 'ogg':
                    if expected_type and media_type != expected_type:
                        logger.debug(f"Media type {media_type} does not match extension type {expected_type}")
                        return False
            # If no media type specified, validate extension against allowed types
            else:
                if not expected_type:
                    logger.debug(f"Extension {ext} not allowed for any media type")
                    return False

        # Validate URL schemes
        url_pattern = r'\[(.*?)\]\((.*?)(?:\s+"([^"]*)")?\)'
        for match in re.finditer(url_pattern, content):
            url = match.group(2).strip()
            base_url = url.split('?')[0]  # Remove query parameters for scheme check
            
            # Skip URL scheme validation for media files
            is_media = bool(re.search(r'!\[.*?\]\(' + re.escape(url) + r'\)', content))
            if not is_media and not base_url.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                logger.debug(f"Invalid URL scheme: {base_url}")
                return False

        # Validate content length
        if len(content) > 10000:  # Maximum content length
            logger.debug("Content too long")
            return False

        # Validate nested formatting depth
        max_nesting = 3
        for char in ['*', '_', '`']:
            if content.count(char) > max_nesting * 2:
                logger.debug(f"Too many {char} characters")
                return False

        # Validate blockquote nesting
        max_blockquote_depth = 5
        for line in content.split('\n'):
            line = line.lstrip()
            quote_count = 0
            while line.startswith('>'):
                quote_count += 1
                line = line[1:].lstrip()
            if quote_count > max_blockquote_depth:
                logger.debug(f"Blockquote nesting too deep: {quote_count}")
                return False

        # Validate list nesting
        list_pattern = r'^(\s*)(?:[-*]|\d+\.)\s'
        max_list_depth = 3
        for line in content.split('\n'):
            match = re.match(list_pattern, line)
            if match:
                indent = len(match.group(1))
                if indent // 2 > max_list_depth - 1:  # Adjust for zero-based counting
                    logger.debug(f"List nesting too deep: {indent}")
                    return False

        # Validate nested formatting combinations
        invalid_patterns = [
            r'`[^`]*\*\*[^`]*`',  # Bold inside code
            r'`[^`]*\*[^`]*`',     # Italic inside code
            r'`[^`]*_[^`]*`'       # Underscore inside code
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, content):
                logger.debug(f"Invalid formatting pattern: {pattern}")
                return False

        # Special handling for mixed content
        lines = [line.strip() for line in content.strip().split('\n')]
        in_block = False  # Track if we're inside a block element
        
        for i, line in enumerate(lines):
            logger.debug(f"Processing line {i}: {line}")
            
            if not line:
                in_block = False
                continue
                
            # Check if line starts a block element
            if (line.startswith('#') or  # Headers
                line.startswith('>') or   # Blockquotes
                line.startswith('-') or   # Unordered lists
                line.startswith('*') or   # Unordered lists or emphasis
                line.startswith('|') or   # Tables
                re.match(r'^\d+\.', line) or  # Ordered lists
                re.match(r'^\s*[-*]', line) or  # Indented lists
                re.match(r'^\s*\d+\.', line)):  # Indented ordered lists
                logger.debug(f"Line {i} starts a block element")
                in_block = True
                continue
                
            # Check for inline elements
            if (re.match(r'.*!\[.*?\]\(.*?(?:\{[^}]*\})?\).*', line) or  # Images with optional type
                re.match(r'.*\[.*?\]\(.*?\).*', line) or  # Links
                re.match(r'.*\*\*.*\*\*.*', line) or  # Bold
                re.match(r'.*\*[^*]+\*.*', line) or  # Italic
                re.match(r'.*`[^`]+`.*', line) or  # Code
                line.strip().startswith('> ') or  # Blockquote
                line.strip().startswith('- ') or  # List item
                re.match(r'^\s*\d+\.\s', line) or  # Ordered list item
                line.strip() == '' or  # Empty line
                line.strip().isspace()):  # Whitespace-only line
                logger.debug(f"Line {i} contains valid inline elements")
                continue
                
            # If we're not in a block and the line contains markdown-like characters
            # but doesn't match any valid markdown pattern, it's invalid
            if not in_block and any(char in line for char in ['*', '_', '`', '[', ']', '(', ')']):
                logger.debug(f"Line {i} contains invalid markdown characters")
                return False
            
        logger.debug("Content validation passed")
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