import streamlit as st
import requests
import json
from datetime import datetime
import time
import speech_recognition as sr
import pyttsx3
import threading
import queue
import io
import base64
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import numpy as np

class IoTChatbotStreamlitVoice:
    def __init__(self):
        # API Configuration
        self.API_KEY = 'sk-53751d5c6f344a5dbc0571de9f51313e'
        self.API_URL = 'https://api.deepseek.com/v1/chat/completions'
        
        # Initialize TTS engine
        if 'tts_engine' not in st.session_state:
            st.session_state.tts_engine = self.init_tts()
        
        # Initialize Speech Recognition
        if 'recognizer' not in st.session_state:
            st.session_state.recognizer = sr.Recognizer()
            st.session_state.microphone = sr.Microphone()
        
        # Initialize session state
        if 'conversacion_actual' not in st.session_state:
            st.session_state.conversacion_actual = []
        if 'proyecto_actual' not in st.session_state:
            st.session_state.proyecto_actual = {}
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'voice_enabled' not in st.session_state:
            st.session_state.voice_enabled = False
        if 'audio_input' not in st.session_state:
            st.session_state.audio_input = ""
        if 'listening' not in st.session_state:
            st.session_state.listening = False

    def init_tts(self):
        """Initialize Text-to-Speech engine"""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            # Try to set Spanish voice
            for voice in voices:
                if 'spanish' in voice.name.lower() or 'es' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.setProperty('rate', 170)
            engine.setProperty('volume', 0.9)
            return engine
        except Exception as e:
            st.error(f"Error inicializando TTS: {e}")
            return None

    def speak_text(self, text):
        """Convert text to speech"""
        if st.session_state.voice_enabled and st.session_state.tts_engine:
            try:
                # Run TTS in a separate thread to avoid blocking
                def tts_thread():
                    st.session_state.tts_engine.say(text)
                    st.session_state.tts_engine.runAndWait()
                
                thread = threading.Thread(target=tts_thread)
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                st.error(f"Error en síntesis de voz: {e}")

    def listen_audio(self, timeout=8):
        """Capture audio from microphone and convert to text"""
        try:
            with st.session_state.microphone as source:
                st.session_state.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = st.session_state.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
            
            text = st.session_state.recognizer.recognize_google(audio, language='es-ES')
            return text.lower()
            
        except sr.WaitTimeoutError:
            return "timeout"
        except sr.UnknownValueError:
            return "no_entendido"
        except sr.RequestError as e:
            st.error(f"Error del servicio de reconocimiento: {e}")
            return "error_servicio"
        except Exception as e:
            st.error(f"Error general en reconocimiento: {e}")
            return "error"

    def consultar_api(self, prompt, temperatura=0.7):
        """Consulta la API de DeepSeek con el prompt generado"""
        headers = {
            'Authorization': f'Bearer {self.API_KEY}',
            'Content-Type': 'application/json'
        }
        
        mensajes = [
            {
                'role': 'system',
                'content': 'Eres un mentor experto en emprendimiento IoT con 15 años de experiencia. Ayudas a emprendedores a desarrollar ideas innovadoras, planes de negocio sólidos y estrategias de crecimiento en el ecosistema Internet of Things. Tus respuestas son prácticas, detalladas y bien estructuradas.'
            }
        ]
        
        mensajes.extend(st.session_state.conversacion_actual[-6:])
        mensajes.append({'role': 'user', 'content': prompt})
        
        data = {
            'model': 'deepseek-chat',
            'temperature': temperatura,
            'messages': mensajes,
            'max_tokens': 1000
        }
        
        try:
            response = requests.post(self.API_URL, headers=headers, json=data)
            response.raise_for_status()
            resultado = response.json()['choices'][0]['message']['content']
            
            # Guardar en historial
            st.session_state.conversacion_actual.append({'role': 'user', 'content': prompt})
            st.session_state.conversacion_actual.append({'role': 'assistant', 'content': resultado})
            
            # Mantener solo las últimas 20 interacciones
            if len(st.session_state.conversacion_actual) > 20:
                st.session_state.conversacion_actual = st.session_state.conversacion_actual[-20:]
            
            return resultado
            
        except requests.exceptions.HTTPError as err:
            return f"❌ Error con la API: {err.response.text}"
        except Exception as e:
            return f"❌ Error técnico: {e}"

    def generar_ideas_iot(self, sector, presupuesto, experiencia, mercado, recursos):
        """Genera ideas de negocio IoT"""
        prompt = f"""Como experto en emprendimiento IoT, genera 3 ideas innovadoras de negocio considerando:

PERFIL DEL EMPRENDEDOR:
- Sector de interés: {sector}
- Presupuesto inicial: {presupuesto}
- Nivel técnico: {experiencia}
- Mercado objetivo: {mercado}
- Recursos disponibles: {recursos}

Para cada idea, incluye:
1. **CONCEPTO**: Descripción clara del producto/servicio IoT
2. **PROBLEMA QUE RESUELVE**: Necesidad específica del mercado
3. **TECNOLOGÍA REQUERIDA**: Sensores, conectividad, plataformas
4. **MODELO DE NEGOCIO**: Cómo generar ingresos
5. **INVERSIÓN ESTIMADA**: Capital inicial necesario
6. **VENTAJA COMPETITIVA**: Qué te diferencia

Enfócate en ideas viables, escalables y con potencial de ROI atractivo."""

        return self.consultar_api(prompt)

    def desarrollar_plan_negocio(self, idea):
        """Desarrolla un plan de negocio completo"""
        prompt = f"""Desarrolla un plan de negocio completo para esta idea IoT:

**IDEA SELECCIONADA**: {idea}

Estructura el plan con:
1. **RESUMEN EJECUTIVO** - Visión, misión y propuesta de valor
2. **ANÁLISIS DE MERCADO** - Tamaño, segmentación y competencia
3. **PRODUCTO/SERVICIO** - Especificaciones y roadmap
4. **ESTRATEGIA DE MARKETING** - Posicionamiento y canales
5. **ANÁLISIS FINANCIERO** - Proyecciones y métricas clave
6. **PLAN DE IMPLEMENTACIÓN** - Hitos y cronograma

Proporciona detalles específicos y accionables para cada sección."""
        
        return self.consultar_api(prompt)

    def generar_proyecciones_financieras(self, precio, usuarios, crecimiento, costos_desarrollo, costos_operacion):
        """Genera proyecciones financieras"""
        prompt = f"""Genera proyecciones financieras detalladas para un negocio IoT con:

**PARÁMETROS**:
- Precio del producto/servicio: {precio}
- Usuarios proyectados año 1: {usuarios}
- Crecimiento anual esperado: {crecimiento}%
- Costos de desarrollo: ${costos_desarrollo:,}
- Costos operacionales mensuales: ${costos_operacion:,}

**INCLUIR**:
1. **Proyección de ingresos** (3 años)
2. **Estructura de costos** principales
3. **Punto de equilibrio** estimado
4. **Métricas clave IoT** (CAC, LTV, MRR)
5. **Recomendaciones de financiación**
6. **Análisis de ROI**

Presenta los números de forma clara y estructurada."""
        
        return self.consultar_api(prompt)

    def analizar_mercado_iot(self):
        """Analiza oportunidades en el mercado IoT"""
        prompt = """Realiza un análisis completo del mercado IoT actual incluyendo:

1. **TENDENCIAS GLOBALES IoT 2024-2025**
2. **OPORTUNIDADES DE NICHO** más prometedoras
3. **FACTORES DE ÉXITO** clave en emprendimientos IoT
4. **ECOSISTEMA DE APOYO** (aceleradoras, fondos, programas)
5. **DESAFÍOS COMUNES** y cómo superarlos
6. **RECOMENDACIONES ESTRATÉGICAS** para nuevos emprendedores

Proporciona datos específicos y insights accionables."""
        
        return self.consultar_api(prompt)

    def consulta_libre(self, pregunta):
        """Permite consultas libres con el mentor IoT"""
        prompt = f"""Como mentor de emprendimiento IoT, responde esta consulta de manera práctica y detallada:

**PREGUNTA**: {pregunta}

Proporciona consejos específicos, ejemplos cuando sea posible, y pasos accionables.
Estructura tu respuesta de forma clara y útil."""
        
        return self.consultar_api(prompt)

    def ver_resumen_proyecto(self):
        """Muestra resumen del proyecto"""
        if not st.session_state.conversacion_actual:
            return "No hay proyecto activo todavía. Te recomiendo generar algunas ideas primero."
        
        prompt = """Basándote en nuestra conversación, crea un resumen ejecutivo del proyecto IoT incluyendo:

1. **Idea principal** desarrollada
2. **Mercado objetivo** identificado  
3. **Propuesta de valor** clave
4. **Próximos pasos** recomendados
5. **Recursos necesarios** prioritarios
6. **Timeline** sugerido

Proporciona un resumen completo y estructurado."""
        
        return self.consultar_api(prompt)

