# Laboratorio 4: Quadtree para logística de entregas

Implementación desde cero de un quadtree 2D para responder búsquedas por radio y
vecinos más cercanos, con comparación frente a recorridos lineales.

## Unidades y datos

Las coordenadas del ejemplo son coordenadas cartesianas locales en **metros**,
generadas de forma reproducible con semilla 2026 dentro de un área de 10 × 10 km.
No son direcciones ni coordenadas geográficas reales. Una consulta de `500` usa
500 metros porque tanto los puntos como el radio usan la misma unidad. Para datos
reales de latitud/longitud se deben proyectar primero a un sistema métrico local;
no se debe comparar un radio en metros directamente con grados.

## Archivos y ejecución

- `quadtree.py`: clases `Point`, `Rectangle`, `QuadTree` y búsquedas espaciales.
- `test.py`: pruebas unitarias y creación de las figuras espaciales.
- `analisis.py`: benchmark con medianas, CSV y gráfico comparativo.
- `graficas/`: figuras SVG y métricas CSV generadas por los comandos siguientes.

Requiere Python 3.10+. Las figuras se generan como SVG sin librerías externas.

```bash
python -m unittest test -v
python test.py
python analisis.py
```

## Uso

```python
from quadtree import Point, Rectangle, QuadTree, build_quadtree

puntos = [Point(100, 200), Point(350, 200)]
limites = Rectangle(0, 0, 1000, 1000)
arbol = QuadTree(limites, capacity=4)
for punto in puntos:
    arbol.insert(punto)

rectangulo = arbol.query(Rectangle(50, 150, 300, 100))
vecinos_en_radio = arbol.range_search(Point(100, 200), 500)
mas_cercano = arbol.nearest(Point(120, 205))
tres_mas_cercanos = arbol.k_nearest(Point(120, 205), k=3)

arbol_automatico = build_quadtree(puntos)
```

`Rectangle.contains` usa límites inferiores inclusivos y superiores exclusivos.
`query` devuelve los puntos dentro de un rectángulo. `range_search` usa esa
consulta rectangular para obtener candidatos y luego conserva solo los puntos
dentro del círculo; incluye los puntos exactamente en el borde. El árbol conserva
duplicados. `k_nearest` devuelve hasta `k` puntos ordenados por distancia y los
empates se resuelven por coordenadas. `build_quadtree` calcula automáticamente
un rectángulo que contiene todos los puntos. El árbol es estático tras construirse.

## Complejidad y análisis

La construcción cuesta O(n log n) en datos espacialmente distribuidos y el espacio
O(n). Una consulta por radio suele visitar solo parte del árbol, pero en el peor
caso puede visitar todos los nodos y costar O(n). La búsqueda de vecinos cercanos
usa una cola prioritaria: su costo depende de los nodos visitados y de las
operaciones de prioridad, y en el peor caso puede llegar a O(n log n). La fuerza
bruta cuesta O(n) por consulta de radio o para encontrar un vecino, y O(n log n) si
se ordena toda la lista para obtener k vecinos.

No hay un umbral universal donde el árbol siempre gane: depende de distribución,
radio, capacidad de hojas, implementación y cantidad de consultas. El benchmark
mide nueve tamaños (100–50.000), 100 consultas por tamaño y medianas de siete
repeticiones. Reporta por separado consultas con índice ya construido y costo
total de construir más consultar. El punto de cruce debe leerse en las gráficas
generadas en la máquina donde se ejecuta el laboratorio; para una sola consulta,
la construcción puede hacer que la lista gane incluso cuando las consultas
repetidas favorecen al árbol.

En la ejecución de referencia guardada en `graficas/metricas.csv`, con 100
consultas por lote, el tiempo total del quadtree (construcción incluida) fue menor
que la lista ya en el menor tamaño medido, **100 puntos**: 4,27 ms frente a 5,36 ms
para rango; para vecino cercano, 4,26 ms frente a 7,34 ms.
Esto solo fija el cruce observado para esta implementación, esta distribución y
100 consultas; no demuestra que el quadtree convenga a partir de 100 puntos para
una consulta aislada. A 10.000 puntos, el rango tomó 257,53 ms con el árbol
incluida su construcción frente a 793,33 ms por lista; para el vecino más cercano,
224,54 ms frente a 726,69 ms. Repetir el benchmark en el equipo de entrega permite
contrastar esos números.

## Decisiones y límites

Se implementa el caso 2D solicitado. `QuadTree(boundary, capacity=4)` divide el
plano en cuatro cuadrantes cuando una hoja supera su capacidad. Los puntos que ya
estaban en un nodo permanecen allí y las inserciones posteriores se derivan a los
hijos. La búsqueda rectangular descarta cajas que no intersectan el rango. Los k
vecinos se encuentran con una cola de prioridad ordenada por la distancia mínima
posible a cada caja, por lo que el resultado es exacto. Datos coincidentes y un
límite de profundidad evitan subdivisiones infinitas.
