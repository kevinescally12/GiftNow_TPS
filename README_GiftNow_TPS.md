# GiftNow TPS

## Descripción

GiftNow TPS es un Sistema de Procesamiento de Transacciones desarrollado para el área de Almacén e Inventarios de GiftNow S.A.C. El sistema permite gestionar movimientos de stock, alertas de inventario y clasificación ABC de productos.

El sistema está diseñado exclusivamente para el área de almacén. No incluye funcionalidades relacionadas con clientes, proveedores, pedidos ni órdenes de compra.

---

## Objetivo

Automatizar la gestión de inventario y reemplazar el control manual realizado en hojas de cálculo, proporcionando:

- Registro de movimientos de stock
- Control de inventario
- Alertas de stock mínimo
- Historial de movimientos
- Clasificación ABC
- Reportes de valorización y rotación

---

## Tecnologías Utilizadas

- Python 3.10+
- Tkinter
- MySQL 8.x
- mysql-connector-python
- Visual Studio Code

---

## Arquitectura

El sistema utiliza una arquitectura de 3 capas:

### Capa de Presentación
Archivos `ui_*.py`

Responsabilidades:
- Interfaces gráficas con Tkinter
- Validaciones visuales
- Control de acceso por rol

### Capa de Negocio
Archivos `logica_*.py`

Responsabilidades:
- Reglas de negocio
- Validaciones funcionales
- Procesamiento de movimientos
- Gestión de alertas
- Clasificación ABC

### Capa de Datos
Archivos `datos_*.py`

Responsabilidades:
- Consultas SQL
- Conexión con MySQL
- Operaciones CRUD

---

## Estructura del Proyecto

```text
giftnow_tps/
│
├── main.py
├── config.py
│
├── datos/
│   ├── conexion.py
│   ├── datos_usuario.py
│   ├── datos_producto.py
│   ├── datos_movimiento.py
│   └── datos_alerta.py
│
├── logica/
│   ├── logica_auth.py
│   ├── logica_movimiento.py
│   ├── logica_alerta.py
│   ├── logica_abc.py
│   └── logica_reportes.py
│
└── ui/
    ├── ui_login.py
    ├── ui_menu.py
    ├── ui_movimiento.py
    ├── ui_consulta.py
    ├── ui_alertas.py
    └── ui_reportes.py
```

---

## Base de Datos

La base de datos utiliza MySQL 8.x con motor InnoDB.

### Tablas principales

- usuario
- producto
- movimiento
- alerta_stock

### Características

- Uso de claves foráneas
- Transacciones atómicas
- Índices de optimización
- Integridad referencial

---

## Roles del Sistema

### ALMACENERO

Puede:
- Registrar ENTRADA
- Registrar SALIDA
- Registrar DEVOLUCION
- Consultar stock

No puede:
- Registrar AJUSTE
- Gestionar alertas

### SUPERVISOR

Puede:
- Registrar todos los movimientos
- Gestionar alertas
- Acceder a reportes
- Registrar AJUSTE

---

## Reglas de Negocio

### Movimientos

- SALIDA reduce stock
- ENTRADA incrementa stock
- DEVOLUCION incrementa stock
- AJUSTE reemplaza el stock actual

### Alertas

Las alertas se generan automáticamente cuando:

```text
stock_actual <= stock_minimo
```

Las alertas se cierran automáticamente cuando:

```text
stock_actual > stock_minimo
```

### Clasificación ABC

Los productos se clasifican según el valor acumulado:

- A: 0% - 70%
- B: 70% - 90%
- C: 90% - 100%

---

## Flujo Principal

1. Autenticación de usuario
2. Registro de movimientos
3. Actualización de stock
4. Validación de reglas
5. Gestión automática de alertas
6. Recalculo de clasificación ABC
7. Generación de reportes

---

## Instalación

### Clonar repositorio

```bash
git clone <repositorio>
cd giftnow_tps
```

### Instalar dependencias

```bash
pip install mysql-connector-python
```

### Configurar base de datos

1. Crear la base de datos MySQL
2. Ejecutar el script SQL
3. Configurar `config.py`

### Ejecutar sistema

```bash
python main.py
```

---

## Restricciones del Proyecto

- Solo se trabaja con el área de Almacén e Inventarios
- No existen módulos de clientes
- No existen módulos de proveedores
- No existen módulos de ventas
- No existen módulos de compras
- No se permite modificar la arquitectura establecida

---

## Roadmap de Desarrollo

1. Infraestructura de base de datos
2. Capa de datos
3. Autenticación y menú
4. Registro de movimientos
5. Consulta y alertas
6. Reportes y pruebas

---

## Autor

Proyecto TPS desarrollado para GiftNow S.A.C.