def voice_interface_component():
    """Component for voice interface controls"""
    st.markdown("### 🎤 Control de Voz")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        voice_enabled = st.checkbox("🔊 Activar síntesis de voz", value=st.session_state.get('voice_enabled', False))
        st.session_state.voice_enabled = voice_enabled
    
    with col2:
        if st.button("🎤 Escuchar Micrófono", type="secondary"):
            st.session_state.listening = True
    
    with col3:
        if st.button("🔇 Detener Audio", type="secondary"):
            st.session_state.listening = False
            st.session_state.audio_input = ""
    
    # Audio input handling
    if st.session_state.listening:
        with st.spinner("🎤 Escuchando... Habla ahora"):
            chatbot = IoTChatbotStreamlitVoice()
            audio_text = chatbot.listen_audio()
            
            if audio_text == "timeout":
                st.warning("⏰ Tiempo de espera agotado. Intenta de nuevo.")
            elif audio_text == "no_entendido":
                st.warning("❓ No pude entender el audio. Habla más claro.")
            elif audio_text in ["error_servicio", "error"]:
                st.error("❌ Error en el reconocimiento de voz.")
            else:
                st.success(f"✅ Escuchado: {audio_text}")
                st.session_state.audio_input = audio_text
            
            st.session_state.listening = False
    
    # Display captured audio text
    if st.session_state.audio_input:
        st.info(f"🎤 **Entrada de voz**: {st.session_state.audio_input}")
        return st.session_state.audio_input
    
    return None

