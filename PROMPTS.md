# AI Assistance Disclosure

This project was primarily designed and implemented by me, applying object-oriented programming
principles learned through my university coursework (abstraction, inheritance, interfaces, and
separation of concerns).

I used **Claude Sonnet 4.5** as an AI assistant in a limited, supportive capacity — mainly for
code scaffolding suggestions, API usage clarification, and validation of design ideas.
All generated snippets were reviewed, modified, and integrated manually.

Below are representative prompt snippets (not full project generation).

---

## Prompt Snippet 1 – High-level design validation

"Review this backend design for a cloud document search service.
The system includes: Google Drive ingestion, text extraction per file type,
Elasticsearch indexing, and a FastAPI search endpoint.
Suggest improvements while keeping it modular and OOP-compliant."

**Usage:** Design review only  
**Human contribution:** Final architecture, class boundaries, and flow

---

## Prompt Snippet 2 – Google Drive API usage reference

"Show a minimal Python example for authenticating with the Google Drive API
using OAuth and listing files from a folder."

**Usage:** API reference  
**Human contribution:** Error handling, folder filtering, incremental sync logic

---

## Prompt Snippet 3 – Elasticsearch indexing example

"Provide a Python example for indexing and searching documents using
Elasticsearch 8.x."

**Usage:** Syntax reference  
**Human contribution:** Index schema design, deletion sync, incremental updates

---

## Prompt Snippet 4 – File extraction guidance

"Suggest libraries and approaches for extracting text from
.txt, .csv, .pdf, and .png files in Python."

**Usage:** Library selection  
**Human contribution:** Implementation of extractor classes and factory pattern

---

## Prompt Snippet 5 – FastAPI endpoint structure

"Give a basic FastAPI example for a GET search endpoint
that accepts a query parameter."

**Usage:** Boilerplate reference  
**Human contribution:** Response schema, error handling, integration with indexer

---

## Summary

- AI tool used: **Claude Sonnet 4.5**
- Role of AI: Reference, validation, and snippet-level assistance only
- Core system design, OOP structure, and integration logic were implemented manually
- OOP concepts applied from university coursework:
  - Abstraction via base classes
  - Inheritance for extractors
  - Separation of concerns
  - Modular, testable design