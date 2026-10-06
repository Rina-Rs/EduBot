import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from openai import OpenAI, RateLimitError, APIError

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
Tu es EduBot, un assistant pédagogique intelligent.

Ton rôle est d'aider les étudiants et enseignants à comprendre
des notions scolaires et informatiques.

Règles :
- Réponds en français par défaut.
- Explique simplement et clairement.
- Utilise des exemples lorsque cela aide.
- Ne prétends pas connaître une information si tu n'es pas sûr.
- Pour les problèmes scolaires, explique le raisonnement étape par étape.
- Pour le code, donne du code propre et explique brièvement son fonctionnement.
- Reste concentré sur la question de l'utilisateur.
"""


MAX_MESSAGE_LENGTH = 4000
MAX_HISTORY_MESSAGES = 12
MAX_HISTORY_ITEM_LENGTH = 4000


@require_POST
def chat(request):
    try:
        data = json.loads(request.body)

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "error": "Le JSON envoyé est invalide."
            },
            status=400,
        )

    message = data.get("message", "")
    history = data.get("history", [])

    # Vérification du message
    if not isinstance(message, str):
        return JsonResponse(
            {
                "error": "Le message doit être une chaîne de caractères."
            },
            status=400,
        )

    message = message.strip()

    if not message:
        return JsonResponse(
            {
                "error": "Le message est vide."
            },
            status=400,
        )

    if len(message) > MAX_MESSAGE_LENGTH:
        return JsonResponse(
            {
                "error": (
                    f"Le message est trop long. "
                    f"Maximum : {MAX_MESSAGE_LENGTH} caractères."
                )
            },
            status=400,
        )

    # Vérification de l'historique
    if not isinstance(history, list):
        history = []

    cleaned_history = []

    for item in history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if role not in {"user", "assistant"}:
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()

        if not content:
            continue

        content = content[:MAX_HISTORY_ITEM_LENGTH]

        cleaned_history.append(
            {
                "role": role,
                "content": content,
            }
        )

    # Vérification de la clé OpenRouter
    if not settings.OPENROUTER_API_KEY:
        return JsonResponse(
            {
                "error": (
                    "La clé OPENROUTER_API_KEY n'est pas configurée "
                    "dans le fichier .env."
                )
            },
            status=500,
        )

    try:
        # OpenRouter est compatible avec le SDK OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "http://127.0.0.1:8000",
                "X-OpenRouter-Title": "EduBot",
            },
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        messages.extend(cleaned_history)

        messages.append(
            {
                "role": "user",
                "content": message,
            }
        )

        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL,
            messages=messages,
        )

        reply = response.choices[0].message.content

        if not reply:
            return JsonResponse(
                {
                    "error": "L'IA n'a retourné aucune réponse."
                },
                status=502,
            )

        return JsonResponse(
            {
                "reply": reply.strip(),
            }
        )

    except RateLimitError:
        logger.exception(
            "Limite OpenRouter atteinte."
        )

        return JsonResponse(
            {
                "error": (
                    "La limite gratuite d'OpenRouter a été atteinte. "
                    "Réessaie plus tard."
                )
            },
            status=429,
        )

    except APIError:
        logger.exception(
            "Erreur API OpenRouter."
        )

        return JsonResponse(
            {
                "error": (
                    "Le service IA a rencontré un problème."
                )
            },
            status=502,
        )

    except Exception:
        logger.exception(
            "Erreur lors de l'appel à OpenRouter."
        )

        return JsonResponse(
            {
                "error": (
                    "Impossible de contacter le service IA "
                    "pour le moment."
                )
            },
            status=502,
        )


def home(request):
    return render(
        request,
        "chatbot/index.html"
    )