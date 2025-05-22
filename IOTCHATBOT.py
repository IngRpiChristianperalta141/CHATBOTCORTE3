import speech_recognition as sr
import pyttsx3
import requests
import json
from datetime import datetime
import threading
import time

class VoiceIoTMenuBot:
    def __init__(self):
        # Inicializar reconocimiento de voz
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Inicializar síntesis de voz
        self.tts_engine = pyttsx3.init()
        self.configurar_voz()
        
        # API Configuration
        self.API_KEY = 'sk-53751d5c6f344a5dbc0571de9f51313e'
        self.API_URL = 'https://api.deepseek.com/v1/chat/completions'
        
        # Estado de conversación
        self.conversacion_actual = []
        self.proyecto_actual = {}
        self.conversacion_activa = True
        self.esperando_entrada = False

    def configurar_voz(self):
        """Configura la voz del sistema TTS"""
        voices = self.tts_engine.getProperty('voices')
        # Buscar voz en español o usar la primera disponible
        for voice in voices:
            if 'spanish' in voice.name.lower() or 'es' in voice.id.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        # Configurar velocidad y volumen
        self.tts_engine.setProperty('rate', 170)  # Velocidad
        self.tts_engine.setProperty('volume', 0.9)  # Volumen

    def hablar(self, texto):
        """Convierte texto a voz"""
        print(f"🤖 Bot: {texto}")
        self.tts_engine.say(texto)
        self.tts_engine.runAndWait()

    def escuchar(self, timeout=8):
        """Captura audio del micrófono y lo convierte a texto"""
        try:
            with self.microphone as source:
                print("🎤 Escuchando... (habla ahora)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
            
            print("🔄 Procesando audio...")
            texto = self.recognizer.recognize_google(audio, language='es-ES')
            print(f"👤 Usuario: {texto}")
            return texto.lower()
            
        except sr.WaitTimeoutError:
            return "timeout"
        except sr.UnknownValueError:
            return "no_entendido"
        except sr.RequestError as e:
            print(f"Error del servicio de reconocimiento: {e}")
            return "error_servicio"

    def detectar_numero_opcion(self, texto):
        """Detecta números de opciones del menú en el texto"""
        # Mapeo de números en texto a dígitos
        numeros_texto = {
            'uno': '1', 'una': '1',
            'dos': '2', 
            'tres': '3',
            'cuatro': '4',
            'cinco': '5',
            'seis': '6',
            'siete': '7',
            'ocho': '8'
        }
        
        # Buscar números directos
        for i in range(1, 9):
            if str(i) in texto:
                return str(i)
        
        # Buscar números en texto
        for palabra, numero in numeros_texto.items():
            if palabra in texto:
                return numero
        
        return None

    def detectar_intencion_menu(self, texto):
        """Detecta intenciones específicas del menú basadas en palabras clave"""
        intenciones = {
            '1': ['idea', 'generar', 'negocio', 'emprender', 'innovar'],
            '2': ['plan', 'negocio', 'business', 'planificar', 'desarrollar'],
            '3': ['financiero', 'dinero', 'proyección', 'ganancia', 'inversión', 'costo'],
            '4': ['mercado', 'competencia', 'análisis', 'oportunidad', 'sector'],
            '5': ['pregunta', 'consulta', 'duda', 'mentor', 'ayuda'],
            '6': ['resumen', 'proyecto', 'actual', 'ver'],
            '7': ['limpiar', 'borrar', 'nuevo', 'reiniciar'],
            '8': ['salir', 'terminar', 'adiós', 'finalizar', 'cerrar']
        }
        
        for opcion, palabras_clave in intenciones.items():
            if any(palabra in texto for palabra in palabras_clave):
                return opcion
        
        return None

    def presentar_menu_voz(self):
        """Presenta el menú principal por voz"""
        menu_texto = """
        Bienvenido al Chatbot de Emprendimiento IoT. 
        Tienes las siguientes opciones:
        
        Opción 1: Generar ideas de negocio IoT
        Opción 2: Desarrollar plan de negocio  
        Opción 3: Crear proyecciones financieras
        Opción 4: Analizar mercado IoT
        Opción 5: Consulta libre con mentor
        Opción 6: Ver resumen del proyecto actual
        Opción 7: Limpiar conversación
        Opción 8: Salir
        
        Puedes decir el número de la opción o describir lo que necesitas.
        """
        self.hablar(menu_texto)

    def obtener_entrada_voz(self, pregunta, timeout=10):
        """Obtiene entrada específica por voz con reintentos"""
        intentos = 0
        max_intentos = 3
        
        while intentos < max_intentos:
            self.hablar(pregunta)
            respuesta = self.escuchar(timeout)
            
            if respuesta == "timeout":
                if intentos < max_intentos - 1:
                    self.hablar("No te escuché. Vamos a intentar de nuevo.")
                intentos += 1
                continue
            elif respuesta == "no_entendido":
                if intentos < max_intentos - 1:
                    self.hablar("No pude entender. Por favor habla más claro.")
                intentos += 1
                continue
            elif respuesta == "error_servicio":
                self.hablar("Hay un problema técnico. Intentemos una vez más.")
                intentos += 1
                continue
            
            return respuesta
        
        return "sin_respuesta"

    def generar_ideas_iot_voz(self):
        """Recolecta información por voz para generar ideas de negocio IoT"""
        self.hablar("Perfecto, vamos a generar ideas de negocio IoT para ti.")
        
        # Recopilar información por voz
        sector = self.obtener_entrada_voz("¿En qué sector te interesa emprender? Por ejemplo: salud, agricultura, hogar inteligente, industria o transporte.")
        
        if sector == "sin_respuesta":
            sector = "general"
            self.hablar("Usaré un enfoque general para las ideas.")
        
        presupuesto = self.obtener_entrada_voz("¿Cuál es tu rango de inversión inicial? Puedes decir bajo para menos de 10 mil dólares, medio para 10 a 50 mil, o alto para más de 50 mil.")
        
        if presupuesto == "sin_respuesta":
            presupuesto = "medio"
            self.hablar("Asumiré un presupuesto medio.")
        
        experiencia = self.obtener_entrada_voz("¿Cuál es tu nivel técnico? Principiante, intermedio o avanzado.")
        
        if experiencia == "sin_respuesta":
            experiencia = "intermedio"
            self.hablar("Consideraré un nivel intermedio.")
        
        mercado = self.obtener_entrada_voz("¿A qué mercado apuntas? Local, nacional o internacional.")
        
        if mercado == "sin_respuesta":
            mercado = "nacional"
        
        recursos = self.obtener_entrada_voz("¿Qué recursos tienes disponibles? Por ejemplo: equipo, tiempo, conexiones.")
        
        if recursos == "sin_respuesta":
            recursos = "recursos básicos"
        
        # Generar prompt
        prompt = f"""Como experto en emprendimiento IoT, genera 3 ideas innovadoras de negocio considerando:

PERFIL DEL EMPRENDEDOR:
- Sector de interés: {sector}
- Presupuesto inicial: {presupuesto}
- Nivel técnico: {experiencia}
- Mercado objetivo: {mercado}
- Recursos disponibles: {recursos}

Para cada idea, incluye:
1. CONCEPTO: Descripción clara del producto/servicio IoT
2. PROBLEMA QUE RESUELVE: Necesidad específica del mercado
3. TECNOLOGÍA REQUERIDA: Sensores, conectividad, plataformas
4. MODELO DE NEGOCIO: Cómo generar ingresos
5. INVERSIÓN ESTIMADA: Capital inicial necesario
6. VENTAJA COMPETITIVA: Qué te diferencia

Enfócate en ideas viables, escalables y con potencial de ROI atractivo. Respuesta máximo 400 palabras para audio."""

        return self.consultar_api(prompt)

    def desarrollar_plan_negocio_voz(self):
        """Desarrolla un plan de negocio con entrada por voz"""
        idea = self.obtener_entrada_voz("Describe brevemente la idea IoT para la cual quieres el plan de negocio.")
        
        if idea == "sin_respuesta":
            self.hablar("Desarrollaré un plan general de negocio IoT.")
            idea = "startup IoT general"
        
        prompt = f"""Desarrolla un plan de negocio completo para esta idea IoT:

IDEA SELECCIONADA: {idea}

Estructura el plan con:
1. RESUMEN EJECUTIVO - Visión, misión y propuesta de valor
2. ANÁLISIS DE MERCADO - Tamaño, segmentación y competencia
3. PRODUCTO/SERVICIO - Especificaciones y roadmap
4. ESTRATEGIA DE MARKETING - Posicionamiento y canales
5. ANÁLISIS FINANCIERO - Proyecciones y métricas clave
6. PLAN DE IMPLEMENTACIÓN - Hitos y cronograma

Máximo 400 palabras para presentación por voz."""
        
        return self.consultar_api(prompt)

    def generar_proyecciones_financieras_voz(self):
        """Genera proyecciones financieras con entrada por voz"""
        self.hablar("Vamos a crear proyecciones financieras para tu negocio IoT.")
        
        precio = self.obtener_entrada_voz("¿Cuál sería el precio aproximado de tu producto o servicio IoT?")
        usuarios = self.obtener_entrada_voz("¿Cuántos usuarios o clientes esperas en el primer año?")
        crecimiento = self.obtener_entrada_voz("¿Qué porcentaje de crecimiento anual proyectas?")
        costos_desarrollo = self.obtener_entrada_voz("¿Cuáles son tus costos de desarrollo estimados?")
        costos_operacion = self.obtener_entrada_voz("¿Cuáles son tus costos operacionales mensuales estimados?")
        
        prompt = f"""Genera proyecciones financieras detalladas para un negocio IoT con:

PARÁMETROS:
- Precio del producto/servicio: {precio if precio != "sin_respuesta" else "precio competitivo"}
- Usuarios proyectados año 1: {usuarios if usuarios != "sin_respuesta" else "crecimiento gradual"}
- Crecimiento anual esperado: {crecimiento if crecimiento != "sin_respuesta" else "20-30%"}
- Costos de desarrollo: {costos_desarrollo if costos_desarrollo != "sin_respuesta" else "moderados"}
- Costos operacionales: {costos_operacion if costos_operacion != "sin_respuesta" else "escalables"}

INCLUIR:
1. Proyección de ingresos (3 años)
2. Estructura de costos principales
3. Punto de equilibrio estimado
4. Métricas clave IoT (CAC, LTV, MRR)
5. Recomendaciones de financiación

Respuesta concisa para audio, máximo 350 palabras."""
        
        return self.consultar_api(prompt)

    def analizar_mercado_iot_voz(self):
        """Analiza oportunidades en el mercado IoT"""
        prompt = """Realiza un análisis del mercado IoT actual incluyendo:

1. TENDENCIAS GLOBALES IoT 2024-2025
2. OPORTUNIDADES DE NICHO más prometedoras
3. FACTORES DE ÉXITO clave en emprendimientos IoT
4. ECOSISTEMA DE APOYO (aceleradoras, fondos, programas)
5. RECOMENDACIONES ESTRATÉGICAS para nuevos emprendedores

Enfoque práctico y conciso para presentación por voz, máximo 350 palabras."""
        
        return self.consultar_api(prompt)

    def consulta_libre_voz(self):
        """Permite consultas libres con el mentor IoT por voz"""
        self.hablar("Perfecto, soy tu mentor de emprendimiento IoT. ¿Qué te gustaría saber?")
        
        while True:
            pregunta = self.obtener_entrada_voz("Hazme tu consulta, o di 'menú' para volver al menú principal.")
            
            if pregunta == "sin_respuesta":
                self.hablar("No pude escuchar tu pregunta. ¿Quieres intentar de nuevo o volver al menú?")
                continue
            
            if any(palabra in pregunta for palabra in ['menú', 'menu', 'volver', 'regresar', 'salir']):
                self.hablar("Perfecto, regresemos al menú principal.")
                break
            
            prompt = f"""Como mentor de emprendimiento IoT, responde esta consulta de manera práctica y conversacional:

PREGUNTA: {pregunta}

Proporciona consejos específicos, ejemplos cuando sea posible, y pasos accionables.
Respuesta máximo 300 palabras para audio."""
            
            respuesta = self.consultar_api(prompt)
            self.hablar(respuesta)
            
            continuar = self.obtener_entrada_voz("¿Tienes otra pregunta, o quieres volver al menú principal?")
            if any(palabra in continuar for palabra in ['menú', 'menu', 'volver', 'no', 'salir']) if continuar != "sin_respuesta" else False:
                break

    def ver_resumen_proyecto_voz(self):
        """Muestra resumen del proyecto por voz"""
        if not self.conversacion_actual:
            self.hablar("No hay proyecto activo todavía. Te recomiendo generar algunas ideas primero.")
            return
        
        prompt = """Basándote en nuestra conversación, crea un resumen ejecutivo del proyecto IoT incluyendo:

1. Idea principal desarrollada
2. Mercado objetivo identificado  
3. Propuesta de valor clave
4. Próximos pasos recomendados
5. Recursos necesarios prioritarios

Resumen conciso para audio, máximo 250 palabras."""
        
        resumen = self.consultar_api(prompt)
        self.hablar("Aquí tienes el resumen de tu proyecto:")
        self.hablar(resumen)

    def limpiar_conversacion_voz(self):
        """Limpia el historial por voz"""
        self.conversacion_actual = []
        self.proyecto_actual = {}
        self.hablar("Perfecto, he limpiado la conversación. Ahora puedes empezar un nuevo proyecto desde cero.")

    def consultar_api(self, prompt, temperatura=0.7):
        """Consulta la API de DeepSeek con el prompt generado"""
        headers = {
            'Authorization': f'Bearer {self.API_KEY}',
            'Content-Type': 'application/json'
        }
        
        mensajes = [
            {
                'role': 'system',
                'content': 'Eres un mentor experto en emprendimiento IoT con 15 años de experiencia. Ayudas a emprendedores a desarrollar ideas innovadoras, planes de negocio sólidos y estrategias de crecimiento en el ecosistema Internet of Things. Tus respuestas son prácticas, detalladas, conversacionales y optimizadas para ser escuchadas por voz.'
            }
        ]
        
        mensajes.extend(self.conversacion_actual[-6:])  # Últimas 6 interacciones
        mensajes.append({'role': 'user', 'content': prompt})
        
        data = {
            'model': 'deepseek-chat',
            'temperature': temperatura,
            'messages': mensajes,
            'max_tokens': 800
        }
        
        try:
            response = requests.post(self.API_URL, headers=headers, json=data)
            response.raise_for_status()
            resultado = response.json()['choices'][0]['message']['content']
            
            # Guardar en historial
            self.conversacion_actual.append({'role': 'user', 'content': prompt})
            self.conversacion_actual.append({'role': 'assistant', 'content': resultado})
            
            # Mantener solo las últimas 20 interacciones
            if len(self.conversacion_actual) > 20:
                self.conversacion_actual = self.conversacion_actual[-20:]
            
            return resultado
            
        except requests.exceptions.HTTPError as err:
            return f"Disculpa, tuve un problema con la API. Error: {err.response.text}"
        except Exception as e:
            return f"Disculpa, tuve un problema técnico: {e}"

    def procesar_opcion_menu(self, opcion):
        """Procesa la opción seleccionada del menú"""
        if opcion == '1':
            respuesta = self.generar_ideas_iot_voz()
            self.hablar("Aquí tienes las ideas de negocio IoT generadas para ti:")
            self.hablar(respuesta)
            
        elif opcion == '2':
            respuesta = self.desarrollar_plan_negocio_voz()
            self.hablar("He desarrollado un plan de negocio completo para tu idea:")
            self.hablar(respuesta)
            
        elif opcion == '3':
            respuesta = self.generar_proyecciones_financieras_voz()
            self.hablar("Aquí están las proyecciones financieras para tu negocio IoT:")
            self.hablar(respuesta)
            
        elif opcion == '4':
            respuesta = self.analizar_mercado_iot_voz()
            self.hablar("Este es el análisis del mercado IoT actual:")
            self.hablar(respuesta)
            
        elif opcion == '5':
            self.consulta_libre_voz()
            
        elif opcion == '6':
            self.ver_resumen_proyecto_voz()
            
        elif opcion == '7':
            self.limpiar_conversacion_voz()
            
        elif opcion == '8':
            self.hablar("Ha sido un placer ayudarte con tu emprendimiento IoT. ¡Mucho éxito en tu proyecto! Hasta luego.")
            self.conversacion_activa = False
            return False
        
        return True

    def ejecutar_menu_voz(self):
        """Ejecuta el menú principal con reconocimiento de voz"""
        self.hablar("¡Bienvenido al Chatbot de Emprendimiento IoT con reconocimiento de voz! Te ayudaré a desarrollar ideas innovadoras y planes de negocio para el ecosistema IoT.")
        
        # Verificar micrófono
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Micrófono configurado correctamente")
        except Exception as e:
            print(f"❌ Error con el micrófono: {e}")
            self.hablar("Hay un problema con el micrófono. Verifica que esté conectado correctamente.")
            return
        
        while self.conversacion_activa:
            try:
                # Presentar menú
                self.presentar_menu_voz()
                
                # Obtener selección
                entrada_usuario = self.obtener_entrada_voz("¿Qué opción eliges? Puedes decir el número o describir lo que necesitas.", timeout=15)
                
                if entrada_usuario == "sin_respuesta":
                    self.hablar("No pude escuchar tu selección. Vamos a intentar de nuevo.")
                    continue
                
                # Detectar opción
                opcion = self.detectar_numero_opcion(entrada_usuario)
                
                if opcion is None:
                    opcion = self.detectar_intencion_menu(entrada_usuario)
                
                if opcion and opcion in ['1', '2', '3', '4', '5', '6', '7', '8']:
                    self.hablar(f"Has seleccionado la opción {opcion}.")
                    continuar = self.procesar_opcion_menu(opcion)
                    if not continuar:
                        break
                        
                    # Preguntar si quiere continuar
                    if opcion != '8':
                        continuar_respuesta = self.obtener_entrada_voz("¿Quieres hacer algo más, o prefieres salir?")
                        if continuar_respuesta != "sin_respuesta" and any(palabra in continuar_respuesta for palabra in ['salir', 'terminar', 'adiós', 'no']):
                            self.hablar("¡Perfecto! Ha sido un placer ayudarte. ¡Éxito en tu emprendimiento IoT!")
                            break
                else:
                    self.hablar("No pude identificar tu selección. Por favor, di el número de la opción que deseas, del 1 al 8.")
                
            except KeyboardInterrupt:
                self.hablar("Conversación interrumpida. ¡Hasta luego!")
                break
            except Exception as e:
                print(f"Error: {e}")
                self.hablar("Disculpa, tuve un problema técnico. Vamos a continuar.")

def main():
    """Función principal"""
    print("🚀 Iniciando Chatbot IoT con Reconocimiento de Voz y Menú Interactivo...")
    print("🎤 Asegúrate de tener un micrófono conectado y funcional")
    print("🔊 Habla claro y espera a que el bot termine de hablar antes de responder")
    print("-" * 80)
    
    bot = VoiceIoTMenuBot()
    bot.ejecutar_menu_voz()

if __name__ == "__main__":
    main()