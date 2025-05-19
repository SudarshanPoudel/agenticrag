from langchain.text_splitter import RecursiveCharacterTextSplitter
from .markdown_processor import MarkdownDocumentConverter, MarkdownTableChunks, MarkdownTextChunks
from typing import List, Union

class MarkdownSplitter:
    def __init__(self, chunk_size, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self,  text:Union[str, None] = None)->List[str]:
        """Splits a markdown document into manageable chunks."""
        self.markdown_str = text
    
        converter = MarkdownDocumentConverter()
        doc_chunks = converter.convert(self.markdown_str)

        split_chunks = self._split_chunks(doc_chunks) # Split based on headings and table size
        merged_chunks = self._merge_text_chunks(split_chunks) # Merge smaller text chunks, and adjust headings
        final_chunks = self._final_merge(merged_chunks) # Final merge, capable of merging text and tables in markdown
        
        return final_chunks

   
    def _split_chunks(self, doc_chunks:List[Union[MarkdownTextChunks, MarkdownTableChunks]]):
        """Checks each chunks and splits oversized chunks."""
        result = []
        for chunk in doc_chunks:
            if chunk.length <= self.chunk_size:
                result.append(chunk)
            else:
                result.extend(self._split_chunk(chunk))
        return result

    def _split_chunk(self, chunk:Union[MarkdownTextChunks, MarkdownTableChunks])->List[Union[MarkdownTextChunks, MarkdownTableChunks]]:
        """Splits a single oversized chunk."""
        if isinstance(chunk, MarkdownTextChunks):
            while (self.chunk_size // 2 < chunk.heading_length):
                if not chunk.headings:
                    chunk.heading_length = 0
                else:
                    chunk.headings.pop(0)
                    chunk.heading_length -= chunk._get_heading_length()


            text_splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", ".", "?", "\n", " "],
                chunk_size=self.chunk_size - chunk.heading_length,
                chunk_overlap=self.chunk_overlap
            )
            splits = text_splitter.split_text(chunk.content)
            return [MarkdownTextChunks(headings=chunk.headings, content=split) for split in splits]

        elif isinstance(chunk, MarkdownTableChunks):
            chunks = []
            start = 0
            total_rows = len(chunk.cells)
            while start < total_rows:
                end = min(start + (len(chunk.cells) // 2), total_rows)
                chunks.append(
                    MarkdownTableChunks(
                        headings=chunk.headings,
                        cells=chunk.cells[start:end]
                    )
                )
                # Adjust the start index with overlap
                start = max(0, end)
            return chunks
        
        return [chunk]

    def _merge_text_chunks(self, chunks:List[Union[MarkdownTextChunks, MarkdownTableChunks]])->List[Union[MarkdownTextChunks, MarkdownTableChunks]]:
        """Merges smaller text chunks while checking for headers"""
        merged_chunks = []
        current_chunk = None

        for chunk in chunks:
            if isinstance(current_chunk, MarkdownTextChunks) and isinstance(chunk, MarkdownTextChunks):
                combined_chunk = self._merge_two_text_chunks(current_chunk, chunk)
                if combined_chunk.length <= self.chunk_size:
                    current_chunk = combined_chunk
                else:
                    merged_chunks.append(current_chunk)
                    current_chunk = chunk
            else:
                if current_chunk:
                    merged_chunks.append(current_chunk)
                current_chunk = chunk

        if current_chunk:
            merged_chunks.append(current_chunk)

        return merged_chunks

    def _merge_two_text_chunks(self, chunk1:MarkdownTextChunks, chunk2:MarkdownTextChunks)->MarkdownTextChunks:
        """Merges two text chunks."""
        def format_heading(heading):
            return f"{'#' * heading['level']} {heading['heading']}\n"

        common_headings = self._find_common_headings(chunk1.headings, chunk2.headings)
        unique_headings_chunk1 = [
            h for h in chunk1.headings if h not in common_headings
        ]
        unique_headings_chunk2 = [
            h for h in chunk2.headings if h not in common_headings
        ]

        # Format unique headings as markdown and append contents
        content = "".join(format_heading(h) for h in unique_headings_chunk1) + chunk1.content + "\n" + \
                "".join(format_heading(h) for h in unique_headings_chunk2) + chunk2.content

        # Build the merged chunk
        merged_chunk = MarkdownTextChunks(
            headings=common_headings,
            content=content.strip()
        )
        return merged_chunk

    def _find_common_headings(self, headings1, headings2):
        """Finds common headings between two sets."""
        return [h for h in headings1 if h in headings2]

    def _final_merge(self, chunks):
        """Performs a final merge of all chunk types based on their markdown strings."""
        merged_chunks = []
        current_chunk = ""

        for chunk in chunks:
            chunk_md = chunk.markdown_str  # Get the markdown string representation
            if len(current_chunk) + len(chunk_md) < self.chunk_size:
                current_chunk += ("\n" if current_chunk else "") + chunk_md
            else:
                if current_chunk:
                    merged_chunks.append(current_chunk)
                current_chunk = chunk_md

        if current_chunk:
            merged_chunks.append(current_chunk)
        cleaned_header_chunks = self._clean_headers(merged_chunks)
        return cleaned_header_chunks
    
    def _clean_headers(self, chunks):
        """Removes duplicate headers within the final merged chunks for all header levels."""
        cleaned_chunks = []
        for chunk in chunks:
            if isinstance(chunk, str):
                lines = chunk.split("\n")
                seen_headers = set()
                filtered_lines = []
                for line in lines:
                    # Check if the line is a header (starts with one or more '#')
                    if line.startswith("#"):
                        # Extract the header text, ignoring leading '#' and spaces
                        header_text = line.lstrip("# ").strip()
                        # If this header text hasn't been seen before, keep it
                        if header_text not in seen_headers:
                            filtered_lines.append(line)
                            seen_headers.add(header_text)
                        else:
                            filtered_lines.append('')

                    else:
                        # For non-header lines, just add them
                        filtered_lines.append(line)
                # Rebuild the chunk with filtered lines
                chunk = "\n".join(filtered_lines)
            cleaned_chunks.append(chunk)
        return cleaned_chunks