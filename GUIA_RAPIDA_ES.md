# Pointo Store: guía rápida

Este es un proyecto académico independiente. No cambia tu Pointo real ni procesa compras reales.

## Qué recibiste

Una tienda Django con tres aplicaciones: **shop** (catálogo), **cart** (carrito) y **orders** (pedidos). Tiene las tres categorías de tu propuesta: impresoras de recibos, rollos de papel y soportes para tablets. Incluye seis productos ficticios, administrador, pruebas y documentación.

## Cómo abrirlo

1. Descomprime el ZIP.
2. Instala Python 3.10 o superior si no lo tienes.
3. Abre una terminal dentro de `pointo-course-store`.
4. Sigue la sección de tu sistema operativo en `README.md`. Los comandos crean un entorno aislado, instalan Django/Pillow, crean las tablas y cargan productos ficticios.
5. Ejecuta `python manage.py runserver` y abre `http://127.0.0.1:8000/`.
6. Para administrar, ejecuta `python manage.py createsuperuser`, elige tus credenciales y entra en `/admin/`.

En Windows puedes usar `.\.venv\Scripts\python.exe` en lugar de `python`, como muestra el README. No hace falta publicar un sitio ni pagar hosting para probarlo.

## Qué debes poder explicar

- **Modelo:** define qué datos guardan las tablas. `Category` agrupa productos; `Product` guarda precio, disponibilidad y especificaciones. `Order` guarda el pedido y `OrderItem` sus productos, cantidades y precios.
- **Vista:** recibe una petición, consulta o actualiza datos y devuelve una página. Por ejemplo, `product_list` filtra los productos disponibles.
- **Template:** muestra los datos con HTML. `base.html` comparte cabecera y contador del carrito.
- **Sesión:** conserva tu carrito entre páginas sin crear una tabla personalizada de carritos.
- **Migración:** permite crear las tablas desde el código; por eso se incluye en el proyecto.
- **Checkout:** valida el formulario, guarda Order/OrderItem, vacía el carrito y muestra confirmación. No cobra nada.
- **Pruebas:** verifican automáticamente que el filtro por categoría, cambios del carrito y guardado de pedidos funcionen, entre otras cosas.

Los campos extra son `paper_width_mm` y `connection_type` para impresoras; `width_mm` y `length_m` para rollos; `tablet_size_inches` y `mount_type` para soportes. En el administrador, completa solo los dos campos de la categoría elegida.

## Para revisar antes de entregar

1. Ejecuta `python manage.py test`.
2. Prueba catálogo → producto → carrito → checkout usando datos ficticios.
3. Revisa el pedido guardado en el administrador.
4. Lee los comentarios y el README para entender el funcionamiento y cumplir las reglas del profesor sobre asistencia externa/IA.
5. Publica el código en el repositorio público de GitHub que pide la consigna y entrega su URL en Canvas, una vez autorizado. El ZIP no sustituye ese requisito.

**Estado:** no se ha creado/publicado un repositorio GitHub ni enviado la tarea a Canvas. Tampoco se ha instalado todavía en tu computadora personal; el código se verificó en un entorno cloud independiente.
