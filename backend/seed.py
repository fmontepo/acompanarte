"""
seed.py — Reset completo + datos demo para Acompañarte
=======================================================
⚠️  ADVERTENCIA: Este script BORRA TODOS LOS DATOS del sistema
    y los reemplaza con un escenario de demo predefinido.
    Usar SOLO en entornos de desarrollo / demo. NUNCA en producción.

Qué hace:
  1. Trunca TODAS las tablas (CASCADE — respeta FK automáticamente)
  2. Re-crea roles y catálogo de parentescos
  3. Crea 4 usuarios demo (uno por rol)
  4. Crea 3 pacientes, actividades, registros, alertas y recursos

Uso:
    docker compose exec backend python seed.py
    docker compose exec backend python seed.py --confirm   # salta la pregunta
"""

import asyncio
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, __file__.rsplit("/", 1)[0])  # asegura que app/ sea encontrado

from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.familiar import Familiar
from app.models.terapeuta import Terapeuta
from app.models.administrador import Administrador
from app.models.paciente import Paciente
from app.models.parentesco import Parentesco
from app.models.vinculoPaciente import VinculoPaciente
from app.models.actividadFamiliar import ActividadFamiliar
from app.models.registroSeguimiento import RegistroSeguimiento
from app.models.alerta import Alerta
from app.models.ia import SesionIA
from app.models.recursoProfesional import RecursoProfesional

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─────────────────────────────────────────────────────────────────────────────
# Orden de truncado — de más dependiente a menos dependiente.
# Con CASCADE, no es estrictamente necesario, pero es más claro y rápido.
# ─────────────────────────────────────────────────────────────────────────────
TABLAS_TRUNCAR = [
    "auditoria",
    "consentimientos",
    "permisos_seguimiento",
    "registros_seguimiento",
    "progreso_actividad",
    "actividades_familiar",
    "alertas",
    "mensajes_ia",
    "sesiones_ia",
    "recursos_profesionales",
    "miembros_equipo",
    "equipos_terapeuticos",
    "vinculos_paciente",
    "administradores",
    "terapeutas",
    "familiares",
    "usuarios",
    "pacientes",
    "parentescos",
    "roles",
]

# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGO DE ROLES (igual que main.py)
# ─────────────────────────────────────────────────────────────────────────────
ROLES_SEED = [
    {
        "key": "familia",
        "label": "Panel familiar",
        "default_path": "/familiar/dashboard",
        "nav_config": [
            {"section": "Principal", "items": [
                {"id": "dashboard",    "icon": "home",      "label": "Panel de inicio"},
                {"id": "seguimientos", "icon": "clipboard", "label": "Seguimientos"},
                {"id": "actividades",  "icon": "target",    "label": "Actividades"},
            ]},
            {"section": "Herramientas", "items": [
                {"id": "asistente", "icon": "bot",  "label": "Asistente IA"},
                {"id": "alertas",   "icon": "bell", "label": "Alertas", "badge": 0},
            ]},
        ],
    },
    {
        "key": "ter-int",
        "label": "Terapeuta interno",
        "default_path": "/terapeuta/interno/dashboard",
        "nav_config": [
            {"section": "Principal", "items": [
                {"id": "ter-int-dash",        "icon": "home",      "label": "Panel de inicio"},
                {"id": "ter-int-registros",   "icon": "pencil",    "label": "Registros"},
                {"id": "ter-int-actividades", "icon": "clipboard", "label": "Actividades"},
            ]},
            {"section": "Herramientas", "items": [
                {"id": "ter-int-conocimiento", "icon": "book", "label": "Base de conocimiento"},
                {"id": "alertas",              "icon": "bell", "label": "Alertas", "badge": 0},
            ]},
        ],
    },
    {
        "key": "ter-ext",
        "label": "Terapeuta externo",
        "default_path": "/terapeuta/externo/dashboard",
        "nav_config": [
            {"section": "Principal", "items": [
                {"id": "ter-ext-dash",      "icon": "home",   "label": "Panel de inicio"},
                {"id": "ter-ext-registros", "icon": "pencil", "label": "Mis registros"},
            ]},
        ],
    },
    {
        "key": "admin",
        "label": "Administración",
        "default_path": "/admin/dashboard",
        "nav_config": [
            {"section": "Sistema", "items": [
                {"id": "admin-dash",      "icon": "home",      "label": "Panel de inicio"},
                {"id": "admin-usuarios",  "icon": "users",     "label": "Terapeutas"},
                {"id": "admin-auditoria", "icon": "bar-chart", "label": "Auditoría"},
            ]},
        ],
    },
]

PARENTESCOS_SEED = [
    ("MA", "Madre"),
    ("PA", "Padre"),
    ("HI", "Hijo/a"),
    ("CO", "Cónyuge / Pareja"),
    ("AB", "Abuelo/a"),
    ("HE", "Hermano/a"),
    ("TI", "Tío/a"),
    ("NI", "Nieto/a"),
    ("OT", "Otro"),
]

