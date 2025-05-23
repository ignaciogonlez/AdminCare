import pickle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sentence_transformers import SentenceTransformer, util

# Cargamos embeddings al inicio
with open('chatbot/embeddings/ayudas.pkl', 'rb') as f:
    data = pickle.load(f)
chunks, emb_chunks = data['chunks'], data['emb']
modelo = SentenceTransformer('all-MiniLM-L6-v2')

class ChatbotAPIView(APIView):
    def post(self, request):
        question = request.data.get('question', '').strip()
        if not question:
            return Response({'answer': '❗ Por favor, escribe una pregunta.'}, status=status.HTTP_400_BAD_REQUEST)

        # Embed de la pregunta
        emb_q = modelo.encode(question, convert_to_tensor=True)
        # Similitudes
        sims = util.cos_sim(emb_q, emb_chunks)[0]
        best_idx = int(sims.argmax().item())
        score = float(sims[best_idx].item())

        # Guard rail: si no supera umbral, fallback
        if score < 0.5:
            sugerencia = chunks[best_idx][:60] + '…'
            return Response({
                'answer': f"🤖 No estoy seguro de haber entendido. ¿Quizás querías preguntar sobre: «{sugerencia}»?"
            })

        return Response({'answer': chunks[best_idx]})
