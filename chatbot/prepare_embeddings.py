import os
import pickle
from docx import Document
from sentence_transformers import SentenceTransformer

# Configuración de rutas
dir_base = os.path.dirname(os.path.abspath(__file__))
path_docx = os.path.join(dir_base, 'data', 'ayudas.docx')
path_out_dir = os.path.join(dir_base, 'embeddings')
path_out_file = os.path.join(path_out_dir, 'ayudas.pkl')

# Crear carpeta de salida si no existe
os.makedirs(path_out_dir, exist_ok=True)

# Cargar y procesar el documento Word
print(f"📄 Leyendo documento: {path_docx}")
doc = Document(path_docx)
# Extraer párrafos no vacíos como chunks
chunks = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
print(f"✂️  Número de chunks extraídos: {len(chunks)}")

# Cargar modelo de embeddings
ess_model = SentenceTransformer('all-MiniLM-L6-v2')
print("🤖 Calculando embeddings...")
embeddings = ess_model.encode(chunks, convert_to_tensor=False, show_progress_bar=True)

# Guardar en pickle
with open(path_out_file, 'wb') as f:
    pickle.dump({'chunks': chunks, 'emb': embeddings}, f)
print(f"✅ Guardado embeddings en: {path_out_file}")

# Instrucciones de uso:
# Ejecuta desde la raíz del proyecto:
# python chatbot/prepare_embeddings.py
