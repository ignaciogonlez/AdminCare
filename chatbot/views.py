import os, pickle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Variables globales para recursos
_chatbot_model = None
_chunks = None
_emb_chunks = None

def _load_resources():
    global _chatbot_model, _chunks, _emb_chunks
    if _chatbot_model is None:
        # 1) Cargar embeddings serializados
        embeddings_path = os.path.join(os.path.dirname(__file__),
                                       'embeddings', 'ayudas.pkl')
        with open(embeddings_path, 'rb') as f:
            data = pickle.load(f)
        _chunks, _emb_chunks = data['chunks'], data['emb']

        # 2) Import y carga del modelo
        from sentence_transformers import SentenceTransformer, util
        _chatbot_model = SentenceTransformer('all-MiniLM-L6-v2')
        # Guardamos util también
        _chatbot_model.util = util

class ChatbotAPIView(APIView):
    def post(self, request):
        question = request.data.get('question', '').strip()
        if not question:
            return Response({'answer': '❗ Por favor, escribe una pregunta.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Asegurarnos de que el modelo y embeddings están cargados
        _load_resources()

        # Embed pregunta
        emb_q = _chatbot_model.encode(question, convert_to_tensor=True)
        # Calcular similitud
        sims = _chatbot_model.util.cos_sim(emb_q, _emb_chunks)[0]
        best_idx = int(sims.argmax().item())
        score = float(sims[best_idx].item())

        # Guard rails
        if score < 0.5:
            sugerencia = _chunks[best_idx][:60] + '…'
            return Response({'answer': f"🤖 No estoy seguro. ¿Quizás querías preguntar sobre: «{sugerencia}»?"})

        return Response({'answer': _chunks[best_idx]})
