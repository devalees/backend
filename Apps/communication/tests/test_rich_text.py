import pytest
from Apps.communication.rich_text import RichTextMessage, RichTextFormatter

def test_rich_text_message_creation():
    """Test creating a new rich text message"""
    message = RichTextMessage("Hello, **world**!")
    assert message.raw_content == "Hello, **world**!"
    assert message.formatted_content == "<p>Hello, <strong>world</strong>!</p>"

def test_rich_text_formatting():
    """Test basic rich text formatting"""
    formatter = RichTextFormatter()
    
    # Test bold
    assert formatter.format("**bold**") == "<p><strong>bold</strong></p>"
    
    # Test italic
    assert formatter.format("*italic*") == "<p><em>italic</em></p>"
    
    # Test code
    assert formatter.format("`code`") == "<p><code>code</code></p>"

def test_rich_text_media_embedding():
    """Test media embedding in rich text messages"""
    formatter = RichTextFormatter()
    
    # Test image embedding
    content = "![Alt text](https://example.com/image.jpg)"
    formatted = formatter.format(content)
    assert '<img src="https://example.com/image.jpg" alt="Alt text" class="rich-text-media">' in formatted
    
    # Test video embedding with explicit type
    content = "![Video description](https://example.com/video.mp4){video}"
    formatted = formatter.format(content)
    assert '<video src="https://example.com/video.mp4" controls class="rich-text-media">' in formatted
    assert '<p>Video description</p>' in formatted
    
    # Test video embedding with extension detection
    content = "![Video description](https://example.com/video.webm)"
    formatted = formatter.format(content)
    assert '<video src="https://example.com/video.webm" controls class="rich-text-media">' in formatted
    
    # Test audio embedding with explicit type
    content = "![Audio description](https://example.com/audio.mp3){audio}"
    formatted = formatter.format(content)
    assert '<audio src="https://example.com/audio.mp3" controls class="rich-text-media">' in formatted
    assert '<p>Audio description</p>' in formatted
    
    # Test audio embedding with extension detection
    content = "![Audio description](https://example.com/audio.wav)"
    formatted = formatter.format(content)
    assert '<audio src="https://example.com/audio.wav" controls class="rich-text-media">' in formatted
    
    # Test multiple media types in one message
    content = """
    ![Image](https://example.com/image.png)
    ![Video](https://example.com/video.mp4){video}
    ![Audio](https://example.com/audio.mp3){audio}
    """
    formatted = formatter.format(content)
    assert '<img src="https://example.com/image.png" alt="Image" class="rich-text-media">' in formatted
    assert '<video src="https://example.com/video.mp4" controls class="rich-text-media">' in formatted
    assert '<audio src="https://example.com/audio.mp3" controls class="rich-text-media">' in formatted
    
    # Test media with special characters in alt text
    content = '![Special & "characters"](https://example.com/image.jpg)'
    formatted = formatter.format(content)
    assert 'alt="Special &amp; &quot;characters&quot;"' in formatted
    
    # Test media with spaces in URL
    content = '![Alt text](https://example.com/image with spaces.jpg)'
    formatted = formatter.format(content)
    assert 'src="https://example.com/image%20with%20spaces.jpg"' in formatted
    
    # Test media with invalid type
    content = '![Alt text](https://example.com/image.jpg){invalid}'
    formatted = formatter.format(content)
    assert '<img src="https://example.com/image.jpg" alt="Alt text" class="rich-text-media">' in formatted

def test_rich_text_validation():
    """Test content validation"""
    formatter = RichTextFormatter()
    
    # Test valid content
    assert formatter.validate("Normal text") is True
    
    # Test invalid content (script injection attempt)
    assert formatter.validate("<script>alert('xss')</script>") is False

def test_rich_text_preview():
    """Test preview generation"""
    message = RichTextMessage("This is a **preview** test")
    preview = message.generate_preview()
    assert len(preview) <= 100  # Preview should be truncated
    assert "preview" in preview.lower()

def test_rich_text_combinations():
    """Test combining multiple formatting options"""
    formatter = RichTextFormatter()
    content = "**Bold** and *italic* with `code`"
    formatted = formatter.format(content)
    
    assert "<strong>Bold</strong>" in formatted
    assert "<em>italic</em>" in formatted
    assert "<code>code</code>" in formatted