# ─────────────────────────────────────────────────────────────────────────────
# DATOS DEMO
# ─────────────────────────────────────────────────────────────────────────────
USUARIOS_DEMO = [
    {
        "email":    "admin@acompanarte.com",
        "password": "Admin1234",
        "nombre":   "Carlos",
        "apellido": "Administrador",
        "rol_key":  "admin",
        "avatar_initials": "CA",
        "avatar_class":    "av-rd",
        "profile_label":   "Administrador del sistema",
    },
    {
        "email":    "terapeuta@acompanarte.com",
        "password": "Terapeuta1234",
        "nombre":   "Lucía",
        "apellido": "Herrera",
        "rol_key":  "ter-int",
        "avatar_initials": "LH",
        "avatar_class":    "av-pp",
        "profile_label":   "Terapeuta interna · Psicóloga",
    },
    {
        "email":    "externo@acompanarte.com",
        "password": "Externo1234",
        "nombre":   "Martín",
        "apellido": "Ruiz",
        "rol_key":  "ter-ext",
        "avatar_initials": "MR",
        "avatar_class":    "av-tl",
        "profile_label":   "Terapeuta externo · Fonoaudiólogo",
    },
    {
        "email":    "familiar@acompanarte.com",
        "password": "Familiar1234",
        "nombre":   "Ana",
        "apellido": "García",
        "rol_key":  "familia",
        "avatar_initials": "AG",
        "avatar_class":    "av-bu",
        "profile_label":   "Familiar · Madre de Roberto García",
    },
]

PACIENTES_DEMO = [
    {
        "nombre_enc":        "Roberto García",
        "nivel_soporte":     2,
        "observaciones_enc": "TEA Nivel 2. En seguimiento desde 2024. Buena respuesta a rutinas estructuradas.",
    },
    {
        "nombre_enc":        "Carmen Villalba",
        "nivel_soporte":     1,
        "observaciones_enc": "TEA Nivel 1 — Perfil Asperger. Comunicación verbal conservada. Dificultades en flexibilidad cognitiva.",
    },
    {
        "nombre_enc":        "Héctor Rodríguez",
        "nivel_soporte":     3,
        "observaciones_enc": "TEA Nivel 3 con epilepsia asociada. Requiere supervisión constante y entorno muy controlado.",
    },
]

ACTIVIDADES_DEMO = [
    # (paciente_idx, titulo, descripcion, frecuencia)
    (0, "Ejercicio de respiración diafragmática",
     "Practicar 5 ciclos de respiración lenta antes de levantarse. Inhalar 4 seg, retener 2 seg, exhalar 6 seg.",
     "diaria"),
    (0, "Reconocimiento fotográfico familiar",
     "Mostrar álbum de fotos familiares. Pedir que identifique cada persona y cuente un recuerdo asociado.",
     "diaria"),
    (0, "Caminata matutina",
     "Salida de 15-20 minutos antes del desayuno. Mantener ritmo suave. Registrar si hubo irritabilidad al regresar.",
     "diaria"),
    (1, "Terapia de reminiscencia",
     "Usar objetos y fotos del pasado para estimular la memoria autobiográfica. Sesión de 30 min con familiar presente.",
     "semanal"),
    (1, "Lectura guiada en voz alta",
     "Leer en voz alta durante 15 minutos. Pausar cada párrafo para preguntar sobre el contenido leído.",
     "diaria"),
    (2, "Ejercicios de equilibrio y motricidad",
     "Serie de 10 ejercicios de pie: apoyo monopodal, marcha sobre línea, giros lentos. Con supervisión constante.",
     "semanal"),
    (2, "Música y relajación vespertina",
     "Reproducir playlist de música suave entre 17 y 18 hs. Evitar estímulos externos durante ese período.",
     "diaria"),
]

REGISTROS_DEMO = [
    # (paciente_idx, tipo, contenido, días_atras)
    (0, "evolucion",
     "Excelente sesión de estimulación cognitiva. Roberto completó el reconocimiento fotográfico con 9/10 aciertos. Estado de ánimo estable. Se recomienda aumentar gradualmente la dificultad.",
     1),
    (0, "observacion",
     "Caminata matutina completada sin incidentes. Buen ritmo y disposición. La madre refiere que durmió bien la noche anterior, lo que correlaciona positivamente con el comportamiento diurno.",
     3),
    (1, "evolucion",
     "Sesión de terapia de reminiscencia con fotos de la infancia. Carmen recordó nombres y eventos con notable fluidez. Momento de emoción al ver foto del colegio. Sesión muy positiva.",
     2),
    (1, "incidente",
     "Episodio de agitación vespertina de aproximadamente 15 minutos. Se aplicó técnica de redirección con música. Familiar notificada. Se recomienda revisar estímulos en horario 17-18 hs.",
     5),
    (2, "evolucion",
     "Primer circuito de equilibrio completado sin asistencia. Héctor mantuvo apoyo monopodal 8 seg en pie derecho y 6 seg en el izquierdo. Logro muy significativo. Se ajusta plan.",
     4),
    (2, "observacion",
     "Sin novedades destacadas. Rutina cumplida. Buen apetito y descanso nocturno adecuado según la cuidadora. Continuar con el plan actual.",
     7),
    (0, "logro",
     "Roberto completó todas las actividades de la semana por primera vez desde el inicio del tratamiento. Adherencia 100%. Se celebró el logro con actividad de su preferencia.",
     8),
]