def main():
    st.set_page_config(
        page_title="🚀 Chatbot IoT con Voz",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize chatbot
    chatbot = IoTChatbotStreamlitVoice()
    
    # Header
    st.title("🚀 Chatbot de Emprendimiento IoT con Voz")
    st.markdown("### Tu mentor personal con capacidades de voz para desarrollar ideas innovadoras en IoT")
    
    # Voice interface
    voice_interface_component()
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Menú de Opciones")
        st.markdown("---")
        
        # Voice status
        if st.session_state.voice_enabled:
            st.success("🔊 Voz activada")
        else:
            st.info("🔇 Voz desactivada")
        
        st.markdown("---")
        
        # Menu options
        opcion = st.selectbox(
            "Selecciona una opción:",
            [
                "🏠 Inicio",
                "💡 Generar Ideas IoT",
                "📊 Plan de Negocio",
                "💰 Proyecciones Financieras",
                "📈 Análisis de Mercado",
                "🤖 Consulta con Mentor",
                "📋 Resumen del Proyecto",
                "🔄 Limpiar Conversación"
            ]
        )
        
        st.markdown("---")
        st.markdown("""
        **🎤 Controles de Voz:**
        - 🔊 Activa síntesis de voz
        - 🎤 Usa el micrófono
        - Habla claro y espera
        
        **📞 Contacto:**
        - 📧 mentor@iot-startup.com
        - 🌐 www.iot-emprendimiento.com
        """)
        
        # Clear conversation button
        if st.button("🗑️ Limpiar Todo", type="secondary"):
            st.session_state.conversacion_actual = []
            st.session_state.proyecto_actual = {}
            st.session_state.chat_history = []
            st.session_state.audio_input = ""
            st.success("✅ Conversación limpiada")
            st.rerun()
    
    # Main content area
    if opcion == "🏠 Inicio":
        st.markdown("""
        ## 🎯 Bienvenido al Chatbot de Emprendimiento IoT con Voz
        
        Este asistente combina una interfaz visual moderna con capacidades completas de voz para ayudarte a desarrollar tu startup IoT.
        
        ### 🌟 Nuevas Características de Voz:
        
        - **🔊 Síntesis de Voz**: Escucha las respuestas del mentor
        - **🎤 Reconocimiento de Voz**: Habla directamente con el asistente
        - **🗣️ Interfaz Multimodal**: Usa voz, texto o ambos
        - **🎧 Control Total**: Activa/desactiva funciones según necesites
        
        ### 🚀 ¿Qué puedes hacer?
        
        - **💡 Generar Ideas IoT**: Ideas personalizadas con entrada por voz
        - **📊 Desarrollar Plan de Negocio**: Dicta tu idea y obtén un plan completo
        - **💰 Proyecciones Financieras**: Calcula viabilidad con datos hablados
        - **📈 Análisis de Mercado**: Escucha oportunidades actuales en IoT
        - **🤖 Consultas de Voz**: Conversa naturalmente con tu mentor
        - **📋 Seguimiento**: Resúmenes hablados de tu progreso
        
        ### 🎤 Cómo Usar la Voz:
        
        1. **Activa la síntesis de voz** en el panel superior
        2. **Haz clic en "🎤 Escuchar Micrófono"** cuando quieras hablar
        3. **Habla claro y espera** a que el sistema procese
        4. **Combina voz e interfaz** como prefieras
        
        ¡Empecemos tu viaje emprendedor en IoT!
        """)
        
        # Recent activity
        if st.session_state.conversacion_actual:
            st.markdown("### 📈 Actividad Reciente")
            with st.expander("Ver conversación reciente"):
                for mensaje in st.session_state.conversacion_actual[-4:]:
                    if mensaje['role'] == 'user':
                        st.markdown(f"**👤 Tú:** {mensaje['content'][:200]}...")
                    else:
                        st.markdown(f"**🤖 Mentor:** {mensaje['content'][:200]}...")
    
    elif opcion == "💡 Generar Ideas IoT":
        st.header("💡 Generador de Ideas IoT")
        st.markdown("Cuéntame sobre ti para generar ideas personalizadas (usa voz o texto)")
        
        # Check for voice input
        voice_input = voice_interface_component()
        
        col1, col2 = st.columns(2)
        
        with col1:
            sector = st.selectbox(
                "🏭 Sector de interés:",
                ["Salud", "Agricultura", "Hogar inteligente", "Industria 4.0", "Transporte", "Educación", "Retail", "Otro"]
            )
            
            presupuesto = st.selectbox(
                "💵 Presupuesto inicial:",
                ["Bajo (< $10K)", "Medio ($10K - $50K)", "Alto (> $50K)"]
            )
            
            experiencia = st.selectbox(
                "🎓 Nivel técnico:",
                ["Principiante", "Intermedio", "Avanzado"]
            )
        
        with col2:
            mercado = st.selectbox(
                "🌍 Mercado objetivo:",
                ["Local", "Nacional", "Internacional"]
            )
            
            # Use voice input if available, otherwise text area
            recursos_default = voice_input if voice_input else ""
            recursos = st.text_area(
                "🛠️ Recursos disponibles:",
                value=recursos_default,
                placeholder="Ej: Equipo de desarrollo, capital semilla, conexiones industriales... (o usa el micrófono)",
                help="💡 Puedes usar el micrófono para dictar esta información"
            )
        
        if st.button("🚀 Generar Ideas", type="primary"):
            if recursos:
                with st.spinner("🤖 Generando ideas innovadoras..."):
                    ideas = chatbot.generar_ideas_iot(sector, presupuesto, experiencia, mercado, recursos)
                
                st.markdown("### 💡 Ideas Generadas")
                st.markdown(ideas)
                
                # Speak the response if voice is enabled
                if st.session_state.voice_enabled:
                    chatbot.speak_text("He generado ideas personalizadas para tu emprendimiento IoT. Revisa los detalles en pantalla.")
                
                # Save to chat history
                st.session_state.chat_history.append({
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'type': 'Ideas IoT',
                    'content': ideas
                })
            else:
                st.warning("⚠️ Por favor, describe tus recursos disponibles (texto o voz)")
    
    elif opcion == "📊 Plan de Negocio":
        st.header("📊 Desarrollador de Plan de Negocio")
        
        # Voice input component
        voice_input = voice_interface_component()
        
        # Use voice input if available
        idea_default = voice_input if voice_input else ""
        idea = st.text_area(
            "💭 Describe tu idea IoT:",
            value=idea_default,
            placeholder="Ej: Una plataforma IoT para monitorear la calidad del aire... (o usa el micrófono)",
            height=100,
            help="💡 Puedes usar el micrófono para dictar tu idea"
        )
        
        if st.button("📈 Crear Plan de Negocio", type="primary"):
            if idea:
                with st.spinner("📋 Desarrollando tu plan de negocio..."):
                    plan = chatbot.desarrollar_plan_negocio(idea)
                
                st.markdown("### 📊 Plan de Negocio Completo")
                st.markdown(plan)
                
                # Speak the response if voice is enabled
                if st.session_state.voice_enabled:
                    chatbot.speak_text("He creado un plan de negocio completo para tu idea IoT. Revisa todos los detalles en pantalla.")
                
                # Save to chat history
                st.session_state.chat_history.append({
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'type': 'Plan de Negocio',
                    'content': plan
                })
            else:
                st.warning("⚠️ Por favor, describe tu idea IoT")
    
    elif opcion == "💰 Proyecciones Financieras":
        st.header("💰 Calculadora de Proyecciones Financieras")
        
        col1, col2 = st.columns(2)
        
        with col1:
            precio = st.number_input("💵 Precio del producto/servicio ($):", min_value=1, value=100)
            usuarios = st.number_input("👥 Usuarios proyectados año 1:", min_value=1, value=1000)
            crecimiento = st.slider("📈 Crecimiento anual (%):", 0, 200, 30)
        
        with col2:
            costos_desarrollo = st.number_input("🛠️ Costos de desarrollo ($):", min_value=0, value=50000)
            costos_operacion = st.number_input("🔄 Costos operacionales mensuales ($):", min_value=0, value=5000)
        
        if st.button("📊 Generar Proyecciones", type="primary"):
            with st.spinner("📈 Calculando proyecciones financieras..."):
                proyecciones = chatbot.generar_proyecciones_financieras(
                    precio, usuarios, crecimiento, costos_desarrollo, costos_operacion
                )
            
            st.markdown("### 💰 Proyecciones Financieras")
            st.markdown(proyecciones)
            
            # Speak the response if voice is enabled
            if st.session_state.voice_enabled:
                chatbot.speak_text("He calculado las proyecciones financieras de tu negocio IoT. Revisa los números y métricas clave en pantalla.")
            
            # Save to chat history
            st.session_state.chat_history.append({
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'type': 'Proyecciones Financieras',
                'content': proyecciones
            })
    
    elif opcion == "📈 Análisis de Mercado":
        st.header("📈 Análisis del Mercado IoT")
        
        if st.button("🔍 Analizar Mercado IoT", type="primary"):
            with st.spinner("📊 Analizando el mercado IoT actual..."):
                analisis = chatbot.analizar_mercado_iot()
            
            st.markdown("### 📈 Análisis de Mercado IoT")
            st.markdown(analisis)
            
            # Speak the response if voice is enabled
            if st.session_state.voice_enabled:
                chatbot.speak_text("He completado el análisis del mercado IoT actual. Encontrarás tendencias, oportunidades y recomendaciones estratégicas en pantalla.")
            
            # Save to chat history
            st.session_state.chat_history.append({
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'type': 'Análisis de Mercado',
                'content': analisis
            })
    
    elif opcion == "🤖 Consulta con Mentor":
        st.header("🤖 Consulta Libre con tu Mentor IoT")
        st.markdown("Conversa con tu mentor usando voz, texto o ambos")
        
        # Voice interface for chat
        voice_input = voice_interface_component()
        
        # Chat interface
        if "mentor_messages" not in st.session_state:
            st.session_state.mentor_messages = []
        
        # Display chat history
        for message in st.session_state.mentor_messages:
            if message["role"] == "user":
                st.markdown(f"**👤 Tú:** {message['content']}")
            else:
                st.markdown(f"**🤖 Mentor:** {message['content']}")
        
        # Chat input (voice or text)
        pregunta_default = voice_input if voice_input else ""
        pregunta = st.text_area(
            "💬 Hazle una pregunta a tu mentor:",
            value=pregunta_default,
            placeholder="Ej: ¿Cómo puedo validar mi idea IoT? (o usa el micrófono)",
            key="mentor_input",
            help="💡 Puedes usar el micrófono para hacer tu pregunta"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Enviar Pregunta", type="primary"):
                if pregunta:
                    # Add user message
                    st.session_state.mentor_messages.append({"role": "user", "content": pregunta})
                    
                    with st.spinner("🤖 El mentor está pensando..."):
                        respuesta = chatbot.consulta_libre(pregunta)
                    
                    # Add assistant response
                    st.session_state.mentor_messages.append({"role": "assistant", "content": respuesta})
                    
                    # Speak the response if voice is enabled
                    if st.session_state.voice_enabled:
                        chatbot.speak_text(f"Aquí tienes mi respuesta: {respuesta[:200]}...")
                    
                    # Clear the input
                    st.session_state.audio_input = ""
                    st.rerun()
                else:
                    st.warning("⚠️ Por favor, escribe o dicta tu pregunta")
        
        with col2:
            if st.button("🗑️ Limpiar Chat"):
                st.session_state.mentor_messages = []
                st.session_state.audio_input = ""
                st.rerun()
    
    elif opcion == "📋 Resumen del Proyecto":
        st.header("📋 Resumen del Proyecto Actual")
        
        if st.button("📋 Generar Resumen", type="primary"):
            with st.spinner("📝 Generando resumen del proyecto..."):
                resumen = chatbot.ver_resumen_proyecto()
            
            st.markdown("### 📋 Resumen Ejecutivo")
            st.markdown(resumen)
            
            # Speak the response if voice is enabled
            if st.session_state.voice_enabled:
                chatbot.speak_text("He generado un resumen ejecutivo de tu proyecto IoT. Incluye la idea principal, mercado objetivo y próximos pasos recomendados.")
            
            # Save to chat history
            st.session_state.chat_history.append({
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'type': 'Resumen del Proyecto',
                'content': resumen
            })
    
    elif opcion == "🔄 Limpiar Conversación":
        st.header("🔄 Limpiar Conversación")
        
        st.warning("⚠️ Esta acción eliminará todo el historial de conversación y el proyecto actual.")
        
        if st.button("🗑️ Confirmar Limpieza", type="secondary"):
            st.session_state.conversacion_actual = []
            st.session_state.proyecto_actual = {}
            st.session_state.chat_history = []
            st.session_state.audio_input = ""
            if "mentor_messages" in st.session_state:
                st.session_state.mentor_messages = []
            
            if st.session_state.voice_enabled:
                chatbot.speak_text("He limpiado toda la conversación. Ahora puedes empezar un proyecto completamente nuevo.")
            
            st.success("✅ Conversación limpiada exitosamente")
            time.sleep(1)
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        🚀 Chatbot IoT Emprendimiento con Voz | Desarrollado con ❤️ para emprendedores innovadores
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