def test_rich_text_lists():
    """Test list formatting (ordered and unordered)"""
    formatter = RichTextFormatter()
    
    # Test unordered list
    unordered_content = """
    - Item 1
    - Item 2
    - Item 3
    """
    formatted = formatter.format(unordered_content)
    assert "<ul>" in formatted
    assert "<li>Item 1</li>" in formatted
    assert "<li>Item 2</li>" in formatted
    assert "<li>Item 3</li>" in formatted
    
    # Test ordered list
    ordered_content = """
    1. First item
    2. Second item
    3. Third item
    """
    formatted = formatter.format(ordered_content)
    assert "<ol>" in formatted
    assert "<li>First item</li>" in formatted
    assert "<li>Second item</li>" in formatted
    assert "<li>Third item</li>" in formatted

def test_rich_text_tables():
    """Test table formatting"""
    formatter = RichTextFormatter()
    
    table_content = """
    | Header 1 | Header 2 |
    |----------|----------|
    | Cell 1   | Cell 2   |
    | Cell 3   | Cell 4   |
    """
    formatted = formatter.format(table_content)
    assert "<table>" in formatted
    assert "<thead>" in formatted
    assert "<th>Header 1</th>" in formatted
    assert "<th>Header 2</th>" in formatted
    assert "<tbody>" in formatted
    assert "<td>Cell 1</td>" in formatted
    assert "<td>Cell 2</td>" in formatted

def test_rich_text_links():
    """Test link formatting"""
    formatter = RichTextFormatter()
    
    # Test basic link
    assert formatter.format("[Google](https://google.com)") == '<p><a href="https://google.com">Google</a></p>'
    
    # Test link with title
    assert formatter.format('[Google](https://google.com "Google Search")') == '<p><a href="https://google.com" title="Google Search">Google</a></p>'

def test_rich_text_blockquotes():
    """Test blockquote formatting"""
    formatter = RichTextFormatter()
    
    content = "> This is a blockquote\n> with multiple lines"
    formatted = formatter.format(content)
    assert "<blockquote>" in formatted
    assert "This is a blockquote" in formatted
    assert "with multiple lines" in formatted

def test_rich_text_headers():
    """Test header formatting"""
    formatter = RichTextFormatter()
    
    # Test different header levels
    assert formatter.format("# Header 1") == "<h1>Header 1</h1>"
    assert formatter.format("## Header 2") == "<h2>Header 2</h2>"
    assert formatter.format("### Header 3") == "<h3>Header 3</h3>"

def test_rich_text_horizontal_rules():
    """Test horizontal rule formatting"""
    formatter = RichTextFormatter()
    
    content = "Some text\n---\nMore text"
    formatted = formatter.format(content)
    assert "<hr>" in formatted
    assert "Some text" in formatted
    assert "More text" in formatted

def test_rich_text_nested_formatting():
    """Test nested formatting combinations"""
    formatter = RichTextFormatter()
    
    # Test nested formatting in lists
    content = """
    - **Bold item**
    - *Italic item*
    - `Code item`
    - [Link item](url)
    """
    formatted = formatter.format(content)
    assert "<strong>Bold item</strong>" in formatted
    assert "<em>Italic item</em>" in formatted
    assert "<code>Code item</code>" in formatted
    assert "<a href=" in formatted
    
    # Test nested formatting in blockquotes
    content = "> **Bold quote** with *italic* and `code`"
    formatted = formatter.format(content)
    assert "<strong>Bold quote</strong>" in formatted
    assert "<em>italic</em>" in formatted
    assert "<code>code</code>" in formatted 

def test_rich_text_validation_media_types():
    """Test media type validation"""
    formatter = RichTextFormatter()
    
    # Test valid image types
    assert formatter.validate("![Alt](image.jpg)") is True
    assert formatter.validate("![Alt](image.png)") is True
    assert formatter.validate("![Alt](image.gif)") is True
    assert formatter.validate("![Alt](image.webp)") is True
    assert formatter.validate("![Alt](image.svg)") is True
    
    # Test valid video types
    assert formatter.validate("![Alt](video.mp4){video}") is True
    assert formatter.validate("![Alt](video.webm){video}") is True
    assert formatter.validate("![Alt](video.ogg){video}") is True
    
    # Test valid audio types
    assert formatter.validate("![Alt](audio.mp3){audio}") is True
    assert formatter.validate("![Alt](audio.wav){audio}") is True
    assert formatter.validate("![Alt](audio.ogg){audio}") is True
    assert formatter.validate("![Alt](audio.m4a){audio}") is True
    
    # Test invalid file types
    assert formatter.validate("![Alt](file.exe)") is False
    assert formatter.validate("![Alt](file.bat)") is False
    assert formatter.validate("![Alt](file.php)") is False
    
    # Test mismatched media type and extension
    assert formatter.validate("![Alt](image.jpg){video}") is False
    assert formatter.validate("![Alt](video.mp4){audio}") is False
    assert formatter.validate("![Alt](audio.mp3){image}") is False

