# Document Ingestion & Chunking Strategy for Production RAG

## Overview

Production RAG ingestion should not be treated as:

```text
File → Extract text → Split every N tokens → Embed
```

A better approach is:

```text
File
  ↓
Format-aware parsing
  ↓
OCR / vision when required
  ↓
Cleaning & normalization
  ↓
Structure preservation
  ↓
Document-aware chunking
  ↓
Metadata enrichment
  ↓
Embeddings
  ↓
Vector store
```

The key principle is:

> **Never destroy document structure before chunking.**

A paragraph, Excel row, PowerPoint slide, table, chart, and diagram should not all be treated as plain text.

---

# 1. Recommended Ingestion Architecture

```text
                         ┌─────────────────┐
                         │   Source File   │
                         └────────┬────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │ File Type Detection       │
                    │ PDF/DOCX/PPTX/XLSX/...    │
                    └─────────────┬─────────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
        Text parser          Structured parser      OCR/Vision
        PDF/DOCX/TXT         XLSX/CSV/HTML          scanned/image
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │ Normalize / Clean       │
                    │ headers, whitespace,    │
                    │ encoding, artifacts     │
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ Preserve Structure      │
                    │ tables/charts/sections/ │
                    │ slide/page relationships│
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ Document-aware Chunking  │
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ Metadata enrichment     │
                    │ page/slide/table/etc.   │
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ Embedding + Vector DB   │
                    └─────────────────────────┘
```

---

# 2. Quick Recommendation by Document Type

| Type | Extraction | OCR? | Cleaning | Recommended Chunking |
|---|---|---|---|---|
| PDF | PDF parser | If scanned | High | Hierarchical / semantic |
| DOCX | Paragraphs, headings, tables | If images/scans | Medium | Hierarchical |
| PPTX | Slides, text boxes, notes | Sometimes | Medium | Slide-aware |
| XLSX | Sheets, cells, tables | Usually no | High | Table/row-aware |
| CSV | Rows/columns | No | Medium | Row/group-aware |
| HTML | DOM | Usually no | High | DOM/semantic |
| TXT | Raw text | No | Medium | Recursive/semantic |
| Scanned documents | OCR | Yes | High | Layout + hierarchical |
| Screenshots | Vision/OCR | Yes | High | Image-aware / semantic |

---

# 3. PDF

## 3.1 Extraction

For a normal text PDF:

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")

pages = []

for page_number, page in enumerate(reader.pages, start=1):
    text = page.extract_text()

    pages.append({
        "page_number": page_number,
        "text": text or ""
    })
```

PDFs can contain:

```text
PDF
 ├── real text
 ├── scanned image
 ├── tables
 ├── charts
 ├── diagrams
 ├── headers/footers
 └── mixed content
```

A PDF parser may extract text successfully while losing the visual relationship between elements.

## 3.2 OCR

Use OCR when a PDF contains scanned pages.

```text
Scanned PDF
     ↓
Render page as image
     ↓
OCR
     ↓
Text + bounding boxes
```

OCR is necessary because a scanned PDF may contain pixels rather than actual text characters.

Possible OCR/document-understanding technologies include:

- Amazon Textract
- Amazon Bedrock Data Automation
- Tesseract
- PaddleOCR
- Other cloud OCR/document AI services

For an AWS-centric system, Textract or Bedrock Data Automation are natural options.

## 3.3 Cleaning

Typical PDF cleanup:

```python
import re

def clean_pdf_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
```

Do not blindly remove line breaks because they can represent:

- table rows
- headings
- list items
- code
- addresses

## 3.4 Chunking

For long PDFs, use:

- hierarchical chunking
- semantic + structural chunking

Example:

```text
Parent: 1500 tokens
Child:   400 tokens
Overlap: 50 tokens
```

The child chunk provides precise retrieval while the parent provides broader context.

---

# 4. DOCX

DOCX already contains useful structural information.

```text
Document
 ├── Heading 1
 │    ├── Paragraph
 │    ├── Paragraph
 │    └── Table
 ├── Heading 1
 │    └── Paragraph
 └── Heading 1
