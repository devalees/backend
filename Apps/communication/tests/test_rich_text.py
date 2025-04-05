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
    """Test embedding media in rich text"""
    message = RichTextMessage("Check this image: ![alt](https://example.com/image.jpg)")
    assert "img" in message.formatted_content
    assert "src=\"https://example.com/image.jpg\"" in message.formatted_content

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