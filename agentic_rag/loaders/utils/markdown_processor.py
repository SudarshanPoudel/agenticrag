import re
import markdown
from bs4 import BeautifulSoup
from typing import Union, List

class MarkdownTextChunks:
    def __init__(self, headings, content):
        self.chunk_type = 'text'
        self.headings = headings
        self.content = content
        self.heading_length = self._get_heading_length()
        self.markdown_str = self._to_markdown()
        self.length = len(self.markdown_str)

    def _get_heading_length(self):
        length = 0
        for heading in self.headings:
            length += (len(heading['heading']) + heading['level'] + 2)
        return length

    
    def _to_markdown(self):
        md_str = ''
        for heading in self.headings:
            md_str += f"{'#' * heading['level']} {heading['heading']}\n"
        md_str += self.content
        return md_str
    
    
class MarkdownTableChunks:
    def __init__(self, headings, cells):
        self.headings = headings
        self.cells = cells
        self.markdown_str = self._to_markdown()
        self.length = len(self.markdown_str)

    def _to_markdown(self):
        col_widths = [
            max(len(str(cell)) for cell in col) 
            for col in zip(self.headings, *self.cells)
        ]
        header_row = " | ".join(f"{heading.ljust(col_widths[i])}" for i, heading in enumerate(self.headings))
        separator_row = "|".join("-" * width for width in col_widths)
        
        # Format the content rows
        content_rows = []
        for row in self.cells:
            content_row = " | ".join(f"{str(cell).ljust(col_widths[i])}" for i, cell in enumerate(row))
            content_rows.append(content_row)

        md = f"{header_row}\n{separator_row}\n" + "\n".join(content_rows)
        return md
        

class MarkdownDocumentConverter:
    def __init__(self):
        pass

    def convert(self, md_str:str)->List[Union[MarkdownTableChunks, MarkdownTextChunks]]:
        result = []
        headings_stack = []
        lines = md_str.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i]
            heading_match = re.match(r'^(#+)\s+(.*)', line)
            
            if heading_match:
                # Match headings
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                headings_stack = [h for h in headings_stack if h['level'] < level]
                headings_stack.append({'heading': heading_text, 'level': level})
                i += 1
            elif '|' in line and '---' not in line:
                # Match tables
                table_lines = []
                while i < len(lines) and ('|' in lines[i] or '---' in lines[i]):
                    table_lines.append(lines[i])
                    i += 1

                html_table = markdown.markdown('\n'.join(table_lines), extensions=['tables'])
                soup = BeautifulSoup(html_table, 'html.parser')
                table = soup.find('table')

                if table:
                    headers = [th.get_text().strip() for th in table.find_all('th')]
                    rows = [
                        [td.get_text().strip() for td in row.find_all('td')]
                        for row in table.find_all('tr')[1:]  # Skip header row
                    ]
                    result.append(MarkdownTableChunks(
                        headings=headers,
                        cells=rows
                    ))
            elif line.strip():
                # Match content
                content_lines = []
                while i < len(lines) and lines[i].strip() and not re.match(r'^(#+)\s+(.*)', lines[i]) and '|' not in lines[i]:
                    content_lines.append(lines[i].strip())
                    i += 1

                content = ' '.join(content_lines)
                result.append(MarkdownTextChunks(
                    headings=headings_stack,
                    content=content
                ))
            else:
                i += 1

        return result