```

## 4.1 Paragraph extraction

```python
from docx import Document

doc = Document("report.docx")

for paragraph in doc.paragraphs:
    print(paragraph.style.name)
    print(paragraph.text)
```

## 4.2 Table extraction

```python
for table in doc.tables:
    for row in table.rows:
        values = [cell.text for cell in row.cells]
        print(values)
```

## 4.3 OCR

Normally no OCR is required for DOCX text.

OCR is needed when useful information exists inside:

- scanned images
- screenshots
- image-based pages
- diagrams containing text

## 4.4 Cleaning

Preserve:

- heading hierarchy
- numbered lists
- bullet lists
- tables
- captions

Example:

```text
## Authentication

The system uses OAuth 2.0.

### Token Flow

1. User authenticates.
2. Authorization server returns code.
3. Backend exchanges code for tokens.
```

This is better for RAG than flattening everything into one string.

## 4.5 Chunking

Use hierarchical chunking:

```text
Parent:
Authentication

Children:
OAuth token flow
Refresh token flow
Token expiration
```

---

# 5. PPTX

PowerPoint requires slide-aware processing.

A slide can contain:

```text
Slide
 ├── title
 ├── text boxes
 ├── bullet points
 ├── speaker notes
 ├── table
 ├── chart
 ├── diagram
 └── image
```

## 5.1 Text extraction

```python
from pptx import Presentation

prs = Presentation("presentation.pptx")

for slide_number, slide in enumerate(prs.slides, start=1):

    for shape in slide.shapes:

        if hasattr(shape, "text"):
            print(shape.text)
```

## 5.2 OCR

OCR/vision may be required for:

- screenshots embedded in slides
- scanned images
- diagrams containing text
- images containing labels

## 5.3 Preserve slide relationships

Instead of flattening:

```text
Revenue increased 20%
Product A 40%
Product B 60%
```

store:

```json
{
  "slide_number": 7,
  "slide_title": "Revenue Breakdown",
  "content": "...",
  "visual_type": "chart",
  "visual_id": "slide7_chart1"
}
```

Then preserve:

```text
slide7_chart1
      ↓
Revenue Breakdown
      ↓
Product A = 40%
Product B = 60%
```

## 5.4 Chunking

Use slide-aware chunking first.

```text
Slide 1 → chunk
Slide 2 → chunk
Slide 3 → chunk
```

Avoid creating chunks that arbitrarily span multiple unrelated slides.

If a slide is very large, split it into logical sections while retaining the slide number in metadata.

---

# 6. XLSX

Excel requires structured extraction.

Do not convert an entire workbook into one giant string.

Use:

```text
Workbook
 ├── Sheet: Revenue
 │    ├── Header
 │    ├── Row
 │    ├── Row
 │    └── Row
 │
 ├── Sheet: Expenses
 │    └── ...
```

## 6.1 Extraction

```python
from openpyxl import load_workbook

wb = load_workbook("financials.xlsx", data_only=True)

for ws in wb.worksheets:
    print("Sheet:", ws.title)

    for row in ws.iter_rows(values_only=True):
        print(row)
```

## 6.2 Cleaning

Consider normalizing:

- `None`
- `NaN`
- merged cells
- empty rows
- duplicate headers
- formatting-only rows

But do not remove important values.

Prefer:

```text
Sheet: Financial Summary
Year: 2026
Metric: Revenue
Value: $2.4M
```

over:

```text
2026 Revenue $2.4M
```

## 6.3 Chunking

Use table-aware / row-group chunking.

Example:

```text
Table: Revenue

Columns:
Year | Region | Product | Revenue

Rows:
2024 | APAC | A | 100
2024 | APAC | B | 200
2024 | EU   | A | 150
```

Create chunks around logical groups of rows rather than arbitrary token boundaries.

For analytical questions such as:

> What was total revenue in APAC?

consider SQL/structured retrieval instead of relying only on vector search.

---

# 7. CSV

Example:

```csv
product,region,revenue
A,APAC,100
B,APAC,200
C,EU,300
```

## 7.1 Extraction

```python
import csv