def test_rich_text_validation_url_schemes():
    """Test URL scheme validation"""
    formatter = RichTextFormatter()
    
    # Test valid URL schemes
    assert formatter.validate("[Link](https://example.com)") is True
    assert formatter.validate("[Link](http://example.com)") is True
    assert formatter.validate("[Email](mailto:user@example.com)") is True
    assert formatter.validate("[Phone](tel:+1234567890)") is True
    
    # Test invalid URL schemes
    assert formatter.validate("[Link](javascript:alert('xss'))") is False
    assert formatter.validate("[Link](data:text/html,<script>alert('xss')</script>)") is False
    assert formatter.validate("[Link](file:///etc/passwd)") is False
    assert formatter.validate("[Link](ftp://example.com)") is False

def test_rich_text_validation_content_length():
    """Test content length validation"""
    formatter = RichTextFormatter()
    
    # Test valid content length
    assert formatter.validate("Short content") is True
    assert formatter.validate("A" * 10000) is True
    
    # Test invalid content length
    assert formatter.validate("A" * 10001) is False

def test_rich_text_validation_nested_formatting():
    """Test nested formatting validation"""
    formatter = RichTextFormatter()
    
    # Test valid nesting
    assert formatter.validate("**bold** *italic* `code`") is True
    assert formatter.validate("**bold *italic* bold**") is True
    assert formatter.validate("**bold `code` bold**") is True
    
    # Test invalid nesting (too deep)
    assert formatter.validate("**bold *italic **bold** italic* bold**") is False
    assert formatter.validate("`code **bold** code`") is False

def test_rich_text_validation_blockquote_nesting():
    """Test blockquote nesting validation"""
    formatter = RichTextFormatter()
    
    # Test valid blockquote nesting
    assert formatter.validate("> Quote\n> Quote\n> Quote") is True
    assert formatter.validate("> Quote\n> > Nested\n> Quote") is True
    
    # Test invalid blockquote nesting (too deep)
    assert formatter.validate("> > > > > > Too deep") is False

def test_rich_text_validation_list_nesting():
    """Test list nesting validation"""
    formatter = RichTextFormatter()
    
    # Test valid list nesting
    assert formatter.validate("- Item 1\n  - Item 1.1\n    - Item 1.1.1") is True
    assert formatter.validate("1. Item 1\n  1. Item 1.1\n    1. Item 1.1.1") is True
    
    # Test invalid list nesting (too deep)
    assert formatter.validate("- Item 1\n  - Item 1.1\n    - Item 1.1.1\n      - Item 1.1.1.1") is False
    assert formatter.validate("1. Item 1\n  1. Item 1.1\n    1. Item 1.1.1\n      1. Item 1.1.1.1") is False

def test_rich_text_validation_media_url_parameters():
    """Test media URL with query parameters"""
    formatter = RichTextFormatter()
    
    # Test valid media URLs with parameters
    assert formatter.validate("![Alt](image.jpg?width=100&height=100)") is True
    assert formatter.validate("![Alt](video.mp4?t=10)") is True
    assert formatter.validate("![Alt](audio.mp3?start=30)") is True
    
    # Test invalid media URLs with parameters
    assert formatter.validate("![Alt](file.exe?param=value)") is False
    assert formatter.validate("![Alt](script.php?cmd=rm)") is False

def test_rich_text_validation_mixed_content():
    """Test validation of mixed content types"""
    formatter = RichTextFormatter()
    
    # Test valid mixed content
    content = """
    # Header
    ![Image](image.jpg)
    [Link](https://example.com)
    > Quote
    - List item
    **Bold** *italic* `code`
    """
    assert formatter.validate(content) is True
    
    # Test invalid mixed content
    invalid_content = """
    # Header
    ![Invalid](file.exe)
    [Invalid](javascript:alert('xss'))
    > > > > > > Too deep
    - - - - Too deep
    """
    assert formatter.validate(invalid_content) is False 