RECURSOS_DEMO = [
    {
        "titulo":      "Señales tempranas del Trastorno del Espectro Autista (TEA)",
        "descripcion": "Guía de detección temprana basada en los criterios DSM-5. Señales de alerta por etapa evolutiva, desde los 6 meses hasta los 3 años, y criterios de derivación al especialista.",
        "tipo":        "guia",
        "validado":    True,
        "contenido_texto": """
SEÑALES TEMPRANAS DEL TRASTORNO DEL ESPECTRO AUTISTA (TEA)

Las señales de alerta para TEA pueden observarse desde los primeros meses de vida. La detección temprana es fundamental para iniciar la intervención en los períodos de mayor plasticidad cerebral.

SEÑALES DE ALERTA POR EDAD

A los 6 meses:
- No sonríe ampliamente ni muestra expresiones de alegría.
- No responde a sonidos del entorno.
- Ausencia de balbuceo o contacto visual sostenido.

A los 9-12 meses:
- No señala, muestra ni agita la mano para saludar.
- No responde al ser llamado por su nombre.
- Pérdida de habilidades ya adquiridas (balbuceo, gestos).

A los 16 meses:
- No dice ninguna palabra.
- No usa gestos comunicativos (señalar para pedir, para mostrar).
- Contacto visual escaso o ausente.

A los 24 meses:
- No utiliza frases de dos palabras espontáneas.
- No imita acciones ni juega de forma funcional con objetos.
- Preferencia por actividades solitarias y repetitivas.

SEÑALES DE ALERTA EN CUALQUIER EDAD:
- Regresión en el lenguaje o habilidades sociales ya adquiridas.
- Ausencia de juego simbólico o juego imaginativo.
- Escasa o nula respuesta a la interacción social.
- Movimientos corporales repetitivos (balanceo, aleteo de manos, giro sobre el eje).
- Fijación intensa en partes de objetos (ruedas, brillos).
- Hipersensibilidad o hiposensibilidad sensorial marcada.
- Rituales rígidos y resistencia intensa al cambio de rutinas.
- Dificultad para mantener el juego compartido con pares.

HERRAMIENTAS DE DETECCIÓN RECOMENDADAS:
- M-CHAT-R/F (Modified Checklist for Autism in Toddlers): cuestionario para padres, aplicable entre 16 y 30 meses. Se administra en atención primaria.
- Escala de Observación para el Diagnóstico del Autismo (ADOS-2): herramienta de observación estructurada administrada por profesionales capacitados.
- ADI-R (Autism Diagnostic Interview-Revised): entrevista semiestructurada para padres.

CUÁNDO DERIVAR AL ESPECIALISTA:
Ante la presencia de 3 o más señales de alerta de la lista anterior, o ante cualquier regresión en habilidades ya adquiridas, se debe derivar de forma urgente a un neuropediatra, psicólogo especialista en desarrollo infantil, o equipo interdisciplinario de TEA.

IMPORTANCIA DE LA INTERVENCIÓN TEMPRANA:
La intervención antes de los 3 años aprovecha la mayor plasticidad neuronal. Los programas de intervención temprana basados en evidencia (ABA, ESDM, DIR/Floortime) han demostrado mejorar significativamente el pronóstico en comunicación, cognición y conducta adaptativa.
""",
    },
    {
        "titulo":      "Técnicas de redirección en TEA — Guía clínica",
        "descripcion": "Estrategias basadas en evidencia para manejar episodios de agitación y desorientación. Protocolo paso a paso para el familiar y criterios de escalamiento al equipo terapéutico.",
        "tipo":        "guia",
        "validado":    True,
        "contenido_texto": """
TÉCNICAS DE REDIRECCIÓN EN TEA — GUÍA CLÍNICA

La redirección es una estrategia conductual que consiste en desviar la atención de la persona con TEA de una conducta no deseada hacia una actividad o estímulo más apropiado. Es una herramienta fundamental en el manejo cotidiano.

¿QUÉ ES LA REDIRECCIÓN?
La redirección implica interrumpir suavemente una conducta problemática y guiar a la persona hacia una actividad alternativa que sea funcional, segura y que cumpla una función similar (sensorial, comunicativa o regulatoria).

TIPOS DE REDIRECCIÓN

1. Redirección física:
Consiste en guiar suavemente el cuerpo de la persona hacia otra actividad. Por ejemplo: si está golpeando la mesa repetidamente, se puede tomar su mano con calma y llevarla hacia una pelota antiestrés o superficie apropiada para golpear.

2. Redirección verbal:
Usar instrucciones cortas y claras. Evitar frases largas o negaciones ("no hagas eso"). Preferir instrucciones positivas: "Vení, mirá esto", "¿Podés ayudarme con...?".

3. Redirección con objetos o actividades:
Ofrecer un objeto preferido, un juego o una actividad que cumpla la misma función sensorial. Si la conducta es girar objetos (función vestibular), ofrecer una peonza o trompo.

PROTOCOLO PASO A PASO

Paso 1 — Identificar la función de la conducta:
¿Por qué está ocurriendo? Busca comunicar algo, obtener un objeto, escapar de una situación, o regulación sensorial. La redirección es más efectiva cuando la alternativa cumple la misma función.

Paso 2 — Mantener la calma:
El tono de voz tranquilo y los movimientos lentos reducen la escalada. Evitar elevar la voz o hacer movimientos bruscos.

Paso 3 — Acercarse despacio y avisar:
Antes de tocar al niño/a, avisar verbalmente: "Voy a ayudarte". Respetar el espacio personal.

Paso 4 — Presentar la alternativa de forma concreta:
Ofrecer la alternativa visualmente: mostrar el objeto, señalar la actividad. No alcanza con decirlo verbalmente.

Paso 5 — Reforzar inmediatamente:
Cuando acepta la redirección, reforzar con alabanza específica y afecto: "¡Muy bien! Eso está mucho mejor."

Paso 6 — Ignorar la conducta original (extinción controlada):
Si la conducta no implica riesgo, ignorarla sistemáticamente mientras se refuerza la alternativa.

SEÑALES QUE REQUIEREN ESCALAMIENTO AL EQUIPO:
- La conducta ocurre más de 10 veces por día durante más de una semana.
- Implica riesgo de lesión para el niño/a u otros.
- No responde a ninguna técnica de redirección en 3 semanas.
- Se asocia a cambios en el sueño, alimentación o nivel de actividad general.
""",
    },
    {
        "titulo":      "Comunicación efectiva con el familiar cuidador",
        "descripcion": "Guía para establecer comunicación clara y empática con los familiares, reduciendo la carga emocional y mejorando la adherencia al plan terapéutico.",
        "tipo":        "articulo",
        "validado":    True,
        "contenido_texto": """
COMUNICACIÓN EFECTIVA CON EL FAMILIAR CUIDADOR EN TEA

Los familiares de personas con TEA son los principales agentes de cambio en la intervención. Su bienestar emocional y su comprensión del plan terapéutico impactan directamente en los resultados del tratamiento.

EL ROL DEL FAMILIAR COMO CO-TERAPEUTA
El familiar no es solo un observador: es quien implementa las estrategias las 16–18 horas del día que el niño/a no está en terapia. Esta comprensión debe guiar toda la comunicación clínica: el familiar necesita información práctica, no solo diagnósticos.

PRINCIPIOS DE COMUNICACIÓN CON FAMILIAS TEA

1. Escucha activa antes que información:
Antes de dar recomendaciones, preguntar: "¿Cómo estuvo la semana?", "¿Qué fue lo más difícil?". Las familias necesitan sentirse escuchadas para poder recibir nueva información.

2. Lenguaje concreto y sin jerga técnica:
Evitar términos como "refuerzo diferencial de conductas incompatibles". Decir: "Cuando haga algo que te guste, felicitalo enseguida con un abrazo o diciéndole algo lindo."

3. Validación emocional sistemática:
Reconocer explícitamente el esfuerzo: "Sé que es muy difícil mantener la constancia cuando estás cansado/a." La validación reduce la resistencia y aumenta la adherencia.

4. Una sola prioridad por sesión:
No entregar 5 pautas nuevas en cada encuentro. Priorizar la estrategia más urgente y asegurarse de que el familiar la entendió y puede implementarla.

5. Modelar en lugar de solo explicar:
Mostrar cómo se implementa la estrategia. El aprendizaje observacional es más efectivo que la instrucción verbal.

6. Preguntar si hay dudas de forma abierta:
No preguntar "¿Entendiste?" (respuesta automática: sí). Preguntar: "¿Cómo lo harías vos en casa cuando pase esto?"

MANEJO DE SITUACIONES DIFÍCILES

Cuando el familiar no puede seguir las pautas:
Explorar barreras reales: carga laboral, otros hijos, conflicto de pareja, agotamiento. Ajustar las pautas a la realidad de la familia, no al ideal clínico.

Cuando hay negación del diagnóstico:
No confrontar directamente. Trabajar con lo que la familia ya observa: "Veo que te preocupa cuando no te mira. Vamos a trabajar en eso." El diagnóstico se va integrando gradualmente.

Cuando hay conflicto entre padres:
Evitar tomar partido. Buscar el punto común: ambos quieren lo mejor para su hijo/a. Proponer que asistan juntos a las reuniones de orientación familiar.

SEÑALES DE AGOTAMIENTO DEL CUIDADOR (burnout):
- Llora frecuentemente en las consultas.
- Refiere que "ya no puede más" o "lo hago solo/a".
- Abandono del cuidado personal (no duerme, no come, no sale).
- Irritabilidad o desinterés marcados durante la entrevista.

Ante estas señales, derivar a apoyo psicológico individual para el familiar. El bienestar del cuidador es condición para el bienestar del niño/a.
""",
    },
    {
        "titulo":      "Ejercicios cognitivos adaptados por nivel TEA",
        "descripcion": "Banco de actividades cognitivas clasificadas por nivel de soporte (1, 2, 3), con instrucciones para que el familiar las implemente en casa.",
        "tipo":        "guia",
        "validado":    True,
        "contenido_texto": """
EJERCICIOS COGNITIVOS ADAPTADOS POR NIVEL TEA

Las actividades cognitivas deben adaptarse al nivel de soporte de cada persona. El DSM-5 define tres niveles: Nivel 1 (requiere apoyo), Nivel 2 (requiere apoyo sustancial) y Nivel 3 (requiere apoyo muy sustancial).

PRINCIPIOS GENERALES DE ADAPTACIÓN

- Instrucciones breves: máximo 3–4 palabras para nivel 3; frases simples para nivel 2; instrucciones completas para nivel 1.
- Apoyo visual siempre: pictogramas, fotografías, objetos concretos.
- Tiempo extra: dar al menos el doble del tiempo que le daríamos a un niño neurotípico.
- Errores controlados: diseñar actividades donde el error sea mínimo para preservar la motivación.
- Refuerzo inmediato: reforzar dentro de los primeros 3 segundos de completar la tarea.

ACTIVIDADES PARA NIVEL 3 (apoyo muy sustancial)

Clasificación de objetos concretos:
Material: objetos cotidianos de 2 categorías (frutas/autos, ropa/comida).
Procedimiento: presentar 4 objetos, mostrar la categoría de forma visual, guiar físicamente la primera clasificación. Objetivo: clasificar correctamente 3 de 4 sin guía física.

Secuencias de 2 pasos:
Material: fotos de 2 acciones de la rutina (lavarse las manos: abrir canilla → jabón → agua → secar).
Procedimiento: mostrar las 2 fotos en orden, ejecutar junto al niño/a. Objetivo: ejecutar la secuencia de 2 pasos con apoyo verbal solamente.

ACTIVIDADES PARA NIVEL 2 (apoyo sustancial)

Secuencias de 3–4 pasos con pictogramas:
Armar la secuencia de una actividad cotidiana (preparar la mochila, poner la mesa) usando 3–4 pictogramas. El familiar muestra la secuencia y el niño/a la reproduce.

Emparejamiento de emociones:
Material: tarjetas con expresiones faciales (alegre, triste, enojado, asustado).
Procedimiento: mostrar una emoción en foto y pedirle que busque la igual. Luego conectar con situaciones: "¿Cuándo te sentís así vos?"

Memoria secuencial (2–3 ítems):
Mostrar 3 objetos, cubrirlos, pedir que recuerde cuáles eran. Aumentar gradualmente la cantidad.

ACTIVIDADES PARA NIVEL 1 (apoyo)

Juegos de categorías semánticas:
Nombrar 5 elementos de una categoría (animales, frutas, medios de transporte) en 30 segundos. Variar las categorías para generalización.

Resolución de problemas cotidianos:
Presentar un problema con imágenes ("Se cayó el vaso de agua, ¿qué hacés?"). Discutir soluciones posibles y consecuencias de cada una.

Lectura comprensiva con preguntas inferenciales:
Leer un texto breve y hacer preguntas de comprensión: literales primero, luego inferenciales ("¿Por qué crees que se puso triste?").

Planificación de actividades:
Pedirle que organice los pasos para realizar una actividad que le guste (preparar una merienda, armar un juego). Trabajar flexibilidad si el orden cambia.

SEÑALES DE QUE LA ACTIVIDAD ES DEMASIADO DIFÍCIL:
- Evita iniciarla o la abandona en menos de 2 minutos.
- Errores en más del 50% de los intentos.
- Aparecen conductas de agitación o autoestimulación aumentada.
- Llanto o negativa activa.

Ante estas señales, bajar un nivel o simplificar la tarea, no insistir.
""",
    },
    {
        "titulo":      "Intervención familiar en crisis de conducta",
        "descripcion": "Protocolo de acción inmediata ante episodios disruptivos. Define roles del familiar, estrategias de contención y criterios de consulta urgente.",
        "tipo":        "protocolo",
        "validado":    True,
        "contenido_texto": """
INTERVENCIÓN FAMILIAR EN CRISIS DE CONDUCTA TEA

Una crisis de conducta en TEA es un episodio de comportamiento intenso que excede las estrategias habituales de manejo. Puede manifestarse como llanto intenso, gritos, agresión hacia otros o hacia sí mismo, destrucción de objetos o huida.

FASES DE UNA CRISIS Y CÓMO ACTUAR EN CADA UNA

FASE 1 — Señales tempranas (agitación)
La persona muestra signos de sobrecarga antes de que la crisis escale: aumento de autoestimulaciones, búsqueda de ciertos objetos, cambios en el tono de voz, rechazo al contacto físico.

Qué hacer:
- Reducir estímulos del entorno (bajar volumen, apagar luces brillantes, alejar personas).
- Ofrecer el "kit de regulación": objeto de apego, auriculares, espacio tranquilo.
- Hablar poco y despacio: "Estoy acá. Estoy tranquilo/a."
- NO intentar razonar ni dar explicaciones largas.

FASE 2 — Crisis activa (escalada)
El comportamiento ya escaló. Puede haber gritos, tirar objetos, golpear.

Qué hacer:
- Garantizar la seguridad física: alejar objetos peligrosos, no inmovilizar salvo riesgo inminente de lesión grave.
- Mantener presencia tranquila sin confrontar.
- No dar instrucciones ni hacer preguntas.
- No aplicar consecuencias ni intentar enseñar en este momento.
- Si hay otros niños presentes, pedirle a otro adulto que los retire del espacio.

Qué NO hacer:
- No gritar ni responder con agresividad.
- No castigar ni amenazar durante la crisis.
- No forzar el contacto físico si la persona lo rechaza.
- No intentar calmar con lógica: "Ya sé que estás enojado, pero si te calmás..."

FASE 3 — Desescalada
La persona empieza a calmarse. Puede aparecer llanto más suave, búsqueda de contacto, agotamiento.

Qué hacer:
- Ofrecer presencia sin demandas: estar cerca sin hablar ni pedir nada.
- Si acepta el contacto, ofrecer abrazo o mano.
- Cuando esté claramente calmada, validar: "Estuvo difícil. Ya pasó."
- Esperar al menos 20–30 minutos antes de retomar actividades.

FASE 4 — Recuperación y registro
Una vez pasada la crisis, registrar: duración, desencadenante aparente, qué estrategias funcionaron, intensidad (1–5).

CRITERIOS DE CONSULTA URGENTE AL EQUIPO:
- Autolesiones que dejan marcas visibles (mordeduras, golpes en la cabeza).
- La crisis dura más de 45 minutos sin desescalada.
- Frecuencia mayor a 3 crisis en una semana.
- Aparición nueva de conductas de crisis en alguien que habitualmente no las tenía.
- El familiar siente que no puede manejar la situación de forma segura.

DESPUÉS DE UNA CRISIS SEVERA:
El familiar también necesita contención. Es normal sentir culpa, impotencia o agotamiento intenso. Comunicarlo al equipo terapéutico en la próxima sesión.
""",
    },
    {
        "titulo":      "Evaluación de bienestar — Escala CMAI adaptada para TEA",
        "descripcion": "Protocolo de uso de la escala de agitación de Cohen-Mansfield adaptada para TEA. Interpretación de resultados y umbrales de alerta para derivación.",
        "tipo":        "protocolo",
        "validado":    True,
        "contenido_texto": """
EVALUACIÓN DE BIENESTAR — ESCALA CMAI ADAPTADA PARA TEA

La escala CMAI (Cohen-Mansfield Agitation Inventory) fue diseñada para evaluar conductas de agitación. Esta versión adaptada para TEA en niños y adolescentes evalúa indicadores de bienestar y malestar observable.

OBJETIVO DE LA ESCALA
Proporcionar una medida sistemática y observable del bienestar de la persona con TEA, con el fin de monitorear cambios a lo largo del tiempo y detectar situaciones que requieran ajuste en el plan de intervención.

DOMINIOS EVALUADOS

Dominio 1 — Conductas de agitación física:
- Balanceo o movimientos repetitivos de intensidad inusual.
- Golpeteo de objetos o superficies.
- Deambulación o movimiento constante sin propósito aparente.
- Rascado, pellizcos o conductas autoestimulatorias físicas.
Escala: 1 (nunca) a 5 (varias veces al día).

Dominio 2 — Conductas de agitación verbal:
- Gritos o vocalizaciones repetitivas de alta intensidad.
- Repetición de frases fuera de contexto (ecolalia de malestar).
- Rechazo verbal ante actividades que habitualmente acepta.
Escala: 1 (nunca) a 5 (varias veces al día).

Dominio 3 — Conductas de agresividad:
- Agresión hacia otros (golpes, mordidas, pellizcos a terceros).
- Autoagresión (golpearse la cabeza, morderse las manos).
- Destrucción de objetos.
Escala: 1 (nunca) a 5 (varias veces al día).

Dominio 4 — Indicadores de bienestar positivo:
- Inicia interacción espontánea con adultos o pares.
- Participa en actividades de su interés con expresión positiva.
- Acepta cambios de rutina con adaptación en menos de 5 minutos.
- Muestra afecto espontáneo.
Escala: 1 (nunca) a 5 (siempre).

INTERPRETACIÓN DE RESULTADOS

Puntaje dominios 1–3 (agitación y agresividad):
- 3–6 puntos: Nivel bajo. Situación estable.
- 7–10 puntos: Nivel moderado. Revisar desencadenantes recientes y ajustar estrategias.
- 11–15 puntos: Nivel alto. Derivación urgente al equipo terapéutico.

Puntaje dominio 4 (bienestar positivo):
- 16–20 puntos: Bienestar alto.
- 10–15 puntos: Bienestar moderado. Explorar factores que lo reducen.
- Menos de 10 puntos: Bienestar bajo. Revisión del plan terapéutico.

FRECUENCIA DE APLICACIÓN RECOMENDADA:
- Routine semanal por parte del familiar.
- En momentos de cambio significativo (inicio de ciclo escolar, cambio de terapeuta, mudanza, enfermedad).
- Ante cualquier cambio conductual llamativo.

NOTAS PARA EL FAMILIAR:
Completar la escala basándose en las últimas 72 horas. Si algún comportamiento no ocurrió en ese período, marcar 1. No hay respuestas correctas o incorrectas: se busca precisión observacional.
""",
    },
    {
        "titulo":      "Plan de cuidados individualizado — Plantilla editable",
        "descripcion": "Plantilla estructurada para armar el plan de cuidados con objetivos SMART, actividades, frecuencia y métricas de seguimiento.",
        "tipo":        "pdf",
        "validado":    False,
        "contenido_texto": None,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _hace(dias: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=dias)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
async def seed(confirmar: bool = False):

    # ── Confirmación de seguridad ─────────────────────────────────────────
    if not confirmar:
        print("⚠️  ADVERTENCIA: Este script borrará TODOS los datos del sistema.")
        print("   Esta acción no se puede deshacer.\n")
        respuesta = input("   ¿Continuar? Escribí 'si' para confirmar: ").strip().lower()
        if respuesta != "si":
            print("\n   Operación cancelada.")
            return

    print("\n🗑️  Truncando todas las tablas…")

    # ── 1. Crear tablas si no existen ────────────────────────────────────
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── 2. Truncar todo con CASCADE ───────────────────────────────────────
    async with engine.begin() as conn:
        tablas = ", ".join(TABLAS_TRUNCAR)
        await conn.execute(text(f"TRUNCATE TABLE {tablas} RESTART IDENTITY CASCADE"))
    print("   ✓ Todas las tablas vaciadas\n")

    async with AsyncSessionLocal() as db:

        # ── 3. Roles ──────────────────────────────────────────────────────
        print("🔧 Creando roles del sistema…")
        roles_map: dict[str, Rol] = {}
        for r in ROLES_SEED:
            rol = Rol(
                key=r["key"],
                label=r["label"],
                default_path=r["default_path"],
                nav_config=r["nav_config"],
            )
            db.add(rol)
            await db.flush()
            roles_map[r["key"]] = rol
            print(f"   ✓ {r['key']}")
        await db.commit()

        # ── 4. Parentescos ─────────────────────────────────────────────────
        print("\n🔧 Creando catálogo de parentescos…")
        for id_p, nombre in PARENTESCOS_SEED:
            db.add(Parentesco(id_parentesco=id_p, nombre=nombre))
        await db.commit()
        print(f"   ✓ {len(PARENTESCOS_SEED)} parentescos")

        # ── 5. Usuarios demo ───────────────────────────────────────────────
        print("\n👤 Creando usuarios demo…")
        usuarios_map: dict[str, Usuario] = {}

        for u_data in USUARIOS_DEMO:
            # Refrescar el rol desde la sesión actual
            res = await db.execute(select(Rol).where(Rol.key == u_data["rol_key"]))
            rol = res.scalar_one()

            usuario = Usuario(
                email=u_data["email"],
                password_hash=_pwd.hash(u_data["password"]),
                nombre=u_data["nombre"],
                apellido=u_data["apellido"],
                rol_id=rol.id,
                avatar_initials=u_data["avatar_initials"],
                avatar_class=u_data["avatar_class"],
                profile_label=u_data["profile_label"],
                activo=True,
                email_verificado=True,
            )
            db.add(usuario)
            await db.flush()
            usuarios_map[u_data["rol_key"]] = usuario
            print(f"   ✓ [{u_data['rol_key']:8}]  {u_data['email']}  /  {u_data['password']}")
        await db.commit()

        for u in usuarios_map.values():
            await db.refresh(u)

        # ── 6. Perfiles de rol ─────────────────────────────────────────────
        print("\n🔧 Creando perfiles de rol…")

        # Administrador
        db.add(Administrador(
            usuario_id=usuarios_map["admin"].id,
            nivel_acceso=3,
            activo=True,
        ))

        # Terapeuta interno
        ter_int = Terapeuta(
            usuario_id=usuarios_map["ter-int"].id,
            matricula="MP-12345",
            profesion="Psicóloga",
            especialidad="TEA / Neurodesarrollo",
            institucion="Acompañarte",
            tipo_acceso="institucional",
            validado=True,
            institucional=True,
            activo=True,
        )
        db.add(ter_int)

        # Terapeuta externo
        ter_ext = Terapeuta(
            usuario_id=usuarios_map["ter-ext"].id,
            matricula="MF-98765",
            profesion="Fonoaudiólogo",
            especialidad="Comunicación aumentativa",
            institucion="Consulta independiente",
            tipo_acceso="independiente",
            validado=True,
            institucional=False,
            activo=True,
        )
        db.add(ter_ext)

        # Familiar
        familiar = Familiar(
            usuario_id=usuarios_map["familia"].id,
            contacto_emergencia=True,
            consentimiento_otorgado=True,
            consentimiento_en=_hace(30),
            consentimiento_version="1.0",
        )
        db.add(familiar)

        await db.flush()
        await db.commit()
        await db.refresh(ter_int)
        await db.refresh(ter_ext)
        await db.refresh(familiar)
        print("   ✓ Administrador, 2 terapeutas, 1 familiar")

        # ── 7. Pacientes ───────────────────────────────────────────────────
        print("\n🏥 Creando pacientes…")
        pacientes: list[Paciente] = []
        for p_data in PACIENTES_DEMO:
            p = Paciente(
                nombre_enc=p_data["nombre_enc"],
                nivel_soporte=p_data["nivel_soporte"],
                observaciones_enc=p_data["observaciones_enc"],
                activo=True,
            )
            db.add(p)
            pacientes.append(p)

        await db.flush()
        await db.commit()
        for p in pacientes:
            await db.refresh(p)
            print(f"   ✓ {p.nombre_enc}  (nivel {p.nivel_soporte})")

        # ── 8. Vínculo familiar → paciente principal ───────────────────────
        print("\n🔗 Vinculando familiar con paciente…")
        db.add(VinculoPaciente(
            familiar_id=familiar.id,
            paciente_id=pacientes[0].id,
            id_parentesco="MA",
            es_tutor_legal=True,
            autorizado_medico=True,
            activo=True,
        ))
        await db.commit()
        print(f"   ✓ {usuarios_map['familia'].nombre} {usuarios_map['familia'].apellido} → {pacientes[0].nombre_enc}")

        # ── 9. Actividades terapéuticas ────────────────────────────────────
        print("\n📋 Creando actividades terapéuticas…")
        for pac_idx, titulo, descripcion, frecuencia in ACTIVIDADES_DEMO:
            db.add(ActividadFamiliar(
                terapeuta_id=ter_int.id,
                paciente_id=pacientes[pac_idx].id,
                titulo=titulo,
                descripcion=descripcion,
                frecuencia=frecuencia,
                activa=True,
            ))
        await db.commit()
        print(f"   ✓ {len(ACTIVIDADES_DEMO)} actividades creadas")

        # ── 10. Registros de seguimiento ───────────────────────────────────
        print("\n📝 Creando registros de seguimiento…")
        for pac_idx, tipo, contenido, dias_atras in REGISTROS_DEMO:
            db.add(RegistroSeguimiento(
                paciente_id=pacientes[pac_idx].id,
                autor_id=usuarios_map["ter-int"].id,
                contenido_enc=contenido,
                tipo=tipo,
                visibilidad="equipo",
                fecha_registro=date.today() - timedelta(days=dias_atras),
                version=1,
            ))
        await db.commit()
        print(f"   ✓ {len(REGISTROS_DEMO)} registros creados")

        # ── 11. Sesiones IA + Alertas ──────────────────────────────────────
        print("\n🔔 Creando sesiones IA y alertas…")

        sesion_ref = SesionIA(
            familiar_id=familiar.id,
            paciente_id=pacientes[0].id,
            estado="cerrada",
            contexto_anonimo={"nivel_soporte": 2, "contexto": "seguimiento rutina"},
        )
        sesion_alerta = SesionIA(
            familiar_id=familiar.id,
            paciente_id=pacientes[0].id,
            estado="escalada",
            contexto_anonimo={"nivel_soporte": 2, "contexto": "episodio agitación"},
        )
        sesion_consent = SesionIA(
            familiar_id=familiar.id,
            paciente_id=pacientes[2].id,
            estado="cerrada",
            contexto_anonimo={"nivel_soporte": 3, "contexto": "control consentimiento"},
        )
        db.add_all([sesion_ref, sesion_alerta, sesion_consent])
        await db.flush()

        alertas = [
            Alerta(
                sesion_id=sesion_ref.id,
                tipo="riesgo",
                severidad=2,
                descripcion="Carmen no ha completado ninguna actividad en los últimos 3 días. Se recomienda contactar al familiar para evaluar la situación.",
                resuelta=False,
            ),
            Alerta(
                sesion_id=sesion_alerta.id,
                tipo="crisis",
                severidad=3,
                descripcion="El familiar reportó un episodio de agitación vespertina el martes. Duración aprox. 20 minutos. Revisar plan de actividades del horario 17-19 hs.",
                resuelta=False,
            ),
            Alerta(
                sesion_id=sesion_consent.id,
                tipo="escalamiento",
                severidad=1,
                descripcion="El consentimiento de seguimiento de Héctor vence en 5 días. Coordinar renovación con el familiar antes del vencimiento.",
                resuelta=False,
            ),
            Alerta(
                sesion_id=sesion_ref.id,
                tipo="riesgo",
                severidad=1,
                descripcion="Héctor completó el circuito de equilibrio sin asistencia por primera vez. Actualizar plan terapéutico aumentando la dificultad.",
                resuelta=True,
                nota_resolucion="Plan actualizado. Actividad de equilibrio nivel 2 asignada.",
                resuelta_en=_hace(1),
            ),
        ]
        for a in alertas:
            db.add(a)
        await db.commit()
        activas = sum(1 for a in alertas if not a.resuelta)
        print(f"   ✓ {len(alertas)} alertas ({activas} activas, {len(alertas)-activas} resueltas)")

        # ── 12. Recursos profesionales ─────────────────────────────────────
        print("\n📚 Creando base de conocimiento…")
        for r_data in RECURSOS_DEMO:
            db.add(RecursoProfesional(
                subido_por=usuarios_map["ter-int"].id,
                validado_por=usuarios_map["ter-int"].id if r_data["validado"] else None,
                titulo=r_data["titulo"],
                descripcion=r_data["descripcion"],
                tipo=r_data["tipo"],
                contenido_texto=r_data.get("contenido_texto"),
                validado=r_data["validado"],
                activo=True,
                validado_en=_hace(15) if r_data["validado"] else None,
            ))
        await db.commit()
        validados = sum(1 for r in RECURSOS_DEMO if r["validado"])
        print(f"   ✓ {len(RECURSOS_DEMO)} recursos ({validados} validados)")

    # ── Resumen final ─────────────────────────────────────────────────────
    sep = "═" * 58
    print(f"\n{sep}")
    print("  ✅  SEED COMPLETADO — Sistema en estado demo")
    print(sep)
    print()
    print("  CREDENCIALES DE ACCESO")
    print("  " + "─" * 54)
    creds = [
        ("Admin",            "admin@acompanarte.com",      "Admin1234"),
        ("Terapeuta interno", "terapeuta@acompanarte.com", "Terapeuta1234"),
        ("Terapeuta externo", "externo@acompanarte.com",   "Externo1234"),
        ("Familiar",         "familiar@acompanarte.com",   "Familiar1234"),
    ]
    for rol, email, pwd in creds:
        print(f"  {rol:<20}  {email:<32}  {pwd}")
    print("  " + "─" * 54)
    print()
    print("  DATOS CREADOS")
    print(f"  • Pacientes      : {len(PACIENTES_DEMO)}")
    print(f"  • Actividades    : {len(ACTIVIDADES_DEMO)}")
    print(f"  • Registros      : {len(REGISTROS_DEMO)}")
    print(f"  • Alertas        : {len(alertas)} ({activas} activas)")
    print(f"  • Recursos       : {len(RECURSOS_DEMO)} ({validados} validados)")
    print(f"\n{sep}\n")


if __name__ == "__main__":
    auto_confirm = "--confirm" in sys.argv or "-y" in sys.argv
    asyncio.run(seed(confirmar=auto_confirm))