with open("sales.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        print(row)
```

## 7.2 Convert rows into semantic text

```python
def row_to_text(row):
    return (
        f"Product: {row['product']}\n"
        f"Region: {row['region']}\n"
        f"Revenue: {row['revenue']}"
    )
```

## 7.3 Chunking

Use row/group-aware chunking.

Example:

```text
Dataset: Sales

Columns:
product, region, revenue

Rows:
1-50
```

For analytical datasets, combine RAG with structured querying where appropriate.

---

# 8. HTML

HTML should be parsed as a DOM instead of being treated as raw text.

```python
from bs4 import BeautifulSoup

with open("page.html", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

for tag in soup(["script", "style", "nav", "footer"]):
    tag.decompose()

text = soup.get_text("\n", strip=True)
```

## 8.1 Cleaning

Usually remove:

```text
<script>
<style>
navigation
cookie banners
tracking elements
ads
footer
```

Preserve:

```text
<h1>
<h2>
<h3>
<table>
<ol>
<ul>
```

because they provide structure.

## 8.2 Chunking

Recommended:

**DOM/heading-aware + semantic chunking**

Example:

```text
H1: Authentication
    H2: OAuth
        paragraphs...

    H2: JWT
        paragraphs...

H1: Authorization
    H2: RBAC
        paragraphs...
```

---

# 9. TXT

TXT is straightforward.

```python
with open("document.txt", encoding="utf-8") as f:
    text = f.read()
```

Cleaning:

```python
import re

text = text.replace("\r\n", "\n")
text = re.sub(r"[ \t]+", " ", text)
text = re.sub(r"\n{3,}", "\n\n", text)
```

Recommended chunking:

- Recursive character splitting
- Semantic chunking
- Section-aware chunking for structured text

---

# 10. Scanned Documents

The processing pipeline is different from a digital PDF.

Digital PDF:

```text
PDF
 ↓
Text extraction
 ↓
Chunks
```

Scanned PDF:

```text
PDF
 ↓
Image
 ↓
OCR
 ↓
Text + coordinates
 ↓
Structure reconstruction
 ↓
Chunks
```

OCR should ideally provide:

```text
word
bounding box
confidence
page
line
table information
```

This helps preserve layout.

Example source:

```text
        Revenue Report

Region       Revenue
APAC         $2M
Europe       $3M
US           $5M
```

Poor OCR representation:

```text
Revenue Report Region Revenue APAC $2M Europe $3M US $5M
```

Better representation:

```text
Title: Revenue Report

Table:
Region | Revenue
APAC   | $2M
Europe | $3M
US     | $5M
```

This is much better for retrieval.

---

# 11. Screenshots

Screenshots are an image-understanding problem.

```text
Screenshot
   ↓
Vision model / OCR
   ↓
Text
+
UI elements
+
Relationships
```

For example:

```text
┌────────────────────────────┐
│ User Profile               │
│                            │
│ Name: Balaji               │
│ Status: Active             │
│                            │
│ [Save] [Cancel]            │
└────────────────────────────┘
```

Instead of only storing:

```text
User Profile Name Balaji Status Active Save Cancel
```

store structured information:

```json
{
  "type": "ui_screenshot",
  "title": "User Profile",
  "fields": {
    "Name": "Balaji",
    "Status": "Active"
  },
  "buttons": ["Save", "Cancel"]
}
```

For screenshots containing diagrams/charts, use a vision-capable document/image parser.

---

# 12. Preserving Tables

Tables should not normally be flattened into arbitrary text chunks.

Example:

| Product | Region | Revenue |
|---|---|---:|
| A | APAC | $2M |
| B | EU | $3M |

Bad representation:

```text
Product Region Revenue A APAC $2M B EU $3M
```

Better:

```text
Table: Revenue by Product and Region

Columns:
Product | Region | Revenue

Row:
Product=A
Region=APAC
Revenue=$2M

Row:
Product=B
Region=EU
Revenue=$3M
```

Best practice is to retain both structured and retrieval-friendly forms.

```json
{
  "document_id": "doc123",
  "page": 5,
  "table_id": "table_5_1",
  "headers": ["Product", "Region", "Revenue"],
  "rows": [
    ["A", "APAC", "$2M"],
    ["B", "EU", "$3M"]
  ]
}
```

Retrieval-friendly representation:

```text
Table: Revenue by Product and Region

Product A in APAC generated $2M revenue.
Product B in EU generated $3M revenue.
```

This gives the RAG system:

**structured representation + retrieval-friendly representation.**

---

# 13. Preserving Charts

Consider:

```text
Revenue

2024 █████ $2M
2025 ███████ $3M
2026 █████████ $5M
```

Do not store only the image.

Extract:

```json
{
  "chart_type": "bar",
  "title": "Revenue",
  "x_axis": "Year",
  "y_axis": "Revenue",
  "data": [
    {"year": 2024, "revenue": "$2M"},
    {"year": 2025, "revenue": "$3M"},
    {"year": 2026, "revenue": "$5M"}
  ]
}
```

You can also create retrieval-friendly text:

```text
Chart: Revenue

Revenue increased from $2M in 2024
to $5M in 2026.
```

The original chart should still be retained as an artifact when citations or visual verification are required.

---

# 14. Preserving Diagrams

Diagrams are difficult because meaning comes from relationships, not only text.

Example:

```text
User
 ↓
API Gateway
 ↓
Auth Service
 ↓
Database
```

OCR might return:

```text
User API Gateway Auth Service Database
```

The relationships have been lost.

Instead, preserve them explicitly:

```json
{
  "diagram_type": "architecture",
  "nodes": [
    "User",
    "API Gateway",
    "Auth Service",
    "Database"
  ],
  "relationships": [
    ["User", "API Gateway"],
    ["API Gateway", "Auth Service"],
    ["Auth Service", "Database"]
  ]
}
```

This is an important distinction:

> OCR extracts visible text. Document understanding preserves the meaning and relationships encoded by layout.

---

# 15. Preserve Document Relationships with IDs

Every structural element should ideally have an identifier.

```text
document_id
    │
    ├── page_1
    │     ├── section_1
    │     ├── table_1
    │     └── figure_1
    │
    ├── page_2
    │     ├── section_2
    │     └── figure_2
```

Example chunk metadata:

```json
{
  "document_id": "financial_report_2026",
  "page": 12,
  "section": "Revenue Analysis",
  "chunk_id": "chunk_12_03",
  "element_type": "table",
  "table_id": "table_12_1",
  "parent_section": "Revenue Analysis"
}
```

This allows the application to reconstruct context after retrieval.

---

# 16. Parent-Child Chunking

For complex documents:

```text
Document
    │
    ├── Parent chunk
    │      │
    │      ├── Child chunk
    │      ├── Child chunk
    │      └── Child chunk
    │
    └── Parent chunk
           │
           ├── Child
           └── Child
```

Example:

```text
Parent:
Revenue Analysis — Q1 2026

Children:
1. Regional revenue
2. Product revenue
3. Revenue chart
4. Revenue commentary
```

Retrieval can find:

```text
Child:
Product A generated $4M...
```

while generation can receive:

```text
Parent:
Revenue Analysis — Q1 2026

Child:
Product A generated $4M...
```

This gives precise retrieval with broader generation context.

---

# 17. Recommended Chunking Strategy by File Type

| Document | Recommended Strategy |
|---|---|
| PDF | Hierarchical |
| DOCX | Hierarchical |
| PPTX | Slide-aware + hierarchical |
| XLSX | Table/row-aware |
| CSV | Row/group-aware |
| HTML | Heading/DOM + semantic |
| TXT | Recursive / semantic |
| Scanned PDF | Layout-aware OCR + hierarchical |
| Screenshot | Vision extraction + semantic |

Do not force one universal chunking algorithm onto every document type.

---

# 18. Bedrock Knowledge Bases Chunking

Amazon Bedrock Knowledge Bases provides several chunking strategies depending on the Knowledge Base/data-source configuration:

- Default
- Fixed-size
- Hierarchical
- Semantic
- None

For AWS documentation and current API behavior, see:

- https://docs.aws.amazon.com/bedrock/latest/userguide/kb-chunking.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/kb-data-source-customize-ingestion.html

Important: not every Bedrock Knowledge Base configuration exposes every strategy. For example, AWS currently documents semantic chunking limitations for managed Knowledge Bases.

---

# 19. Bedrock Fixed-Size Chunking

Example target:

```text
500 tokens
20% overlap
```

Configuration:

```json
{
  "chunkingConfiguration": {
    "chunkingStrategy": "FIXED_SIZE",
    "fixedSizeChunkingConfiguration": {
      "maxTokens": 500,
      "overlapPercentage": 20
    }
  }
}
```

Python / boto3:

```python
import boto3

client = boto3.client("bedrock-agent")

response = client.create_data_source(
    knowledgeBaseId="KB_ID",

    name="documents",

    dataSourceConfiguration={
        "type": "S3",
        "s3Configuration": {
            "bucketArn": "arn:aws:s3:::my-rag-bucket",
            "inclusionPrefixes": ["documents/"]
        }
    },

    vectorIngestionConfiguration={
        "chunkingConfiguration": {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 500,
                "overlapPercentage": 20
            }
        }
    }
)
```

---

# 20. Bedrock Hierarchical Chunking

For long structured documents, hierarchical chunking is a strong option.

Example:

```text
Parent = 1500 tokens
Child  = 400 tokens
Overlap = 50 tokens
```

Python / boto3:

```python
import boto3

client = boto3.client("bedrock-agent")

vector_ingestion_configuration = {
    "chunkingConfiguration": {
        "chunkingStrategy": "HIERARCHICAL",
        "hierarchicalChunkingConfiguration": {
            "levelConfigurations": [
                {
                    "maxTokens": 1500
                },
                {
                    "maxTokens": 400
                }
            ],
            "overlapTokens": 50
        }
    }
}
```

Full example:

```python
response = client.create_data_source(
    knowledgeBaseId="KB_ID",

    name="enterprise-documents",

    dataSourceConfiguration={
        "type": "S3",
        "s3Configuration": {
            "bucketArn": "arn:aws:s3:::my-rag-bucket",
            "inclusionPrefixes": [
                "documents/"
            ]
        }
    },

    vectorIngestionConfiguration={
        "chunkingConfiguration": {
            "chunkingStrategy": "HIERARCHICAL",

            "hierarchicalChunkingConfiguration": {
                "levelConfigurations": [
                    {
                        "maxTokens": 1500
                    },
                    {
                        "maxTokens": 400
                    }
                ],
                "overlapTokens": 50
            }
        }
    }
)
```

---

# 21. Bedrock Semantic Chunking

Where supported, semantic chunking can be configured conceptually as:

```json
{
  "chunkingConfiguration": {
    "chunkingStrategy": "SEMANTIC",
    "semanticChunkingConfiguration": {
      "maxTokens": 500,
      "bufferSize": 1,
      "breakpointPercentileThreshold": 95
    }
  }
}
```

Semantic chunking attempts to find boundaries based on semantic differences between sentences rather than simply cutting at a fixed token count.

---

# 22. Custom Chunking with Bedrock Knowledge Bases

A major limitation of generic token chunkers is that they don't inherently understand:

```text
PPTX:
one slide = one logical boundary

XLSX:
one table = one logical boundary

PDF:
heading + paragraph + table = one logical unit

Diagram:
image + caption + surrounding explanation = one logical unit
```

For these cases, use a custom transformation Lambda where appropriate.

Architecture:

```text
S3
 │
 ▼
Bedrock Knowledge Base
 │
 ▼
Parser
 │
 ▼
Custom Transformation Lambda
 │
 ├── identify tables
 ├── identify headings
 ├── preserve slide boundaries
 ├── preserve diagram relationships
 ├── create parent/child metadata
 └── generate custom chunks
 │
 ▼
Bedrock embedding
 │
 ▼
Vector DB
```

AWS documentation:

https://docs.aws.amazon.com/bedrock/latest/userguide/kb-custom-transformation.html

---

# 23. Example Custom Chunk Representation

A custom transformation can conceptually create chunks like:

```json
{
  "chunk_id": "doc1_page5_table1",
  "content": "Revenue by Region...",
  "metadata": {
    "document_id": "doc1",
    "page": 5,
    "section": "Revenue Analysis",
    "element_type": "table",
    "table_id": "table1"
  }
}
```

For a diagram:

```json
{
  "chunk_id": "doc1_page8_diagram1",
  "content": "Architecture diagram showing User → API Gateway → Auth Service → Database.",
  "metadata": {
    "document_id": "doc1",
    "page": 8,
    "element_type": "diagram",
    "diagram_id": "diagram1"
  }
}
```

For a PowerPoint slide:

```json
{
  "chunk_id": "presentation_slide_12",
  "content": "Revenue increased 20%...",
  "metadata": {
    "document_id": "presentation",
    "slide_number": 12,
    "element_type": "slide",
    "has_chart": true
  }
}
```

---

# 24. Multimodal Bedrock Approach

For tables, charts, diagrams and images, Bedrock provides multimodal processing options.

Broadly:

### Default parser

Useful for primarily text-based content.

### Bedrock Data Automation

Useful for converting multimodal content into structured/searchable representations.

### Foundation model parser

Useful for complex documents and visually rich content such as tables, charts, and diagrams.

AWS documentation:

https://docs.aws.amazon.com/bedrock/latest/userguide/kb-multimodal-create.html

Important distinction:

```text
Text-based RAG

Parser → Text → Chunk → Embed
```

versus:

```text
Native multimodal

Raw image/PDF → Multimodal embedding
```

For native multimodal embeddings, traditional text chunking strategies do not apply in the same way.

AWS documentation:

https://docs.aws.amazon.com/bedrock/latest/userguide/kb-managed-native-multimodal.html

---

# 25. Recommended Architecture for an Enterprise RAG System

For a production system:

```text
                         S3
                          │
                          ▼
                   File Detector
                          │
          ┌───────────────┼────────────────┐
          │               │                │
         PDF           Office            Images
          │           DOCX/PPTX/        Screenshots
          │           XLSX/CSV              │
          ▼               ▼                 ▼
       Parser         Format Parser       Vision/OCR
          │               │                 │
          └───────────────┼─────────────────┘
                          ▼
                 Structure Extraction
                          │
           ┌──────────────┼──────────────┐
           │              │              │
        Sections        Tables        Figures
           │              │              │
           └──────────────┼──────────────┘
                          ▼
                  Structure-aware
                     chunking
                          │
             ┌────────────┴────────────┐
             │                         │
         Parent chunks            Child chunks
             │                         │
             └────────────┬────────────┘
                          ▼
                     Metadata
                          │
                          ▼
                     Embeddings
                          │
                          ▼
                     Pinecone
```

---

# 26. Recommended Metadata Schema

Use consistent metadata across all document types:

```python
metadata = {
    "document_id": document_id,
    "source": source_name,
    "file_type": file_type,

    "page_number": page_number,
    "slide_number": slide_number,
    "sheet_name": sheet_name,

    "section": section_name,

    "element_type": element_type,

    "table_id": table_id,
    "figure_id": figure_id,
    "diagram_id": diagram_id,

    "parent_chunk_id": parent_chunk_id,
    "chunk_index": chunk_index
}
```

Not every field needs to be populated for every document.

For example:

```text
PDF:
page_number = 12

PPTX:
slide_number = 7

XLSX:
sheet_name = Revenue

Table:
table_id = table_12_1

Diagram:
diagram_id = diagram_8_1
```

---

# 27. Recommended Strategy for a Full RAG Project

Do not use one universal chunker.

Use:

```text
PDF
 → layout extraction
 → OCR if scanned
 → section/table/figure preservation
 → hierarchical chunks

DOCX
 → heading/table extraction
 → hierarchical chunks

PPTX
 → slide extraction
 → slide-aware chunks
 → vision for charts/diagrams

XLSX
 → sheet/table extraction
 → row-group chunks
 → optionally SQL retrieval

CSV
 → schema + row-group chunks
 → optionally SQL retrieval

HTML
 → DOM extraction
 → heading-aware semantic chunks

TXT
 → recursive/semantic chunks

Scanned documents
 → OCR + layout reconstruction
 → hierarchical chunks

Screenshots
 → vision/OCR
 → semantic image description
 → metadata + relationships
```

For Bedrock:

```text
Simple corpus
    ↓
FIXED_SIZE / DEFAULT

Long structured documents
    ↓
HIERARCHICAL

Need semantic boundaries
    ↓
SEMANTIC (where supported)

Need completely custom structure
    ↓
CUSTOM TRANSFORMATION LAMBDA

Images/charts/diagrams are central
    ↓
MULTIMODAL / advanced parser
```

---

# 28. Key Interview Takeaways

### 1. Why is OCR needed?

OCR is needed when the source contains image-based text rather than machine-readable text.

It converts:

```text
pixels → text
```

But high-quality document ingestion should ideally preserve:

```text
text + coordinates + layout + relationships
```

### 2. Why not use the same chunking strategy for every document?

Because document structure differs.

```text
PDF    → sections/pages
DOCX   → headings/paragraphs
PPTX   → slides
XLSX   → tables/rows
CSV    → records
HTML   → DOM hierarchy
Image  → visual relationships
```

### 3. How do you preserve tables?

Store:

```text
table ID
headers
rows
page/section
```

and create a retrieval-friendly textual representation.

### 4. How do you preserve diagrams?

Extract:

```text
nodes
relationships
labels
caption
page/slide
```

Do not rely solely on OCR.

### 5. Why use parent-child chunks?

Because retrieval benefits from small precise chunks while generation often needs larger context.

```text
Small child → precise retrieval
Large parent → context
```

### 6. When should you use custom chunking?

When generic token boundaries don't respect the source structure.

Examples:

- slide boundaries
- tables
- sections
- diagrams
- captions
- figures

### 7. Is RAG always the right approach for Excel/CSV?

No.

For analytical questions, structured querying/SQL may be better:

```text
User question
     ↓
Intent/router
     ├── Knowledge question → RAG
     └── Numerical/data question → SQL
```

---

# 29. Final Mental Model

The best way to think about document ingestion is:

```text
             DOCUMENT INGESTION
                     │
        ┌────────────┴────────────┐
        │                         │
    Understand                 Preserve
      content                  structure
        │                         │
        ├── Text                 ├── Page
        ├── Tables               ├── Section
        ├── Charts               ├── Slide
        ├── Images               ├── Table
        └── Diagrams             ├── Figure
                                 └── Relationships
                     │
                     ▼
              Structure-aware
                  chunks
                     │
                     ▼
                Metadata
                     │
                     ▼
                Embeddings
                     │
                     ▼
                Retrieval
                     │
                     ▼
             Grounded generation
```

The core production principle is:

> **Chunking is not merely a tokenization problem. It is an information-structure problem.**

A good RAG ingestion system preserves enough of the original document's semantic and visual structure that retrieval can find the relevant information **without losing the relationships that gave that information its meaning**.

---

## Useful AWS References

- Bedrock Knowledge Base chunking:
  https://docs.aws.amazon.com/bedrock/latest/userguide/kb-chunking.html

- Customize ingestion/chunking:
  https://docs.aws.amazon.com/bedrock/latest/userguide/kb-data-source-customize-ingestion.html

- Custom transformation Lambda:
  https://docs.aws.amazon.com/bedrock/latest/userguide/kb-custom-transformation.html

- Multimodal Knowledge Bases:
  https://docs.aws.amazon.com/bedrock/latest/userguide/kb-multimodal-create.html

- Native multimodal embeddings:
  https://docs.aws.amazon.com/bedrock/latest/userguide/kb-managed-native-multimodal.html
