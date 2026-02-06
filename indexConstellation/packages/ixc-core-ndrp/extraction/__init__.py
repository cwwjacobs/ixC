"""
Extraction Stage - NDRP Pipeline

The extraction stage is responsible for:
- Loading raw text data from files
- Detecting the mode/type of each entry (instruction, conversation, narrative, etc.)
- Creating preliminary NDRP entries with basic metadata
- Isolating meaningful content from noise

This is the first stage of the three-stage NDRP pipeline:
1. Extraction (this stage) - identify and isolate core meaning
2. Standardization - transform into unified schema
3. Enhancement - improve clarity, density, and coherence
"""
