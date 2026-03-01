# Detalles del Proyecto

Voy a investigar una forma de estudiar sistemáticamente a Chaplin. Las preguntas clave son:

- ¿Cuántas veces va Chaplin al baño al día?
- ¿Cada cuánto debería limpiar su arena?
- ¿Con qué frecuencia orina y hace sus necesidades sólidas?
- ¿Qué relación existe entre su horario de comidas y sus visitas al baño?
- ¿Existen correlaciones entre la frecuencia de sus visitas al baño y su salud, basadas en la cantidad y periodicidad de la comida y el agua que consume?
- ¿Es posible establecer indicadores de salud a partir de estos datos?
- Y, finalmente, ¿es posible automatizar la limpieza de su arena?

## Implementación

### 1. Frecuencia de visitas al baño

Utilizo un sensor de ultrasonido, ajustado a nivel de código para medir distancias. Esto me permite establecer de manera precisa si Chaplin está o no presente en la caja de arena: si la caja mide 50 cm de largo, el sensor detectará un obstáculo a una distancia menor cuando el felino esté dentro, y volverá a detectar la distancia total de la caja cuando salga.

El sensor verifica la presencia del animal cada 5 segundos. La comunicación entre el sensor y el sistema se realiza a través de un dispositivo ESP 32 conectado a una red WiFi, que a su vez se comunica con un servidor central. Este servidor gestiona el almacenamiento de datos y la comunicación entre los distintos dispositivos/sensores y la interfaz de usuario.

### 2. Limpieza de la arena

Inicialmente, realizaré una observación cualitativa para correlacionar los datos proporcionados por el sistema con mis observaciones directas. Esto me permitirá establecer un umbral de visitas al baño después del cual será necesario limpiar la arena.

Con el tiempo, y tras un análisis más detallado, espero determinar el momento óptimo para limpiar la arena, teniendo en cuenta los distintos tipos de desechos y cómo estos afectan la necesidad de limpieza.

### 3. Diferenciación entre orina y heces

En este punto, aún no tengo un método definido, pero espero utilizar algún tipo de tecnología de inteligencia artificial (idealmente de Google) para distinguir entre los diferentes tipos de desechos. Esto es crucial para entender mejor los patrones de salud y comportamiento de Chaplin.


