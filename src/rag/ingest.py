import os
import glob
from pypdf import PdfReader
import pandas as pd
import pickle

DATA_DIR = "data/evidence"
PROCESSED_DIR = "data/processed"

def extract_text_from_pdfs():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    pdf_files = glob.glob(os.path.join(DATA_DIR, "*.pdf"))
    
    if not pdf_files:
        print(f"Warning: No PDF files found in {DATA_DIR}!")
        return []

    chunks = []
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"Processing: {filename}")
        try:
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    # Simple chunking by paragraphs or blocks
                    paragraphs = text.split('\n\n')
                    for p in paragraphs:
                        clean_p = p.strip()
                        if len(clean_p) > 30: # ignore very short lines
                            chunks.append({
                                "source": filename,
                                "page": page_num + 1,
                                "text": clean_p
                            })
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    return chunks

def main():
    print("Starting ingestion pipeline...")
    chunks = extract_text_from_pdfs()
    if chunks:
        df = pd.DataFrame(chunks)
        output_path = os.path.join(PROCESSED_DIR, "evidence_chunks.pkl")
        df.to_pickle(output_path)
        print(f"Successfully ingested {len(df)} chunks into {output_path}")
    else:
        print("No chunks generated.")

if __name__ == "__main__":
    main()